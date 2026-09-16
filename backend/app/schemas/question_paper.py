from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class QuestionPaperConfig(BaseModel):
    project_id: int
    document_id: Optional[int] = None
    title: Optional[str] = "Generated Question Paper"
    num_questions: int = Field(default=5, ge=1, le=50)
    total_marks: int = Field(default=25, ge=5, le=100)
    difficulty: str = Field(default="Medium")
    question_type: str = Field(default="Mixed")
    duration: int = Field(default=30, ge=5, le=180)

class QuestionResult(BaseModel):
    question_number: int
    question_text: str
    question_type: str
    marks: int
    difficulty: str
    options: List[str] = []
    correct_answer: str
    explanation: str

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_paper_id: int
    question_number: int
    question_text: str
    question_type: str
    marks: int
    difficulty: str
    options: List[str]
    correct_answer: str
    explanation: str

class QuestionPaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    document_id: Optional[int]
    title: str
    total_marks: int
    duration: int
    difficulty: str
    question_type: str
    created_at: datetime
    questions: List[QuestionOut] = []
