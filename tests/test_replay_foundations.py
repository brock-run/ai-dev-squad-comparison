"""
Unit Tests for Record-Replay Foundation Components

Tests the critical foundation components implemented in Phase 0:
- Canonical input hashing
- Event ordering and concurrency
- Deterministic time and randomness
- Redaction and retention
- Security policy integration
"""

import json
import pytest
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

from common.replay import (
    # Canonicalization
    CanonicalHasher,
    IOKey,
    create_io_key,
    hash_prompt,
    hash_tool_call,
    
    # Ordering
    OrderedEvent,
    EventOrderingManager,
    create_ordered_event,
    step_context,
    
    # Determinism
    SystemClockProvider,
    SystemRngProvider,
    FrozenClockProvider,
    RecordingClockProvider,
    RecordingRngProvider,
    ReplayRngProvider,
    DeterminismManager,
    deterministic_context,
    
    # Redaction
    RedactionLevel,
    RedactionFilter,
    RetentionManager,
    RetentionClass,
    
    # Policy Integration
    ReplayMode,
    ReplaySecurityPolicy,
    ReplayPolicyManager,
    replay_security_context
)


class TestCanonicalHashing:
    """Test canonical input hashing functionality."""
    
    def test_consistent_hashing_across_platforms(self):
        """Test that hashing is consistent across different conditions."""
        hasher = CanonicalHasher()
        
        # Same data should produce same hash
        data1 = {"prompt": "Hello world", "temperature": 0.7, "max_tokens": 100}
        data2 = {"max_tokens": 100, "prompt": "Hello world", "temperature": 0.7}  # Different order
        
        hash1 = hasher.hash_input(data1)
        hash2 = hasher.hash_input(data2)
        
        assert hash1 == hash2, "Hash should be consistent regardless of key order"
    
    def test_string_normalization(self):
        """Test string normalization for consistent hashing."""
        hasher = CanonicalHasher()
        
        # Different whitespace should normalize to same hash
        text1 = "Hello    world\r\n\r\nHow are you?"
        text2 = "Hello world\n\nHow are you?"
        
        hash1 = hasher.hash_input(text1)
        hash2 = hasher.hash_input(text2)
        
        assert hash1 == hash2, "Normalized strings should have same hash"
    
    def test_float_precision_consistency(self):
        """Test that float precision is consistent."""
        hasher = CanonicalHasher()
        
        data1 = {"temperature": 0.7000001}
        data2 = {"temperature": 0.7000002}  # Within precision tolerance
        
        hash1 = hasher.hash_input(data1)
        hash2 = hasher.hash_input(data2)
        
        assert hash1 == hash2, "Floats within precision tolerance should have same hash"
    
    def test_io_key_creation(self):
        """Test IO key creation and uniqueness."""
        key1 = create_io_key(
            event_type="llm_call",
            adapter="langgraph",
            agent_id="agent_1",
            tool_name="openai",
            call_index=0,
            input_data={"prompt": "Hello"}
        )
        
        key2 = create_io_key(
            event_type="llm_call",
            adapter="langgraph",
            agent_id="agent_1",
            tool_name="openai",
            call_index=1,  # Different call index
            input_data={"prompt": "Hello"}
        )
        
        assert key1 != key2, "Different call indices should produce different keys"
        assert key1.input_fingerprint == key2.input_fingerprint, "Same input should have same fingerprint"
    
    def test_hash_collision_resistance(self):
        """Test that similar inputs produce different hashes."""
        hasher = CanonicalHasher()
        
        # Very similar but different inputs
        data1 = {"prompt": "Write a function to calculate fibonacci"}
        data2 = {"prompt": "Write a function to calculate fibonacci."}  # Added period
        
        hash1 = hasher.hash_input(data1)
        hash2 = hasher.hash_input(data2)
        
        assert hash1 != hash2, "Similar but different inputs should have different hashes"


class TestEventOrdering:
    """Test event ordering and concurrency control."""
    
    def test_ordered_event_creation(self):
        """Test creation of ordered events."""
        manager = EventOrderingManager()
        
        event = manager.create_ordered_event(
            event_type="llm_call",
            agent_id="agent_1",
            tool_name="openai",
            data={"prompt": "Hello"}
        )
        
        assert event.step == 1, "First event should have step 1"
        assert event.agent_id == "agent_1"
        assert event.call_index == 0, "First call should have index 0"
    
    def test_call_index_increment(self):
        """Test that call indices increment correctly."""
        manager = EventOrderingManager()
        
        event1 = manager.create_ordered_event("llm_call", "agent_1", "openai")
        event2 = manager.create_ordered_event("llm_call", "agent_1", "openai")
        event3 = manager.create_ordered_event("llm_call", "agent_1", "anthropic")  # Different tool
        
        assert event1.call_index == 0
        assert event2.call_index == 1
        assert event3.call_index == 0, "Different tool should start at 0"
    
    def test_step_context_tracking(self):
        """Test parent-child step tracking."""
        manager = EventOrderingManager()
        
        parent_event = manager.create_ordered_event("task_start", "agent_1")
        
        with step_context(parent_event.step):
            child_event = manager.create_ordered_event("llm_call", "agent_1")
            assert child_event.parent_step == parent_event.step
    
    def test_concurrent_event_creation(self):
        """Test thread safety of event creation."""
        manager = EventOrderingManager()
        manager.start_writer()
        
        events = []
        errors = []
        
        def create_events(agent_id: str, count: int):
            try:
                for i in range(count):
                    event = manager.create_ordered_event(
                        "llm_call", 
                        agent_id, 
                        "openai",
                        data={"index": i}
                    )
                    events.append(event)
            except Exception as e:
                errors.append(e)
        
        # Create events from multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_events, args=[f"agent_{i}", 5])
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        manager.stop_writer()
        
        assert len(errors) == 0, f"No errors should occur: {errors}"
        assert len(events) == 15, "Should have 15 events total"
        
        # Check that steps are unique and ordered
        steps = [event.step for event in events]
        assert len(set(steps)) == len(steps), "All steps should be unique"


class TestDeterministicProviders:
    """Test deterministic time and randomness providers."""
    
    def test_frozen_clock_provider(self):
        """Test frozen clock provider."""
        frozen_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        clock = FrozenClockProvider(frozen_time)
        
        # Multiple calls should return same time
        time1 = clock.now()
        time.sleep(0.01)  # Small delay
        time2 = clock.now()
        
        assert time1 == time2 == frozen_time
    
    def test_recording_clock_provider(self):
        """Test recording clock provider."""
        clock = RecordingClockProvider()
        
        time1 = clock.now()
        time.sleep(0.01)
        time2 = clock.now()
        
        recorded_times = clock.get_recorded_times()
        assert len(recorded_times) == 2
        assert recorded_times[0] < recorded_times[1]
    
    def test_system_rng_determinism(self):
        """Test that seeded RNG is deterministic."""
        rng1 = SystemRngProvider(seed_value=42)
        rng2 = SystemRngProvider(seed_value=42)
        
        # Same seed should produce same sequence
        values1 = [rng1.random() for _ in range(10)]
        values2 = [rng2.random() for _ in range(10)]
        
        assert values1 == values2, "Same seed should produce same random sequence"
    
    def test_recording_rng_provider(self):
        """Test recording RNG provider."""
        rng = RecordingRngProvider(seed_value=42)
        
        # Generate some values
        float_val = rng.random()
        int_val = rng.randint(1, 10)
        uuid_val = rng.uuid4()
        
        recorded = rng.get_recorded_values()
        
        assert len(recorded['random']) == 1
        assert len(recorded['randint']) == 1
        assert len(recorded['uuid4']) == 1
        assert recorded['random'][0] == float_val
        assert recorded['randint'][0][2] == int_val  # Third element is the value
        assert recorded['uuid4'][0] == uuid_val
    
    def test_replay_rng_provider(self):
        """Test replay RNG provider."""
        # First record some values
        recording_rng = RecordingRngProvider(seed_value=42)
        original_values = {
            'random': [recording_rng.random() for _ in range(3)],
            'randint': [(1, 10, recording_rng.randint(1, 10)) for _ in range(2)],
            'uuid4': [recording_rng.uuid4() for _ in range(2)]
        }
        
        # Now replay them
        replay_rng = ReplayRngProvider(original_values)
        
        # Should get same values back
        for i in range(3):
            assert replay_rng.random() == original_values['random'][i]
        
        for i in range(2):
            a, b, expected = original_values['randint'][i]
            assert replay_rng.randint(a, b) == expected
        
        for i in range(2):
            assert replay_rng.uuid4() == original_values['uuid4'][i]
    
    def test_deterministic_context(self):
        """Test deterministic context manager."""
        with deterministic_context("recording", seed=42):
            manager = DeterminismManager()
            assert manager.get_mode() == "recording"
            
            # Should be able to get recorded data
            rng = manager.get_rng()
            rng.random()  # Generate a value
            
            recorded_data = manager.get_recorded_data()
            assert 'random_values' in recorded_data


class TestRedactionSystem:
    """Test redaction and retention functionality."""
    
    def test_basic_redaction_rules(self):
        """Test basic redaction patterns."""
        filter = RedactionFilter(RedactionLevel.BASIC)
        
        # Test GitHub token redaction
        text_with_token = "Authorization: ghp_1234567890abcdef1234567890abcdef12345678"
        redacted = filter.redact_text(text_with_token)
        
        assert "ghp_" not in redacted
        assert "[REDACTED]" in redacted
    
    def test_dict_redaction(self):
        """Test dictionary redaction."""
        filter = RedactionFilter(RedactionLevel.STANDARD)
        
        data = {
            "config": {
                "api_key": "secret_key_12345",
                "user": "john.doe@example.com",
                "safe_value": "this is fine"
            }
        }
        
        redacted = filter.redact_dict(data)
        
        assert "secret_key_12345" not in str(redacted)
        assert "john.doe@example.com" not in str(redacted)
        assert redacted["config"]["safe_value"] == "this is fine"
    
    def test_json_redaction(self):
        """Test JSON string redaction."""
        filter = RedactionFilter(RedactionLevel.STANDARD)
        
        json_str = json.dumps({
            "authorization": "Bearer abc123def456",
            "data": "normal data"
        })
        
        redacted = filter.redact_json(json_str)
        redacted_data = json.loads(redacted)
        
        assert "abc123def456" not in redacted
        assert redacted_data["data"] == "normal data"
    
    def test_retention_policy(self):
        """Test retention policy evaluation."""
        manager = RetentionManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            old_file = temp_path / "old_file.txt"
            new_file = temp_path / "new_file.txt"
            
            old_file.write_text("old content")
            new_file.write_text("new content")
            
            # Simulate old file by modifying timestamp
            old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
            old_file.touch(times=(old_time, old_time))
            
            # Test retention for development class (7 day limit)
            assert not manager.should_retain(old_file, RetentionClass.DEVELOPMENT)
            assert manager.should_retain(new_file, RetentionClass.DEVELOPMENT)


class TestSecurityPolicyIntegration:
    """Test security policy integration."""
    
    def test_replay_security_policy_creation(self):
        """Test creation of replay security policies."""
        policy = ReplaySecurityPolicy(ReplayMode.REPLAY)
        
        assert not policy.network_enabled
        assert not policy.filesystem_write_enabled
        assert len(policy.allowed_read_paths) > 0
    
    def test_file_access_checking(self):
        """Test file access policy checking."""
        policy = ReplaySecurityPolicy(ReplayMode.REPLAY)
        
        # Should allow reading from artifacts directory
        artifacts_path = Path("artifacts/test.json")
        assert policy.is_read_allowed(artifacts_path)
        
        # Should not allow writing
        assert not policy.is_write_allowed(artifacts_path)
        
        # Should not allow reading from arbitrary paths
        arbitrary_path = Path("/etc/passwd")
        assert not policy.is_read_allowed(arbitrary_path)
    
    def test_network_access_checking(self):
        """Test network access policy checking."""
        policy = ReplaySecurityPolicy(ReplayMode.REPLAY)
        
        # Should deny all network access in strict replay mode
        assert not policy.is_network_allowed("api.openai.com")
        assert not policy.is_network_allowed("github.com")
    
    def test_hybrid_mode_policy(self):
        """Test hybrid mode policy."""
        policy = ReplaySecurityPolicy(ReplayMode.HYBRID)
        
        # Should allow network access but not filesystem writes
        assert policy.network_enabled
        assert not policy.filesystem_write_enabled
    
    def test_security_context_manager(self):
        """Test security context manager."""
        with replay_security_context(
            ReplayMode.REPLAY,
            allowed_read_paths=["custom_path"],
            allowed_domains=["example.com"]
        ) as policy:
            assert policy.mode == ReplayMode.REPLAY
            assert Path("custom_path") in policy.allowed_read_paths
            assert "example.com" in policy.allowed_domains
    
    def test_policy_manager_stack(self):
        """Test policy manager stack behavior."""
        manager = ReplayPolicyManager()
        
        policy1 = ReplaySecurityPolicy(ReplayMode.LIVE)
        policy2 = ReplaySecurityPolicy(ReplayMode.REPLAY)
        
        # Apply first policy
        manager.apply_replay_policy(policy1)
        assert manager.get_current_policy() == policy1
        
        # Apply second policy (should stack)
        manager.apply_replay_policy(policy2)
        assert manager.get_current_policy() == policy2
        
        # Restore previous policy
        manager.restore_previous_policy()
        assert manager.get_current_policy() == policy1


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""
    
    def test_end_to_end_deterministic_execution(self):
        """Test complete deterministic execution scenario."""
        # Setup deterministic context
        with deterministic_context("recording", seed=42):
            # Create ordered events
            manager = EventOrderingManager()
            manager.start_writer()
            
            # Create some events with deterministic data
            event1 = manager.create_ordered_event(
                "llm_call",
                "agent_1",
                "openai",
                data={"prompt": "Hello world"}
            )
            
            # Use deterministic random values
            from common.replay import random_float, random_uuid
            random_val = random_float()
            uuid_val = random_uuid()
            
            event2 = manager.create_ordered_event(
                "tool_call",
                "agent_1",
                "calculator",
                data={"random": random_val, "uuid": uuid_val}
            )
            
            manager.stop_writer()
            
            # Verify events are properly ordered
            all_events = manager.get_all_events_ordered()
            assert len(all_events) == 2
            assert all_events[0].step < all_events[1].step
    
    def test_security_with_redaction(self):
        """Test security policy with redaction."""
        with replay_security_context(ReplayMode.REPLAY):
            # Create some data with secrets
            data = {
                "config": {
                    "github_token": "ghp_1234567890abcdef1234567890abcdef12345678",
                    "api_endpoint": "https://api.example.com"
                }
            }
            
            # Redact the data
            from common.replay import redact_dict
            redacted_data = redact_dict(data)
            
            # Verify secrets are redacted
            assert "ghp_" not in str(redacted_data)
            assert "[REDACTED]" in str(redacted_data)
            
            # Verify non-secrets are preserved
            assert "api.example.com" in str(redacted_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])