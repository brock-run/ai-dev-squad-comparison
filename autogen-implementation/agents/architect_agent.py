"""
Architect Agent for AutoGen Implementation

This agent is responsible for system design and architecture decisions.
It analyzes requirements and creates high-level designs.
"""

import os
import autogen
from typing import Dict, List, Any

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_ARCHITECT", "llama3.1:8b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Define the architect's system message
ARCHITECT_SYSTEM_MESSAGE = """
You are an expert software architect with deep knowledge of software design patterns, 
system architecture, and best practices. Your role is to:

1. Analyze requirements and create high-level designs
2. Make architectural decisions based on requirements
3. Define interfaces between components
4. Consider scalability, maintainability, and performance
5. Provide clear design documentation

Always think step-by-step and consider trade-offs in your design decisions.
Explain your reasoning clearly and provide diagrams or pseudocode when helpful.
"""

def create_architect_agent(config: Dict[str, Any] = None) -> autogen.AssistantAgent:
    """
    Create an architect agent for the AutoGen implementation.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured architect agent
    """
    # Default configuration
    default_config = {
        "name": "Architect",
        "llm_config": {
            "config_list": [
                {
                    "model": OLLAMA_MODEL,
                    "api_base": OLLAMA_BASE_URL,
                    "api_type": "ollama",
                    "temperature": TEMPERATURE
                }
            ]
        },
        "system_message": ARCHITECT_SYSTEM_MESSAGE
    }
    
    # Override with provided config
    if config:
        for key, value in config.items():
            if key == "llm_config" and isinstance(value, dict):
                default_config["llm_config"].update(value)
            else:
                default_config[key] = value
    
    # Create the agent
    return autogen.AssistantAgent(**default_config)

def create_design_prompt(task: str, requirements: List[str]) -> str:
    """
    Create a design prompt for the architect agent.
    
    Args:
        task: The main task description
        requirements: List of requirement statements
        
    Returns:
        Formatted prompt for the architect agent
    """
    requirements_text = "\n".join([f"- {req}" for req in requirements])
    
    return f"""
    Create a high-level design for the following task:
    
    Task: {task}
    
    Requirements:
    {requirements_text}
    
    Please provide:
    1. Component breakdown
    2. Interface definitions
    3. Data flow
    4. Key design patterns to use
    5. Potential challenges and solutions
    
    Think step-by-step and consider trade-offs in your design decisions.
    Explain your reasoning clearly and provide diagrams or pseudocode when helpful.
    """

def analyze_requirements_prompt(requirements: List[str]) -> str:
    """
    Create a requirements analysis prompt for the architect agent.
    
    Args:
        requirements: List of requirement statements
        
    Returns:
        Formatted prompt for the architect agent
    """
    requirements_text = "\n".join([f"- {req}" for req in requirements])
    
    return f"""
    Analyze the following requirements and extract key architectural considerations:
    
    Requirements:
    {requirements_text}
    
    Please identify:
    1. Key functional requirements
    2. Non-functional requirements (performance, scalability, etc.)
    3. Technical constraints
    4. Potential architectural approaches
    5. Trade-offs to consider
    
    Think step-by-step and be thorough in your analysis.
    """