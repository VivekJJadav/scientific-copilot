from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rate_limit import rate_limit
from app.db.session import get_session

router = APIRouter()

TABLES_TO_CLEAR = (
    "experiment_results",
    "experiments",
    "hypotheses",
    "gaps",
    "dataset_registry",
    "papers",
    "paper_clusters",
)


@router.post("/reset-db")
async def reset_db(
    db: AsyncSession = Depends(get_session),
    _rate_limited: None = Depends(rate_limit()),
):
    table_sql = ", ".join(TABLES_TO_CLEAR)
    await db.execute(text(f"TRUNCATE TABLE {table_sql} RESTART IDENTITY CASCADE"))
    await db.commit()
    return {"cleared_tables": list(TABLES_TO_CLEAR)}
