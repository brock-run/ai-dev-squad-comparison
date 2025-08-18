"""
Tests for the developer agent module.

This module contains tests for the developer agent functionality,
including agent creation, prompt generation, and code extraction.
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

# Now import the developer_agent module
from agents.developer import DeveloperAgent, DEVELOPER_SYSTEM_PROMPT


class TestDeveloperAgent:
    """Tests for the developer agent functionality."""
    
    def test_init(self):
        """Test initializing a developer agent."""
        agent = DeveloperAgent()
        
        assert agent.model is not None
        assert isinstance(agent.model, ChatOllama)
        assert agent.model.model == "codellama:13b"
        assert agent.model.base_url == "http://localhost:11434"
        assert agent.model.temperature == 0.7
        assert agent.system_prompt == DEVELOPER_SYSTEM_PROMPT
    
    def test_implement_code(self):
        """Test implementing code."""
        agent = DeveloperAgent()
        task = "Build a Python function to calculate Fibonacci numbers"
        design = {
            "components": ["- Fibonacci function", "- Error handling"],
            "interfaces": ["- Function signature: fibonacci(n)"],
            "data_flow": ["- Input validation -> calculation -> result"],
            "design_patterns": ["- Iterative approach for performance"],
            "challenges": ["- Handling negative numbers"]
        }
        
        result = agent.implement_code(task, design)
        
        assert "raw_response" in result
        assert "code" in result
        assert "fibonacci" in result["code"]
        assert "def" in result["code"]
        assert "return" in result["code"]
    
    def test_refine_code(self):
        """Test refining code."""
        agent = DeveloperAgent()
        code = """
        def fibonacci(n):
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b
        """
        feedback = "Add error handling for negative numbers and add type hints."
        
        result = agent.refine_code(code, feedback)
        
        assert "raw_response" in result
        assert "refined_code" in result
        assert "fibonacci" in result["refined_code"]
        assert "def" in result["refined_code"]
        assert "return" in result["refined_code"]
        assert "ValueError" in result["refined_code"] or "if n < 0" in result["refined_code"]
    
    def test_extract_code_with_markers(self):
        """Test extracting code from text with code block markers."""
        agent = DeveloperAgent()
        text = """
        Here's the implementation:
        
        ```python
        def fibonacci(n):
            if n < 0:
                raise ValueError("Input must be a non-negative integer")
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b
        ```
        
        This function calculates the nth Fibonacci number efficiently.
        """
        
        code = agent._extract_code(text, "python")
        
        assert "def fibonacci(n):" in code
        assert "if n < 0:" in code
        assert "raise ValueError" in code
        assert "return b" in code
        assert "```" not in code
    
    def test_extract_code_without_markers(self):
        """Test extracting code from text without code block markers."""
        agent = DeveloperAgent()
        text = """
        Here's the implementation:
        
        def fibonacci(n):
            if n < 0:
                raise ValueError("Input must be a non-negative integer")
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b
        
        This function calculates the nth Fibonacci number efficiently.
        """
        
        code = agent._extract_code(text, "python")
        
        assert "def fibonacci(n):" in code
        assert "if n < 0:" in code
        assert "raise ValueError" in code
        assert "return b" in code