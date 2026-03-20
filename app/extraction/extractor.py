"""PaperExtractor: fills methods/limitations/claims via LLM extraction."""

import json
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.config.settings import settings
from app.core.atoms import ResearchAtom
from app.db.models import Paper
from app.llm.router import LLMRouter, LLMUnavailableError
from app.llm.prompts import EXTRACTION_PROMPT

logger = structlog.get_logger(__name__)


class PaperExtractor:
    """Extracts structured fields from paper abstracts using LLM."""

    def __init__(self):
        self.llm = LLMRouter()

    async def extract_one(self, atom: ResearchAtom, db: AsyncSession) -> ResearchAtom:
        """Extract methods, limitations, and claims for a single paper.

        Calls LLM with EXTRACTION_PROMPT, parses JSON, fills fields,
        updates DB record, and sets arxiv_status to 'processed'.
        On failure, sets arxiv_status to 'extraction_failed'.
        """
        try:
            prompt = EXTRACTION_PROMPT.format(abstract=atom.abstract)
            response = await self.llm.complete(prompt, expect_json=True)
            parsed = json.loads(response)

            atom.methods = parsed.get("methods", [])
            atom.limitations = parsed.get("limitations", [])
            atom.claims = parsed.get("claims", [])
            atom.arxiv_status = "processed"

            # Update DB record
            stmt = select(Paper).where(Paper.arxiv_id == atom.paper_id)
            result = await db.execute(stmt)
            paper = result.scalar_one_or_none()
            if paper:
                paper.arxiv_status = "processed"
                paper.updated_at = datetime.utcnow()
                await db.commit()

            logger.info(
                "extraction_complete",
                paper_id=atom.paper_id,
                methods_count=len(atom.methods),
                limitations_count=len(atom.limitations),
                claims_count=len(atom.claims),
            )
            return atom

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "extraction_json_parse_failed",
                paper_id=atom.paper_id,
                error=str(e),
                raw_response=response if "response" in dir() else "N/A",
            )
            await self._mark_failed(atom.paper_id, db)
            atom.arxiv_status = "extraction_failed"
            return atom

        except LLMUnavailableError:
            logger.error("extraction_llm_unavailable", paper_id=atom.paper_id)
            await self._mark_failed(atom.paper_id, db)
            atom.arxiv_status = "extraction_failed"
            return atom

    async def extract_batch(self, atoms: list[ResearchAtom], db: AsyncSession) -> list[ResearchAtom]:
        """Process a batch of papers through extraction.

        Processes each paper individually to ensure partial failures
        don't block the entire batch.
        """
        results = []
        for atom in atoms:
            extracted = await self.extract_one(atom, db)
            results.append(extracted)
        return results

    async def run_extraction_pipeline(self, db: AsyncSession) -> dict:
        """Fetch all 'raw' papers from DB and run batch extraction.

        Returns:
            Summary dict: {"processed": n, "failed": n}
        """
        logger.info("extraction_pipeline_started")

        # Fetch raw papers
        stmt = select(Paper).where(Paper.arxiv_status == "raw")
        result = await db.execute(stmt)
        papers = result.scalars().all()

        if not papers:
            logger.info("extraction_pipeline_no_raw_papers")
            return {"processed": 0, "failed": 0}

        # Convert to atoms
        atoms = [
            ResearchAtom(
                paper_id=p.arxiv_id,
                title=p.title,
                abstract=p.abstract,
                authors=p.authors or [],
                published_year=p.published_year,
                pdf_url=p.pdf_url,
                methods=[],
                limitations=[],
                claims=[],
                embedding=None,
                arxiv_status=p.arxiv_status,
            )
            for p in papers
        ]

        # Process in batches
        summary = {"processed": 0, "failed": 0}
        batch_size = settings.EXTRACTION_BATCH_SIZE

        for i in range(0, len(atoms), batch_size):
            batch = atoms[i : i + batch_size]
            results = await self.extract_batch(batch, db)
            for r in results:
                if r.arxiv_status == "processed":
                    summary["processed"] += 1
                else:
                    summary["failed"] += 1

        logger.info("extraction_pipeline_completed", **summary)
        return summary

    async def _mark_failed(self, arxiv_id: str, db: AsyncSession):
        """Mark a paper as extraction_failed in the DB."""
        stmt = select(Paper).where(Paper.arxiv_id == arxiv_id)
        result = await db.execute(stmt)
        paper = result.scalar_one_or_none()
        if paper:
            paper.arxiv_status = "extraction_failed"
            paper.updated_at = datetime.utcnow()
            await db.commit()
