"""API routes for paper clustering and dataset registry."""

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func

from app.db.session import get_session
from app.db.models import PaperCluster, DatasetRegistry
from app.clustering.cluster_service import ClusterService
from app.clustering.dataset_extractor import DatasetExtractor

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/run")
async def run_clustering(db: AsyncSession = Depends(get_session)):
    """Run full clustering pipeline: HDBSCAN → dataset extraction → gap finding.

    Returns:
        {clusters_created, papers_clustered, datasets_found, gaps_found}
    """
    service = ClusterService()
    result = await service.run_full_pipeline(db)
    return result


@router.get("/clusters")
async def list_clusters(db: AsyncSession = Depends(get_session)):
    """List all paper clusters with label, top_terms, and paper count."""
    stmt = select(PaperCluster).order_by(desc(PaperCluster.created_at))
    clusters = (await db.execute(stmt)).scalars().all()

    return {
        "clusters": [
            {
                "id": str(c.id),
                "label": c.label,
                "top_terms": c.top_terms,
                "paper_ids": c.paper_ids or [],
                "paper_count": len(c.paper_ids) if c.paper_ids else 0,
            }
            for c in clusters
        ],
        "total": len(clusters),
    }


@router.post("/extract-datasets")
async def extract_datasets(db: AsyncSession = Depends(get_session)):
    """Run dataset extraction only, without re-clustering.

    Returns:
        {datasets_found, new_entries, updated_entries}
    """
    extractor = DatasetExtractor()
    result = await extractor.extract_from_papers(db)
    return result


@router.get("/datasets")
async def list_datasets(db: AsyncSession = Depends(get_session)):
    """List all entries in dataset_registry ordered by mention_count DESC."""
    stmt = select(DatasetRegistry).order_by(desc(DatasetRegistry.mention_count))
    datasets = (await db.execute(stmt)).scalars().all()

    return {
        "datasets": [
            {
                "id": str(d.id),
                "name": d.name,
                "mention_count": d.mention_count,
                "paper_count": len(d.paper_ids) if d.paper_ids else 0,
            }
            for d in datasets
        ],
        "total": len(datasets),
    }
