from app.schemas.auth import UserRegister, UserLogin, Token, UserOut
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectDetailOut
from app.schemas.document import DocumentCreate, DocumentOut
from app.schemas.summary import SummaryGenerateRequest, SummaryResult, SummaryOut
from app.schemas.topic import TopicGenerateRequest, ImportantTopicResult, TopicOut
from app.schemas.question_paper import QuestionPaperConfig, QuestionResult, QuestionOut, QuestionPaperOut
from app.schemas.quiz import QuizSubmitRequest, QuizAnswerItem, QuizAttemptOut, QuizQuestionEvaluation
from app.schemas.history import GenerationHistoryOut
from app.schemas.common import MessageResponse

__all__ = [
    "UserRegister",
    "UserLogin",
    "Token",
    "UserOut",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectOut",
    "ProjectDetailOut",
    "DocumentCreate",
    "DocumentOut",
    "SummaryGenerateRequest",
    "SummaryResult",
    "SummaryOut",
    "TopicGenerateRequest",
    "ImportantTopicResult",
    "TopicOut",
    "QuestionPaperConfig",
    "QuestionResult",
    "QuestionOut",
    "QuestionPaperOut",
    "QuizSubmitRequest",
    "QuizAnswerItem",
    "QuizAttemptOut",
    "QuizQuestionEvaluation",
    "GenerationHistoryOut",
    "MessageResponse",
]
