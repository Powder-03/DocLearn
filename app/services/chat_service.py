"""
Chat Service.

Business logic for handling chat interactions with the AI tutor.
Orchestrates the LangGraph execution and state management.
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage

from app.db.models import LearningSession, SessionStatus
from app.services.session_service import SessionService
from app.graphs import invoke_generation_graph, create_initial_state

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service class for handling chat interactions.
    
    Manages the conversation flow between users and the AI tutor,
    including graph invocation and state persistence.
    """
    
    def __init__(self, session_service: SessionService):
        """
        Initialize the chat service.
        
        Args:
            session_service: SessionService instance for data access
        """
        self.session_service = session_service
    
    async def send_message(
        self,
        session_id: UUID,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send a message to the AI tutor and get a response.
        
        Args:
            session_id: Session identifier
            message: User's message
            
        Returns:
            Dictionary containing:
                - response: AI's response
                - current_day: Current day number
                - current_topic_index: Current topic index
                - is_day_complete: Whether day is complete
                - is_course_complete: Whether course is complete
                
        Raises:
            ValueError: If session not found or not ready
        """
        # Get session
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status not in [SessionStatus.READY.value, SessionStatus.IN_PROGRESS.value]:
            raise ValueError(f"Session is not ready for chat. Status: {session.status}")
        
        # Update status to in progress if needed
        if session.status == SessionStatus.READY.value:
            self.session_service.set_status(session_id, SessionStatus.IN_PROGRESS.value)
        
        # Build graph state from session
        state = self._build_state_from_session(session, message)
        
        # Invoke the graph
        result = await invoke_generation_graph(state)
        
        # Persist the updated chat history
        if result.get("ai_response"):
            self.session_service.append_to_chat_history(
                session_id=session_id,
                human_message=message,
                ai_message=result["ai_response"],
            )
        
        # Handle topic advancement
        if result.get("should_advance_topic"):
            self.session_service.advance_topic(session_id)
        
        # Handle day completion
        if result.get("is_day_complete"):
            if not result.get("is_course_complete"):
                # Move to next day
                self.session_service.advance_day(session_id)
        
        # Handle course completion
        if result.get("is_course_complete"):
            self.session_service.set_status(session_id, SessionStatus.COMPLETED.value)
        
        # Refresh session for latest state
        session = self.session_service.get_session(session_id)
        
        return {
            "response": result.get("ai_response", ""),
            "current_day": session.current_day,
            "current_topic_index": session.current_topic_index,
            "is_day_complete": result.get("is_day_complete", False),
            "is_course_complete": result.get("is_course_complete", False),
        }
    
    async def start_lesson(
        self,
        session_id: UUID,
        day: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Start or resume a lesson for a specific day.
        
        Args:
            session_id: Session identifier
            day: Day number to start (optional, defaults to current day)
            
        Returns:
            Dictionary with lesson info and welcome message
            
        Raises:
            ValueError: If session not found or invalid day
        """
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status == SessionStatus.PLANNING.value:
            raise ValueError("Lesson plan is still being generated")
        
        # Set day if specified
        if day is not None:
            if day < 1 or day > session.total_days:
                raise ValueError(f"Day must be between 1 and {session.total_days}")
            self.session_service.update_progress(session_id, current_day=day, current_topic_index=0)
            session = self.session_service.get_session(session_id)
        
        # Get day content
        lesson_plan = session.lesson_plan or {}
        days = lesson_plan.get("days", [])
        
        if session.current_day <= len(days):
            day_content = days[session.current_day - 1]
        else:
            day_content = {}
        
        # Build state and invoke graph for welcome message
        state = self._build_state_from_session(session, user_message=None)
        result = await invoke_generation_graph(state)
        
        # Persist the welcome message
        if result.get("ai_response"):
            self.session_service.append_to_chat_history(
                session_id=session_id,
                human_message="[Started lesson]",
                ai_message=result["ai_response"],
            )
        
        return {
            "current_day": session.current_day,
            "day_title": day_content.get("title", f"Day {session.current_day}"),
            "objectives": day_content.get("objectives", []),
            "welcome_message": result.get("ai_response", ""),
        }
    
    def get_chat_history(
        self,
        session_id: UUID,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum messages to return
            
        Returns:
            List of message dictionaries
            
        Raises:
            ValueError: If session not found
        """
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        history = session.chat_history or []
        return history[-limit:]
    
    def _build_state_from_session(
        self,
        session: LearningSession,
        user_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build graph state from a session model.
        
        Args:
            session: LearningSession instance
            user_message: Current user message (optional)
            
        Returns:
            Graph state dictionary
        """
        # Convert stored chat history to LangChain messages
        chat_history = self._convert_history_to_messages(session.chat_history or [])
        
        return create_initial_state(
            session_id=str(session.session_id),
            user_id=str(session.user_id),
            topic=session.topic,
            total_days=session.total_days,
            time_per_day=session.time_per_day,
            lesson_plan=session.lesson_plan,
            current_day=session.current_day,
            current_topic_index=session.current_topic_index,
            chat_history=chat_history,
            memory_summary=session.memory_summary,
        ) | {"user_message": user_message}
    
    def _convert_history_to_messages(
        self,
        history: List[Dict[str, Any]],
    ) -> List:
        """
        Convert stored chat history to LangChain message objects.
        
        Args:
            history: List of message dictionaries
            
        Returns:
            List of LangChain message objects
        """
        messages = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        
        return messages
