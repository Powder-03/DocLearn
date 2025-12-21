"""
Pydantic Schemas for Chat Operations.

Defines request/response models for chat-related API endpoints.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Represents a single chat message."""
    role: str = Field(..., description="Message role: 'human' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request model for sending a chat message."""
    session_id: UUID = Field(..., description="Session identifier")
    message: str = Field(
        ..., 
        min_length=1,
        max_length=5000,
        description="User's message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "What is a neural network?"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    session_id: UUID
    response: str = Field(..., description="AI tutor's response")
    current_day: int
    current_topic_index: int
    is_day_complete: bool = False
    is_course_complete: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "response": "Great question! A neural network is...",
                "current_day": 1,
                "current_topic_index": 0,
                "is_day_complete": False,
                "is_course_complete": False
            }
        }


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    session_id: UUID
    messages: List[ChatMessage]
    total_messages: int
    current_day: int


class StartLessonRequest(BaseModel):
    """Request model for starting a lesson (Day N)."""
    session_id: UUID = Field(..., description="Session identifier")
    day: Optional[int] = Field(
        None, 
        ge=1,
        description="Day to start. If not provided, continues from current day."
    )


class StartLessonResponse(BaseModel):
    """Response model for starting a lesson."""
    session_id: UUID
    current_day: int
    day_title: str
    objectives: List[str]
    welcome_message: str
