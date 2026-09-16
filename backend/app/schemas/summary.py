from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict

class SummaryGenerateRequest(BaseModel):
    document_id: int

class SummaryResult(BaseModel):
    summary: str
    key_concepts: List[str]
    important_topics: List[str]
    quick_revision: List[str]

class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    summary: str
    key_concepts: List[str]
    important_topics: List[str]
    quick_revision: List[str]
    created_at: datetime
