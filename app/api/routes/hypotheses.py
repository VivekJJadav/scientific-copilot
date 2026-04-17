"""API routes for extraction and hypothesis generation."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from typing import Optional

from app.db.session import get_session
from app.db.models import HypothesisModel
from app.schemas.hypothesis import HypothesisListResponse, HypothesisResponse
from app.extraction.extractor import PaperExtractor
from app.extraction.embedder import get_embedder
from app.reasoning.hypothesis_generator import HypothesisGenerator
from app.api.routes.tasks import create_task, run_in_background
from app.api.rate_limit import rate_limit

router = APIRouter()


async def _run_extraction_task(db: AsyncSession):
    extractor = PaperExtractor()
    extraction_result = await extractor.run_extraction_pipeline(db)

    embedder = get_embedder()
    embed_result = await embedder.embed_papers(db)

    return {
        "processed": extraction_result["processed"],
        "failed": extraction_result["failed"],
        "embedded": embed_result["embedded"],
    }

@router.post("/extract")
async def run_extraction(
    background_tasks: BackgroundTasks,
    _rate_limited: None = Depends(rate_limit()),
):
    task_id = create_task("extract")
    background_tasks.add_task(run_in_background, task_id, _run_extraction_task)
    return {"task_id": task_id, "status": "queued"}

async def _generate_hypotheses_task(db: AsyncSession):
    generator = HypothesisGenerator()
    return await generator.run_generation_pipeline(db)

@router.post("/hypotheses/generate")
async def generate_hypotheses(
    background_tasks: BackgroundTasks,
    _rate_limited: None = Depends(rate_limit()),
):
    task_id = create_task("hypothesize")
    background_tasks.add_task(run_in_background, task_id, _generate_hypotheses_task)
    return {"task_id": task_id, "status": "queued"}


@router.get("/hypotheses", response_model=HypothesisListResponse)
async def list_hypotheses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
):
    """List hypotheses with pagination and optional status filter."""
    # Count total
    count_stmt = select(func.count()).select_from(HypothesisModel)
    if status:
        count_stmt = count_stmt.where(HypothesisModel.status == status)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Fetch items
    stmt = select(HypothesisModel).order_by(desc(HypothesisModel.created_at))
    if status:
        stmt = stmt.where(HypothesisModel.status == status)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    hypotheses = result.scalars().all()

    return {"items": hypotheses, "total": total}


@router.get("/hypotheses/{id}", response_model=HypothesisResponse)
async def get_hypothesis(id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """Get a single hypothesis by UUID. Returns 404 if not found."""
    hypothesis = await db.get(HypothesisModel, id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis
