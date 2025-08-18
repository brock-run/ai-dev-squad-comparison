"""
Tests for the development workflow module.

This module contains tests for the development workflow functionality,
including state transitions and agent interactions.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to allow importing from the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import mock classes
from tests.mocks.mock_langchain import ChatOllama, ChatPromptTemplate, SystemMessage, HumanMessage, AIMessage
from tests.mocks.mock_langgraph import StateGraph, END
from tests.mocks.mock_pydantic import BaseModel, TypedDict

# Patch the modules with our mocks
sys.modules['langchain.prompts'] = MagicMock()
sys.modules['langchain.prompts'].ChatPromptTemplate = ChatPromptTemplate
sys.modules['langchain.schema'] = MagicMock()
sys.modules['langchain.schema'].SystemMessage = SystemMessage
sys.modules['langchain.schema'].HumanMessage = HumanMessage
sys.modules['langchain_community.chat_models'] = MagicMock()
sys.modules['langchain_community.chat_models'].ChatOllama = ChatOllama
sys.modules['langgraph.graph'] = MagicMock()
sys.modules['langgraph.graph'].StateGraph = StateGraph
sys.modules['langgraph.graph'].END = END
sys.modules['pydantic'] = MagicMock()
sys.modules['pydantic'].BaseModel = BaseModel

# Now import the modules we want to test
from workflows.development_workflow import (
    DevelopmentState,
    create_design,
    implement_code,
    create_and_run_tests,
    human_review,
    handle_error,
    should_end,
    development_workflow,
    run_development_workflow
)


class TestDevelopmentWorkflow:
    """Tests for the development workflow functionality."""
    
    def test_create_design(self):
        """Test the create_design function."""
        # Create a mock state
        state = {
            "task": "Build a Python function to calculate Fibonacci numbers",
            "requirements": [
                "Must handle negative numbers",
                "Should be optimized for performance",
                "Should include proper error handling",
                "Should have clear documentation"
            ],
            "design": {},
            "code": "",
            "tests": "",
            "test_results": {},
            "feedback": "",
            "status": "design",
            "error": ""
        }
        
        # Call the function
        result = create_design(state)
        
        # Check the result
        assert result["status"] == "implementation"
        assert "design" in result
        assert result["design"] != {}
        assert "components" in result["design"]
        assert "interfaces" in result["design"]
        assert "data_flow" in result["design"]
        assert "design_patterns" in result["design"]
        assert "challenges" in result["design"]
    
    def test_implement_code(self):
        """Test the implement_code function."""
        # Create a mock state
        state = {
            "task": "Build a Python function to calculate Fibonacci numbers",
            "requirements": [
                "Must handle negative numbers",
                "Should be optimized for performance",
                "Should include proper error handling",
                "Should have clear documentation"
            ],
            "design": {
                "components": ["- Fibonacci function", "- Error handling"],
                "interfaces": ["- Function signature: fibonacci(n)"],
                "data_flow": ["- Input validation -> calculation -> result"],
                "design_patterns": ["- Iterative approach for performance"],
                "challenges": ["- Handling negative numbers"]
            },
            "code": "",
            "tests": "",
            "test_results": {},
            "feedback": "",
            "status": "implementation",
            "error": ""
        }
        
        # Call the function
        result = implement_code(state)
        
        # Check the result
        assert result["status"] == "testing"
        assert result["code"] != ""
        assert "fibonacci" in result["code"]
        assert "def" in result["code"]
    
    def test_create_and_run_tests(self):
        """Test the create_and_run_tests function."""
        # Create a mock state
        state = {
            "task": "Build a Python function to calculate Fibonacci numbers",
            "requirements": [
                "Must handle negative numbers",
                "Should be optimized for performance",
                "Should include proper error handling",
                "Should have clear documentation"
            ],
            "design": {
                "components": ["- Fibonacci function", "- Error handling"],
                "interfaces": ["- Function signature: fibonacci(n)"],
                "data_flow": ["- Input validation -> calculation -> result"],
                "design_patterns": ["- Iterative approach for performance"],
                "challenges": ["- Handling negative numbers"]
            },
            "code": """
            def fibonacci(n):
                if n < 0:
                    raise ValueError("Input must be a non-negative integer")
                if n <= 1:
                    return n
                a, b = 0, 1
                for _ in range(2, n + 1):
                    a, b = b, a + b
                return b
            """,
            "tests": "",
            "test_results": {},
            "feedback": "",
            "status": "testing",
            "error": ""
        }
        
        # Call the function
        with patch('workflows.development_workflow.ENABLE_HUMAN_FEEDBACK', False):
            result = create_and_run_tests(state)
        
        # Check the result
        assert result["status"] == "complete"
        assert result["tests"] != ""
        assert "unittest" in result["tests"] or "pytest" in result["tests"]
        assert "test" in result["tests"]
        assert "fibonacci" in result["tests"]
        assert "test_results" in result
        assert result["test_results"] != {}
        assert "passed" in result["test_results"]
        assert "total" in result["test_results"]
        assert "coverage" in result["test_results"]
    
    def test_human_review(self):
        """Test the human_review function."""
        # Create a mock state
        state = {
            "task": "Build a Python function to calculate Fibonacci numbers",
            "requirements": [
                "Must handle negative numbers",
                "Should be optimized for performance",
                "Should include proper error handling",
                "Should have clear documentation"
            ],
            "design": {
                "components": ["- Fibonacci function", "- Error handling"],
                "interfaces": ["- Function signature: fibonacci(n)"],
                "data_flow": ["- Input validation -> calculation -> result"],
                "design_patterns": ["- Iterative approach for performance"],
                "challenges": ["- Handling negative numbers"]
            },
            "code": """
            def fibonacci(n):
                if n < 0:
                    raise ValueError("Input must be a non-negative integer")
                if n <= 1:
                    return n
                a, b = 0, 1
                for _ in range(2, n + 1):
                    a, b = b, a + b
                return b
            """,
            "tests": "...",
            "test_results": {
                "passed": 8,
                "failed": 0,
                "total": 8,
                "coverage": "85%"
            },
            "feedback": "",
            "status": "review",
            "error": ""
        }
        
        # Call the function
        result = human_review(state)
        
        # Check the result
        assert result["status"] == "complete"
        assert result["feedback"] != ""
    
    def test_handle_error(self):
        """Test the handle_error function."""
        # Create a mock state
        state = {
            "task": "Build a Python function to calculate Fibonacci numbers",
            "requirements": [
                "Must handle negative numbers",
                "Should be optimized for performance",
                "Should include proper error handling",
                "Should have clear documentation"
            ],
            "design": {},
            "code": "",
            "tests": "",
            "test_results": {},
            "feedback": "",
            "status": "error",
            "error": "Something went wrong"
        }
        
        # Call the function
        result = handle_error(state)
        
        # Check the result
        assert result["status"] == "error"
        assert result["error"] == "Something went wrong"
    
    def test_should_end_complete(self):
        """Test the should_end function with complete status."""
        # Create a mock state
        state = {
            "status": "complete",
            "error": ""
        }
        
        # Call the function
        result = should_end(state)
        
        # Check the result
        assert result == "end"
    
    def test_should_end_error(self):
        """Test the should_end function with error status."""
        # Create a mock state
        state = {
            "status": "error",
            "error": "Something went wrong"
        }
        
        # Call the function
        result = should_end(state)
        
        # Check the result
        assert result == "end"
    
    def test_should_end_continue(self):
        """Test the should_end function with a status that should continue."""
        # Create a mock state
        state = {
            "status": "design",
            "error": ""
        }
        
        # Call the function
        result = should_end(state)
        
        # Check the result
        assert result == "continue"
    
    def test_development_workflow(self):
        """Test the development_workflow function."""
        # Call the function
        workflow = development_workflow()
        
        # Check the result
        assert workflow is not None
        assert isinstance(workflow, StateGraph)
        assert "design" in workflow.nodes
        assert "implementation" in workflow.nodes
        assert "testing" in workflow.nodes
        assert "review" in workflow.nodes
        assert "error" in workflow.nodes
        assert workflow.entry_point == "design"
    
    def test_run_development_workflow(self):
        """Test the run_development_workflow function."""
        # Define test inputs
        task = "Build a Python function to calculate Fibonacci numbers"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        
        # Call the function
        result = run_development_workflow(task, requirements)
        
        # Check the result
        assert result is not None
        assert result["task"] == task
        assert result["requirements"] == requirements
        assert result["design"] != {}
        assert result["code"] != ""
        assert result["tests"] != ""
        assert result["test_results"] != {}
        assert result["status"] in ["complete", "error"]