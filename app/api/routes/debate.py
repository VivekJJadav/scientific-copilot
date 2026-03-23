import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_session
from app.db.models import HypothesisModel, Paper
from app.core.atoms import ResearchAtom
from app.debate.debate_graph import run_debate

logger = structlog.get_logger(__name__)
router = APIRouter()

async def _process_debate(hypothesis_id: uuid.UUID, db: AsyncSession) -> dict:
    hypothesis = await db.get(HypothesisModel, hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
        
    # Fetch source papers
    papers = []
    if hypothesis.source_paper_ids:
        stmt = select(Paper).where(Paper.arxiv_id.in_(hypothesis.source_paper_ids))
        result = await db.execute(stmt)
        papers_db = result.scalars().all()
        papers = [
            ResearchAtom(
                paper_id=p.arxiv_id,
                title=p.title,
                abstract=p.abstract,
                authors=p.authors,
                published_year=p.published_year,
                pdf_url=p.pdf_url,
                methods=[],
                limitations=[],
                claims=[],
                embedding=p.embedding,
                arxiv_status=p.arxiv_status
            )
            for p in papers_db
        ]

    # Run LangGraph Debate
    final_state = await run_debate(hypothesis, papers)
    
    verdict = final_state.get("arbiter_verdict", "FAIL")
    rounds_completed = final_state.get("round", 0) - 1  # -1 because proposer is 1, so 3 cycles -> 4. Wait.
    # Actually just log state["round"] or state["round"] - 1.
    # proposer increments to 1. 3 cycles increment to 4. 
    # Let's say rounds_completed = (state["round"] - 1)
    
    if verdict == "PASS" and final_state["final_hypothesis"]:
        updated_hyp = final_state["final_hypothesis"]
        hypothesis.novelty_score = updated_hyp.novelty_score
        hypothesis.feasibility_score = updated_hyp.feasibility_score
        hypothesis.risk_factors = updated_hyp.risk_factors
        hypothesis.status = "pending"
    else:
        hypothesis.status = "rejected"
        hypothesis.rejection_reason = final_state.get("rejection_reason", "Failed debate")
        
    hypothesis.debate_rounds = rounds_completed
    
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
async def debate_single(id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    return await _process_debate(id, db)


@router.post("/run-all")
async def debate_run_all(db: AsyncSession = Depends(get_session)):
    stmt = select(HypothesisModel).where(
        HypothesisModel.status == "pending",
        HypothesisModel.debate_rounds == None
    )
    result = await db.execute(stmt)
    hypotheses = result.scalars().all()
    
    summary = {"debated": 0, "passed": 0, "failed": 0}
    
    for h in hypotheses:
        res = await _process_debate(h.id, db)
        summary["debated"] += 1
        if res["verdict"] == "PASS":
            summary["passed"] += 1
        else:
            summary["failed"] += 1
            
    return summary
