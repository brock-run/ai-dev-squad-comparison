"""
Tester Agent for Langroid Implementation

This module provides a specialized tester agent that handles test creation
and execution through natural conversation.
"""

import logging
from typing import Dict, List, Any, Optional

try:
    import langroid as lr
    from langroid import ChatAgent, ChatDocument
    from langroid.agent.chat_agent import ChatAgentConfig
    LANGROID_AVAILABLE = True
except ImportError:
    LANGROID_AVAILABLE = False

logger = logging.getLogger(__name__)


class TesterAgent:
    """
    Tester agent specialized for test creation and execution.
    
    This agent handles:
    - Test case design and creation
    - Test automation and execution
    - Test coverage analysis
    - Quality assurance validation
    """
    
    def __init__(self, llm_config):
        """Initialize the tester agent."""
        self.role = "Tester"
        self.llm_config = llm_config
        
        if LANGROID_AVAILABLE:
            # Create Langroid ChatAgent
            agent_config = ChatAgentConfig(
                name="TesterAgent",
                llm=llm_config,
                system_message=self._get_system_message()
            )
            self.agent = ChatAgent(agent_config)
        else:
            # Mock agent
            self.agent = None
        
        logger.info("Tester agent initialized")
    
    def _get_system_message(self) -> str:
        """Get the system message for the tester agent."""
        return """
You are a skilled software testing agent specializing in test creation and quality assurance.

Your responsibilities:
- Design comprehensive test cases and test suites
- Create unit tests, integration tests, and end-to-end tests
- Analyze test coverage and identify gaps
- Validate that implementations meet requirements
- Test edge cases and error conditions
- Ensure test maintainability and reliability
- Collaborate with other agents through natural conversation

Testing approach:
- Follow test-driven development principles
- Create tests that are clear, maintainable, and reliable
- Cover both positive and negative test cases
- Test boundary conditions and edge cases
- Ensure proper error handling validation
- Focus on requirement validation through tests

Communication style:
- Be thorough and systematic in test planning
- Explain test strategies and reasoning
- Ask clarifying questions about expected behavior
- Provide clear test documentation
- Collaborate effectively with developers and reviewers

Always focus on creating comprehensive, reliable tests that ensure code quality and requirement compliance.
"""
    
    async def llm_response_async(self, message: str) -> str:
        """Generate response to a message."""
        if self.agent and LANGROID_AVAILABLE:
            try:
                # Use Langroid agent for response
                response = await self.agent.llm_response_async(message)
                return response
            except Exception as e:
                logger.error(f"Tester agent response failed: {e}")
                return self._fallback_response(message)
        else:
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Fallback response when Langroid is not available."""
        if "test" in message.lower():
            return f"As the Tester Agent, I'll create comprehensive tests for this functionality. Let me design test cases that cover all requirements."
        elif "validate" in message.lower():
            return f"I'll validate the implementation through systematic testing and requirement verification."
        elif "coverage" in message.lower():
            return f"I'll analyze test coverage and ensure all code paths and requirements are properly tested."
        else:
            return f"As the Tester Agent, I'm ready to create and execute tests. {message[:50]}..."
    
    async def create_tests(self, code: str, requirements: List[str]) -> str:
        """Create comprehensive tests for given code and requirements."""
        prompt = f"""
Please create comprehensive tests for the following code based on the requirements:

Code:
{code}

Requirements:
{chr(10).join(f"- {req}" for req in requirements)}

Create tests that include:
1. Unit tests for individual functions/methods
2. Integration tests for component interactions
3. Edge case and boundary condition tests
4. Error handling and exception tests
5. Requirement validation tests
6. Performance tests if applicable
"""
        
        return await self.llm_response_async(prompt)
    
    async def analyze_coverage(self, code: str, tests: str) -> str:
        """Analyze test coverage and identify gaps."""
        prompt = f"""
Please analyze the test coverage for the following code and tests:

Code:
{code}

Tests:
{tests}

Provide analysis of:
1. Current test coverage percentage (estimate)
2. Uncovered code paths or functions
3. Missing test scenarios
4. Suggestions for additional tests
5. Test quality assessment
"""
        
        return await self.llm_response_async(prompt)
    
    async def validate_requirements(self, implementation: str, tests: str, requirements: List[str]) -> str:
        """Validate that tests properly verify requirements."""
        prompt = f"""
Please validate that the tests properly verify all requirements:

Implementation:
{implementation}

Tests:
{tests}

Requirements:
{chr(10).join(f"- {req}" for req in requirements)}

Check:
1. Each requirement has corresponding tests
2. Tests adequately validate requirement fulfillment
3. Missing requirement validations
4. Suggestions for improved requirement testing
"""
        
        return await self.llm_response_async(prompt)
    
    async def design_test_strategy(self, requirements: List[str], architecture: str) -> str:
        """Design comprehensive test strategy."""
        prompt = f"""
Please design a comprehensive test strategy for the following:

Requirements:
{chr(10).join(f"- {req}" for req in requirements)}

Architecture:
{architecture}

Design strategy covering:
1. Test types needed (unit, integration, e2e)
2. Test priorities and phases
3. Test data requirements
4. Test environment considerations
5. Risk-based testing approach
6. Automation strategy
"""
        
        return await self.llm_response_async(prompt)
    
    async def create_edge_case_tests(self, code: str, functionality_description: str) -> str:
        """Create tests specifically for edge cases and error conditions."""
        prompt = f"""
Please create tests specifically for edge cases and error conditions:

Code:
{code}

Functionality Description:
{functionality_description}

Focus on:
1. Boundary value testing
2. Invalid input handling
3. Error condition testing
4. Resource limitation scenarios
5. Concurrent access issues
6. Performance edge cases
"""
        
        return await self.llm_response_async(prompt)
    
    async def test(self, code: str, requirements: List[str] = None) -> str:
        """Main testing method for test generation."""
        if requirements is None:
            requirements = []
        
        return await self.generate_tests(code, requirements)