"""GapExtractor: identifies research gaps from ResearchAtoms and paper clusters."""

import json
import structlog
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config.settings import settings
from app.core.atoms import ResearchAtom
from app.llm.router import LLMRouter, LLMUnavailableError
from app.llm.prompts import GAP_EXTRACTION_PROMPT

logger = structlog.get_logger(__name__)


class GapExtractor:
    """Identifies research gaps from limitations across multiple papers."""

    def __init__(self):
        self.llm = LLMRouter()

    async def extract_gaps(self, atoms: list[ResearchAtom], topic: str) -> list[dict]:
        """Extract research gaps from a collection of ResearchAtoms.

        Args:
            atoms: List of atoms with populated limitations.
            topic: The research topic for context.

        Returns:
            List of gap dicts with description, source_paper_ids, gap_type.
        """
        if len(atoms) < 1:
            logger.warning(
                "gap_extraction_insufficient_papers",
                paper_count=len(atoms),
                minimum_required=1,
            )
            return []

        # Build limitations block
        limitations_block = self._build_limitations_block(atoms)

        prompt = GAP_EXTRACTION_PROMPT.format(
            n=len(atoms),
            topic=topic,
            limitations_block=limitations_block,
        )

        try:
            response = await self.llm.complete(
                prompt, expect_json=True, force_json_object=True
            )
            parsed = json.loads(response)
            gaps = parsed.get("gaps", [])

            logger.info(
                "gap_extraction_complete",
                topic=topic,
                paper_count=len(atoms),
                gaps_found=len(gaps),
            )
            return gaps

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "gap_extraction_json_parse_failed",
                error=str(e),
                topic=topic,
            )
            return []

        except LLMUnavailableError:
            logger.error("gap_extraction_llm_unavailable", topic=topic)
            return []

    def _build_limitations_block(self, atoms: list[ResearchAtom]) -> str:
        """Format limitations from all atoms into a block for the prompt."""
        lines = []
        for atom in atoms:
            if atom.limitations:
                header = f"Paper [{atom.paper_id}]: {atom.title}"
                for lim in atom.limitations:
                    lines.append(f"- {header}: {lim}")
            if atom.claims:
                for claim in atom.claims:
                    lines.append(f"- Paper [{atom.paper_id}] claims: {claim}")
        return "\n".join(lines) if lines else "No limitations found."

    async def find_gaps_from_clusters(
        self, db: AsyncSession, top_k: int = 5
    ) -> list[dict]:
        """Find research gaps from paper clusters using cosine similarity.

        For each cluster:
        - Fetches papers assigned to that cluster
        - Computes pairwise cosine similarity between embeddings
        - Returns pairs with similarity > GAP_SIMILARITY_THRESHOLD
        - Deduplicates against existing gaps in the DB

        Returns:
            List of gap dicts sorted by similarity descending.
        """
        from app.db.models import Paper, PaperCluster, Gap

        stmt = select(PaperCluster)
        clusters = (await db.execute(stmt)).scalars().all()

        if not clusters:
            logger.info("find_gaps_no_clusters")
            return []

        # Get existing gap source_paper_ids for dedup
        existing_gaps_stmt = select(Gap.source_paper_ids)
        existing_gaps = (await db.execute(existing_gaps_stmt)).scalars().all()
        existing_pairs = set()
        for gap_ids in existing_gaps:
            if gap_ids and len(gap_ids) >= 2:
                existing_pairs.add(frozenset(gap_ids[:2]))

        all_gaps = []

        for cluster in clusters:
            if not cluster.paper_ids:
                continue

            # Fetch papers in this cluster
            stmt = select(Paper).where(
                Paper.arxiv_id.in_(cluster.paper_ids),
                Paper.embedding.isnot(None),
            )
            papers = (await db.execute(stmt)).scalars().all()

            if len(papers) < 2:
                continue

            # Compute pairwise cosine similarity
            for i, p1 in enumerate(papers):
                for p2 in papers[i + 1:]:
                    pair_key = frozenset([p1.arxiv_id, p2.arxiv_id])
                    if pair_key in existing_pairs:
                        continue  # Dedup

                    e1 = np.array(p1.embedding)
                    e2 = np.array(p2.embedding)
                    similarity = float(
                        np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2) + 1e-8)
                    )

                    if similarity > settings.GAP_SIMILARITY_THRESHOLD:
                        all_gaps.append({
                            "gap_type": "cluster_insight",
                            "description": (
                                f"Topically close but methodologically disconnected: "
                                f"'{p1.title}' and '{p2.title}' (cluster: {cluster.label})"
                            ),
                            "source_paper_ids": [p1.arxiv_id, p2.arxiv_id],
                            "cluster_id": cluster.id,
                            "similarity": similarity,
                        })
                        existing_pairs.add(pair_key)

                        if len(all_gaps) >= top_k:
                            break
                if len(all_gaps) >= top_k:
                    break
            if len(all_gaps) >= top_k:
                break

        # Sort by similarity descending
        all_gaps.sort(key=lambda g: g["similarity"], reverse=True)

        logger.info("find_gaps_from_clusters_complete", gaps_found=len(all_gaps))
        return all_gaps[:top_k]
