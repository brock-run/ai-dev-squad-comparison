"""
Tests for the unified security policy system.
"""
import pytest
import tempfile
import yaml
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from common.safety.policy import (
    SecurityPolicyManager, SecurityPolicy, PolicyLevel, PolicyDomain,
    ExecutionPolicyConfig, FilesystemPolicyConfig, NetworkPolicyConfig, 
    InjectionPolicyConfig, PolicyViolation, get_policy_manager, set_security_level
)
from common.safety.execute import SandboxType


class TestSecurityPolicy:
    """Test SecurityPolicy class functionality."""
    
    def test_policy_creation(self):
        """Test creating a security policy."""
        policy = SecurityPolicy(
            name="test-policy",
            level=PolicyLevel.STANDARD,
            description="Test policy"
        )
        
        assert policy.name == "test-policy"
        assert policy.level == PolicyLevel.STANDARD
        assert policy.description == "Test policy"
        assert isinstance(policy.execution, ExecutionPolicyConfig)
        assert isinstance(policy.filesystem, FilesystemPolicyConfig)
        assert isinstance(policy.network, NetworkPolicyConfig)
        assert isinstance(policy.injection, InjectionPolicyConfig)
    
    def test_policy_to_dict(self):
        """Test converting policy to dictionary."""
        policy = SecurityPolicy(
            name="test-policy",
            level=PolicyLevel.STANDARD,
            description="Test policy"
        )
        
        policy_dict = policy.to_dict()
        
        assert policy_dict['name'] == "test-policy"
        assert policy_dict['level'] == "standard"
        assert policy_dict['description'] == "Test policy"
        assert 'execution' in policy_dict
        assert 'filesystem' in policy_dict
        assert 'network' in policy_dict
        assert 'injection' in policy_dict
        assert 'created_at' in policy_dict


class TestSecurityPolicyManager:
    """Test SecurityPolicyManager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SecurityPolicyManager(config_dir=self.temp_dir)
    
    def test_builtin_policies_loaded(self):
        """Test that built-in policies are loaded correctly."""
        policies = self.manager.list_policies()
        
        expected_policies = ["disabled", "permissive", "standard", "strict", "paranoid"]
        for policy_name in expected_policies:
            assert policy_name in policies
    
    def test_get_policy(self):
        """Test getting a policy by name."""
        policy = self.manager.get_policy("standard")
        
        assert policy is not None
        assert policy.name == "standard"
        assert policy.level == PolicyLevel.STANDARD
    
    def test_get_nonexistent_policy(self):
        """Test getting a non-existent policy."""
        policy = self.manager.get_policy("nonexistent")
        assert policy is None
    
    def test_set_active_policy(self):
        """Test setting the active policy."""
        success = self.manager.set_active_policy("strict")
        
        assert success is True
        active_policy = self.manager.get_active_policy()
        assert active_policy.name == "strict"
        assert active_policy.level == PolicyLevel.STRICT
    
    def test_set_nonexistent_active_policy(self):
        """Test setting a non-existent active policy."""
        success = self.manager.set_active_policy("nonexistent")
        
        assert success is False
        # Should still have the default policy
        active_policy = self.manager.get_active_policy()
        assert active_policy.name == "standard"
    
    def test_create_custom_policy(self):
        """Test creating a custom policy."""
        custom_execution = ExecutionPolicyConfig(
            max_memory_mb=2048,
            timeout_seconds=600
        )
        
        policy = self.manager.create_custom_policy(
            name="custom-test",
            level=PolicyLevel.PERMISSIVE,
            description="Custom test policy",
            execution=custom_execution
        )
        
        assert policy.name == "custom-test"
        assert policy.level == PolicyLevel.PERMISSIVE
        assert policy.execution.max_memory_mb == 2048
        assert policy.execution.timeout_seconds == 600
        
        # Verify it's stored in the manager
        retrieved_policy = self.manager.get_policy("custom-test")
        assert retrieved_policy is not None
        assert retrieved_policy.name == "custom-test"
    
    def test_save_and_load_policy(self):
        """Test saving and loading policies from files."""
        # Create a custom policy
        policy = self.manager.create_custom_policy(
            name="file-test",
            level=PolicyLevel.STRICT,
            description="File test policy"
        )
        
        # Save to file
        policy_file = Path(self.temp_dir) / "test_policy.yaml"
        self.manager.save_policy_to_file("file-test", str(policy_file))
        
        assert policy_file.exists()
        
        # Create new manager and load the policy
        new_manager = SecurityPolicyManager(config_dir=self.temp_dir)
        loaded_policy = new_manager.load_policy_from_file(str(policy_file))
        
        assert loaded_policy.name == "file-test"
        assert loaded_policy.level == PolicyLevel.STRICT
        assert loaded_policy.description == "File test policy"
    
    def test_validate_policy_warnings(self):
        """Test policy validation warnings."""
        # Create a policy with potential issues
        risky_policy = SecurityPolicy(
            name="risky-policy",
            level=PolicyLevel.STANDARD,
            description="Policy with potential issues",
            execution=ExecutionPolicyConfig(
                max_memory_mb=32,  # Very low memory
                timeout_seconds=7200  # Very long timeout
            ),
            filesystem=FilesystemPolicyConfig(
                system_access=True,  # System access enabled
                max_file_size_mb=2000  # Very large files
            ),
            network=NetworkPolicyConfig(
                default_deny=False,  # Default allow
                verify_ssl=False  # SSL verification disabled
            )
        )
        
        warnings = self.manager.validate_policy(risky_policy)
        
        assert len(warnings) > 0
        warning_text = " ".join(warnings)
        assert "memory limit is very low" in warning_text
        assert "timeout is very long" in warning_text
        assert "System access enabled" in warning_text
        assert "File size limit is very high" in warning_text
        assert "default deny is disabled" in warning_text
        assert "SSL verification disabled" in warning_text
    
    def test_record_violation(self):
        """Test recording policy violations."""
        self.manager.record_violation(
            domain=PolicyDomain.EXECUTION,
            policy_name="test-policy",
            violation_type="resource_limit",
            severity="high",
            description="Memory limit exceeded",
            user_id="test-user",
            session_id="test-session",
            memory_used=1024
        )
        
        violations = self.manager.get_violations()
        assert len(violations) == 1
        
        violation = violations[0]
        assert violation.domain == PolicyDomain.EXECUTION
        assert violation.policy_name == "test-policy"
        assert violation.violation_type == "resource_limit"
        assert violation.severity == "high"
        assert violation.description == "Memory limit exceeded"
        assert violation.user_id == "test-user"
        assert violation.session_id == "test-session"
        assert violation.metadata["memory_used"] == 1024
    
    def test_get_violations_filtered(self):
        """Test getting filtered violations."""
        # Record violations in different domains
        self.manager.record_violation(
            domain=PolicyDomain.EXECUTION,
            policy_name="test-policy",
            violation_type="resource_limit",
            severity="high",
            description="Execution violation"
        )
        
        self.manager.record_violation(
            domain=PolicyDomain.NETWORK,
            policy_name="test-policy",
            violation_type="blocked_domain",
            severity="medium",
            description="Network violation"
        )
        
        # Get all violations
        all_violations = self.manager.get_violations()
        assert len(all_violations) == 2
        
        # Get execution violations only
        execution_violations = self.manager.get_violations(domain=PolicyDomain.EXECUTION)
        assert len(execution_violations) == 1
        assert execution_violations[0].domain == PolicyDomain.EXECUTION
        
        # Get network violations only
        network_violations = self.manager.get_violations(domain=PolicyDomain.NETWORK)
        assert len(network_violations) == 1
        assert network_violations[0].domain == PolicyDomain.NETWORK
    
    def test_get_policy_statistics(self):
        """Test getting policy statistics."""
        # Record some violations
        self.manager.record_violation(
            domain=PolicyDomain.EXECUTION,
            policy_name="standard",
            violation_type="resource_limit",
            severity="high",
            description="Test violation 1"
        )
        
        self.manager.record_violation(
            domain=PolicyDomain.NETWORK,
            policy_name="standard",
            violation_type="blocked_domain",
            severity="medium",
            description="Test violation 2"
        )
        
        stats = self.manager.get_policy_statistics()
        
        assert stats['total_policies'] == 5  # Built-in policies
        assert stats['active_policy'] == "standard"
        assert stats['active_level'] == "standard"
        assert stats['total_violations'] == 2
        assert stats['violations_by_domain']['execution'] == 1
        assert stats['violations_by_domain']['network'] == 1
        assert stats['violations_by_severity']['high'] == 1
        assert stats['violations_by_severity']['medium'] == 1
        assert stats['policy_levels']['disabled'] == 1
        assert stats['policy_levels']['permissive'] == 1
        assert stats['policy_levels']['standard'] == 1
        assert stats['policy_levels']['strict'] == 1
        assert stats['policy_levels']['paranoid'] == 1


class TestBuiltinPolicies:
    """Test built-in policy configurations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = SecurityPolicyManager()
    
    def test_disabled_policy(self):
        """Test disabled policy configuration."""
        policy = self.manager.get_policy("disabled")
        
        assert policy.level == PolicyLevel.DISABLED
        assert policy.execution.enabled is False
        assert policy.filesystem.enabled is False
        assert policy.network.enabled is False
        assert policy.injection.enabled is False
    
    def test_permissive_policy(self):
        """Test permissive policy configuration."""
        policy = self.manager.get_policy("permissive")
        
        assert policy.level == PolicyLevel.PERMISSIVE
        assert policy.execution.enabled is True
        assert policy.execution.sandbox_type == SandboxType.SUBPROCESS
        assert policy.execution.network_enabled is True
        assert policy.filesystem.restrict_to_repo is False
        assert policy.network.default_deny is False
        assert policy.injection.block_high is False
    
    def test_standard_policy(self):
        """Test standard policy configuration."""
        policy = self.manager.get_policy("standard")
        
        assert policy.level == PolicyLevel.STANDARD
        assert policy.execution.enabled is True
        assert policy.execution.sandbox_type == SandboxType.DOCKER
        assert policy.execution.network_enabled is False
        assert policy.filesystem.restrict_to_repo is True
        assert policy.network.default_deny is True
        assert policy.injection.block_critical is True
        assert policy.injection.block_high is True
    
    def test_strict_policy(self):
        """Test strict policy configuration."""
        policy = self.manager.get_policy("strict")
        
        assert policy.level == PolicyLevel.STRICT
        assert policy.execution.max_memory_mb == 512
        assert policy.execution.max_cpu_percent == 60
        assert policy.filesystem.max_file_size_mb == 50
        assert policy.network.rate_limit == 30
        assert policy.injection.flag_medium is False  # Block medium threats
    
    def test_paranoid_policy(self):
        """Test paranoid policy configuration."""
        policy = self.manager.get_policy("paranoid")
        
        assert policy.level == PolicyLevel.PARANOID
        assert policy.execution.max_memory_mb == 256
        assert policy.execution.temp_dir_access is False
        assert policy.filesystem.temp_dir_access is False
        assert policy.network.enabled is False
        assert policy.injection.allow_low is False  # Block low threats


class TestGlobalFunctions:
    """Test global utility functions."""
    
    def test_get_policy_manager_singleton(self):
        """Test that get_policy_manager returns singleton."""
        manager1 = get_policy_manager()
        manager2 = get_policy_manager()
        
        assert manager1 is manager2
    
    def test_set_security_level(self):
        """Test setting security level via global function."""
        success = set_security_level(PolicyLevel.STRICT)
        
        assert success is True
        
        manager = get_policy_manager()
        active_policy = manager.get_active_policy()
        assert active_policy.level == PolicyLevel.STRICT


class TestPolicyViolation:
    """Test PolicyViolation functionality."""
    
    def test_violation_creation(self):
        """Test creating a policy violation."""
        violation = PolicyViolation(
            timestamp=datetime.utcnow(),
            domain=PolicyDomain.FILESYSTEM,
            policy_name="test-policy",
            violation_type="unauthorized_access",
            severity="critical",
            description="Attempted to access system files",
            user_id="test-user",
            session_id="test-session",
            metadata={"file_path": "/etc/passwd"}
        )
        
        assert violation.domain == PolicyDomain.FILESYSTEM
        assert violation.policy_name == "test-policy"
        assert violation.violation_type == "unauthorized_access"
        assert violation.severity == "critical"
        assert violation.description == "Attempted to access system files"
        assert violation.user_id == "test-user"
        assert violation.session_id == "test-session"
        assert violation.metadata["file_path"] == "/etc/passwd"


class TestPolicyFileOperations:
    """Test policy file operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SecurityPolicyManager(config_dir=self.temp_dir)
    
    def test_load_invalid_policy_file(self):
        """Test loading an invalid policy file."""
        # Create invalid YAML file
        invalid_file = Path(self.temp_dir) / "invalid.yaml"
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            self.manager.load_policy_from_file(str(invalid_file))
    
    def test_load_nonexistent_policy_file(self):
        """Test loading a non-existent policy file."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.yaml"
        
        with pytest.raises(FileNotFoundError):
            self.manager.load_policy_from_file(str(nonexistent_file))
    
    def test_save_nonexistent_policy(self):
        """Test saving a non-existent policy."""
        output_file = Path(self.temp_dir) / "output.yaml"
        
        with pytest.raises(ValueError):
            self.manager.save_policy_to_file("nonexistent", str(output_file))
    
    def test_export_violations(self):
        """Test exporting violations to JSON."""
        # Record some violations
        self.manager.record_violation(
            domain=PolicyDomain.EXECUTION,
            policy_name="test-policy",
            violation_type="resource_limit",
            severity="high",
            description="Test violation"
        )
        
        # Export violations
        output_file = Path(self.temp_dir) / "violations.json"
        self.manager.export_violations(str(output_file))
        
        assert output_file.exists()
        
        # Verify content
        import json
        with open(output_file, 'r') as f:
            violations_data = json.load(f)
        
        assert len(violations_data) == 1
        assert violations_data[0]['domain'] == 'execution'
        assert violations_data[0]['violation_type'] == 'resource_limit'


if __name__ == "__main__":
    pytest.main([__file__])