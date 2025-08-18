"""
Mock implementations of langchain classes for testing.

This module provides mock implementations of the langchain classes used in the code,
allowing tests to run without depending on the actual langchain implementation.
"""

from typing import Dict, List, Any, Optional, Callable, Union


class BaseTool:
    """Mock implementation of langchain.tools.BaseTool."""
    
    def __init__(self, name: str = None, description: str = None, 
                 func: Callable = None, return_direct: bool = False, **kwargs):
        """Initialize a mock BaseTool."""
        self.name = name or "MockTool"
        self.description = description or "A mock tool for testing"
        self.func = func
        self.return_direct = return_direct
        self.kwargs = kwargs
    
    def __call__(self, *args, **kwargs) -> str:
        """Mock implementation of __call__ method."""
        if self.func:
            return self.func(*args, **kwargs)
        return f"Mock tool {self.name} called with args: {args}, kwargs: {kwargs}"
    
    def run(self, *args, **kwargs) -> str:
        """Mock implementation of run method."""
        return self.__call__(*args, **kwargs)


class Tool(BaseTool):
    """Mock implementation of langchain.tools.Tool."""
    
    def __init__(self, name: str = None, description: str = None, 
                 func: Callable = None, return_direct: bool = False, **kwargs):
        """Initialize a mock Tool."""
        super().__init__(name, description, func, return_direct, **kwargs)


def tool(func: Callable = None, **kwargs) -> Callable:
    """Mock implementation of langchain.tools.tool decorator."""
    def decorator(f: Callable) -> Tool:
        return Tool(
            name=kwargs.get("name", f.__name__),
            description=kwargs.get("description", f.__doc__),
            func=f,
            return_direct=kwargs.get("return_direct", False)
        )
    
    if func:
        return decorator(func)
    return decorator