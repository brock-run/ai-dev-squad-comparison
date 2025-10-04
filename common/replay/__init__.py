"""
Record-Replay Foundation Module

Provides the foundational components for deterministic record-replay functionality
including canonical hashing, event ordering, deterministic providers, redaction,
security policy integration, and streaming support.

This module implements Phase 0 and Phase 1 of the Record-Replay integration plan,
establishing the critical foundations for production-ready deterministic testing
with enhanced telemetry integration and streaming capabilities.
"""

# Core components
from .canonicalization import (
    CanonicalHasher,
    IOKey,
    create_io_key,
    hash_prompt,
    hash_tool_call,
    normalize_json_for_comparison
)

from .ordering import (
    OrderedEvent,
    EventOrderingManager,
    StepContext,
    get_ordering_manager,
    create_ordered_event,
    queue_event,
    step_context
)

from .determinism import (
    ClockProvider,
    RngProvider,
    SystemClockProvider,
    SystemRngProvider,
    FrozenClockProvider,
    RecordingClockProvider,
    RecordingRngProvider,
    ReplayRngProvider,
    DeterminismManager,
    get_determinism_manager,
    get_clock,
    get_rng,
    deterministic_context,
    now,
    timestamp,
    sleep,
    random_float,
    random_int,
    random_choice,
    random_uuid
)

from .redaction import (
    RedactionLevel,
    RetentionClass,
    RedactionRule,
    RetentionPolicy,
    RedactionFilter,
    RetentionManager,
    get_redaction_filter,
    get_retention_manager,
    set_redaction_level,
    redact_text,
    redact_dict,
    redact_json
)

from .policy_integration import (
    ReplayMode,
    ReplaySecurityPolicy,
    ReplayPolicyManager,
    get_replay_policy_manager,
    replay_security_context,
    check_file_access,
    check_network_access,
    enforce_replay_file_access,
    enforce_replay_network_access
)

# Phase 1: Streaming Support (Enhanced Telemetry Integration)
from .streaming import (
    StreamToken,
    StreamCapture,
    StreamReplay,
    StreamingLLMWrapper,
    capture_stream,
    capture_stream_async,
    create_streaming_wrapper,
    analyze_stream_timing,
    merge_stream_chunks,
    split_content_into_chunks
)

__all__ = [
    # Canonicalization
    'CanonicalHasher',
    'IOKey',
    'create_io_key',
    'hash_prompt',
    'hash_tool_call',
    'normalize_json_for_comparison',
    
    # Ordering
    'OrderedEvent',
    'EventOrderingManager',
    'StepContext',
    'get_ordering_manager',
    'create_ordered_event',
    'queue_event',
    'step_context',
    
    # Determinism
    'ClockProvider',
    'RngProvider',
    'SystemClockProvider',
    'SystemRngProvider',
    'FrozenClockProvider',
    'RecordingClockProvider',
    'RecordingRngProvider',
    'ReplayRngProvider',
    'DeterminismManager',
    'get_determinism_manager',
    'get_clock',
    'get_rng',
    'deterministic_context',
    'now',
    'timestamp',
    'sleep',
    'random_float',
    'random_int',
    'random_choice',
    'random_uuid',
    
    # Redaction
    'RedactionLevel',
    'RetentionClass',
    'RedactionRule',
    'RetentionPolicy',
    'RedactionFilter',
    'RetentionManager',
    'get_redaction_filter',
    'get_retention_manager',
    'set_redaction_level',
    'redact_text',
    'redact_dict',
    'redact_json',
    
    # Policy Integration
    'ReplayMode',
    'ReplaySecurityPolicy',
    'ReplayPolicyManager',
    'get_replay_policy_manager',
    'replay_security_context',
    'check_file_access',
    'check_network_access',
    'enforce_replay_file_access',
    'enforce_replay_network_access',
    
    # Streaming Support (Phase 1)
    'StreamToken',
    'StreamCapture',
    'StreamReplay',
    'StreamingLLMWrapper',
    'capture_stream',
    'capture_stream_async',
    'create_streaming_wrapper',
    'analyze_stream_timing',
    'merge_stream_chunks',
    'split_content_into_chunks'
]

# Version information
__version__ = "1.1.0"  # Updated for Phase 1
__author__ = "AI Dev Squad Enhancement Platform"
__description__ = "Record-Replay Foundation Components with Enhanced Telemetry Integration"