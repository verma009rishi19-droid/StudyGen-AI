from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.history import GenerationHistory
from app.schemas.history import GenerationHistoryOut
from app.utils.security import get_optional_user
from app.routes.projects import resolve_user

router = APIRouter(prefix="/generation", tags=["Generation History & AI Status"])

@router.get("/project/{project_id}", response_model=List[GenerationHistoryOut])
def get_project_generation_history(
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

    logs = db.query(GenerationHistory).filter(
        GenerationHistory.project_id == project.id
    ).order_by(GenerationHistory.created_at.desc()).all()

    return [GenerationHistoryOut.model_validate(log) for log in logs]

@router.get("/status")
def get_ai_status() -> Dict[str, Any]:
    active_provider = settings.AI_PROVIDER.lower()
    has_gemini_key = bool(
        settings.GEMINI_API_KEY
        and len(settings.GEMINI_API_KEY.strip()) > 5
        and settings.GEMINI_API_KEY.strip() != "your_gemini_api_key_here"
    )
    has_openai_key = bool(
        settings.OPENAI_API_KEY
        and len(settings.OPENAI_API_KEY.strip()) > 5
        and settings.OPENAI_API_KEY.strip() != "your_openai_api_key_here"
    )
    
    return {
        "active_provider": active_provider,
        "gemini_configured": has_gemini_key,
        "gemini_model": settings.GEMINI_MODEL,
        "ollama_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "openai_configured": has_openai_key,
        "openai_model": settings.OPENAI_MODEL,
        "fallback_available": True
    }
