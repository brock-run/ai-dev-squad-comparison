"""
Group Chat Manager for AutoGen Implementation

This module defines the group chat workflow for the AI development squad.
It orchestrates the architect, developer, tester, and user proxy agents to complete software development tasks.
"""

import os
import pyautogen as autogen
from typing import List, Dict, Any, Optional

# Import agent factories
from agents.architect_agent import create_architect_agent, create_design_prompt
from agents.developer_agent import create_developer_agent, create_implementation_prompt, extract_code_from_message
from agents.tester_agent import create_tester_agent, create_test_cases_prompt, create_evaluation_prompt

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ENABLE_HUMAN_FEEDBACK = os.getenv("ENABLE_HUMAN_FEEDBACK", "true").lower() == "true"
CODE_EXECUTION_ALLOWED = os.getenv("CODE_EXECUTION_ALLOWED", "true").lower() == "true"

def create_user_proxy(config: Dict[str, Any] = None) -> autogen.UserProxyAgent:
    """
    Create a user proxy agent for the AutoGen implementation.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured user proxy agent
    """
    # Default configuration
    default_config = {
        "name": "User",
        "human_input_mode": "ALWAYS" if ENABLE_HUMAN_FEEDBACK else "NEVER",
        "code_execution_config": {
            "work_dir": "workspace",
            "use_docker": False
        } if CODE_EXECUTION_ALLOWED else None
    }
    
    # Override with provided config
    if config:
        for key, value in config.items():
            if key == "code_execution_config" and isinstance(value, dict) and default_config["code_execution_config"]:
                default_config["code_execution_config"].update(value)
            else:
                default_config[key] = value
    
    # Create the agent
    return autogen.UserProxyAgent(**default_config)

def create_groupchat(agents: List[autogen.Agent], config: Dict[str, Any] = None) -> autogen.GroupChat:
    """
    Create a group chat for the development process.
    
    Args:
        agents: List of agents to include in the group chat
        config: Optional configuration overrides
        
    Returns:
        Configured group chat
    """
    # Default configuration
    default_config = {
        "agents": agents,
        "messages": [],
        "max_round": 15
    }
    
    # Override with provided config
    if config:
        default_config.update(config)
    
    # Create the group chat
    return autogen.GroupChat(**default_config)

def setup_development_agents(config: Optional[Dict[str, Any]] = None) -> Dict[str, autogen.Agent]:
    """
    Set up all agents needed for the development process.
    
    Args:
        config: Optional configuration overrides for agents
        
    Returns:
        Dictionary of configured agents
    """
    architect_config = config.get("architect") if config else None
    developer_config = config.get("developer") if config else None
    tester_config = config.get("tester") if config else None
    user_config = config.get("user") if config else None
    
    architect = create_architect_agent(architect_config)
    developer = create_developer_agent(developer_config)
    tester = create_tester_agent(tester_config)
    user_proxy = create_user_proxy(user_config)
    
    return {
        "architect": architect,
        "developer": developer,
        "tester": tester,
        "user_proxy": user_proxy
    }

def run_development_workflow(task: str, requirements: List[str], language: str = "python") -> Dict[str, Any]:
    """
    Run the development workflow for a given task and requirements.
    
    Args:
        task: Description of the development task
        requirements: List of requirements
        language: Programming language to use
        
    Returns:
        Results of the development process
    """
    # Set up agents
    agents = setup_development_agents()
    architect = agents["architect"]
    developer = agents["developer"]
    tester = agents["tester"]
    user_proxy = agents["user_proxy"]
    
    # Create group chat
    groupchat = create_groupchat([architect, developer, tester, user_proxy])
    manager = autogen.GroupChatManager(groupchat=groupchat)
    
    # Format the requirements for the initial message
    requirements_text = "\n".join([f"- {req}" for req in requirements])
    
    # Start the conversation
    initial_message = f"""
    I need you to build a {language} implementation for the following task:
    
    Task: {task}
    
    Requirements:
    {requirements_text}
    
    Please follow this process:
    1. Architect: Create a high-level design for the implementation
    2. Developer: Implement the code based on the design
    3. Tester: Create test cases and evaluate the implementation
    4. Developer: Refine the implementation based on test results if needed
    
    Let's start with the Architect creating the design.
    """
    
    # Start the conversation
    user_proxy.initiate_chat(manager, message=initial_message)
    
    # Extract results from the conversation
    # In a real implementation, we would parse the conversation to extract specific outputs
    # For this example, we'll just return a simplified result
    
    # Find the last message from the developer (should contain the final code)
    developer_messages = [msg for msg in groupchat.messages if msg.get("sender") == developer.name]
    final_code = extract_code_from_message(developer_messages[-1]["content"], language) if developer_messages else ""
    
    # Find the last message from the tester (should contain the evaluation)
    tester_messages = [msg for msg in groupchat.messages if msg.get("sender") == tester.name]
    evaluation = tester_messages[-1]["content"] if tester_messages else ""
    
    return {
        "task": task,
        "requirements": requirements,
        "code": final_code,
        "evaluation": evaluation,
        "conversation": groupchat.messages
    }

if __name__ == "__main__":
    # Example usage
    task = "Build a Python function to calculate Fibonacci numbers"
    requirements = [
        "Must handle negative numbers",
        "Should be optimized for performance",
        "Should include proper error handling",
        "Should have clear documentation"
    ]
    
    result = run_development_workflow(task, requirements)
    
    print(f"Task: {result['task']}")
    print("\nFinal Code:")
    print(result['code'])
    
    print("\nEvaluation:")
    print(result['evaluation'])