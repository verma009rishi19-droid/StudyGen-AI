from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.question_paper import QuestionPaper
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectDetailOut
from app.schemas.common import MessageResponse
from app.utils.security import get_current_user, get_optional_user

router = APIRouter(prefix="/projects", tags=["Projects"])

def resolve_user(db: Session, optional_user: User | None) -> User:
    if optional_user:
        return optional_user
    # Demo/Default user fallback for quick evaluation without friction
    demo_email = "demo@studygen.ai"
    demo_user = db.query(User).filter(User.email == demo_email).first()
    if not demo_user:
        from app.utils.security import get_password_hash
        demo_user = User(
            name="Demo Student",
            email=demo_email,
            password_hash=get_password_hash("studygen123")
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
    return demo_user

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    request: ProjectCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    project = Project(
        user_id=current_user.id,
        name=request.name.strip(),
        subject=request.subject.strip(),
        description=(request.description or "").strip()
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    out = ProjectOut.model_validate(project)
    out.document_count = 0
    out.question_paper_count = 0
    return out

@router.get("", response_model=List[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.updated_at.desc()).all()
    
    results = []
    for p in projects:
        out = ProjectOut.model_validate(p)
        out.document_count = db.query(Document).filter(Document.project_id == p.id).count()
        out.question_paper_count = db.query(QuestionPaper).filter(QuestionPaper.project_id == p.id).count()
        results.append(out)
    return results

@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied."
        )

    out = ProjectDetailOut.model_validate(project)
    out.document_count = db.query(Document).filter(Document.project_id == project.id).count()
    out.question_paper_count = db.query(QuestionPaper).filter(QuestionPaper.project_id == project.id).count()
    return out

@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    request: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied."
        )

    if request.name is not None:
        project.name = request.name.strip()
    if request.subject is not None:
        project.subject = request.subject.strip()
    if request.description is not None:
        project.description = request.description.strip()

    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)

@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied."
        )

    db.delete(project)
    db.commit()
    return MessageResponse(message="Project deleted successfully.")
