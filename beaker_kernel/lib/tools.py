"""
Native LangChain tool system for Beaker.

Provides a clean @tool decorator that works directly with LangChain/LangGraph
without any Archytas compatibility layers.
"""

import asyncio
import inspect
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

from langchain_core.tools import BaseTool, tool as langchain_tool
from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)


def tool(func: Callable = None, *, name: str = None, description: str = None) -> Callable:
    """
    Decorator to create LangChain tools with Beaker execution context.
    
    Usage:
        @tool
        def my_tool(param: str) -> str:
            '''Tool description'''
            return f"Result: {param}"
            
        @tool(name="custom_name", description="Custom description")
        def another_tool(x: int, y: int = 5) -> str:
            return f"Sum: {x + y}"
    """
    def decorator(func: Callable) -> BaseTool:
        # Extract metadata
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        # Get function signature for schema creation
        sig = inspect.signature(func)
        
        # Create parameter schema
        params = {}
        for param_name, param in sig.parameters.items():
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            
            if param.default != inspect.Parameter.empty:
                params[param_name] = (param_type, Field(default=param.default))
            else:
                params[param_name] = (param_type, Field(...))
        
        # Create Pydantic schema
        tool_schema = create_model(f"{tool_name}Schema", **params) if params else None
        
        # Create wrapper that handles execution context
        @wraps(func)
        def wrapper(*args, **kwargs):
            from beaker_kernel.lib.utils import get_execution_context, get_beaker_kernel
            
            # Get execution context
            context = get_execution_context() or {}
            kernel = get_beaker_kernel()
            
            # Log tool invocation
            if kernel:
                kernel.log("agent_react_tool", {"tool": tool_name, "input": kwargs or args})
            
            try:
                # Execute the tool
                if inspect.iscoroutinefunction(func):
                    # Handle async functions
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If we're already in an event loop, create a task
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, func(*args, **kwargs))
                                result = future.result()
                        else:
                            result = loop.run_until_complete(func(*args, **kwargs))
                    except RuntimeError:
                        result = asyncio.run(func(*args, **kwargs))
                else:
                    result = func(*args, **kwargs)
                
                # Log result
                if kernel:
                    kernel.log("agent_react_tool_output", {
                        "tool": tool_name,
                        "input": kwargs or args,
                        "output": result
                    })
                
                return str(result) if result is not None else ""
                
            except Exception as e:
                error_msg = f"Error in {tool_name}: {str(e)}"
                logger.error(error_msg)
                
                if kernel:
                    kernel.log("agent_react_tool_output", {
                        "tool": tool_name,
                        "input": kwargs or args,
                        "output": error_msg
                    })
                
                return error_msg
        
        # Create LangChain tool
        return langchain_tool(
            tool_name,
            return_direct=False,
            args_schema=tool_schema
        )(wrapper)
    
    # Handle both @tool and @tool() usage
    if func is None:
        return decorator
    else:
        return decorator(func)


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