"""
API Dependencies.

Provides dependency injection for API routes.
"""
from typing import Generator

from sqlalchemy.orm import Session

from app.db.session import get_session_local
from app.services import SessionService, ChatService, PlanService


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    
    Yields a database session and ensures proper cleanup.
    """
    db = get_session_local()
    try:
        yield db
    finally:
        db.close()


def get_session_service(db: Session) -> SessionService:
    """Get SessionService instance."""
    return SessionService(db)


def get_chat_service(db: Session) -> ChatService:
    """Get ChatService instance."""
    session_service = SessionService(db)
    return ChatService(session_service)


def get_plan_service(db: Session) -> PlanService:
    """Get PlanService instance."""
    session_service = SessionService(db)
    return PlanService(session_service)
