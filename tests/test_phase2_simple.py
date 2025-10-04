"""Simple smoke tests for Phase 2 core components.

This module provides basic smoke tests to verify that the core Phase 2 components
are working correctly together.
"""

import pytest
from common.phase2.enums import MismatchType, SafetyLevel, ResolutionActionType
from common.phase2.models import create_mismatch, create_simple_resolution_plan
from common.phase2.config import create_default_config, Environment


def test_basic_mismatch_workflow():
    """Test basic mismatch detection and resolution workflow."""
    # Create a mismatch
    mismatch = create_mismatch(
        run_id="test_run_001",
        artifact_ids=["artifact_001"],
        mismatch_type=MismatchType.WHITESPACE,
        detectors=["whitespace_detector"],
        diff_id="diff_001",
        confidence_score=0.95
    )
    
    # Verify mismatch properties
    assert mismatch.id.startswith("mis_")
    assert mismatch.type == "whitespace"  # String after Pydantic processing
    assert mismatch.is_resolvable()
    
    # Create resolution plan
    plan = create_simple_resolution_plan(
        mismatch_id=mismatch.id,
        action_type=ResolutionActionType.NORMALIZE_WHITESPACE,
        target_artifact_id="artifact_001",
        safety_level=SafetyLevel.AUTOMATIC
    )
    
    # Verify plan properties
    assert plan.id.startswith("plan_")
    assert plan.mismatch_id == mismatch.id
    assert plan.has_required_approvals()  # Automatic safety level
    assert len(plan.actions) == 1
    assert plan.actions[0].type == "normalize_whitespace"


def test_configuration_integration():
    """Test configuration system integration."""
    # Create default configuration
    config = create_default_config(Environment.DEVELOPMENT)
    
    # Test AI service configuration
    ai_service = config.get_ai_service("ollama")
    assert ai_service is not None
    assert ai_service.enabled
    
    # Test resolution policy lookup
    policy = config.get_resolution_policy(MismatchType.WHITESPACE)
    assert policy is not None
    assert policy.safety_level == SafetyLevel.AUTOMATIC
    assert ResolutionActionType.NORMALIZE_WHITESPACE in policy.allowed_actions
    
    # Test action permission check
    allowed = config.is_action_allowed(
        MismatchType.WHITESPACE, 
        ResolutionActionType.NORMALIZE_WHITESPACE
    )
    assert allowed


def test_enum_consistency():
    """Test that enums are consistent and provide expected functionality."""
    # Test mismatch type classification
    safe_types = MismatchType.safe_for_auto_resolve()
    assert MismatchType.WHITESPACE in safe_types
    assert MismatchType.JSON_ORDERING in safe_types
    assert MismatchType.SEMANTICS_TEXT not in safe_types
    
    # Test safety level behavior
    assert SafetyLevel.AUTOMATIC.allows_auto_apply()
    assert not SafetyLevel.ADVISORY.allows_auto_apply()
    assert SafetyLevel.EXPERIMENTAL.requires_approval()
    
    # Test resolution action safety
    assert ResolutionActionType.REPLACE_ARTIFACT.is_destructive()
    assert not ResolutionActionType.NORMALIZE_WHITESPACE.is_destructive()


def test_model_serialization():
    """Test model serialization and deserialization."""
    # Create a mismatch
    mismatch = create_mismatch(
        run_id="test_run_002",
        artifact_ids=["artifact_002"],
        mismatch_type=MismatchType.JSON_ORDERING,
        detectors=["json_detector"],
        diff_id="diff_002",
        confidence_score=0.88
    )
    
    # Test serialization
    mismatch_dict = mismatch.to_dict()
    assert mismatch_dict['type'] == 'json_ordering'
    assert mismatch_dict['confidence_score'] == 0.88
    
    mismatch_json = mismatch.to_json()
    assert 'json_ordering' in mismatch_json
    assert 'test_run_002' in mismatch_json
    
    # Test deserialization
    mismatch_copy = mismatch.from_dict(mismatch_dict)
    assert mismatch_copy.id == mismatch.id
    assert mismatch_copy.run_id == mismatch.run_id
    assert mismatch_copy.confidence_score == mismatch.confidence_score


if __name__ == "__main__":
    print("🧪 Running Phase 2 simple smoke tests...")
    
    tests = [
        (test_basic_mismatch_workflow, "Basic mismatch workflow"),
        (test_configuration_integration, "Configuration integration"),
        (test_enum_consistency, "Enum consistency"),
        (test_model_serialization, "Model serialization"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, description in tests:
        try:
            test_func()
            print(f"✅ {description}")
            passed += 1
        except Exception as e:
            print(f"❌ {description}: {e}")
            failed += 1
    
    print(f"\\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Phase 2 simple smoke tests passed!")
    else:
        print("❌ Some tests failed.")
        exit(1)