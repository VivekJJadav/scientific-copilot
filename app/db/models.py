import uuid
from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, desc
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
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=datetime.utcnow))
