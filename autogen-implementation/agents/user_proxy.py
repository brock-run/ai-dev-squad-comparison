"""
User Proxy Agent for AutoGen Implementation

This agent represents the human user in the conversation and manages
the interaction between humans and AI agents.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def create_user_proxy(config: Optional[Dict[str, Any]] = None):
    """
    Create a user proxy agent for human interaction.
    
    Args:
        config: Configuration dictionary for the agent
        
    Returns:
        User proxy agent instance
    """
    try:
        # Try to import AutoGen
        try:
            import autogen
            from autogen import UserProxyAgent
            
            # Create AutoGen UserProxyAgent
            user_proxy = UserProxyAgent(
                name="UserProxy",
                system_message="You are a helpful assistant representing the human user. "
                              "You coordinate with other agents to complete development tasks. "
                              "You can execute code and provide feedback on the work done by other agents.",
                human_input_mode="NEVER",  # Automated for testing
                max_consecutive_auto_reply=10,
                is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                code_execution_config={
                    "work_dir": "./autogen_workspace",
                    "use_docker": False,
                    "timeout": 60,
                    "last_n_messages": 3
                }
            )
            
            logger.info("Created AutoGen UserProxyAgent")
            return user_proxy
            
        except ImportError:
            # Fallback to mock agent
            logger.warning("AutoGen not available, creating mock user proxy agent")
            return MockUserProxyAgent(config or {})
            
    except Exception as e:
        logger.error(f"Failed to create user proxy agent: {e}")
        return MockUserProxyAgent(config or {})

class MockUserProxyAgent:
    """Mock user proxy agent when AutoGen is not available."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock user proxy agent."""
        self.config = config
        self.name = "UserProxy"
        self.system_message = "Mock user proxy agent for testing"
        self.human_input_mode = "NEVER"
        self.max_consecutive_auto_reply = 10
        
        logger.info("Initialized mock user proxy agent")
    
    async def generate_reply(self, messages: List[Dict[str, Any]], sender=None, **kwargs) -> Dict[str, Any]:
        """Generate a reply as the user proxy."""
        if not messages:
            return {
                "content": "Hello! I'm ready to help coordinate the development task.",
                "role": "assistant"
            }
        
        last_message = messages[-1] if messages else {}
        content = last_message.get("content", "")
        
        # Mock user proxy responses
        if "design" in content.lower() or "architecture" in content.lower():
            response = "The design looks good. Please proceed with implementation."
        elif "implementation" in content.lower() or "code" in content.lower():
            response = "The implementation looks solid. Please create comprehensive tests."
        elif "test" in content.lower():
            response = "The tests cover the requirements well. The task is complete. TERMINATE"
        else:
            response = "Please continue with the next step in the development process."
        
        return {
            "content": response,
            "role": "assistant"
        }
    
    def initiate_chat(self, recipient, message: str, **kwargs):
        """Initiate a chat with another agent."""
        logger.info(f"Mock initiate_chat with {getattr(recipient, 'name', 'unknown')}: {message}")
        
        # Mock conversation result
        return {
            "success": True,
            "message": message,
            "recipient": getattr(recipient, 'name', 'unknown'),
            "conversation_log": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "Mock conversation completed successfully."}
            ]
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": self.name,
            "type": "user_proxy",
            "features": [
                "human_interaction",
                "code_execution",
                "conversation_coordination",
                "task_management"
            ],
            "interaction_modes": ["automated", "human_in_loop"],
            "execution_capabilities": ["python", "shell", "file_operations"]
        }