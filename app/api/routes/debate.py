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
from app.api.routes.tasks import create_task, run_in_background, update_task_status
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

    # Load ancestor debate history
    from app.debate.debate_memory import DebateMemory
    memory = DebateMemory()
    ancestor_records = await memory.get_ancestor_debates(str(hypothesis_id), db)
    debate_history_block = memory.format_history_block(ancestor_records)

    # Run LangGraph Debate with history context
    final_state = await run_debate(hypothesis, papers, debate_history=debate_history_block)
    
    verdict = final_state.get("arbiter_verdict", "FAIL")
    rounds_completed = final_state.get("round", 0)
    
    if verdict == "PASS" and final_state["final_hypothesis"]:
        updated_hyp = final_state["final_hypothesis"]
        hypothesis.novelty_score = updated_hyp.novelty_score
        hypothesis.feasibility_score = updated_hyp.feasibility_score
        hypothesis.risk_factors = updated_hyp.risk_factors
        hypothesis.rejection_reason = None

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
            transcript.append({"role": "rebuttal", "content": final_state.get("rebuttals")[i], "round": i+1})

    arbiter_content = "\n".join(
        part for part in [
            f"Verdict: {verdict}",
            f"Reason: {hypothesis.rejection_reason}" if hypothesis.rejection_reason else None,
            f"Notes: {hypothesis.arbiter_notes}" if hypothesis.arbiter_notes else None,
        ] if part
    )
    if arbiter_content:
        transcript.append({"role": "arbiter", "content": arbiter_content, "round": rounds_completed})
            
    hypothesis.debate_transcript = transcript

    # Persist structured DebateHistory record
    from app.db.models import DebateHistory
    arbiter_parsed = final_state.get("_arbiter_parsed", {})
    debate_record = DebateHistory(
        hypothesis_id=hypothesis.id,
        verdict=verdict,
        rejection_reason=hypothesis.rejection_reason,
        objections=arbiter_parsed.get("key_objections", []),
        rebuttals=arbiter_parsed.get("addressed_prior_objections", []),
        surviving_risks=arbiter_parsed.get("surviving_risks", []),
        arbiter_notes=arbiter_parsed.get("arbiter_notes", ""),
        final_novelty_score=hypothesis.novelty_score,
        final_feasibility_score=hypothesis.feasibility_score,
        addressed_prior_objections=arbiter_parsed.get("addressed_prior_objections", []),
    )
    db.add(debate_record)

    await db.commit()
    
    logger.info(
        "debate_completed",
        hypothesis_id=str(hypothesis_id),
        verdict=verdict,
        rounds=rounds_completed,
        final_novelty=hypothesis.novelty_score,
        final_feasibility=hypothesis.feasibility_score,
        ancestor_debates=len(ancestor_records),
        key_objections=len(arbiter_parsed.get("key_objections", [])),
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


async def _debate_run_all_task(db: AsyncSession, task_id: str | None = None):
    stmt = select(HypothesisModel).where(
        HypothesisModel.status == "pending"
    )
    result = await db.execute(stmt)
    all_pending = result.scalars().all()
    
    # Filter in Python to capture both NULL and 0 rounds
    hypotheses = [h for h in all_pending if not h.debate_rounds]
    
    summary = {"debated": 0, "passed": 0, "failed": 0}

    total_hypotheses = max(len(hypotheses), 1)
    for index, h in enumerate(hypotheses, start=1):
        res = await _process_debate(h.id, db)
        summary["debated"] += 1
        if res["verdict"] == "PASS":
            summary["passed"] += 1
        else:
            summary["failed"] += 1

        if task_id:
            progress = 15 + int((index / total_hypotheses) * 80)
            update_task_status(
                task_id,
                "running",
                progress=min(progress, 95),
                message=(
                    f"Debated {summary['debated']} hypotheses "
                    f"({summary['passed']} pass / {summary['failed']} fail)"
                ),
            )
            
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

    verdict = "PENDING"
    if hypothesis.rejection_reason:
        verdict = "FAIL"
    elif hypothesis.debate_rounds is not None and hypothesis.debate_rounds > 0:
        verdict = "PASS"

    return {
        "transcript": hypothesis.debate_transcript,
        "verdict": verdict,
        "final_novelty": hypothesis.novelty_score,
        "final_feasibility": hypothesis.feasibility_score,
        "surviving_risks": hypothesis.risk_factors or [],
        "arbiter_notes": hypothesis.arbiter_notes or ""
    }
