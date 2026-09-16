from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class QuestionPaper(Base):
    __tablename__ = "question_papers"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    total_marks = Column(Integer, default=50, nullable=False)
    duration = Column(Integer, default=60, nullable=False)  # in minutes
    difficulty = Column(String(50), default="Medium", nullable=False)  # Easy, Medium, Hard
    question_type = Column(String(50), default="Mixed", nullable=False)  # MCQ, Short Answer, Long Answer, Mixed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="question_papers")
    document = relationship("Document", back_populates="question_papers")
    questions = relationship("Question", back_populates="question_paper", cascade="all, delete-orphan", order_by="Question.question_number")
    quiz_attempts = relationship("QuizAttempt", back_populates="question_paper", cascade="all, delete-orphan")
