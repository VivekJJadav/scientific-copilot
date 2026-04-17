"""PaperExtractor: fills methods/limitations/claims via LLM extraction."""

import json
import asyncio
import structlog
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import UTC, datetime

from app.config.settings import settings
from app.core.atoms import ResearchAtom
from app.db.models import Paper
from app.ingestion.pdf_text import fetch_pdf_text
from app.llm.router import LLMRouter, LLMUnavailableError
from app.llm.prompts import EXTRACTION_PROMPT

logger = structlog.get_logger(__name__)


class ExtractionResponse(BaseModel):
    methods: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)

class PaperExtractor:
    """Extracts structured fields from paper abstracts using LLM."""

    def __init__(self):
        self.llm = LLMRouter()

    async def extract_one(self, atom: ResearchAtom, sem: asyncio.Semaphore) -> tuple[ResearchAtom, bool]:
        """Extract methods, limitations, and claims using LLM concurrently.
        
        Returns a tuple: (atom, success_flag). Does not perform DB writes.
        """
        async with sem:
            try:
                full_text, chunks, source = await fetch_pdf_text(atom.pdf_url)
                extraction_text = full_text or atom.abstract
                atom_text_chunks = chunks
                atom_content_source = source
                prompt = EXTRACTION_PROMPT.format(abstract=extraction_text[:12000])
                response = await self.llm.complete(
                    prompt, expect_json=True, force_json_object=True
                )
                parsed = ExtractionResponse.model_validate_json(response)

                atom.methods = parsed.methods
                atom.limitations = parsed.limitations
                atom.claims = parsed.claims
                atom.arxiv_status = "processed"

                logger.info(
                    "extraction_llm_complete",
                    paper_id=atom.paper_id,
                    methods_count=len(atom.methods),
                    limitations_count=len(atom.limitations),
                    claims_count=len(atom.claims),
                    content_source=atom_content_source,
                )
                atom._full_text = full_text  # type: ignore[attr-defined]
                atom._text_chunks = atom_text_chunks  # type: ignore[attr-defined]
                atom._content_source = atom_content_source  # type: ignore[attr-defined]
                return atom, True

            except ValidationError as e:
                logger.warning(
                    "extraction_json_parse_failed",
                    paper_id=atom.paper_id,
                    error=str(e),
                    raw_output=response if "response" in locals() else None,
                )
                atom.arxiv_status = "extraction_failed"
                return atom, False

            except LLMUnavailableError:
                logger.error("extraction_llm_unavailable", paper_id=atom.paper_id)
                atom.arxiv_status = "extraction_failed"
                return atom, False

    async def extract_batch(self, atoms: list[ResearchAtom], db: AsyncSession) -> list[ResearchAtom]:
        """Process a batch of papers concurrently using an asyncio.Semaphore.
        
        DB writes happen sequentially after LLM calls resolve.
        """
        import asyncio
        sem = asyncio.Semaphore(min(settings.EXTRACTION_BATCH_SIZE, 5))
        
        tasks = [self.extract_one(atom, sem) for atom in atoms]
        results = await asyncio.gather(*tasks)

        final_atoms = []
        for atom, success in results:
            stmt = select(Paper).where(Paper.arxiv_id == atom.paper_id)
            res = await db.execute(stmt)
            paper = res.scalar_one_or_none()
            if paper:
                if success:
                    paper.full_text = getattr(atom, "_full_text", None)
                    paper.text_chunks = getattr(atom, "_text_chunks", [])
                    paper.content_source = getattr(atom, "_content_source", "abstract")
                    paper.methods = atom.methods
                    paper.limitations = atom.limitations
                    paper.claims = atom.claims
                    paper.arxiv_status = "processed"
                else:
                    paper.full_text = getattr(atom, "_full_text", None)
                    paper.text_chunks = getattr(atom, "_text_chunks", [])
                    paper.content_source = getattr(atom, "_content_source", "abstract")
                    paper.arxiv_status = "extraction_failed"
                paper.updated_at = datetime.now(UTC)
                
            final_atoms.append(atom)
            
        await db.commit()
        return final_atoms

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
        atoms = [ResearchAtom.from_paper(p) for p in papers]

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
