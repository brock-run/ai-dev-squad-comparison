"""Tests for Phase 2 core components integration.

This module tests the integration between enums, models, configuration,
and persistence layers to ensure they work together correctly.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from common.phase2.enums import (
    MismatchType,
    MismatchStatus,
    ResolutionStatus,
    SafetyLevel,
    ResolutionActionType,
    EquivalenceMethod,
    ArtifactType,
    Environment
)
from common.phase2.models import (
    Mismatch,
    ResolutionPlan,
    ResolutionAction,
    Evidence,
    Provenance,
    create_mismatch,
    create_simple_resolution_plan
)
from common.phase2.config import (
    Phase2Config,
    create_default_config,
    ResolutionPolicyConfig,
    EquivalenceConfig
)


class TestEnumConsistency:
    """Test that enums are consistent and provide expected functionality."""
    
    def test_mismatch_type_safety_classification(self):
        """Test mismatch type safety classification."""
        # Safe for auto-resolution
        safe_types = MismatchType.safe_for_auto_resolve()
        assert MismatchType.WHITESPACE in safe_types
        assert MismatchType.JSON_ORDERING in safe_types
        
        # Requires human review
        review_types = MismatchType.requires_human_review()
        assert MismatchType.SEMANTICS_TEXT in review_types
        assert MismatchType.SEMANTICS_CODE in review_types
        assert MismatchType.POLICY_VIOLATION in review_types
        
        # Analysis only
        analysis_only = MismatchType.analysis_only()
        assert MismatchType.NONDETERMINISM in analysis_only
        assert MismatchType.POLICY_VIOLATION in analysis_only
        assert MismatchType.INFRA_ENV_DRIFT in analysis_only
    
    def test_mismatch_type_auto_resolution_safety(self):
        """Test safe auto-resolution classification."""
        safe_types = MismatchType.safe_for_auto_resolve()
        assert MismatchType.WHITESPACE in safe_types
        assert MismatchType.JSON_ORDERING in safe_types
        assert MismatchType.SEMANTICS_TEXT not in safe_types
        assert MismatchType.POLICY_VIOLATION not in safe_types
    
    def test_resolution_action_safety(self):
        """Test resolution action safety classification."""
        # Destructive actions
        assert ResolutionActionType.REPLACE_ARTIFACT.is_destructive()
        assert ResolutionActionType.REWRITE_FORMATTING.is_destructive()
        assert ResolutionActionType.APPLY_TRANSFORM.is_destructive()
        
        # Non-destructive actions
        assert not ResolutionActionType.NORMALIZE_WHITESPACE.is_destructive()
        assert not ResolutionActionType.CANONICALIZE_JSON.is_destructive()
        assert not ResolutionActionType.IGNORE_MISMATCH.is_destructive()
    
    def test_equivalence_method_ai_requirements(self):
        """Test equivalence method AI service requirements."""
        # Methods requiring AI
        assert EquivalenceMethod.COSINE_SIMILARITY.requires_ai()
        assert EquivalenceMethod.LLM_RUBRIC_JUDGE.requires_ai()
        
        # Methods not requiring AI
        assert not EquivalenceMethod.EXACT.requires_ai()
        assert not EquivalenceMethod.AST_NORMALIZED.requires_ai()
        assert not EquivalenceMethod.CANONICAL_JSON.requires_ai()
    
    def test_safety_level_approval_requirements(self):
        """Test safety level approval requirements."""
        # Test approval requirements
        assert not SafetyLevel.AUTOMATIC.requires_approval()
        assert SafetyLevel.ADVISORY.requires_approval()
        assert SafetyLevel.EXPERIMENTAL.requires_approval()
        
        # Test auto-apply permissions
        assert SafetyLevel.AUTOMATIC.allows_auto_apply()
        assert not SafetyLevel.ADVISORY.allows_auto_apply()
        assert not SafetyLevel.EXPERIMENTAL.allows_auto_apply()


class TestModelValidation:
    """Test data model validation and business logic."""
    
    def test_mismatch_creation_and_validation(self):
        """Test mismatch creation with proper validation."""
        mismatch = create_mismatch(
            run_id="run_12345678",
            artifact_ids=["art_001", "art_002"],
            mismatch_type=MismatchType.WHITESPACE,
            detectors=["whitespace_detector"],
            diff_id="diff_001",
            confidence_score=0.95
        )
        
        # Test ID format validation
        assert mismatch.id.startswith("mis_")
        assert len(mismatch.id) == 12
        
        # Test resolvability logic
        assert mismatch.is_resolvable()  # High confidence, safe type, detected status
        
        # Test signature generation
        signature = mismatch.get_signature()
        assert len(signature) == 16
        assert isinstance(signature, str)
    
    def test_mismatch_status_transitions(self):
        """Test mismatch status update logic."""
        mismatch = create_mismatch(
            run_id="run_12345678",
            artifact_ids=["art_001"],
            mismatch_type=MismatchType.WHITESPACE,
            detectors=["detector"],
            diff_id="diff_001",
            confidence_score=0.95
        )
        
        # Test normal status update
        mismatch.update_status(MismatchStatus.ANALYZING)
        assert mismatch.status == 'analyzing'  # Pydantic converts enum to string
        assert mismatch.error_code is None
        
        # Test error status update
        mismatch.update_status(MismatchStatus.ERROR, "E001", "Test error")
        assert mismatch.status == 'error'  # Pydantic converts enum to string
        assert mismatch.error_code == "E001"
        assert mismatch.error_message == "Test error"
    
    def test_resolution_plan_creation_and_validation(self):
        """Test resolution plan creation with proper validation."""
        plan = create_simple_resolution_plan(
            mismatch_id="mis_12345678",
            action_type=ResolutionActionType.NORMALIZE_WHITESPACE,
            target_artifact_id="art_001",
            safety_level=SafetyLevel.AUTOMATIC
        )
        
        # Test ID format validation
        assert plan.id.startswith("plan_")
        assert len(plan.id) == 13
        
        # Test mismatch ID validation
        assert plan.mismatch_id == "mis_12345678"
        
        # Test approval logic
        assert plan.has_required_approvals()  # Automatic safety level
        assert plan.get_status() == ResolutionStatus.APPROVED
    
    def test_resolution_plan_approval_workflow(self):
        """Test resolution plan approval workflow."""
        plan = create_simple_resolution_plan(
            mismatch_id="mis_12345678",
            action_type=ResolutionActionType.REWRITE_FORMATTING,
            target_artifact_id="art_001",
            safety_level=SafetyLevel.ADVISORY
        )
        
        # Initially no approvals
        assert not plan.has_required_approvals()
        assert plan.get_status() == ResolutionStatus.PROPOSED
        
        # Add approval
        plan.add_approval("user1", "standard")
        assert plan.has_required_approvals()
        assert len(plan.approvals) == 1
        
        # Test dual-key requirement
        plan.safety_level = SafetyLevel.EXPERIMENTAL
        assert not plan.has_required_approvals()  # Needs 2 approvals
        
        plan.add_approval("user2", "dual_key")
        assert plan.has_required_approvals()
        assert len(plan.approvals) == 2
    
    def test_resolution_action_validation(self):
        """Test resolution action validation logic."""
        # Test safe action
        safe_action = ResolutionAction(
            type=ResolutionActionType.NORMALIZE_WHITESPACE,
            target_artifact_id="art_001",
            transformation="normalize_whitespace"
        )
        assert not safe_action.destructive
        
        # Test destructive action - should auto-set destructive flag
        destructive_action = ResolutionAction(
            type=ResolutionActionType.REPLACE_ARTIFACT,
            target_artifact_id="art_001",
            transformation="replace_artifact"
        )
        assert destructive_action.destructive  # Should be auto-set
    
    def test_model_serialization(self):
        """Test model JSON serialization and deserialization."""
        mismatch = create_mismatch(
            run_id="run_12345678",
            artifact_ids=["art_001"],
            mismatch_type=MismatchType.WHITESPACE,
            detectors=["detector"],
            diff_id="diff_001",
            confidence_score=0.95
        )
        
        # Test serialization
        mismatch_dict = mismatch.to_dict()
        assert mismatch_dict['type'] == 'whitespace'  # Enum value
        assert mismatch_dict['status'] == 'detected'
        
        mismatch_json = mismatch.to_json()
        assert isinstance(mismatch_json, str)
        assert 'whitespace' in mismatch_json
        
        # Test deserialization
        mismatch_copy = Mismatch.from_dict(mismatch_dict)
        assert mismatch_copy.id == mismatch.id
        assert mismatch_copy.type == mismatch.type
        # After deserialization, values should be strings
        assert mismatch_copy.status == 'detected'
        assert mismatch_copy.type == 'whitespace'


class TestConfigurationManagement:
    """Test configuration management functionality."""
    
    def test_default_config_creation(self):
        """Test default configuration creation for different environments."""
        # Development config
        dev_config = create_default_config(Environment.DEVELOPMENT)
        assert dev_config.environment == Environment.DEVELOPMENT
        assert dev_config.primary_ai_service == "ollama"
        assert "ollama" in dev_config.ai_services
        
        # Production config would have stricter settings
        prod_config = create_default_config(Environment.PRODUCTION)
        assert prod_config.environment == Environment.PRODUCTION
    
    def test_ai_service_configuration(self):
        """Test AI service configuration and retrieval."""
        config = create_default_config(Environment.DEVELOPMENT)
        
        # Test primary service retrieval
        primary_service = config.get_ai_service()
        assert primary_service is not None
        assert primary_service.provider.value == "ollama"
        
        # Test specific service retrieval
        ollama_service = config.get_ai_service("ollama")
        assert ollama_service is not None
        assert ollama_service.enabled
    
    def test_resolution_policy_lookup(self):
        """Test resolution policy lookup by mismatch type and environment."""
        config = create_default_config(Environment.DEVELOPMENT)
        
        # Test whitespace policy lookup
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
        
        # Test disallowed action
        not_allowed = config.is_action_allowed(
            MismatchType.WHITESPACE,
            ResolutionActionType.REPLACE_ARTIFACT
        )
        assert not not_allowed
    
    def test_equivalence_configuration(self):
        """Test equivalence configuration lookup."""
        config = create_default_config(Environment.DEVELOPMENT)
        
        # Test text artifact equivalence config
        text_config = config.get_equivalence_config(ArtifactType.TEXT)
        assert text_config is not None
        assert EquivalenceMethod.EXACT in text_config.methods
        assert EquivalenceMethod.COSINE_SIMILARITY in text_config.methods
        
        # Test JSON artifact equivalence config
        json_config = config.get_equivalence_config(ArtifactType.JSON)
        assert json_config is not None
        assert EquivalenceMethod.CANONICAL_JSON in json_config.methods
    
    def test_approval_requirements(self):
        """Test approval requirement logic."""
        config = create_default_config(Environment.DEVELOPMENT)
        
        # Safe types shouldn't require approval in dev
        requires_approval = config.requires_approval(MismatchType.WHITESPACE)
        assert not requires_approval
        
        # Semantic types should require approval
        requires_approval = config.requires_approval(MismatchType.SEMANTICS_TEXT)
        assert requires_approval


class TestIntegration:
    """Test integration between different components."""
    
    def test_mismatch_to_resolution_workflow(self):
        """Test complete workflow from mismatch detection to resolution planning."""
        # Create configuration
        config = create_default_config(Environment.DEVELOPMENT)
        
        # Create mismatch
        mismatch = create_mismatch(
            run_id="run_12345678",
            artifact_ids=["art_001"],
            mismatch_type=MismatchType.WHITESPACE,
            detectors=["whitespace_detector"],
            diff_id="diff_001",
            confidence_score=0.95
        )
        
        # Check if mismatch is resolvable
        assert mismatch.is_resolvable()
        
        # Get resolution policy
        policy = config.get_resolution_policy(mismatch.type)
        assert policy is not None
        
        # Create resolution plan based on policy
        allowed_actions = policy.allowed_actions
        assert len(allowed_actions) > 0
        
        plan = create_simple_resolution_plan(
            mismatch_id=mismatch.id,
            action_type=allowed_actions[0],
            target_artifact_id=mismatch.artifact_ids[0],
            safety_level=policy.safety_level
        )
        
        # Verify plan is properly configured
        # Handle enum/string comparison
        plan_safety = plan.safety_level if isinstance(plan.safety_level, str) else plan.safety_level.value
        policy_safety = policy.safety_level if isinstance(policy.safety_level, str) else policy.safety_level.value
        assert plan_safety == policy_safety
        assert plan.has_required_approvals()  # Should be automatic for whitespace
        assert plan.get_status() == ResolutionStatus.APPROVED
    
    def test_configuration_policy_consistency(self):
        """Test that configuration policies are consistent with enum definitions."""
        config = create_default_config(Environment.DEVELOPMENT)
        
        # Test that all configured mismatch types exist in enum
        for policy in config.resolution_policies:
            assert isinstance(policy.mismatch_type, MismatchType)
            assert isinstance(policy.safety_level, SafetyLevel)
            
            # Test that all allowed actions exist in enum
            for action in policy.allowed_actions:
                assert isinstance(action, ResolutionActionType)
        
        # Test that all equivalence configs reference valid artifact types
        for eq_config in config.equivalence_configs:
            assert isinstance(eq_config.artifact_type, ArtifactType)
            
            # Test that all methods exist in enum
            for method in eq_config.methods:
                assert isinstance(method, EquivalenceMethod)


if __name__ == "__main__":
    # Run tests directly
    import sys
    
    print("🧪 Running Phase 2 core component tests...")
    
    # Create test instances
    enum_tests = TestEnumConsistency()
    model_tests = TestModelValidation()
    config_tests = TestConfigurationManagement()
    integration_tests = TestIntegration()
    
    test_methods = [
        # Enum tests
        (enum_tests.test_mismatch_type_safety_classification, "Mismatch type safety classification"),
        (enum_tests.test_mismatch_type_auto_resolution_safety, "Auto-resolution safety"),
        (enum_tests.test_resolution_action_safety, "Resolution action safety"),
        (enum_tests.test_equivalence_method_ai_requirements, "Equivalence method AI requirements"),
        (enum_tests.test_safety_level_approval_requirements, "Safety level approval requirements"),
        
        # Model tests
        (model_tests.test_mismatch_creation_and_validation, "Mismatch creation and validation"),
        (model_tests.test_mismatch_status_transitions, "Mismatch status transitions"),
        (model_tests.test_resolution_plan_creation_and_validation, "Resolution plan creation"),
        (model_tests.test_resolution_plan_approval_workflow, "Resolution plan approval workflow"),
        (model_tests.test_resolution_action_validation, "Resolution action validation"),
        (model_tests.test_model_serialization, "Model serialization"),
        
        # Config tests
        (config_tests.test_default_config_creation, "Default config creation"),
        (config_tests.test_ai_service_configuration, "AI service configuration"),
        (config_tests.test_resolution_policy_lookup, "Resolution policy lookup"),
        (config_tests.test_equivalence_configuration, "Equivalence configuration"),
        (config_tests.test_approval_requirements, "Approval requirements"),
        
        # Integration tests
        (integration_tests.test_mismatch_to_resolution_workflow, "Mismatch to resolution workflow"),
        (integration_tests.test_configuration_policy_consistency, "Configuration policy consistency"),
    ]
    
    passed = 0
    failed = 0
    
    for test_method, description in test_methods:
        try:
            test_method()
            print(f"✅ {description}")
            passed += 1
        except Exception as e:
            print(f"❌ {description}: {e}")
            if "serialization" in description.lower() or "workflow" in description.lower():
                import traceback
                traceback.print_exc()
            failed += 1
    
    print(f"\\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)
    else:
        print("\\n🎉 All Phase 2 core component tests passed!")
        sys.exit(0)