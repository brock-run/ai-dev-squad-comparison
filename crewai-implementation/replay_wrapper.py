"""
CrewAI Replay Wrapper

This module wraps the CrewAI adapter with record-replay capabilities,
following the adjustment plan for Week 1, Day 4.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, AsyncIterator
from pathlib import Path

from benchmark.replay.player import (
    Player, set_global_player, intercept_llm_call, intercept_tool_call,
    intercept_sandbox_exec, intercept_vcs_operation
)
from benchmark.replay.recorder import Recorder
from common.agent_api import AgentAdapter, RunResult, Event, TaskSchema, EventStream

# Import the original adapter
from adapter import CrewAIAdapter

logger = logging.getLogger(__name__)


class ReplayCrewAIAdapter(AgentAdapter):
    """
    CrewAI adapter with record-replay capabilities.
    
    This wrapper adds deterministic replay functionality to the CrewAI adapter
    by intercepting LLM calls, tool executions, sandbox operations, and VCS operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, replay_mode: str = "normal"):
        """
        Initialize the replay wrapper.
        
        Args:
            config: Configuration dictionary
            replay_mode: "normal", "record", or "replay"
        """
        self.replay_mode = replay_mode
        self.original_adapter = CrewAIAdapter(config)
        
        # Copy adapter properties
        self.name = f"{self.original_adapter.name} (Replay)"
        self.version = self.original_adapter.version
        self.description = f"{self.original_adapter.description} with replay capabilities"
        
        # Initialize replay components
        self.recorder: Optional[Recorder] = None
        self.player: Optional[Player] = None
        
        if replay_mode == "record":
            self.recorder = Recorder()
        elif replay_mode == "replay":
            self.player = Player()
            set_global_player(self.player)
        
        # Wrap the original adapter's methods with interception
        self._wrap_adapter_methods()
        
        logger.info(f"Initialized {self.name} in {replay_mode} mode")
    
    def _wrap_adapter_methods(self):
        """Wrap the original adapter's methods with replay interception."""
        if self.replay_mode in ["record", "replay"]:
            # Wrap CrewAI-specific methods
            self._wrap_crew_execution()
            self._wrap_agent_execution()
            self._wrap_tool_calls()
            self._wrap_sandbox_execution()
            self._wrap_vcs_operations()
    
    def _wrap_crew_execution(self):
        """Wrap crew execution methods with interception."""
        # Wrap the main crew execution method
        if hasattr(self.original_adapter, '_execute_crew'):
            original_execute_crew = self.original_adapter._execute_crew
            self.original_adapter._execute_crew = intercept_llm_call(
                adapter_name="crewai", agent_id="crew_manager"
            )(original_execute_crew)
        
        # Wrap crew kickoff method if available
        if hasattr(self.original_adapter, 'crew') and self.original_adapter.crew:
            if hasattr(self.original_adapter.crew, 'kickoff'):
                original_kickoff = self.original_adapter.crew.kickoff
                self.original_adapter.crew.kickoff = intercept_llm_call(
                    adapter_name="crewai", agent_id="crew"
                )(original_kickoff)
    
    def _wrap_agent_execution(self):
        """Wrap individual agent execution methods."""
        # Wrap agent execution methods
        if hasattr(self.original_adapter, 'agents'):
            for i, agent in enumerate(self.original_adapter.agents):
                if hasattr(agent, 'execute_task'):
                    original_execute = agent.execute_task
                    agent.execute_task = intercept_llm_call(
                        adapter_name="crewai", agent_id=f"agent_{i}_{agent.role if hasattr(agent, 'role') else 'unknown'}"
                    )(original_execute)
                
                # Wrap agent's LLM calls if accessible
                if hasattr(agent, 'llm') and hasattr(agent.llm, 'call'):
                    original_llm_call = agent.llm.call
                    agent.llm.call = intercept_llm_call(
                        adapter_name="crewai", agent_id=f"agent_{i}_llm"
                    )(original_llm_call)
    
    def _wrap_tool_calls(self):
        """Wrap tool calls with interception decorators."""
        # Wrap SafeCodeExecutorTool
        if hasattr(self.original_adapter, 'code_executor_tool'):
            tool = self.original_adapter.code_executor_tool
            if hasattr(tool, '_run'):
                original_run = tool._run
                tool._run = intercept_tool_call(
                    adapter_name="crewai", agent_id="code_executor", tool_name="safe_code_executor"
                )(original_run)
        
        # Wrap SafeFileOperationsTool
        if hasattr(self.original_adapter, 'file_operations_tool'):
            tool = self.original_adapter.file_operations_tool
            if hasattr(tool, '_run'):
                original_run = tool._run
                tool._run = intercept_tool_call(
                    adapter_name="crewai", agent_id="file_operations", tool_name="safe_file_operations"
                )(original_run)
        
        # Wrap SafeVCSOperationsTool
        if hasattr(self.original_adapter, 'vcs_operations_tool'):
            tool = self.original_adapter.vcs_operations_tool
            if hasattr(tool, '_run'):
                original_run = tool._run
                tool._run = intercept_tool_call(
                    adapter_name="crewai", agent_id="vcs_operations", tool_name="safe_vcs_operations"
                )(original_run)
    
    def _wrap_sandbox_execution(self):
        """Wrap sandbox execution with interception decorators."""
        if hasattr(self.original_adapter, 'sandbox') and self.original_adapter.sandbox:
            if hasattr(self.original_adapter.sandbox, 'execute_code'):
                original_execute_code = self.original_adapter.sandbox.execute_code
                self.original_adapter.sandbox.execute_code = intercept_sandbox_exec(
                    adapter_name="crewai", agent_id="sandbox"
                )(original_execute_code)
    
    def _wrap_vcs_operations(self):
        """Wrap VCS operations with interception decorators."""
        # Wrap GitHub operations
        if hasattr(self.original_adapter, 'github') and self.original_adapter.github:
            if hasattr(self.original_adapter.github, 'create_branch'):
                original_create_branch = self.original_adapter.github.create_branch
                self.original_adapter.github.create_branch = intercept_vcs_operation(
                    adapter_name="crewai", agent_id="github", operation="create_branch"
                )(original_create_branch)
            
            if hasattr(self.original_adapter.github, 'create_pull_request'):
                original_create_pr = self.original_adapter.github.create_pull_request
                self.original_adapter.github.create_pull_request = intercept_vcs_operation(
                    adapter_name="crewai", agent_id="github", operation="create_pull_request"
                )(original_create_pr)
        
        # Wrap GitLab operations
        if hasattr(self.original_adapter, 'gitlab') and self.original_adapter.gitlab:
            if hasattr(self.original_adapter.gitlab, 'create_branch'):
                original_create_branch = self.original_adapter.gitlab.create_branch
                self.original_adapter.gitlab.create_branch = intercept_vcs_operation(
                    adapter_name="crewai", agent_id="gitlab", operation="create_branch"
                )(original_create_branch)
            
            if hasattr(self.original_adapter.gitlab, 'create_merge_request'):
                original_create_mr = self.original_adapter.gitlab.create_merge_request
                self.original_adapter.gitlab.create_merge_request = intercept_vcs_operation(
                    adapter_name="crewai", agent_id="gitlab", operation="create_merge_request"
                )(original_create_mr)
    
    # Delegate all AgentAdapter methods to the original adapter
    
    async def run_task(self, task: TaskSchema) -> RunResult:
        """Run a task with replay capabilities."""
        if self.replay_mode == "record" and self.recorder:
            # Start recording for this task
            run_id = f"crewai_{task.id}_{int(datetime.now().timestamp())}"
            self.recorder.start_recording(run_id, task_id=task.id, adapter="crewai")
        
        if self.replay_mode == "replay" and self.player:
            # Load recording if specified in task
            if hasattr(task, 'replay_run_id') and task.replay_run_id:
                success = self.player.load_recording(task.replay_run_id)
                if not success:
                    logger.error(f"Failed to load recording: {task.replay_run_id}")
                    raise ValueError(f"Recording not found: {task.replay_run_id}")
                
                # Start replay mode
                replay_run_id = self.player.start_replay()
                logger.info(f"Started replay with run ID: {replay_run_id}")
        
        # Execute the task using the original adapter
        result = await self.original_adapter.run_task(task)
        
        if self.replay_mode == "record" and self.recorder:
            # Stop recording
            self.recorder.stop_recording()
        
        return result
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get adapter capabilities including replay features."""
        capabilities = self.original_adapter.get_capabilities()
        capabilities["replay"] = {
            "mode": self.replay_mode,
            "supports_recording": True,
            "supports_playback": True,
            "deterministic": True,
            "crew_specific": True
        }
        return capabilities
    
    def validate_task(self, task: TaskSchema) -> bool:
        """Validate task with replay considerations."""
        return self.original_adapter.validate_task(task)
    
    async def stream_events(self, task: TaskSchema) -> AsyncIterator[Event]:
        """Stream events with replay metadata."""
        async for event in self.original_adapter.stream_events(task):
            # Add replay metadata to events
            if self.replay_mode != "normal":
                event.metadata = event.metadata or {}
                event.metadata["replay_mode"] = self.replay_mode
                event.metadata["adapter"] = "crewai"
                if self.replay_mode == "record" and self.recorder:
                    event.metadata["recording_run_id"] = self.recorder._current_run_id
                elif self.replay_mode == "replay" and self.player:
                    event.metadata["replay_run_id"] = self.player._current_run_id
            yield event
    
    def cleanup(self) -> None:
        """Cleanup resources including replay components."""
        if self.recorder:
            self.recorder.stop_recording()
        if self.player:
            set_global_player(None)
        self.original_adapter.cleanup()


def create_replay_adapter(config: Optional[Dict[str, Any]] = None, 
                         replay_mode: str = "normal") -> ReplayCrewAIAdapter:
    """
    Factory function to create a CrewAI adapter with replay capabilities.
    
    Args:
        config: Configuration dictionary
        replay_mode: "normal", "record", or "replay"
    
    Returns:
        ReplayCrewAIAdapter instance
    """
    return ReplayCrewAIAdapter(config, replay_mode)