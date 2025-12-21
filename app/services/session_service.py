"""
Session Service.

Business logic for managing learning sessions.
Separates database operations from API route handlers.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import LearningSession, SessionStatus, SessionMode

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service class for managing learning sessions.
    
    Handles all CRUD operations and business logic related to sessions.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the session service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    # =========================================================================
    # CREATE OPERATIONS
    # =========================================================================
    
    def create_session(
        self,
        user_id: uuid.UUID,
        topic: str,
        total_days: int,
        time_per_day: str,
        mode: str = SessionMode.GENERATION.value,
    ) -> LearningSession:
        """
        Create a new learning session.
        
        Args:
            user_id: User identifier
            topic: Learning topic
            total_days: Total days for the plan
            time_per_day: Daily time commitment
            mode: Session mode (generation or rag)
            
        Returns:
            Created LearningSession instance
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            session = LearningSession(
                user_id=user_id,
                topic=topic,
                total_days=total_days,
                time_per_day=time_per_day,
                mode=mode,
                status=SessionStatus.PLANNING.value,
                current_day=1,
                current_topic_index=0,
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Created session {session.session_id} for user {user_id}")
            return session
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    def get_session(self, session_id: uuid.UUID) -> Optional[LearningSession]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            LearningSession if found, None otherwise
        """
        return self.db.query(LearningSession).filter(
            LearningSession.session_id == session_id
        ).first()
    
    def get_session_or_raise(self, session_id: uuid.UUID) -> LearningSession:
        """
        Retrieve a session by ID or raise an exception.
        
        Args:
            session_id: Session identifier
            
        Returns:
            LearningSession instance
            
        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return session
    
    def get_user_sessions(
        self, 
        user_id: uuid.UUID,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[LearningSession]:
        """
        Get all sessions for a user with optional filtering.
        
        Args:
            user_id: User identifier
            mode: Filter by mode (optional)
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of LearningSession instances
        """
        query = self.db.query(LearningSession).filter(
            LearningSession.user_id == user_id
        )
        
        if mode:
            query = query.filter(LearningSession.mode == mode)
        
        if status:
            query = query.filter(LearningSession.status == status)
        
        return query.order_by(
            LearningSession.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    def count_user_sessions(
        self, 
        user_id: uuid.UUID,
        mode: Optional[str] = None,
    ) -> int:
        """Count total sessions for a user."""
        query = self.db.query(LearningSession).filter(
            LearningSession.user_id == user_id
        )
        
        if mode:
            query = query.filter(LearningSession.mode == mode)
        
        return query.count()
    
    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================
    
    def update_lesson_plan(
        self,
        session_id: uuid.UUID,
        lesson_plan: Dict[str, Any],
        status: str = SessionStatus.READY.value,
    ) -> Optional[LearningSession]:
        """
        Update the lesson plan for a session.
        
        Args:
            session_id: Session identifier
            lesson_plan: Generated lesson plan JSON
            status: New session status
            
        Returns:
            Updated LearningSession or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        try:
            session.lesson_plan = lesson_plan
            session.status = status
            session.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Updated lesson plan for session {session_id}")
            return session
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update lesson plan: {str(e)}")
            raise
    
    def update_progress(
        self,
        session_id: uuid.UUID,
        current_day: Optional[int] = None,
        current_topic_index: Optional[int] = None,
    ) -> Optional[LearningSession]:
        """
        Update learning progress.
        
        Args:
            session_id: Session identifier
            current_day: New current day (optional)
            current_topic_index: New topic index (optional)
            
        Returns:
            Updated LearningSession or None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        try:
            if current_day is not None:
                session.current_day = min(current_day, session.total_days)
            
            if current_topic_index is not None:
                session.current_topic_index = current_topic_index
            
            session.updated_at = datetime.utcnow()
            
            # Check if course is complete
            if session.current_day >= session.total_days:
                lesson_plan = session.lesson_plan or {}
                days = lesson_plan.get("days", [])
                if days:
                    last_day = days[-1]
                    topics = last_day.get("topics", [])
                    if session.current_topic_index >= len(topics) - 1:
                        session.status = SessionStatus.COMPLETED.value
                        session.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            return session
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update progress: {str(e)}")
            raise
    
    def advance_day(self, session_id: uuid.UUID) -> Optional[LearningSession]:
        """
        Move to the next day.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated LearningSession or None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        if session.current_day < session.total_days:
            return self.update_progress(
                session_id,
                current_day=session.current_day + 1,
                current_topic_index=0,
            )
        
        return session
    
    def advance_topic(self, session_id: uuid.UUID) -> Optional[LearningSession]:
        """
        Move to the next topic within the current day.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated LearningSession or None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return self.update_progress(
            session_id,
            current_topic_index=session.current_topic_index + 1,
        )
    
    def set_status(
        self,
        session_id: uuid.UUID,
        status: str,
    ) -> Optional[LearningSession]:
        """
        Update session status.
        
        Args:
            session_id: Session identifier
            status: New status value
            
        Returns:
            Updated LearningSession or None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        try:
            session.status = status
            session.updated_at = datetime.utcnow()
            
            if status == SessionStatus.COMPLETED.value:
                session.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            return session
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update status: {str(e)}")
            raise
    
    # =========================================================================
    # DELETE OPERATIONS
    # =========================================================================
    
    def delete_session(self, session_id: uuid.UUID) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        try:
            self.db.delete(session)
            self.db.commit()
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to delete session: {str(e)}")
            raise
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def calculate_progress_percentage(self, session: LearningSession) -> float:
        """
        Calculate completion percentage for a session.
        
        Args:
            session: LearningSession instance
            
        Returns:
            Progress percentage (0-100)
        """
        if not session.lesson_plan:
            return 0.0
        
        days = session.lesson_plan.get("days", [])
        if not days:
            return 0.0
        
        total_topics = sum(len(day.get("topics", [])) for day in days)
        if total_topics == 0:
            return 0.0
        
        # Count completed topics
        completed_topics = 0
        for i, day in enumerate(days):
            day_num = i + 1
            topics_in_day = len(day.get("topics", []))
            
            if day_num < session.current_day:
                # All topics in previous days are complete
                completed_topics += topics_in_day
            elif day_num == session.current_day:
                # Current day - count up to current topic
                completed_topics += min(session.current_topic_index, topics_in_day)
        
        return round((completed_topics / total_topics) * 100, 1)
