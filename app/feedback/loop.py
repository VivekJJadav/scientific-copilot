"""FeedbackLoop: Orchestrates the full feedback cycle — analyze → gaps → hypotheses."""

import re
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

    async def run(
        self,
        db: AsyncSession,
        task_id: str | None = None,
    ) -> dict:
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
        if task_id:
            from app.api.routes.tasks import update_task_status

            update_task_status(
                task_id,
                "running",
                progress=15,
                message="Analyzing completed experiments",
            )

        # Step 1: Analyze experiments
        analysis_result = await self.analyzer.run_analysis_pipeline(db)

        # Step 2: Count arbiter examples
        examples = await self.trainer.get_few_shot_examples(db)
        arbiter_examples_count = len(examples)

        # Step 3: Fetch unused gaps from failures
        stmt = select(Gap).where(Gap.used == False, Gap.gap_type == "negative_result")  # noqa: E712
        unused_gaps = (await db.execute(stmt)).scalars().all()

        if task_id:
            from app.api.routes.tasks import update_task_status

            update_task_status(
                task_id,
                "running",
                progress=55,
                message=f"Loaded {len(unused_gaps)} feedback gaps",
            )

        new_hypotheses = 0
        total_gaps = max(len(unused_gaps), 1)
        for index, gap in enumerate(unused_gaps, start=1):
            # Find the original hypothesis that spawned this gap
            parent_hyp = await self._find_parent_hypothesis(gap, db)

            # Generate a new hypothesis from this gap
            hypothesis = await self._generate_from_gap(gap, parent_hyp, db)
            if hypothesis:
                new_hypotheses += 1
                gap.used = True
            else:
                logger.info(
                    "feedback_gap_retained_for_retry",
                    gap_id=str(gap.id),
                    gap_type=gap.gap_type,
                )

            if task_id:
                from app.api.routes.tasks import update_task_status

                progress = 55 + int((index / total_gaps) * 40)
                update_task_status(
                    task_id,
                    "running",
                    progress=min(progress, 95),
                    message=f"Generated {new_hypotheses} feedback hypotheses",
                )

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
        marker_match = re.match(
            r"^\[parent_hypothesis:([0-9a-fA-F-]{36})\]\s*",
            gap.gap_description or "",
        )
        if marker_match:
            return await db.get(HypothesisModel, marker_match.group(1))

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
            "description": re.sub(
                r"^\[parent_hypothesis:[0-9a-fA-F-]{36}\]\s*",
                "",
                gap.gap_description,
            ),
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
            hypothesis.parent_hypothesis_id = str(parent_hyp.id)
            hypothesis.iteration_count = parent_hyp.iteration_count + 1
            await db.commit()
            await db.refresh(hypothesis)
            logger.info(
                "feedback_hypothesis_linked",
                new_id=str(hypothesis.id),
                parent_id=str(parent_hyp.id),
                iteration=hypothesis.iteration_count,
            )

        return hypothesis
