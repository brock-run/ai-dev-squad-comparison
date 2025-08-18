"""
Tests for the architect agent module using unittest.

This module contains tests for the architect agent functionality,
including agent creation and prompt generation, using unittest and mocking.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to allow importing from the agents module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the architect_agent module
from agents.architect_agent import (
    create_architect_agent,
    create_design_prompt,
    analyze_requirements_prompt,
    ARCHITECT_SYSTEM_MESSAGE
)

class TestArchitectAgent(unittest.TestCase):
    """Tests for the architect agent functionality."""
    
    @patch('agents.architect_agent.autogen.AssistantAgent')
    def test_create_architect_agent_default_config(self, mock_assistant_agent):
        """Test creating an architect agent with default configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_assistant_agent.return_value = mock_instance
        
        # Call the function under test
        agent = create_architect_agent()
        
        # Check that AssistantAgent was called with the correct arguments
        mock_assistant_agent.assert_called_once()
        args, kwargs = mock_assistant_agent.call_args
        
        self.assertEqual(kwargs['name'], "Architect")
        self.assertEqual(kwargs['system_message'], ARCHITECT_SYSTEM_MESSAGE)
        self.assertIn('llm_config', kwargs)
        self.assertIn('config_list', kwargs['llm_config'])
    
    @patch('agents.architect_agent.autogen.AssistantAgent')
    def test_create_architect_agent_custom_config(self, mock_assistant_agent):
        """Test creating an architect agent with custom configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_assistant_agent.return_value = mock_instance
        
        custom_config = {
            "name": "CustomArchitect",
            "llm_config": {
                "temperature": 0.5
            }
        }
        
        # Call the function under test
        agent = create_architect_agent(custom_config)
        
        # Check that AssistantAgent was called with the correct arguments
        mock_assistant_agent.assert_called_once()
        args, kwargs = mock_assistant_agent.call_args
        
        self.assertEqual(kwargs['name'], "CustomArchitect")
        self.assertEqual(kwargs['system_message'], ARCHITECT_SYSTEM_MESSAGE)
        self.assertEqual(kwargs['llm_config']['temperature'], 0.5)
    
    def test_create_design_prompt(self):
        """Test creating a design prompt."""
        task = "Build a calculator app"
        requirements = [
            "Must support basic arithmetic operations",
            "Should have a user-friendly interface"
        ]
        
        prompt = create_design_prompt(task, requirements)
        
        self.assertIn(task, prompt)
        self.assertIn("Must support basic arithmetic operations", prompt)
        self.assertIn("Should have a user-friendly interface", prompt)
        self.assertIn("Component breakdown", prompt)
        self.assertIn("Interface definitions", prompt)
    
    def test_analyze_requirements_prompt(self):
        """Test creating a requirements analysis prompt."""
        requirements = [
            "Must support basic arithmetic operations",
            "Should have a user-friendly interface"
        ]
        
        prompt = analyze_requirements_prompt(requirements)
        
        self.assertIn("Must support basic arithmetic operations", prompt)
        self.assertIn("Should have a user-friendly interface", prompt)
        self.assertIn("Key functional requirements", prompt)
        self.assertIn("Non-functional requirements", prompt)

if __name__ == "__main__":
    unittest.main()