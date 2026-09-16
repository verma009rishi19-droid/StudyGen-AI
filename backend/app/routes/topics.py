from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.topic import ImportantTopic
from app.schemas.topic import TopicGenerateRequest, TopicOut
from app.services.study_service import StudyService
from app.utils.security import get_optional_user
from app.routes.projects import resolve_user

router = APIRouter(prefix="/topics", tags=["Important Topics"])

@router.post("/generate", response_model=List[TopicOut])
async def generate_topics(
    request: TopicGenerateRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    return await StudyService.generate_topics_for_document(db, request.document_id, current_user.id)

@router.get("/document/{document_id}", response_model=List[TopicOut])
def get_topics_by_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    topics = db.query(ImportantTopic).join(Document).join(Project).filter(
        ImportantTopic.document_id == document_id,
        Project.user_id == current_user.id
    ).all()

    return [TopicOut.model_validate(t) for t in topics]
