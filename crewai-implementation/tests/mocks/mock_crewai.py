"""
Mock implementations of crewai classes for testing.

This module provides mock implementations of the crewai classes used in the code,
allowing tests to run without depending on the actual crewai implementation.
"""

from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum


class Process(Enum):
    """Mock implementation of crewai.Process."""
    sequential = "sequential"
    hierarchical = "hierarchical"


class Agent:
    """Mock implementation of crewai.Agent."""
    
    def __init__(self, role: str, goal: str, backstory: str = "", verbose: bool = False, 
                 llm: str = None, tools: List[Any] = None, allow_delegation: bool = True, **kwargs):
        """Initialize a mock Agent."""
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.verbose = verbose
        self.llm = llm
        self.tools = tools or []
        self.allow_delegation = allow_delegation
        self.kwargs = kwargs
        self.messages = []
    
    def execute_task(self, task: Any) -> str:
        """Mock implementation of execute_task method."""
        # For testing, we'll return a simple response based on the task
        if "design" in task.description.lower():
            return """
            # Design
            
            ## Components
            - Component 1
            - Component 2
            
            ## Interfaces
            - Interface 1
            - Interface 2
            
            ## Data Flow
            - Data flows from Component 1 to Component 2
            
            ## Design Patterns
            - Factory Pattern
            - Observer Pattern
            
            ## Challenges
            - Challenge 1
            - Challenge 2
            """
        elif "implement" in task.description.lower() or "code" in task.description.lower():
            return """
            Here's the implementation:
            
            ```python
            def fibonacci(n):
                \"\"\"
                Calculate the nth Fibonacci number.
                
                Args:
                    n: The position in the Fibonacci sequence
                    
                Returns:
                    The nth Fibonacci number
                \"\"\"
                if n < 0:
                    raise ValueError("Input must be a non-negative integer")
                if n <= 1:
                    return n
                    
                a, b = 0, 1
                for _ in range(2, n + 1):
                    a, b = b, a + b
                return b
            ```
            """
        elif "test" in task.description.lower():
            return """
            Here are the test cases:
            
            ```python
            import unittest
            
            class TestFibonacci(unittest.TestCase):
                def test_positive_numbers(self):
                    self.assertEqual(fibonacci(0), 0)
                    self.assertEqual(fibonacci(1), 1)
                    self.assertEqual(fibonacci(5), 5)
                    self.assertEqual(fibonacci(10), 55)
                
                def test_negative_numbers(self):
                    with self.assertRaises(ValueError):
                        fibonacci(-1)
            ```
            """
        elif "evaluate" in task.description.lower():
            return """
            # Code Evaluation
            
            ## Assessment
            The code is well-implemented and passes all tests.
            
            ## Issues
            - No issues found
            
            ## Suggestions
            - Add type hints
            - Consider memoization for better performance
            
            ## Coverage
            The test coverage is 100%.
            """
        elif "refine" in task.description.lower():
            return """
            Here's the refined implementation:
            
            ```python
            from typing import int
            
            def fibonacci(n: int) -> int:
                \"\"\"
                Calculate the nth Fibonacci number.
                
                Args:
                    n: The position in the Fibonacci sequence
                    
                Returns:
                    The nth Fibonacci number
                    
                Raises:
                    ValueError: If n is negative
                \"\"\"
                if n < 0:
                    raise ValueError("Input must be a non-negative integer")
                if n <= 1:
                    return n
                    
                a, b = 0, 1
                for _ in range(2, n + 1):
                    a, b = b, a + b
                return b
            ```
            
            I've added type hints and improved the docstring to better document the function.
            """
        else:
            return "I don't have a specific response for this task."


class Task:
    """Mock implementation of crewai.Task."""
    
    def __init__(self, description: str, agent: Agent, expected_output: str = "", 
                 context: List[Any] = None, output: str = None, **kwargs):
        """Initialize a mock Task."""
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.context = context or []
        self.output = output
        self.kwargs = kwargs
    
    def execute(self) -> str:
        """Mock implementation of execute method."""
        return self.agent.execute_task(self)


class Crew:
    """Mock implementation of crewai.Crew."""
    
    def __init__(self, agents: List[Agent], tasks: List[Task], verbose: bool = False, 
                 process: Process = Process.sequential, **kwargs):
        """Initialize a mock Crew."""
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose
        self.process = process
        self.kwargs = kwargs
    
    def kickoff(self) -> Dict[str, Any]:
        """Mock implementation of kickoff method."""
        results = {}
        
        # Execute tasks based on the process
        if self.process == Process.sequential:
            for i, task in enumerate(self.tasks):
                # Replace placeholders in the task description with outputs from previous tasks
                if i > 0:
                    for j in range(i):
                        prev_task = self.tasks[j]
                        if prev_task.output:
                            placeholder = f"{{{prev_task.agent.role.lower()}_output}}"
                            task.description = task.description.replace(placeholder, prev_task.output)
                
                # Execute the task
                task.output = task.execute()
                results[f"task_{i+1}"] = task.output
        
        return results