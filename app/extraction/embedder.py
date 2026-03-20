"""PaperEmbedder: generates sentence-transformer embeddings for papers.

This is a separate step from LLM extraction. After papers are 'processed',
this generates 384-dim embeddings using all-MiniLM-L6-v2 and stores them
in the embedding column, setting arxiv_status to 'embedded'.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.db.models import Paper

logger = structlog.get_logger(__name__)


class PaperEmbedder:
    """Generates embeddings for processed papers using sentence-transformers."""

    def __init__(self):
        self._model = None

    def _get_model(self):
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("embedding_model_loaded", model="all-MiniLM-L6-v2")
        return self._model

    async def embed_papers(self, db: AsyncSession) -> dict:
        """Generate embeddings for all 'processed' papers.

        Returns:
            Summary dict: {"embedded": n, "failed": n}
        """
        logger.info("embedding_pipeline_started")

        stmt = select(Paper).where(Paper.arxiv_status == "processed")
        result = await db.execute(stmt)
        papers = result.scalars().all()

        if not papers:
            logger.info("embedding_pipeline_no_processed_papers")
            return {"embedded": 0, "failed": 0}

        summary = {"embedded": 0, "failed": 0}
        model = self._get_model()

        # Build texts for batch encoding
        texts = [f"{p.title}. {p.abstract}" for p in papers]

        try:
            embeddings = model.encode(texts, show_progress_bar=False)
        except Exception as e:
            logger.error("embedding_batch_encode_failed", error=str(e))
            return {"embedded": 0, "failed": len(papers)}

        for paper, embedding in zip(papers, embeddings):
            try:
                paper.embedding = embedding.tolist()
                paper.arxiv_status = "embedded"
                paper.updated_at = datetime.utcnow()
                summary["embedded"] += 1
            except Exception as e:
                logger.warning(
                    "embedding_single_failed",
                    paper_id=paper.arxiv_id,
                    error=str(e),
                )
                summary["failed"] += 1

        await db.commit()
        logger.info("embedding_pipeline_completed", **summary)
        return summary
