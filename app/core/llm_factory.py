"""
LLM Factory Module.

Provides a factory pattern for instantiating different LLM instances
based on use case (planning vs tutoring).
"""
from enum import Enum
from typing import Optional

from langchain_core.language_models import BaseChatModel

from app.core.config import settings


class LLMType(str, Enum):
    """Types of LLMs for different use cases."""
    PLANNER = "planner"  # Fast, cheap - for curriculum generation
    TUTOR = "tutor"  # Powerful, creative - for interactive teaching


class LLMFactory:
    """
    Factory for creating LLM instances.
    
    Uses a hybrid strategy:
    - PLANNER: Gemini Flash (fast, cheap) for structured output
    - TUTOR: GPT-4o (powerful) for engaging conversation
    """
    
    _instances: dict = {}
    
    @classmethod
    def get_llm(
        cls,
        llm_type: LLMType,
        temperature: Optional[float] = None,
        streaming: bool = False
    ) -> BaseChatModel:
        """
        Get an LLM instance for the specified use case.
        
        Args:
            llm_type: The type of LLM to create
            temperature: Override default temperature
            streaming: Enable streaming responses
            
        Returns:
            Configured LLM instance
        """
        if llm_type == LLMType.PLANNER:
            return cls._create_planner_llm(temperature)
        elif llm_type == LLMType.TUTOR:
            return cls._create_tutor_llm(temperature, streaming)
        else:
            raise ValueError(f"Unknown LLM type: {llm_type}")
    
    @classmethod
    def _create_planner_llm(
        cls, 
        temperature: Optional[float] = None
    ) -> BaseChatModel:
        """Create LLM for planning/curriculum generation."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        return ChatGoogleGenerativeAI(
            model=settings.PLANNING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature if temperature is not None else 0.3,
            convert_system_message_to_human=True,
        )
    
    @classmethod
    def _create_tutor_llm(
        cls,
        temperature: Optional[float] = None,
        streaming: bool = False
    ) -> BaseChatModel:
        """Create LLM for interactive tutoring."""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=settings.TUTORING_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature if temperature is not None else 0.7,
            streaming=streaming,
        )


def get_planner_llm(temperature: float = 0.3) -> BaseChatModel:
    """Convenience function to get planner LLM."""
    return LLMFactory.get_llm(LLMType.PLANNER, temperature=temperature)


def get_tutor_llm(temperature: float = 0.7, streaming: bool = False) -> BaseChatModel:
    """Convenience function to get tutor LLM."""
    return LLMFactory.get_llm(LLMType.TUTOR, temperature=temperature, streaming=streaming)
