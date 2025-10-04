#!/usr/bin/env python3
"""
Policy conformance tests for Phase 2 resolution policies.
Ensures ResolutionPolicy actually gates actions as specified.
"""
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Import Phase 2 modules (will be created in Task 1)
# from common.phase2.policy import ResolutionPolicyManager
# from common.phase2.models import MismatchType, SafetyLevel

class MockResolutionPolicyManager:
    """Mock policy manager for testing until real implementation exists."""
    
    def __init__(self, policy_data: Dict[str, Any]):
        self.policy_data = policy_data
        self.matrix = policy_data.get('matrix', [])
    
    def permits(self, mismatch_type: str, environment: str, action: str) -> bool:
        """Check if policy permits the given action."""
        for rule in self.matrix:
            if (rule['mismatch_type'] == mismatch_type and 
                environment in rule['environment'] and
                action in rule['allowed_actions']):
                return True
        return False
    
    def get_safety_level(self, mismatch_type: str, environment: str) -> str:
        """Get safety level for mismatch type in environment."""
        for rule in self.matrix:
            if (rule['mismatch_type'] == mismatch_type and 
                environment in rule['environment']):
                return rule['safety_level']
        return 'experimental'  # Default to most restrictive
    
    def requires_dual_key(self, mismatch_type: str, environment: str) -> bool:
        """Check if dual-key approval is required."""
        for rule in self.matrix:
            if (rule['mismatch_type'] == mismatch_type and 
                environment in rule['environment']):
                return rule.get('dual_key_required', False)
        return True  # Default to requiring dual-key

@pytest.fixture
def load_policy():
    """Load resolution policy from YAML file."""
    def _load_policy(policy_id: str):
        policy_path = Path(f".kiro/specs/phase2-ai-mismatch-resolution/entities/v1/resolution_policy.yaml")
        with open(policy_path) as f:
            policy_data = yaml.safe_load(f)
        return MockResolutionPolicyManager(policy_data)
    return _load_policy

class TestResolutionPolicyConformance:
    """Test that resolution policies enforce expected constraints."""
    
    def test_policy_blocks_destructive_in_prod(self, load_policy):
        """Test that destructive actions are blocked in production."""
        policy = load_policy("policy.phase2.default")
        
        # Semantic text rewriting should be blocked in prod
        assert policy.permits("semantics_text", "prod", "rewrite_formatting") is False
        
        # Semantic code changes should be blocked in prod
        assert policy.permits("semantics_code", "prod", "rewrite_formatting") is False
        
        # Policy violations should have no allowed actions
        assert policy.permits("policy_violation", "prod", "rewrite_formatting") is False
        assert policy.permits("policy_violation", "dev", "rewrite_formatting") is False
    
    def test_policy_allows_safe_actions_in_dev(self, load_policy):
        """Test that safe actions are allowed in development."""
        policy = load_policy("policy.phase2.default")
        
        # JSON ordering should be allowed in all environments
        assert policy.permits("json_ordering", "dev", "canonicalize_json") is True
        assert policy.permits("json_ordering", "stage", "canonicalize_json") is True
        assert policy.permits("json_ordering", "prod", "canonicalize_json") is True
        
        # Whitespace should be allowed in dev/stage
        assert policy.permits("whitespace", "dev", "normalize_whitespace") is True
        assert policy.permits("whitespace", "stage", "normalize_whitespace") is True
    
    def test_policy_safety_levels_correct(self, load_policy):
        """Test that safety levels are correctly assigned."""
        policy = load_policy("policy.phase2.default")
        
        # Safe operations should be automatic
        assert policy.get_safety_level("json_ordering", "prod") == "automatic"
        assert policy.get_safety_level("whitespace", "dev") == "automatic"
        
        # Risky operations should be experimental
        assert policy.get_safety_level("semantics_text", "dev") == "experimental"
        assert policy.get_safety_level("semantics_code", "dev") == "experimental"
        
        # Production should be more restrictive
        assert policy.get_safety_level("whitespace", "prod") == "advisory"
    
    def test_policy_dual_key_requirements(self, load_policy):
        """Test that dual-key requirements are enforced."""
        policy = load_policy("policy.phase2.default")
        
        # Semantic operations should require dual-key
        assert policy.requires_dual_key("semantics_text", "dev") is True
        assert policy.requires_dual_key("semantics_code", "dev") is True
        assert policy.requires_dual_key("policy_violation", "dev") is True
        
        # Safe operations should not require dual-key
        assert policy.requires_dual_key("json_ordering", "dev") is False
        assert policy.requires_dual_key("whitespace", "dev") is False
    
    def test_policy_environment_progression(self, load_policy):
        """Test that policies become more restrictive from dev -> stage -> prod."""
        policy = load_policy("policy.phase2.default")
        
        # Whitespace: automatic in dev/stage, advisory in prod
        assert policy.get_safety_level("whitespace", "dev") == "automatic"
        assert policy.get_safety_level("whitespace", "stage") == "automatic"
        assert policy.get_safety_level("whitespace", "prod") == "advisory"
        
        # Markdown: advisory in dev/stage, experimental in prod
        assert policy.get_safety_level("markdown_formatting", "dev") == "advisory"
        assert policy.get_safety_level("markdown_formatting", "stage") == "advisory"
        assert policy.get_safety_level("markdown_formatting", "prod") == "experimental"
    
    def test_policy_no_auto_resolve_for_analysis_only_types(self, load_policy):
        """Test that analysis-only types have no auto-resolution actions."""
        policy = load_policy("policy.phase2.default")
        
        # These types should only allow ignore_mismatch or no actions
        analysis_only_types = ["nondeterminism", "infra_env_drift"]
        
        for mismatch_type in analysis_only_types:
            for env in ["dev", "stage", "prod"]:
                # Should not allow destructive actions
                assert policy.permits(mismatch_type, env, "rewrite_formatting") is False
                assert policy.permits(mismatch_type, env, "canonicalize_json") is False
                
                # May allow ignore_mismatch for flagging
                # (This is acceptable for analysis-only types)

class TestPolicyValidation:
    """Test policy file validation and structure."""
    
    def test_policy_file_structure(self):
        """Test that policy file has required structure."""
        policy_path = Path(".kiro/specs/phase2-ai-mismatch-resolution/entities/v1/resolution_policy.yaml")
        assert policy_path.exists(), "Resolution policy file must exist"
        
        with open(policy_path) as f:
            policy_data = yaml.safe_load(f)
        
        # Required top-level fields
        assert "id" in policy_data
        assert "version" in policy_data
        assert "matrix" in policy_data
        assert "rollbacks" in policy_data
        assert "audit" in policy_data
        
        # Matrix should be a list of rules
        assert isinstance(policy_data["matrix"], list)
        assert len(policy_data["matrix"]) > 0
        
        # Each rule should have required fields
        for rule in policy_data["matrix"]:
            assert "mismatch_type" in rule
            assert "environment" in rule
            assert "allowed_actions" in rule
            assert "safety_level" in rule
            assert "required_evidence" in rule
            assert "confidence_min" in rule
            assert "dual_key_required" in rule
    
    def test_policy_covers_all_mismatch_types(self):
        """Test that policy covers all defined mismatch types."""
        policy_path = Path(".kiro/specs/phase2-ai-mismatch-resolution/entities/v1/resolution_policy.yaml")
        
        with open(policy_path) as f:
            policy_data = yaml.safe_load(f)
        
        # Expected mismatch types from schema
        expected_types = {
            'whitespace', 'markdown_formatting', 'json_ordering', 
            'semantics_text', 'semantics_code', 'nondeterminism',
            'policy_violation', 'infra_env_drift'
        }
        
        # Types covered in policy
        covered_types = set()
        for rule in policy_data["matrix"]:
            covered_types.add(rule["mismatch_type"])
        
        # All types should be covered
        missing_types = expected_types - covered_types
        assert not missing_types, f"Policy missing coverage for types: {missing_types}"
    
    def test_policy_rollback_triggers_defined(self):
        """Test that rollback triggers are properly defined."""
        policy_path = Path(".kiro/specs/phase2-ai-mismatch-resolution/entities/v1/resolution_policy.yaml")
        
        with open(policy_path) as f:
            policy_data = yaml.safe_load(f)
        
        rollbacks = policy_data["rollbacks"]
        
        # Required rollback triggers
        assert "trigger" in rollbacks
        assert "action" in rollbacks
        
        triggers = rollbacks["trigger"]
        
        # Key safety triggers should be defined
        assert "fp_rate_7d" in triggers
        assert "consecutive_failures" in triggers
        
        # Trigger values should be reasonable
        fp_rate = triggers["fp_rate_7d"]
        assert fp_rate.startswith(">="), "FP rate trigger should be >= threshold"
        
        # Extract numeric value and validate
        fp_threshold = float(fp_rate.split(">=")[1])
        assert 0.01 <= fp_threshold <= 0.05, "FP rate threshold should be 1-5%"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])