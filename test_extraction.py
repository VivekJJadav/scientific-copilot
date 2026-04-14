import asyncio
import os
import structlog
from app.db.session import SessionLocal
from app.extraction.extractor import PaperExtractor
from sqlalchemy import text, select
from app.db.models import Paper

async def run():
    async with SessionLocal() as db:
        extractor = PaperExtractor()
        # Ensure there is a raw paper
        await db.execute(text("UPDATE papers SET arxiv_status='raw'"))
        await db.commit()
        
        stmt = select(Paper).where(Paper.arxiv_status == 'raw')
        result = await db.execute(stmt)
        paper = result.scalars().first()
        
        if not paper:
            print("No paper found")
            return
            
        print(f"Testing extraction for paper {paper.arxiv_id}")
        # Let's run run_extraction_pipeline directly
        res = await extractor.run_extraction_pipeline(db)
        print("Pipeline Result:", res)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
