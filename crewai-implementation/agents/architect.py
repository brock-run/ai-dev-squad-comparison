"""
Architect Agent for CrewAI Implementation

This agent is responsible for system design and architecture decisions.
It analyzes requirements and creates high-level designs.
"""

import os
from typing import List
from crewai import Agent
from langchain.tools import BaseTool

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_ARCHITECT", "llama3.1:8b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

class ArchitectAgent:
    """Factory class for creating the architect agent."""
    
    @staticmethod
    def create(tools: List[BaseTool] = None) -> Agent:
        """
        Create an architect agent with the specified tools.
        
        Args:
            tools: Optional list of tools for the agent to use
            
        Returns:
            Configured architect agent
        """
        return Agent(
            role="Software Architect",
            goal="Create optimal software architecture designs based on requirements",
            backstory="""
            You are an expert software architect with deep knowledge of software design patterns, 
            system architecture, and best practices. You have years of experience designing 
            scalable, maintainable, and efficient software systems. You excel at analyzing 
            requirements and creating high-level designs that balance technical constraints 
            with business needs.
            """,
            verbose=True,
            llm=OLLAMA_MODEL,
            tools=tools or [],
            allow_delegation=False
        )

    @staticmethod
    def create_design_task(agent: Agent, task_description: str, requirements: List[str]) -> str:
        """
        Create a design task for the architect agent.
        
        Args:
            agent: The architect agent
            task_description: Description of the development task
            requirements: List of requirements
            
        Returns:
            Task description for the agent
        """
        requirements_text = "\n".join([f"- {req}" for req in requirements])
        
        return f"""
        Create a high-level design for the following task:
        
        Task: {task_description}
        
        Requirements:
        {requirements_text}
        
        Your design should include:
        1. Component breakdown
        2. Interface definitions
        3. Data flow
        4. Key design patterns to use
        5. Potential challenges and solutions
        
        Think step-by-step and consider trade-offs in your design decisions.
        Explain your reasoning clearly and provide diagrams or pseudocode when helpful.
        """