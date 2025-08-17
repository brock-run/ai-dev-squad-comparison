"""
Developer Agent for AutoGen Implementation

This agent is responsible for implementing code based on architectural designs.
It writes code, handles implementation details, and follows best practices.
"""

import os
import autogen
from typing import Dict, List, Any

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_DEVELOPER", "codellama:13b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Define the developer's system message
DEVELOPER_SYSTEM_MESSAGE = """
You are an expert software developer with deep knowledge of programming languages, 
algorithms, data structures, and best practices. Your role is to:

1. Implement code based on architectural designs and requirements
2. Write clean, efficient, and maintainable code
3. Follow language-specific best practices and conventions
4. Handle edge cases and error conditions
5. Document your code thoroughly

Always think step-by-step and consider performance, readability, and maintainability.
Explain your implementation decisions and include comments in your code.
"""

def create_developer_agent(config: Dict[str, Any] = None) -> autogen.AssistantAgent:
    """
    Create a developer agent for the AutoGen implementation.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured developer agent
    """
    # Default configuration
    default_config = {
        "name": "Developer",
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
        "system_message": DEVELOPER_SYSTEM_MESSAGE
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

def create_implementation_prompt(task: str, design: str, language: str = "python") -> str:
    """
    Create an implementation prompt for the developer agent.
    
    Args:
        task: The main task description
        design: The architectural design to implement
        language: The programming language to use
        
    Returns:
        Formatted prompt for the developer agent
    """
    return f"""
    Implement code for the following task based on the provided design:
    
    Task: {task}
    
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

def create_refine_code_prompt(code: str, feedback: str, language: str = "python") -> str:
    """
    Create a code refinement prompt for the developer agent.
    
    Args:
        code: The original code
        feedback: Feedback to address
        language: The programming language
        
    Returns:
        Formatted prompt for the developer agent
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

def extract_code_from_message(message: str, language: str = "python") -> str:
    """
    Extract code blocks from a message.
    
    Args:
        message: The message containing code
        language: The programming language
        
    Returns:
        Extracted code
    """
    # Look for code blocks with language-specific markers
    code_blocks = []
    in_code_block = False
    current_block = []
    
    for line in message.split("\n"):
        if line.strip().startswith(f"```{language}") or line.strip() == "```" and not in_code_block:
            in_code_block = True
            continue
        elif line.strip() == "```" and in_code_block:
            in_code_block = False
            code_blocks.append("\n".join(current_block))
            current_block = []
            continue
        
        if in_code_block:
            current_block.append(line)
    
    # If we found code blocks, return them joined together
    if code_blocks:
        return "\n\n".join(code_blocks)
    
    # If no code blocks with markers were found, try to extract code heuristically
    # This is a simplified approach and might not work for all cases
    lines = message.split("\n")
    code_lines = []
    in_code_section = False
    
    for line in lines:
        # Heuristics to identify code sections without markers
        if (line.strip().startswith("def ") or 
            line.strip().startswith("class ") or 
            line.strip().startswith("import ") or 
            line.strip().startswith("from ") or
            "=" in line and not line.strip().startswith("#")):
            in_code_section = True
        
        if in_code_section:
            code_lines.append(line)
    
    if code_lines:
        return "\n".join(code_lines)
    
    # If all else fails, return the entire message
    return message