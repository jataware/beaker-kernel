"""
Simple extractive summarization strategy.

Provides basic fallback summarization when LLM-powered approaches are unavailable.
"""

import logging
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

from .base import ChatHistorySummarizer

logger = logging.getLogger(__name__)


class SimpleSummarizer(ChatHistorySummarizer):
    """
    Simple extractive summarization strategy.
    
    This implementation provides a lightweight fallback when LLM-powered
    summarization is unavailable or fails.
    """
    
    @property
    def name(self) -> str:
        return "simple"
    
    async def summarize(self, messages: List[BaseMessage]) -> str:
        """
        Create simple extractive summary by truncating message content.
        
        Args:
            messages: List of chat messages to summarize
            
        Returns:
            str: Simple extractive summary
        """
        if not messages:
            return "Empty conversation"
        
        summary_parts = []
        
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            if isinstance(msg, HumanMessage):
                summary_parts.append(f"User asked: {content[:100]}...")
            elif isinstance(msg, AIMessage):
                summary_parts.append(f"Assistant responded: {content[:100]}...")
            elif isinstance(msg, ToolMessage):
                summary_parts.append(f"Tool executed: {content[:50]}...")
        
        # Keep last 10 key points to avoid overly long summaries
        summary = " | ".join(summary_parts[-10:])
        return f"Simple summary of {len(messages)} messages: {summary}"