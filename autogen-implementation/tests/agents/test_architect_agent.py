"""
Tests for the architect agent module.

This module contains tests for the architect agent functionality,
including agent creation and prompt generation.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to allow importing from the agents module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import mock autogen classes
from tests.mocks.mock_autogen import AssistantAgent

# Patch the autogen module with our mock
sys.modules['pyautogen'] = MagicMock()
sys.modules['pyautogen'].AssistantAgent = AssistantAgent

from agents.architect_agent import (
    create_architect_agent,
    create_design_prompt,
    analyze_requirements_prompt,
    ARCHITECT_SYSTEM_MESSAGE
)

class TestArchitectAgent:
    """Tests for the architect agent functionality."""
    
    def test_create_architect_agent_default_config(self):
        """Test creating an architect agent with default configuration."""
        agent = create_architect_agent()
        
        assert agent.name == "Architect"
        assert agent.system_message == ARCHITECT_SYSTEM_MESSAGE
        assert "config_list" in agent.llm_config
        
    def test_create_architect_agent_custom_config(self):
        """Test creating an architect agent with custom configuration."""
        custom_config = {
            "name": "CustomArchitect",
            "llm_config": {
                "temperature": 0.5
            }
        }
        
        agent = create_architect_agent(custom_config)
        
        assert agent.name == "CustomArchitect"
        assert agent.system_message == ARCHITECT_SYSTEM_MESSAGE
        assert agent.llm_config["temperature"] == 0.5
    
    def test_create_design_prompt(self):
        """Test creating a design prompt."""
        task = "Build a calculator app"
        requirements = [
            "Must support basic arithmetic operations",
            "Should have a user-friendly interface"
        ]
        
        prompt = create_design_prompt(task, requirements)
        
        assert task in prompt
        assert "Must support basic arithmetic operations" in prompt
        assert "Should have a user-friendly interface" in prompt
        assert "Component breakdown" in prompt
        assert "Interface definitions" in prompt
        
    def test_analyze_requirements_prompt(self):
        """Test creating a requirements analysis prompt."""
        requirements = [
            "Must support basic arithmetic operations",
            "Should have a user-friendly interface"
        ]
        
        prompt = analyze_requirements_prompt(requirements)
        
        assert "Must support basic arithmetic operations" in prompt
        assert "Should have a user-friendly interface" in prompt
        assert "Key functional requirements" in prompt
        assert "Non-functional requirements" in prompt