from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.question_paper import QuestionPaper
from app.schemas.question_paper import QuestionPaperConfig, QuestionPaperOut
from app.schemas.common import MessageResponse
from app.services.study_service import StudyService
from app.utils.security import get_optional_user
from app.routes.projects import resolve_user

router = APIRouter(prefix="/question-papers", tags=["Question Papers"])

@router.post("/generate", response_model=QuestionPaperOut, status_code=status.HTTP_201_CREATED)
async def generate_question_paper(
    config: QuestionPaperConfig,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    return await StudyService.generate_question_paper(db, config, current_user.id)

@router.get("/project/{project_id}", response_model=List[QuestionPaperOut])
def list_question_papers(
    project_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied.")

    papers = db.query(QuestionPaper).filter(
        QuestionPaper.project_id == project.id
    ).order_by(QuestionPaper.created_at.desc()).all()

    return [QuestionPaperOut.model_validate(p) for p in papers]

@router.get("/{paper_id}", response_model=QuestionPaperOut)
def get_question_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    paper = db.query(QuestionPaper).join(Project).filter(
        QuestionPaper.id == paper_id,
        Project.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found or access denied.")

    return QuestionPaperOut.model_validate(paper)

@router.delete("/{paper_id}", response_model=MessageResponse)
def delete_question_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    paper = db.query(QuestionPaper).join(Project).filter(
        QuestionPaper.id == paper_id,
        Project.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found or access denied.")

    db.delete(paper)
    db.commit()
    return MessageResponse(message="Question paper deleted successfully.")
