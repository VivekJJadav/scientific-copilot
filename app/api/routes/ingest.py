from fastapi import APIRouter, BackgroundTasks, Depends
from app.api.routes.tasks import create_task, run_in_background
from app.ingestion.ingest_service import run_ingestion
from app.api.rate_limit import rate_limit

router = APIRouter()

@router.post("/arxiv")
async def ingest_arxiv(
    background_tasks: BackgroundTasks,
    limit: int = 2,
    _rate_limited: None = Depends(rate_limit()),
):
    task_id = create_task("ingest")
    background_tasks.add_task(run_in_background, task_id, run_ingestion, limit=limit)
    return {"task_id": task_id, "status": "queued"}
