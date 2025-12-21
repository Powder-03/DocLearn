"""
Database Session Management.

Provides thread-safe database session creation and dependency injection
for FastAPI routes.
"""
import threading
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.db.models import Base


# Thread-safe singleton pattern for engine and sessionmaker
_engine = None
_SessionLocal = None
_lock = threading.Lock()


def get_engine():
    """Get or create the database engine (singleton)."""
    global _engine
    with _lock:
        if _engine is None:
            _engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=settings.DEBUG,
            )
    return _engine


def get_session_maker():
    """Get or create the session maker (singleton)."""
    global _SessionLocal
    with _lock:
        if _SessionLocal is None:
            engine = get_engine()
            _SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
    return _SessionLocal


def get_session_local() -> Session:
    """Create a new database session."""
    SessionLocal = get_session_maker()
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for FastAPI routes.
    
    Yields a database session and ensures proper cleanup.
    
    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = get_session_local()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            session = db.query(LearningSession).first()
    """
    db = get_session_local()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables. Use with caution!"""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
