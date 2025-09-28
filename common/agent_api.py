#!/usr/bin/env python3
"""
Common Agent API for AI Dev Squad Comparison

This module defines the standardized interfaces and data structures that all
orchestrator frameworks must implement to ensure fair comparison and consistent
behavior across different agent implementations.
"""

from typing import Protocol, Dict, Any, List, Optional, Iterable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class TaskType(Enum):
    """Enumeration of supported task types."""
    BUGFIX = "bugfix"
    FEATURE_ADD = "feature_add"
    QA = "qa"
    OPTIMIZE = "optimize"
    EDGE_CASE = "edge_case"


class ExecutionMode(Enum):
    """Execution mode for agent tasks."""
    AUTONOMOUS = "autonomous"  # Agent performs VCS actions itself
    ADVISORY = "advisory"     # Agent produces diff/plan; harness applies


class TaskStatus(Enum):
    """Status of task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TaskSchema:
    """Standardized task input schema."""
    id: str
    type: TaskType
    inputs: Dict[str, Any]
    repo_path: str
    vcs_provider: str  # "github" or "gitlab"
    mode: ExecutionMode = ExecutionMode.AUTONOMOUS
    seed: Optional[int] = None
    model_prefs: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 300
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate task schema after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if isinstance(self.type, str):
            self.type = TaskType(self.type)
        
        if isinstance(self.mode, str):
            self.mode = ExecutionMode(self.mode)
        
        # Set default resource limits if not provided
        if not self.resource_limits:
            self.resource_limits = {
                "max_memory_mb": 1024,
                "max_cpu_percent": 80,
                "max_execution_time": 60
            }


@dataclass
class RunResult:
    """Standardized result from task execution."""
    status: TaskStatus
    artifacts: Dict[str, Any]
    timings: Dict[str, float]
    tokens: Dict[str, int]
    costs: Dict[str, float]
    trace_id: str
    metadata: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate and set defaults for run result."""
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
        
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
        
        # Ensure required dictionaries exist
        self.artifacts = self.artifacts or {}
        self.timings = self.timings or {}
        self.tokens = self.tokens or {}
        self.costs = self.costs or {}
        self.metadata = self.metadata or {}
    
    def add_artifact(self, name: str, content: Any) -> None:
        """Add an artifact to the result."""
        self.artifacts[name] = content
    
    def add_timing(self, operation: str, duration: float) -> None:
        """Add a timing measurement."""
        self.timings[operation] = duration
    
    def add_token_usage(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Add token usage information."""
        self.tokens[f"{model}_prompt"] = prompt_tokens
        self.tokens[f"{model}_completion"] = completion_tokens
        self.tokens[f"{model}_total"] = prompt_tokens + completion_tokens
    
    def add_cost(self, model: str, cost: float) -> None:
        """Add cost information."""
        self.costs[model] = cost
    
    def is_successful(self) -> bool:
        """Check if the task execution was successful."""
        return self.status == TaskStatus.COMPLETED


@dataclass
class Event:
    """Structured event for agent operations."""
    timestamp: datetime
    event_type: str
    framework: str
    agent_id: str
    task_id: str
    trace_id: str
    span_id: Optional[str]
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set defaults for event."""
        if not self.span_id:
            self.span_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "framework": self.framework,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "data": self.data,
            "metadata": self.metadata
        }


class AgentAdapter(Protocol):
    """Protocol that all orchestrator adapters must implement."""
    
    name: str
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the adapter with runtime parameters.
        
        Args:
            config: Configuration dictionary containing model settings,
                   credentials, and other runtime parameters.
        """
        ...
    
    def run_task(self, task: TaskSchema, context: Dict[str, Any]) -> RunResult:
        """
        Execute a task and return standardized results.
        
        Args:
            task: Standardized task specification
            context: Additional context for task execution
            
        Returns:
            RunResult with status, artifacts, and metadata
        """
        ...
    
    def events(self) -> Iterable[Event]:
        """
        Stream events during task execution.
        
        Returns:
            Iterator of Event objects representing agent operations
        """
        ...
    
    def validate_configuration(self) -> bool:
        """
        Validate that the adapter is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        ...
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about adapter capabilities and limitations.
        
        Returns:
            Dictionary describing supported features and constraints
        """
        ...


class EventStream:
    """Manager for real-time event emission and collection."""
    
    def __init__(self):
        self.events: List[Event] = []
        self.subscribers: List[callable] = []
    
    def emit(self, event: Event) -> None:
        """Emit an event to all subscribers."""
        self.events.append(event)
        for subscriber in self.subscribers:
            try:
                subscriber(event)
            except Exception as e:
                # Log error but don't fail event emission
                print(f"Error in event subscriber: {e}")
    
    def subscribe(self, callback: callable) -> None:
        """Subscribe to event stream."""
        self.subscribers.append(callback)
    
    def get_events(self, task_id: Optional[str] = None) -> List[Event]:
        """Get events, optionally filtered by task ID."""
        if task_id:
            return [e for e in self.events if e.task_id == task_id]
        return self.events.copy()
    
    def clear(self) -> None:
        """Clear all events."""
        self.events.clear()


class AdapterFactory:
    """Factory for creating and managing agent adapters."""
    
    def __init__(self):
        self._adapters: Dict[str, type] = {}
        self._instances: Dict[str, AgentAdapter] = {}
    
    def register(self, name: str, adapter_class: type) -> None:
        """Register an adapter class."""
        self._adapters[name] = adapter_class
    
    def create(self, name: str, config: Dict[str, Any]) -> AgentAdapter:
        """Create and configure an adapter instance."""
        if name not in self._adapters:
            raise ValueError(f"Unknown adapter: {name}")
        
        if name not in self._instances:
            adapter = self._adapters[name]()
            adapter.configure(config)
            self._instances[name] = adapter
        
        return self._instances[name]
    
    def list_adapters(self) -> List[str]:
        """List all registered adapter names."""
        return list(self._adapters.keys())
    
    def get_adapter_info(self, name: str) -> Dict[str, Any]:
        """Get information about a specific adapter."""
        if name not in self._adapters:
            raise ValueError(f"Unknown adapter: {name}")
        
        adapter = self._adapters[name]()
        return {
            "name": name,
            "class": adapter.__class__.__name__,
            "capabilities": adapter.get_capabilities() if hasattr(adapter, 'get_capabilities') else {}
        }


class TaskValidator:
    """Validator for task schema and inputs."""
    
    @staticmethod
    def validate_task(task: TaskSchema) -> List[str]:
        """
        Validate a task schema and return any validation errors.
        
        Args:
            task: Task to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate required fields
        if not task.id:
            errors.append("Task ID is required")
        
        if not task.inputs:
            errors.append("Task inputs are required")
        
        if not task.repo_path:
            errors.append("Repository path is required")
        
        if task.vcs_provider not in ["github", "gitlab"]:
            errors.append("VCS provider must be 'github' or 'gitlab'")
        
        # Validate timeout
        if task.timeout_seconds <= 0:
            errors.append("Timeout must be positive")
        
        # Validate resource limits
        if task.resource_limits:
            if "max_memory_mb" in task.resource_limits and task.resource_limits["max_memory_mb"] <= 0:
                errors.append("Max memory must be positive")
            
            if "max_cpu_percent" in task.resource_limits:
                cpu_percent = task.resource_limits["max_cpu_percent"]
                if not (0 < cpu_percent <= 100):
                    errors.append("CPU percent must be between 1 and 100")
        
        return errors
    
    @staticmethod
    def validate_inputs_for_task_type(task_type: TaskType, inputs: Dict[str, Any]) -> List[str]:
        """
        Validate inputs specific to task type.
        
        Args:
            task_type: Type of task
            inputs: Task inputs to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if task_type == TaskType.BUGFIX:
            if "issue_description" not in inputs:
                errors.append("Bug fix tasks require 'issue_description'")
            if "failing_test" not in inputs:
                errors.append("Bug fix tasks require 'failing_test'")
        
        elif task_type == TaskType.FEATURE_ADD:
            if "feature_spec" not in inputs:
                errors.append("Feature addition tasks require 'feature_spec'")
            if "code_scaffold" not in inputs:
                errors.append("Feature addition tasks require 'code_scaffold'")
        
        elif task_type == TaskType.QA:
            if "questions" not in inputs:
                errors.append("QA tasks require 'questions'")
            if "context_source" not in inputs:
                errors.append("QA tasks require 'context_source' (codebase or logs)")
        
        elif task_type == TaskType.OPTIMIZE:
            if "target_function" not in inputs:
                errors.append("Optimization tasks require 'target_function'")
            if "performance_test" not in inputs:
                errors.append("Optimization tasks require 'performance_test'")
        
        elif task_type == TaskType.EDGE_CASE:
            if "issue_description" not in inputs:
                errors.append("Edge case tasks require 'issue_description'")
        
        return errors


# Event type constants for consistency
class EventTypes:
    """Standard event types for consistent logging."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    VCS_ACTION = "vcs_action"
    SAFETY_VIOLATION = "safety_violation"
    ERROR = "error"
    METRIC = "metric"


# Global factory instance
adapter_factory = AdapterFactory()


def create_task(
    task_type: TaskType,
    inputs: Dict[str, Any],
    repo_path: str,
    vcs_provider: str = "github",
    mode: ExecutionMode = ExecutionMode.AUTONOMOUS,
    **kwargs
) -> TaskSchema:
    """
    Convenience function to create a validated task.
    
    Args:
        task_type: Type of task to create
        inputs: Task-specific inputs
        repo_path: Path to repository
        vcs_provider: VCS provider (github or gitlab)
        mode: Execution mode (autonomous or advisory)
        **kwargs: Additional task parameters
        
    Returns:
        Validated TaskSchema instance
        
    Raises:
        ValueError: If task validation fails
    """
    task = TaskSchema(
        id=kwargs.get('id', str(uuid.uuid4())),
        type=task_type,
        inputs=inputs,
        repo_path=repo_path,
        vcs_provider=vcs_provider,
        mode=mode,
        seed=kwargs.get('seed'),
        model_prefs=kwargs.get('model_prefs', {}),
        timeout_seconds=kwargs.get('timeout_seconds', 300),
        resource_limits=kwargs.get('resource_limits', {}),
        metadata=kwargs.get('metadata', {})
    )
    
    # Validate the task
    errors = TaskValidator.validate_task(task)
    if errors:
        raise ValueError(f"Task validation failed: {'; '.join(errors)}")
    
    # Validate task-type specific inputs
    input_errors = TaskValidator.validate_inputs_for_task_type(task.type, task.inputs)
    if input_errors:
        raise ValueError(f"Task input validation failed: {'; '.join(input_errors)}")
    
    return task


def create_event(
    event_type: str,
    framework: str,
    agent_id: str,
    task_id: str,
    trace_id: str,
    data: Dict[str, Any],
    **kwargs
) -> Event:
    """
    Convenience function to create a structured event.
    
    Args:
        event_type: Type of event (use EventTypes constants)
        framework: Name of the orchestrator framework
        agent_id: Identifier of the agent
        task_id: Identifier of the task
        trace_id: Distributed tracing ID
        data: Event-specific data
        **kwargs: Additional event parameters
        
    Returns:
        Event instance
    """
    return Event(
        timestamp=kwargs.get('timestamp', datetime.now()),
        event_type=event_type,
        framework=framework,
        agent_id=agent_id,
        task_id=task_id,
        trace_id=trace_id,
        span_id=kwargs.get('span_id'),
        data=data,
        metadata=kwargs.get('metadata', {})
    )


# Example usage and testing functions
if __name__ == "__main__":
    # Example task creation
    task = create_task(
        task_type=TaskType.BUGFIX,
        inputs={
            "issue_description": "Function returns incorrect result for edge case",
            "failing_test": "test_edge_case_handling",
            "code_file": "src/utils.py"
        },
        repo_path="/path/to/repo",
        vcs_provider="github",
        mode=ExecutionMode.AUTONOMOUS,
        seed=42
    )
    
    print(f"Created task: {task.id}")
    print(f"Task type: {task.type.value}")
    print(f"Mode: {task.mode.value}")
    
    # Example event creation
    event = create_event(
        event_type=EventTypes.TASK_START,
        framework="example_framework",
        agent_id="developer_agent",
        task_id=task.id,
        trace_id=str(uuid.uuid4()),
        data={"task_type": task.type.value, "mode": task.mode.value}
    )
    
    print(f"Created event: {event.event_type}")
    print(f"Event data: {event.to_dict()}")