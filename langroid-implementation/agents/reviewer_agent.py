"""
Reviewer Agent for Langroid Implementation

This module provides a specialized reviewer agent that handles code review
and quality assurance through natural conversation.
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


class ReviewerAgent:
    """
    Reviewer agent specialized for code review and quality assurance.
    
    This agent handles:
    - Code review and quality assessment
    - Best practices enforcement
    - Security and performance analysis
    - Documentation review
    """
    
    def __init__(self, llm_config):
        """Initialize the reviewer agent."""
        self.role = "Reviewer"
        self.llm_config = llm_config
        
        if LANGROID_AVAILABLE:
            # Create Langroid ChatAgent
            agent_config = ChatAgentConfig(
                name="ReviewerAgent",
                llm=llm_config,
                system_message=self._get_system_message()
            )
            self.agent = ChatAgent(agent_config)
        else:
            # Mock agent
            self.agent = None
        
        logger.info("Reviewer agent initialized")
    
    def _get_system_message(self) -> str:
        """Get the system message for the reviewer agent."""
        return """
You are an experienced code reviewer agent specializing in quality assurance and best practices.

Your responsibilities:
- Review code for correctness, efficiency, and maintainability
- Ensure adherence to coding standards and best practices
- Identify potential security vulnerabilities
- Assess performance implications
- Review documentation and comments
- Provide constructive feedback and suggestions
- Collaborate with other agents through natural conversation

Review criteria:
- Code correctness and logic
- Performance and efficiency
- Security considerations
- Maintainability and readability
- Error handling and edge cases
- Documentation quality
- Test coverage adequacy

Communication style:
- Be constructive and helpful in feedback
- Explain the reasoning behind suggestions
- Prioritize issues by severity
- Acknowledge good practices when present
- Ask questions to clarify intent when needed

Always focus on improving code quality while being supportive and educational.
"""
    
    async def llm_response_async(self, message: str) -> str:
        """Generate response to a message."""
        if self.agent and LANGROID_AVAILABLE:
            try:
                # Use Langroid agent for response
                response = await self.agent.llm_response_async(message)
                return response
            except Exception as e:
                logger.error(f"Reviewer agent response failed: {e}")
                return self._fallback_response(message)
        else:
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Fallback response when Langroid is not available."""
        if "review" in message.lower():
            return f"As the Reviewer Agent, I'll conduct a thorough code review. Let me analyze the implementation for quality and best practices."
        elif "feedback" in message.lower():
            return f"I'll provide constructive feedback on the code quality, security, and maintainability aspects."
        elif "improve" in message.lower():
            return f"I'll suggest improvements to enhance code quality and follow best practices."
        else:
            return f"As the Reviewer Agent, I'm ready to review code and provide quality feedback. {message[:50]}..."
    
    async def review_code(self, code: str, context: str = "") -> str:
        """Review code and provide feedback."""
        prompt = f"""
Please review the following code for quality, best practices, and potential issues:

Code:
{code}

Context: {context}

Provide a comprehensive review covering:
1. Code correctness and logic
2. Performance considerations
3. Security implications
4. Maintainability and readability
5. Error handling
6. Suggestions for improvement
"""
        
        return await self.llm_response_async(prompt)
    
    async def assess_architecture(self, architecture_description: str) -> str:
        """Assess architectural design and provide feedback."""
        prompt = f"""
Please review the following architectural design:

Architecture:
{architecture_description}

Assess the design for:
1. Scalability and performance
2. Maintainability
3. Security considerations
4. Best practices adherence
5. Potential risks or issues
6. Suggestions for improvement
"""
        
        return await self.llm_response_async(prompt)
    
    async def validate_requirements(self, implementation: str, requirements: List[str]) -> str:
        """Validate that implementation meets requirements."""
        prompt = f"""
Please validate that the following implementation meets the specified requirements:

Implementation:
{implementation}

Requirements:
{chr(10).join(f"- {req}" for req in requirements)}

Check each requirement and provide:
1. Compliance status for each requirement
2. Any missing functionality
3. Suggestions for better requirement fulfillment
"""
        
        return await self.llm_response_async(prompt)
    
    async def security_review(self, code: str) -> str:
        """Conduct security-focused code review."""
        prompt = f"""
Please conduct a security-focused review of the following code:

Code:
{code}

Focus on:
1. Input validation and sanitization
2. Authentication and authorization
3. Data handling and storage
4. Potential injection vulnerabilities
5. Error handling that might leak information
6. Security best practices compliance
"""
        
        return await self.llm_response_async(prompt)
    
    async def review(self, code: str, requirements: List[str] = None) -> str:
        """Main review method for code analysis."""
        if requirements is None:
            requirements = []
        
        return await self.review_code(code, requirements)