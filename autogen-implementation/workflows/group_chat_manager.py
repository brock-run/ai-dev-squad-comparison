"""
Group Chat Manager for AutoGen Implementation

This module defines the group chat workflow for the AI development squad.
It orchestrates the architect, developer, tester, and user proxy agents to complete software development tasks.
"""

import os
import logging
from typing import List, Dict, Any, Optional

# Try to import AutoGen with fallback
try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    try:
        import pyautogen as autogen
        AUTOGEN_AVAILABLE = True
    except ImportError:
        AUTOGEN_AVAILABLE = False
        logging.warning("AutoGen not available")

logger = logging.getLogger(__name__)

class MockGroupChat:
    """Mock group chat when AutoGen is not available."""
    
    def __init__(self, agents: List[Any], config: Dict[str, Any]):
        """Initialize mock group chat."""
        self.agents = agents
        self.config = config
        self.messages = []
        self.max_round = config.get('max_round', 15)
        
        logger.info(f"Initialized mock group chat with {len(agents)} agents")
    
    def start_conversation(self, initial_message: str) -> Dict[str, Any]:
        """Start a mock conversation."""
        logger.info(f"Starting mock conversation: {initial_message}")
        
        # Mock conversation flow
        conversation_log = [
            {"agent": "UserProxy", "message": initial_message},
            {"agent": "Architect", "message": "I'll design the system architecture based on your requirements."},
            {"agent": "Developer", "message": "I'll implement the code according to the architecture."},
            {"agent": "Tester", "message": "I'll create comprehensive tests for the implementation."},
            {"agent": "UserProxy", "message": "The development task has been completed successfully."}
        ]
        
        return {
            "success": True,
            "conversation_log": conversation_log,
            "agents_participated": [agent.name if hasattr(agent, 'name') else str(agent) for agent in self.agents],
            "total_messages": len(conversation_log)
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get group chat capabilities."""
        return {
            "type": "group_chat",
            "features": [
                "multi_agent_conversation",
                "turn_taking",
                "conversation_orchestration",
                "collaborative_development"
            ],
            "agents_count": len(self.agents),
            "max_rounds": self.max_round
        }

# Import agent factories
from agents.architect_agent import create_architect_agent, create_design_prompt
from agents.developer_agent import create_developer_agent, create_implementation_prompt, extract_code_from_message
from agents.tester_agent import create_tester_agent, create_test_cases_prompt, create_evaluation_prompt

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ENABLE_HUMAN_FEEDBACK = os.getenv("ENABLE_HUMAN_FEEDBACK", "true").lower() == "true"
CODE_EXECUTION_ALLOWED = os.getenv("CODE_EXECUTION_ALLOWED", "true").lower() == "true"

def create_user_proxy(config: Dict[str, Any] = None):
    """
    Create a user proxy agent for the AutoGen implementation.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured user proxy agent
    """
    if not AUTOGEN_AVAILABLE:
        logger.warning("AutoGen not available, creating mock user proxy")
        from agents.user_proxy import MockUserProxyAgent
        return MockUserProxyAgent(config or {})
    
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
    try:
        return autogen.UserProxyAgent(**default_config)
    except Exception as e:
        logger.error(f"Failed to create AutoGen UserProxyAgent: {e}")
        from agents.user_proxy import MockUserProxyAgent
        return MockUserProxyAgent(config or {})

def create_groupchat(agents: List[Any], config: Dict[str, Any] = None):
    """
    Create a group chat for the development process.
    
    Args:
        agents: List of agents to include in the group chat
        config: Optional configuration overrides
        
    Returns:
        Configured group chat
    """
    if not AUTOGEN_AVAILABLE:
        logger.warning("AutoGen not available, creating mock group chat")
        return MockGroupChat(agents, config or {})
    
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
    try:
        return autogen.GroupChat(**default_config)
    except Exception as e:
        logger.error(f"Failed to create AutoGen GroupChat: {e}")
        return MockGroupChat(agents, config or {})

def setup_development_agents(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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