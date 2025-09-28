"""
OpenTelemetry integration for AI Dev Squad platform.

This module provides distributed tracing capabilities with span management,
trace correlation, and Jaeger exporter configuration for comprehensive
observability across all agent operations and framework implementations.
"""

import os
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union
from functools import wraps

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Optional Jaeger exporter (may not be available due to dependency conflicts)
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False

from .schema import EventType, LogLevel, BaseEvent


class TraceManager:
    """Manages OpenTelemetry tracing configuration and span operations."""
    
    def __init__(
        self,
        service_name: str = "ai-dev-squad",
        service_version: str = "1.0.0",
        environment: str = "development",
        jaeger_endpoint: Optional[str] = None,
        otlp_endpoint: Optional[str] = None,
        console_export: bool = False,
        sample_rate: float = 1.0
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.sample_rate = sample_rate
        
        # Initialize tracer provider
        self._setup_tracer_provider()
        
        # Setup exporters
        self._setup_exporters(jaeger_endpoint, otlp_endpoint, console_export)
        
        # Setup instrumentation
        self._setup_instrumentation()
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        
        # Propagator for trace context
        self.propagator = TraceContextTextMapPropagator()
    
    def _setup_tracer_provider(self):
        """Setup the OpenTelemetry tracer provider with resource information."""
        
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
    
    def _setup_exporters(
        self,
        jaeger_endpoint: Optional[str],
        otlp_endpoint: Optional[str],
        console_export: bool
    ):
        """Setup trace exporters for different backends."""
        
        tracer_provider = trace.get_tracer_provider()
        
        # Jaeger exporter (if available)
        if jaeger_endpoint and JAEGER_AVAILABLE:
            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_endpoint.split(':')[0] if ':' in jaeger_endpoint else jaeger_endpoint,
                agent_port=int(jaeger_endpoint.split(':')[1]) if ':' in jaeger_endpoint else 14268,
            )
            tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
        elif jaeger_endpoint and not JAEGER_AVAILABLE:
            print("Warning: Jaeger exporter requested but not available due to dependency conflicts")
        
        # OTLP exporter
        if otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
        
        # Console exporter for development
        if console_export:
            console_exporter = ConsoleSpanExporter()
            tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
        
        # Default to console if no exporters configured
        if not any([jaeger_endpoint, otlp_endpoint, console_export]):
            console_exporter = ConsoleSpanExporter()
            tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
    
    def _setup_instrumentation(self):
        """Setup automatic instrumentation for common libraries."""
        
        # Instrument HTTP requests
        RequestsInstrumentor().instrument()
        URLLib3Instrumentor().instrument()
    
    def create_span(
        self,
        name: str,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        parent_context: Optional[trace.Context] = None
    ) -> trace.Span:
        """Create a new span with optional attributes and parent context."""
        
        span = self.tracer.start_span(
            name=name,
            kind=kind,
            context=parent_context,
            attributes=attributes or {}
        )
        
        return span
    
    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        operation_type: str = "internal",
        attributes: Optional[Dict[str, Any]] = None,
        record_exception: bool = True
    ):
        """Context manager for tracing operations with automatic span management."""
        
        # Determine span kind
        span_kind_map = {
            "internal": trace.SpanKind.INTERNAL,
            "server": trace.SpanKind.SERVER,
            "client": trace.SpanKind.CLIENT,
            "producer": trace.SpanKind.PRODUCER,
            "consumer": trace.SpanKind.CONSUMER
        }
        span_kind = span_kind_map.get(operation_type, trace.SpanKind.INTERNAL)
        
        # Create span
        with self.tracer.start_as_current_span(
            name=operation_name,
            kind=span_kind,
            attributes=attributes or {}
        ) as span:
            start_time = time.time()
            
            try:
                yield span
                
                # Mark as successful
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Record exception
                if record_exception:
                    span.record_exception(e)
                    span.set_status(
                        Status(StatusCode.ERROR, str(e))
                    )
                
                # Re-raise exception
                raise
            
            finally:
                # Add timing information
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("operation.duration_ms", duration_ms)
    
    def trace_agent_operation(
        self,
        agent_id: str,
        framework: str,
        operation: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing agent operations."""
        
        operation_attributes = {
            "agent.id": agent_id,
            "agent.framework": framework,
            "agent.operation": operation,
            **(attributes or {})
        }
        
        return self.trace_operation(
            operation_name=f"agent.{operation}",
            operation_type="internal",
            attributes=operation_attributes
        )
    
    def trace_task_execution(
        self,
        task_id: str,
        task_name: str,
        agent_id: str,
        framework: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing task execution."""
        
        task_attributes = {
            "task.id": task_id,
            "task.name": task_name,
            "agent.id": agent_id,
            "agent.framework": framework,
            **(attributes or {})
        }
        
        return self.trace_operation(
            operation_name=f"task.{task_name}",
            operation_type="internal",
            attributes=task_attributes
        )
    
    def trace_tool_call(
        self,
        tool_name: str,
        agent_id: str,
        framework: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing tool calls."""
        
        tool_attributes = {
            "tool.name": tool_name,
            "agent.id": agent_id,
            "agent.framework": framework,
            **(attributes or {})
        }
        
        return self.trace_operation(
            operation_name=f"tool.{tool_name}",
            operation_type="client",
            attributes=tool_attributes
        )
    
    def trace_llm_interaction(
        self,
        model_name: str,
        provider: str,
        agent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing LLM interactions."""
        
        llm_attributes = {
            "llm.model": model_name,
            "llm.provider": provider,
            **({"agent.id": agent_id} if agent_id else {}),
            **(attributes or {})
        }
        
        return self.trace_operation(
            operation_name=f"llm.{provider}.{model_name}",
            operation_type="client",
            attributes=llm_attributes
        )
    
    def trace_safety_check(
        self,
        policy_name: str,
        check_type: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing safety checks."""
        
        safety_attributes = {
            "safety.policy": policy_name,
            "safety.check_type": check_type,
            **(attributes or {})
        }
        
        return self.trace_operation(
            operation_name=f"safety.{check_type}",
            operation_type="internal",
            attributes=safety_attributes
        )
    
    def trace_vcs_operation(
        self,
        repository: str,
        operation: str,
        branch: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing VCS operations."""
        
        vcs_attributes = {
            "vcs.repository": repository,
            "vcs.operation": operation,
            **({"vcs.branch": branch} if branch else {}),
            **(attributes or {})
        }
        
        return self.trace_operation(
            operation_name=f"vcs.{operation}",
            operation_type="client",
            attributes=vcs_attributes
        )
    
    def add_event_to_current_span(
        self,
        event: BaseEvent,
        event_name: Optional[str] = None
    ):
        """Add a telemetry event to the current span."""
        
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            
            # Convert event to span event
            event_data = event.to_dict()
            
            # Use event type as name if not provided
            name = event_name or event_data.get("event_type", "telemetry.event")
            
            # Add as span event
            current_span.add_event(
                name=name,
                attributes={
                    "event.id": event_data.get("event_id"),
                    "event.type": event_data.get("event_type"),
                    "event.level": event_data.get("level"),
                    "event.message": event_data.get("message"),
                    "event.framework": event_data.get("framework"),
                    "event.agent_id": event_data.get("agent_id"),
                    "event.task_id": event_data.get("task_id"),
                }
            )
    
    def get_trace_context(self) -> Dict[str, str]:
        """Get current trace context for propagation."""
        
        context = {}
        self.propagator.inject(context)
        return context
    
    def set_trace_context(self, context: Dict[str, str]):
        """Set trace context from propagated headers."""
        
        return self.propagator.extract(context)
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID if available."""
        
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            trace_id = current_span.get_span_context().trace_id
            return f"{trace_id:032x}"
        return None
    
    def get_current_span_id(self) -> Optional[str]:
        """Get current span ID if available."""
        
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            span_id = current_span.get_span_context().span_id
            return f"{span_id:016x}"
        return None
    
    def shutdown(self):
        """Shutdown the tracer provider and flush remaining spans."""
        
        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, 'shutdown'):
            tracer_provider.shutdown()


def trace_function(
    operation_name: Optional[str] = None,
    operation_type: str = "internal",
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True
):
    """Decorator for tracing function calls."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get global trace manager
            trace_manager = get_trace_manager()
            if not trace_manager:
                return func(*args, **kwargs)
            
            # Use function name if operation name not provided
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Add function information to attributes
            func_attributes = {
                "function.name": func.__name__,
                "function.module": func.__module__,
                **(attributes or {})
            }
            
            with trace_manager.trace_operation(
                operation_name=name,
                operation_type=operation_type,
                attributes=func_attributes,
                record_exception=record_exception
            ) as span:
                
                # Add argument information (be careful with sensitive data)
                if args:
                    span.set_attribute("function.args_count", len(args))
                if kwargs:
                    span.set_attribute("function.kwargs_count", len(kwargs))
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Add result information
                if result is not None:
                    span.set_attribute("function.has_result", True)
                    if isinstance(result, (str, int, float, bool)):
                        span.set_attribute("function.result_type", type(result).__name__)
                
                return result
        
        return wrapper
    return decorator


# Global trace manager instance
_global_trace_manager: Optional[TraceManager] = None


def configure_tracing(
    service_name: str = "ai-dev-squad",
    service_version: str = "1.0.0",
    environment: str = None,
    jaeger_endpoint: str = None,
    otlp_endpoint: str = None,
    console_export: bool = None,
    sample_rate: float = 1.0
) -> TraceManager:
    """Configure global tracing with specified parameters."""
    global _global_trace_manager
    
    # Use environment variables as defaults
    environment = environment or os.getenv("AI_DEV_SQUAD_ENVIRONMENT", "development")
    jaeger_endpoint = jaeger_endpoint or os.getenv("JAEGER_ENDPOINT")
    otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    # Default console export for development
    if console_export is None:
        console_export = environment == "development"
    
    _global_trace_manager = TraceManager(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        jaeger_endpoint=jaeger_endpoint,
        otlp_endpoint=otlp_endpoint,
        console_export=console_export,
        sample_rate=sample_rate
    )
    
    return _global_trace_manager


def get_trace_manager() -> Optional[TraceManager]:
    """Get the global trace manager instance."""
    return _global_trace_manager


def shutdown_tracing():
    """Shutdown global tracing and cleanup resources."""
    global _global_trace_manager
    
    if _global_trace_manager:
        _global_trace_manager.shutdown()
        _global_trace_manager = None