import uuid
from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class PaperResponse(BaseModel):
    id: uuid.UUID
    arxiv_id: str
    title: str
    abstract: str
    authors: List[dict[str, Any]]
    published_year: int
    pdf_url: str
    embedding: Optional[List[float]] = None
    arxiv_status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaperListResponse(BaseModel):
    items: List[PaperResponse]
    total: int
