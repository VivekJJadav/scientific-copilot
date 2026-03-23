import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from fastapi import HTTPException

from app.db.models import HypothesisModel

class ReviewService:
    async def get_pending(self, db: AsyncSession) -> list[HypothesisModel]:
        stmt = select(HypothesisModel).where(
            HypothesisModel.status == "pending"
        ).order_by(desc(HypothesisModel.novelty_score))
        
        result = await db.execute(stmt)
        return result.scalars().all()
        
    async def approve(self, hypothesis_id: str, db: AsyncSession) -> HypothesisModel:
        hypothesis = await db.get(HypothesisModel, uuid.UUID(hypothesis_id))
        if not hypothesis:
            raise HTTPException(status_code=404, detail="Hypothesis not found")
            
        if hypothesis.status != "pending":
            raise HTTPException(status_code=400, detail=f"Hypothesis is in {hypothesis.status} state, not pending.")
            
        hypothesis.status = "approved"
        hypothesis.approved_at = datetime.utcnow()
        
        # Create an experiment record automatically
        from app.db.models import Experiment
        experiment = Experiment(
            hypothesis_id=hypothesis.id,
            status="queued",
            experiment_dir="" # Will be populated by TemplateRunner
        )
        db.add(experiment)
        
        await db.commit()
        await db.refresh(hypothesis)
        return hypothesis

    async def reject(self, hypothesis_id: str, reason: str, db: AsyncSession) -> HypothesisModel:
        hypothesis = await db.get(HypothesisModel, uuid.UUID(hypothesis_id))
        if not hypothesis:
            raise HTTPException(status_code=404, detail="Hypothesis not found")
            
        if hypothesis.status != "pending":
            raise HTTPException(status_code=400, detail=f"Hypothesis is in {hypothesis.status} state, not pending.")
            
        hypothesis.status = "rejected"
        hypothesis.rejection_reason = reason
        await db.commit()
        await db.refresh(hypothesis)
        return hypothesis

    async def modify(self, hypothesis_id: str, updates: dict, db: AsyncSession) -> HypothesisModel:
        hypothesis = await db.get(HypothesisModel, uuid.UUID(hypothesis_id))
        if not hypothesis:
            raise HTTPException(status_code=404, detail="Hypothesis not found")
            
        if hypothesis.status != "pending":
            raise HTTPException(status_code=400, detail=f"Hypothesis is in {hypothesis.status} state, not pending.")
        
        allowed_keys = {"method_sketch", "expected_outcome", "risk_factors"}
        
        modified = False
        for key, value in updates.items():
            if key in allowed_keys and value is not None:
                setattr(hypothesis, key, value)
                modified = True
                
        if modified:
            await db.commit()
            await db.refresh(hypothesis)
            
        return hypothesis
