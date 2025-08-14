"""
Beaker tool system using native LangChain tools with Beaker-specific logging.
"""

import inspect
import logging
from functools import wraps
from typing import Any, Callable

from langchain_core.tools import tool as langchain_tool, BaseTool

logger = logging.getLogger(__name__)


def tool(func: Callable = None, *, name: str = None, description: str = None):
    """
    Wrapper around LangChain's @tool that adds Beaker logging.
    
    Usage:
        @tool
        def my_tool(param: str) -> str:
            '''Tool description
            
            Args:
                param: Description of parameter
            '''
            return f"Result: {param}"
    """
    def decorator(func: Callable):
        # Create the LangChain tool with proper docstring parsing
        langchain_decorated = langchain_tool(func, parse_docstring=True)
        
        # Override name and description if provided
        if name:
            langchain_decorated.name = name
        if description:
            langchain_decorated.description = description
        
        # Add logging wrapper
        if inspect.iscoroutinefunction(func):
            # Store original coroutine before replacing it
            original_coroutine = langchain_decorated.coroutine
            
            @wraps(original_coroutine)
            async def async_logging_wrapper(*args, **kwargs):
                tool_name = langchain_decorated.name
                result = await original_coroutine(*args, **kwargs)
                _log_tool_result(tool_name, kwargs, result)
                return result
            
            # Replace the coroutine with our logging wrapper
            langchain_decorated.coroutine = async_logging_wrapper
        else:
            # Store original function before replacing it
            original_func = langchain_decorated.func
            
            @wraps(original_func)
            def sync_logging_wrapper(*args, **kwargs):
                tool_name = langchain_decorated.name
                result = original_func(*args, **kwargs)
                _log_tool_result(tool_name, kwargs, result)
                return result
            
            # Replace the func with our logging wrapper
            langchain_decorated.func = sync_logging_wrapper
        
        return langchain_decorated
    
    # Handle both @tool and @tool() usage
    if func is None:
        return decorator
    else:
        return decorator(func)



def _log_tool_result(tool_name: str, tool_input: dict, result: Any):
    """Log tool execution for debugging."""
    try:
        from beaker_kernel.lib.utils import get_beaker_kernel
        
        kernel = get_beaker_kernel()
        if kernel:
            kernel.log("agent_react_tool", {"tool": tool_name, "input": tool_input})
            kernel.log("agent_react_tool_output", {
                "tool": tool_name,
                "input": tool_input,
                "output": str(result)
            })
    except Exception as e:
        logger.warning(f"Failed to log tool result for {tool_name}: {e}")


class BeakerTool(BaseTool):
    """
    Base class for more complex Beaker tools that need access to kernel context.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _run(self, *args, **kwargs) -> str:
        """Synchronous execution with Beaker context."""
        from beaker_kernel.lib.utils import get_beaker_kernel
        
        kernel = get_beaker_kernel()
        if kernel:
            kernel.log("agent_react_tool", {"tool": self.name, "input": kwargs or args})
        
        try:
            result = self.execute(*args, **kwargs)
            
            if kernel:
                kernel.log("agent_react_tool_output", {
                    "tool": self.name,
                    "input": kwargs or args,
                    "output": result
                })
            
            return str(result) if result is not None else ""
            
        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            logger.error(error_msg)
            
            if kernel:
                kernel.log("agent_react_tool_output", {
                    "tool": self.name,
                    "input": kwargs or args,
                    "output": error_msg
                })
            
            return error_msg
    
    async def _arun(self, *args, **kwargs) -> str:
        """Asynchronous execution with Beaker context."""
        from beaker_kernel.lib.utils import get_beaker_kernel
        
        kernel = get_beaker_kernel()
        if kernel:
            kernel.log("agent_react_tool", {"tool": self.name, "input": kwargs or args})
        
        try:
            if hasattr(self, 'aexecute'):
                result = await self.aexecute(*args, **kwargs)
            else:
                result = self.execute(*args, **kwargs)
            
            if kernel:
                kernel.log("agent_react_tool_output", {
                    "tool": self.name,
                    "input": kwargs or args,
                    "output": result
                })
            
            return str(result) if result is not None else ""
            
        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            logger.error(error_msg)
            
            if kernel:
                kernel.log("agent_react_tool_output", {
                    "tool": self.name,
                    "input": kwargs or args,
                    "output": error_msg
                })
            
            return error_msg
    
    def execute(self, *args, **kwargs) -> Any:
        """Override this method to implement the tool's functionality."""
        raise NotImplementedError("Subclasses must implement execute()")
    
    async def aexecute(self, *args, **kwargs) -> Any:
        """Override this method for async tool functionality."""
        return self.execute(*args, **kwargs)