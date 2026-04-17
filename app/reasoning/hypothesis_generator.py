"""HypothesisGenerator: produces grounded Hypothesis objects from gaps."""

import uuid
import structlog
from pydantic import BaseModel, ValidationError, Field
from datetime import UTC, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text, func

from app.config.settings import settings
from app.core.atoms import ResearchAtom
from app.db.models import Paper, HypothesisModel, Gap, DatasetRegistry
from app.llm.router import LLMRouter, LLMUnavailableError
from app.llm.prompts import HYPOTHESIS_GENERATION_PROMPT, NOVELTY_CHECK_PROMPT
from app.reasoning.gap_extractor import GapExtractor
from app.extraction.embedder import get_embedder

logger = structlog.get_logger(__name__)


class HypothesisResponseSchema(BaseModel):
    title: str = ""
    motivation: str = ""
    core_claim: str = ""
    method_sketch: str = ""
    expected_outcome: str = ""
    risk_factors: list[str] = Field(default_factory=list)
    novelty_score: float = 0.0
    feasibility_score: float = 0.0
    hardware_requirement: str = ""

class NoveltyResponseSchema(BaseModel):
    novelty_score: float
    reasoning: str = ""


class GapLLMResponseSchema(BaseModel):
    description: str
    source_paper_ids: list[str] = Field(default_factory=list)
    gap_type: str = "unknown"

class HypothesisGenerator:
    """Generates grounded hypotheses from research gaps."""

    def __init__(self):
        self.llm = LLMRouter()
        self.gap_extractor = GapExtractor()
        self.embedder = get_embedder()

    async def generate(
        self, gap: dict, source_atoms: list[ResearchAtom], db: AsyncSession
    ) -> HypothesisModel | None:
        """Generate a single hypothesis from a gap and source papers.

        Uses pgvector cosine similarity for RAG retrieval of related papers
        to provide grounding context.
        """
        # Build paper summaries for context
        paper_summaries = self._build_paper_summaries(source_atoms)

        # Keep track of all source paper IDs
        source_ids = set()
        for atom in source_atoms:
            source_ids.add(atom.paper_id)
        for gap_id in gap.get("source_paper_ids", []):
            source_ids.add(gap_id)

        # Retrieve top-5 similar papers via pgvector for grounding
        # NOTE: RAG papers are used for prompt context only, NOT added to source_paper_ids
        # to avoid connecting hypotheses to papers they weren't actually derived from.
        rag_context, rag_ids = await self._retrieve_similar_papers(
            gap.get("description", ""), db
        )
        if rag_context:
            paper_summaries += "\n\nAdditional related papers (retrieved by similarity):\n"
            paper_summaries += rag_context

        if not source_ids:
            logger.warning("hypothesis_no_sources", gap=gap.get("description", ""))
            return None

        # Inject dataset context from registry
        ds_context = await self._get_dataset_context(db)
        gap_desc = gap.get("description", "")
        if ds_context:
            gap_desc += f"\n\nRecommended datasets/benchmarks: {ds_context}"

        prompt = HYPOTHESIS_GENERATION_PROMPT.format(
            gap_description=gap_desc,
            paper_summaries=paper_summaries,
            max_compute=settings.MAX_COMPUTE,
        )

        try:
            response = await self.llm.complete(
                prompt, expect_json=True, force_json_object=True
            )
            parsed = HypothesisResponseSchema.model_validate_json(response)

            hypothesis = HypothesisModel(
                id=uuid.uuid4(),
                title=parsed.title,
                motivation=parsed.motivation,
                core_claim=parsed.core_claim,
                method_sketch=parsed.method_sketch,
                expected_outcome=parsed.expected_outcome,
                risk_factors=parsed.risk_factors,
                novelty_score=parsed.novelty_score,
                feasibility_score=parsed.feasibility_score,
                hardware_requirement=parsed.hardware_requirement,
                source_paper_ids=list(source_ids),
                gap_description=gap.get("description", ""),
                status="pending",
                iteration_count=0,
                created_at=datetime.now(UTC),
            )

            # Run novelty check against existing hypotheses
            novelty_score = await self._check_novelty(hypothesis, db)
            hypothesis.novelty_score = novelty_score  # Override self-assessed score

            # Check thresholds
            if not hypothesis.passes_threshold(
                settings.NOVELTY_THRESHOLD, settings.FEASIBILITY_THRESHOLD
            ):
                logger.info(
                    "hypothesis_discarded_below_threshold",
                    title=hypothesis.title,
                    novelty_score=hypothesis.novelty_score,
                    feasibility_score=hypothesis.feasibility_score,
                )
                return None

            # Persist to DB
            await self._persist_hypothesis(hypothesis, db)

            logger.info(
                "hypothesis_generated",
                hypothesis_id=hypothesis.id,
                title=hypothesis.title,
                novelty_score=hypothesis.novelty_score,
                feasibility_score=hypothesis.feasibility_score,
            )
            return hypothesis

        except ValidationError as e:
            logger.warning(
                "hypothesis_generation_json_parse_failed",
                error=str(e),
                gap=gap.get("description", ""),
                raw_output=response if "response" in locals() else None,
            )
            return None

        except LLMUnavailableError:
            logger.error(
                "hypothesis_generation_llm_unavailable",
                gap=gap.get("description", ""),
            )
            return None

    async def run_generation_pipeline(self, db: AsyncSession) -> dict:
        """Full pipeline: fetch gaps → generate hypotheses.

        Prioritizes unused gaps from the gaps table, then falls back to
        extracting new gaps from processed papers.

        Returns:
            Summary dict: {"gaps_found": n, "hypotheses_generated": n, "hypotheses_discarded": n}
        """
        logger.info("hypothesis_generation_pipeline_started")

        # First, embed any processed papers that haven't been embedded yet
        embed_result = await self.embedder.embed_papers(db)
        logger.info("embedding_step_complete", **embed_result)

        # Fetch unused gaps from DB first (these come from clustering + feedback)
        stmt = select(Gap).where(Gap.used == False).limit(20)  # noqa: E712
        db_gaps = (await db.execute(stmt)).scalars().all()

        # Convert DB gaps to dicts
        gaps = []
        gap_models = {}
        for g in db_gaps:
            gap_dict = {
                "description": g.gap_description,
                "source_paper_ids": g.source_paper_ids or [],
                "gap_type": g.gap_type,
            }
            gaps.append(gap_dict)
            gap_models[g.gap_description] = g

        # If we have fewer than 15 gaps, extract more from papers to top off
        if len(gaps) < 15:
            papers_stmt = select(Paper).where(
                Paper.arxiv_status.in_(["processed", "embedded"])
            )
            result = await db.execute(papers_stmt)
            papers = result.scalars().all()

            if papers:
                atoms = [ResearchAtom.from_paper(p) for p in papers]
                extracted_gaps = await self.gap_extractor.extract_gaps(atoms, settings.ARXIV_QUERY)

                # Also find cluster-aware gaps
                cluster_gaps = await self.gap_extractor.find_gaps_from_clusters(db)
                gaps.extend(cluster_gaps)
                gaps.extend(extracted_gaps)

        summary = {
            "gaps_found": len(gaps),
            "hypotheses_generated": 0,
            "hypotheses_discarded": 0,
        }

        if not gaps:
            logger.info("hypothesis_pipeline_no_gaps")
            return summary

        # Fetch all papers for atom building
        all_papers_stmt = select(Paper).where(
            Paper.arxiv_status.in_(["processed", "embedded"])
        )
        all_papers = (await db.execute(all_papers_stmt)).scalars().all()
        all_atoms = [ResearchAtom.from_paper(p) for p in all_papers]

        # Generate hypotheses for up to 10 gaps to yield more hypotheses
        for gap in gaps[:10]:
            # Find source atoms for this gap
            source_ids = gap.get("source_paper_ids", [])
            source_atoms = [a for a in all_atoms if a.paper_id in source_ids]
            if not source_atoms:
                source_atoms = all_atoms[:5]  # fallback: use first 5

            hypothesis = await self.generate(gap, source_atoms, db)
            if hypothesis:
                summary["hypotheses_generated"] += 1
                # Mark the gap as used if it came from DB
                gap_desc = gap.get("description", "")
                if gap_desc in gap_models:
                    gap_models[gap_desc].used = True
            else:
                summary["hypotheses_discarded"] += 1

        # Commit gap used=true updates
        await db.commit()

        logger.info("hypothesis_generation_pipeline_completed", **summary)
        return summary

    async def _get_dataset_context(self, db: AsyncSession) -> str:
        """Fetch top datasets from registry for injection into prompts."""
        stmt = (
            select(DatasetRegistry.name)
            .where(DatasetRegistry.mention_count >= settings.DATASET_MIN_MENTIONS)
            .order_by(DatasetRegistry.mention_count.desc())
            .limit(5)
        )
        names = (await db.execute(stmt)).scalars().all()
        return ", ".join(names) if names else ""

    async def _check_novelty(self, hypothesis: HypothesisModel, db: AsyncSession) -> float:
        """Check novelty of a hypothesis against existing ones."""
        stmt = select(HypothesisModel.title)
        result = await db.execute(stmt)
        existing_titles = result.scalars().all()

        if not existing_titles:
            return hypothesis.novelty_score  # Keep LLM self-assessed score if no existing

        existing_block = "\n".join(f"- {t}" for t in existing_titles)
        prompt = NOVELTY_CHECK_PROMPT.format(
            hypothesis_title=hypothesis.title,
            core_claim=hypothesis.core_claim,
            existing_titles=existing_block,
        )

        try:
            response = await self.llm.complete(prompt, expect_json=True)
            parsed = NoveltyResponseSchema.model_validate_json(response)
            score = float(parsed.novelty_score)

            logger.info(
                "novelty_check_complete",
                hypothesis_id=hypothesis.id,
                novelty_score=score,
                reasoning=parsed.reasoning,
            )
            return score

        except ValidationError as e:
            logger.warning(
                "novelty_check_failed",
                hypothesis_id=hypothesis.id,
                error=str(e),
                raw_output=response if "response" in locals() else None,
            )
            return hypothesis.novelty_score
        except Exception as e:
            logger.warning(
                "novelty_check_failed",
                hypothesis_id=hypothesis.id,
                error=str(e),
            )
            return hypothesis.novelty_score

    async def _retrieve_similar_papers(
        self, query_text: str, db: AsyncSession
    ) -> tuple[str, list[str]]:
        """Retrieve top-5 most similar papers using pgvector cosine similarity."""
        try:
            # Generate embedding for the query
            model = self.embedder._get_model()
            query_embedding = model.encode(query_text).tolist()

            # Use pgvector cosine distance operator
            stmt = (
                select(Paper)
                .where(Paper.embedding.isnot(None))
                .order_by(Paper.embedding.cosine_distance(query_embedding))
                .limit(5)
            )
            result = await db.execute(stmt)
            papers = result.scalars().all()

            if not papers:
                return "", []

            lines = []
            ids = []
            for p in papers:
                lines.append(f"[{p.arxiv_id}] {p.title}: {p.abstract[:200]}...")
                ids.append(p.arxiv_id)
            return "\n".join(lines), ids

        except Exception as e:
            logger.warning("rag_retrieval_failed", error=str(e))
            return "", []

    async def _persist_hypothesis(self, hypothesis: HypothesisModel, db: AsyncSession):
        """Save a Hypothesis to the database."""
        db.add(hypothesis)
        await db.commit()

    def _build_paper_summaries(self, atoms: list[ResearchAtom]) -> str:
        """Build a summary block from source atoms for the prompt."""
        lines = []
        for atom in atoms:
            methods_str = ", ".join(atom.methods) if atom.methods else "N/A"
            lines.append(
                f"[{atom.paper_id}] {atom.title} (methods: {methods_str})\n"
                f"  Abstract: {atom.abstract[:300]}..."
            )
        return "\n\n".join(lines)
