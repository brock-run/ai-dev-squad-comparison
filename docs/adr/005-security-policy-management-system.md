# ADR-005: Security Policy Management System

## Status
Accepted

## Date
2024-01-15

## Context

The AI Dev Squad Comparison platform requires a unified way to manage security policies across all security components (execution, filesystem, network, injection detection). We need a system that:

1. **Centralizes Policy Management**: Single source of truth for all security settings
2. **Supports Multiple Environments**: Different policies for dev, staging, production
3. **Enables Dynamic Configuration**: Runtime policy changes without restarts
4. **Provides Policy Validation**: Ensures policy configurations are valid and secure
5. **Maintains Audit Trail**: Complete history of policy changes and violations
6. **Supports Policy Templates**: Pre-built policies for common security levels

## Decision

We will implement a **unified security policy management system** with the following components:

### Core Components

1. **SecurityPolicyManager**: Central policy management and enforcement
2. **SecurityPolicy**: Unified policy configuration object
3. **Policy Templates**: Pre-built policies for different security levels
4. **Policy Validation**: Configuration validation and security checks
5. **Violation Tracking**: Audit trail for policy violations
6. **Dynamic Updates**: Runtime policy changes with validation

### Policy Hierarchy

```
SecurityPolicy
├── ExecutionPolicyConfig
├── FilesystemPolicyConfig  
├── NetworkPolicyConfig
└── InjectionPolicyConfig
```

### Built-in Policy Levels

1. **Disabled**: All security controls off (testing only)
2. **Permissive**: Minimal restrictions (development)
3. **Standard**: Balanced security (default production)
4. **Strict**: High security (sensitive environments)
5. **Paranoid**: Maximum security (high-risk environments)

## Alternatives Considered

### 1. Separate Policy Files per Component
**Rejected**: Would lead to configuration drift and inconsistencies between security components.

### 2. Database-Stored Policies
**Rejected**: Adds complexity and external dependencies. File-based configuration is simpler and more portable.

### 3. Environment Variables Only
**Rejected**: Not suitable for complex nested configurations. Difficult to manage and validate.

### 4. External Policy Service
**Rejected**: Introduces network dependencies and latency. Our use case requires local policy enforcement.

### 5. Hardcoded Security Levels
**Rejected**: Not flexible enough for different organizational needs and custom security requirements.

## Consequences

### Positive
- **Consistency**: All security components use the same policy framework
- **Flexibility**: Custom policies can be created for specific needs
- **Auditability**: Complete visibility into policy changes and violations
- **Maintainability**: Centralized policy management reduces configuration complexity
- **Validation**: Built-in validation prevents misconfigurations

### Negative
- **Complexity**: Unified system requires careful design to handle all security domains
- **Migration**: Existing configurations need to be migrated to new format
- **Performance**: Policy validation adds overhead to configuration changes
- **Learning Curve**: Users need to understand the unified policy structure

## Policy Structure

### SecurityPolicy Configuration
```python
@dataclass
class SecurityPolicy:
    name: str
    level: PolicyLevel
    description: str
    execution: ExecutionPolicyConfig
    filesystem: FilesystemPolicyConfig
    network: NetworkPolicyConfig
    injection: InjectionPolicyConfig
    metadata: Dict[str, Any]
    created_at: datetime
```

### Policy Level Definitions

#### Disabled Policy
- All security controls disabled
- For testing and development only
- No restrictions on any operations

#### Permissive Policy
- Minimal security restrictions
- Suitable for development environments
- Allows most operations with basic logging

#### Standard Policy (Default)
- Balanced security for production use
- Docker sandbox with network isolation
- Filesystem restricted to repository
- Basic injection detection enabled

#### Strict Policy
- High security for sensitive environments
- Reduced resource limits
- Limited file extensions allowed
- Enhanced injection detection

#### Paranoid Policy
- Maximum security for high-risk environments
- Minimal resource allocation
- No network access
- Aggressive injection detection

## Implementation Details

### Policy Manager Interface
```python
class SecurityPolicyManager:
    def get_policy(self, name: str) -> Optional[SecurityPolicy]
    def set_active_policy(self, name: str) -> bool
    def create_custom_policy(self, name: str, **kwargs) -> SecurityPolicy
    def validate_policy(self, policy: SecurityPolicy) -> List[str]
    def record_violation(self, domain: PolicyDomain, **kwargs)
    def get_violations(self, domain: Optional[PolicyDomain] = None) -> List[PolicyViolation]
```

### Policy File Format (YAML)
```yaml
name: "custom-policy"
level: "standard"
description: "Custom policy for specific use case"
execution:
  enabled: true
  sandbox_type: "docker"
  max_memory_mb: 1024
  timeout_seconds: 300
filesystem:
  enabled: true
  restrict_to_repo: true
  max_file_size_mb: 100
network:
  enabled: true
  default_deny: true
  allowed_domains:
    - "api.github.com"
injection:
  enabled: true
  block_critical: true
  block_high: true
```

### Policy Validation Rules

1. **Resource Limits**: Ensure reasonable resource allocations
2. **Security Consistency**: Validate security level consistency
3. **File Path Validation**: Check file paths exist and are accessible
4. **Network Configuration**: Validate domain and port configurations
5. **Injection Patterns**: Verify pattern files exist and are valid

## Violation Tracking

### PolicyViolation Structure
```python
@dataclass
class PolicyViolation:
    timestamp: datetime
    domain: PolicyDomain
    policy_name: str
    violation_type: str
    severity: str
    description: str
    user_id: Optional[str]
    session_id: Optional[str]
    metadata: Dict[str, Any]
```

### Violation Categories
- **Execution Violations**: Resource limit exceeded, forbidden operations
- **Filesystem Violations**: Unauthorized file access, size limits exceeded
- **Network Violations**: Blocked domains, rate limits exceeded
- **Injection Violations**: Detected prompt injection attempts

## Configuration Integration

### Integration with Existing Config System
```python
# config_integration.py
def apply_security_policy(config: SystemConfig, policy: SecurityPolicy):
    """Apply security policy to system configuration"""
    
def validate_security_config(config: SystemConfig) -> List[str]:
    """Validate security configuration"""
```

### Environment-Specific Policies
- Development: `policies/development.yaml`
- Staging: `policies/staging.yaml`
- Production: `policies/production.yaml`
- Custom: `policies/custom/*.yaml`

## Usage Examples

### Setting Active Policy
```python
from common.safety.policy import get_policy_manager

manager = get_policy_manager()
manager.set_active_policy("strict")
```

### Creating Custom Policy
```python
custom_policy = manager.create_custom_policy(
    name="api-testing",
    level=PolicyLevel.PERMISSIVE,
    description="Policy for API testing",
    network=NetworkPolicyConfig(
        allowed_domains={"httpbin.org", "jsonplaceholder.typicode.com"}
    )
)
```

### Monitoring Violations
```python
violations = manager.get_violations(domain=PolicyDomain.NETWORK)
for violation in violations[-10:]:  # Last 10 violations
    print(f"{violation.timestamp}: {violation.description}")
```

## Monitoring and Reporting

### Policy Statistics
- Active policy usage
- Violation counts by domain
- Policy change history
- Security level distribution

### Automated Reports
- Daily security summaries
- Policy violation trends
- Configuration drift detection
- Security posture assessments

## Testing Strategy

- Unit tests for policy validation logic
- Integration tests with all security components
- Policy template validation tests
- Violation tracking accuracy tests
- Performance tests for policy enforcement

## Migration Strategy

### From Existing Configuration
1. Parse existing security configurations
2. Map to new policy structure
3. Validate converted policies
4. Provide migration scripts
5. Maintain backward compatibility during transition

## Related ADRs

- ADR-001: Security Architecture Approach
- ADR-002: Execution Sandbox Implementation
- ADR-003: Network Access Control Strategy
- ADR-004: Prompt Injection Detection Approach