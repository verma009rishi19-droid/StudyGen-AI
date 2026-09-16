from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class GenerationHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    generation_type: str
    model_used: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
