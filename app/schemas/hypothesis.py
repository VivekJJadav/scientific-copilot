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
    # Phase 3 Fields
    debate_rounds: Optional[int] = None
    arbiter_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    parent_hypothesis_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HypothesisListResponse(BaseModel):
    items: List[HypothesisResponse]
    total: int
