from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_paper_id = Column(Integer, ForeignKey("question_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="MCQ", nullable=False)  # MCQ, Short Answer, Long Answer
    marks = Column(Integer, default=1, nullable=False)
    difficulty = Column(String(50), default="Medium", nullable=False)
    options = Column(JSON, default=list, nullable=False)  # list of strings for MCQs e.g. ["A...", "B...", ...]
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, default="", nullable=False)

    question_paper = relationship("QuestionPaper", back_populates="questions")
