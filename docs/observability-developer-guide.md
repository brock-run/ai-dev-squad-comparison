# AI Dev Squad Observability - Developer Guide

This guide provides comprehensive technical information for developers integrating observability into AI agent frameworks and extending the observability system.

## 🏗️ Architecture Overview

The observability system consists of four integrated components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Structured     │    │  OpenTelemetry  │    │  Cost & Token   │
│  Logging        │    │  Tracing        │    │  Tracking       │
│                 │    │                 │    │                 │
│ • Event Schema  │    │ • Distributed   │    │ • Multi-Provider│
│ • JSON Lines    │    │   Traces        │    │ • Budget Mgmt   │
│ • Filtering     │    │ • Span Context  │    │ • Optimization  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Enhanced       │
                    │  Dashboard      │
                    │                 │
                    │ • Real-time UI  │
                    │ • REST APIs     │
                    │ • WebSocket     │
                    └─────────────────┘
```

## 📝 Structured Logging Implementation

### Core Components

#### Event Schema (`common/telemetry/schema.py`)
```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

class EventType(Enum):
    AGENT_START = "agent.start"
    AGENT_STOP = "agent.stop"
    TASK_START = "task.start"
    TASK_COMPLETE = "task.complete"
    TASK_FAIL = "task.fail"
    TOOL_CALL = "tool.call"
    TOOL_RESULT = "tool.result"
    SAFETY_VIOLATION = "safety.violation"
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    VCS_COMMIT = "vcs.commit"
    PERFORMANCE_METRIC = "performance.metric"
    SYSTEM_ERROR = "system.error"

@dataclass
class LogEvent:
    event_type: EventType
    timestamp: datetime
    level: LogLevel
    message: str
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    agent_id: Optional[str] = None
    framework: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

#### Logger Implementation (`common/telemetry/logger.py`)
```python
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from .schema import LogEvent, EventType, LogLevel

class StructuredLogger:
    def __init__(self, log_dir: str = "logs", enable_console: bool = False):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.session_id: Optional[str] = None
        self.correlation_id: Optional[str] = None
        
        # Setup file handler for JSON Lines format
        self.file_handler = logging.FileHandler(
            self.log_dir / "ai_dev_squad.jsonl"
        )
        self.file_handler.setFormatter(self._json_formatter)
        
        # Setup console handler if requested
        if enable_console:
            self.console_handler = logging.StreamHandler()
            self.console_handler.setFormatter(self._human_formatter)
    
    def _json_formatter(self, record):
        """Format log record as JSON Lines"""
        return json.dumps(record.__dict__, default=str)
    
    def _human_formatter(self, record):
        """Format log record for human reading"""
        return f"{record.timestamp} [{record.level.name}] {record.message}"
    
    def log_event(self, event: LogEvent):
        """Log a structured event"""
        # Add session context if available
        if self.session_id:
            event.session_id = self.session_id
        if self.correlation_id:
            event.correlation_id = self.correlation_id
        
        # Create log record
        record = logging.LogRecord(
            name="ai_dev_squad",
            level=event.level.value,
            pathname="",
            lineno=0,
            msg=event.message,
            args=(),
            exc_info=None
        )
        
        # Add structured data
        for field, value in event.__dict__.items():
            setattr(record, field, value)
        
        # Emit to handlers
        self.file_handler.emit(record)
        if hasattr(self, 'console_handler'):
            self.console_handler.emit(record)
    
    def set_session_context(self, session_id: str, correlation_id: str):
        """Set session context for all subsequent logs"""
        self.session_id = session_id
        self.correlation_id = correlation_id
    
    # Convenience methods for common events
    def log_agent_start(self, agent_id: str, agent_type: str, framework: str, 
                       capabilities: Optional[list] = None):
        event = LogEvent(
            event_type=EventType.AGENT_START,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            message=f"Agent {agent_id} starting",
            agent_id=agent_id,
            framework=framework,
            metadata={
                "agent_type": agent_type,
                "capabilities": capabilities or []
            }
        )
        self.log_event(event)
```

### Advanced Filtering

```python
class EventFilter:
    def __init__(self):
        self.level_filter: Optional[LogLevel] = None
        self.framework_filter: Optional[set] = None
        self.custom_filters: list = []
    
    def set_level_filter(self, min_level: LogLevel):
        """Filter events by minimum log level"""
        self.level_filter = min_level
    
    def set_framework_filter(self, frameworks: list):
        """Filter events by framework"""
        self.framework_filter = set(frameworks)
    
    def add_custom_filter(self, filter_func):
        """Add custom filter function"""
        self.custom_filters.append(filter_func)
    
    def should_log(self, event: LogEvent) -> bool:
        """Determine if event should be logged"""
        # Level filter
        if self.level_filter and event.level.value < self.level_filter.value:
            return False
        
        # Framework filter
        if self.framework_filter and event.framework not in self.framework_filter:
            return False
        
        # Custom filters
        for filter_func in self.custom_filters:
            if not filter_func(event.__dict__):
                return False
        
        return True
```

## 🔍 OpenTelemetry Tracing Implementation

### Trace Manager (`common/telemetry/otel.py`)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from contextlib import contextmanager
from typing import Optional, Dict, Any

class TraceManager:
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        
        # Configure tracer provider
        trace.set_tracer_provider(TracerProvider(
            resource=Resource.create({
                "service.name": service_name,
                "service.version": service_version
            })
        ))
        
        self.tracer = trace.get_tracer(__name__)
        
        # Auto-instrument common libraries
        RequestsInstrumentor().instrument()
    
    def add_exporter(self, exporter_type: str, **kwargs):
        """Add span exporter"""
        if exporter_type == "otlp":
            exporter = OTLPSpanExporter(
                endpoint=kwargs.get("endpoint", "http://localhost:4317")
            )
        elif exporter_type == "jaeger":
            exporter = JaegerExporter(
                agent_host_name=kwargs.get("host", "localhost"),
                agent_port=kwargs.get("port", 6831)
            )
        elif exporter_type == "console":
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            exporter = ConsoleSpanExporter()
        else:
            raise ValueError(f"Unknown exporter type: {exporter_type}")
        
        processor = BatchSpanProcessor(exporter)
        trace.get_tracer_provider().add_span_processor(processor)
    
    @contextmanager
    def trace_operation(self, operation_name: str, attributes: Optional[Dict] = None):
        """Create a traced operation context"""
        with self.tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
    
    @contextmanager
    def trace_agent_operation(self, agent_id: str, framework: str, operation: str):
        """Trace an agent operation with standard attributes"""
        attributes = {
            "agent.id": agent_id,
            "agent.framework": framework,
            "agent.operation": operation
        }
        
        with self.trace_operation(f"agent.{operation}", attributes) as span:
            yield span
    
    @contextmanager
    def trace_llm_interaction(self, model_name: str, provider: str, agent_id: str):
        """Trace LLM API interactions"""
        attributes = {
            "llm.model": model_name,
            "llm.provider": provider,
            "agent.id": agent_id
        }
        
        with self.trace_operation("llm.interaction", attributes) as span:
            yield span
```

### Function Tracing Decorator

```python
from functools import wraps
from typing import Callable, Optional, Dict, Any

def trace_function(
    operation_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
):
    """Decorator to automatically trace function calls"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_trace_manager()
            if not tracer:
                return func(*args, **kwargs)
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.trace_operation(op_name, attributes) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Add result metadata if serializable
                try:
                    if isinstance(result, (str, int, float, bool)):
                        span.set_attribute("function.result_type", type(result).__name__)
                except:
                    pass
                
                return result
        
        return wrapper
    return decorator

# Usage example
@trace_function(
    operation_name="data_processing",
    attributes={"component": "data_pipeline"}
)
def process_data(data):
    # Function automatically traced
    return transformed_data
```

## 💰 Cost and Token Tracking Implementation

### Cost Tracker Core (`common/telemetry/cost_tracker.py`)

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import tiktoken

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    CUSTOM = "custom"

@dataclass
class ModelPricing:
    model_name: str
    provider: ModelProvider
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float
    context_window: int

@dataclass
class CostEntry:
    timestamp: datetime
    model_name: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    framework: Optional[str] = None

class CostTracker:
    def __init__(self):
        self.entries: List[CostEntry] = []
        self.pricing_models: Dict[str, ModelPricing] = {}
        self.budget_manager = BudgetManager()
        
        # Load default pricing models
        self._load_default_pricing()
    
    def _load_default_pricing(self):
        """Load default pricing for common models"""
        default_models = [
            ModelPricing("gpt-4", ModelProvider.OPENAI, 0.03, 0.06, 8192),
            ModelPricing("gpt-3.5-turbo", ModelProvider.OPENAI, 0.001, 0.002, 4096),
            ModelPricing("claude-3-opus", ModelProvider.ANTHROPIC, 0.015, 0.075, 200000),
            ModelPricing("claude-3-sonnet", ModelProvider.ANTHROPIC, 0.003, 0.015, 200000),
        ]
        
        for model in default_models:
            self.pricing_models[f"{model.provider.value}:{model.model_name}"] = model
    
    def add_pricing_model(self, pricing: ModelPricing):
        """Add or update pricing for a model"""
        key = f"{pricing.provider.value}:{pricing.model_name}"
        self.pricing_models[key] = pricing
    
    def estimate_cost(self, text: str, model_name: str, provider: str) -> Dict[str, Any]:
        """Estimate cost for a text input"""
        key = f"{provider}:{model_name}"
        if key not in self.pricing_models:
            raise ValueError(f"No pricing data for {key}")
        
        pricing = self.pricing_models[key]
        
        # Count input tokens
        input_tokens = self._count_tokens(text, model_name)
        
        # Estimate output tokens (rough heuristic)
        estimated_output_tokens = min(input_tokens // 2, pricing.context_window - input_tokens)
        
        # Calculate costs
        input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k_tokens
        estimated_output_cost = (estimated_output_tokens / 1000) * pricing.output_cost_per_1k_tokens
        
        return {
            "input_tokens": input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "input_cost_usd": input_cost,
            "estimated_output_cost_usd": estimated_output_cost,
            "estimated_cost_usd": input_cost + estimated_output_cost
        }
    
    def track_llm_usage(self, model_name: str, provider: str, input_tokens: int,
                       output_tokens: int, duration_ms: int,
                       session_id: Optional[str] = None,
                       agent_id: Optional[str] = None,
                       framework: Optional[str] = None) -> CostEntry:
        """Track actual LLM usage and calculate cost"""
        key = f"{provider}:{model_name}"
        if key not in self.pricing_models:
            # Use default pricing if not found
            cost_usd = 0.0
        else:
            pricing = self.pricing_models[key]
            input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k_tokens
            output_cost = (output_tokens / 1000) * pricing.output_cost_per_1k_tokens
            cost_usd = input_cost + output_cost
        
        entry = CostEntry(
            timestamp=datetime.utcnow(),
            model_name=model_name,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            session_id=session_id,
            agent_id=agent_id,
            framework=framework
        )
        
        self.entries.append(entry)
        
        # Check budgets
        self.budget_manager.check_budgets(entry)
        
        return entry
    
    def _count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens for text using appropriate tokenizer"""
        try:
            if "gpt" in model_name.lower():
                encoding = tiktoken.encoding_for_model(model_name)
                return len(encoding.encode(text))
            else:
                # Rough approximation for other models
                return len(text.split()) * 1.3
        except:
            # Fallback approximation
            return len(text) // 4
```

### Budget Management

```python
class BudgetManager:
    def __init__(self):
        self.budgets: Dict[str, Budget] = {}
        self.alert_callbacks: List[Callable] = []
    
    def set_budget(self, name: str, limit_usd: float, period: str,
                  alert_thresholds: List[float] = None):
        """Set a budget with optional alert thresholds"""
        budget = Budget(
            name=name,
            limit_usd=limit_usd,
            period=period,
            alert_thresholds=alert_thresholds or [0.8, 0.9]
        )
        self.budgets[name] = budget
    
    def check_budgets(self, cost_entry: CostEntry):
        """Check all budgets against new cost entry"""
        for budget in self.budgets.values():
            current_spend = self._calculate_period_spend(budget, cost_entry.timestamp)
            spend_ratio = current_spend / budget.limit_usd
            
            # Check if any thresholds are crossed
            for threshold in budget.alert_thresholds:
                if spend_ratio >= threshold and not budget.alerts_sent.get(threshold, False):
                    self._send_alert(budget, spend_ratio, current_spend)
                    budget.alerts_sent[threshold] = True
    
    def _send_alert(self, budget: Budget, spend_ratio: float, current_spend: float):
        """Send budget alert to registered callbacks"""
        alert_data = {
            "budget_name": budget.name,
            "spend_ratio": spend_ratio,
            "current_spend_usd": current_spend,
            "limit_usd": budget.limit_usd,
            "timestamp": datetime.utcnow()
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                print(f"Error in budget alert callback: {e}")
```

## 📊 Enhanced Dashboard Implementation

### Flask Application (`common/telemetry/dashboard.py`)

```python
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class ObservabilityDashboard:
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.host = host
        self.port = port
        
        # Data sources
        self.logger = get_logger()
        self.cost_tracker = get_cost_tracker()
        
        # Setup routes
        self._setup_routes()
        self._setup_websocket_handlers()
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/parity-matrix')
        def parity_matrix():
            return render_template('parity_matrix.html')
        
        @self.app.route('/api/metrics')
        def api_metrics():
            time_range = request.args.get('time_range', '24h')
            frameworks = request.args.get('frameworks', '').split(',')
            
            metrics = self._get_metrics(time_range, frameworks)
            return jsonify(metrics)
        
        @self.app.route('/api/cost-analysis')
        def api_cost_analysis():
            time_range = request.args.get('time_range', '7d')
            analysis = self._get_cost_analysis(time_range)
            return jsonify(analysis)
        
        @self.app.route('/api/parity-matrix')
        def api_parity_matrix():
            matrix = self._get_parity_matrix()
            return jsonify(matrix)
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket handlers for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected')
            # Send initial data
            emit('metrics_update', self._get_real_time_metrics())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected')
    
    def _get_metrics(self, time_range: str, frameworks: List[str]) -> Dict[str, Any]:
        """Get metrics for specified time range and frameworks"""
        # Parse time range
        if time_range == '1h':
            start_time = datetime.utcnow() - timedelta(hours=1)
        elif time_range == '24h':
            start_time = datetime.utcnow() - timedelta(days=1)
        elif time_range == '7d':
            start_time = datetime.utcnow() - timedelta(days=7)
        else:
            start_time = datetime.utcnow() - timedelta(days=1)
        
        # Filter cost entries
        filtered_entries = [
            entry for entry in self.cost_tracker.entries
            if entry.timestamp >= start_time and
            (not frameworks or entry.framework in frameworks)
        ]
        
        # Calculate metrics
        total_cost = sum(entry.cost_usd for entry in filtered_entries)
        total_tokens = sum(entry.input_tokens + entry.output_tokens for entry in filtered_entries)
        total_requests = len(filtered_entries)
        avg_response_time = sum(entry.duration_ms for entry in filtered_entries) / max(total_requests, 1)
        
        return {
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "avg_response_time_ms": avg_response_time,
            "cost_by_model": self._group_by_model(filtered_entries),
            "usage_over_time": self._get_usage_timeline(filtered_entries)
        }
    
    def run(self, debug: bool = False):
        """Start the dashboard server"""
        print(f"🚀 Starting observability dashboard at http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)
```

### Real-time Updates

```python
import threading
import time

class RealTimeUpdater:
    def __init__(self, dashboard: ObservabilityDashboard):
        self.dashboard = dashboard
        self.running = False
        self.update_thread = None
    
    def start(self, interval: int = 5):
        """Start real-time updates"""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, args=(interval,))
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def stop(self):
        """Stop real-time updates"""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
    
    def _update_loop(self, interval: int):
        """Main update loop"""
        while self.running:
            try:
                # Get latest metrics
                metrics = self.dashboard._get_real_time_metrics()
                
                # Emit to all connected clients
                self.dashboard.socketio.emit('metrics_update', metrics)
                
                time.sleep(interval)
            except Exception as e:
                print(f"Error in real-time update: {e}")
                time.sleep(interval)
```

## 🔧 Framework Integration Patterns

### LangGraph Integration

```python
from langgraph import StateGraph
from common.telemetry import get_logger, get_trace_manager, get_cost_tracker

class ObservableLangGraphAdapter:
    def __init__(self):
        self.logger = get_logger()
        self.tracer = get_trace_manager()
        self.cost_tracker = get_cost_tracker()
    
    def create_observable_node(self, node_func, node_name: str):
        """Wrap a LangGraph node with observability"""
        def observable_node(state):
            agent_id = f"langgraph_{node_name}"
            
            with self.tracer.trace_agent_operation(agent_id, "langgraph", "node_execution"):
                self.logger.log_task_start(node_name, node_name, agent_id, "langgraph")
                
                try:
                    # Execute original node
                    result = node_func(state)
                    
                    # Log success
                    self.logger.log_task_complete(node_name, node_name, agent_id, "langgraph", 1500)
                    
                    return result
                    
                except Exception as e:
                    # Log error
                    self.logger.log_task_error(node_name, node_name, agent_id, "langgraph", str(e))
                    raise
        
        return observable_node
    
    def build_observable_graph(self, graph_definition: Dict):
        """Build a LangGraph with observability"""
        graph = StateGraph(dict)
        
        for node_name, node_func in graph_definition.items():
            observable_node = self.create_observable_node(node_func, node_name)
            graph.add_node(node_name, observable_node)
        
        return graph
```

### CrewAI Integration

```python
from crewai import Agent, Task, Crew
from common.telemetry import get_logger, get_trace_manager

class ObservableCrewAIAdapter:
    def __init__(self):
        self.logger = get_logger()
        self.tracer = get_trace_manager()
    
    def create_observable_agent(self, agent_config: Dict) -> Agent:
        """Create a CrewAI agent with observability"""
        
        class ObservableAgent(Agent):
            def __init__(self, adapter, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.adapter = adapter
                self.agent_id = f"crewai_{self.role.lower().replace(' ', '_')}"
            
            def execute_task(self, task):
                with self.adapter.tracer.trace_agent_operation(
                    self.agent_id, "crewai", "task_execution"
                ):
                    self.adapter.logger.log_agent_start(
                        self.agent_id, self.role, "crewai"
                    )
                    
                    try:
                        result = super().execute_task(task)
                        self.adapter.logger.log_agent_stop(self.agent_id, "crewai")
                        return result
                    except Exception as e:
                        self.adapter.logger.log_task_error(
                            "task_execution", "execute_task", 
                            self.agent_id, "crewai", str(e)
                        )
                        raise
        
        return ObservableAgent(self, **agent_config)
```

## 🧪 Testing Observability Components

### Unit Tests

```python
import unittest
from unittest.mock import Mock, patch
from common.telemetry import StructuredLogger, TraceManager, CostTracker

class TestStructuredLogger(unittest.TestCase):
    def setUp(self):
        self.logger = StructuredLogger(log_dir="test_logs", enable_console=False)
    
    def test_log_event(self):
        """Test basic event logging"""
        event = LogEvent(
            event_type=EventType.AGENT_START,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            message="Test message"
        )
        
        # Should not raise exception
        self.logger.log_event(event)
    
    def test_session_context(self):
        """Test session context setting"""
        self.logger.set_session_context("session_123", "correlation_456")
        
        self.assertEqual(self.logger.session_id, "session_123")
        self.assertEqual(self.logger.correlation_id, "correlation_456")

class TestCostTracker(unittest.TestCase):
    def setUp(self):
        self.cost_tracker = CostTracker()
    
    def test_track_llm_usage(self):
        """Test LLM usage tracking"""
        entry = self.cost_tracker.track_llm_usage(
            model_name="gpt-3.5-turbo",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            duration_ms=1500
        )
        
        self.assertEqual(entry.model_name, "gpt-3.5-turbo")
        self.assertEqual(entry.input_tokens, 100)
        self.assertEqual(entry.output_tokens, 50)
        self.assertGreater(entry.cost_usd, 0)
    
    def test_cost_estimation(self):
        """Test cost estimation"""
        estimate = self.cost_tracker.estimate_cost(
            "Hello world", "gpt-3.5-turbo", "openai"
        )
        
        self.assertIn("estimated_cost_usd", estimate)
        self.assertIn("input_tokens", estimate)
        self.assertGreater(estimate["estimated_cost_usd"], 0)
```

### Integration Tests

```python
class TestObservabilityIntegration(unittest.TestCase):
    def setUp(self):
        """Setup full observability stack"""
        self.logger = configure_logging(log_dir="test_logs")
        self.tracer = configure_tracing(service_name="test_service")
        self.cost_tracker = configure_cost_tracking()
        self.dashboard = create_dashboard(port=8081)
    
    def test_end_to_end_flow(self):
        """Test complete observability flow"""
        # Start tracing
        with self.tracer.trace_operation("test_operation") as span:
            # Log events
            self.logger.log_agent_start("test_agent", "developer", "test_framework")
            
            # Track costs
            cost_entry = self.cost_tracker.track_llm_usage(
                model_name="gpt-3.5-turbo",
                provider="openai",
                input_tokens=100,
                output_tokens=50,
                duration_ms=1500
            )
            
            # Verify data is connected
            self.assertIsNotNone(cost_entry)
            self.assertIsNotNone(span)
    
    def test_dashboard_api(self):
        """Test dashboard API endpoints"""
        with self.dashboard.app.test_client() as client:
            # Test metrics endpoint
            response = client.get('/api/metrics?time_range=1h')
            self.assertEqual(response.status_code, 200)
            
            data = response.get_json()
            self.assertIn("total_cost_usd", data)
            self.assertIn("total_requests", data)
```

## 🚀 Production Deployment

### Docker Configuration

```dockerfile
# Dockerfile for observability-enabled service
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create log directory
RUN mkdir -p /app/logs

# Expose dashboard port
EXPOSE 8080

# Set environment variables
ENV AI_DEV_SQUAD_LOG_LEVEL=INFO
ENV AI_DEV_SQUAD_LOG_DIR=/app/logs
ENV DASHBOARD_HOST=0.0.0.0
ENV DASHBOARD_PORT=8080

# Start application with observability
CMD ["python", "main.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-dev-squad-observability
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-dev-squad
  template:
    metadata:
      labels:
        app: ai-dev-squad
    spec:
      containers:
      - name: ai-dev-squad
        image: ai-dev-squad:latest
        ports:
        - containerPort: 8080
        env:
        - name: AI_DEV_SQUAD_ENVIRONMENT
          value: "production"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector:4317"
        - name: DASHBOARD_HOST
          value: "0.0.0.0"
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: ai-dev-squad-service
spec:
  selector:
    app: ai-dev-squad
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

## 📈 Performance Considerations

### Optimization Strategies

1. **Async Logging**: Use background threads for log processing
2. **Batch Processing**: Batch span exports and log writes
3. **Sampling**: Use trace sampling in high-volume environments
4. **Caching**: Cache dashboard data with appropriate TTL
5. **Compression**: Compress log files and trace data

### Memory Management

```python
class OptimizedCostTracker(CostTracker):
    def __init__(self, max_entries: int = 10000):
        super().__init__()
        self.max_entries = max_entries
    
    def track_llm_usage(self, *args, **kwargs) -> CostEntry:
        """Track usage with memory management"""
        entry = super().track_llm_usage(*args, **kwargs)
        
        # Rotate entries if limit exceeded
        if len(self.entries) > self.max_entries:
            # Keep most recent entries
            self.entries = self.entries[-self.max_entries:]
        
        return entry
```

## 🔧 Extending the System

### Adding New Event Types

```python
# 1. Add to EventType enum
class EventType(Enum):
    # ... existing types
    CUSTOM_EVENT = "custom.event"

# 2. Create convenience method
def log_custom_event(self, custom_data: Dict[str, Any]):
    event = LogEvent(
        event_type=EventType.CUSTOM_EVENT,
        timestamp=datetime.utcnow(),
        level=LogLevel.INFO,
        message="Custom event occurred",
        metadata=custom_data
    )
    self.log_event(event)
```

### Adding New Cost Providers

```python
class CustomProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_pricing(self, model_name: str) -> ModelPricing:
        """Fetch pricing from custom provider API"""
        # Implementation specific to provider
        pass
    
    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens using provider's tokenizer"""
        # Implementation specific to provider
        pass

# Register with cost tracker
cost_tracker.add_provider("custom", CustomProvider(api_key="..."))
```

This developer guide provides comprehensive technical information for integrating and extending the AI Dev Squad observability system. The modular architecture allows for easy customization while maintaining consistency across different AI frameworks.