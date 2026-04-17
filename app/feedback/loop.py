"""FeedbackLoop: Orchestrates the full feedback cycle — analyze → gaps → hypotheses."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config.settings import settings
from app.db.models import Gap, HypothesisModel
from app.feedback.result_analyzer import ResultAnalyzer
from app.feedback.arbiter_trainer import ArbiterTrainer
from app.reasoning.hypothesis_generator import HypothesisGenerator

logger = structlog.get_logger(__name__)


class FeedbackLoop:
    """Orchestrates the complete feedback cycle."""

    def __init__(self):
        self.analyzer = ResultAnalyzer()
        self.trainer = ArbiterTrainer()
        self.generator = HypothesisGenerator()

    async def run(self, db: AsyncSession) -> dict:
        """Run the full feedback loop.

        Steps:
        1. Analyze all completed but unanalyzed experiments
        2. Failed outcomes already create gaps via ResultAnalyzer
        3. Fetch unused gaps and generate new hypotheses from them
        4. Set parent_hypothesis_id and iteration_count on feedback hypotheses
        5. Update arbiter few-shot example count

        Returns:
            Summary dict with counts.
        """
        logger.info("feedback_loop_started")

        # Step 1: Analyze experiments
        analysis_result = await self.analyzer.run_analysis_pipeline(db)

        # Step 2: Count arbiter examples
        examples = await self.trainer.get_few_shot_examples(db)
        arbiter_examples_count = len(examples)

        # Step 3: Fetch unused gaps from failures
        stmt = select(Gap).where(Gap.used == False, Gap.gap_type == "negative_result")  # noqa: E712
        unused_gaps = (await db.execute(stmt)).scalars().all()

        new_hypotheses = 0
        for gap in unused_gaps:
            # Find the original hypothesis that spawned this gap
            parent_hyp = await self._find_parent_hypothesis(gap, db)

            # Generate a new hypothesis from this gap
            hypothesis = await self._generate_from_gap(gap, parent_hyp, db)
            if hypothesis:
                new_hypotheses += 1

            # Mark gap as used
            gap.used = True

        if unused_gaps:
            await db.commit()

        summary = {
            "experiments_analyzed": analysis_result["analyzed"],
            "new_gaps_from_failures": analysis_result.get("new_gaps", 0),
            "arbiter_examples_updated": arbiter_examples_count,
            "new_hypotheses_generated": new_hypotheses,
        }

        logger.info("feedback_loop_completed", **summary)
        return summary

    async def _find_parent_hypothesis(
        self, gap: Gap, db: AsyncSession
    ) -> HypothesisModel | None:
        """Find the parent hypothesis that this gap derived from."""
        if not gap.source_paper_ids:
            return None

        # Look for a hypothesis whose source papers overlap with this gap
        # Use a simple query — fetch recent hypotheses and check overlap in Python
        stmt = select(HypothesisModel).order_by(HypothesisModel.created_at.desc()).limit(20)
        hypotheses = (await db.execute(stmt)).scalars().all()

        gap_ids = set(gap.source_paper_ids)
        for hyp in hypotheses:
            hyp_ids = set(hyp.source_paper_ids or [])
            if gap_ids & hyp_ids:  # any overlap
                return hyp
        return None

    async def _generate_from_gap(
        self,
        gap: Gap,
        parent_hyp: HypothesisModel | None,
        db: AsyncSession,
    ):
        """Generate a hypothesis from a feedback-derived gap."""
        from app.core.atoms import ResearchAtom
        from app.db.models import Paper

        # Build gap dict compatible with HypothesisGenerator
        gap_dict = {
            "description": gap.gap_description,
            "source_paper_ids": gap.source_paper_ids or [],
            "gap_type": gap.gap_type,
        }

        # Get source papers for context
        source_atoms = []
        if gap.source_paper_ids:
            stmt = select(Paper).where(Paper.arxiv_id.in_(gap.source_paper_ids[:5]))
            papers = (await db.execute(stmt)).scalars().all()
            source_atoms = [ResearchAtom.from_paper(p) for p in papers]

        if not source_atoms:
            # Fallback: use any processed papers
            stmt = select(Paper).where(Paper.arxiv_status.in_(["processed", "embedded"])).limit(3)
            papers = (await db.execute(stmt)).scalars().all()
            source_atoms = [ResearchAtom.from_paper(p) for p in papers]

        hypothesis = await self.generator.generate(gap_dict, source_atoms, db)

        if hypothesis and parent_hyp:
            # Update the persisted hypothesis with parent info
            from app.db.models import HypothesisModel as HM
            import uuid

            stmt = select(HM).where(HM.id == uuid.UUID(hypothesis.id))
            hyp_model = (await db.execute(stmt)).scalars().first()
            if hyp_model:
                hyp_model.parent_hypothesis_id = str(parent_hyp.id)
                hyp_model.iteration_count = parent_hyp.iteration_count + 1
                await db.commit()
                logger.info(
                    "feedback_hypothesis_linked",
                    new_id=hypothesis.id,
                    parent_id=str(parent_hyp.id),
                    iteration=hyp_model.iteration_count,
                )

        return hypothesis
