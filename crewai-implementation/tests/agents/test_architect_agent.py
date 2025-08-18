"""
Tests for the architect agent module.

This module contains tests for the architect agent functionality,
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

# Now import the architect_agent module
from agents.architect import ArchitectAgent


class TestArchitectAgent:
    """Tests for the architect agent functionality."""
    
    def test_create_no_tools(self):
        """Test creating an architect agent with no tools."""
        agent = ArchitectAgent.create()
        
        assert agent is not None
        assert isinstance(agent, Agent)
        assert agent.role == "Software Architect"
        assert "Create optimal software architecture designs" in agent.goal
        assert "expert software architect" in agent.backstory
        assert agent.verbose is True
        assert agent.llm == "llama3.1:8b"
        assert agent.tools == []
        assert agent.allow_delegation is False
    
    def test_create_with_tools(self):
        """Test creating an architect agent with tools."""
        tool1 = BaseTool(name="Tool1", description="A test tool")
        tool2 = BaseTool(name="Tool2", description="Another test tool")
        
        agent = ArchitectAgent.create([tool1, tool2])
        
        assert agent is not None
        assert isinstance(agent, Agent)
        assert agent.role == "Software Architect"
        assert "Create optimal software architecture designs" in agent.goal
        assert "expert software architect" in agent.backstory
        assert agent.verbose is True
        assert agent.llm == "llama3.1:8b"
        assert len(agent.tools) == 2
        assert agent.tools[0] == tool1
        assert agent.tools[1] == tool2
        assert agent.allow_delegation is False
    
    def test_create_design_task(self):
        """Test creating a design task."""
        agent = ArchitectAgent.create()
        task_description = "Build a Python function to calculate Fibonacci numbers"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        
        task = ArchitectAgent.create_design_task(agent, task_description, requirements)
        
        assert task is not None
        assert isinstance(task, str)
        assert task_description in task
        assert "Create a high-level design" in task
        assert "Component breakdown" in task
        assert "Interface definitions" in task
        assert "Data flow" in task
        assert "Key design patterns" in task
        assert "Potential challenges" in task
        
        # Check that all requirements are included
        for req in requirements:
            assert req in task