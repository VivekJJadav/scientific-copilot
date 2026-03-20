"""Pydantic response schemas for hypotheses."""

import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HypothesisResponse(BaseModel):
    id: uuid.UUID
    title: str
    motivation: str
    core_claim: str
    method_sketch: str
    expected_outcome: str
    risk_factors: List[str]
    novelty_score: float
    feasibility_score: float
    hardware_requirement: str
    source_paper_ids: List[str]
    gap_description: str
    status: str
    iteration_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HypothesisListResponse(BaseModel):
    items: List[HypothesisResponse]
    total: int
