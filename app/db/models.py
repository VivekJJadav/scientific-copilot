import uuid
from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel
from pgvector.sqlalchemy import Vector


class Paper(SQLModel, table=True):
    __tablename__ = "papers"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    arxiv_id: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    title: str = Field(nullable=False)
    abstract: str = Field(nullable=False)
    authors: List[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSONB))
    published_year: int
    pdf_url: str
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(Vector(384)))
    arxiv_status: str = Field(default="raw")
    cluster_id: Optional[uuid.UUID] = Field(default=None, foreign_key="paper_clusters.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=datetime.utcnow))


class HypothesisModel(SQLModel, table=True):
    __tablename__ = "hypotheses"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(sa_column=Column(Text, nullable=False))
    motivation: str = Field(sa_column=Column(Text, nullable=False))
    core_claim: str = Field(sa_column=Column(Text, nullable=False))
    method_sketch: str = Field(sa_column=Column(Text, nullable=False))
    expected_outcome: str = Field(sa_column=Column(Text, nullable=False))
    risk_factors: List[str] = Field(default_factory=list, sa_column=Column(JSONB))
    novelty_score: float = Field(default=0.0, sa_column=Column(Float, nullable=False))
    feasibility_score: float = Field(default=0.0, sa_column=Column(Float, nullable=False))
    hardware_requirement: str = Field(default="")
    source_paper_ids: List[str] = Field(default_factory=list, sa_column=Column(JSONB))
    gap_description: str = Field(sa_column=Column(Text, nullable=False))
    status: str = Field(default="pending")
    iteration_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    parent_hypothesis_id: Optional[uuid.UUID] = Field(default=None, sa_column=Column(String, nullable=True))

    # Phase 3 Fields
    approved_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    rejection_reason: Optional[str] = Field(default=None, sa_column=Column(Text))
    debate_rounds: Optional[int] = Field(default=None, sa_column=Column(Integer))
    arbiter_notes: Optional[str] = Field(default=None, sa_column=Column(Text))

    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=datetime.utcnow))


class Experiment(SQLModel, table=True):
    __tablename__ = "experiments"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hypothesis_id: uuid.UUID = Field(foreign_key="hypotheses.id", nullable=False)
    status: str = Field(default="queued")
    experiment_dir: str = Field(nullable=False)
    container_id: Optional[str] = Field(default=None)
    results: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    result_summary: Optional[str] = Field(default=None, sa_column=Column(Text))
    wandb_run_url: Optional[str] = Field(default=None)
    mlflow_run_id: Optional[str] = Field(default=None)
    error_log: Optional[str] = Field(default=None, sa_column=Column(Text))
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))


class PaperCluster(SQLModel, table=True):
    __tablename__ = "paper_clusters"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    label: str = Field(nullable=False)
    top_terms: List[str] = Field(default_factory=list, sa_column=Column(JSONB))
    paper_ids: List[str] = Field(default_factory=list, sa_column=Column(JSONB))
    centroid_embedding: Optional[List[float]] = Field(default=None, sa_column=Column(Vector(384)))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))


class ExperimentResult(SQLModel, table=True):
    __tablename__ = "experiment_results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    experiment_id: uuid.UUID = Field(foreign_key="experiments.id", nullable=False)
    hypothesis_id: uuid.UUID = Field(foreign_key="hypotheses.id", nullable=False)
    outcome: str = Field(nullable=False)  # validated / failed / inconclusive
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    result_summary: str = Field(sa_column=Column(Text, nullable=False))
    lessons_learned: List[str] = Field(default_factory=list, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))


class Gap(SQLModel, table=True):
    __tablename__ = "gaps"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    gap_type: str = Field(nullable=False)
    gap_description: str = Field(sa_column=Column(Text, nullable=False))
    source_paper_ids: List[str] = Field(default_factory=list, sa_column=Column(JSONB))
    cluster_id: Optional[uuid.UUID] = Field(default=None, foreign_key="paper_clusters.id")
    similarity: float = Field(default=0.0)
    used: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default="false"))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))


class DatasetRegistry(SQLModel, table=True):
    __tablename__ = "dataset_registry"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    mention_count: int = Field(default=0)
    paper_ids: List[str] = Field(default_factory=list, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=datetime.utcnow))
