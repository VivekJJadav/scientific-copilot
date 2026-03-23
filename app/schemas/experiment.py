import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ExperimentResponse(BaseModel):
    id: uuid.UUID
    hypothesis_id: uuid.UUID
    status: str
    experiment_dir: str
    container_id: Optional[str]
    results: Optional[dict]
    result_summary: Optional[str]
    wandb_run_url: Optional[str]
    mlflow_run_id: Optional[str]
    error_log: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
class ExperimentListResponse(BaseModel):
    items: list[ExperimentResponse]
    total: int
