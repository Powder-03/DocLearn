"""
Chat Routes.

API endpoints for chat interactions with the AI tutor.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_chat_service
from app.services import ChatService
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatMessage,
    StartLessonRequest,
    StartLessonResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI tutor and receive a response.
    
    This is the main tutoring endpoint. The AI will:
    - Teach concepts one at a time
    - Ask questions to verify understanding
    - Adapt to user's pace and questions
    
    **Request Body:**
    - `session_id`: Session identifier
    - `message`: User's message to the tutor
    
    **Response:**
    - `response`: AI tutor's response
    - `current_day`: Current day in the lesson plan
    - `current_topic_index`: Current topic index
    - `is_day_complete`: Whether all topics for the day are done
    - `is_course_complete`: Whether the entire course is done
    """
    chat_service = get_chat_service(db)
    
    try:
        result = await chat_service.send_message(
            session_id=request.session_id,
            message=request.message,
        )
        
        return ChatResponse(
            session_id=request.session_id,
            response=result["response"],
            current_day=result["current_day"],
            current_topic_index=result["current_topic_index"],
            is_day_complete=result["is_day_complete"],
            is_course_complete=result["is_course_complete"],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/start-lesson", response_model=StartLessonResponse)
async def start_lesson(
    request: StartLessonRequest,
    db: Session = Depends(get_db),
):
    """
    Start or resume a lesson.
    
    If no day is specified, continues from the current day.
    If a day is specified, jumps to that day.
    
    Returns a welcome message and day objectives.
    """
    chat_service = get_chat_service(db)
    
    try:
        result = await chat_service.start_lesson(
            session_id=request.session_id,
            day=request.day,
        )
        
        return StartLessonResponse(
            session_id=request.session_id,
            current_day=result["current_day"],
            day_title=result["day_title"],
            objectives=result["objectives"],
            welcome_message=result["welcome_message"],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Start lesson error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start lesson: {str(e)}"
        )


@router.get("/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: UUID,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get chat history for a session.
    
    Returns the most recent messages up to the limit.
    """
    chat_service = get_chat_service(db)
    
    try:
        # Get session to include current day
        from app.api.deps import get_session_service
        session_service = get_session_service(db)
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        history = chat_service.get_chat_history(session_id, limit)
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=[
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg.get("timestamp"),
                )
                for msg in history
            ],
            total_messages=len(history),
            current_day=session.current_day,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
