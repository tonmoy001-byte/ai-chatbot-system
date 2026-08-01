from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_SessionLocal = None


def _create_engine(url: str):
    """Create engine configured for Supabase PostgreSQL or SQLite (testing)."""
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})

    logger.info("Connecting to Supabase database")

    if ":6543/" in url:
        engine = create_engine(
            url,
            poolclass=NullPool,
            connect_args={"sslmode": "require"},
        )
    else:
        engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
            pool_pre_ping=True,
            connect_args={"sslmode": "require"},
        )
    return engine


def get_engine():
    """Lazily create and return the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        if not settings.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not set. "
                "Please configure your Supabase connection string in .env"
            )
        _engine = _create_engine(settings.DATABASE_URL)
    return _engine


def get_session_local():
    """Lazily create and return the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal


class _LazySessionLocal:
    """Proxy that behaves like SessionLocal but creates sessions lazily."""

    def __call__(self):
        return get_session_local()()


SessionLocal = _LazySessionLocal()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
