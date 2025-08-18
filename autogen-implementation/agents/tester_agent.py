"""
Tester Agent for AutoGen Implementation

This agent is responsible for testing code implementations.
It creates test cases, validates functionality, and ensures code quality.
"""

import os
import pyautogen as autogen
from typing import Dict, List, Any

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_TESTER", "llama3.1:8b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Define the tester's system message
TESTER_SYSTEM_MESSAGE = """
You are an expert software tester with deep knowledge of testing methodologies, 
test design, and quality assurance. Your role is to:

1. Create comprehensive test cases for code implementations
2. Identify edge cases and potential bugs
3. Validate that code meets requirements and specifications
4. Provide detailed feedback on code quality and test results
5. Suggest improvements based on test findings

Always think step-by-step and consider different testing approaches (unit tests, 
integration tests, edge case testing, etc.).
Explain your testing strategy and provide clear test cases with expected outputs.
"""

def create_tester_agent(config: Dict[str, Any] = None) -> autogen.AssistantAgent:
    """
    Create a tester agent for the AutoGen implementation.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured tester agent
    """
    # Default configuration
    default_config = {
        "name": "Tester",
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
        "system_message": TESTER_SYSTEM_MESSAGE
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

def create_test_plan_prompt(task: str, requirements: List[str]) -> str:
    """
    Create a test plan prompt for the tester agent.
    
    Args:
        task: The main task description
        requirements: List of requirement statements
        
    Returns:
        Formatted prompt for the tester agent
    """
    requirements_text = "\n".join([f"- {req}" for req in requirements])
    
    return f"""
    Create a comprehensive test plan for the following task:
    
    Task: {task}
    
    Requirements:
    {requirements_text}
    
    Please provide:
    1. Test strategy overview
    2. Unit test cases
    3. Integration test cases
    4. Edge cases to test
    5. Performance considerations
    
    Think step-by-step and consider different testing approaches.
    Explain your testing strategy and provide clear test cases with expected outputs.
    """

def create_test_cases_prompt(code: str, language: str, requirements: List[str]) -> str:
    """
    Create a prompt for generating test cases for the given code.
    
    Args:
        code: The code to test
        language: The programming language
        requirements: List of requirements
        
    Returns:
        Formatted prompt for the tester agent
    """
    requirements_text = "\n".join([f"- {req}" for req in requirements])
    
    return f"""
    Create test cases for the following {language} code:
    
    ```{language}
    {code}
    ```
    
    Requirements:
    {requirements_text}
    
    Please provide:
    1. Unit tests that cover all functionality
    2. Tests for edge cases
    3. Tests for error conditions
    4. Any necessary test setup and teardown
    
    Write the tests in {language} using an appropriate testing framework.
    Ensure your tests are comprehensive and verify that the code meets all requirements.
    """

def create_evaluation_prompt(code: str, test_results: str) -> str:
    """
    Create a code evaluation prompt based on test results.
    
    Args:
        code: The code being tested
        test_results: Results of running tests
        
    Returns:
        Formatted prompt for the tester agent
    """
    return f"""
    Evaluate the following code based on test results:
    
    Code:
    ```
    {code}
    ```
    
    Test Results:
    {test_results}
    
    Please provide:
    1. Overall assessment of code quality
    2. Identified issues or bugs
    3. Suggestions for improvement
    4. Code coverage analysis
    
    Be thorough in your analysis and provide specific, actionable feedback.
    Focus on both functional correctness and code quality aspects.
    """

def extract_test_cases_from_message(message: str, language: str = "python") -> str:
    """
    Extract test cases from a message.
    
    Args:
        message: The message containing test cases
        language: The programming language
        
    Returns:
        Extracted test cases
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
    
    # If no code blocks with markers were found, return the entire message
    return message