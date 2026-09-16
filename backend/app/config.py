import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or backend directory if present
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_paths = [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break
else:
    load_dotenv()


class Settings:
    PROJECT_NAME: str = "StudyGen AI"
    PROJECT_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/studygen_ai")
    SQLITE_URL: str = os.getenv("SQLITE_URL", "sqlite:///./studygen.db")
    USE_SQLITE_FALLBACK: bool = os.getenv("USE_SQLITE_FALLBACK", "True").lower() in ("true", "1", "yes")

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "studygen-ai-secure-secret-key-2026-production-ready")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

    # AI Configuration - Default to Gemini API
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini").lower()  # 'gemini', 'ollama', or 'openai'
    
    # Google Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Ollama Local LLM Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # OpenAI Cloud LLM Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Document upload limits
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    MAX_CONTENT_CHARS: int = int(os.getenv("MAX_CONTENT_CHARS", "150000"))

    # CORS
    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()
