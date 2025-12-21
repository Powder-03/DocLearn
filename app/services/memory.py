"""
Memory service with buffer-based summarization.
Manages the 10-message buffer threshold and triggers summarization.
"""

import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.services.mongodb import chat_storage, ChatStorageService

logger = logging.getLogger(__name__)


SUMMARIZATION_PROMPT = """You are a conversation summarizer for an educational tutoring platform. 
Your task is to create a concise but comprehensive summary of the following conversation between a student and an AI tutor.

IMPORTANT GUIDELINES:
1. Capture the main topics discussed
2. Note any key concepts the student learned or struggled with
3. Record the student's current progress and understanding level
4. Highlight any questions that were asked and answered
5. Keep the summary focused and under 300 words
6. Use third person perspective (e.g., "The student asked about...", "The tutor explained...")

CONVERSATION TO SUMMARIZE:
{conversation}

Provide a clear, educational summary that will help continue the tutoring session later:"""


class MemoryService:
    """
    Service for managing conversation memory with buffer-based summarization.
    
    Flow:
    1. Messages are added to the buffer in MongoDB
    2. When buffer reaches MEMORY_BUFFER_SIZE (10), summarization is triggered
    3. The summary replaces the buffer messages
    4. Summaries accumulate over time for long conversations
    """
    
    def __init__(self, storage: ChatStorageService = chat_storage):
        self.storage = storage
        self.buffer_threshold = settings.MEMORY_BUFFER_SIZE
        self._summarizer_llm = None
    
    @property
    def summarizer_llm(self) -> ChatGoogleGenerativeAI:
        """Lazy initialization of summarizer LLM (using Flash for speed)."""
        if self._summarizer_llm is None:
            self._summarizer_llm = ChatGoogleGenerativeAI(
                model=settings.TUTORING_MODEL,  # Use Flash for summarization
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.3,  # Low temperature for consistent summaries
            )
        return self._summarizer_llm
    
    async def add_user_message(self, session_id: str, content: str) -> None:
        """
        Add a user message to the conversation.
        
        Args:
            session_id: The session identifier
            content: The user's message
        """
        await self.storage.add_message(session_id, "user", content)
        logger.debug(f"Added user message for session {session_id}")
    
    async def add_assistant_message(self, session_id: str, content: str) -> None:
        """
        Add an assistant message and check if summarization is needed.
        
        Args:
            session_id: The session identifier
            content: The assistant's response
        """
        doc = await self.storage.add_message(session_id, "assistant", content)
        
        # Check if we need to summarize
        buffer_count = doc.get("buffer_count", 0)
        
        if buffer_count >= self.buffer_threshold:
            logger.info(f"Buffer threshold reached for session {session_id}, triggering summarization")
            await self._summarize_buffer(session_id)
    
    async def _summarize_buffer(self, session_id: str) -> str:
        """
        Summarize the current buffer and clear it.
        
        Args:
            session_id: The session identifier
            
        Returns:
            The generated summary
        """
        # Get buffer messages
        messages = await self.storage.get_buffer_messages(session_id)
        
        if not messages:
            logger.warning(f"No messages to summarize for session {session_id}")
            return ""
        
        # Format conversation for summarization
        conversation_text = self._format_messages_for_summary(messages)
        
        # Generate summary using LLM
        try:
            summary = await self._generate_summary(conversation_text)
            
            # Clear buffer and store summary
            await self.storage.clear_buffer_and_add_summary(session_id, summary)
            
            logger.info(f"Successfully summarized {len(messages)} messages for session {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize buffer for session {session_id}: {e}")
            # Don't clear buffer if summarization fails
            raise
    
    def _format_messages_for_summary(self, messages: list) -> str:
        """Format messages into a readable conversation string."""
        lines = []
        for msg in messages:
            role = "Student" if msg["role"] == "user" else "Tutor"
            lines.append(f"{role}: {msg['content']}")
        return "\n\n".join(lines)
    
    async def _generate_summary(self, conversation_text: str) -> str:
        """
        Generate a summary using the LLM.
        
        Args:
            conversation_text: Formatted conversation to summarize
            
        Returns:
            Generated summary string
        """
        prompt = SUMMARIZATION_PROMPT.format(conversation=conversation_text)
        
        messages = [
            SystemMessage(content="You are a helpful educational summarizer."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.summarizer_llm.ainvoke(messages)
        return response.content
    
    async def get_conversation_context(self, session_id: str) -> str:
        """
        Get the full conversation context for the LLM.
        Combines summaries and recent buffer messages.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Formatted context string
        """
        return await self.storage.format_context_for_llm(session_id)
    
    async def get_context_for_graph(self, session_id: str) -> dict:
        """
        Get context formatted for the LangGraph state.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dict with 'memory_summary' and 'chat_history' keys
        """
        context = await self.storage.get_full_context(session_id)
        
        # Combine summaries into memory_summary
        memory_summary = "\n\n".join(context["summaries"]) if context["summaries"] else None
        
        # Convert recent messages to chat history format
        chat_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in context["recent_messages"]
        ]
        
        return {
            "memory_summary": memory_summary,
            "chat_history": chat_history
        }
    
    async def should_summarize(self, session_id: str) -> bool:
        """Check if the buffer has reached the summarization threshold."""
        count = await self.storage.get_buffer_count(session_id)
        return count >= self.buffer_threshold
    
    async def force_summarize(self, session_id: str) -> Optional[str]:
        """
        Force summarization regardless of buffer count.
        Useful for session end or explicit user request.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Generated summary or None if no messages
        """
        count = await self.storage.get_buffer_count(session_id)
        if count == 0:
            return None
        
        return await self._summarize_buffer(session_id)
    
    async def clear_session_memory(self, session_id: str) -> bool:
        """
        Clear all memory for a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if deleted successfully
        """
        return await self.storage.delete_chat(session_id)


# Singleton instance
memory_service = MemoryService()
