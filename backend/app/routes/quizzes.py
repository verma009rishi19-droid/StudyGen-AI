from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.quiz import QuizAttempt
from app.models.question_paper import QuestionPaper
from app.models.project import Project
from app.schemas.quiz import QuizSubmitRequest, QuizAttemptOut
from app.services.quiz_service import QuizService
from app.utils.security import get_optional_user
from app.routes.projects import resolve_user

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])

@router.post("/submit", response_model=QuizAttemptOut)
def submit_quiz_answers(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    return QuizService.evaluate_quiz(db, request, current_user.id)

@router.get("/paper/{paper_id}/attempts", response_model=List[QuizAttemptOut])
def get_paper_quiz_attempts(
    paper_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.question_paper_id == paper_id,
        QuizAttempt.user_id == current_user.id
    ).order_by(QuizAttempt.completed_at.desc()).all()

    return [QuizAttemptOut.model_validate(a) for a in attempts]

@router.get("/attempts/{attempt_id}", response_model=QuizAttemptOut)
def get_quiz_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.id == attempt_id,
        QuizAttempt.user_id == current_user.id
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found or access denied.")

    return QuizAttemptOut.model_validate(attempt)
