"""
API Dependencies.

Provides dependency injection for API routes.
"""
from app.services import SessionService, ChatService, PlanService
from app.services.user_service import user_service, UserService
from app.core.auth import (
    verify_token,
    get_optional_user,
    get_current_user,
    require_verified_user,
    AuthUser,
)


# Create service instances (MongoDB-based, no DB session needed)
_session_service = SessionService()


def get_session_service() -> SessionService:
    """Get SessionService instance (MongoDB-based)."""
    return _session_service


def get_chat_service() -> ChatService:
    """Get ChatService instance."""
    return ChatService(_session_service)


def get_plan_service() -> PlanService:
    """Get PlanService instance."""
    return PlanService(_session_service)


def get_user_service() -> UserService:
    """Get UserService instance."""
    return user_service


# Re-export auth dependencies for convenience
__all__ = [
    "get_session_service",
    "get_chat_service",
    "get_plan_service",
    "get_user_service",
    "get_current_user",
    "get_optional_user",
    "require_verified_user",
    "verify_token",
    "AuthUser",
]
