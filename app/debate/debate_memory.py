"""DebateMemory: Loads ancestor debate history for arbiter context."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config.settings import settings
from app.core.debate_record import DebateRecord
from app.db.models import DebateHistory, HypothesisModel

logger = structlog.get_logger(__name__)


class DebateMemory:
    """Queries the ancestor chain of debates for a given hypothesis."""

    async def get_ancestor_debates(
        self,
        hypothesis_id: str,
        db: AsyncSession,
        max_depth: int | None = None,
    ) -> list[DebateRecord]:
        """Walk parent_hypothesis_id chain and fetch DebateHistory records.

        Returns records ordered most-recent-ancestor first.
        """
        if max_depth is None:
            max_depth = settings.DEBATE_HISTORY_MAX_DEPTH

        records: list[DebateRecord] = []
        current_id = hypothesis_id

        for _ in range(max_depth):
            # Load the hypothesis to find its parent
            hypothesis = await db.get(HypothesisModel, current_id)
            if not hypothesis or not hypothesis.parent_hypothesis_id:
                break

            parent_id = str(hypothesis.parent_hypothesis_id)

            # Load the parent hypothesis for title/claim
            parent_hyp = await db.get(HypothesisModel, parent_id)
            if not parent_hyp:
                break

            # Load debate history for the parent
            stmt = (
                select(DebateHistory)
                .where(DebateHistory.hypothesis_id == parent_hyp.id)
                .order_by(DebateHistory.created_at.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            debate_row = result.scalars().first()

            if debate_row:
                record = DebateRecord.from_db(
                    debate_row,
                    hypothesis_title=parent_hyp.title,
                    core_claim=parent_hyp.core_claim,
                )
                records.append(record)

            current_id = parent_id

        logger.info(
            "debate_memory_loaded",
            hypothesis_id=hypothesis_id,
            ancestor_count=len(records),
        )
        return records

    def format_history_block(self, records: list[DebateRecord]) -> str:
        """Format debate records into a compact, prompt-ready text block."""
        if not records:
            return ""

        lines = []
        for i, rec in enumerate(records, 1):
            label = "Parent" if i == 1 else f"Ancestor-{i}"
            parts = [
                f"{i}. {label}: \"{rec.hypothesis_title}\" ({rec.verdict})",
                f"   Claim: {rec.core_claim}",
            ]
            if rec.objections:
                parts.append(f"   Objections: {'; '.join(rec.objections)}")
            if rec.rebuttals:
                parts.append(f"   Rebuttals: {'; '.join(rec.rebuttals)}")
            if rec.rejection_reason:
                parts.append(f"   Rejection reason: {rec.rejection_reason}")
            if rec.addressed_prior_objections:
                parts.append(
                    f"   Addressed from prior: {'; '.join(rec.addressed_prior_objections)}"
                )
            if rec.surviving_risks:
                parts.append(f"   Surviving risks: {'; '.join(rec.surviving_risks)}")

            lines.append("\n".join(parts))

        return "\n\n".join(lines)
