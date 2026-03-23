import structlog
from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
import uuid
from datetime import datetime

from app.config.settings import settings
from app.db.models import Paper
from app.ingestion.arxiv_client import fetch_papers

logger = structlog.get_logger(__name__)

async def run_ingestion(db: AsyncSession, limit: int = None) -> dict:
    logger.info("ingestion_started", query=settings.ARXIV_QUERY)
    
    # Fetch from ArXiv
    fetch_limit = limit or settings.ARXIV_MAX_RESULTS
    atoms = await fetch_papers(settings.ARXIV_QUERY, fetch_limit)
    
    # Fetch existing titles for deduplication
    result = await db.execute(select(Paper.title))
    existing_titles = result.scalars().all()
    
    summary = {"fetched": len(atoms), "inserted": 0, "skipped": 0}
    
    for atom in atoms:
        # Title dedup check using RapidFuzz
        is_duplicate = False
        for ext_title in existing_titles:
            similarity = fuzz.ratio(atom.title.lower(), ext_title.lower())
            if similarity > 90:
                is_duplicate = True
                break
                
        if is_duplicate:
            logger.warning("paper_skipped_duplicate", arxiv_id=atom.paper_id, title=atom.title)
            summary["skipped"] += 1
            continue
            
        stmt = insert(Paper).values(
            id=uuid.uuid4(),
            arxiv_id=atom.paper_id,
            title=atom.title,
            abstract=atom.abstract,
            authors=atom.authors,
            published_year=atom.published_year,
            pdf_url=atom.pdf_url,
            embedding=atom.embedding,
            arxiv_status=atom.arxiv_status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # On conflict do nothing
        stmt = stmt.on_conflict_do_nothing(index_elements=["arxiv_id"])
        
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount > 0:
            logger.info("paper_inserted", arxiv_id=atom.paper_id)
            summary["inserted"] += 1
            existing_titles.append(atom.title)  # Add to existing titles to prevent within-batch duplicates
        else:
            logger.warning("paper_skipped_duplicate", arxiv_id=atom.paper_id)
            summary["skipped"] += 1
            
    logger.info("ingestion_completed", **summary)
    return summary
