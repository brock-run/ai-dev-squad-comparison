"""
Tests for structured logging system.

This module tests the structured logger, event filtering, buffering,
and JSON Lines output functionality.
"""

import json
import os
import tempfile
import time
import threading
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

from common.telemetry.logger import (
    StructuredLogger,
    EventFilter,
    EventBuffer,
    JSONLinesFormatter,
    get_logger,
    configure_logging
)
from common.telemetry.schema import EventType, LogLevel, BaseEvent, AgentEvent


class TestEventBuffer(TestCase):
    """Test cases for event buffer functionality."""
    
    def test_buffer_creation(self):
        """Test event buffer creation with default parameters."""
        buffer = EventBuffer()
        
        self.assertEqual(buffer.max_size, 1000)
        self.assertEqual(buffer.flush_interval, 5.0)
        self.assertEqual(buffer.size(), 0)
    
    def test_buffer_add_events(self):
        """Test adding events to buffer."""
        buffer = EventBuffer(max_size=3, flush_interval=10.0)
        
        # Add events below threshold
        event1 = {"event_id": "1", "message": "test1"}
        event2 = {"event_id": "2", "message": "test2"}
        
        should_flush1 = buffer.add_event(event1)
        should_flush2 = buffer.add_event(event2)
        
        self.assertFalse(should_flush1)
        self.assertFalse(should_flush2)
        self.assertEqual(buffer.size(), 2)
        
        # Add event that triggers size threshold
        event3 = {"event_id": "3", "message": "test3"}
        should_flush3 = buffer.add_event(event3)
        
        self.assertTrue(should_flush3)
        self.assertEqual(buffer.size(), 3)
    
    def test_buffer_time_flush(self):
        """Test buffer flushing based on time interval."""
        buffer = EventBuffer(max_size=100, flush_interval=0.1)
        
        # Add event
        event = {"event_id": "1", "message": "test"}
        should_flush1 = buffer.add_event(event)
        self.assertFalse(should_flush1)
        
        # Wait for flush interval
        time.sleep(0.15)
        
        # Add another event - should trigger time-based flush
        event2 = {"event_id": "2", "message": "test2"}
        should_flush2 = buffer.add_event(event2)
        self.assertTrue(should_flush2)
    
    def test_buffer_get_events(self):
        """Test retrieving events from buffer."""
        buffer = EventBuffer()
        
        # Add some events
        events = [
            {"event_id": "1", "message": "test1"},
            {"event_id": "2", "message": "test2"},
            {"event_id": "3", "message": "test3"}
        ]
        
        for event in events:
            buffer.add_event(event)
        
        # Get events
        retrieved_events = buffer.get_events()
        
        self.assertEqual(len(retrieved_events), 3)
        self.assertEqual(retrieved_events[0]["event_id"], "1")
        self.assertEqual(retrieved_events[2]["event_id"], "3")
        
        # Buffer should be empty after get_events
        self.assertEqual(buffer.size(), 0)
    
    def test_buffer_thread_safety(self):
        """Test buffer thread safety with concurrent access."""
        buffer = EventBuffer(max_size=1000)
        results = []
        
        def add_events(start_id, count):
            for i in range(count):
                event = {"event_id": f"{start_id}_{i}", "message": f"test_{start_id}_{i}"}
                buffer.add_event(event)
        
        # Create multiple threads adding events
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_events, args=(i, 20))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have 100 events total
        self.assertEqual(buffer.size(), 100)
        
        # Get all events
        events = buffer.get_events()
        self.assertEqual(len(events), 100)


class TestEventFilter(TestCase):
    """Test cases for event filtering functionality."""
    
    def test_filter_creation(self):
        """Test event filter creation with default settings."""
        filter_obj = EventFilter()
        
        self.assertIsNone(filter_obj.level_filter)
        self.assertIsNone(filter_obj.event_type_filter)
        self.assertIsNone(filter_obj.framework_filter)
        self.assertIsNone(filter_obj.agent_filter)
        self.assertEqual(len(filter_obj.custom_filters), 0)
    
    def test_level_filtering(self):
        """Test filtering by log level."""
        filter_obj = EventFilter()
        filter_obj.set_level_filter(LogLevel.WARNING)
        
        # Test events at different levels
        debug_event = {"level": "DEBUG", "message": "debug message"}
        info_event = {"level": "INFO", "message": "info message"}
        warning_event = {"level": "WARNING", "message": "warning message"}
        error_event = {"level": "ERROR", "message": "error message"}
        
        self.assertFalse(filter_obj.should_process(debug_event))
        self.assertFalse(filter_obj.should_process(info_event))
        self.assertTrue(filter_obj.should_process(warning_event))
        self.assertTrue(filter_obj.should_process(error_event))
    
    def test_event_type_filtering(self):
        """Test filtering by event type."""
        filter_obj = EventFilter()
        filter_obj.set_event_type_filter([EventType.AGENT_START, EventType.TASK_COMPLETE])
        
        # Test events of different types
        agent_event = {"event_type": "agent.start", "message": "agent started"}
        task_event = {"event_type": "task.complete", "message": "task completed"}
        tool_event = {"event_type": "tool.call", "message": "tool called"}
        
        self.assertTrue(filter_obj.should_process(agent_event))
        self.assertTrue(filter_obj.should_process(task_event))
        self.assertFalse(filter_obj.should_process(tool_event))
    
    def test_framework_filtering(self):
        """Test filtering by framework."""
        filter_obj = EventFilter()
        filter_obj.set_framework_filter(["langgraph", "crewai"])
        
        # Test events from different frameworks
        langgraph_event = {"framework": "langgraph", "message": "langgraph event"}
        crewai_event = {"framework": "crewai", "message": "crewai event"}
        autogen_event = {"framework": "autogen", "message": "autogen event"}
        no_framework_event = {"message": "no framework"}
        
        self.assertTrue(filter_obj.should_process(langgraph_event))
        self.assertTrue(filter_obj.should_process(crewai_event))
        self.assertFalse(filter_obj.should_process(autogen_event))
        self.assertFalse(filter_obj.should_process(no_framework_event))
    
    def test_agent_filtering(self):
        """Test filtering by agent ID."""
        filter_obj = EventFilter()
        filter_obj.set_agent_filter(["agent_1", "agent_2"])
        
        # Test events from different agents
        agent1_event = {"agent_id": "agent_1", "message": "agent 1 event"}
        agent2_event = {"agent_id": "agent_2", "message": "agent 2 event"}
        agent3_event = {"agent_id": "agent_3", "message": "agent 3 event"}
        no_agent_event = {"message": "no agent"}
        
        self.assertTrue(filter_obj.should_process(agent1_event))
        self.assertTrue(filter_obj.should_process(agent2_event))
        self.assertFalse(filter_obj.should_process(agent3_event))
        self.assertFalse(filter_obj.should_process(no_agent_event))
    
    def test_custom_filtering(self):
        """Test custom filter functions."""
        filter_obj = EventFilter()
        
        # Add custom filter that only allows events with "important" in message
        def important_filter(event_data):
            return "important" in event_data.get("message", "").lower()
        
        filter_obj.add_custom_filter(important_filter)
        
        # Test events
        important_event = {"message": "This is important"}
        normal_event = {"message": "This is normal"}
        
        self.assertTrue(filter_obj.should_process(important_event))
        self.assertFalse(filter_obj.should_process(normal_event))
    
    def test_combined_filtering(self):
        """Test multiple filters working together."""
        filter_obj = EventFilter()
        filter_obj.set_level_filter(LogLevel.INFO)
        filter_obj.set_framework_filter(["langgraph"])
        
        # Test events with different combinations
        valid_event = {
            "level": "INFO",
            "framework": "langgraph",
            "message": "valid event"
        }
        
        wrong_level_event = {
            "level": "DEBUG",
            "framework": "langgraph",
            "message": "wrong level"
        }
        
        wrong_framework_event = {
            "level": "INFO",
            "framework": "crewai",
            "message": "wrong framework"
        }
        
        self.assertTrue(filter_obj.should_process(valid_event))
        self.assertFalse(filter_obj.should_process(wrong_level_event))
        self.assertFalse(filter_obj.should_process(wrong_framework_event))


class TestJSONLinesFormatter(TestCase):
    """Test cases for JSON Lines formatter."""
    
    def test_formatter_with_event_data(self):
        """Test formatter with structured event data."""
        formatter = JSONLinesFormatter()
        
        # Create mock log record with event data
        record = MagicMock()
        record.event_data = {
            "event_id": "test_123",
            "timestamp": "2024-01-01T12:00:00",
            "event_type": "test.event",
            "level": "INFO",
            "message": "Test message"
        }
        
        # Format the record
        formatted = formatter.format(record)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        self.assertEqual(parsed["event_id"], "test_123")
        self.assertEqual(parsed["event_type"], "test.event")
        self.assertEqual(parsed["message"], "Test message")
    
    def test_formatter_without_event_data(self):
        """Test formatter with standard log record."""
        formatter = JSONLinesFormatter()
        
        # Create mock log record without event data
        record = MagicMock()
        record.levelname = "INFO"
        record.name = "test_logger"
        record.module = "test_module"
        record.funcName = "test_function"
        record.lineno = 42
        record.getMessage.return_value = "Standard log message"
        
        # Remove event_data attribute
        del record.event_data
        
        # Format the record
        formatted = formatter.format(record)
        
        # Should be valid JSON with basic structure
        parsed = json.loads(formatted)
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["message"], "Standard log message")
        self.assertEqual(parsed["metadata"]["logger_name"], "test_logger")
        self.assertEqual(parsed["metadata"]["module"], "test_module")


class TestStructuredLogger(TestCase):
    """Test cases for structured logger functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_creation(self):
        """Test structured logger creation."""
        logger = StructuredLogger(
            name="test_logger",
            log_dir=str(self.log_dir),
            enable_console=False
        )
        
        self.assertEqual(logger.name, "test_logger")
        self.assertTrue(self.log_dir.exists())
        
        # Clean up
        logger.close()
    
    def test_session_context(self):
        """Test session context setting."""
        logger = StructuredLogger(
            name="test_logger",
            log_dir=str(self.log_dir),
            enable_console=False
        )
        
        # Set session context
        logger.set_session_context("session_123", "correlation_456")
        
        self.assertEqual(logger.session_id, "session_123")
        self.assertEqual(logger.correlation_id, "correlation_456")
        
        # Clean up
        logger.close()
    
    def test_agent_logging(self):
        """Test agent lifecycle logging."""
        logger = StructuredLogger(
            name="test_logger",
            log_dir=str(self.log_dir),
            enable_console=False
        )
        
        # Log agent start
        logger.log_agent_start(
            agent_id="test_agent",
            agent_type="developer",
            framework="langgraph",
            capabilities=["coding", "testing"]
        )
        
        # Log agent stop
        logger.log_agent_stop(
            agent_id="test_agent",
            framework="langgraph",
            duration_ms=5000.0
        )
        
        # Flush and check log file
        logger.flush()
        
        log_file = self.log_dir / "test_logger.jsonl"
        self.assertTrue(log_file.exists())
        
        # Read and verify log entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        
        # Parse first line (agent start)
        start_event = json.loads(lines[0])
        self.assertEqual(start_event["event_type"], "agent.start")
        self.assertEqual(start_event["agent_id"], "test_agent")
        
        # Parse second line (agent stop)
        stop_event = json.loads(lines[1])
        self.assertEqual(stop_event["event_type"], "agent.stop")
        self.assertEqual(stop_event["agent_id"], "test_agent")
        
        # Clean up
        logger.close()
    
    def test_task_logging(self):
        """Test task execution logging."""
        logger = StructuredLogger(
            name="test_logger",
            log_dir=str(self.log_dir),
            enable_console=False
        )
        
        # Log task start
        logger.log_task_start(
            task_id="task_123",
            task_name="generate_code",
            agent_id="test_agent",
            framework="crewai",
            task_input={"prompt": "Create a function"}
        )
        
        # Log task completion
        logger.log_task_complete(
            task_id="task_123",
            task_name="generate_code",
            agent_id="test_agent",
            framework="crewai",
            duration_ms=2500.0,
            task_output={"code": "def test(): pass"}
        )
        
        # Log task error
        logger.log_task_error(
            task_id="task_456",
            task_name="broken_task",
            agent_id="test_agent",
            framework="crewai",
            error="Syntax error in generated code",
            duration_ms=1000.0
        )
        
        # Flush and verify
        logger.flush()
        
        log_file = self.log_dir / "test_logger.jsonl"
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 3)
        
        # Verify task events
        start_event = json.loads(lines[0])
        complete_event = json.loads(lines[1])
        error_event = json.loads(lines[2])
        
        self.assertEqual(start_event["event_type"], "task.start")
        self.assertEqual(complete_event["event_type"], "task.complete")
        self.assertEqual(error_event["event_type"], "task.fail")
        
        self.assertTrue(complete_event["success"])
        self.assertFalse(error_event["success"])
        
        # Clean up
        logger.close()
    
    def test_safety_logging(self):
        """Test safety violation logging."""
        logger = StructuredLogger(
            name="test_logger",
            log_dir=str(self.log_dir),
            enable_console=False
        )
        
        # Log safety violation
        logger.log_safety_violation(
            policy_name="file_access_policy",
            violation_type="unauthorized_read",
            risk_level="high",
            action_taken="blocked",
            agent_id="malicious_agent",
            blocked_content="/etc/passwd"
        )
        
        # Flush and verify
        logger.flush()
        
        log_file = self.log_dir / "test_logger.jsonl"
        with open(log_file, 'r') as f:
            content = f.read()
        
        safety_event = json.loads(content.strip())
        self.assertEqual(safety_event["event_type"], "safety.violation")
        self.assertEqual(safety_event["policy_name"], "file_access_policy")
        self.assertEqual(safety_event["risk_level"], "high")
        self.assertEqual(safety_event["level"], "WARNING")
        
        # Clean up
        logger.close()
    
    def test_llm_interaction_logging(self):
        """Test LLM interaction logging."""
        logger = StructuredLogger(
            name="test_logger",
            log_dir=str(self.log_dir),
            enable_console=False
        )
        
        # Log LLM interaction
        logger.log_llm_interaction(
            model_name="llama3.1:8b",
            provider="ollama",
            prompt_tokens=100,
            completion_tokens=50,
            duration_ms=1500.0,
            cost_usd=0.0,
            agent_id="test_agent"
        )
        
        # Flush and verify
        logger.flush()
        
        log_file = self.log_dir / "test_logger.jsonl"
        with open(log_file, 'r') as f:
            content = f.read()
        
        llm_event = json.loads(content.strip())
        self.assertEqual(llm_event["event_type"], "llm.response")
        self.assertEqual(llm_event["model_name"], "llama3.1:8b")
        self.assertEqual(llm_event["total_tokens"], 150)
        self.assertEqual(llm_event["cost_usd"], 0.0)
        
        # Clean up
        logger.close()
    
    def test_filtering_integration(self):
        """Test logger with event filtering."""
        logger = StructuredLogger(
            name="test_logger",
            log_dir=str(self.log_dir),
            enable_console=False
        )
        
        # Set filter to only allow ERROR level and above
        logger.get_filter().set_level_filter(LogLevel.ERROR)
        
        # Log events at different levels
        logger.log_agent_start(
            agent_id="test_agent",
            agent_type="developer",
            framework="langgraph"
        )  # INFO level - should be filtered out
        
        logger.log_task_error(
            task_id="task_123",
            task_name="broken_task",
            agent_id="test_agent",
            framework="langgraph",
            error="Critical error"
        )  # ERROR level - should be logged
        
        # Give time for background processing
        time.sleep(0.2)
        logger.flush()
        
        log_file = self.log_dir / "test_logger.jsonl"
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Should only have the error event
            self.assertEqual(len(lines), 1)
            
            error_event = json.loads(lines[0])
            self.assertEqual(error_event["event_type"], "task.fail")
            self.assertEqual(error_event["level"], "ERROR")
        
        # Clean up
        logger.close()


class TestGlobalLogger(TestCase):
    """Test cases for global logger functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset global logger
        import common.telemetry.logger
        common.telemetry.logger._global_logger = None
    
    def test_get_logger_singleton(self):
        """Test global logger singleton behavior."""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")
        
        # Should return the same instance
        self.assertIs(logger1, logger2)
        
        # Clean up
        logger1.close()
    
    def test_configure_logging(self):
        """Test global logging configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = configure_logging(
                log_dir=temp_dir,
                level=LogLevel.WARNING,
                enable_console=False
            )
            
            self.assertIsInstance(logger, StructuredLogger)
            self.assertEqual(logger.get_filter().level_filter, LogLevel.WARNING)
            
            # Clean up
            logger.close()