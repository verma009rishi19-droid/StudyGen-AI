from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_paper_id = Column(Integer, ForeignKey("question_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, default=0.0, nullable=False)
    total_questions = Column(Integer, default=0, nullable=False)
    correct_count = Column(Integer, default=0, nullable=False)
    incorrect_count = Column(Integer, default=0, nullable=False)
    percentage = Column(Float, default=0.0, nullable=False)
    details = Column(JSON, default=list, nullable=False)  # list of question answers with user response, correctness, explanation
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="quiz_attempts")
    question_paper = relationship("QuestionPaper", back_populates="quiz_attempts")
