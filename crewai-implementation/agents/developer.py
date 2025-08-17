"""
Developer Agent for CrewAI Implementation

This agent is responsible for implementing code based on architectural designs.
It writes code, handles implementation details, and follows best practices.
"""

import os
from typing import List
from crewai import Agent
from langchain.tools import BaseTool

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_DEVELOPER", "codellama:13b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

class DeveloperAgent:
    """Factory class for creating the developer agent."""
    
    @staticmethod
    def create(tools: List[BaseTool] = None) -> Agent:
        """
        Create a developer agent with the specified tools.
        
        Args:
            tools: Optional list of tools for the agent to use
            
        Returns:
            Configured developer agent
        """
        return Agent(
            role="Software Developer",
            goal="Implement high-quality code based on architectural designs and requirements",
            backstory="""
            You are an expert software developer with deep knowledge of programming languages, 
            algorithms, data structures, and best practices. You have years of experience writing 
            clean, efficient, and maintainable code. You excel at translating architectural designs 
            into working implementations, handling edge cases, and ensuring code quality.
            """,
            verbose=True,
            llm=OLLAMA_MODEL,
            tools=tools or [],
            allow_delegation=False
        )

    @staticmethod
    def create_implementation_task(agent: Agent, task_description: str, design: str, language: str = "python") -> str:
        """
        Create an implementation task for the developer agent.
        
        Args:
            agent: The developer agent
            task_description: Description of the development task
            design: The architectural design to implement
            language: The programming language to use
            
        Returns:
            Task description for the agent
        """
        return f"""
        Implement code for the following task based on the provided design:
        
        Task: {task_description}
        
        Design:
        {design}
        
        Please implement this in {language}. Your implementation should include:
        1. Complete implementation with all necessary functions and classes
        2. Proper error handling
        3. Comments and documentation
        4. Any necessary imports
        
        Think step-by-step and consider performance, readability, and maintainability.
        Explain your implementation decisions and include comments in your code.
        """
    
    @staticmethod
    def create_refine_task(agent: Agent, code: str, feedback: str, language: str = "python") -> str:
        """
        Create a code refinement task for the developer agent.
        
        Args:
            agent: The developer agent
            code: The original code
            feedback: Feedback to address
            language: The programming language
            
        Returns:
            Task description for the agent
        """
        return f"""
        Refine the following {language} code based on the feedback:
        
        Original Code:
        ```{language}
        {code}
        ```
        
        Feedback:
        {feedback}
        
        Please provide the improved code with all necessary changes.
        Explain your changes and reasoning.
        """