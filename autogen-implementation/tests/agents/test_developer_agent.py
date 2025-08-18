"""
Tests for the developer agent module.

This module contains tests for the developer agent functionality,
including agent creation, prompt generation, and code extraction.
"""

import pytest
from unittest.mock import patch
import pyautogen as autogen

from agents.developer_agent import (
    create_developer_agent,
    create_implementation_prompt,
    create_refine_code_prompt,
    extract_code_from_message,
    DEVELOPER_SYSTEM_MESSAGE
)

class TestDeveloperAgent:
    """Tests for the developer agent functionality."""
    
    def test_create_developer_agent_default_config(self):
        """Test creating a developer agent with default configuration."""
        agent = create_developer_agent()
        
        assert agent.name == "Developer"
        assert agent.system_message == DEVELOPER_SYSTEM_MESSAGE
        assert "config_list" in agent.llm_config
        
    def test_create_developer_agent_custom_config(self):
        """Test creating a developer agent with custom configuration."""
        custom_config = {
            "name": "CustomDeveloper",
            "llm_config": {
                "temperature": 0.5
            }
        }
        
        agent = create_developer_agent(custom_config)
        
        assert agent.name == "CustomDeveloper"
        assert agent.system_message == DEVELOPER_SYSTEM_MESSAGE
        assert agent.llm_config["temperature"] == 0.5
    
    def test_create_implementation_prompt(self):
        """Test creating an implementation prompt."""
        task = "Build a calculator app"
        design = "A simple calculator with add, subtract, multiply, divide functions"
        language = "python"
        
        prompt = create_implementation_prompt(task, design, language)
        
        assert task in prompt
        assert design in prompt
        assert language in prompt
        assert "Complete implementation" in prompt
        assert "Proper error handling" in prompt
        
    def test_create_refine_code_prompt(self):
        """Test creating a code refinement prompt."""
        code = "def add(a, b):\n    return a + b"
        feedback = "Add type hints and docstring"
        language = "python"
        
        prompt = create_refine_code_prompt(code, feedback, language)
        
        assert code in prompt
        assert feedback in prompt
        assert language in prompt
        assert "Original Code" in prompt
        assert "Feedback" in prompt
        
    def test_extract_code_from_message_with_markers(self):
        """Test extracting code from a message with code block markers."""
        message = """
        Here's the implementation:
        
        ```python
        def add(a, b):
            return a + b
        ```
        
        This function adds two numbers.
        """
        
        code = extract_code_from_message(message)
        
        assert "def add(a, b):" in code
        assert "return a + b" in code
        assert "```" not in code
        
    def test_extract_code_from_message_without_markers(self):
        """Test extracting code from a message without code block markers."""
        message = """
        Here's the implementation:
        
        def add(a, b):
            return a + b
        
        This function adds two numbers.
        """
        
        code = extract_code_from_message(message)
        
        assert "def add(a, b):" in code
        assert "return a + b" in code