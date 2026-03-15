import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from app.db.session import get_session
from app.db.models import Paper
from app.schemas.paper import PaperListResponse, PaperResponse

router = APIRouter()

@router.get("", response_model=PaperListResponse)
async def list_papers(
    skip: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_session)
):
    count_stmt = select(func.count()).select_from(Paper)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = select(Paper).order_by(desc(Paper.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    papers = result.scalars().all()

    return {"items": papers, "total": total}

@router.get("/{id}", response_model=PaperResponse)
async def get_paper(id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    paper = await db.get(Paper, id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper
