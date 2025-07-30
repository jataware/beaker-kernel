"""
LLM-powered chat history summarization.

This module provides sophisticated LLM-powered summarization with UUID-based
message tracking and semantic understanding. The implementation was ported
from Archytas to maintain compatibility with existing behavior.
"""

import logging
from typing import List
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage

from .base import ChatHistorySummarizer

logger = logging.getLogger(__name__)


class LLMSummarizer(ChatHistorySummarizer):
    """
    LLM-powered summarization with semantic understanding.
    
    This implementation provides sophisticated summarization including:
    - Detailed prompt templates for comprehensive summaries
    - UUID-based message formatting for referenceability
    - Tool call handling with context preservation
    - Structured output format for conversation continuity
    
    Note: Logic was ported from Archytas to maintain behavioral compatibility.
    """
    
    @property
    def name(self) -> str:
        return "llm"
    
    async def summarize(self, messages: List[BaseMessage]) -> str:
        """
        Create LLM-powered summary with semantic understanding.
        Uses sophisticated prompting for high-fidelity conversation summaries.
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
                summary_messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
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
            
            # Fallback to simple summary
            return self._simple_fallback(messages)
            
        except Exception as e:
            logger.error(f"Error in LLM summarization: {e}")
            return self._simple_fallback(messages)
    
    def _simple_fallback(self, messages: List[BaseMessage]) -> str:
        """Fallback to simple extractive summary if LLM fails."""
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