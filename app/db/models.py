import uuid
from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import Column, DateTime, String, desc
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
