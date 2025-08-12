"""
Beaker agent implementation.
"""

import asyncio
import logging
import typing
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

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
        
        # Initialize system prompt handling
        self._system_prompt_callback = None
        
        # Always use custom LangGraph with thought extraction for all models
        # (The difference is in whether tools have thought parameters, not the graph itself)
        logger.debug(f"Using thought-extracting LangGraph for {type(self.model).__name__}")
        self._langgraph_app = self._create_thought_extracting_graph()
        
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
            
            # Get all messages for LangGraph (filter out empty ones and clean for serialization)
            all_messages = []
            
            # Add system prompt if available
            if self._system_prompt_callback:
                try:
                    system_content = await self._get_system_prompt_async()
                    if system_content and system_content.strip():
                        from langchain_core.messages import SystemMessage
                        system_msg = SystemMessage(content=system_content)
                        all_messages.append(system_msg)
                        logger.debug("Added dynamic system prompt to messages")
                except Exception as e:
                    logger.warning(f"Failed to generate system prompt: {e}")
            
            # Add existing messages from chat history
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
                    # Handle different content formats (string vs list for different providers)
                    content = last_message.content
                    if isinstance(content, list):
                        # Anthropic format: extract text from list of content blocks
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                text_parts.append(item.get('text', ''))
                        response_content = ' '.join(text_parts).strip()
                    else:
                        # String format (OpenAI, Gemini, etc.)
                        response_content = str(content).strip()
                    
                    # Only add to history if it's not already there (avoid duplicates)
                    if last_message not in self.chat_history.messages:
                        self.chat_history.add_message(last_message, loop_id)
                        logger.debug(f"Added AI response to chat history: {len(str(last_message.content))} chars")
            
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
        """Set auto context for system prompt."""
        if content_updater and callable(content_updater):
            self._system_prompt_callback = content_updater
        elif default_content:
            self._system_prompt_callback = lambda: default_content
        else:
            self._system_prompt_callback = None
            
        logger.debug(f"Set auto context with callback: {self._system_prompt_callback is not None}")

    async def _get_system_prompt_async(self):
        """Generate system prompt content asynchronously."""
        import inspect
        
        if self._system_prompt_callback:
            try:
                # Call the callback to get updated context
                result = self._system_prompt_callback()
                
                # Handle async callbacks properly
                if inspect.iscoroutine(result):
                    prompt_content = await result
                    return prompt_content
                else:
                    # Synchronous callback
                    return result
            except Exception as e:
                logger.warning(f"Failed to generate auto context: {e}")
                return "You are a helpful AI assistant."
        else:
            return "You are a helpful AI assistant."

    def _is_claude_model(self) -> bool:
        """Check if the current model is a Claude/Anthropic model."""
        try:
            # Check model class name
            model_class = type(self.model).__name__.lower()
            if 'anthropic' in model_class or 'claude' in model_class:
                return True
            
            # Check model name if available
            if hasattr(self.model, 'model') and self.model.model:
                model_name = str(self.model.model).lower()
                if 'claude' in model_name or 'anthropic' in model_name:
                    return True
            
            # Check module name
            module_name = type(self.model).__module__.lower()
            if 'anthropic' in module_name:
                return True
                
            return False
        except Exception as e:
            logger.warning(f"Failed to detect model type: {e}")
            return False

    def _create_thought_extracting_graph(self):
        """Create a custom LangGraph with thought extraction node."""
        from langgraph.graph import END
        
        # Create the state graph
        workflow = StateGraph(MessagesState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("extract_thoughts", self._extract_thoughts_node)  
        workflow.add_node("tools", ToolNode(self._tools))
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add edges
        workflow.add_conditional_edges(
            "agent",
            self._should_extract_thoughts,
            {
                "extract_thoughts": "extract_thoughts",
                "end": END,
            }
        )
        
        workflow.add_edge("extract_thoughts", "tools")
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()

    def _agent_node(self, state: MessagesState):
        """The main agent node that generates responses."""
        # Bind tools to the model so it can call them
        model_with_tools = self.model.bind_tools(self._tools)
        logger.debug(f"Agent node: {len(self._tools)} tools bound to model")
        response = model_with_tools.invoke(state["messages"])
        logger.debug(f"Agent response type: {type(response)}, has tool_calls: {hasattr(response, 'tool_calls')}")
        if hasattr(response, 'tool_calls'):
            logger.debug(f"Tool calls: {len(response.tool_calls) if response.tool_calls else 0}")
        return {"messages": [response]}

    def _should_extract_thoughts(self, state: MessagesState):
        """Determine if we need to extract thoughts from tool calls."""
        last_message = state["messages"][-1]
        logger.debug(f"Should extract thoughts check - message type: {type(last_message)}")
        if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.debug(f"Found {len(last_message.tool_calls)} tool calls - going to extract_thoughts")
            return "extract_thoughts"
        logger.debug("No tool calls found - going to end")
        return "end"

    def _extract_thoughts_node(self, state: MessagesState):
        """Extract thoughts from tool calls and send to UI (just like Archytas did)."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
            extracted_thoughts = []
            
            # Get the AI message content to use as thought when no explicit thought parameter
            ai_content = ""
            if hasattr(last_message, 'content') and last_message.content:
                if isinstance(last_message.content, list):
                    # Handle list format (Anthropic)
                    ai_content = "\n".join(item.get('text', '') for item in last_message.content if item.get('type') == 'text')
                else:
                    # Handle string format
                    ai_content = str(last_message.content)
            
            for tool_call in last_message.tool_calls:
                if 'args' in tool_call and isinstance(tool_call['args'], dict):
                    args = tool_call['args']
                    tool_name = tool_call.get('name', 'unknown_tool')
                    
                    # Check for malformed tool calls (missing required parameters)
                    if tool_name == 'run_code' and (not args or 'code' not in args or not args.get('code', '').strip()):
                        logger.warning(f"Detected malformed run_code call with missing/empty code parameter - adding fallback")
                        # Add helpful code parameter to prevent validation error
                        args['code'] = f"# Error: The model generated an empty run_code call.\n# This is a model inference issue, not a problem with your request.\nprint('Model generated empty run_code call - please try again')"
                    
                    # Extract thought - use AI content if no explicit thought, fallback as last resort
                    if 'thought' in args:
                        thought = args.pop('thought')
                    elif ai_content.strip():
                        thought = ai_content.strip()
                    else:
                        thought = f"Calling tool '{tool_name}'"
                    
                    extracted_thoughts.append(thought)
                    
                    # Send thought to UI
                    self._send_thought_to_ui(thought, tool_name, str(args))
                    
                    logger.debug(f"Extracted thought for {tool_name}: {thought[:50]}...")
            
            # If message has no content but has tool calls, use thoughts as content (like Archytas)
            if not last_message.content and extracted_thoughts:
                last_message.content = "\n".join(extracted_thoughts)
                logger.debug("Set message content to extracted thoughts")
        
        return {"messages": messages}

    def _send_thought_to_ui(self, thought: str, tool_name: str, tool_input: str):
        """Send thought to UI via kernel handle_thoughts."""
        try:
            if self.context and self.context.beaker_kernel and thought.strip():
                # Get parent message context
                from beaker_kernel.lib.utils import get_parent_message
                parent_context = get_parent_message()
                parent_header = parent_context.get('parent_message').header if parent_context and 'parent_message' in parent_context else {}
                
                self.context.beaker_kernel.handle_thoughts(
                    thought=thought.strip(),
                    tool_name=tool_name,
                    tool_input=tool_input[:100] + "..." if len(tool_input) > 100 else tool_input,
                    parent_header=parent_header
                )
                logger.debug(f"Sent thought to UI: {thought[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to send thought to UI: {e}")