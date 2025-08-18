"""
Tests for the tester agent module using unittest.

This module contains tests for the tester agent functionality,
including agent creation, prompt generation, and test case extraction.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to allow importing from the agents module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We'll use patch decorators in the test methods instead of patching at the module level

# Now import the tester_agent module
from agents.tester_agent import (
    create_tester_agent,
    create_test_plan_prompt,
    create_test_cases_prompt,
    create_evaluation_prompt,
    extract_test_cases_from_message,
    TESTER_SYSTEM_MESSAGE
)

class TestTesterAgent(unittest.TestCase):
    """Tests for the tester agent functionality."""
    
    @patch('agents.tester_agent.autogen.AssistantAgent')
    def test_create_tester_agent_default_config(self, mock_assistant_agent):
        """Test creating a tester agent with default configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_assistant_agent.return_value = mock_instance
        
        # Call the function under test
        agent = create_tester_agent()
        
        # Check that AssistantAgent was called with the correct arguments
        mock_assistant_agent.assert_called_once()
        args, kwargs = mock_assistant_agent.call_args
        
        self.assertEqual(kwargs['name'], "Tester")
        self.assertEqual(kwargs['system_message'], TESTER_SYSTEM_MESSAGE)
        self.assertIn('llm_config', kwargs)
        self.assertIn('config_list', kwargs['llm_config'])
    
    @patch('agents.tester_agent.autogen.AssistantAgent')
    def test_create_tester_agent_custom_config(self, mock_assistant_agent):
        """Test creating a tester agent with custom configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_assistant_agent.return_value = mock_instance
        
        custom_config = {
            "name": "CustomTester",
            "llm_config": {
                "temperature": 0.5
            }
        }
        
        # Call the function under test
        agent = create_tester_agent(custom_config)
        
        # Check that AssistantAgent was called with the correct arguments
        mock_assistant_agent.assert_called_once()
        args, kwargs = mock_assistant_agent.call_args
        
        self.assertEqual(kwargs['name'], "CustomTester")
        self.assertEqual(kwargs['system_message'], TESTER_SYSTEM_MESSAGE)
        self.assertEqual(kwargs['llm_config']['temperature'], 0.5)
    
    def test_create_test_plan_prompt(self):
        """Test creating a test plan prompt."""
        task = "Build a calculator app"
        requirements = [
            "Must support basic arithmetic operations",
            "Should have a user-friendly interface"
        ]
        
        prompt = create_test_plan_prompt(task, requirements)
        
        self.assertIn(task, prompt)
        self.assertIn("Must support basic arithmetic operations", prompt)
        self.assertIn("Should have a user-friendly interface", prompt)
        self.assertIn("Test strategy overview", prompt)
        self.assertIn("Edge cases to test", prompt)
    
    def test_create_test_cases_prompt(self):
        """Test creating test cases prompt."""
        code = "def add(a, b):\n    return a + b"
        language = "python"
        requirements = [
            "Must support basic arithmetic operations",
            "Should handle edge cases"
        ]
        
        prompt = create_test_cases_prompt(code, language, requirements)
        
        self.assertIn(code, prompt)
        self.assertIn(language, prompt)
        self.assertIn("Must support basic arithmetic operations", prompt)
        self.assertIn("Should handle edge cases", prompt)
        self.assertIn("Unit tests", prompt)
        self.assertIn("Tests for edge cases", prompt)
    
    def test_create_evaluation_prompt(self):
        """Test creating an evaluation prompt."""
        code = "def add(a, b):\n    return a + b"
        test_results = "All tests passed"
        
        prompt = create_evaluation_prompt(code, test_results)
        
        self.assertIn(code, prompt)
        self.assertIn(test_results, prompt)
        self.assertIn("Evaluate the following code based on test results", prompt)
        self.assertIn("Test Results", prompt)
    
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
        
        self.assertIn("def test_add():", test_cases)
        self.assertIn("assert add(1, 2) == 3", test_cases)
        self.assertNotIn("```", test_cases)

if __name__ == "__main__":
    unittest.main()