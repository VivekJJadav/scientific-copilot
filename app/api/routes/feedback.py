"""API routes for the feedback loop."""

import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_session
from app.db.models import Experiment, HypothesisModel, ExperimentResult, Gap
from app.feedback.result_analyzer import ResultAnalyzer
from app.feedback.loop import FeedbackLoop

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/run")
async def run_feedback_loop(db: AsyncSession = Depends(get_session)):
    """Run the full feedback loop: analyze → gaps → hypotheses.

    Returns:
        Summary with experiments_analyzed, new_gaps_from_failures,
        arbiter_examples_updated, new_hypotheses_generated.
    """
    loop = FeedbackLoop()
    result = await loop.run(db)
    return result


@router.post("/analyze/{experiment_id}")
async def analyze_experiment(
    experiment_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    """Analyze a single completed experiment.

    Returns:
        Analysis with outcome, result_summary, lessons_learned.
    """
    exp = await db.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if exp.status != "completed":
        raise HTTPException(status_code=400, detail="Experiment is not completed")

    # Check if already analyzed
    stmt = select(ExperimentResult).where(ExperimentResult.experiment_id == exp.id)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        return {
            "status": "already_analyzed",
            "result_id": str(existing.id),
            "outcome": existing.outcome,
        }

    hypothesis = await db.get(HypothesisModel, exp.hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    analyzer = ResultAnalyzer()
    analysis = await analyzer.analyze(
        results=exp.results or {},
        hypothesis={
            "title": hypothesis.title,
            "core_claim": hypothesis.core_claim,
            "expected_outcome": hypothesis.expected_outcome,
        },
        experiment_id=str(exp.id),
    )

    er = ExperimentResult(
        experiment_id=exp.id,
        hypothesis_id=hypothesis.id,
        outcome=analysis["outcome"],
        metrics=exp.results or {},
        result_summary=analysis["result_summary"],
        lessons_learned=analysis["lessons_learned"],
    )
    db.add(er)
    await db.commit()
    await db.refresh(er)

    return {"status": "success", "analysis": analysis}


@router.post("/requeue-failed")
async def requeue_failed(db: AsyncSession = Depends(get_session)):
    """Convert all failed experiment outcomes into new gaps.

    Returns:
        {failed_outcomes_processed, new_gaps_created}
    """
    stmt = select(ExperimentResult).where(ExperimentResult.outcome == "failed")
    failed_results = (await db.execute(stmt)).scalars().all()

    processed = 0
    new_gaps = 0
    for r in failed_results:
        # Check if a gap already exists from this experiment result
        hyp = await db.get(HypothesisModel, r.hypothesis_id)
        if not hyp:
            continue

        gap = Gap(
            gap_type="negative_result",
            gap_description=(
                f"Failed hypothesis '{hyp.title}': {r.result_summary}. "
                f"Lessons: {', '.join(r.lessons_learned)}"
            ),
            source_paper_ids=hyp.source_paper_ids or [],
            similarity=0.0,
            used=False,
        )
        db.add(gap)
        processed += 1
        new_gaps += 1

    if new_gaps > 0:
        await db.commit()

    return {"failed_outcomes_processed": processed, "new_gaps_created": new_gaps}
