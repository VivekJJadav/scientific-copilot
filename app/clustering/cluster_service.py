"""ClusterService: Orchestrates the full clustering pipeline."""

import structlog
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering.clusterer import PaperClusterer
from app.clustering.dataset_extractor import DatasetExtractor
from app.reasoning.gap_extractor import GapExtractor
from app.db.models import Gap, Paper, PaperCluster

logger = structlog.get_logger(__name__)


class ClusterService:
    """Orchestrates clustering → dataset extraction → gap finding."""

    def __init__(self):
        self.clusterer = PaperClusterer()
        self.dataset_extractor = DatasetExtractor()
        self.gap_extractor = GapExtractor()

    async def run_full_pipeline(
        self,
        db: AsyncSession,
        task_id: str | None = None,
    ) -> dict:
        """Run complete clustering pipeline.

        Steps:
        1. PaperClusterer.run() — HDBSCAN clustering
        2. DatasetExtractor.extract_from_papers() — LLM dataset extraction
        3. GapExtractor.find_gaps_from_clusters() — find cluster-aware research gaps

        Returns:
            Combined summary from all steps.
        """
        logger.info("cluster_service_pipeline_started")
        if task_id:
            from app.api.routes.tasks import update_task_status

            update_task_status(
                task_id,
                "running",
                progress=15,
                message="Clustering embedded papers",
            )

        await self._reset_cluster_state(db)

        # Step 1: Cluster papers
        cluster_result = await self.clusterer.run(db)

        if task_id:
            from app.api.routes.tasks import update_task_status

            update_task_status(
                task_id,
                "running",
                progress=55,
                message="Extracting dataset and benchmark mentions",
            )

        # Step 2: Extract datasets
        dataset_result = await self.dataset_extractor.extract_from_papers(db)

        if task_id:
            from app.api.routes.tasks import update_task_status

            update_task_status(
                task_id,
                "running",
                progress=80,
                message="Persisting cluster-aware research gaps",
            )

        # Step 3: Find gaps from clusters
        gaps = await self.gap_extractor.find_gaps_from_clusters(db)

        # Persist new gaps
        gaps_persisted = 0
        for gap_dict in gaps:
            gap = Gap(
                gap_type=gap_dict.get("gap_type", "cluster_insight"),
                gap_description=gap_dict.get("description", ""),
                source_paper_ids=gap_dict.get("source_paper_ids", []),
                cluster_id=gap_dict.get("cluster_id"),
                similarity=gap_dict.get("similarity", 0.0),
                used=False,
            )
            db.add(gap)
            gaps_persisted += 1

        if gaps_persisted > 0:
            await db.commit()

        summary = {
            "clusters_created": cluster_result.get("clusters_created", 0),
            "papers_clustered": cluster_result.get("papers_clustered", 0),
            "datasets_found": dataset_result.get("datasets_found", 0),
            "gaps_found": gaps_persisted,
        }

        logger.info("cluster_service_pipeline_completed", **summary)
        return summary

    async def _reset_cluster_state(self, db: AsyncSession) -> None:
        """Clear cluster-derived state so reruns replace prior clustering output."""
        await db.execute(
            delete(Gap).where(
                Gap.gap_type == "cluster_insight"
            )
        )
        await db.execute(update(Paper).values(cluster_id=None))
        await db.execute(delete(PaperCluster))
        await db.commit()
