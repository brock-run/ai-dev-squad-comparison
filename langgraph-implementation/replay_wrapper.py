"""
LangGraph Replay Wrapper

This module wraps the LangGraph adapter with record-replay capabilities,
following the adjustment plan for Week 1, Day 3.
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
from adapter import LangGraphAdapter

logger = logging.getLogger(__name__)


class ReplayLangGraphAdapter(AgentAdapter):
    """
    LangGraph adapter with record-replay capabilities.
    
    This wrapper adds deterministic replay functionality to the LangGraph adapter
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
        self.original_adapter = LangGraphAdapter(config)
        
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
            # Wrap LLM calls in the original adapter
            self._wrap_llm_calls()
            # Wrap tool calls
            self._wrap_tool_calls()
            # Wrap sandbox execution
            self._wrap_sandbox_execution()
            # Wrap VCS operations
            self._wrap_vcs_operations()
    
    def _wrap_llm_calls(self):
        """Wrap LLM calls with interception decorators."""
        # Find and wrap LLM-related methods in the original adapter
        if hasattr(self.original_adapter, '_architect_node'):
            original_architect = self.original_adapter._architect_node
            self.original_adapter._architect_node = intercept_llm_call(
                adapter_name="langgraph", agent_id="architect"
            )(original_architect)
        
        if hasattr(self.original_adapter, '_developer_node'):
            original_developer = self.original_adapter._developer_node
            self.original_adapter._developer_node = intercept_llm_call(
                adapter_name="langgraph", agent_id="developer"
            )(original_developer)
        
        if hasattr(self.original_adapter, '_tester_node'):
            original_tester = self.original_adapter._tester_node
            self.original_adapter._tester_node = intercept_llm_call(
                adapter_name="langgraph", agent_id="tester"
            )(original_tester)
        
        if hasattr(self.original_adapter, '_reviewer_node'):
            original_reviewer = self.original_adapter._reviewer_node
            self.original_adapter._reviewer_node = intercept_llm_call(
                adapter_name="langgraph", agent_id="reviewer"
            )(original_reviewer)
    
    def _wrap_tool_calls(self):
        """Wrap tool calls with interception decorators."""
        # Wrap any tool execution methods
        if hasattr(self.original_adapter, 'sandbox') and self.original_adapter.sandbox:
            if hasattr(self.original_adapter.sandbox, 'execute'):
                original_execute = self.original_adapter.sandbox.execute
                self.original_adapter.sandbox.execute = intercept_tool_call(
                    adapter_name="langgraph", agent_id="sandbox", tool_name="execute"
                )(original_execute)
    
    def _wrap_sandbox_execution(self):
        """Wrap sandbox execution with interception decorators."""
        if hasattr(self.original_adapter, 'sandbox') and self.original_adapter.sandbox:
            if hasattr(self.original_adapter.sandbox, 'run_code'):
                original_run_code = self.original_adapter.sandbox.run_code
                self.original_adapter.sandbox.run_code = intercept_sandbox_exec(
                    adapter_name="langgraph", agent_id="sandbox"
                )(original_run_code)
    
    def _wrap_vcs_operations(self):
        """Wrap VCS operations with interception decorators."""
        # Wrap GitHub operations
        if hasattr(self.original_adapter, 'github') and self.original_adapter.github:
            if hasattr(self.original_adapter.github, 'create_branch'):
                original_create_branch = self.original_adapter.github.create_branch
                self.original_adapter.github.create_branch = intercept_vcs_operation(
                    adapter_name="langgraph", agent_id="github", operation="create_branch"
                )(original_create_branch)
            
            if hasattr(self.original_adapter.github, 'create_pull_request'):
                original_create_pr = self.original_adapter.github.create_pull_request
                self.original_adapter.github.create_pull_request = intercept_vcs_operation(
                    adapter_name="langgraph", agent_id="github", operation="create_pull_request"
                )(original_create_pr)
        
        # Wrap GitLab operations
        if hasattr(self.original_adapter, 'gitlab') and self.original_adapter.gitlab:
            if hasattr(self.original_adapter.gitlab, 'create_branch'):
                original_create_branch = self.original_adapter.gitlab.create_branch
                self.original_adapter.gitlab.create_branch = intercept_vcs_operation(
                    adapter_name="langgraph", agent_id="gitlab", operation="create_branch"
                )(original_create_branch)
            
            if hasattr(self.original_adapter.gitlab, 'create_merge_request'):
                original_create_mr = self.original_adapter.gitlab.create_merge_request
                self.original_adapter.gitlab.create_merge_request = intercept_vcs_operation(
                    adapter_name="langgraph", agent_id="gitlab", operation="create_merge_request"
                )(original_create_mr)
    
    # Delegate all AgentAdapter methods to the original adapter
    
    async def run_task(self, task: TaskSchema) -> RunResult:
        """Run a task with replay capabilities."""
        if self.replay_mode == "record" and self.recorder:
            # Start recording for this task
            run_id = f"langgraph_{task.id}_{int(datetime.now().timestamp())}"
            self.recorder.start_recording(run_id, task_id=task.id, adapter="langgraph")
        
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
            "deterministic": True
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
                         replay_mode: str = "normal") -> ReplayLangGraphAdapter:
    """
    Factory function to create a LangGraph adapter with replay capabilities.
    
    Args:
        config: Configuration dictionary
        replay_mode: "normal", "record", or "replay"
    
    Returns:
        ReplayLangGraphAdapter instance
    """
    return ReplayLangGraphAdapter(config, replay_mode)