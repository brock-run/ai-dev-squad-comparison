"""
Tests for OpenTelemetry integration.

This module tests the distributed tracing capabilities, span management,
trace correlation, and exporter configuration functionality.
"""

import os
import time
import tempfile
from unittest import TestCase
from unittest.mock import patch, MagicMock

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from common.telemetry.otel import (
    TraceManager,
    trace_function,
    configure_tracing,
    get_trace_manager,
    shutdown_tracing
)
from common.telemetry.schema import EventType, BaseEvent


class TestTraceManager(TestCase):
    """Test cases for TraceManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset global state
        shutdown_tracing()
    
    def tearDown(self):
        """Clean up test environment."""
        shutdown_tracing()
    
    def test_trace_manager_creation(self):
        """Test TraceManager creation with default parameters."""
        trace_manager = TraceManager(
            service_name="test_service",
            service_version="1.0.0",
            environment="test",
            console_export=True
        )
        
        self.assertEqual(trace_manager.service_name, "test_service")
        self.assertEqual(trace_manager.service_version, "1.0.0")
        self.assertEqual(trace_manager.environment, "test")
        self.assertIsNotNone(trace_manager.tracer)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_manager_with_otlp_endpoint(self):
        """Test TraceManager with OTLP endpoint configuration."""
        trace_manager = TraceManager(
            service_name="test_service",
            otlp_endpoint="http://localhost:4317",
            console_export=False
        )
        
        self.assertIsNotNone(trace_manager.tracer)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_create_span(self):
        """Test span creation with attributes."""
        trace_manager = TraceManager(console_export=True)
        
        attributes = {
            "test.attribute": "test_value",
            "test.number": 42
        }
        
        span = trace_manager.create_span(
            name="test_span",
            kind=trace.SpanKind.INTERNAL,
            attributes=attributes
        )
        
        self.assertIsNotNone(span)
        self.assertTrue(span.is_recording())
        
        # End span
        span.end()
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_operation_context_manager(self):
        """Test trace operation context manager."""
        trace_manager = TraceManager(console_export=True)
        
        attributes = {"operation.type": "test"}
        
        with trace_manager.trace_operation(
            operation_name="test_operation",
            operation_type="internal",
            attributes=attributes
        ) as span:
            
            self.assertIsNotNone(span)
            self.assertTrue(span.is_recording())
            
            # Add some work
            time.sleep(0.01)
            
            # Span should still be active
            current_span = trace.get_current_span()
            self.assertEqual(span, current_span)
        
        # Span should be ended after context
        self.assertFalse(span.is_recording())
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_operation_with_exception(self):
        """Test trace operation handling exceptions."""
        trace_manager = TraceManager(console_export=True)
        
        with self.assertRaises(ValueError):
            with trace_manager.trace_operation(
                operation_name="failing_operation",
                record_exception=True
            ) as span:
                
                self.assertTrue(span.is_recording())
                raise ValueError("Test exception")
        
        # Span should be ended and marked as error
        self.assertFalse(span.is_recording())
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_agent_operation(self):
        """Test agent operation tracing."""
        trace_manager = TraceManager(console_export=True)
        
        with trace_manager.trace_agent_operation(
            agent_id="test_agent",
            framework="test_framework",
            operation="test_operation",
            attributes={"custom": "value"}
        ) as span:
            
            self.assertTrue(span.is_recording())
            
            # Verify span is current
            current_span = trace.get_current_span()
            self.assertEqual(span, current_span)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_task_execution(self):
        """Test task execution tracing."""
        trace_manager = TraceManager(console_export=True)
        
        with trace_manager.trace_task_execution(
            task_id="task_123",
            task_name="test_task",
            agent_id="test_agent",
            framework="test_framework"
        ) as span:
            
            self.assertTrue(span.is_recording())
            
            # Simulate task work
            time.sleep(0.01)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_tool_call(self):
        """Test tool call tracing."""
        trace_manager = TraceManager(console_export=True)
        
        with trace_manager.trace_tool_call(
            tool_name="test_tool",
            agent_id="test_agent",
            framework="test_framework",
            attributes={"tool.input": "test_input"}
        ) as span:
            
            self.assertTrue(span.is_recording())
            
            # Simulate tool execution
            time.sleep(0.01)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_llm_interaction(self):
        """Test LLM interaction tracing."""
        trace_manager = TraceManager(console_export=True)
        
        with trace_manager.trace_llm_interaction(
            model_name="test_model",
            provider="test_provider",
            agent_id="test_agent",
            attributes={"llm.tokens": 100}
        ) as span:
            
            self.assertTrue(span.is_recording())
            
            # Simulate LLM call
            time.sleep(0.01)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_safety_check(self):
        """Test safety check tracing."""
        trace_manager = TraceManager(console_export=True)
        
        with trace_manager.trace_safety_check(
            policy_name="test_policy",
            check_type="input_validation",
            attributes={"safety.risk_level": "low"}
        ) as span:
            
            self.assertTrue(span.is_recording())
            
            # Simulate safety check
            time.sleep(0.01)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_trace_vcs_operation(self):
        """Test VCS operation tracing."""
        trace_manager = TraceManager(console_export=True)
        
        with trace_manager.trace_vcs_operation(
            repository="test_repo",
            operation="commit",
            branch="main",
            attributes={"vcs.files_changed": 3}
        ) as span:
            
            self.assertTrue(span.is_recording())
            
            # Simulate VCS operation
            time.sleep(0.01)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_add_event_to_current_span(self):
        """Test adding telemetry events to current span."""
        trace_manager = TraceManager(console_export=True)
        
        # Create a test event
        event = BaseEvent(
            event_type=EventType.AGENT_START,
            message="Test agent started",
            agent_id="test_agent",
            framework="test_framework"
        )
        
        with trace_manager.trace_operation("test_operation") as span:
            
            # Add event to current span
            trace_manager.add_event_to_current_span(event, "agent.lifecycle")
            
            # Span should still be recording
            self.assertTrue(span.is_recording())
        
        # Clean up
        trace_manager.shutdown()
    
    def test_get_trace_context(self):
        """Test trace context extraction."""
        trace_manager = TraceManager(console_export=True)
        
        with trace_manager.trace_operation("test_operation"):
            
            # Get trace context
            context = trace_manager.get_trace_context()
            
            self.assertIsInstance(context, dict)
            # Should contain trace context headers
            self.assertTrue(any(key.startswith('traceparent') or key.startswith('tracestate') 
                              for key in context.keys()) or len(context) == 0)
        
        # Clean up
        trace_manager.shutdown()
    
    def test_get_current_trace_id(self):
        """Test getting current trace ID."""
        trace_manager = TraceManager(console_export=True)
        
        # No active span
        trace_id = trace_manager.get_current_trace_id()
        self.assertIsNone(trace_id)
        
        with trace_manager.trace_operation("test_operation"):
            
            # Should have trace ID
            trace_id = trace_manager.get_current_trace_id()
            self.assertIsNotNone(trace_id)
            self.assertIsInstance(trace_id, str)
            self.assertEqual(len(trace_id), 32)  # 128-bit trace ID as hex
        
        # Clean up
        trace_manager.shutdown()
    
    def test_get_current_span_id(self):
        """Test getting current span ID."""
        trace_manager = TraceManager(console_export=True)
        
        # No active span
        span_id = trace_manager.get_current_span_id()
        self.assertIsNone(span_id)
        
        with trace_manager.trace_operation("test_operation"):
            
            # Should have span ID
            span_id = trace_manager.get_current_span_id()
            self.assertIsNotNone(span_id)
            self.assertIsInstance(span_id, str)
            self.assertEqual(len(span_id), 16)  # 64-bit span ID as hex
        
        # Clean up
        trace_manager.shutdown()


class TestTraceFunctionDecorator(TestCase):
    """Test cases for trace function decorator."""
    
    def setUp(self):
        """Set up test environment."""
        shutdown_tracing()
        configure_tracing(console_export=True)
    
    def tearDown(self):
        """Clean up test environment."""
        shutdown_tracing()
    
    def test_trace_function_decorator(self):
        """Test function tracing decorator."""
        
        @trace_function(operation_name="test_function")
        def test_func(x, y):
            return x + y
        
        result = test_func(2, 3)
        self.assertEqual(result, 5)
    
    def test_trace_function_with_exception(self):
        """Test function decorator with exception handling."""
        
        @trace_function(record_exception=True)
        def failing_func():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            failing_func()
    
    def test_trace_function_with_attributes(self):
        """Test function decorator with custom attributes."""
        
        @trace_function(
            operation_name="custom_operation",
            attributes={"custom.attribute": "test_value"}
        )
        def custom_func(data):
            return len(data)
        
        result = custom_func("test")
        self.assertEqual(result, 4)
    
    def test_trace_function_without_trace_manager(self):
        """Test function decorator when no trace manager is configured."""
        
        # Shutdown tracing
        shutdown_tracing()
        
        @trace_function()
        def untraced_func():
            return "success"
        
        # Should work normally without tracing
        result = untraced_func()
        self.assertEqual(result, "success")


class TestGlobalTracing(TestCase):
    """Test cases for global tracing configuration."""
    
    def setUp(self):
        """Set up test environment."""
        shutdown_tracing()
    
    def tearDown(self):
        """Clean up test environment."""
        shutdown_tracing()
    
    def test_configure_tracing(self):
        """Test global tracing configuration."""
        
        trace_manager = configure_tracing(
            service_name="test_service",
            service_version="2.0.0",
            environment="test",
            console_export=True
        )
        
        self.assertIsNotNone(trace_manager)
        self.assertEqual(trace_manager.service_name, "test_service")
        self.assertEqual(trace_manager.service_version, "2.0.0")
        
        # Should be accessible globally
        global_manager = get_trace_manager()
        self.assertIs(trace_manager, global_manager)
    
    def test_configure_tracing_with_environment_variables(self):
        """Test tracing configuration with environment variables."""
        
        with patch.dict(os.environ, {
            'AI_DEV_SQUAD_ENVIRONMENT': 'production',
            'OTEL_EXPORTER_OTLP_ENDPOINT': 'http://localhost:4317'
        }):
            
            trace_manager = configure_tracing(
                service_name="env_test_service"
            )
            
            self.assertEqual(trace_manager.environment, "production")
    
    def test_get_trace_manager_when_not_configured(self):
        """Test getting trace manager when not configured."""
        
        manager = get_trace_manager()
        self.assertIsNone(manager)
    
    def test_shutdown_tracing(self):
        """Test tracing shutdown."""
        
        # Configure tracing
        trace_manager = configure_tracing(console_export=True)
        self.assertIsNotNone(get_trace_manager())
        
        # Shutdown
        shutdown_tracing()
        self.assertIsNone(get_trace_manager())


class TestTraceIntegration(TestCase):
    """Test cases for trace integration scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        shutdown_tracing()
        self.trace_manager = configure_tracing(
            service_name="integration_test",
            console_export=True
        )
    
    def tearDown(self):
        """Clean up test environment."""
        shutdown_tracing()
    
    def test_nested_operations(self):
        """Test nested operation tracing."""
        
        with self.trace_manager.trace_agent_operation(
            agent_id="parent_agent",
            framework="test_framework",
            operation="parent_operation"
        ) as parent_span:
            
            self.assertTrue(parent_span.is_recording())
            
            with self.trace_manager.trace_task_execution(
                task_id="child_task",
                task_name="child_task",
                agent_id="parent_agent",
                framework="test_framework"
            ) as child_span:
                
                self.assertTrue(child_span.is_recording())
                
                # Both spans should be different
                self.assertNotEqual(parent_span, child_span)
                
                # Child should be current
                current_span = trace.get_current_span()
                self.assertEqual(child_span, current_span)
            
            # Parent should be current again
            current_span = trace.get_current_span()
            self.assertEqual(parent_span, current_span)
    
    def test_multiple_concurrent_operations(self):
        """Test multiple concurrent operations."""
        
        # Start multiple operations
        with self.trace_manager.trace_agent_operation(
            agent_id="agent_1",
            framework="framework_1",
            operation="operation_1"
        ):
            
            with self.trace_manager.trace_tool_call(
                tool_name="tool_1",
                agent_id="agent_1",
                framework="framework_1"
            ):
                
                with self.trace_manager.trace_llm_interaction(
                    model_name="model_1",
                    provider="provider_1",
                    agent_id="agent_1"
                ):
                    
                    # All operations should be properly nested
                    current_span = trace.get_current_span()
                    self.assertTrue(current_span.is_recording())
    
    def test_trace_correlation(self):
        """Test trace correlation across operations."""
        
        trace_id = None
        
        with self.trace_manager.trace_operation("parent_operation") as parent_span:
            
            # Get trace ID from parent
            trace_id = self.trace_manager.get_current_trace_id()
            self.assertIsNotNone(trace_id)
            
            with self.trace_manager.trace_operation("child_operation") as child_span:
                
                # Child should have same trace ID
                child_trace_id = self.trace_manager.get_current_trace_id()
                self.assertEqual(trace_id, child_trace_id)
                
                # But different span IDs
                parent_span_id = parent_span.get_span_context().span_id
                child_span_id = child_span.get_span_context().span_id
                self.assertNotEqual(parent_span_id, child_span_id)
    
    def test_event_integration(self):
        """Test integration with telemetry events."""
        
        event = BaseEvent(
            event_type=EventType.TASK_START,
            message="Task started",
            task_id="test_task",
            agent_id="test_agent"
        )
        
        with self.trace_manager.trace_operation("event_test") as span:
            
            # Add event to span
            self.trace_manager.add_event_to_current_span(event)
            
            # Span should still be active
            self.assertTrue(span.is_recording())
            
            # Current span should be the same
            current_span = trace.get_current_span()
            self.assertEqual(span, current_span)