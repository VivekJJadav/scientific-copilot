import uuid
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.review.review_service import ReviewService

router = APIRouter()
review_service = ReviewService()

class QueueItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    core_claim: str
    novelty_score: float
    feasibility_score: float
    risk_factors: list[str]
    arbiter_notes: Optional[str]
    source_paper_ids: list[str]
    
class RejectRequest(BaseModel):
    reason: str

class ModifyRequest(BaseModel):
    method_sketch: Optional[str] = None
    expected_outcome: Optional[str] = None
    risk_factors: Optional[list[str]] = None

@router.get("/queue", response_model=List[QueueItemResponse])
async def get_review_queue(db: AsyncSession = Depends(get_session)):
    pending = await review_service.get_pending(db)
    
    # We only want to return a subset of keys for the queue view
    return [
        QueueItemResponse(
            id=h.id,
            title=h.title,
            core_claim=h.core_claim,
            novelty_score=h.novelty_score,
            feasibility_score=h.feasibility_score,
            risk_factors=h.risk_factors or [],
            arbiter_notes=h.arbiter_notes,
            source_paper_ids=h.source_paper_ids or []
        ) for h in pending
    ]

@router.post("/{id}/approve")
async def approve_hypothesis(id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    hypothesis = await review_service.approve(str(id), db)
    return {"status": "success", "hypothesis_id": hypothesis.id, "new_status": hypothesis.status}

@router.post("/{id}/reject")
async def reject_hypothesis(id: uuid.UUID, req: RejectRequest, db: AsyncSession = Depends(get_session)):
    hypothesis = await review_service.reject(str(id), req.reason, db)
    return {"status": "success", "hypothesis_id": hypothesis.id, "new_status": hypothesis.status}

@router.patch("/{id}/modify")
async def modify_hypothesis(id: uuid.UUID, req: ModifyRequest, db: AsyncSession = Depends(get_session)):
    updates = req.model_dump(exclude_unset=True)
    hypothesis = await review_service.modify(str(id), updates, db)
    return {"status": "success", "hypothesis_id": hypothesis.id, "action": "modified"}
