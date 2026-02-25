"""
Plan Service.

Business logic for creating and managing lesson plans.
Orchestrates the plan generation process using MongoDB.
"""
import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from langchain_core.messages import SystemMessage, HumanMessage

from app.services.session_service import SessionService, SessionStatus
from app.services.leetcode_service import leetcode_service
from app.graphs import invoke_generation_graph, create_initial_state
from app.core.prompts import DSA_PLAN_GENERATION_PROMPT
from app.core.llm_factory import get_dsa_llm, get_dsa_heavy_llm

logger = logging.getLogger(__name__)


class PlanService:
    """
    Service class for managing lesson plans.
    
    Handles plan generation using the LangGraph planner node.
    Uses MongoDB for session storage.
    """
    
    def __init__(self, session_service: SessionService):
        """
        Initialize the plan service.
        
        Args:
            session_service: SessionService instance for data access
        """
        self.session_service = session_service
    
    async def create_plan(
        self,
        user_id: UUID,
        topic: str,
        total_days: int,
        time_per_day: str,
        mode: str = "generation",
        target: Optional[str] = None,
        question_number: Optional[int] = None,
        programming_language: Optional[str] = None,
        question_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new learning plan.
        
        Args:
            user_id: User identifier
            topic: Topic to learn
            total_days: Number of days for the plan
            time_per_day: Daily time commitment
            mode: Learning mode
            target: Target exam or goal
            question_number: LeetCode question number (DSA LeetCode mode)
            programming_language: Programming language (DSA modes)
            question_text: Full question text (DSA Other mode)
            
        Returns:
            Dictionary with session_id, status, message, lesson_plan
        """
        # Handle DSA modes
        if mode in ("dsa_leetcode", "dsa_other"):
            return await self._create_dsa_plan(
                user_id=user_id,
                mode=mode,
                question_number=question_number,
                programming_language=programming_language or "python",
                question_text=question_text,
                time_per_day=time_per_day,
            )
        
        # Force single day for quick mode
        if mode == "quick":
            total_days = 1
        
        # Create the session (async)
        session = await self.session_service.create_session(
            user_id=user_id,
            topic=topic,
            total_days=total_days,
            time_per_day=time_per_day,
            mode=mode,
            target=target,
        )
        
        session_id = session["session_id"]
        logger.info(f"Created session {session_id}, starting plan generation (mode={mode})")
        
        # Build initial state for the graph
        initial_state = create_initial_state(
            session_id=session_id,
            user_id=str(user_id),
            topic=topic,
            total_days=total_days,
            time_per_day=time_per_day,
            lesson_plan=None,  # No plan yet - triggers planning node
            mode=mode,
            target=target,
        )
        
        try:
            # Run the graph (will route to plan_generator_node)
            result = await invoke_generation_graph(initial_state)
            
            lesson_plan = result.get("lesson_plan")
            ai_response = result.get("ai_response", "Your plan is ready!")
            
            # Check if plan generation was successful
            if lesson_plan and "error" not in lesson_plan:
                # Update session with the plan (async)
                await self.session_service.update_lesson_plan(
                    session_id=UUID(session_id),
                    lesson_plan=lesson_plan,
                    status=SessionStatus.READY.value,
                )
                
                logger.info(f"Successfully generated plan for session {session_id}")
                
                return {
                    "session_id": UUID(session_id),
                    "status": SessionStatus.READY.value,
                    "message": ai_response,
                    "lesson_plan": lesson_plan,
                }
            else:
                # Plan generation failed
                error_msg = lesson_plan.get("error", "Unknown error") if lesson_plan else "No plan generated"
                
                await self.session_service.update_lesson_plan(
                    session_id=UUID(session_id),
                    lesson_plan={"error": error_msg},
                    status=SessionStatus.FAILED.value,
                )
                
                logger.error(f"Plan generation failed for session {session_id}: {error_msg}")
                
                return {
                    "session_id": UUID(session_id),
                    "status": SessionStatus.FAILED.value,
                    "message": f"Failed to generate plan: {error_msg}",
                    "lesson_plan": None,
                }
                
        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error during plan generation: {str(e)}")
            
            await self.session_service.update_lesson_plan(
                session_id=UUID(session_id),
                lesson_plan={"error": str(e)},
                status=SessionStatus.FAILED.value,
            )
            
            raise
    
    async def _create_dsa_plan(
        self,
        user_id: UUID,
        mode: str,
        programming_language: str,
        question_number: Optional[int] = None,
        question_text: Optional[str] = None,
        time_per_day: str = "1 hour",
    ) -> Dict[str, Any]:
        """
        Create a DSA problem-solving session.
        
        For LeetCode mode: fetches problem from LeetCode API.
        For Other mode: uses the provided question text.
        """
        leetcode_data = None
        problem_title = "Custom DSA Problem"
        problem_description = question_text or ""
        difficulty = "Unknown"
        topic_tags = ""
        
        # Fetch LeetCode problem if applicable
        if mode == "dsa_leetcode" and question_number:
            logger.info(f"Fetching LeetCode problem #{question_number}")
            leetcode_data = await leetcode_service.get_problem_by_number(question_number)
            
            if leetcode_data:
                problem_title = f"#{leetcode_data['number']}. {leetcode_data['title']}"
                problem_description = leetcode_data["description"]
                difficulty = leetcode_data["difficulty"]
                topic_tags = ", ".join(leetcode_data.get("topic_tags", []))
            else:
                # Fallback: let LLM use its knowledge
                problem_title = f"LeetCode #{question_number}"
                problem_description = f"LeetCode problem number {question_number}. Please use your knowledge of this problem."
                difficulty = "Unknown"
        elif mode == "dsa_other":
            problem_title = "Custom Problem"
            problem_description = question_text or "No problem description provided"
        
        topic = problem_title
        
        # Create session with DSA fields
        session = await self.session_service.create_session(
            user_id=user_id,
            topic=topic,
            total_days=1,
            time_per_day=time_per_day,
            mode=mode,
            target=f"Solve: {problem_title}",
            question_number=question_number,
            programming_language=programming_language,
            question_text=question_text,
            leetcode_data=leetcode_data,
        )
        
        session_id = session["session_id"]
        logger.info(f"Created DSA session {session_id} (mode={mode})")
        
        # Generate DSA lesson plan using the appropriate LLM
        try:
            if mode == "dsa_other":
                llm = get_dsa_heavy_llm(temperature=0.3, streaming=False)
            else:
                llm = get_dsa_llm(temperature=0.3, streaming=False)
            
            plan_prompt = DSA_PLAN_GENERATION_PROMPT.format(
                problem_title=problem_title,
                difficulty=difficulty,
                problem_description=problem_description[:2000],
                topic_tags=topic_tags,
                programming_language=programming_language,
            )
            
            messages = [
                SystemMessage(content="You are an expert DSA curriculum designer. Output valid JSON only."),
                HumanMessage(content=plan_prompt),
            ]
            
            response = await llm.ainvoke(messages)
            response_text = response.content.strip()
            
            # Clean markdown JSON wrapper if present
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1] if "\n" in response_text else response_text
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
            
            lesson_plan = json.loads(response_text)
            
            # Update session with the plan
            await self.session_service.update_lesson_plan(
                session_id=UUID(session_id),
                lesson_plan=lesson_plan,
                status=SessionStatus.READY.value,
            )
            
            logger.info(f"Successfully generated DSA plan for session {session_id}")
            
            return {
                "session_id": UUID(session_id),
                "status": SessionStatus.READY.value,
                "message": f"Ready to solve: {problem_title}",
                "lesson_plan": lesson_plan,
            }
            
        except Exception as e:
            logger.exception(f"DSA plan generation failed for session {session_id}: {e}")
            
            await self.session_service.update_lesson_plan(
                session_id=UUID(session_id),
                lesson_plan={"error": str(e)},
                status=SessionStatus.FAILED.value,
            )
            
            raise
    
    async def get_plan(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get the lesson plan for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with plan details
            
        Raises:
            ValueError: If session not found or plan not ready
        """
        session = await self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.get("lesson_plan"):
            raise ValueError("Lesson plan not yet generated")
        
        progress = self.session_service.calculate_progress_percentage(session)
        
        return {
            "session_id": UUID(session["session_id"]),
            "topic": session["topic"],
            "lesson_plan": session["lesson_plan"],
            "current_day": session["current_day"],
            "total_days": session["total_days"],
            "progress_percentage": progress,
        }
    
    async def get_day_content(self, session_id: UUID, day: int) -> Dict[str, Any]:
        """
        Get content for a specific day.
        
        Args:
            session_id: Session identifier
            day: Day number (1-indexed)
            
        Returns:
            Dictionary with day content
            
        Raises:
            ValueError: If session not found or invalid day
        """
        session = await self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.get("lesson_plan"):
            raise ValueError("Lesson plan not yet generated")
        
        days = session["lesson_plan"].get("days", [])
        if day < 1 or day > len(days):
            raise ValueError(f"Day must be between 1 and {len(days)}")
        
        day_content = days[day - 1]
        
        return {
            "session_id": UUID(session["session_id"]),
            "day": day,
            "total_days": session["total_days"],
            "is_current_day": day == session["current_day"],
            "is_completed": day < session["current_day"],
            **day_content,
        }
