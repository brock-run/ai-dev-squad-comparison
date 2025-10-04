"""
Comprehensive telemetry event schema for AI Dev Squad platform.

This module defines structured event dataclasses for consistent logging
and observability across all agent operations and framework implementations.

Schema version: 1.0 (ADR-008)
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Schema version for compatibility tracking (ADR-008)
SCHEMA_VERSION = "1.0"


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
    
    # Streaming LLM events (Phase 1)
    LLM_CALL_STARTED = "llm.call.started"
    LLM_CALL_CHUNK = "llm.call.chunk"
    LLM_CALL_FINISHED = "llm.call.finished"
    
    # Performance metrics
    PERFORMANCE_METRIC = "performance.metric"
    RESOURCE_USAGE = "resource.usage"
    
    # Framework-specific events
    FRAMEWORK_EVENT = "framework.event"
    
    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    
    # Record-Replay events (ADR-008, Phase 1 Enhanced)
    REPLAY_CHECKPOINT = "replay.checkpoint"
    RECORDING_NOTE = "recording.note"
    REPLAY_ASSERT = "replay.assert"
    REPLAY_MISMATCH = "replay.mismatch"
    REPLAY_FALLBACK = "replay.fallback"
    
    # Manifest and integrity events
    MANIFEST_CREATED = "manifest.created"
    MANIFEST_VALIDATED = "manifest.validated"
    INTEGRITY_CHECK = "integrity.check"
    
    # Run lifecycle events
    RUN_START = "run.start"
    RUN_END = "run.end"


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
    
    # Schema version for compatibility (ADR-008)
    schema_version: str = SCHEMA_VERSION
    
    # Core identification
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: EventType = EventType.SYSTEM_ERROR
    level: LogLevel = LogLevel.INFO
    
    # Context information (ADR-008: correlation fields)
    run_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    step: Optional[int] = None
    framework: Optional[str] = None
    adapter: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    
    # Event details
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "level": self.level.value,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "step": self.step,
            "framework": self.framework,
            "adapter": self.adapter,
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


@dataclass
class ReplayEvent(BaseEvent):
    """Event for record-replay operations (ADR-008, ADR-009)."""
    
    # Replay-specific fields
    replay_mode: Optional[str] = None  # "record" | "replay"
    lookup_key: Optional[str] = None   # Stable key for IO edge matching
    input_fingerprint: Optional[str] = None  # BLAKE3 hash of normalized inputs
    call_index: Optional[int] = None   # Sequential call number within operation
    
    # IO edge data
    io_type: Optional[str] = None      # "llm_call" | "tool_call" | "sandbox_exec" | "vcs_action"
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # Replay validation
    replay_match: Optional[bool] = None
    replay_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "replay_mode": self.replay_mode,
            "lookup_key": self.lookup_key,
            "input_fingerprint": self.input_fingerprint,
            "call_index": self.call_index,
            "io_type": self.io_type,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "replay_match": self.replay_match,
            "replay_error": self.replay_error
        })
        return data


@dataclass
class RunEvent(BaseEvent):
    """Event for run lifecycle tracking."""
    
    run_id: Optional[str] = None
    adapter: Optional[str] = None
    framework_version: Optional[str] = None
    model_ids: Dict[str, str] = field(default_factory=dict)
    seeds: Dict[str, int] = field(default_factory=dict)
    git_sha: Optional[str] = None
    hardware_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "run_id": self.run_id,
            "adapter": self.adapter,
            "framework_version": self.framework_version,
            "model_ids": self.model_ids,
            "seeds": self.seeds,
            "git_sha": self.git_sha,
            "hardware_info": self.hardware_info
        })
        return data


@dataclass
class StreamingLLMEvent(BaseEvent):
    """Event for streaming LLM interactions (Phase 1)."""
    
    # Request information
    model: Optional[str] = None
    prompt: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Streaming information
    chunk_index: Optional[int] = None
    chunk_content: Optional[str] = None
    chunk_type: Optional[str] = None  # 'text', 'function_call', 'tool_call'
    is_final: bool = False
    
    # Response aggregation
    full_response: Optional[str] = None
    total_chunks: Optional[int] = None
    
    # Token information
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    # Timing
    duration_ms: Optional[float] = None
    first_token_ms: Optional[float] = None  # Time to first token
    
    # Replay information
    io_key: Optional[str] = None
    input_fingerprint: Optional[str] = None
    call_index: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "model": self.model,
            "prompt": self.prompt,
            "parameters": self.parameters,
            "chunk_index": self.chunk_index,
            "chunk_content": self.chunk_content,
            "chunk_type": self.chunk_type,
            "is_final": self.is_final,
            "full_response": self.full_response,
            "total_chunks": self.total_chunks,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "first_token_ms": self.first_token_ms,
            "io_key": self.io_key,
            "input_fingerprint": self.input_fingerprint,
            "call_index": self.call_index
        })
        return data


@dataclass
class EnhancedReplayEvent(BaseEvent):
    """Enhanced replay event with integrity and provenance (Phase 1)."""
    
    # Replay operation type
    operation: Optional[str] = None  # 'checkpoint', 'note', 'assert', 'mismatch', 'fallback'
    
    # Checkpoint information
    checkpoint_label: Optional[str] = None
    checkpoint_step: Optional[int] = None
    
    # Assertion information
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    assertion_type: Optional[str] = None  # 'exact', 'semantic', 'fuzzy'
    
    # Mismatch information
    mismatch_type: Optional[str] = None  # 'key_not_found', 'value_mismatch', 'type_mismatch'
    expected_key: Optional[str] = None
    actual_key: Optional[str] = None
    diff_summary: Optional[str] = None
    
    # Fallback information
    fallback_reason: Optional[str] = None
    fallback_action: Optional[str] = None
    
    # Integrity information
    content_hash: Optional[str] = None
    manifest_hash: Optional[str] = None
    integrity_status: Optional[str] = None  # 'valid', 'invalid', 'missing'
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "operation": self.operation,
            "checkpoint_label": self.checkpoint_label,
            "checkpoint_step": self.checkpoint_step,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "assertion_type": self.assertion_type,
            "mismatch_type": self.mismatch_type,
            "expected_key": self.expected_key,
            "actual_key": self.actual_key,
            "diff_summary": self.diff_summary,
            "fallback_reason": self.fallback_reason,
            "fallback_action": self.fallback_action,
            "content_hash": self.content_hash,
            "manifest_hash": self.manifest_hash,
            "integrity_status": self.integrity_status
        })
        return data


@dataclass
class ManifestEvent(BaseEvent):
    """Event for manifest creation and validation (Phase 1)."""
    
    # Manifest information
    manifest_version: Optional[str] = None
    run_id: Optional[str] = None
    
    # Provenance information
    git_sha: Optional[str] = None
    adapter_version: Optional[str] = None
    framework_version: Optional[str] = None
    model_ids: List[str] = field(default_factory=list)
    seeds: List[int] = field(default_factory=list)
    
    # Configuration
    config_digest: Optional[str] = None
    policy_digest: Optional[str] = None
    
    # Integrity hashes
    events_hash: Optional[str] = None
    inputs_hash: Optional[str] = None
    outputs_hash: Optional[str] = None
    
    # Size and compression info
    compressed_size_bytes: Optional[int] = None
    uncompressed_size_bytes: Optional[int] = None
    compression_ratio: Optional[float] = None
    
    # Redaction log
    redaction_applied: bool = False
    redaction_level: Optional[str] = None
    redacted_fields: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "manifest_version": self.manifest_version,
            "run_id": self.run_id,
            "git_sha": self.git_sha,
            "adapter_version": self.adapter_version,
            "framework_version": self.framework_version,
            "model_ids": self.model_ids,
            "seeds": self.seeds,
            "config_digest": self.config_digest,
            "policy_digest": self.policy_digest,
            "events_hash": self.events_hash,
            "inputs_hash": self.inputs_hash,
            "outputs_hash": self.outputs_hash,
            "compressed_size_bytes": self.compressed_size_bytes,
            "uncompressed_size_bytes": self.uncompressed_size_bytes,
            "compression_ratio": self.compression_ratio,
            "redaction_applied": self.redaction_applied,
            "redaction_level": self.redaction_level,
            "redacted_fields": self.redacted_fields
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
        
        EventType.REPLAY_CHECKPOINT: ReplayEvent,
        EventType.RECORDING_NOTE: ReplayEvent,
        EventType.REPLAY_ASSERT: ReplayEvent,
        
        EventType.RUN_START: RunEvent,
        EventType.RUN_END: RunEvent,
    }
    
    event_class = event_mapping.get(event_type, BaseEvent)
    return event_class(event_type=event_type, **kwargs)


# Convenience functions for creating Phase 1 events

def create_streaming_llm_start_event(prompt: str,
                                    model: str,
                                    agent_id: str,
                                    stream_id: str,
                                    session_id: Optional[str] = None,
                                    task_id: Optional[str] = None,
                                    **kwargs) -> StreamingLLMEvent:
    """Create a streaming LLM start event."""
    return StreamingLLMEvent(
        event_type=EventType.LLM_CALL_STARTED,
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        model=model,
        prompt=prompt,
        chunk_index=0,
        metadata={
            "stream_id": stream_id,
            **kwargs
        }
    )


def create_streaming_llm_chunk_event(chunk_content: str,
                                    stream_id: str,
                                    chunk_index: int,
                                    agent_id: str,
                                    session_id: Optional[str] = None,
                                    task_id: Optional[str] = None,
                                    **kwargs) -> StreamingLLMEvent:
    """Create a streaming LLM chunk event."""
    return StreamingLLMEvent(
        event_type=EventType.LLM_CALL_CHUNK,
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        chunk_content=chunk_content,
        chunk_index=chunk_index,
        metadata={
            "stream_id": stream_id,
            "chunk_size": len(chunk_content),
            **kwargs
        }
    )


def create_streaming_llm_finish_event(stream_id: str,
                                     total_chunks: int,
                                     total_tokens: int,
                                     agent_id: str,
                                     session_id: Optional[str] = None,
                                     task_id: Optional[str] = None,
                                     **kwargs) -> StreamingLLMEvent:
    """Create a streaming LLM finish event."""
    return StreamingLLMEvent(
        event_type=EventType.LLM_CALL_FINISHED,
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        total_chunks=total_chunks,
        total_tokens=total_tokens,
        is_final=True,
        metadata={
            "stream_id": stream_id,
            **kwargs
        }
    )


def create_recording_start_event(recording_session: str,
                                artifacts_path: str,
                                agent_id: str,
                                session_id: Optional[str] = None,
                                task_id: Optional[str] = None,
                                **kwargs) -> ManifestEvent:
    """Create a recording start event."""
    return ManifestEvent(
        event_type=EventType.RECORDING_NOTE,
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        run_id=recording_session,
        metadata={
            "artifacts_path": artifacts_path,
            **kwargs
        }
    )


def create_replay_start_event(recording_session: str,
                             replay_mode: str,
                             agent_id: str,
                             session_id: Optional[str] = None,
                             task_id: Optional[str] = None,
                             **kwargs) -> EnhancedReplayEvent:
    """Create a replay start event."""
    return EnhancedReplayEvent(
        event_type=EventType.REPLAY_START,
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        operation="start",
        metadata={
            "recording_session": recording_session,
            "replay_mode": replay_mode,
            **kwargs
        }
    )


def create_replay_mismatch_event(original_event_id: str,
                                mismatch_details: Dict[str, Any],
                                agent_id: str,
                                io_key: str,
                                session_id: Optional[str] = None,
                                task_id: Optional[str] = None) -> EnhancedReplayEvent:
    """Create a replay mismatch event."""
    return EnhancedReplayEvent(
        event_type=EventType.REPLAY_MISMATCH,
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        operation="mismatch",
        mismatch_type=mismatch_details.get("type", "unknown"),
        diff_summary=str(mismatch_details),
        metadata={
            "original_event_id": original_event_id,
            "io_key": io_key,
            "mismatch_details": mismatch_details
        }
    )


# Aliases for backward compatibility
RecordingEvent = ManifestEvent
ReplayEvent = EnhancedReplayEvent