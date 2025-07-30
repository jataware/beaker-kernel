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
    
    def __init__(self, max_tokens: int = None, summarization_threshold: float = 0.8, model=None):
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
        
    def estimate_tokens(self, text: str) -> int:
        """Simple token estimation (roughly 4 chars per token)."""
        return max(1, len(str(text)) // 4)
    
    def add_message(self, message: BaseMessage, react_loop_id: Optional[str] = None) -> str:
        """Add a message to chat history."""
        record_id = str(uuid4())
        token_count = self.estimate_tokens(message.content if hasattr(message, 'content') else str(message))
        
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
            
            # Create a summary message using LLM
            summary_content = await self._create_summary(messages_to_summarize)
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
    
    async def _create_summary(self, messages: List[BaseMessage]) -> str:
        """
        Create LLM-powered summary using ported Archytas logic.
        Based on archytas.summarizers.default_history_summarizer()
        """
        try:
            if not messages:
                return "Empty conversation"
            
            # Port the exact Archytas Jinja template approach
            system_prompt = """You are an intelligent agent capable of reviewing conversations with an LLM by analyzing the system message, human messages, AI responses, and tool usage and generating a detailed but terse summary of the conversation that can then be used by other agents to continue long conversations that may exceed the context window."""
            
            # Build the user prompt with Archytas-style message formatting
            user_prompt_parts = [
                "Please summarize all of the following messages into a single block of text that will replace the messages in future calls to the LLM. Please include all details needed to preserve fidelity with the original meaning, while being as short as reasonably possible so that the context window remains available for future conversation. Try to generate one sentence per message, but you can combine messages or use multiple sentences as needed due to light or heavy information load, respectively.",
                "",
                "While summarizing, please include each message UUID along with a brief summary of the message(s). Messages can be grouped for narrative sake, but try to keep each group to be 5 messages or less and be sure to include the UUIDs of each message in the group.",
                "",
                "If higher fidelity recall of the summarized messages are needed in the future, they original message content can be retrieved using the UUID. However, be sure to focus the summaries on semantic understanding for conversation over searching and retrieval.",
                "",
                "### START OF MESSAGES ###"
            ]
            
            # Format messages in Archytas style
            for i, msg in enumerate(messages):
                # Generate a UUID for each message (simplified)
                msg_uuid = f"msg_{i+1:08x}"
                content = msg.content if hasattr(msg, 'content') else str(msg)
                msg_type = type(msg).__name__
                
                user_prompt_parts.append(f"```{msg_type} {msg_uuid} content")
                user_prompt_parts.append(content.strip())
                user_prompt_parts.append("```")
                user_prompt_parts.append("")
                
                # Handle tool calls like Archytas
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        user_prompt_parts.append(f"```{msg_type} {msg_uuid} tool_call")
                        user_prompt_parts.append(f"tool_name: {tool_call.get('name', 'unknown')}")
                        user_prompt_parts.append(f"args: {tool_call.get('args', {})}")
                        user_prompt_parts.append(f"tool_call_id: {tool_call.get('id', 'unknown')}")
                        user_prompt_parts.append("```")
                        user_prompt_parts.append("")
            
            user_prompt_parts.append("### END OF MESSAGES ###")
            user_prompt = "\n".join(user_prompt_parts)
            
            # Get the current agent's model
            from beaker_kernel.lib.utils import get_beaker_kernel
            kernel = get_beaker_kernel()
            if kernel and hasattr(kernel.context, 'agent') and hasattr(kernel.context.agent, 'model'):
                model = kernel.context.agent.model
                
                # Create messages exactly like Archytas does
                from langchain_core.messages import SystemMessage, HumanMessage as LCHumanMessage
                summary_messages = [
                    SystemMessage(content=system_prompt),
                    LCHumanMessage(content=user_prompt)
                ]
                
                try:
                    # Call the model directly like Archytas
                    response = await model.ainvoke(summary_messages)
                    summary_text = response.content if hasattr(response, 'content') else str(response)
                    
                    # Format like Archytas: include message count and summary
                    message_count = len(messages)
                    return f"Below is a summary of {message_count} messages:\n\n```summary\n{summary_text}\n```"
                    
                except Exception as e:
                    logger.warning(f"LLM summarization failed: {e}")
            
            # Fallback to extractive summary
            return self._extractive_summary_fallback(messages)
            
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return self._extractive_summary_fallback(messages)
    
    def _extractive_summary_fallback(self, messages: List[BaseMessage]) -> str:
        """Fallback extractive summary if LLM summarization fails."""
        summary_parts = []
        
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            if isinstance(msg, HumanMessage):
                summary_parts.append(f"User asked: {content[:100]}...")
            elif isinstance(msg, AIMessage):
                summary_parts.append(f"Assistant responded: {content[:100]}...")
            elif isinstance(msg, ToolMessage):
                summary_parts.append(f"Tool executed: {content[:50]}...")
        
        return " | ".join(summary_parts[-10:])  # Keep last 10 key points
    
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