from pydantic import BaseModel
from typing import Optional, Any

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
    data: Optional[Any] = None
