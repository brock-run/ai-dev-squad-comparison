"""
Security Policy System for AI Dev Squad Comparison
This module provides unified security policy management and enforcement
across all safety components (execution, filesystem, network, injection).
"""
import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from datetime import datetime

from .execute import SandboxType
from .fs import FilesystemPolicy
from .net import NetworkPolicy
from .injection import InjectionPattern, InjectionType, ThreatLevel, FilterAction

logger = logging.getLogger(__name__)

class PolicyLevel(str, Enum):
    """Security policy enforcement level."""
    DISABLED = "disabled"
    PERMISSIVE = "permissive"
    BALANCED = "balanced"
    STRICT = "strict"
    PARANOID = "paranoid"

class PolicyScope(str, Enum):
    """Policy application scope."""
    GLOBAL = "global"
    TASK = "task"
    USER = "user"
    SESSION = "session"

@dataclass
class ExecutionPolicy:
    """Execution sandbox policy configuration."""
    enabled: bool = True
    sandbox_type: SandboxType = SandboxType.DOCKER
    max_memory_mb: int = 1024
    max_cpu_percent: int = 80
    timeout_seconds: int = 300
    network_enabled: bool = False
    allowed_languages: Set[str] = field(default_factory=lambda: {"python", "javascript", "bash"})
    denied_imports: Set[str] = field(default_factory=lambda: {"os", "subprocess", "sys"})
    resource_monitoring: bool = True

@dataclass
class SecurityPolicyViolation:
    """Record of a security policy violation."""
    timestamp: datetime
    policy_name: str
    violation_type: str
    severity: str
    description: str
    component: str  # execution, filesystem, network, injection
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityPolicy:
    """Comprehensive security policy configuration."""
    name: str
    version: str
    level: PolicyLevel
    scope: PolicyScope
    description: str
    
    # Component policies
    execution: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    filesystem: Optional[FilesystemPolicy] = None
    network: Optional[NetworkPolicy] = None
    injection_patterns: List[InjectionPattern] = field(default_factory=list)
    
    # Policy metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    tags: Set[str] = field(default_factory=set)
    
    # Enforcement settings
    enforce_all: bool = True
    fail_open: bool = False  # Fail secure by default
    audit_enabled: bool = True
    violation_threshold: int = 10  # Max violations before escalation

class SecurityPolicyManager:
    """
    Centralized security policy management and enforcement system.
    """
    
    def __init__(self, policy_dir: Optional[str] = None):
        self.policy_dir = Path(policy_dir or "config/policies")
        self.policies: Dict[str, SecurityPolicy] = {}
        self.active_policy: Optional[SecurityPolicy] = None
        self.violations: List[SecurityPolicyViolation] = []
        self.policy_overrides: Dict[str, Dict[str, Any]] = {}
        
        # Ensure policy directory exists
        self.policy_dir.mkdir(parents=True, exist_ok=True)
        
        # Load default policies
        self._create_default_policies()
        
        logger.info(f"Security policy manager initialized with {len(self.policies)} policies")
    
    def _create_default_policies(self):
        """Create default security policies for different use cases."""
        
        # Development Policy - Permissive for development work
        dev_policy = SecurityPolicy(
            name="development",
            version="1.0.0",
            level=PolicyLevel.PERMISSIVE,
            scope=PolicyScope.GLOBAL,
            description="Permissive policy for development environments",
            execution=ExecutionPolicy(
                enabled=True,
                sandbox_type=SandboxType.SUBPROCESS,
                max_memory_mb=2048,
                max_cpu_percent=90,
                timeout_seconds=600,
                network_enabled=True,
                allowed_languages={"python", "javascript", "bash", "shell"},
                denied_imports={"subprocess"},
                resource_monitoring=True
            ),
            filesystem=FilesystemPolicy(
                restrict_to_repo=True,
                temp_dir_access=True,
                system_access=False,
                max_file_size=50 * 1024 * 1024,  # 50MB
                audit_enabled=True
            ),
            network=NetworkPolicy(
                default_deny=False,
                allowed_domains={"*"},  # Allow all in dev
                request_timeout=60,
                verify_ssl=False,  # For testing
                audit_enabled=True
            ),
            tags={"development", "permissive"},
            enforce_all=False,
            fail_open=True
        )
        
        # Production Policy - Strict for production environments
        prod_policy = SecurityPolicy(
            name="production",
            version="1.0.0",
            level=PolicyLevel.STRICT,
            scope=PolicyScope.GLOBAL,
            description="Strict policy for production environments",
            execution=ExecutionPolicy(
                enabled=True,
                sandbox_type=SandboxType.DOCKER,
                max_memory_mb=512,
                max_cpu_percent=70,
                timeout_seconds=300,
                network_enabled=False,
                allowed_languages={"python"},
                denied_imports={"os", "subprocess", "sys", "importlib"},
                resource_monitoring=True
            ),
            filesystem=FilesystemPolicy(
                restrict_to_repo=True,
                temp_dir_access=True,
                system_access=False,
                max_file_size=10 * 1024 * 1024,  # 10MB
                allowed_extensions={'.py', '.json', '.txt', '.md'},
                denied_extensions={'.exe', '.dll', '.so', '.sh', '.bat'},
                audit_enabled=True
            ),
            network=NetworkPolicy(
                default_deny=True,
                allowed_domains={"api.github.com", "api.gitlab.com"},
                allowed_ports={443},
                denied_ports={22, 23, 25, 53, 80},
                request_timeout=30,
                max_response_size=5 * 1024 * 1024,  # 5MB
                verify_ssl=True,
                rate_limit=30,
                audit_enabled=True
            ),
            tags={"production", "strict"},
            enforce_all=True,
            fail_open=False,
            violation_threshold=5
        )
        
        # Balanced Policy - Good default for most use cases
        balanced_policy = SecurityPolicy(
            name="balanced",
            version="1.0.0",
            level=PolicyLevel.BALANCED,
            scope=PolicyScope.GLOBAL,
            description="Balanced policy for general use",
            execution=ExecutionPolicy(
                enabled=True,
                sandbox_type=SandboxType.DOCKER,
                max_memory_mb=1024,
                max_cpu_percent=80,
                timeout_seconds=300,
                network_enabled=False,
                allowed_languages={"python", "javascript"},
                denied_imports={"os", "subprocess"},
                resource_monitoring=True
            ),
            filesystem=FilesystemPolicy(
                restrict_to_repo=True,
                temp_dir_access=True,
                system_access=False,
                max_file_size=25 * 1024 * 1024,  # 25MB
                allowed_extensions={'.py', '.js', '.json', '.yaml', '.txt', '.md'},
                denied_extensions={'.exe', '.dll', '.so'},
                audit_enabled=True
            ),
            network=NetworkPolicy(
                default_deny=True,
                allowed_domains={"api.github.com", "api.gitlab.com", "httpbin.org"},
                allowed_ports={80, 443},
                denied_ports={22, 23, 25},
                request_timeout=30,
                verify_ssl=True,
                rate_limit=60,
                audit_enabled=True
            ),
            tags={"balanced", "default"},
            enforce_all=True,
            fail_open=False
        )
        
        # Paranoid Policy - Maximum security
        paranoid_policy = SecurityPolicy(
            name="paranoid",
            version="1.0.0",
            level=PolicyLevel.PARANOID,
            scope=PolicyScope.GLOBAL,
            description="Maximum security policy for high-risk environments",
            execution=ExecutionPolicy(
                enabled=True,
                sandbox_type=SandboxType.DOCKER,
                max_memory_mb=256,
                max_cpu_percent=50,
                timeout_seconds=120,
                network_enabled=False,
                allowed_languages={"python"},
                denied_imports={"os", "subprocess", "sys", "importlib", "eval", "exec"},
                resource_monitoring=True
            ),
            filesystem=FilesystemPolicy(
                restrict_to_repo=True,
                temp_dir_access=False,
                system_access=False,
                max_file_size=5 * 1024 * 1024,  # 5MB
                max_files_created=100,
                allowed_extensions={'.py', '.json', '.txt'},
                denied_extensions={'.exe', '.dll', '.so', '.sh', '.bat', '.js'},
                audit_enabled=True
            ),
            network=NetworkPolicy(
                default_deny=True,
                allowed_domains=set(),  # No network access
                allowed_ports=set(),
                denied_ports={i for i in range(1, 65536)},  # Block all ports
                request_timeout=10,
                verify_ssl=True,
                rate_limit=10,
                audit_enabled=True
            ),
            tags={"paranoid", "maximum-security"},
            enforce_all=True,
            fail_open=False,
            violation_threshold=1
        )
        
        # Store default policies
        self.policies = {
            "development": dev_policy,
            "production": prod_policy,
            "balanced": balanced_policy,
            "paranoid": paranoid_policy
        }
        
        # Set balanced as default active policy
        self.active_policy = balanced_policy
    
    def load_policy_from_file(self, policy_file: str) -> SecurityPolicy:
        """
        Load security policy from YAML file.
        
        Args:
            policy_file: Path to policy configuration file
            
        Returns:
            Loaded SecurityPolicy instance
        """
        policy_path = Path(policy_file)
        if not policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {policy_file}")
        
        try:
            with open(policy_path, 'r') as f:
                policy_data = yaml.safe_load(f)
            
            # Parse policy components
            policy = SecurityPolicy(
                name=policy_data['name'],
                version=policy_data['version'],
                level=PolicyLevel(policy_data['level']),
                scope=PolicyScope(policy_data['scope']),
                description=policy_data['description']
            )
            
            # Load execution policy
            if 'execution' in policy_data:
                exec_data = policy_data['execution']
                policy.execution = ExecutionPolicy(
                    enabled=exec_data.get('enabled', True),
                    sandbox_type=SandboxType(exec_data.get('sandbox_type', 'docker')),
                    max_memory_mb=exec_data.get('max_memory_mb', 1024),
                    max_cpu_percent=exec_data.get('max_cpu_percent', 80),
                    timeout_seconds=exec_data.get('timeout_seconds', 300),
                    network_enabled=exec_data.get('network_enabled', False),
                    allowed_languages=set(exec_data.get('allowed_languages', ['python'])),
                    denied_imports=set(exec_data.get('denied_imports', ['os', 'subprocess']))
                )
            
            # Load filesystem policy
            if 'filesystem' in policy_data:
                fs_data = policy_data['filesystem']
                policy.filesystem = FilesystemPolicy(
                    restrict_to_repo=fs_data.get('restrict_to_repo', True),
                    temp_dir_access=fs_data.get('temp_dir_access', True),
                    system_access=fs_data.get('system_access', False),
                    max_file_size=fs_data.get('max_file_size', 10 * 1024 * 1024),
                    allowed_extensions=set(fs_data.get('allowed_extensions', [])),
                    denied_extensions=set(fs_data.get('denied_extensions', [])),
                    audit_enabled=fs_data.get('audit_enabled', True)
                )
            
            # Load network policy
            if 'network' in policy_data:
                net_data = policy_data['network']
                policy.network = NetworkPolicy(
                    default_deny=net_data.get('default_deny', True),
                    allowed_domains=set(net_data.get('allowed_domains', [])),
                    denied_domains=set(net_data.get('denied_domains', [])),
                    allowed_ports=set(net_data.get('allowed_ports', [80, 443])),
                    denied_ports=set(net_data.get('denied_ports', [])),
                    request_timeout=net_data.get('request_timeout', 30),
                    verify_ssl=net_data.get('verify_ssl', True),
                    audit_enabled=net_data.get('audit_enabled', True)
                )
            
            # Load injection patterns
            if 'injection_patterns' in policy_data:
                for pattern_data in policy_data['injection_patterns']:
                    pattern = InjectionPattern(
                        name=pattern_data['name'],
                        pattern=pattern_data['pattern'],
                        injection_type=InjectionType(pattern_data['injection_type']),
                        threat_level=ThreatLevel(pattern_data['threat_level']),
                        description=pattern_data['description'],
                        action=FilterAction(pattern_data.get('action', 'block'))
                    )
                    policy.injection_patterns.append(pattern)
            
            # Load metadata
            policy.tags = set(policy_data.get('tags', []))
            policy.enforce_all = policy_data.get('enforce_all', True)
            policy.fail_open = policy_data.get('fail_open', False)
            policy.audit_enabled = policy_data.get('audit_enabled', True)
            
            logger.info(f"Loaded security policy: {policy.name} v{policy.version}")
            return policy
            
        except Exception as e:
            logger.error(f"Error loading policy from {policy_file}: {e}")
            raise ValueError(f"Invalid policy file: {e}")
    
    def save_policy_to_file(self, policy: SecurityPolicy, output_file: str):
        """
        Save security policy to YAML file.
        
        Args:
            policy: SecurityPolicy to save
            output_file: Path to output file
        """
        policy_data = {
            'name': policy.name,
            'version': policy.version,
            'level': policy.level.value,
            'scope': policy.scope.value,
            'description': policy.description,
            'execution': {
                'enabled': policy.execution.enabled,
                'sandbox_type': policy.execution.sandbox_type.value,
                'max_memory_mb': policy.execution.max_memory_mb,
                'max_cpu_percent': policy.execution.max_cpu_percent,
                'timeout_seconds': policy.execution.timeout_seconds,
                'network_enabled': policy.execution.network_enabled,
                'allowed_languages': list(policy.execution.allowed_languages),
                'denied_imports': list(policy.execution.denied_imports),
                'resource_monitoring': policy.execution.resource_monitoring
            },
            'tags': list(policy.tags),
            'enforce_all': policy.enforce_all,
            'fail_open': policy.fail_open,
            'audit_enabled': policy.audit_enabled,
            'violation_threshold': policy.violation_threshold
        }
        
        # Add filesystem policy if present
        if policy.filesystem:
            policy_data['filesystem'] = {
                'restrict_to_repo': policy.filesystem.restrict_to_repo,
                'temp_dir_access': policy.filesystem.temp_dir_access,
                'system_access': policy.filesystem.system_access,
                'max_file_size': policy.filesystem.max_file_size,
                'max_files_created': policy.filesystem.max_files_created,
                'allowed_extensions': list(policy.filesystem.allowed_extensions),
                'denied_extensions': list(policy.filesystem.denied_extensions),
                'audit_enabled': policy.filesystem.audit_enabled
            }
        
        # Add network policy if present
        if policy.network:
            policy_data['network'] = {
                'default_deny': policy.network.default_deny,
                'allowed_domains': list(policy.network.allowed_domains),
                'denied_domains': list(policy.network.denied_domains),
                'allowed_ports': list(policy.network.allowed_ports),
                'denied_ports': list(policy.network.denied_ports),
                'request_timeout': policy.network.request_timeout,
                'max_response_size': policy.network.max_response_size,
                'verify_ssl': policy.network.verify_ssl,
                'rate_limit': policy.network.rate_limit,
                'audit_enabled': policy.network.audit_enabled
            }
        
        # Add injection patterns if present
        if policy.injection_patterns:
            policy_data['injection_patterns'] = []
            for pattern in policy.injection_patterns:
                policy_data['injection_patterns'].append({
                    'name': pattern.name,
                    'pattern': pattern.pattern,
                    'injection_type': pattern.injection_type.value,
                    'threat_level': pattern.threat_level.value,
                    'description': pattern.description,
                    'action': pattern.action.value
                })
        
        # Write to file
        with open(output_file, 'w') as f:
            yaml.dump(policy_data, f, default_flow_style=False, indent=2)
        
        logger.info(f"Saved security policy to {output_file}")
    
    def register_policy(self, policy: SecurityPolicy):
        """
        Register a security policy.
        
        Args:
            policy: SecurityPolicy to register
        """
        self.policies[policy.name] = policy
        logger.info(f"Registered security policy: {policy.name}")
    
    def activate_policy(self, policy_name: str) -> bool:
        """
        Activate a security policy by name.
        
        Args:
            policy_name: Name of policy to activate
            
        Returns:
            True if policy was activated successfully
        """
        if policy_name not in self.policies:
            logger.error(f"Policy not found: {policy_name}")
            return False
        
        self.active_policy = self.policies[policy_name]
        logger.info(f"Activated security policy: {policy_name}")
        return True
    
    def get_active_policy(self) -> Optional[SecurityPolicy]:
        """Get the currently active security policy."""
        return self.active_policy
    
    def list_policies(self) -> List[str]:
        """Get list of available policy names."""
        return list(self.policies.keys())
    
    def get_policy(self, policy_name: str) -> Optional[SecurityPolicy]:
        """Get a specific policy by name."""
        return self.policies.get(policy_name)
    
    def set_policy_override(self, scope: str, overrides: Dict[str, Any]):
        """
        Set policy overrides for specific scope (task, user, session).
        
        Args:
            scope: Scope identifier (task_id, user_id, session_id)
            overrides: Dictionary of policy overrides
        """
        self.policy_overrides[scope] = overrides
        logger.info(f"Set policy overrides for scope: {scope}")
    
    def clear_policy_override(self, scope: str):
        """Clear policy overrides for specific scope."""
        if scope in self.policy_overrides:
            del self.policy_overrides[scope]
            logger.info(f"Cleared policy overrides for scope: {scope}")
    
    def get_effective_policy(self, scope: Optional[str] = None) -> SecurityPolicy:
        """
        Get effective policy with any applicable overrides.
        
        Args:
            scope: Optional scope identifier for overrides
            
        Returns:
            Effective SecurityPolicy with overrides applied
        """
        if not self.active_policy:
            raise ValueError("No active security policy")
        
        # Start with active policy
        effective_policy = SecurityPolicy(
            name=f"{self.active_policy.name}_effective",
            version=self.active_policy.version,
            level=self.active_policy.level,
            scope=self.active_policy.scope,
            description=f"Effective policy based on {self.active_policy.name}",
            execution=ExecutionPolicy(**asdict(self.active_policy.execution)),
            filesystem=FilesystemPolicy(**asdict(self.active_policy.filesystem)) if self.active_policy.filesystem else None,
            network=NetworkPolicy(**asdict(self.active_policy.network)) if self.active_policy.network else None,
            injection_patterns=self.active_policy.injection_patterns.copy(),
            tags=self.active_policy.tags.copy(),
            enforce_all=self.active_policy.enforce_all,
            fail_open=self.active_policy.fail_open,
            audit_enabled=self.active_policy.audit_enabled,
            violation_threshold=self.active_policy.violation_threshold
        )
        
        # Apply overrides if scope is provided
        if scope and scope in self.policy_overrides:
            overrides = self.policy_overrides[scope]
            
            # Apply execution overrides
            if 'execution' in overrides:
                for key, value in overrides['execution'].items():
                    if hasattr(effective_policy.execution, key):
                        setattr(effective_policy.execution, key, value)
            
            # Apply filesystem overrides
            if 'filesystem' in overrides and effective_policy.filesystem:
                for key, value in overrides['filesystem'].items():
                    if hasattr(effective_policy.filesystem, key):
                        setattr(effective_policy.filesystem, key, value)
            
            # Apply network overrides
            if 'network' in overrides and effective_policy.network:
                for key, value in overrides['network'].items():
                    if hasattr(effective_policy.network, key):
                        setattr(effective_policy.network, key, value)
        
        return effective_policy
    
    def record_violation(self, violation: SecurityPolicyViolation):
        """
        Record a security policy violation.
        
        Args:
            violation: SecurityPolicyViolation to record
        """
        self.violations.append(violation)
        
        # Log violation based on severity
        log_level = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(violation.severity.lower(), logging.WARNING)
        
        logger.log(log_level, 
                  f"Security violation: {violation.violation_type} in {violation.component} - {violation.description}")
        
        # Check violation threshold
        if self.active_policy and len(self.violations) >= self.active_policy.violation_threshold:
            logger.critical(f"Violation threshold exceeded: {len(self.violations)} violations")
    
    def get_violations(self, limit: Optional[int] = None, 
                      component: Optional[str] = None) -> List[SecurityPolicyViolation]:
        """
        Get recorded security violations.
        
        Args:
            limit: Maximum number of violations to return
            component: Filter by component (execution, filesystem, network, injection)
            
        Returns:
            List of security violations
        """
        violations = self.violations
        
        if component:
            violations = [v for v in violations if v.component == component]
        
        if limit:
            violations = violations[-limit:]
        
        return violations
    
    def export_violations(self, output_file: str):
        """
        Export security violations to JSON file.
        
        Args:
            output_file: Path to output file
        """
        violations_data = []
        
        for violation in self.violations:
            violations_data.append({
                'timestamp': violation.timestamp.isoformat(),
                'policy_name': violation.policy_name,
                'violation_type': violation.violation_type,
                'severity': violation.severity,
                'description': violation.description,
                'component': violation.component,
                'user_id': violation.user_id,
                'session_id': violation.session_id,
                'task_id': violation.task_id,
                'metadata': violation.metadata
            })
        
        with open(output_file, 'w') as f:
            json.dump(violations_data, f, indent=2)
        
        logger.info(f"Exported {len(violations_data)} violations to {output_file}")
    
    def get_policy_statistics(self) -> Dict[str, Any]:
        """
        Get security policy statistics.
        
        Returns:
            Dictionary with policy statistics
        """
        stats = {
            'total_policies': len(self.policies),
            'active_policy': self.active_policy.name if self.active_policy else None,
            'total_violations': len(self.violations),
            'violations_by_component': {},
            'violations_by_severity': {},
            'policy_overrides_active': len(self.policy_overrides)
        }
        
        # Count violations by component and severity
        for violation in self.violations:
            component = violation.component
            severity = violation.severity
            
            stats['violations_by_component'][component] = stats['violations_by_component'].get(component, 0) + 1
            stats['violations_by_severity'][severity] = stats['violations_by_severity'].get(severity, 0) + 1
        
        return stats

# Global security policy manager
_policy_manager: Optional[SecurityPolicyManager] = None

def get_policy_manager(policy_dir: Optional[str] = None) -> SecurityPolicyManager:
    """Get the global security policy manager."""
    global _policy_manager
    if _policy_manager is None:
        _policy_manager = SecurityPolicyManager(policy_dir)
    return _policy_manager

def get_active_policy() -> Optional[SecurityPolicy]:
    """Get the currently active security policy."""
    manager = get_policy_manager()
    return manager.get_active_policy()

def activate_policy(policy_name: str) -> bool:
    """Activate a security policy by name."""
    manager = get_policy_manager()
    return manager.activate_policy(policy_name)