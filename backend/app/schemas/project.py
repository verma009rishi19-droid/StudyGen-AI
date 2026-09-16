from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    subject: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=1000)

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    name: str
    subject: str
    description: str
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0
    question_paper_count: Optional[int] = 0

class ProjectDetailOut(ProjectOut):
    pass
