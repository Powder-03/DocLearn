"""
Session Routes.

API endpoints for managing learning sessions.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_session_service, get_plan_service
from app.services import SessionService, PlanService
from app.schemas import (
    CreatePlanRequest,
    CreatePlanResponse,
    SessionResponse,
    SessionListResponse,
    LessonPlanResponse,
    UpdateProgressRequest,
    ProgressResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=CreatePlanResponse, status_code=201)
async def create_session(
    request: CreatePlanRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new learning session and generate a lesson plan.
    
    This endpoint:
    1. Creates a new LearningSession in the database
    2. Invokes the AI to generate the curriculum
    3. Returns the session_id for subsequent interactions
    
    **Request Body:**
    - `user_id`: User identifier
    - `topic`: Topic to learn (e.g., "Machine Learning Basics")
    - `total_days`: Number of days (1-90)
    - `time_per_day`: Daily time commitment (e.g., "1 hour")
    """
    plan_service = get_plan_service(db)
    
    try:
        result = await plan_service.create_plan(
            user_id=request.user_id,
            topic=request.topic,
            total_days=request.total_days,
            time_per_day=request.time_per_day,
        )
        
        return CreatePlanResponse(
            session_id=result["session_id"],
            status=result["status"],
            message=result["message"],
            lesson_plan=result.get("lesson_plan"),
        )
        
    except Exception as e:
        logger.exception(f"Failed to create session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create learning plan: {str(e)}"
        )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: UUID = Query(..., description="User identifier"),
    mode: Optional[str] = Query(None, description="Filter by mode"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """
    List all learning sessions for a user.
    
    Supports filtering by mode and status, with pagination.
    """
    session_service = get_session_service(db)
    
    sessions = session_service.get_user_sessions(
        user_id=user_id,
        mode=mode,
        status=status,
        limit=limit,
        offset=offset,
    )
    
    total = session_service.count_user_sessions(user_id, mode)
    
    return SessionListResponse(
        sessions=[
            SessionResponse(
                session_id=s.session_id,
                user_id=s.user_id,
                topic=s.topic,
                total_days=s.total_days,
                time_per_day=s.time_per_day,
                current_day=s.current_day,
                current_topic_index=s.current_topic_index,
                status=s.status,
                mode=s.mode,
                lesson_plan=s.lesson_plan,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ],
        total=total,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get details of a specific learning session.
    """
    session_service = get_session_service(db)
    
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        topic=session.topic,
        total_days=session.total_days,
        time_per_day=session.time_per_day,
        current_day=session.current_day,
        current_topic_index=session.current_topic_index,
        status=session.status,
        mode=session.mode,
        lesson_plan=session.lesson_plan,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{session_id}/plan", response_model=LessonPlanResponse)
async def get_lesson_plan(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get the full lesson plan for a session.
    
    Returns the complete curriculum with progress information.
    """
    plan_service = get_plan_service(db)
    
    try:
        result = plan_service.get_plan(session_id)
        
        return LessonPlanResponse(
            session_id=result["session_id"],
            topic=result["topic"],
            lesson_plan=result["lesson_plan"],
            current_day=result["current_day"],
            total_days=result["total_days"],
            progress_percentage=result["progress_percentage"],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{session_id}/plan/day/{day}")
async def get_day_content(
    session_id: UUID,
    day: int,
    db: Session = Depends(get_db),
):
    """
    Get content for a specific day in the lesson plan.
    
    Useful for displaying day details in a sidebar or preview.
    """
    plan_service = get_plan_service(db)
    
    try:
        return plan_service.get_day_content(session_id, day)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{session_id}/progress", response_model=ProgressResponse)
async def update_progress(
    session_id: UUID,
    request: UpdateProgressRequest,
    db: Session = Depends(get_db),
):
    """
    Update learning progress for a session.
    
    Can set current day and/or current topic index.
    """
    session_service = get_session_service(db)
    
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    updated = session_service.update_progress(
        session_id=session_id,
        current_day=request.current_day,
        current_topic_index=request.current_topic_index,
    )
    
    progress = session_service.calculate_progress_percentage(updated)
    
    return ProgressResponse(
        session_id=updated.session_id,
        current_day=updated.current_day,
        current_topic_index=updated.current_topic_index,
        total_days=updated.total_days,
        is_complete=updated.status == "COMPLETED",
        progress_percentage=progress,
    )


@router.post("/{session_id}/advance-day", response_model=ProgressResponse)
async def advance_day(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Move to the next day in the lesson plan.
    """
    session_service = get_session_service(db)
    
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.current_day >= session.total_days:
        raise HTTPException(
            status_code=400,
            detail="Already on the last day"
        )
    
    updated = session_service.advance_day(session_id)
    progress = session_service.calculate_progress_percentage(updated)
    
    return ProgressResponse(
        session_id=updated.session_id,
        current_day=updated.current_day,
        current_topic_index=updated.current_topic_index,
        total_days=updated.total_days,
        is_complete=updated.status == "COMPLETED",
        progress_percentage=progress,
    )


@router.post("/{session_id}/goto-day/{day}", response_model=ProgressResponse)
async def goto_day(
    session_id: UUID,
    day: int,
    db: Session = Depends(get_db),
):
    """
    Jump to a specific day (for reviewing past lessons).
    """
    session_service = get_session_service(db)
    
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if day < 1 or day > session.total_days:
        raise HTTPException(
            status_code=400,
            detail=f"Day must be between 1 and {session.total_days}"
        )
    
    updated = session_service.update_progress(
        session_id=session_id,
        current_day=day,
        current_topic_index=0,
    )
    
    progress = session_service.calculate_progress_percentage(updated)
    
    return ProgressResponse(
        session_id=updated.session_id,
        current_day=updated.current_day,
        current_topic_index=updated.current_topic_index,
        total_days=updated.total_days,
        is_complete=updated.status == "COMPLETED",
        progress_percentage=progress,
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Delete a learning session.
    """
    session_service = get_session_service(db)
    
    deleted = session_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return None
