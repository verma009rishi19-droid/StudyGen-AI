from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.projects import router as projects_router
from app.routes.documents import router as documents_router
from app.routes.summaries import router as summaries_router
from app.routes.topics import router as topics_router
from app.routes.question_papers import router as question_papers_router
from app.routes.quizzes import router as quizzes_router
from app.routes.generation import router as generation_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(documents_router)
api_router.include_router(summaries_router)
api_router.include_router(topics_router)
api_router.include_router(question_papers_router)
api_router.include_router(quizzes_router)
api_router.include_router(generation_router)

__all__ = ["api_router"]
