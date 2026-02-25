"""
Pydantic Schemas for Learning Sessions.

Defines request/response models for session-related API endpoints.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class CreatePlanRequest(BaseModel):
    """Request model for creating a new learning plan.
    
    Note: user_id is extracted from the JWT token, not from the request body.
    """
    topic: str = Field(
        ..., 
        min_length=3, 
        max_length=500,
        description="Topic to learn",
        examples=["Quantum Computing", "Machine Learning Basics"]
    )
    total_days: int = Field(
        default=7, 
        ge=1, 
        le=90,
        description="Number of days for the learning plan"
    )
    time_per_day: str = Field(
        default="1 hour", 
        description="Time commitment per day",
        examples=["1 hour", "30 minutes", "2 hours"]
    )
    mode: str = Field(
        default="generation",
        description="Learning mode: 'generation', 'quick', 'dsa_leetcode', or 'dsa_other'"
    )
    target: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Learning goal or target (e.g., exam prep, career switch, project-based)",
        examples=["GATE exam", "Job interview prep", "Build a portfolio project", "Quick revision"]
    )
    # DSA mode fields
    question_number: Optional[int] = Field(
        default=None,
        description="LeetCode question number (for dsa_leetcode mode)"
    )
    programming_language: Optional[str] = Field(
        default=None,
        description="Programming language for DSA mode",
        examples=["python", "java", "cpp", "javascript"]
    )
    question_text: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Full question text (for dsa_other mode)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Machine Learning",
                "total_days": 14,
                "time_per_day": "1 hour",
                "mode": "generation",
                "target": None
            }
        }


class CreatePlanResponse(BaseModel):
    """Response model after creating a learning plan."""
    session_id: UUID
    status: str
    message: str
    lesson_plan: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "READY",
                "message": "Your learning plan is ready!"
            }
        }


class SessionResponse(BaseModel):
    """Response model for session details."""
    session_id: UUID
    user_id: str  # User IDs are UUIDs stored as strings
    topic: str
    total_days: int
    time_per_day: str
    current_day: int
    current_topic_index: int
    status: str
    mode: str
    target: Optional[str] = None
    programming_language: Optional[str] = None
    question_number: Optional[int] = None
    leetcode_data: Optional[Dict[str, Any]] = None
    lesson_plan: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Response model for listing user sessions."""
    sessions: List[SessionResponse]
    total: int


class LessonPlanResponse(BaseModel):
    """Response model for lesson plan details."""
    session_id: UUID
    topic: str
    lesson_plan: Dict[str, Any]
    current_day: int
    total_days: int
    progress_percentage: float = Field(..., description="Completion percentage")


class UpdateProgressRequest(BaseModel):
    """Request model for updating session progress."""
    current_day: Optional[int] = Field(None, ge=1, description="Set current day")
    current_topic_index: Optional[int] = Field(None, ge=0, description="Set current topic index")


class ProgressResponse(BaseModel):
    """Response model for progress updates."""
    session_id: UUID
    current_day: int
    current_topic_index: int
    total_days: int
    is_complete: bool
    progress_percentage: float
