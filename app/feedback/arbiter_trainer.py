"""ArbiterTrainer: Builds few-shot examples from past experimental outcomes."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.config.settings import settings
from app.db.models import ExperimentResult, HypothesisModel

logger = structlog.get_logger(__name__)


class ArbiterTrainer:
    """Retrieves and formats past outcomes for Arbiter few-shot learning."""

    async def get_few_shot_examples(
        self, db: AsyncSession, limit: int | None = None
    ) -> list[dict]:
        """Query experiment_results joined with hypotheses for few-shot context.

        Returns empty list if fewer than FEEDBACK_MIN_EXPERIMENTS results exist.
        """
        if limit is None:
            limit = settings.ARBITER_FEW_SHOT_LIMIT

        # Check if we have enough data
        count_stmt = select(ExperimentResult)
        count_result = (await db.execute(count_stmt)).scalars().all()
        if len(count_result) < settings.FEEDBACK_MIN_EXPERIMENTS:
            logger.info(
                "arbiter_few_shot_insufficient_data",
                count=len(count_result),
                required=settings.FEEDBACK_MIN_EXPERIMENTS,
            )
            return []

        stmt = (
            select(ExperimentResult, HypothesisModel)
            .join(HypothesisModel, ExperimentResult.hypothesis_id == HypothesisModel.id)
            .order_by(desc(ExperimentResult.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()

        examples = []
        for er, hyp in rows:
            examples.append({
                "hypothesis_title": hyp.title,
                "core_claim": hyp.core_claim,
                "outcome": er.outcome,
                "result_summary": er.result_summary,
            })

        logger.info("arbiter_few_shot_loaded", count=len(examples))
        return examples

    def format_examples(self, examples: list[dict]) -> str:
        """Format few-shot examples into a readable string block."""
        if not examples:
            return ""

        lines = []
        for i, ex in enumerate(examples, 1):
            lines.append(
                f"{i}. Hypothesis: {ex['hypothesis_title']}\n"
                f"   Claim: {ex['core_claim']}\n"
                f"   Outcome: {ex['outcome']}\n"
                f"   Summary: {ex['result_summary']}"
            )
        return "\n\n".join(lines)
