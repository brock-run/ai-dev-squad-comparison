"""
Tests for the tester agent module.

This module contains tests for the tester agent functionality,
including agent creation, prompt generation, and test extraction.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to allow importing from the agents module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import mock classes
from tests.mocks.mock_langchain import ChatOllama, ChatPromptTemplate, SystemMessage, HumanMessage, AIMessage

# Patch the langchain modules with our mocks
sys.modules['langchain.prompts'] = MagicMock()
sys.modules['langchain.prompts'].ChatPromptTemplate = ChatPromptTemplate
sys.modules['langchain.schema'] = MagicMock()
sys.modules['langchain.schema'].SystemMessage = SystemMessage
sys.modules['langchain.schema'].HumanMessage = HumanMessage
sys.modules['langchain_community.chat_models'] = MagicMock()
sys.modules['langchain_community.chat_models'].ChatOllama = ChatOllama

# Now import the tester_agent module
from agents.tester import TesterAgent, TESTER_SYSTEM_PROMPT


class TestTesterAgent:
    """Tests for the tester agent functionality."""
    
    def test_init(self):
        """Test initializing a tester agent."""
        agent = TesterAgent()
        
        assert agent.model is not None
        assert isinstance(agent.model, ChatOllama)
        assert agent.model.model == "llama3.1:8b"
        assert agent.model.base_url == "http://localhost:11434"
        assert agent.model.temperature == 0.7
        assert agent.system_prompt == TESTER_SYSTEM_PROMPT
    
    def test_create_test_plan(self):
        """Test creating a test plan."""
        agent = TesterAgent()
        task = "Build a Python function to calculate Fibonacci numbers"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        
        result = agent.create_test_plan(task, requirements)
        
        assert "raw_response" in result
        assert "test_plan" in result
        assert isinstance(result["test_plan"], dict)
        assert "strategy" in result["test_plan"]
        assert "unit_tests" in result["test_plan"]
        assert "integration_tests" in result["test_plan"]
        assert "edge_cases" in result["test_plan"]
        assert "performance" in result["test_plan"]
    
    def test_create_test_cases(self):
        """Test creating test cases."""
        agent = TesterAgent()
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
        
        result = agent.create_test_cases(code, language, requirements)
        
        assert "raw_response" in result
        assert "test_code" in result
        assert "unittest" in result["test_code"] or "pytest" in result["test_code"]
        assert "test" in result["test_code"]
        assert "fibonacci" in result["test_code"]
    
    def test_evaluate_code(self):
        """Test evaluating code."""
        agent = TesterAgent()
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
        test_results = {
            "passed": 8,
            "failed": 0,
            "total": 8,
            "coverage": "85%"
        }
        
        result = agent.evaluate_code(code, test_results)
        
        assert "raw_response" in result
        assert "evaluation" in result
        assert isinstance(result["evaluation"], dict)
        assert "assessment" in result["evaluation"]
        assert "issues" in result["evaluation"]
        assert "suggestions" in result["evaluation"]
        assert "coverage" in result["evaluation"]
    
    def test_extract_test_plan(self):
        """Test extracting test plan from text."""
        agent = TesterAgent()
        text = """
        # Test Plan
        
        ## Test Strategy
        - Use unit tests for individual functions
        - Use integration tests for the whole module
        
        ## Unit Tests
        - Test with positive numbers
        - Test with zero
        
        ## Integration Tests
        - Test with the full application
        
        ## Edge Cases
        - Test with negative numbers
        - Test with large numbers
        
        ## Performance
        - Benchmark with large inputs
        """
        
        test_plan = agent._extract_test_plan(text)
        
        assert len(test_plan["strategy"]) == 2
        assert "- Use unit tests for individual functions" in test_plan["strategy"]
        assert "- Use integration tests for the whole module" in test_plan["strategy"]
        
        assert len(test_plan["unit_tests"]) == 2
        assert "- Test with positive numbers" in test_plan["unit_tests"]
        assert "- Test with zero" in test_plan["unit_tests"]
        
        assert len(test_plan["integration_tests"]) == 1
        assert "- Test with the full application" in test_plan["integration_tests"]
        
        assert len(test_plan["edge_cases"]) == 2
        assert "- Test with negative numbers" in test_plan["edge_cases"]
        assert "- Test with large numbers" in test_plan["edge_cases"]
        
        assert len(test_plan["performance"]) == 1
        assert "- Benchmark with large inputs" in test_plan["performance"]
    
    def test_extract_code(self):
        """Test extracting code from text."""
        agent = TesterAgent()
        text = """
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
        
        These tests verify the fibonacci function works correctly.
        """
        
        code = agent._extract_code(text, "python")
        
        assert "import unittest" in code
        assert "class TestFibonacci" in code
        assert "test_positive_numbers" in code
        assert "test_negative_numbers" in code
        assert "self.assertEqual" in code
        assert "self.assertRaises" in code
        assert "```" not in code
    
    def test_extract_evaluation(self):
        """Test extracting evaluation from text."""
        agent = TesterAgent()
        text = """
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
        
        evaluation = agent._extract_evaluation(text)
        
        assert len(evaluation["assessment"]) == 1
        assert "The code is well-implemented and passes all tests." in evaluation["assessment"]
        
        assert len(evaluation["issues"]) == 1
        assert "- No issues found" in evaluation["issues"]
        
        assert len(evaluation["suggestions"]) == 2
        assert "- Add type hints" in evaluation["suggestions"]
        assert "- Consider memoization for better performance" in evaluation["suggestions"]
        
        assert len(evaluation["coverage"]) == 1
        assert "The test coverage is 100%." in evaluation["coverage"]