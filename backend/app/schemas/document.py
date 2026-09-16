from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class DocumentCreate(BaseModel):
    project_id: int
    filename: Optional[str] = "Pasted Study Material.txt"
    content: str = Field(..., min_length=10)
    file_type: Optional[str] = "text"

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    filename: str
    file_type: str
    char_count: int
    created_at: datetime
    content: Optional[str] = None
