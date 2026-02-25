"""
LLM Factory Module.

Provides a factory pattern for instantiating different LLM instances
based on use case (planning vs tutoring).

All LLMs use Google Gemini API:
- Planner: Gemini 2.5 Pro (powerful for curriculum generation)
- Tutor: Gemini 2.5 Flash (fast for interactive tutoring)

Streaming Strategy:
- Expected tokens < 100: Burst response (non-streaming)
- Expected tokens >= 100: Streaming response
"""
from enum import Enum
from typing import Optional, AsyncGenerator, Union
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMType(str, Enum):
    """Types of LLMs for different use cases."""
    PLANNER = "planner"  # Gemini 2.5 Pro - for curriculum generation
    TUTOR = "tutor"  # Gemini 2.5 Flash - for interactive teaching
    DSA = "dsa"  # Gemini 2.5 Pro - for DSA LeetCode tutoring
    DSA_HEAVY = "dsa_heavy"  # Gemini 3.0 Pro - for complex DSA problems


class ResponseMode(str, Enum):
    """Response delivery mode."""
    BURST = "burst"  # Non-streaming, immediate full response
    STREAM = "stream"  # Streaming, token by token
    AUTO = "auto"  # Automatically choose based on expected tokens


class LLMFactory:
    """
    Factory for creating Gemini LLM instances.
    
    Uses Google Gemini API exclusively:
    - PLANNER: Gemini 2.5 Pro (powerful, detailed curriculum generation)
    - TUTOR: Gemini 2.5 Flash (fast, interactive tutoring)
    """
    
    @classmethod
    def get_llm(
        cls,
        llm_type: LLMType,
        temperature: Optional[float] = None,
        streaming: bool = False
    ) -> ChatGoogleGenerativeAI:
        """
        Get a Gemini LLM instance for the specified use case.
        
        Args:
            llm_type: The type of LLM to create (PLANNER or TUTOR)
            temperature: Override default temperature
            streaming: Enable streaming responses
            
        Returns:
            Configured ChatGoogleGenerativeAI instance
        """
        if llm_type == LLMType.PLANNER:
            return cls._create_planner_llm(temperature, streaming)
        elif llm_type == LLMType.TUTOR:
            return cls._create_tutor_llm(temperature, streaming)
        elif llm_type == LLMType.DSA:
            return cls._create_dsa_llm(temperature, streaming)
        elif llm_type == LLMType.DSA_HEAVY:
            return cls._create_dsa_heavy_llm(temperature, streaming)
        else:
            raise ValueError(f"Unknown LLM type: {llm_type}")
    
    @classmethod
    def _create_planner_llm(
        cls, 
        temperature: Optional[float] = None,
        streaming: bool = False
    ) -> ChatGoogleGenerativeAI:
        """
        Create Gemini 2.5 Pro for planning/curriculum generation.
        
        Uses lower temperature for structured, consistent output.
        """
        return ChatGoogleGenerativeAI(
            model=settings.PLANNING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature if temperature is not None else 0.3,
            streaming=streaming,
            convert_system_message_to_human=True,
        )
    
    @classmethod
    def _create_tutor_llm(
        cls,
        temperature: Optional[float] = None,
        streaming: bool = False
    ) -> ChatGoogleGenerativeAI:
        """
        Create Gemini 2.5 Flash for interactive tutoring.
        
        Uses higher temperature for engaging, varied responses.
        """
        return ChatGoogleGenerativeAI(
            model=settings.TUTORING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature if temperature is not None else 0.7,
            streaming=streaming,
            convert_system_message_to_human=True,
        )
    
    @classmethod
    def _create_dsa_llm(
        cls,
        temperature: Optional[float] = None,
        streaming: bool = False
    ) -> ChatGoogleGenerativeAI:
        """
        Create Gemini 2.5 Pro for DSA LeetCode tutoring.
        
        Uses moderate temperature for structured but engaging responses.
        """
        return ChatGoogleGenerativeAI(
            model=settings.DSA_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature if temperature is not None else 0.5,
            streaming=streaming,
            convert_system_message_to_human=True,
        )
    
    @classmethod
    def _create_dsa_heavy_llm(
        cls,
        temperature: Optional[float] = None,
        streaming: bool = False
    ) -> ChatGoogleGenerativeAI:
        """
        Create Gemini 3.0 Pro for complex DSA problems.
        
        Uses the heavy model for difficult custom problems.
        """
        return ChatGoogleGenerativeAI(
            model=settings.DSA_HEAVY_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature if temperature is not None else 0.5,
            streaming=streaming,
            convert_system_message_to_human=True,
        )


def get_planner_llm(
    temperature: float = 0.3,
    streaming: bool = False
) -> ChatGoogleGenerativeAI:
    """
    Get Gemini 2.5 Pro for planning.
    
    Args:
        temperature: Sampling temperature (default 0.3 for consistency)
        streaming: Enable streaming (usually False for JSON output)
        
    Returns:
        Configured Gemini Pro instance
    """
    return LLMFactory.get_llm(LLMType.PLANNER, temperature=temperature, streaming=streaming)


def get_tutor_llm(
    temperature: float = 0.7,
    streaming: bool = False
) -> ChatGoogleGenerativeAI:
    """
    Get Gemini 2.5 Flash for tutoring.
    
    Args:
        temperature: Sampling temperature (default 0.7 for engagement)
        streaming: Enable streaming responses
        
    Returns:
        Configured Gemini Flash instance
    """
    return LLMFactory.get_llm(LLMType.TUTOR, temperature=temperature, streaming=streaming)


def get_dsa_llm(
    temperature: float = 0.5,
    streaming: bool = False
) -> ChatGoogleGenerativeAI:
    """Get Gemini 2.5 Pro for DSA LeetCode tutoring."""
    return LLMFactory.get_llm(LLMType.DSA, temperature=temperature, streaming=streaming)


def get_dsa_heavy_llm(
    temperature: float = 0.5,
    streaming: bool = False
) -> ChatGoogleGenerativeAI:
    """Get Gemini 3.0 Pro for complex DSA problems."""
    return LLMFactory.get_llm(LLMType.DSA_HEAVY, temperature=temperature, streaming=streaming)


def should_stream(expected_tokens: int) -> bool:
    """
    Determine if streaming should be used based on expected output tokens.
    
    Strategy:
    - If expected tokens < threshold: Use burst (immediate full response)
    - If expected tokens >= threshold: Use streaming (token by token)
    
    Args:
        expected_tokens: Estimated number of output tokens
        
    Returns:
        True if streaming should be used, False for burst
    """
    return expected_tokens >= settings.STREAMING_TOKEN_THRESHOLD


def estimate_response_tokens(message_type: str) -> int:
    """
    Estimate expected response tokens based on message type.
    
    Args:
        message_type: Type of message/response expected
        
    Returns:
        Estimated token count
    """
    # Token estimates for different response types
    estimates = {
        "acknowledgment": 20,  # "Got it!", "I understand"
        "short_answer": 50,  # Brief factual answers
        "clarification": 80,  # "Could you explain more?"
        "explanation": 200,  # Teaching a concept
        "detailed_explanation": 400,  # In-depth teaching
        "lesson_intro": 300,  # Day/topic introduction
        "day_summary": 250,  # End of day summary
        "plan_generation": 2000,  # Full lesson plan
        "default": 150,  # Default for tutoring responses
    }
    return estimates.get(message_type, estimates["default"])


def classify_expected_response(user_message: Optional[str]) -> str:
    """
    Classify the expected response type based on user message.
    
    Args:
        user_message: The user's input message
        
    Returns:
        Response type classification
    """
    if not user_message:
        return "lesson_intro"
    
    message_lower = user_message.lower().strip()
    
    # Short acknowledgments (expect short response)
    acknowledgment_phrases = [
        "ok", "okay", "got it", "i understand", "understood",
        "yes", "no", "sure", "thanks", "thank you", "next",
        "continue", "go on", "proceed"
    ]
    if message_lower in acknowledgment_phrases or len(message_lower) < 10:
        return "acknowledgment"
    
    # Questions requesting explanation
    explanation_triggers = [
        "explain", "what is", "what are", "how does", "how do",
        "why is", "why does", "tell me about", "describe",
        "can you explain", "help me understand"
    ]
    if any(trigger in message_lower for trigger in explanation_triggers):
        return "detailed_explanation"
    
    # Clarification requests
    clarification_triggers = [
        "what do you mean", "i don't understand", "confused",
        "simpler", "example", "analogy"
    ]
    if any(trigger in message_lower for trigger in clarification_triggers):
        return "explanation"
    
    # Default to standard explanation
    return "default"
