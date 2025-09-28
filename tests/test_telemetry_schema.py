"""
Tests for telemetry event schema.

This module tests the structured event dataclasses and event creation
functionality for consistency and correctness.
"""

import json
import uuid
from datetime import datetime
from unittest import TestCase

from common.telemetry.schema import (
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


class TestEventSchema(TestCase):
    """Test cases for event schema classes."""
    
    def test_base_event_creation(self):
        """Test basic event creation and serialization."""
        event = BaseEvent(
            event_type=EventType.SYSTEM_START,
            level=LogLevel.INFO,
            message="System starting up",
            framework="test_framework",
            agent_id="test_agent",
            metadata={"version": "1.0.0"}
        )
        
        # Check basic properties
        self.assertEqual(event.event_type, EventType.SYSTEM_START)
        self.assertEqual(event.level, LogLevel.INFO)
        self.assertEqual(event.message, "System starting up")
        self.assertEqual(event.framework, "test_framework")
        self.assertEqual(event.agent_id, "test_agent")
        self.assertEqual(event.metadata["version"], "1.0.0")
        
        # Check auto-generated fields
        self.assertIsNotNone(event.event_id)
        self.assertIsInstance(event.timestamp, datetime)
        
        # Test serialization
        event_dict = event.to_dict()
        self.assertIsInstance(event_dict, dict)
        self.assertEqual(event_dict["event_type"], "system.start")
        self.assertEqual(event_dict["level"], "INFO")
        self.assertEqual(event_dict["message"], "System starting up")
        
        # Ensure JSON serializable
        json_str = json.dumps(event_dict)
        self.assertIsInstance(json_str, str)
    
    def test_agent_event_creation(self):
        """Test agent event creation with specific fields."""
        event = AgentEvent(
            event_type=EventType.AGENT_START,
            agent_id="test_agent",
            agent_type="developer",
            framework="langgraph",
            capabilities=["code_generation", "testing"],
            agent_config={"temperature": 0.7, "max_tokens": 1000}
        )
        
        # Check agent-specific fields
        self.assertEqual(event.agent_type, "developer")
        self.assertEqual(event.capabilities, ["code_generation", "testing"])
        self.assertEqual(event.agent_config["temperature"], 0.7)
        
        # Test serialization includes agent fields
        event_dict = event.to_dict()
        self.assertEqual(event_dict["agent_type"], "developer")
        self.assertEqual(event_dict["capabilities"], ["code_generation", "testing"])
        self.assertEqual(event_dict["agent_config"]["temperature"], 0.7)
    
    def test_task_event_creation(self):
        """Test task event creation and tracking."""
        event = TaskEvent(
            event_type=EventType.TASK_COMPLETE,
            task_id="task_123",
            task_name="generate_code",
            task_description="Generate Python function",
            task_input={"prompt": "Create a hello world function"},
            task_output={"code": "def hello(): print('Hello, World!')"},
            duration_ms=1500.5,
            success=True
        )
        
        # Check task-specific fields
        self.assertEqual(event.task_id, "task_123")
        self.assertEqual(event.task_name, "generate_code")
        self.assertEqual(event.duration_ms, 1500.5)
        self.assertTrue(event.success)
        
        # Test serialization
        event_dict = event.to_dict()
        self.assertEqual(event_dict["task_name"], "generate_code")
        self.assertEqual(event_dict["duration_ms"], 1500.5)
        self.assertTrue(event_dict["success"])
    
    def test_tool_event_creation(self):
        """Test tool event creation and usage tracking."""
        event = ToolEvent(
            event_type=EventType.TOOL_CALL,
            tool_name="file_writer",
            tool_input={"filename": "test.py", "content": "print('test')"},
            tool_output={"success": True, "bytes_written": 15},
            duration_ms=250.0,
            success=True
        )
        
        # Check tool-specific fields
        self.assertEqual(event.tool_name, "file_writer")
        self.assertEqual(event.tool_input["filename"], "test.py")
        self.assertEqual(event.tool_output["bytes_written"], 15)
        
        # Test serialization
        event_dict = event.to_dict()
        self.assertEqual(event_dict["tool_name"], "file_writer")
        self.assertEqual(event_dict["tool_input"]["filename"], "test.py")
    
    def test_safety_event_creation(self):
        """Test safety event creation for security tracking."""
        event = SafetyEvent(
            event_type=EventType.SAFETY_VIOLATION,
            policy_name="code_execution_policy",
            violation_type="unauthorized_file_access",
            risk_level="medium",
            action_taken="blocked",
            blocked_content="/etc/passwd"
        )
        
        # Check safety-specific fields
        self.assertEqual(event.policy_name, "code_execution_policy")
        self.assertEqual(event.violation_type, "unauthorized_file_access")
        self.assertEqual(event.risk_level, "medium")
        self.assertEqual(event.action_taken, "blocked")
        
        # Test serialization
        event_dict = event.to_dict()
        self.assertEqual(event_dict["policy_name"], "code_execution_policy")
        self.assertEqual(event_dict["violation_type"], "unauthorized_file_access")
    
    def test_vcs_event_creation(self):
        """Test VCS event creation for version control tracking."""
        event = VCSEvent(
            event_type=EventType.VCS_COMMIT,
            repository="ai-dev-squad",
            branch="feature/telemetry",
            commit_hash="abc123def456",
            operation="commit",
            files_changed=["common/telemetry/schema.py", "tests/test_schema.py"],
            pr_number=42
        )
        
        # Check VCS-specific fields
        self.assertEqual(event.repository, "ai-dev-squad")
        self.assertEqual(event.branch, "feature/telemetry")
        self.assertEqual(event.commit_hash, "abc123def456")
        self.assertEqual(len(event.files_changed), 2)
        self.assertEqual(event.pr_number, 42)
        
        # Test serialization
        event_dict = event.to_dict()
        self.assertEqual(event_dict["repository"], "ai-dev-squad")
        self.assertEqual(len(event_dict["files_changed"]), 2)
    
    def test_llm_event_creation(self):
        """Test LLM event creation for model interaction tracking."""
        event = LLMEvent(
            event_type=EventType.LLM_RESPONSE,
            model_name="llama3.1:8b",
            provider="ollama",
            prompt_tokens=150,
            completion_tokens=75,
            total_tokens=225,
            cost_usd=0.0,  # Local model
            duration_ms=2500.0,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Check LLM-specific fields
        self.assertEqual(event.model_name, "llama3.1:8b")
        self.assertEqual(event.provider, "ollama")
        self.assertEqual(event.prompt_tokens, 150)
        self.assertEqual(event.completion_tokens, 75)
        self.assertEqual(event.total_tokens, 225)
        self.assertEqual(event.cost_usd, 0.0)
        
        # Test serialization
        event_dict = event.to_dict()
        self.assertEqual(event_dict["model_name"], "llama3.1:8b")
        self.assertEqual(event_dict["total_tokens"], 225)
    
    def test_performance_event_creation(self):
        """Test performance event creation for metrics tracking."""
        event = PerformanceEvent(
            event_type=EventType.PERFORMANCE_METRIC,
            metric_name="task_completion_time",
            metric_value=1.5,
            metric_unit="seconds",
            cpu_percent=45.2,
            memory_mb=512.0,
            disk_io_mb=10.5,
            network_io_mb=2.1
        )
        
        # Check performance-specific fields
        self.assertEqual(event.metric_name, "task_completion_time")
        self.assertEqual(event.metric_value, 1.5)
        self.assertEqual(event.metric_unit, "seconds")
        self.assertEqual(event.cpu_percent, 45.2)
        
        # Test serialization
        event_dict = event.to_dict()
        self.assertEqual(event_dict["metric_name"], "task_completion_time")
        self.assertEqual(event_dict["cpu_percent"], 45.2)
    
    def test_framework_event_creation(self):
        """Test framework event creation for framework-specific tracking."""
        event = FrameworkEvent(
            event_type=EventType.FRAMEWORK_EVENT,
            framework="langgraph",
            framework_version="0.2.0",
            operation="state_transition",
            component="graph_executor",
            state_data={"current_node": "code_generator", "next_node": "code_reviewer"}
        )
        
        # Check framework-specific fields
        self.assertEqual(event.framework_version, "0.2.0")
        self.assertEqual(event.operation, "state_transition")
        self.assertEqual(event.component, "graph_executor")
        self.assertEqual(event.state_data["current_node"], "code_generator")
        
        # Test serialization
        event_dict = event.to_dict()
        self.assertEqual(event_dict["framework_version"], "0.2.0")
        self.assertEqual(event_dict["state_data"]["current_node"], "code_generator")
    
    def test_create_event_factory(self):
        """Test event factory function for creating appropriate event types."""
        
        # Test agent event creation
        agent_event = create_event(
            EventType.AGENT_START,
            agent_id="test_agent",
            agent_type="developer",
            framework="crewai"
        )
        self.assertIsInstance(agent_event, AgentEvent)
        self.assertEqual(agent_event.event_type, EventType.AGENT_START)
        self.assertEqual(agent_event.agent_id, "test_agent")
        
        # Test task event creation
        task_event = create_event(
            EventType.TASK_COMPLETE,
            task_id="task_456",
            task_name="code_review",
            success=True
        )
        self.assertIsInstance(task_event, TaskEvent)
        self.assertEqual(task_event.event_type, EventType.TASK_COMPLETE)
        self.assertEqual(task_event.task_id, "task_456")
        
        # Test safety event creation
        safety_event = create_event(
            EventType.SAFETY_VIOLATION,
            policy_name="test_policy",
            violation_type="test_violation"
        )
        self.assertIsInstance(safety_event, SafetyEvent)
        self.assertEqual(safety_event.event_type, EventType.SAFETY_VIOLATION)
        
        # Test fallback to BaseEvent for unknown types
        system_event = create_event(
            EventType.SYSTEM_START,
            message="System starting"
        )
        self.assertIsInstance(system_event, BaseEvent)
        self.assertEqual(system_event.event_type, EventType.SYSTEM_START)
    
    def test_event_type_enum_values(self):
        """Test that event type enum values are properly formatted."""
        
        # Test agent events
        self.assertEqual(EventType.AGENT_START.value, "agent.start")
        self.assertEqual(EventType.AGENT_STOP.value, "agent.stop")
        self.assertEqual(EventType.AGENT_ERROR.value, "agent.error")
        
        # Test task events
        self.assertEqual(EventType.TASK_START.value, "task.start")
        self.assertEqual(EventType.TASK_COMPLETE.value, "task.complete")
        self.assertEqual(EventType.TASK_FAIL.value, "task.fail")
        
        # Test tool events
        self.assertEqual(EventType.TOOL_CALL.value, "tool.call")
        self.assertEqual(EventType.TOOL_RESULT.value, "tool.result")
        
        # Test safety events
        self.assertEqual(EventType.SAFETY_VIOLATION.value, "safety.violation")
        self.assertEqual(EventType.INJECTION_DETECTED.value, "injection.detected")
        
        # Test VCS events
        self.assertEqual(EventType.VCS_COMMIT.value, "vcs.commit")
        self.assertEqual(EventType.VCS_PR_CREATE.value, "vcs.pr.create")
        
        # Test LLM events
        self.assertEqual(EventType.LLM_REQUEST.value, "llm.request")
        self.assertEqual(EventType.LLM_RESPONSE.value, "llm.response")
    
    def test_log_level_enum_values(self):
        """Test that log level enum values match standard logging levels."""
        
        self.assertEqual(LogLevel.DEBUG.value, "DEBUG")
        self.assertEqual(LogLevel.INFO.value, "INFO")
        self.assertEqual(LogLevel.WARNING.value, "WARNING")
        self.assertEqual(LogLevel.ERROR.value, "ERROR")
        self.assertEqual(LogLevel.CRITICAL.value, "CRITICAL")
    
    def test_event_id_uniqueness(self):
        """Test that event IDs are unique across multiple events."""
        
        events = [BaseEvent() for _ in range(100)]
        event_ids = [event.event_id for event in events]
        
        # Check all IDs are unique
        self.assertEqual(len(event_ids), len(set(event_ids)))
        
        # Check all IDs are valid UUIDs
        for event_id in event_ids:
            uuid.UUID(event_id)  # Will raise ValueError if invalid
    
    def test_timestamp_consistency(self):
        """Test that timestamps are properly generated and formatted."""
        
        event = BaseEvent()
        
        # Check timestamp is datetime object
        self.assertIsInstance(event.timestamp, datetime)
        
        # Check serialization produces ISO format
        event_dict = event.to_dict()
        timestamp_str = event_dict["timestamp"]
        
        # Should be able to parse back to datetime
        parsed_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        self.assertIsInstance(parsed_timestamp, datetime)