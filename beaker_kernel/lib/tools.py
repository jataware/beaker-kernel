"""
Beaker tool system with automatic thought parameter injection.

Based on the Archytas approach but simplified for LangChain/LangGraph.
Automatically adds 'thought' parameters to tools like Archytas did.
"""

import asyncio
import inspect
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union, Annotated

from langchain_core.tools import BaseTool, tool as langchain_tool, StructuredTool
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

logger = logging.getLogger(__name__)


def _parse_docstring_parameters(func: Callable) -> Dict[str, str]:
    """Extract parameter descriptions from function docstring Args section."""
    docstring = func.__doc__
    if not docstring:
        return {}
    
    param_descriptions = {}
    
    # Look for Args: section in docstring
    lines = docstring.split('\n')
    in_args_section = False
    current_param = None
    current_desc = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check if we're entering the Args section
        if stripped.lower() in ['args:', 'arguments:', 'parameters:']:
            in_args_section = True
            continue
        
        # Check if we're leaving the Args section (Returns:, Raises:, etc.)
        if in_args_section and stripped.lower() in ['returns:', 'return:', 'raises:', 'examples:', 'example:', 'note:', 'notes:']:
            # Save the current parameter if we have one
            if current_param and current_desc:
                param_descriptions[current_param] = ' '.join(current_desc).strip()
            break
        
        if in_args_section and stripped:
            # Check if this line starts a new parameter (contains colon)
            if ':' in stripped:
                # Save previous parameter if exists
                if current_param and current_desc:
                    param_descriptions[current_param] = ' '.join(current_desc).strip()
                
                # Extract parameter name and start of description
                param_part, desc_part = stripped.split(':', 1)
                # Remove type annotations in parentheses
                param_name = param_part.split('(')[0].strip()
                current_param = param_name
                current_desc = [desc_part.strip()]
            elif current_param and stripped:
                # Continue description for current parameter
                current_desc.append(stripped)
    
    # Save the last parameter
    if current_param and current_desc:
        param_descriptions[current_param] = ' '.join(current_desc).strip()
    
    return param_descriptions


def _is_claude_environment() -> bool:
    """Check if we're likely running in a Claude/Anthropic environment."""
    try:
        from beaker_kernel.lib.utils import get_beaker_kernel
        
        kernel = get_beaker_kernel()
        if kernel and hasattr(kernel, 'context') and kernel.context:
            agent = getattr(kernel.context, 'agent', None)
            if agent and hasattr(agent, 'model'):
                # Check model class name
                model_class = type(agent.model).__name__.lower()
                if 'anthropic' in model_class or 'claude' in model_class:
                    return True
                
                # Check model name if available
                if hasattr(agent.model, 'model') and agent.model.model:
                    model_name = str(agent.model.model).lower()
                    if 'claude' in model_name or 'anthropic' in model_name:
                        return True
                
                # Check module name
                module_name = type(agent.model).__module__.lower()
                if 'anthropic' in module_name:
                    return True
        
        return False
    except Exception:
        # If we can't detect, default to False (no thought parameter)
        return False


def tool(func: Callable = None, *, name: str = None, description: str = None) -> Callable:
    """
    Decorator to create LangChain tools with automatic thought parameter injection.
    
    Like Archytas, automatically adds a 'thought' parameter to all tools for UI display.
    
    Usage:
        @tool
        def my_tool(param: str) -> str:
            '''Tool description'''
            return f"Result: {param}"
    """
    def decorator(func: Callable) -> StructuredTool:
        # Extract metadata and preserve original function for docstring parsing
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        # Get function signature
        sig = inspect.signature(func)
        
        # Parse parameter descriptions from docstring
        param_descriptions = _parse_docstring_parameters(func)
        
        # Build argument dictionary like Archytas did
        arg_dict = {}
        
        # Add original function parameters
        for param_name, param in sig.parameters.items():
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            # Use docstring description if available, otherwise fall back to generic
            param_desc = param_descriptions.get(param_name, f"Parameter {param_name}")
            
            if param.default != inspect.Parameter.empty:
                arg_dict[param_name] = Annotated[param_type, FieldInfo(description=param_desc, default=param.default)]
            else:
                arg_dict[param_name] = Annotated[param_type, FieldInfo(description=param_desc)]
        
        # Automatically add thought parameter like Archytas did (but only for Claude models)
        if "thought" not in arg_dict and _is_claude_environment():
            arg_dict["thought"] = Annotated[str, FieldInfo(description="Reasoning around why this tool is being called.", default="")]
        
        # Create Pydantic model for arguments
        tool_schema = create_model(f"{tool_name}Schema", **arg_dict)
        
        # Create wrapper function (thought extraction now handled at graph level)
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Remove thought parameter if it somehow gets through
                kwargs.pop('thought', '')
                
                # Call original function
                result = await func(*args, **kwargs)
                
                # Log and return result
                _log_tool_result(tool_name, kwargs, result)
                return str(result) if result is not None else ""
            wrapper_func = async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Remove thought parameter if it somehow gets through
                kwargs.pop('thought', '')
                
                # Call original function
                result = func(*args, **kwargs)
                
                # Log and return result
                _log_tool_result(tool_name, kwargs, result)
                return str(result) if result is not None else ""
            wrapper_func = sync_wrapper
        
        # Create StructuredTool like Archytas did
        if inspect.iscoroutinefunction(func):
            # For async functions, use the async versions
            return StructuredTool(
                name=tool_name,
                description=tool_description,
                args_schema=tool_schema,
                coroutine=wrapper_func,  # Use coroutine parameter for async
            )
        else:
            return StructuredTool(
                name=tool_name,
                description=tool_description,
                args_schema=tool_schema,
                func=wrapper_func,
            )
    
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