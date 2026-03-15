from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.ingestion.ingest_service import run_ingestion

router = APIRouter()

@router.post("/arxiv")
async def ingest_arxiv(db: AsyncSession = Depends(get_session)):
    summary = await run_ingestion(db)
    return summary
