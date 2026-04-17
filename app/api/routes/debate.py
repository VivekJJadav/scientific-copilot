import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_session
from app.db.models import HypothesisModel, Paper
from app.core.atoms import ResearchAtom
from app.config.settings import settings
from app.debate.debate_graph import run_debate
from app.api.routes.tasks import create_task, run_in_background
from app.api.rate_limit import rate_limit

logger = structlog.get_logger(__name__)
router = APIRouter()

async def _process_debate(hypothesis_id: uuid.UUID, db: AsyncSession) -> dict:
    hypothesis = await db.get(HypothesisModel, hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
        
    # Fetch source papers
    papers = []
    if hypothesis.source_paper_ids:
        limited_source_ids = hypothesis.source_paper_ids[:settings.DEBATE_MAX_SOURCE_PAPERS]
        stmt = select(Paper).where(Paper.arxiv_id.in_(limited_source_ids))
        result = await db.execute(stmt)
        papers_db = result.scalars().all()
        papers = [ResearchAtom.from_paper(p) for p in papers_db]

    # Run LangGraph Debate
    final_state = await run_debate(hypothesis, papers)
    
    verdict = final_state.get("arbiter_verdict", "FAIL")
    rounds_completed = final_state.get("round", 0)
    
    if verdict == "PASS" and final_state["final_hypothesis"]:
        updated_hyp = final_state["final_hypothesis"]
        hypothesis.novelty_score = updated_hyp.novelty_score
        hypothesis.feasibility_score = updated_hyp.feasibility_score
        hypothesis.risk_factors = updated_hyp.risk_factors
        
    # Always keep it pending so the human can review it (Approve/Reject)
    hypothesis.status = "pending"
    if verdict != "PASS":
        hypothesis.rejection_reason = final_state.get("rejection_reason", "Failed debate")
        
    # Ensure we store at least 1 round if started
    hypothesis.debate_rounds = rounds_completed
    
    # Store transcript in memory for the Debate Drawer UI
    transcript = []
    if final_state.get("proposal"):
        transcript.append({"role": "proposer", "content": final_state["proposal"], "round": 0})
        
    for i, crit in enumerate(final_state.get("critiques", [])):
        transcript.append({"role": "critic", "content": crit, "round": i+1})
        if i < len(final_state.get("rebuttals", [])):
            transcript.append({"role": "proposer", "content": final_state.get("rebuttals")[i], "round": i+1})
            
    hypothesis.debate_transcript = transcript
    await db.commit()
    
    logger.info(
        "debate_completed",
        hypothesis_id=str(hypothesis_id),
        verdict=verdict,
        rounds=rounds_completed,
        final_novelty=hypothesis.novelty_score,
        final_feasibility=hypothesis.feasibility_score
    )
    
    return {
        "verdict": verdict,
        "final_novelty_score": hypothesis.novelty_score,
        "final_feasibility_score": hypothesis.feasibility_score,
        "rounds_completed": rounds_completed,
        "rejection_reason": hypothesis.rejection_reason
    }


@router.post("/{id}/debate")
async def debate_single(
    id: uuid.UUID,
    background_tasks: BackgroundTasks,
    _rate_limited: None = Depends(rate_limit()),
):
    task_id = create_task("debate")
    background_tasks.add_task(run_in_background, task_id, _process_debate, id)
    return {"task_id": task_id, "status": "queued"}


async def _debate_run_all_task(db: AsyncSession):
    stmt = select(HypothesisModel).where(
        HypothesisModel.status == "pending"
    )
    result = await db.execute(stmt)
    all_pending = result.scalars().all()
    
    # Filter in Python to capture both NULL and 0 rounds
    hypotheses = [h for h in all_pending if not h.debate_rounds]
    
    summary = {"debated": 0, "passed": 0, "failed": 0}
    
    for h in hypotheses:
        res = await _process_debate(h.id, db)
        summary["debated"] += 1
        if res["verdict"] == "PASS":
            summary["passed"] += 1
        else:
            summary["failed"] += 1
            
    return summary

@router.post("/run-all")
async def debate_run_all(
    background_tasks: BackgroundTasks,
    _rate_limited: None = Depends(rate_limit()),
):
    task_id = create_task("debate")
    background_tasks.add_task(run_in_background, task_id, _debate_run_all_task)
    return {"task_id": task_id, "status": "queued"}

@router.get("/{id}")
async def get_debate_transcript(id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    hypothesis = await db.get(HypothesisModel, id)
    if not hypothesis or hypothesis.debate_transcript is None:
        raise HTTPException(status_code=404, detail="Debate transcript not found")
        
    return {
        "transcript": hypothesis.debate_transcript,
        "verdict": "PASS" if hypothesis.status == "approved" else ("FAIL" if hypothesis.rejection_reason else "PENDING"),
        "final_novelty": hypothesis.novelty_score,
        "final_feasibility": hypothesis.feasibility_score,
        "surviving_risks": hypothesis.risk_factors or [],
        "arbiter_notes": hypothesis.arbiter_notes or ""
    }
