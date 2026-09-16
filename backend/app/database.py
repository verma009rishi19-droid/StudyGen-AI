import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger("studygen.database")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

def create_db_engine():
    """
    Creates the SQLAlchemy engine for PostgreSQL.
    If PostgreSQL is unreachable or fails authentication and fallback is enabled,
    gracefully falls back to SQLite for local development/testing.
    """
    db_url = settings.DATABASE_URL
    connect_args = {}

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        return create_engine(db_url, connect_args=connect_args)

    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 3} if "psycopg2" in db_url or "postgresql" in db_url else {}
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to PostgreSQL successfully.")
        return engine
    except Exception as exc:
        logger.warning(
            f"Could not connect to PostgreSQL ({settings.DATABASE_URL}): {exc}."
        )
        if settings.USE_SQLITE_FALLBACK:
            logger.warning(f"Falling back to local SQLite database: {settings.SQLITE_URL}")
            fallback_engine = create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False}
            )
            return fallback_engine
        raise exc

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency that yields a database session and safely closes it.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes all database tables defined in models.
    """
    # Import models so Base has metadata registered
    import app.models  # noqa
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
