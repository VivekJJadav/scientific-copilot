import asyncio
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine
from app.ingestion.ingest_service import run_ingestion

logger = structlog.get_logger(__name__)

async def main():
    logger.info("seed_started")
    async with AsyncSession(engine, expire_on_commit=False) as session:
        summary = await run_ingestion(session)
        print(summary)
        logger.info("seed_completed", **summary)

if __name__ == "__main__":
    asyncio.run(main())
