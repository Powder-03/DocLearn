"""
Database Models for the Generation Mode Microservice.

This module defines SQLAlchemy ORM models for persisting learning sessions,
lesson plans, and chat history.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class SessionStatus(str, PyEnum):
    """Status of a learning session."""
    PLANNING = "PLANNING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SessionMode(str, PyEnum):
    """Mode of learning session."""
    GENERATION = "generation"
    RAG = "rag"


class LearningSession(Base):
    """
    Represents a user's learning journey.
    
    This is the central table that stores:
    - User's learning constraints (topic, days, time)
    - Generated lesson plan (JSON)
    - Chat history for context
    - Memory summary for LLM context compression
    - Current progress tracking
    """
    __tablename__ = "learning_sessions"

    # Primary Key
    session_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    
    # User Reference
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        index=True
    )
    
    # Session Configuration
    mode = Column(
        String(50), 
        nullable=False, 
        default=SessionMode.GENERATION.value,
        index=True
    )
    status = Column(
        String(50), 
        nullable=False, 
        default=SessionStatus.PLANNING.value,
        index=True
    )
    
    # Learning Parameters
    topic = Column(String(500), nullable=False)
    total_days = Column(Integer, nullable=False)
    time_per_day = Column(String(50), nullable=False)  # e.g., "1 hour", "30 minutes"
    
    # Generated Content
    lesson_plan = Column(JSONB, nullable=True)  # Complete curriculum JSON
    
    # Conversation State
    chat_history = Column(JSONB, nullable=True, default=list)  # List of message dicts
    memory_summary = Column(Text, nullable=True)  # Compressed context for LLM
    
    # Progress Tracking
    current_day = Column(Integer, nullable=False, default=1)
    current_topic_index = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<LearningSession("
            f"session_id={self.session_id}, "
            f"topic='{self.topic[:30]}...', "
            f"status='{self.status}', "
            f"day={self.current_day}/{self.total_days}"
            f")>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "session_id": str(self.session_id),
            "user_id": str(self.user_id),
            "mode": self.mode,
            "status": self.status,
            "topic": self.topic,
            "total_days": self.total_days,
            "time_per_day": self.time_per_day,
            "lesson_plan": self.lesson_plan,
            "current_day": self.current_day,
            "current_topic_index": self.current_topic_index,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
