import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from app.db.session import get_session
from app.db.models import Experiment
from app.execution.template_runner import TemplateRunner
from app.schemas.experiment import ExperimentListResponse, ExperimentResponse
from app.api.routes.tasks import create_task, run_in_background
from app.api.rate_limit import rate_limit

router = APIRouter()
runner = TemplateRunner()

async def _run_experiments_task(db: AsyncSession, task_id: str | None = None):
    return await runner.run_approved(db, task_id=task_id)

@router.post("/run")
async def run_experiments(
    background_tasks: BackgroundTasks,
    _rate_limited: None = Depends(rate_limit()),
):
    task_id = create_task("run")
    background_tasks.add_task(run_in_background, task_id, _run_experiments_task)
    return {"task_id": task_id, "status": "queued"}

@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_session)
):
    count_stmt = select(func.count()).select_from(Experiment)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = select(Experiment).order_by(desc(Experiment.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    experiments = result.scalars().all()

    items = [
        ExperimentResponse(
            id=e.id,
            hypothesis_id=e.hypothesis_id,
            status=e.status,
            experiment_dir=e.experiment_dir,
            container_id=e.container_id,
            results=e.results,
            result_summary=e.result_summary,
            wandb_run_url=e.wandb_run_url,
            mlflow_run_id=e.mlflow_run_id,
            error_log=e.error_log,
            started_at=e.started_at,
            completed_at=e.completed_at,
            created_at=e.created_at,
        ) for e in experiments
    ]
    return {"items": items, "total": total}

@router.get("/{id}", response_model=ExperimentResponse)
async def get_experiment(id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    experiment = await db.get(Experiment, id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    return ExperimentResponse(
        id=experiment.id,
        hypothesis_id=experiment.hypothesis_id,
        status=experiment.status,
        experiment_dir=experiment.experiment_dir,
        container_id=experiment.container_id,
        results=experiment.results,
        result_summary=experiment.result_summary,
        wandb_run_url=experiment.wandb_run_url,
        mlflow_run_id=experiment.mlflow_run_id,
        error_log=experiment.error_log,
        started_at=experiment.started_at,
        completed_at=experiment.completed_at,
        created_at=experiment.created_at,
    )
