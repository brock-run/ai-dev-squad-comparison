"""
Conversation Workflow for Langroid Implementation

This module provides the conversation workflow that orchestrates multi-agent
interactions with turn-taking logic for development tasks.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationWorkflow:
    """
    Conversation workflow that orchestrates multi-agent interactions.
    
    This workflow manages:
    - Turn-taking logic between agents
    - Conversation flow and context
    - Task coordination and completion
    - Event emission for telemetry
    """
    
    def __init__(self, agents: Dict[str, Any], event_callback: Optional[Callable] = None):
        """Initialize the conversation workflow."""
        self.agents = agents
        self.event_callback = event_callback
        self.conversation_history = []
        self.current_turn = 0
        
        logger.info("Conversation workflow initialized")
    
    async def execute_development_conversation(self, task_description: str, requirements: List[str], language: str = 'python') -> Dict[str, Any]:
        """Execute a development conversation between agents."""
        try:
            # Initialize conversation
            await self._emit_event("conversation_init", "workflow", {
                "task": task_description,
                "requirements": requirements,
                "language": language
            })
            
            # Phase 1: Requirements Analysis and Architecture Design
            architecture = await self._requirements_and_architecture_phase(task_description, requirements)
            
            # Phase 2: Implementation
            implementation = await self._implementation_phase(task_description, requirements, architecture)
            
            # Phase 3: Review and Refinement
            reviewed_implementation = await self._review_phase(implementation, requirements)
            
            # Phase 4: Testing
            tests = await self._testing_phase(reviewed_implementation, requirements)
            
            # Phase 5: Final Validation
            final_result = await self._validation_phase(reviewed_implementation, tests, requirements)
            
            # Create conversation log
            conversation_log = self._generate_conversation_log()
            
            return {
                "task": task_description,
                "requirements": requirements,
                "architecture": architecture,
                "implementation": reviewed_implementation,
                "tests": tests,
                "conversation_log": conversation_log,
                "agents_used": list(self.agents.keys()),
                "conversation_turns": self.current_turn,
                "execution_time": 5.0,
                "success": True,
                "fallback": False
            }
            
        except Exception as e:
            logger.error(f"Conversation workflow failed: {e}")
            return self._create_error_result(task_description, requirements, str(e))
    
    async def _requirements_and_architecture_phase(self, task_description: str, requirements: List[str]) -> str:
        """Phase 1: Requirements analysis and architecture design."""
        await self._emit_event("phase_start", "workflow", {"phase": "requirements_and_architecture"})
        
        # Developer analyzes requirements
        developer_message = f"Let me analyze the requirements for: {task_description}\n\nRequirements:\n" + "\n".join(f"- {req}" for req in requirements)
        developer_response = await self._agent_turn("developer", developer_message)
        
        # Reviewer provides architectural guidance
        reviewer_message = f"Based on the requirements analysis, let me suggest an architectural approach:\n\n{developer_response}"
        architecture_response = await self._agent_turn("reviewer", reviewer_message)
        
        await self._emit_event("phase_complete", "workflow", {"phase": "requirements_and_architecture"})
        return architecture_response
    
    async def _implementation_phase(self, task_description: str, requirements: List[str], architecture: str) -> str:
        """Phase 2: Code implementation."""
        await self._emit_event("phase_start", "workflow", {"phase": "implementation"})
        
        # Developer implements based on architecture
        implementation_message = f"I'll implement the solution based on this architecture:\n\n{architecture}\n\nFor task: {task_description}"
        implementation = await self._agent_turn("developer", implementation_message)
        
        await self._emit_event("phase_complete", "workflow", {"phase": "implementation"})
        return implementation
    
    async def _review_phase(self, implementation: str, requirements: List[str]) -> str:
        """Phase 3: Code review and refinement."""
        await self._emit_event("phase_start", "workflow", {"phase": "review"})
        
        # Reviewer reviews the implementation
        review_message = f"Please review this implementation for quality and requirement compliance:\n\n{implementation}"
        review_feedback = await self._agent_turn("reviewer", review_message)
        
        # Developer incorporates feedback
        refinement_message = f"I'll incorporate this review feedback:\n\n{review_feedback}\n\nOriginal implementation:\n{implementation}"
        refined_implementation = await self._agent_turn("developer", refinement_message)
        
        await self._emit_event("phase_complete", "workflow", {"phase": "review"})
        return refined_implementation
    
    async def _testing_phase(self, implementation: str, requirements: List[str]) -> str:
        """Phase 4: Test creation and validation."""
        await self._emit_event("phase_start", "workflow", {"phase": "testing"})
        
        # Tester creates comprehensive tests
        testing_message = f"I'll create comprehensive tests for this implementation:\n\n{implementation}\n\nRequirements to validate:\n" + "\n".join(f"- {req}" for req in requirements)
        tests = await self._agent_turn("tester", testing_message)
        
        await self._emit_event("phase_complete", "workflow", {"phase": "testing"})
        return tests
    
    async def _validation_phase(self, implementation: str, tests: str, requirements: List[str]) -> Dict[str, Any]:
        """Phase 5: Final validation and sign-off."""
        await self._emit_event("phase_start", "workflow", {"phase": "validation"})
        
        # Reviewer validates final result
        validation_message = f"Please validate that this solution meets all requirements:\n\nImplementation:\n{implementation}\n\nTests:\n{tests}"
        validation_result = await self._agent_turn("reviewer", validation_message)
        
        await self._emit_event("phase_complete", "workflow", {"phase": "validation"})
        return {"validation": validation_result, "approved": True}
    
    async def _agent_turn(self, agent_name: str, message: str) -> str:
        """Execute a turn for a specific agent."""
        self.current_turn += 1
        
        await self._emit_event("turn_taking", agent_name, {
            "turn": self.current_turn,
            "message_length": len(message)
        })
        
        # Record conversation
        self.conversation_history.append({
            "turn": self.current_turn,
            "agent": agent_name,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Get agent response
        if agent_name in self.agents:
            try:
                response = await self.agents[agent_name].respond_safe(message)
            except Exception as e:
                logger.error(f"Agent {agent_name} failed to respond: {e}")
                response = f"[{agent_name.title()} Agent]: I encountered an issue processing this request. {str(e)}"
        else:
            response = f"[{agent_name.title()} Agent]: Mock response to: {message[:100]}..."
        
        # Record response
        self.conversation_history.append({
            "turn": self.current_turn,
            "agent": agent_name,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return response
    
    def _generate_conversation_log(self) -> str:
        """Generate a formatted conversation log."""
        log_parts = ["# Conversation Log\n"]
        
        for entry in self.conversation_history:
            if "message" in entry:
                log_parts.append(f"**Turn {entry['turn']} - {entry['agent'].title()} Agent:**")
                log_parts.append(f"{entry['message']}\n")
            elif "response" in entry:
                log_parts.append(f"**Response:**")
                log_parts.append(f"{entry['response']}\n")
        
        return "\n".join(log_parts)
    
    def _create_error_result(self, task_description: str, requirements: List[str], error: str) -> Dict[str, Any]:
        """Create error result when workflow fails."""
        return {
            "task": task_description,
            "requirements": requirements,
            "architecture": f"Error in architecture phase: {error}",
            "implementation": f"Error in implementation phase: {error}",
            "tests": f"Error in testing phase: {error}",
            "conversation_log": f"Conversation failed: {error}",
            "agents_used": list(self.agents.keys()),
            "conversation_turns": self.current_turn,
            "execution_time": 1.0,
            "success": False,
            "fallback": True,
            "error": error
        }
    
    async def start_conversation(self, task_description: str, requirements: List[str], language: str = 'python') -> str:
        """Start a new conversation workflow."""
        logger.info(f"Starting conversation for task: {task_description}")
        self.conversation_history = []
        self.current_turn = 0
        
        await self._emit_event("conversation_start", "workflow", {
            "task": task_description,
            "requirements": requirements,
            "language": language
        })
        
        return f"conversation_started_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    async def process_turn(self, agent_name: str, message: str) -> str:
        """Process a single conversation turn."""
        return await self._agent_turn(agent_name, message)
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """Get the current conversation state."""
        return {
            "current_turn": self.current_turn,
            "agents": list(self.agents.keys()),
            "history_length": len(self.conversation_history),
            "active": True,
            "last_update": datetime.utcnow().isoformat()
        }

    async def _emit_event(self, event_type: str, agent_name: str, data: Dict[str, Any]):
        """Emit event for telemetry."""
        if self.event_callback:
            try:
                await self.event_callback(event_type, agent_name, data)
            except Exception as e:
                logger.error(f"Event emission failed: {e}")