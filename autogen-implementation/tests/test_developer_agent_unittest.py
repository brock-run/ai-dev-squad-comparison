"""
Tests for the developer agent module using unittest.

This module contains tests for the developer agent functionality,
including agent creation, prompt generation, and code extraction.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to allow importing from the agents module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We'll use patch decorators in the test methods instead of patching at the module level

# Now import the developer_agent module
from agents.developer_agent import (
    create_developer_agent,
    create_implementation_prompt,
    create_refine_code_prompt,
    extract_code_from_message,
    DEVELOPER_SYSTEM_MESSAGE
)

class TestDeveloperAgent(unittest.TestCase):
    """Tests for the developer agent functionality."""
    
    @patch('agents.developer_agent.autogen.AssistantAgent')
    def test_create_developer_agent_default_config(self, mock_assistant_agent):
        """Test creating a developer agent with default configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_assistant_agent.return_value = mock_instance
        
        # Call the function under test
        agent = create_developer_agent()
        
        # Check that AssistantAgent was called with the correct arguments
        mock_assistant_agent.assert_called_once()
        args, kwargs = mock_assistant_agent.call_args
        
        self.assertEqual(kwargs['name'], "Developer")
        self.assertEqual(kwargs['system_message'], DEVELOPER_SYSTEM_MESSAGE)
        self.assertIn('llm_config', kwargs)
        self.assertIn('config_list', kwargs['llm_config'])
    
    @patch('agents.developer_agent.autogen.AssistantAgent')
    def test_create_developer_agent_custom_config(self, mock_assistant_agent):
        """Test creating a developer agent with custom configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_assistant_agent.return_value = mock_instance
        
        custom_config = {
            "name": "CustomDeveloper",
            "llm_config": {
                "temperature": 0.5
            }
        }
        
        # Call the function under test
        agent = create_developer_agent(custom_config)
        
        # Check that AssistantAgent was called with the correct arguments
        mock_assistant_agent.assert_called_once()
        args, kwargs = mock_assistant_agent.call_args
        
        self.assertEqual(kwargs['name'], "CustomDeveloper")
        self.assertEqual(kwargs['system_message'], DEVELOPER_SYSTEM_MESSAGE)
        self.assertEqual(kwargs['llm_config']['temperature'], 0.5)
    
    def test_create_implementation_prompt(self):
        """Test creating an implementation prompt."""
        task = "Build a calculator app"
        design = "A simple calculator with add, subtract, multiply, divide functions"
        language = "python"
        
        prompt = create_implementation_prompt(task, design, language)
        
        self.assertIn(task, prompt)
        self.assertIn(design, prompt)
        self.assertIn(language, prompt)
        self.assertIn("Complete implementation", prompt)
        self.assertIn("Proper error handling", prompt)
    
    def test_create_refine_code_prompt(self):
        """Test creating a code refinement prompt."""
        code = "def add(a, b):\n    return a + b"
        feedback = "Add type hints and docstring"
        language = "python"
        
        prompt = create_refine_code_prompt(code, feedback, language)
        
        self.assertIn(code, prompt)
        self.assertIn(feedback, prompt)
        self.assertIn(language, prompt)
        self.assertIn("Original Code", prompt)
        self.assertIn("Feedback", prompt)
    
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
        
        self.assertIn("def add(a, b):", code)
        self.assertIn("return a + b", code)
        self.assertNotIn("```", code)
    
    def test_extract_code_from_message_without_markers(self):
        """Test extracting code from a message without code block markers."""
        message = """
        Here's the implementation:
        
        def add(a, b):
            return a + b
        
        This function adds two numbers.
        """
        
        code = extract_code_from_message(message)
        
        self.assertIn("def add(a, b):", code)
        self.assertIn("return a + b", code)

if __name__ == "__main__":
    unittest.main()