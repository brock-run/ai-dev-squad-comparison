"""
Enterprise Telemetry Manager for Strands Implementation

Provides comprehensive telemetry collection, metrics aggregation,
and distributed tracing with OpenTelemetry integration.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Fallback implementations
    class trace:
        @staticmethod
        def set_tracer_provider(provider): pass
        @staticmethod
        def get_tracer(name): return None
        @staticmethod
        def get_current_span(): return None
    
    class metrics:
        @staticmethod
        def set_meter_provider(provider): pass
        @staticmethod
        def get_meter(name): return None
    
    class TracerProvider: pass
    class MeterProvider: pass
    class JaegerExporter: pass


@dataclass
class TelemetryEvent:
    """Structured telemetry event."""
    timestamp: float
    event_type: str
    workflow_id: str
    agent_id: str
    data: Dict[str, Any]
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class TelemetryManager:
    """
    Enterprise telemetry manager with comprehensive observability features.
    """
    
    def __init__(self, endpoint: str = "http://localhost:14268/api/traces", enabled: bool = True):
        self.endpoint = endpoint
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)
        
        # Event storage
        self.events: List[TelemetryEvent] = []
        self.metrics_data: Dict[str, Any] = {}
        
        # OpenTelemetry components
        self.tracer = None
        self.meter = None
        
        if enabled and OTEL_AVAILABLE:
            self._initialize_opentelemetry()
    
    def _initialize_opentelemetry(self):
        """Initialize OpenTelemetry components."""
        try:
            # Initialize tracer
            trace.set_tracer_provider(TracerProvider())
            self.tracer = trace.get_tracer(__name__)
            
            # Initialize meter
            metrics.set_meter_provider(MeterProvider())
            self.meter = metrics.get_meter(__name__)
            
            self.logger.info("OpenTelemetry initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenTelemetry: {e}")
    
    async def emit_event(self, event_data: Dict[str, Any]):
        """Emit a telemetry event."""
        if not self.enabled:
            return
        
        try:
            # Create telemetry event
            event = TelemetryEvent(
                timestamp=time.time(),
                event_type=event_data.get("event_type", "unknown"),
                workflow_id=event_data.get("workflow_id", ""),
                agent_id=event_data.get("agent_id", "strands"),
                data=event_data,
                trace_id=self._get_current_trace_id(),
                span_id=self._get_current_span_id()
            )
            
            # Store event
            self.events.append(event)
            
            # Log structured event
            self.logger.info(
                f"Telemetry event: {event.event_type}",
                extra={
                    "telemetry_event": asdict(event),
                    "structured": True
                }
            )
            
            # Update metrics
            await self._update_metrics(event)
            
        except Exception as e:
            self.logger.error(f"Failed to emit telemetry event: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated telemetry metrics."""
        try:
            # Calculate event metrics
            event_counts = {}
            for event in self.events:
                event_type = event.event_type
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Calculate workflow metrics
            workflows = set(event.workflow_id for event in self.events if event.workflow_id)
            
            # Calculate timing metrics
            workflow_timings = {}
            for workflow_id in workflows:
                workflow_events = [e for e in self.events if e.workflow_id == workflow_id]
                if workflow_events:
                    start_time = min(e.timestamp for e in workflow_events)
                    end_time = max(e.timestamp for e in workflow_events)
                    workflow_timings[workflow_id] = end_time - start_time
            
            return {
                "total_events": len(self.events),
                "event_counts": event_counts,
                "active_workflows": len(workflows),
                "average_workflow_duration": (
                    sum(workflow_timings.values()) / len(workflow_timings)
                    if workflow_timings else 0
                ),
                "observability_events": len([e for e in self.events if "observability" in e.event_type]),
                "trace_spans": len([e for e in self.events if e.trace_id]),
                "last_event_timestamp": max(e.timestamp for e in self.events) if self.events else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate metrics: {e}")
            return {}
    
    async def _update_metrics(self, event: TelemetryEvent):
        """Update internal metrics based on event."""
        try:
            # Update event type counters
            event_type = event.event_type
            if event_type not in self.metrics_data:
                self.metrics_data[event_type] = {"count": 0, "last_seen": 0}
            
            self.metrics_data[event_type]["count"] += 1
            self.metrics_data[event_type]["last_seen"] = event.timestamp
            
            # Update workflow metrics
            if event.workflow_id:
                workflow_key = f"workflow_{event.workflow_id}"
                if workflow_key not in self.metrics_data:
                    self.metrics_data[workflow_key] = {"events": 0, "start_time": event.timestamp}
                
                self.metrics_data[workflow_key]["events"] += 1
                self.metrics_data[workflow_key]["last_event"] = event.timestamp
            
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
    
    def _get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID from OpenTelemetry context."""
        if not self.tracer or not OTEL_AVAILABLE:
            return None
        
        try:
            current_span = trace.get_current_span()
            if current_span and current_span.get_span_context().is_valid:
                return format(current_span.get_span_context().trace_id, '032x')
        except Exception:
            pass
        
        return None
    
    def _get_current_span_id(self) -> Optional[str]:
        """Get current span ID from OpenTelemetry context."""
        if not self.tracer or not OTEL_AVAILABLE:
            return None
        
        try:
            current_span = trace.get_current_span()
            if current_span and current_span.get_span_context().is_valid:
                return format(current_span.get_span_context().span_id, '016x')
        except Exception:
            pass
        
        return None
    
    async def export_events(self, format_type: str = "json") -> str:
        """Export telemetry events in specified format."""
        try:
            if format_type == "json":
                return json.dumps([asdict(event) for event in self.events], indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to export events: {e}")
            return ""
    
    async def clear_events(self, older_than_seconds: Optional[int] = None):
        """Clear telemetry events, optionally keeping recent ones."""
        try:
            if older_than_seconds is None:
                self.events.clear()
                self.logger.info("All telemetry events cleared")
            else:
                cutoff_time = time.time() - older_than_seconds
                initial_count = len(self.events)
                self.events = [e for e in self.events if e.timestamp > cutoff_time]
                cleared_count = initial_count - len(self.events)
                self.logger.info(f"Cleared {cleared_count} old telemetry events")
                
        except Exception as e:
            self.logger.error(f"Failed to clear events: {e}")