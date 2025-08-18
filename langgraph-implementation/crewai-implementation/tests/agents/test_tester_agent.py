"""
Tests for the tester agent module.

This module contains tests for the tester agent functionality,
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

# Now import the tester_agent module
from agents.tester import TesterAgent


class TestTesterAgent:
    """Tests for the tester agent functionality."""
    
    def test_create_no_tools(self):
        """Test creating a tester agent with no tools."""
        agent = TesterAgent.create()
        
        assert agent is not None
        assert isinstance(agent, Agent)
        assert agent.role == "Software Tester"
        assert "Ensure code quality" in agent.goal
        assert "expert software tester" in agent.backstory
        assert agent.verbose is True
        assert agent.llm == "llama3.1:8b"
        assert agent.tools == []
        assert agent.allow_delegation is False
    
    def test_create_with_tools(self):
        """Test creating a tester agent with tools."""
        tool1 = BaseTool(name="Tool1", description="A test tool")
        tool2 = BaseTool(name="Tool2", description="Another test tool")
        
        agent = TesterAgent.create([tool1, tool2])
        
        assert agent is not None
        assert isinstance(agent, Agent)
        assert agent.role == "Software Tester"
        assert "Ensure code quality" in agent.goal
        assert "expert software tester" in agent.backstory
        assert agent.verbose is True
        assert agent.llm == "llama3.1:8b"
        assert len(agent.tools) == 2
        assert agent.tools[0] == tool1
        assert agent.tools[1] == tool2
        assert agent.allow_delegation is False
    
    def test_create_test_plan_task(self):
        """Test creating a test plan task."""
        agent = TesterAgent.create()
        task_description = "Build a Python function to calculate Fibonacci numbers"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        
        task = TesterAgent.create_test_plan_task(agent, task_description, requirements)
        
        assert task is not None
        assert isinstance(task, str)
        assert task_description in task
        assert "Create a comprehensive test plan" in task
        assert "Test strategy overview" in task
        assert "Unit test cases" in task
        assert "Integration test cases" in task
        assert "Edge cases to test" in task
        assert "Performance considerations" in task
        
        # Check that all requirements are included
        for req in requirements:
            assert req in task
    
    def test_create_test_cases_task(self):
        """Test creating a test cases task."""
        agent = TesterAgent.create()
        code = """
        def fibonacci(n):
            if n < 0:
                raise ValueError("Input must be a non-negative integer")
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b
        """
        language = "python"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        
        task = TesterAgent.create_test_cases_task(agent, code, language, requirements)
        
        assert task is not None
        assert isinstance(task, str)
        assert code in task
        assert language in task
        assert "Create test cases" in task
        assert "Unit tests" in task
        assert "Tests for edge cases" in task
        assert "Tests for error conditions" in task
        
        # Check that all requirements are included
        for req in requirements:
            assert req in task
    
    def test_create_evaluation_task(self):
        """Test creating an evaluation task."""
        agent = TesterAgent.create()
        code = """
        def fibonacci(n):
            if n < 0:
                raise ValueError("Input must be a non-negative integer")
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b
        """
        test_results = "All tests passed. 100% code coverage."
        
        task = TesterAgent.create_evaluation_task(agent, code, test_results)
        
        assert task is not None
        assert isinstance(task, str)
        assert code in task
        assert test_results in task
        assert "Evaluate the following code" in task
        assert "Overall assessment" in task
        assert "Identified issues" in task
        assert "Suggestions for improvement" in task
        assert "Code coverage" in task