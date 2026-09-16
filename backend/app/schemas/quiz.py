from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict

class QuizAnswerItem(BaseModel):
    question_id: int
    user_answer: str

class QuizSubmitRequest(BaseModel):
    question_paper_id: int
    answers: List[QuizAnswerItem]

class QuizQuestionEvaluation(BaseModel):
    question_id: int
    question_number: int
    question_text: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str

class QuizAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    question_paper_id: int
    score: float
    total_questions: int
    correct_count: int
    incorrect_count: int
    percentage: float
    details: List[Any]
    completed_at: datetime
