"""Pydantic response schemas for feedback and clustering endpoints."""

import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExperimentResultResponse(BaseModel):
    id: uuid.UUID
    experiment_id: uuid.UUID
    hypothesis_id: uuid.UUID
    outcome: str
    metrics: dict
    result_summary: str
    lessons_learned: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackLoopResponse(BaseModel):
    experiments_analyzed: int
    new_gaps_from_failures: int
    arbiter_examples_updated: int
    new_hypotheses_generated: int


class ClusterResponse(BaseModel):
    id: str
    label: str
    top_terms: List[str]
    paper_count: int


class ClusterListResponse(BaseModel):
    clusters: List[ClusterResponse]
    total: int


class DatasetResponse(BaseModel):
    id: str
    name: str
    mention_count: int
    paper_count: int


class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int


class GapResponse(BaseModel):
    id: uuid.UUID
    gap_type: str
    gap_description: str
    source_paper_ids: List[str]
    cluster_id: Optional[uuid.UUID]
    similarity: float
    used: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
