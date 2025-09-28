#!/usr/bin/env python3
"""
Security Policy System Demonstration

This example demonstrates the unified security policy management system,
showing how to:
1. Use built-in security policies
2. Create custom policies
3. Monitor policy violations
4. Integrate with other security components
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.safety.policy import (
    SecurityPolicyManager, SecurityPolicy, PolicyLevel, PolicyDomain,
    ExecutionPolicyConfig, FilesystemPolicyConfig, NetworkPolicyConfig,
    InjectionPolicyConfig, get_policy_manager, set_security_level
)
from common.safety.execute import SandboxType


def demonstrate_builtin_policies():
    """Demonstrate built-in security policies."""
    print("=== Built-in Security Policies ===")
    
    manager = get_policy_manager()
    
    # List all available policies
    policies = manager.list_policies()
    print(f"Available policies: {', '.join(policies)}")
    
    # Show details for each built-in policy
    for policy_name in ["disabled", "permissive", "standard", "strict", "paranoid"]:
        policy = manager.get_policy(policy_name)
        print(f"\n{policy_name.upper()} Policy:")
        print(f"  Level: {policy.level.value}")
        print(f"  Description: {policy.description}")
        print(f"  Execution sandbox: {policy.execution.sandbox_type.value}")
        print(f"  Max memory: {policy.execution.max_memory_mb}MB")
        print(f"  Network enabled: {policy.execution.network_enabled}")
        print(f"  Filesystem restricted: {policy.filesystem.restrict_to_repo}")
        print(f"  Network default deny: {policy.network.default_deny}")
        print(f"  Injection detection: {policy.injection.enabled}")


def demonstrate_policy_switching():
    """Demonstrate switching between security policies."""
    print("\n=== Policy Switching ===")
    
    manager = get_policy_manager()
    
    # Show current active policy
    current_policy = manager.get_active_policy()
    print(f"Current active policy: {current_policy.name} ({current_policy.level.value})")
    
    # Switch to strict policy
    print("\nSwitching to strict policy...")
    success = manager.set_active_policy("strict")
    if success:
        active_policy = manager.get_active_policy()
        print(f"Active policy is now: {active_policy.name}")
        print(f"  Max memory limit: {active_policy.execution.max_memory_mb}MB")
        print(f"  Network rate limit: {active_policy.network.rate_limit} req/min")
    
    # Switch using global function
    print("\nSwitching to permissive policy using global function...")
    success = set_security_level(PolicyLevel.PERMISSIVE)
    if success:
        active_policy = manager.get_active_policy()
        print(f"Active policy is now: {active_policy.name}")


def demonstrate_custom_policy():
    """Demonstrate creating custom security policies."""
    print("\n=== Custom Policy Creation ===")
    
    manager = get_policy_manager()
    
    # Create custom execution configuration
    custom_execution = ExecutionPolicyConfig(
        enabled=True,
        sandbox_type=SandboxType.DOCKER,
        max_memory_mb=768,
        max_cpu_percent=70,
        timeout_seconds=240,
        network_enabled=False,
        allowed_languages={"python", "javascript"},
        denied_imports={"os", "subprocess", "sys", "importlib"}
    )
    
    # Create custom filesystem configuration
    custom_filesystem = FilesystemPolicyConfig(
        enabled=True,
        restrict_to_repo=True,
        temp_dir_access=True,
        max_file_size_mb=75,
        max_files_created=750,
        allowed_extensions={".py", ".js", ".json", ".txt", ".md"},
        denied_extensions={".exe", ".dll", ".so", ".sh", ".bat"}
    )
    
    # Create custom network configuration
    custom_network = NetworkPolicyConfig(
        enabled=True,
        default_deny=True,
        allowed_domains={"api.github.com", "httpbin.org"},
        allowed_ports={443},
        rate_limit=45,
        verify_ssl=True
    )
    
    # Create custom injection configuration
    custom_injection = InjectionPolicyConfig(
        enabled=True,
        block_critical=True,
        block_high=True,
        flag_medium=False,  # Block medium threats too
        allow_low=True,
        llm_judge_enabled=False
    )
    
    # Create the custom policy
    custom_policy = manager.create_custom_policy(
        name="demo-custom",
        level=PolicyLevel.STANDARD,
        description="Custom policy for demonstration",
        execution=custom_execution,
        filesystem=custom_filesystem,
        network=custom_network,
        injection=custom_injection,
        metadata={
            "created_by": "demo_script",
            "purpose": "demonstration",
            "version": "1.0"
        }
    )
    
    print(f"Created custom policy: {custom_policy.name}")
    print(f"  Level: {custom_policy.level.value}")
    print(f"  Description: {custom_policy.description}")
    print(f"  Max memory: {custom_policy.execution.max_memory_mb}MB")
    print(f"  Allowed domains: {list(custom_policy.network.allowed_domains)}")
    print(f"  Metadata: {custom_policy.metadata}")
    
    # Activate the custom policy
    manager.set_active_policy("demo-custom")
    print(f"\nActivated custom policy: {manager.get_active_policy().name}")


def demonstrate_policy_validation():
    """Demonstrate policy validation."""
    print("\n=== Policy Validation ===")
    
    manager = get_policy_manager()
    
    # Create a policy with potential security issues
    risky_policy = SecurityPolicy(
        name="risky-demo",
        level=PolicyLevel.STANDARD,
        description="Policy with potential security issues",
        execution=ExecutionPolicyConfig(
            max_memory_mb=32,  # Very low memory
            timeout_seconds=7200,  # Very long timeout
            network_enabled=True
        ),
        filesystem=FilesystemPolicyConfig(
            system_access=True,  # System access enabled
            max_file_size_mb=2000,  # Very large files
            restrict_to_repo=False
        ),
        network=NetworkPolicyConfig(
            default_deny=False,  # Default allow
            verify_ssl=False,  # SSL verification disabled
            rate_limit=1000  # Very high rate limit
        ),
        injection=InjectionPolicyConfig(
            enabled=False  # Injection detection disabled
        )
    )
    
    # Validate the policy
    warnings = manager.validate_policy(risky_policy)
    
    print(f"Validating risky policy '{risky_policy.name}':")
    if warnings:
        print("  Validation warnings:")
        for warning in warnings:
            print(f"    - {warning}")
    else:
        print("  No validation warnings")
    
    # Validate a good policy
    good_policy = manager.get_policy("standard")
    warnings = manager.validate_policy(good_policy)
    
    print(f"\nValidating standard policy '{good_policy.name}':")
    if warnings:
        print("  Validation warnings:")
        for warning in warnings:
            print(f"    - {warning}")
    else:
        print("  No validation warnings - policy looks good!")


def demonstrate_violation_tracking():
    """Demonstrate policy violation tracking."""
    print("\n=== Policy Violation Tracking ===")
    
    manager = get_policy_manager()
    
    # Record some sample violations
    violations_data = [
        {
            "domain": PolicyDomain.EXECUTION,
            "policy_name": "standard",
            "violation_type": "memory_limit_exceeded",
            "severity": "high",
            "description": "Process exceeded 1GB memory limit",
            "user_id": "demo_user",
            "session_id": "demo_session_1",
            "memory_used": 1200
        },
        {
            "domain": PolicyDomain.FILESYSTEM,
            "policy_name": "standard",
            "violation_type": "unauthorized_access",
            "severity": "critical",
            "description": "Attempted to access system directory",
            "user_id": "demo_user",
            "session_id": "demo_session_1",
            "attempted_path": "/etc/passwd"
        },
        {
            "domain": PolicyDomain.NETWORK,
            "policy_name": "standard",
            "violation_type": "blocked_domain",
            "severity": "medium",
            "description": "Attempted to access blocked domain",
            "user_id": "demo_user",
            "session_id": "demo_session_2",
            "blocked_domain": "malicious-site.com"
        },
        {
            "domain": PolicyDomain.INJECTION,
            "policy_name": "standard",
            "violation_type": "prompt_injection",
            "severity": "high",
            "description": "Detected prompt injection attempt",
            "user_id": "demo_user",
            "session_id": "demo_session_2",
            "pattern_matched": "ignore_instructions"
        }
    ]
    
    # Record the violations
    for violation_data in violations_data:
        manager.record_violation(**violation_data)
    
    print(f"Recorded {len(violations_data)} sample violations")
    
    # Get all violations
    all_violations = manager.get_violations()
    print(f"\nTotal violations: {len(all_violations)}")
    
    # Get violations by domain
    for domain in PolicyDomain:
        if domain == PolicyDomain.ALL:
            continue
        domain_violations = manager.get_violations(domain=domain)
        if domain_violations:
            print(f"\n{domain.value.upper()} violations:")
            for violation in domain_violations:
                print(f"  - {violation.violation_type}: {violation.description}")
                print(f"    Severity: {violation.severity}, Time: {violation.timestamp}")
    
    # Get policy statistics
    stats = manager.get_policy_statistics()
    print(f"\n=== Policy Statistics ===")
    print(f"Total policies: {stats['total_policies']}")
    print(f"Active policy: {stats['active_policy']} ({stats['active_level']})")
    print(f"Total violations: {stats['total_violations']}")
    print(f"Violations by domain: {stats['violations_by_domain']}")
    print(f"Violations by severity: {stats['violations_by_severity']}")


def demonstrate_file_operations():
    """Demonstrate saving and loading policies from files."""
    print("\n=== Policy File Operations ===")
    
    manager = get_policy_manager()
    
    # Create a temporary directory for demo files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Save a policy to file
        policy_file = temp_path / "demo_policy.yaml"
        manager.save_policy_to_file("standard", str(policy_file))
        print(f"Saved standard policy to: {policy_file}")
        
        # Load policy from file
        loaded_policy = manager.load_policy_from_file(str(policy_file))
        print(f"Loaded policy: {loaded_policy.name} ({loaded_policy.level.value})")
        
        # Export violations to JSON
        violations_file = temp_path / "violations.json"
        manager.export_violations(str(violations_file))
        print(f"Exported violations to: {violations_file}")
        
        # Show file contents
        print(f"\nPolicy file size: {policy_file.stat().st_size} bytes")
        print(f"Violations file size: {violations_file.stat().st_size} bytes")


def demonstrate_integration_example():
    """Demonstrate integration with other security components."""
    print("\n=== Integration Example ===")
    
    manager = get_policy_manager()
    
    # Get active policy
    active_policy = manager.get_active_policy()
    print(f"Active policy: {active_policy.name}")
    
    # Example: Check if network access is allowed
    if active_policy.network.enabled:
        if active_policy.network.default_deny:
            allowed_domains = list(active_policy.network.allowed_domains)
            print(f"Network access: Restricted to {len(allowed_domains)} domains")
            print(f"  Allowed domains: {allowed_domains[:3]}{'...' if len(allowed_domains) > 3 else ''}")
        else:
            print("Network access: Permissive (default allow)")
    else:
        print("Network access: Completely disabled")
    
    # Example: Check execution limits
    exec_config = active_policy.execution
    print(f"Execution limits:")
    print(f"  Sandbox type: {exec_config.sandbox_type.value}")
    print(f"  Memory limit: {exec_config.max_memory_mb}MB")
    print(f"  CPU limit: {exec_config.max_cpu_percent}%")
    print(f"  Timeout: {exec_config.timeout_seconds}s")
    
    # Example: Check filesystem restrictions
    fs_config = active_policy.filesystem
    print(f"Filesystem access:")
    print(f"  Restricted to repo: {fs_config.restrict_to_repo}")
    print(f"  System access: {fs_config.system_access}")
    print(f"  Max file size: {fs_config.max_file_size_mb}MB")
    
    # Example: Check injection detection settings
    inj_config = active_policy.injection
    print(f"Injection detection:")
    print(f"  Enabled: {inj_config.enabled}")
    if inj_config.enabled:
        print(f"  Block critical: {inj_config.block_critical}")
        print(f"  Block high: {inj_config.block_high}")
        print(f"  LLM judge: {inj_config.llm_judge_enabled}")


def main():
    """Run all demonstrations."""
    print("Security Policy System Demonstration")
    print("=" * 50)
    
    try:
        demonstrate_builtin_policies()
        demonstrate_policy_switching()
        demonstrate_custom_policy()
        demonstrate_policy_validation()
        demonstrate_violation_tracking()
        demonstrate_file_operations()
        demonstrate_integration_example()
        
        print("\n" + "=" * 50)
        print("Demonstration completed successfully!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())