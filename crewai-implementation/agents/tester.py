"""
Tester Agent for CrewAI Implementation

This agent is responsible for testing code implementations.
It creates test cases, validates functionality, and ensures code quality.
"""

import os
from typing import List
from crewai import Agent
from langchain.tools import BaseTool

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_TESTER", "llama3.1:8b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

class TesterAgent:
    """Factory class for creating the tester agent."""
    
    @staticmethod
    def create(tools: List[BaseTool] = None) -> Agent:
        """
        Create a tester agent with the specified tools.
        
        Args:
            tools: Optional list of tools for the agent to use
            
        Returns:
            Configured tester agent
        """
        return Agent(
            role="Software Tester",
            goal="Ensure code quality through comprehensive testing and validation",
            backstory="""
            You are an expert software tester with deep knowledge of testing methodologies, 
            test design, and quality assurance. You have years of experience creating 
            comprehensive test suites, identifying edge cases, and validating software 
            against requirements. You excel at finding bugs and providing constructive 
            feedback to improve code quality.
            """,
            verbose=True,
            llm=OLLAMA_MODEL,
            tools=tools or [],
            allow_delegation=False
        )

    @staticmethod
    def create_test_plan_task(agent: Agent, task_description: str, requirements: List[str]) -> str:
        """
        Create a test plan task for the tester agent.
        
        Args:
            agent: The tester agent
            task_description: Description of the development task
            requirements: List of requirements
            
        Returns:
            Task description for the agent
        """
        requirements_text = "\n".join([f"- {req}" for req in requirements])
        
        return f"""
        Create a comprehensive test plan for the following task:
        
        Task: {task_description}
        
        Requirements:
        {requirements_text}
        
        Your test plan should include:
        1. Test strategy overview
        2. Unit test cases
        3. Integration test cases
        4. Edge cases to test
        5. Performance considerations
        
        Think step-by-step and consider different testing approaches.
        Explain your testing strategy and provide clear test cases with expected outputs.
        """
    
    @staticmethod
    def create_test_cases_task(agent: Agent, code: str, language: str, requirements: List[str]) -> str:
        """
        Create a task for generating test cases for the given code.
        
        Args:
            agent: The tester agent
            code: The code to test
            language: The programming language
            requirements: List of requirements
            
        Returns:
            Task description for the agent
        """
        requirements_text = "\n".join([f"- {req}" for req in requirements])
        
        return f"""
        Create test cases for the following {language} code:
        
        ```{language}
        {code}
        ```
        
        Requirements:
        {requirements_text}
        
        Your test cases should include:
        1. Unit tests that cover all functionality
        2. Tests for edge cases
        3. Tests for error conditions
        4. Any necessary test setup and teardown
        
        Write the tests in {language} using an appropriate testing framework.
        Ensure your tests are comprehensive and verify that the code meets all requirements.
        """
    
    @staticmethod
    def create_evaluation_task(agent: Agent, code: str, test_results: str) -> str:
        """
        Create a code evaluation task based on test results.
        
        Args:
            agent: The tester agent
            code: The code being tested
            test_results: Results of running tests
            
        Returns:
            Task description for the agent
        """
        return f"""
        Evaluate the following code based on test results:
        
        Code:
        ```
        {code}
        ```
        
        Test Results:
        {test_results}
        
        Your evaluation should include:
        1. Overall assessment of code quality
        2. Identified issues or bugs
        3. Suggestions for improvement
        4. Code coverage analysis
        
        Be thorough in your analysis and provide specific, actionable feedback.
        Focus on both functional correctness and code quality aspects.
        """