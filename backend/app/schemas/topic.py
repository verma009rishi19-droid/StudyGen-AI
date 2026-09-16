from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict

class TopicGenerateRequest(BaseModel):
    document_id: int

class ImportantTopicResult(BaseModel):
    topic: str
    explanation: str
    importance: str
    related_concepts: List[str]

class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    topic: str
    explanation: str
    importance: str
    related_concepts: List[str]
    created_at: datetime
