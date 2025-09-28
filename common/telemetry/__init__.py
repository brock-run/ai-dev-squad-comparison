"""
Telemetry module for AI Dev Squad platform.

This module provides comprehensive structured logging and observability
capabilities for tracking agent operations, performance metrics, and
system events across all framework implementations.
"""

from .schema import (
    EventType,
    LogLevel,
    BaseEvent,
    AgentEvent,
    TaskEvent,
    ToolEvent,
    SafetyEvent,
    VCSEvent,
    LLMEvent,
    PerformanceEvent,
    FrameworkEvent,
    create_event
)

from .logger import (
    StructuredLogger,
    EventFilter,
    EventBuffer,
    JSONLinesFormatter,
    get_logger,
    configure_logging
)

from .otel import (
    TraceManager,
    trace_function,
    configure_tracing,
    get_trace_manager,
    shutdown_tracing
)

from .cost_tracker import (
    CostTracker,
    ModelProvider,
    ModelPricing,
    TokenUsage,
    CostEntry,
    UsageStats,
    TokenCounter,
    BudgetManager,
    get_cost_tracker,
    configure_cost_tracking
)

from .dashboard import (
    EnhancedDashboard,
    DashboardMetrics,
    DashboardDataCollector,
    ParityMatrixEntry,
    create_dashboard,
    get_dashboard
)

__all__ = [
    # Schema classes
    "EventType",
    "LogLevel", 
    "BaseEvent",
    "AgentEvent",
    "TaskEvent",
    "ToolEvent",
    "SafetyEvent",
    "VCSEvent",
    "LLMEvent",
    "PerformanceEvent",
    "FrameworkEvent",
    "create_event",
    
    # Logger classes
    "StructuredLogger",
    "EventFilter",
    "EventBuffer",
    "JSONLinesFormatter",
    "get_logger",
    "configure_logging",
    
    # OpenTelemetry classes
    "TraceManager",
    "trace_function",
    "configure_tracing",
    "get_trace_manager",
    "shutdown_tracing",
    
    # Cost tracking classes
    "CostTracker",
    "ModelProvider",
    "ModelPricing",
    "TokenUsage",
    "CostEntry",
    "UsageStats",
    "TokenCounter",
    "BudgetManager",
    "get_cost_tracker",
    "configure_cost_tracking",
    
    # Dashboard classes
    "EnhancedDashboard",
    "DashboardMetrics",
    "DashboardDataCollector",
    "ParityMatrixEntry",
    "create_dashboard",
    "get_dashboard"
]