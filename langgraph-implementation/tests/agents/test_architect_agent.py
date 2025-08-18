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

# Now import the architect_agent module
from agents.architect import ArchitectAgent, ARCHITECT_SYSTEM_PROMPT


class TestArchitectAgent:
    """Tests for the architect agent functionality."""
    
    def test_init(self):
        """Test initializing an architect agent."""
        agent = ArchitectAgent()
        
        assert agent.model is not None
        assert isinstance(agent.model, ChatOllama)
        assert agent.model.model == "llama3.1:8b"
        assert agent.model.base_url == "http://localhost:11434"
        assert agent.model.temperature == 0.7
        assert agent.system_prompt == ARCHITECT_SYSTEM_PROMPT
    
    def test_analyze_requirements(self):
        """Test analyzing requirements."""
        agent = ArchitectAgent()
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        
        result = agent.analyze_requirements(requirements)
        
        assert "raw_response" in result
        assert "considerations" in result
        assert isinstance(result["considerations"], list)
        assert len(result["considerations"]) > 0
    
    def test_create_design(self):
        """Test creating a design."""
        agent = ArchitectAgent()
        task = "Build a Python function to calculate Fibonacci numbers"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        
        result = agent.create_design(task, requirements)
        
        assert "raw_response" in result
        assert "design" in result
        assert isinstance(result["design"], dict)
        assert "components" in result["design"]
        assert "interfaces" in result["design"]
        assert "data_flow" in result["design"]
        assert "design_patterns" in result["design"]
        assert "challenges" in result["design"]
        assert len(result["design"]["components"]) > 0
        assert len(result["design"]["interfaces"]) > 0
        assert len(result["design"]["data_flow"]) > 0
        assert len(result["design"]["design_patterns"]) > 0
        assert len(result["design"]["challenges"]) > 0
    
    def test_extract_considerations(self):
        """Test extracting considerations from text."""
        agent = ArchitectAgent()
        text = """
        Here are some considerations:
        
        - Consideration 1
        - Consideration 2
        * Consideration 3
        1. Consideration 4
        """
        
        considerations = agent._extract_considerations(text)
        
        assert len(considerations) == 4
        assert "- Consideration 1" in considerations
        assert "- Consideration 2" in considerations
        assert "* Consideration 3" in considerations
        assert "1. Consideration 4" in considerations
    
    def test_extract_design_components(self):
        """Test extracting design components from text."""
        agent = ArchitectAgent()
        text = """
        # Design
        
        ## Components
        - Component 1
        - Component 2
        
        ## Interfaces
        - Interface 1
        - Interface 2
        
        ## Data Flow
        - Data flows from Component 1 to Component 2
        
        ## Design Patterns
        - Factory Pattern
        - Observer Pattern
        
        ## Challenges
        - Challenge 1
        - Challenge 2
        """
        
        design = agent._extract_design_components(text)
        
        assert len(design["components"]) == 2
        assert "- Component 1" in design["components"]
        assert "- Component 2" in design["components"]
        
        assert len(design["interfaces"]) == 2
        assert "- Interface 1" in design["interfaces"]
        assert "- Interface 2" in design["interfaces"]
        
        assert len(design["data_flow"]) == 1
        assert "- Data flows from Component 1 to Component 2" in design["data_flow"]
        
        assert len(design["design_patterns"]) == 2
        assert "- Factory Pattern" in design["design_patterns"]
        assert "- Observer Pattern" in design["design_patterns"]
        
        assert len(design["challenges"]) == 2
        assert "- Challenge 1" in design["challenges"]
        assert "- Challenge 2" in design["challenges"]