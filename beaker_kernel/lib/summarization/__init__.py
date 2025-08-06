"""
Chat history summarization system.

Provides pluggable summarization strategies for BeakerChatHistory.
"""

from .base import ChatHistorySummarizer
from .llm_summarizer import LLMSummarizer
from .simple_summarizer import SimpleSummarizer

__all__ = ['ChatHistorySummarizer', 'LLMSummarizer', 'SimpleSummarizer']


def get_summarizer(strategy: str = "llm") -> ChatHistorySummarizer:
    """Get a summarization strategy by name."""
    strategies = {
        "llm": LLMSummarizer,
        "simple": SimpleSummarizer,
        # Backward compatibility alias
        "archytas": LLMSummarizer,
    }
    
    if strategy not in strategies:
        raise ValueError(f"Unknown summarization strategy: {strategy}")
    
    return strategies[strategy]()