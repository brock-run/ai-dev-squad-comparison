"""
Tests for the tester agent module.

This module contains tests for the tester agent functionality,
including agent creation, prompt generation, and test case extraction.
"""

import pytest
from unittest.mock import patch
import pyautogen as autogen

from agents.tester_agent import (
    create_tester_agent,
    create_test_plan_prompt,
    create_test_cases_prompt,
    create_evaluation_prompt,
    extract_test_cases_from_message,
    TESTER_SYSTEM_MESSAGE
)

class TestTesterAgent:
    """Tests for the tester agent functionality."""
    
    def test_create_tester_agent_default_config(self):
        """Test creating a tester agent with default configuration."""
        agent = create_tester_agent()
        
        assert agent.name == "Tester"
        assert agent.system_message == TESTER_SYSTEM_MESSAGE
        assert "config_list" in agent.llm_config
        
    def test_create_tester_agent_custom_config(self):
        """Test creating a tester agent with custom configuration."""
        custom_config = {
            "name": "CustomTester",
            "llm_config": {
                "temperature": 0.5
            }
        }
        
        agent = create_tester_agent(custom_config)
        
        assert agent.name == "CustomTester"
        assert agent.system_message == TESTER_SYSTEM_MESSAGE
        assert agent.llm_config["temperature"] == 0.5
    
    def test_create_test_plan_prompt(self):
        """Test creating a test plan prompt."""
        task = "Build a calculator app"
        requirements = [
            "Must support basic arithmetic operations",
            "Should have a user-friendly interface"
        ]
        
        prompt = create_test_plan_prompt(task, requirements)
        
        assert task in prompt
        assert "Must support basic arithmetic operations" in prompt
        assert "Should have a user-friendly interface" in prompt
        assert "Test strategy overview" in prompt
        assert "Edge cases to test" in prompt
        
    def test_create_test_cases_prompt(self):
        """Test creating test cases prompt."""
        code = "def add(a, b):\n    return a + b"
        language = "python"
        requirements = [
            "Must support basic arithmetic operations",
            "Should handle edge cases"
        ]
        
        prompt = create_test_cases_prompt(code, language, requirements)
        
        assert code in prompt
        assert language in prompt
        assert "Must support basic arithmetic operations" in prompt
        assert "Should handle edge cases" in prompt
        assert "Unit tests that cover all functionality" in prompt
        assert "Tests for edge cases" in prompt
        
    def test_create_evaluation_prompt(self):
        """Test creating an evaluation prompt."""
        code = "def add(a, b):\n    return a + b"
        test_results = "All tests passed"
        
        prompt = create_evaluation_prompt(code, test_results)
        
        assert code in prompt
        assert test_results in prompt
        assert "Evaluate the following code based on test results" in prompt
        assert "Test Results" in prompt
        
    def test_extract_test_cases_from_message_with_markers(self):
        """Test extracting test cases from a message with code block markers."""
        message = """
        Here are the test cases:
        
        ```python
        def test_add():
            assert add(1, 2) == 3
        ```
        
        These tests verify the add function.
        """
        
        test_cases = extract_test_cases_from_message(message)
        
        assert "def test_add():" in test_cases
        assert "assert add(1, 2) == 3" in test_cases
        assert "```" not in test_cases