"""Tests for Phase 2 Telemetry System

This module tests the Phase 2 telemetry schema extension, logging,
and validation functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from common.phase2.telemetry import (
    Phase2EventType,
    Phase2BaseEvent,
    MismatchEvent,
    AIAnalysisEvent,
    ResolutionEvent,
    LearningEvent,
    EquivalenceEvent,
    InteractiveEvent,
    create_phase2_event,
    create_mismatch_detected_event,
    create_ai_analysis_complete_event,
    create_resolution_plan_created_event,
    create_pattern_learned_event,
    create_equivalence_check_complete_event,
    create_user_decision_event,
    PHASE2_SCHEMA_VERSION
)

from common.phase2.telemetry_logger import Phase2TelemetryLogger

from common.phase2.telemetry_validation import (
    Phase2TelemetryValidator,
    validate_event,
    validate_event_sequence,
    ValidationError
)

from common.phase2.enums import (
    MismatchType,
    MismatchStatus,
    ResolutionStatus,
    SafetyLevel,
    ResolutionActionType,
    EquivalenceMethod,
    ArtifactType
)


class TestPhase2TelemetryEvents:
    """Test Phase 2 telemetry event creation and serialization."""
    
    def test_phase2_base_event_creation(self):
        """Test Phase 2 base event creation."""
        event = Phase2BaseEvent(
            event_type=Phase2EventType.MISMATCH_DETECTED,
            mismatch_id="mis_12345678",
            confidence_score=0.95,
            cost_estimate=0.05
        )
        
        assert event.schema_version == PHASE2_SCHEMA_VERSION
        assert event.mismatch_id == "mis_12345678"
        assert event.confidence_score == 0.95
        assert event.cost_estimate == 0.05
        
        # Test serialization
        event_dict = event.to_dict()
        assert event_dict["schema_version"] == PHASE2_SCHEMA_VERSION
        assert event_dict["mismatch_id"] == "mis_12345678"
        assert event_dict["confidence_score"] == 0.95
    
    def test_mismatch_event_creation(self):
        """Test mismatch event creation."""
        event = create_mismatch_detected_event(
            mismatch_id="mis_12345678",
            mismatch_type=MismatchType.WHITESPACE,
            artifact_ids=["art_001", "art_002"],
            detectors=["whitespace_detector"],
            confidence_score=0.95,
            run_id="run_12345678"
        )
        
        assert isinstance(event, MismatchEvent)
        assert event.mismatch_id == "mis_12345678"
        assert event.mismatch_type == "whitespace"
        assert event.artifact_ids == ["art_001", "art_002"]
        assert event.detectors == ["whitespace_detector"]
        assert event.confidence_score == 0.95
        assert event.run_id == "run_12345678"
        assert event.status == "detected"
    
    def test_ai_analysis_event_creation(self):
        """Test AI analysis event creation."""
        event = create_ai_analysis_complete_event(
            mismatch_id="mis_12345678",
            analysis_type="semantic",
            result_confidence=0.88,
            latency_ms=1250.5,
            cost_estimate=0.02
        )
        
        assert isinstance(event, AIAnalysisEvent)
        assert event.mismatch_id == "mis_12345678"
        assert event.analysis_type == "semantic"
        assert event.result_confidence == 0.88
        assert event.latency_ms == 1250.5
        assert event.cost_estimate == 0.02
    
    def test_resolution_event_creation(self):
        """Test resolution event creation."""
        event = create_resolution_plan_created_event(
            mismatch_id="mis_12345678",
            resolution_plan_id="plan_87654321",
            action_count=2,
            safety_level=SafetyLevel.ADVISORY
        )
        
        assert isinstance(event, ResolutionEvent)
        assert event.mismatch_id == "mis_12345678"
        assert event.resolution_plan_id == "plan_87654321"
        assert event.action_count == 2
        assert event.safety_level == "advisory"
    
    def test_learning_event_creation(self):
        """Test learning event creation."""
        event = create_pattern_learned_event(
            pattern_id="pat_11111111",
            mismatch_type=MismatchType.JSON_ORDERING,
            pattern_signature="json_order_sig_123",
            success_rate=0.85
        )
        
        assert isinstance(event, LearningEvent)
        assert event.pattern_id == "pat_11111111"
        assert event.pattern_type == "json_ordering"
        assert event.pattern_signature == "json_order_sig_123"
        assert event.success_rate == 0.85
    
    def test_equivalence_event_creation(self):
        """Test equivalence event creation."""
        event = create_equivalence_check_complete_event(
            artifact_type=ArtifactType.TEXT,
            methods_used=[EquivalenceMethod.EXACT, EquivalenceMethod.COSINE_SIMILARITY],
            equivalent=True,
            combined_score=0.92
        )
        
        assert isinstance(event, EquivalenceEvent)
        assert event.artifact_type == "text"
        assert event.methods_used == ["exact", "cosine_similarity"]
        assert event.equivalent is True
        assert event.combined_score == 0.92
    
    def test_interactive_event_creation(self):
        """Test interactive event creation."""
        event = create_user_decision_event(
            session_type="cli",
            user_id="user123",
            user_choice="approve",
            options_presented=["approve", "reject", "modify"]
        )
        
        assert isinstance(event, InteractiveEvent)
        assert event.session_type == "cli"
        assert event.user_id == "user123"
        assert event.user_choice == "approve"
        assert event.options_presented == ["approve", "reject", "modify"]
    
    def test_event_factory_function(self):
        """Test the event factory function."""
        event = create_phase2_event(
            Phase2EventType.MISMATCH_DETECTED,
            mismatch_id="mis_12345678",
            mismatch_type="whitespace"
        )
        
        assert isinstance(event, MismatchEvent)
        assert event.mismatch_id == "mis_12345678"
        assert event.mismatch_type == "whitespace"
    
    def test_event_serialization(self):
        """Test event serialization to dictionary."""
        event = MismatchEvent(
            event_type=Phase2EventType.MISMATCH_DETECTED,
            mismatch_id="mis_12345678",
            mismatch_type="whitespace",
            artifact_ids=["art_001"],
            detectors=["detector1"],
            confidence_score=0.95
        )
        
        event_dict = event.to_dict()
        
        # Check all fields are present
        assert "schema_version" in event_dict
        assert "event_id" in event_dict
        assert "timestamp" in event_dict
        assert "mismatch_id" in event_dict
        assert "mismatch_type" in event_dict
        assert "artifact_ids" in event_dict
        assert "detectors" in event_dict
        assert "confidence_score" in event_dict
        
        # Check values
        assert event_dict["schema_version"] == PHASE2_SCHEMA_VERSION
        assert event_dict["mismatch_id"] == "mis_12345678"
        assert event_dict["mismatch_type"] == "whitespace"
        assert event_dict["confidence_score"] == 0.95


class TestPhase2TelemetryLogger:
    """Test Phase 2 telemetry logger functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_base_logger = Mock()
        self.logger = Phase2TelemetryLogger(self.mock_base_logger)
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        # Test with provided base logger
        logger = Phase2TelemetryLogger(self.mock_base_logger)
        assert logger.base_logger == self.mock_base_logger
        
        # Test with default base logger
        logger = Phase2TelemetryLogger()
        assert logger.base_logger is not None
    
    def test_log_mismatch_detected(self):
        """Test logging mismatch detection."""
        self.logger.log_mismatch_detected(
            mismatch_id="mis_12345678",
            mismatch_type=MismatchType.WHITESPACE,
            artifact_ids=["art_001"],
            detectors=["detector1"],
            confidence_score=0.95,
            run_id="run_12345678"
        )
        
        # Verify base logger was called
        self.mock_base_logger.log_event.assert_called_once()
        
        # Check the logged event data - it's the event object, not dict
        call_args = self.mock_base_logger.log_event.call_args[0][0]
        call_dict = call_args.to_dict()
        assert call_dict["mismatch_id"] == "mis_12345678"
        assert call_dict["mismatch_type"] == "whitespace"
        assert call_dict["confidence_score"] == 0.95
    
    def test_log_mismatch_status_change(self):
        """Test logging mismatch status changes."""
        self.logger.log_mismatch_status_change(
            mismatch_id="mis_12345678",
            old_status=MismatchStatus.DETECTED,
            new_status=MismatchStatus.ANALYZING
        )
        
        self.mock_base_logger.log_structured_event.assert_called_once()
        
        call_args = self.mock_base_logger.log_structured_event.call_args[0][0]
        assert call_args["mismatch_id"] == "mis_12345678"
        assert call_args["status"] == "analyzing"
    
    def test_log_ai_analysis_complete(self):
        """Test logging AI analysis completion."""
        self.logger.log_ai_analysis_complete(
            mismatch_id="mis_12345678",
            analysis_type="semantic",
            result_confidence=0.88,
            latency_ms=1250.5,
            cost_estimate=0.02
        )
        
        self.mock_base_logger.log_structured_event.assert_called_once()
        
        call_args = self.mock_base_logger.log_structured_event.call_args[0][0]
        assert call_args["mismatch_id"] == "mis_12345678"
        assert call_args["analysis_type"] == "semantic"
        assert call_args["result_confidence"] == 0.88
        assert call_args["cost_estimate"] == 0.02
    
    def test_log_resolution_plan_created(self):
        """Test logging resolution plan creation."""
        self.logger.log_resolution_plan_created(
            mismatch_id="mis_12345678",
            resolution_plan_id="plan_87654321",
            action_count=2,
            safety_level=SafetyLevel.ADVISORY
        )
        
        self.mock_base_logger.log_structured_event.assert_called_once()
        
        call_args = self.mock_base_logger.log_structured_event.call_args[0][0]
        assert call_args["mismatch_id"] == "mis_12345678"
        assert call_args["resolution_plan_id"] == "plan_87654321"
        assert call_args["action_count"] == 2
        assert call_args["safety_level"] == "advisory"
    
    def test_log_mismatch_workflow(self):
        """Test logging complete mismatch workflow."""
        self.logger.log_mismatch_workflow(
            mismatch_id="mis_12345678",
            mismatch_type=MismatchType.WHITESPACE,
            artifact_ids=["art_001"],
            detectors=["detector1"],
            confidence_score=0.95,
            run_id="run_12345678",
            analysis_results={
                "type": "semantic",
                "confidence": 0.88,
                "latency_ms": 1250.5,
                "cost": 0.02
            },
            resolution_plan_id="plan_87654321"
        )
        
        # Should have logged 3 events: detection, analysis, resolution plan
        assert self.mock_base_logger.log_structured_event.call_count == 3
    
    def test_log_event_error_handling(self):
        """Test error handling in event logging."""
        # Mock base logger to raise exception
        self.mock_base_logger.log_structured_event.side_effect = Exception("Test error")
        
        # Should not raise exception, just log error
        self.logger.log_mismatch_detected(
            mismatch_id="mis_12345678",
            mismatch_type=MismatchType.WHITESPACE,
            artifact_ids=["art_001"],
            detectors=["detector1"],
            confidence_score=0.95,
            run_id="run_12345678"
        )
        
        # Verify it tried to log
        self.mock_base_logger.log_structured_event.assert_called_once()


class TestPhase2TelemetryValidation:
    """Test Phase 2 telemetry validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = Phase2TelemetryValidator()
    
    def test_valid_mismatch_event(self):
        """Test validation of valid mismatch event."""
        event = create_mismatch_detected_event(
            mismatch_id="mis_12345678",
            mismatch_type=MismatchType.WHITESPACE,
            artifact_ids=["art_001"],
            detectors=["detector1"],
            confidence_score=0.95,
            run_id="run_12345678"
        )
        
        is_valid, errors = validate_event(event)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_mismatch_id_format(self):
        """Test validation of invalid mismatch ID format."""
        event = MismatchEvent(
            event_type=Phase2EventType.MISMATCH_DETECTED,
            mismatch_id="invalid_id",  # Should start with "mis_"
            mismatch_type="whitespace",
            artifact_ids=["art_001"],
            detectors=["detector1"]
        )
        
        is_valid, errors = validate_event(event)
        assert not is_valid
        assert any("Mismatch ID must start with 'mis_'" in error for error in errors)
    
    def test_invalid_enum_value(self):
        """Test validation of invalid enum values."""
        event = MismatchEvent(
            event_type=Phase2EventType.MISMATCH_DETECTED,
            mismatch_id="mis_12345678",
            mismatch_type="invalid_type",  # Invalid mismatch type
            artifact_ids=["art_001"],
            detectors=["detector1"]
        )
        
        is_valid, errors = validate_event(event)
        assert not is_valid
        assert any("Invalid mismatch_type" in error for error in errors)
    
    def test_missing_required_fields(self):
        """Test validation of missing required fields."""
        event = MismatchEvent(
            event_type=Phase2EventType.MISMATCH_DETECTED,
            # Missing mismatch_id, mismatch_type, artifact_ids, detectors
        )
        
        is_valid, errors = validate_event(event)
        assert not is_valid
        assert any("Missing required" in error for error in errors)
    
    def test_invalid_confidence_score(self):
        """Test validation of invalid confidence scores."""
        event = MismatchEvent(
            event_type=Phase2EventType.MISMATCH_DETECTED,
            mismatch_id="mis_12345678",
            mismatch_type="whitespace",
            artifact_ids=["art_001"],
            detectors=["detector1"],
            confidence_score=1.5  # Should be <= 1.0
        )
        
        is_valid, errors = validate_event(event)
        assert not is_valid
        assert any("confidence_score must be <= 1.0" in error for error in errors)
    
    def test_invalid_cost_estimate(self):
        """Test validation of unreasonable cost estimates."""
        event = AIAnalysisEvent(
            event_type=Phase2EventType.AI_ANALYSIS_COMPLETE,
            mismatch_id="mis_12345678",
            analysis_type="semantic",
            ai_provider="openai",
            ai_model="gpt-4",
            cost_estimate=15.0  # Too high
        )
        
        is_valid, errors = validate_event(event)
        assert not is_valid
        assert any("Cost estimate seems too high" in error for error in errors)
    
    def test_invalid_data_types(self):
        """Test validation of incorrect data types."""
        event = MismatchEvent(
            event_type=Phase2EventType.MISMATCH_DETECTED,
            mismatch_id="mis_12345678",
            mismatch_type="whitespace",
            artifact_ids="not_a_list",  # Should be list
            detectors=["detector1"],
            confidence_score="not_a_number"  # Should be float
        )
        
        is_valid, errors = validate_event(event)
        assert not is_valid
        assert any("must be a list" in error for error in errors)
        assert any("must be numeric" in error for error in errors)
    
    def test_event_sequence_validation(self):
        """Test validation of event sequences."""
        # Create a valid sequence
        events = [
            create_mismatch_detected_event(
                mismatch_id="mis_12345678",
                mismatch_type=MismatchType.WHITESPACE,
                artifact_ids=["art_001"],
                detectors=["detector1"],
                confidence_score=0.95,
                run_id="run_12345678"
            ),
            MismatchEvent(
                event_type=Phase2EventType.MISMATCH_ANALYZING,
                mismatch_id="mis_12345678",
                mismatch_type="whitespace",
                artifact_ids=["art_001"],
                detectors=["detector1"],
                status="analyzing"
            ),
            MismatchEvent(
                event_type=Phase2EventType.MISMATCH_RESOLVED,
                mismatch_id="mis_12345678",
                mismatch_type="whitespace",
                artifact_ids=["art_001"],
                detectors=["detector1"],
                status="resolved"
            )
        ]
        
        is_valid, errors = validate_event_sequence(events)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_event_sequence(self):
        """Test validation of invalid event sequences."""
        # Create sequence that starts with wrong event type
        events = [
            MismatchEvent(
                event_type=Phase2EventType.MISMATCH_RESOLVED,  # Should start with DETECTED
                mismatch_id="mis_12345678",
                mismatch_type="whitespace",
                artifact_ids=["art_001"],
                detectors=["detector1"],
                status="resolved"
            )
        ]
        
        is_valid, errors = validate_event_sequence(events)
        assert not is_valid
        assert any("should start with MISMATCH_DETECTED" in error for error in errors)
    
    def test_validate_event_dict(self):
        """Test validation of event dictionaries."""
        from common.phase2.telemetry_validation import validate_event_dict
        
        # Valid event dict
        valid_dict = {
            "schema_version": PHASE2_SCHEMA_VERSION,
            "event_id": "test-id",
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "mismatch.detected",
            "level": "INFO",
            "mismatch_id": "mis_12345678",
            "mismatch_type": "whitespace"
        }
        
        is_valid, errors = validate_event_dict(valid_dict)
        assert is_valid
        assert len(errors) == 0
        
        # Invalid event dict
        invalid_dict = {
            "schema_version": "1.0",  # Wrong version
            "mismatch_type": "invalid_type"  # Invalid enum
        }
        
        is_valid, errors = validate_event_dict(invalid_dict)
        assert not is_valid
        assert len(errors) > 0


if __name__ == "__main__":
    # Run tests directly
    import sys
    
    print("🧪 Running Phase 2 telemetry tests...")
    
    # Create test instances
    event_tests = TestPhase2TelemetryEvents()
    logger_tests = TestPhase2TelemetryLogger()
    validation_tests = TestPhase2TelemetryValidation()
    
    test_methods = [
        # Event tests
        (event_tests.test_phase2_base_event_creation, "Phase 2 base event creation"),
        (event_tests.test_mismatch_event_creation, "Mismatch event creation"),
        (event_tests.test_ai_analysis_event_creation, "AI analysis event creation"),
        (event_tests.test_resolution_event_creation, "Resolution event creation"),
        (event_tests.test_learning_event_creation, "Learning event creation"),
        (event_tests.test_equivalence_event_creation, "Equivalence event creation"),
        (event_tests.test_interactive_event_creation, "Interactive event creation"),
        (event_tests.test_event_factory_function, "Event factory function"),
        (event_tests.test_event_serialization, "Event serialization"),
        
        # Logger tests
        (logger_tests.test_logger_initialization, "Logger initialization"),
        (logger_tests.test_log_mismatch_detected, "Log mismatch detected"),
        (logger_tests.test_log_ai_analysis_complete, "Log AI analysis complete"),
        (logger_tests.test_log_resolution_plan_created, "Log resolution plan created"),
        (logger_tests.test_log_mismatch_workflow, "Log mismatch workflow"),
        
        # Validation tests
        (validation_tests.test_valid_mismatch_event, "Valid mismatch event validation"),
        (validation_tests.test_invalid_mismatch_id_format, "Invalid mismatch ID validation"),
        (validation_tests.test_invalid_enum_value, "Invalid enum value validation"),
        (validation_tests.test_missing_required_fields, "Missing required fields validation"),
        (validation_tests.test_invalid_confidence_score, "Invalid confidence score validation"),
        (validation_tests.test_event_sequence_validation, "Event sequence validation"),
        (validation_tests.test_validate_event_dict, "Event dictionary validation"),
    ]
    
    passed = 0
    failed = 0
    
    for test_method, description in test_methods:
        try:
            # Set up method if it exists
            if hasattr(test_method.__self__, 'setup_method'):
                test_method.__self__.setup_method()
            
            test_method()
            print(f"✅ {description}")
            passed += 1
        except Exception as e:
            print(f"❌ {description}: {e}")
            failed += 1
    
    print(f"\\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\\n❌ Some tests failed.")
        sys.exit(1)
    else:
        print("\\n🎉 All Phase 2 telemetry tests passed!")
        sys.exit(0)