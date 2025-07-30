"""
Chat history management for LangGraph agents.

Provides chat history tracking and auto-summarization compatible with the Beaker UI.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from .summarization import get_summarizer, ChatHistorySummarizer

logger = logging.getLogger(__name__)


@dataclass
class MessageRecord:
    """Record of a single message in chat history."""
    uuid: str
    message: BaseMessage
    token_count: int
    metadata: Dict[str, Any]
    react_loop_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message": {
                "text": self.message.content if hasattr(self.message, 'content') else str(self.message),
                "raw_content": self.message.content if hasattr(self.message, 'content') else str(self.message),
                "type": self.message.type if hasattr(self.message, 'type') else "unknown",
                "id": getattr(self.message, 'id', None),
                "role": getattr(self.message, 'type', 'unknown'),
            },
            "uuid": self.uuid,
            "token_count": self.token_count,
            "metadata": self.metadata,
            "react_loop_id": self.react_loop_id,
        }


@dataclass 
class SystemMessage:
    """System message wrapper."""
    message: BaseMessage
    
    @property
    def text(self) -> str:
        return self.message.content if hasattr(self.message, 'content') else str(self.message)


@dataclass
class OutboundChatHistory:
    """Chat history format for the Beaker UI."""
    records: List[Dict[str, Any]]
    system_message: str
    tool_token_usage_estimate: int
    model: Dict[str, Any]
    overhead_token_count: int
    total_token_count: int
    token_estimate: int
    message_token_count: int  # Required by UI
    summary_token_count: int  # Required by UI
    summarization_threshold: int  # Required by UI
    summarized_count: int = 0


def get_model_context_window(model) -> int:
    """Get the context window size for a given model."""
    if not model:
        return 128000  # Default fallback
    
    model_name = ""
    if hasattr(model, 'model'):
        model_name = model.model.lower()
    elif hasattr(model, 'model_name'):
        model_name = model.model_name.lower()
    
    # Known context windows for popular models
    if 'claude-3' in model_name or 'claude-2' in model_name:
        return 200000  # Claude 3/2 models
    elif 'gpt-4' in model_name:
        if 'turbo' in model_name:
            return 128000  # GPT-4 Turbo
        else:
            return 8192   # GPT-4 base
    elif 'gpt-3.5' in model_name:
        return 16384   # GPT-3.5 Turbo
    elif 'gemini' in model_name:
        if '1.5' in model_name:
            return 1000000  # Gemini 1.5 Pro
        if '2.0' in model_name:
            return 1000000  # Gemini 2.0 Pro
        if '2.5' in model_name:
            return 1000000  # Gemini 2.5 Pro
        else:
            return 32768    # Gemini 1.0
    elif 'llama' in model_name:
        return 32768   # Common Llama context window
    else:
        return 128000  # Conservative default


class BeakerChatHistory:
    """Chat history manager for LangGraph agents."""
    
    def __init__(self, max_tokens: int = None, summarization_threshold: float = 0.05, model=None, summarization_strategy: str = "archytas"):
        self.messages: List[BaseMessage] = []
        self.records: List[MessageRecord] = []
        # Use model-specific context window if available
        self.max_tokens = max_tokens or get_model_context_window(model)
        self.summarization_threshold = summarization_threshold
        self.total_tokens = 0
        self.tool_token_estimate = 0
        self.token_overhead = 500  # Estimated overhead
        self.summarized_count = 0
        self.system_message = SystemMessage(HumanMessage(content="You are a helpful assistant."))
        
        # Pluggable summarization strategy
        self.summarizer = get_summarizer(summarization_strategy)
        
    def estimate_tokens(self, text: str) -> int:
        """Simple token estimation (roughly 4 chars per token)."""
        return max(1, len(str(text)) // 4)
    
    def add_message(self, message: BaseMessage, react_loop_id: Optional[str] = None) -> str:
        """Add a message to chat history."""
        # Validate message content
        content = getattr(message, 'content', '')
        if not content or not str(content).strip():
            logger.warning(f"Skipping message with empty content: {type(message).__name__}")
            return str(uuid4())  # Return dummy ID but don't store the message
        
        record_id = str(uuid4())
        token_count = self.estimate_tokens(content)
        
        record = MessageRecord(
            uuid=record_id,
            message=message,
            token_count=token_count,
            metadata={"timestamp": time.time()},
            react_loop_id=react_loop_id
        )
        
        self.messages.append(message)
        self.records.append(record)
        self.total_tokens += token_count
        
        # Track tool usage for token estimation
        if isinstance(message, ToolMessage):
            self.tool_token_estimate += token_count
        
        logger.debug(f"Added message to chat history: {token_count} tokens, total: {self.total_tokens}")
        
        # Check if we need to summarize
        if self.should_summarize():
            logger.info("Chat history approaching token limit, auto-summarization needed")
            asyncio.create_task(self.auto_summarize())
        
        return record_id
    
    def should_summarize(self) -> bool:
        """Check if chat history should be summarized."""
        threshold_tokens = int(self.max_tokens * self.summarization_threshold)
        return self.total_tokens > threshold_tokens
    
    async def auto_summarize(self):
        """Auto-summarize chat history to reduce token count."""
        try:
            logger.info(f"Starting auto-summarization. Current tokens: {self.total_tokens}")
            
            if len(self.records) <= 2:
                logger.info("Too few messages to summarize")
                return
            
            # Keep the last few messages and summarize the rest
            keep_recent = 3  # Keep last 3 exchanges
            messages_to_summarize = self.messages[:-keep_recent] if len(self.messages) > keep_recent else []
            
            if not messages_to_summarize:
                logger.info("No messages to summarize")
                return
            
            # Create a summary message using pluggable summarizer
            summary_content = await self.summarizer.summarize(messages_to_summarize)
            summary_message = AIMessage(content=f"[SUMMARIZED CONVERSATION]: {summary_content}")
            
            # Replace old messages with summary
            summarized_count = len(messages_to_summarize)
            self.messages = [summary_message] + self.messages[-keep_recent:]
            
            # Update records
            summary_tokens = self.estimate_tokens(summary_content)
            summary_record = MessageRecord(
                uuid=str(uuid4()),
                message=summary_message,
                token_count=summary_tokens,
                metadata={"timestamp": time.time(), "is_summary": True, "summarized_messages": summarized_count}
            )
            
            self.records = [summary_record] + self.records[-keep_recent:]
            
            # Recalculate token count
            self.total_tokens = sum(record.token_count for record in self.records)
            self.summarized_count += summarized_count
            
            logger.info(f"Auto-summarization complete. Summarized {summarized_count} messages. New token count: {self.total_tokens}")
            
            # Notify the kernel that chat history has changed
            from beaker_kernel.lib.utils import get_beaker_kernel
            kernel = get_beaker_kernel()
            if kernel:
                # Trigger a chat history update in the UI
                import asyncio
                asyncio.create_task(kernel.send_chat_history())
            
        except Exception as e:
            logger.error(f"Error during auto-summarization: {e}")
    
    
    async def get_records(self, auto_update_context: bool = True) -> List[MessageRecord]:
        """Get all message records."""
        return self.records.copy()
    
    async def token_estimate_async(self, model=None) -> int:
        """Estimate total tokens."""
        return self.total_tokens
    
    @property
    def token_estimate(self) -> int:
        """Current token estimate."""
        return self.total_tokens
    
    def to_outbound_format(self, model=None) -> OutboundChatHistory:
        """Convert to format expected by Beaker UI."""
        # Get proper model information
        provider_name = "Unknown"
        model_name = "unknown"
        context_window = self.max_tokens  # Use our configured max tokens (already model-aware)
        
        if model:
            provider_name = type(model).__name__
            # Try different ways to get the model name
            if hasattr(model, 'model_name'):
                model_name = model.model_name
            elif hasattr(model, 'model'):
                model_name = model.model
            elif hasattr(model, '_model_name'):
                model_name = model._model_name
        
        # Calculate token breakdown for UI
        message_tokens = 0
        summary_tokens = 0
        
        for record in self.records:
            if record.metadata.get('is_summary', False):
                summary_tokens += record.token_count
            else:
                message_tokens += record.token_count
        
        # Calculate summarization threshold in tokens
        threshold_tokens = int(context_window * self.summarization_threshold)
        
        return OutboundChatHistory(
            records=[record.to_dict() for record in self.records],
            system_message=self.system_message.text,
            tool_token_usage_estimate=self.tool_token_estimate,
            model={
                "provider": provider_name,
                "model_name": model_name,
                "context_window": context_window,
            },
            overhead_token_count=self.token_overhead,
            total_token_count=self.total_tokens,
            token_estimate=self.total_tokens,
            message_token_count=message_tokens,
            summary_token_count=summary_tokens,
            summarization_threshold=threshold_tokens,
            summarized_count=self.summarized_count,
        )