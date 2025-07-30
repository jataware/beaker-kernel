"""
Beaker agent implementation.
"""

import asyncio
import logging
import typing
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from beaker_kernel.lib.config import config
from beaker_kernel.lib.utils import DefaultModel, get_beaker_kernel, set_beaker_kernel
from beaker_kernel.lib.chat_history import BeakerChatHistory

if typing.TYPE_CHECKING:
    from beaker_kernel.lib.context import BeakerContext

logger = logging.getLogger(__name__)


class BeakerAgent:
    """Base agent class for Beaker contexts."""

    def __init__(self, context: "BeakerContext" = None, tools: List[BaseTool] = None, summarization_strategy: str = "llm", **kwargs):
        self.context = context
        
        # Set up global kernel reference for tools
        if context and hasattr(context, 'beaker_kernel'):
            set_beaker_kernel(context.beaker_kernel)
        
        # Get model first
        self.model = config.get_model() or DefaultModel({})
        
        # Initialize chat history with model information and configurable summarization
        self.chat_history = BeakerChatHistory(model=self.model, summarization_strategy=summarization_strategy)
        
        # Prepare tools - include ask_user by default
        all_tools = [self.ask_user] + (tools or [])
        self._tools = all_tools
        
        # Create LangGraph agent
        self._langgraph_app = create_react_agent(
            model=self.model,
            tools=self._tools,
            **kwargs
        )
        
        if context:
            context.beaker_kernel.debug("init-langgraph-agent", {
                "tools_count": len(self._tools),
                "model_type": type(self.model).__name__,
                "chat_history_enabled": True,
            })

    async def react_async(self, query: str, react_context: dict = None) -> str:
        """Execute the agent with a query."""
        try:
            # Set up parent message context for tool execution  
            from beaker_kernel.lib.utils import parent_message_context
            
            parent_message = None
            if react_context and "message" in react_context:
                parent_message = react_context["message"]
            
            # Add user message to chat history
            user_message = HumanMessage(content=query)
            loop_id = self.chat_history.add_message(user_message)
            
            # Get all messages for LangGraph (filter out empty ones)
            all_messages = []
            for msg in self.chat_history.messages:
                content = getattr(msg, 'content', '')
                if content and content.strip():
                    all_messages.append(msg)
                else:
                    logger.warning(f"Skipping message with empty content: {type(msg).__name__}")
            
            logger.debug(f"Executing LangGraph with {len(all_messages)} messages")
            
            # Execute within proper parent message context
            async def execute_with_context():
                state = {"messages": all_messages}
                if react_context:
                    # Add any additional context to the state
                    for key, value in react_context.items():
                        if key != "message":  # Don't override messages
                            state[key] = value
                    
                return await self._langgraph_app.ainvoke(state)
            
            if parent_message:
                with parent_message_context(parent_message):
                    result = await execute_with_context()
            else:
                result = await execute_with_context()
            
            # Extract response content and add to chat history
            response_content = "No response generated"
            if "messages" in result and result["messages"]:
                # Get the last message which should be the AI response
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response_content = last_message.content
                    # Only add to history if it's not already there (avoid duplicates)
                    if last_message not in self.chat_history.messages:
                        self.chat_history.add_message(last_message, loop_id)
                        logger.debug(f"Added AI response to chat history: {len(last_message.content)} chars")
            
            return response_content
            
        except Exception as e:
            logger.error(f"Error in react_async: {e}")
            # Add error message to chat history
            error_message = AIMessage(content=f"Error: {str(e)}")
            self.chat_history.add_message(error_message)
            raise

    async def execute(self, *args, **kwargs) -> str:
        """Execute wrapper for compatibility."""
        query = args[0] if args else kwargs.get('query', '')
        return await self.react_async(query, kwargs)

    async def oneshot(self, prompt: str, query: str) -> str:
        """Execute with system prompt."""
        full_query = f"System: {prompt}\\n\\nUser: {query}"
        return await self.react_async(full_query)

    def get_info(self):
        """Return agent info for kernel communication."""
        tool_info = {
            tool.name: tool.description 
            for tool in self._tools
            if hasattr(tool, 'name') and hasattr(tool, 'description')
        }
        return {
            "name": self.__class__.__name__,
            "tools": tool_info,
            "framework": "LangGraph",
        }

    def log(self, event_type: str, content: typing.Any = None) -> None:
        """Log through Beaker kernel."""
        if self.context:
            self.context.beaker_kernel.log(f"agent_{event_type}", content)

    def debug(self, event_type: str, content: typing.Any = None) -> None:
        """Debug through Beaker kernel.""" 
        if self.context:
            self.context.beaker_kernel.debug(f"agent_{event_type}", content)

    async def ask_user(self, query: str) -> str:
        """Send query to user and return response."""
        if self.context:
            return await self.context.beaker_kernel.prompt_user(query, parent_message=None)
        return "No context available to ask user"

    # Compatibility methods for BeakerContext
    def disable(self, *tool_names):
        """Disable tools by name."""
        if not tool_names:
            return
        # Mark tools as disabled
        for tool_name in tool_names:
            for tool in self._tools:
                if hasattr(tool, 'name') and tool.name == tool_name:
                    setattr(tool, '_disabled', True)

    async def all_messages(self):
        """Return all messages (compatibility method)."""
        return []

    def set_auto_context(self, default_content: str, content_updater=None, auto_update: bool = True):
        """Set auto context (compatibility method)."""
        pass