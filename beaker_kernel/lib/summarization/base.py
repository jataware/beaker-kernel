"""
Base interface for chat history summarization strategies.
"""

from abc import ABC, abstractmethod
from typing import List
from langchain_core.messages import BaseMessage


class ChatHistorySummarizer(ABC):
    """Abstract base class for chat history summarization strategies."""
    
    @abstractmethod
    async def summarize(self, messages: List[BaseMessage]) -> str:
        """
        Summarize a list of chat messages.
        
        Args:
            messages: List of chat messages to summarize
            
        Returns:
            str: Summarized content
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this summarization strategy."""
        pass