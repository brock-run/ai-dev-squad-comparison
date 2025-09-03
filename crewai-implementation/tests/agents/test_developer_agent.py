"""
Tests for the developer agent module.

This module contains tests for the developer agent functionality,
including agent creation and task generation.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to allow importing from the agents module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import mock classes
from tests.mocks.mock_crewai import Agent
from tests.mocks.mock_langchain import BaseTool

# Patch the crewai and langchain modules with our mocks
sys.modules['crewai'] = MagicMock()
sys.modules['crewai'].Agent = Agent
sys.modules['langchain.tools'] = MagicMock()
sys.modules['langchain.tools'].BaseTool = BaseTool

# Now import the developer_agent module
from agents.developer import DeveloperAgent


class TestDeveloperAgent:
    """Tests for the developer agent functionality."""
    
    def test_create_no_tools(self):
        """Test creating a developer agent with no tools."""
        agent = DeveloperAgent.create()
        
        assert agent is not None
        assert isinstance(agent, Agent)
        assert agent.role == "Software Developer"
        assert "Implement high-quality code" in agent.goal
        assert "expert software developer" in agent.backstory
        assert agent.verbose is True
        assert agent.llm == "codellama:13b"
        assert agent.tools == []
        assert agent.allow_delegation is False
    
    def test_create_with_tools(self):
        """Test creating a developer agent with tools."""
        tool1 = BaseTool(name="Tool1", description="A test tool")
        tool2 = BaseTool(name="Tool2", description="Another test tool")
        
        agent = DeveloperAgent.create([tool1, tool2])
        
        assert agent is not None
        assert isinstance(agent, Agent)
        assert agent.role == "Software Developer"
        assert "Implement high-quality code" in agent.goal
        assert "expert software developer" in agent.backstory
        assert agent.verbose is True
        assert agent.llm == "codellama:13b"
        assert len(agent.tools) == 2
        assert agent.tools[0] == tool1
        assert agent.tools[1] == tool2
        assert agent.allow_delegation is False
    
    def test_create_implementation_task(self):
        """Test creating an implementation task."""
        agent = DeveloperAgent.create()
        task_description = "Build a Python function to calculate Fibonacci numbers"
        design = """
        # Design
        
        ## Components
        - Fibonacci function
        - Error handling
        
        ## Interfaces
        - Function signature: fibonacci(n)
        
        ## Data Flow
        - Input validation -> calculation -> result
        
        ## Design Patterns
        - Iterative approach for performance
        
        ## Challenges
        - Handling negative numbers
        """
        language = "python"
        
        task = DeveloperAgent.create_implementation_task(agent, task_description, design, language)
        
        assert task is not None
        assert isinstance(task, str)
        assert task_description in task
        assert design in task
        assert language in task
        assert "Implement code for the following task" in task
        assert "Complete implementation" in task
        assert "Proper error handling" in task
        assert "Comments and documentation" in task
        assert "necessary imports" in task
    
    def test_create_refine_task(self):
        """Test creating a code refinement task."""
        agent = DeveloperAgent.create()
        code = """
        def fibonacci(n):
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b
        """
        feedback = "Add error handling for negative numbers and add type hints."
        language = "python"
        
        task = DeveloperAgent.create_refine_task(agent, code, feedback, language)
        
        assert task is not None
        assert isinstance(task, str)
        assert code in task
        assert feedback in task
        assert language in task
        assert "Refine the following" in task
        assert "Original Code" in task
        assert "Feedback" in task
        assert "improved code" in task
        assert "changes and reasoning" in task