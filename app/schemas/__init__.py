"""
Schemas Package.

Contains Pydantic models for API request/response validation.
"""
from app.schemas.session import (
    CreatePlanRequest,
    CreatePlanResponse,
    SessionResponse,
    SessionListResponse,
    LessonPlanResponse,
    UpdateProgressRequest,
    ProgressResponse,
)
from app.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    StartLessonRequest,
    StartLessonResponse,
)

__all__ = [
    # Session schemas
    "CreatePlanRequest",
    "CreatePlanResponse",
    "SessionResponse",
    "SessionListResponse",
    "LessonPlanResponse",
    "UpdateProgressRequest",
    "ProgressResponse",
    # Chat schemas
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ChatHistoryResponse",
    "StartLessonRequest",
    "StartLessonResponse",
]
