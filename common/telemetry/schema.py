"""
Comprehensive telemetry event schema for AI Dev Squad platform.

This module defines structured event dataclasses for consistent logging
and observability across all agent operations and framework implementations.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class EventType(Enum):
    """Event type enumeration for categorizing telemetry events."""
    
    # Agent lifecycle events
    AGENT_START = "agent.start"
    AGENT_STOP = "agent.stop"
    AGENT_ERROR = "agent.error"
    
    # Task execution events
    TASK_START = "task.start"
    TASK_COMPLETE = "task.complete"
    TASK_FAIL = "task.fail"
    TASK_RETRY = "task.retry"
    
    # Tool usage events
    TOOL_CALL = "tool.call"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"
    
    # Safety and security events
    SAFETY_VIOLATION = "safety.violation"
    SANDBOX_EXECUTION = "sandbox.execution"
    POLICY_CHECK = "policy.check"
    INJECTION_DETECTED = "injection.detected"
    
    # VCS operations
    VCS_COMMIT = "vcs.commit"
    VCS_BRANCH = "vcs.branch"
    VCS_PR_CREATE = "vcs.pr.create"
    VCS_ERROR = "vcs.error"
    
    # Model interactions
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    LLM_ERROR = "llm.error"
    LLM_TOKEN_COUNT = "llm.token_count"
    
    # Performance metrics
    PERFORMANCE_METRIC = "performance.metric"
    RESOURCE_USAGE = "resource.usage"
    
    # Framework-specific events
    FRAMEWORK_EVENT = "framework.event"
    
    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"


class LogLevel(Enum):
    """Log level enumeration matching standard logging levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class BaseEvent:
    """Base event class with common fields for all telemetry events."""
    
    # Core identification
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: EventType = EventType.SYSTEM_ERROR
    level: LogLevel = LogLevel.INFO
    
    # Context information
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    framework: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    
    # Event details
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "level": self.level.value,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "framework": self.framework,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "message": self.message,
            "metadata": self.metadata
        }


@dataclass
class AgentEvent(BaseEvent):
    """Event for agent lifecycle operations."""
    
    agent_type: Optional[str] = None
    agent_config: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "agent_type": self.agent_type,
            "agent_config": self.agent_config,
            "capabilities": self.capabilities
        })
        return data


@dataclass
class TaskEvent(BaseEvent):
    """Event for task execution tracking."""
    
    task_name: Optional[str] = None
    task_description: Optional[str] = None
    task_input: Dict[str, Any] = field(default_factory=dict)
    task_output: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error_details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_name": self.task_name,
            "task_description": self.task_description,
            "task_input": self.task_input,
            "task_output": self.task_output,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_details": self.error_details
        })
        return data


@dataclass
class ToolEvent(BaseEvent):
    """Event for tool usage tracking."""
    
    tool_name: Optional[str] = None
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error_details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_details": self.error_details
        })
        return data


@dataclass
class SafetyEvent(BaseEvent):
    """Event for safety and security operations."""
    
    policy_name: Optional[str] = None
    violation_type: Optional[str] = None
    risk_level: Optional[str] = None
    action_taken: Optional[str] = None
    blocked_content: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "policy_name": self.policy_name,
            "violation_type": self.violation_type,
            "risk_level": self.risk_level,
            "action_taken": self.action_taken,
            "blocked_content": self.blocked_content
        })
        return data


@dataclass
class VCSEvent(BaseEvent):
    """Event for version control operations."""
    
    repository: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    operation: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    pr_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "repository": self.repository,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "operation": self.operation,
            "files_changed": self.files_changed,
            "pr_number": self.pr_number
        })
        return data


@dataclass
class LLMEvent(BaseEvent):
    """Event for LLM interaction tracking."""
    
    model_name: Optional[str] = None
    provider: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    duration_ms: Optional[float] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "model_name": self.model_name,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "duration_ms": self.duration_ms,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        })
        return data


@dataclass
class PerformanceEvent(BaseEvent):
    """Event for performance metrics tracking."""
    
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    metric_unit: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    disk_io_mb: Optional[float] = None
    network_io_mb: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_unit": self.metric_unit,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "disk_io_mb": self.disk_io_mb,
            "network_io_mb": self.network_io_mb
        })
        return data


@dataclass
class FrameworkEvent(BaseEvent):
    """Event for framework-specific operations."""
    
    framework_version: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    state_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "framework_version": self.framework_version,
            "operation": self.operation,
            "component": self.component,
            "state_data": self.state_data
        })
        return data


# Event factory function for creating appropriate event types
def create_event(event_type: EventType, **kwargs) -> BaseEvent:
    """Create an appropriate event instance based on event type."""
    
    event_mapping = {
        EventType.AGENT_START: AgentEvent,
        EventType.AGENT_STOP: AgentEvent,
        EventType.AGENT_ERROR: AgentEvent,
        
        EventType.TASK_START: TaskEvent,
        EventType.TASK_COMPLETE: TaskEvent,
        EventType.TASK_FAIL: TaskEvent,
        EventType.TASK_RETRY: TaskEvent,
        
        EventType.TOOL_CALL: ToolEvent,
        EventType.TOOL_RESULT: ToolEvent,
        EventType.TOOL_ERROR: ToolEvent,
        
        EventType.SAFETY_VIOLATION: SafetyEvent,
        EventType.SANDBOX_EXECUTION: SafetyEvent,
        EventType.POLICY_CHECK: SafetyEvent,
        EventType.INJECTION_DETECTED: SafetyEvent,
        
        EventType.VCS_COMMIT: VCSEvent,
        EventType.VCS_BRANCH: VCSEvent,
        EventType.VCS_PR_CREATE: VCSEvent,
        EventType.VCS_ERROR: VCSEvent,
        
        EventType.LLM_REQUEST: LLMEvent,
        EventType.LLM_RESPONSE: LLMEvent,
        EventType.LLM_ERROR: LLMEvent,
        EventType.LLM_TOKEN_COUNT: LLMEvent,
        
        EventType.PERFORMANCE_METRIC: PerformanceEvent,
        EventType.RESOURCE_USAGE: PerformanceEvent,
        
        EventType.FRAMEWORK_EVENT: FrameworkEvent,
    }
    
    event_class = event_mapping.get(event_type, BaseEvent)
    return event_class(event_type=event_type, **kwargs)