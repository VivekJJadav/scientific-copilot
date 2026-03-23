"""HypothesisGenerator: produces grounded Hypothesis objects from gaps."""

import json
import uuid
import structlog
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text, func

from app.config.settings import settings
from app.core.atoms import ResearchAtom
from app.db.models import Paper, HypothesisModel
from app.llm.router import LLMRouter, LLMUnavailableError
from app.llm.prompts import HYPOTHESIS_GENERATION_PROMPT, NOVELTY_CHECK_PROMPT
from app.reasoning.hypothesis import Hypothesis
from app.reasoning.gap_extractor import GapExtractor
from app.extraction.embedder import PaperEmbedder

logger = structlog.get_logger(__name__)


class HypothesisGenerator:
    """Generates grounded hypotheses from research gaps."""

    def __init__(self):
        self.llm = LLMRouter()
        self.gap_extractor = GapExtractor()
        self.embedder = PaperEmbedder()

    async def generate(
        self, gap: dict, source_atoms: list[ResearchAtom], db: AsyncSession
    ) -> Hypothesis | None:
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
        rag_context, rag_ids = await self._retrieve_similar_papers(
            gap.get("description", ""), db
        )
        if rag_context:
            paper_summaries += "\n\nAdditional related papers (retrieved by similarity):\n"
            paper_summaries += rag_context
            for ret_id in rag_ids:
                source_ids.add(ret_id)

        if not source_ids:
            logger.warning("hypothesis_no_sources", gap=gap.get("description", ""))
            return None

        prompt = HYPOTHESIS_GENERATION_PROMPT.format(
            gap_description=gap.get("description", ""),
            paper_summaries=paper_summaries,
            max_compute=settings.MAX_COMPUTE,
        )

        try:
            response = await self.llm.complete(
                prompt, expect_json=True, force_json_object=True
            )
            parsed = json.loads(response)

            hypothesis = Hypothesis(
                id=str(uuid.uuid4()),
                title=parsed.get("title", ""),
                motivation=parsed.get("motivation", ""),
                core_claim=parsed.get("core_claim", ""),
                method_sketch=parsed.get("method_sketch", ""),
                expected_outcome=parsed.get("expected_outcome", ""),
                risk_factors=parsed.get("risk_factors", []),
                novelty_score=parsed.get("novelty_score", 0.0),
                feasibility_score=parsed.get("feasibility_score", 0.0),
                hardware_requirement=parsed.get("hardware_requirement", ""),
                source_paper_ids=list(source_ids),
                gap_description=gap.get("description", ""),
                status="pending",
                iteration_count=0,
                created_at=datetime.utcnow(),
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

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "hypothesis_generation_json_parse_failed",
                error=str(e),
                gap=gap.get("description", ""),
            )
            return None

        except LLMUnavailableError:
            logger.error(
                "hypothesis_generation_llm_unavailable",
                gap=gap.get("description", ""),
            )
            return None

    async def run_generation_pipeline(self, db: AsyncSession) -> dict:
        """Full pipeline: fetch processed papers → extract gaps → generate hypotheses.

        Returns:
            Summary dict: {"gaps_found": n, "hypotheses_generated": n, "hypotheses_discarded": n}
        """
        logger.info("hypothesis_generation_pipeline_started")

        # First, embed any processed papers that haven't been embedded yet
        embed_result = await self.embedder.embed_papers(db)
        logger.info("embedding_step_complete", **embed_result)

        # Fetch all processed or embedded papers
        stmt = select(Paper).where(
            Paper.arxiv_status.in_(["processed", "embedded"])
        )
        result = await db.execute(stmt)
        papers = result.scalars().all()

        if not papers:
            logger.info("hypothesis_pipeline_no_processed_papers")
            return {"gaps_found": 0, "hypotheses_generated": 0, "hypotheses_discarded": 0}

        # Convert to atoms
        atoms = [
            ResearchAtom(
                paper_id=p.arxiv_id,
                title=p.title,
                abstract=p.abstract,
                authors=p.authors or [],
                published_year=p.published_year,
                pdf_url=p.pdf_url,
                methods=[],
                limitations=[],
                claims=[],
                embedding=list(p.embedding) if p.embedding is not None else None,
                arxiv_status=p.arxiv_status,
            )
            for p in papers
        ]

        # Extract gaps
        gaps = await self.gap_extractor.extract_gaps(atoms, settings.ARXIV_QUERY)

        summary = {
            "gaps_found": len(gaps),
            "hypotheses_generated": 0,
            "hypotheses_discarded": 0,
        }

        # Generate hypotheses for top 3 gaps
        for gap in gaps[:3]:
            # Find source atoms for this gap
            source_ids = gap.get("source_paper_ids", [])
            source_atoms = [a for a in atoms if a.paper_id in source_ids]
            if not source_atoms:
                source_atoms = atoms[:5]  # fallback: use first 5

            hypothesis = await self.generate(gap, source_atoms, db)
            if hypothesis:
                summary["hypotheses_generated"] += 1
            else:
                summary["hypotheses_discarded"] += 1

        logger.info("hypothesis_generation_pipeline_completed", **summary)
        return summary

    async def _check_novelty(self, hypothesis: Hypothesis, db: AsyncSession) -> float:
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
            parsed = json.loads(response)
            score = float(parsed.get("novelty_score", hypothesis.novelty_score))

            logger.info(
                "novelty_check_complete",
                hypothesis_id=hypothesis.id,
                novelty_score=score,
                reasoning=parsed.get("reasoning", ""),
            )
            return score

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

    async def _persist_hypothesis(self, hypothesis: Hypothesis, db: AsyncSession):
        """Save a Hypothesis to the database."""
        model = HypothesisModel(
            id=uuid.UUID(hypothesis.id),
            title=hypothesis.title,
            motivation=hypothesis.motivation,
            core_claim=hypothesis.core_claim,
            method_sketch=hypothesis.method_sketch,
            expected_outcome=hypothesis.expected_outcome,
            risk_factors=hypothesis.risk_factors,
            novelty_score=hypothesis.novelty_score,
            feasibility_score=hypothesis.feasibility_score,
            hardware_requirement=hypothesis.hardware_requirement,
            source_paper_ids=hypothesis.source_paper_ids,
            gap_description=hypothesis.gap_description,
            status=hypothesis.status,
            iteration_count=hypothesis.iteration_count,
        )
        db.add(model)
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
