from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.summary import Summary
from app.schemas.summary import SummaryGenerateRequest, SummaryOut
from app.services.study_service import StudyService
from app.utils.security import get_optional_user
from app.routes.projects import resolve_user

router = APIRouter(prefix="/summaries", tags=["Summaries"])

@router.post("/generate", response_model=SummaryOut)
async def generate_summary(
    request: SummaryGenerateRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    return await StudyService.generate_summary_for_document(db, request.document_id, current_user.id)

@router.get("/document/{document_id}", response_model=SummaryOut)
def get_summary_by_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    summary = db.query(Summary).join(Document).join(Project).filter(
        Summary.document_id == document_id,
        Project.user_id == current_user.id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="No summary found for this document.")

    return SummaryOut.model_validate(summary)
