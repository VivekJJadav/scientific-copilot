"""GapExtractor: identifies research gaps from ResearchAtoms."""

import json
import structlog

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
        if len(atoms) < 5:
            logger.warning(
                "gap_extraction_insufficient_papers",
                paper_count=len(atoms),
                minimum_required=5,
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
            response = await self.llm.complete(prompt, expect_json=True)
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
