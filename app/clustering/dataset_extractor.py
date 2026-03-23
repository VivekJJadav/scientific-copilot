"""DatasetExtractor: Extracts dataset names from papers using LLM."""

import json
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config.settings import settings
from app.db.models import Paper, DatasetRegistry
from app.llm.router import LLMRouter
from app.llm.prompts import DATASET_EXTRACTION_PROMPT

logger = structlog.get_logger(__name__)


class DatasetExtractor:
    """Extracts dataset/benchmark names from papers and maintains a registry."""

    def __init__(self):
        self.llm = LLMRouter()

    async def extract_from_papers(self, db: AsyncSession) -> dict:
        """Extract dataset names from all processed papers, upsert to registry.

        Returns:
            {datasets_found: int, new_entries: int, updated_entries: int}
        """
        stmt = select(Paper).where(Paper.arxiv_status.in_(["processed", "embedded"]))
        papers = (await db.execute(stmt)).scalars().all()

        summary = {"datasets_found": 0, "new_entries": 0, "updated_entries": 0}

        # Collect all dataset mentions across papers
        dataset_papers: dict[str, list[str]] = {}  # dataset_name -> [arxiv_ids]

        for paper in papers:
            datasets = await self._extract_one(paper)
            for ds in datasets:
                ds_lower = ds.strip()
                if not ds_lower:
                    continue
                dataset_papers.setdefault(ds_lower, []).append(paper.arxiv_id)
                summary["datasets_found"] += 1

        # Upsert to registry
        for ds_name, arxiv_ids in dataset_papers.items():
            stmt_existing = select(DatasetRegistry).where(DatasetRegistry.name == ds_name)
            existing = (await db.execute(stmt_existing)).scalars().first()

            if existing:
                existing.mention_count += len(arxiv_ids)
                # Merge paper_ids
                current_ids = set(existing.paper_ids or [])
                current_ids.update(arxiv_ids)
                existing.paper_ids = list(current_ids)
                summary["updated_entries"] += 1
            else:
                if len(arxiv_ids) >= settings.DATASET_MIN_MENTIONS:
                    entry = DatasetRegistry(
                        name=ds_name,
                        mention_count=len(arxiv_ids),
                        paper_ids=list(set(arxiv_ids)),
                    )
                    db.add(entry)
                    summary["new_entries"] += 1

        await db.commit()
        logger.info("dataset_extraction_complete", **summary)
        return summary

    async def _extract_one(self, paper: Paper) -> list[str]:
        """Extract dataset names from a single paper using LLM.

        Returns:
            List of dataset name strings.
        """
        prompt = DATASET_EXTRACTION_PROMPT.format(
            title=paper.title,
            abstract=paper.abstract,
            methods="(extracted from abstract)",
        )

        try:
            response = await self.llm.complete(prompt, expect_json=True)
            parsed = json.loads(response)
            datasets = parsed.get("datasets", [])
            if not isinstance(datasets, list):
                return []
            return [str(d) for d in datasets if d]
        except Exception as e:
            logger.warning(
                "dataset_extraction_failed",
                paper_id=paper.arxiv_id,
                error=str(e),
            )
            return []
