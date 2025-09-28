"""
Developer Agent for Langroid Implementation

This module provides a specialized developer agent that handles code implementation
and development tasks through natural conversation.
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


class DeveloperAgent:
    """
    Developer agent specialized for code implementation tasks.
    
    This agent handles:
    - Code generation and implementation
    - Technical problem solving
    - Code optimization and refactoring
    - Integration with development tools
    """
    
    def __init__(self, llm_config):
        """Initialize the developer agent."""
        self.role = "Developer"
        self.llm_config = llm_config
        
        if LANGROID_AVAILABLE:
            # Create Langroid ChatAgent
            agent_config = ChatAgentConfig(
                name="DeveloperAgent",
                llm=llm_config,
                system_message=self._get_system_message()
            )
            self.agent = ChatAgent(agent_config)
        else:
            # Mock agent
            self.agent = None
        
        logger.info("Developer agent initialized")
    
    def _get_system_message(self) -> str:
        """Get the system message for the developer agent."""
        return """
You are a skilled software developer agent specializing in code implementation and development tasks.

Your responsibilities:
- Analyze requirements and design specifications
- Write clean, efficient, and maintainable code
- Follow best practices and coding standards
- Implement error handling and edge cases
- Optimize code for performance when needed
- Collaborate with other agents through natural conversation

Communication style:
- Be technical but clear in explanations
- Ask clarifying questions when requirements are unclear
- Provide code examples and implementation details
- Explain your reasoning and approach
- Be open to feedback and suggestions from other agents

Always focus on creating high-quality, production-ready code that meets the specified requirements.
"""
    
    async def llm_response_async(self, message: str) -> str:
        """Generate response to a message."""
        if self.agent and LANGROID_AVAILABLE:
            try:
                # Use Langroid agent for response
                response = await self.agent.llm_response_async(message)
                return response
            except Exception as e:
                logger.error(f"Developer agent response failed: {e}")
                return self._fallback_response(message)
        else:
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Fallback response when Langroid is not available."""
        if "implement" in message.lower():
            return f"As the Developer Agent, I'll implement the requested functionality. Here's my approach: {message[:100]}..."
        elif "code" in message.lower():
            return f"I'll write the code for this requirement. Let me analyze the specifications and create a solution."
        elif "optimize" in message.lower():
            return f"I'll optimize the code for better performance and maintainability."
        else:
            return f"As the Developer Agent, I'm ready to help with implementation tasks. {message[:50]}..."
    
    async def implement_feature(self, description: str, requirements: List[str]) -> str:
        """Implement a feature based on description and requirements."""
        prompt = f"""
Please implement a feature with the following description: {description}

Requirements:
{chr(10).join(f"- {req}" for req in requirements)}

Provide a complete implementation with:
1. Main functionality
2. Error handling
3. Documentation
4. Example usage
"""
        
        return await self.llm_response_async(prompt)
    
    async def review_and_improve(self, code: str, feedback: str) -> str:
        """Review code and implement improvements based on feedback."""
        prompt = f"""
Please review and improve the following code based on the feedback:

Code:
{code}

Feedback:
{feedback}

Provide an improved version that addresses the feedback while maintaining functionality.
"""
        
        return await self.llm_response_async(prompt)
    
    async def debug_issue(self, code: str, issue_description: str) -> str:
        """Debug and fix issues in code."""
        prompt = f"""
Please debug and fix the following issue:

Code:
{code}

Issue Description:
{issue_description}

Provide the corrected code with explanations of what was wrong and how it was fixed.
"""
        
        return await self.llm_response_async(prompt)
    
    async def develop(self, task_description: str, requirements: List[str] = None) -> str:
        """Main development method for implementing tasks."""
        if requirements is None:
            requirements = []
        
        return await self.implement_feature(task_description, requirements)