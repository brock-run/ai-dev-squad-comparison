# ADR-003: Network Access Control Strategy

## Status
Accepted

## Date
2024-01-15

## Context

AI agents may need to make network requests for legitimate purposes (API calls, data fetching), but unrestricted network access poses significant security risks:

1. **Data Exfiltration**: Agents could send sensitive data to external servers
2. **Lateral Movement**: Access to internal network resources
3. **DoS Attacks**: Overwhelming external services with requests
4. **Malicious Downloads**: Fetching and executing malicious code
5. **Information Disclosure**: Probing internal network topology

We need a network access control system that allows legitimate use while preventing abuse.

## Decision

We will implement a **allowlist-based network access control system** with the following components:

### Core Components

1. **Domain Allowlist**: Explicit list of allowed domains/hosts
2. **Port Restrictions**: Control which ports can be accessed
3. **Rate Limiting**: Prevent abuse through request throttling
4. **Request Inspection**: Log and analyze all network requests
5. **SSL/TLS Enforcement**: Require secure connections where possible

### Implementation Approach

```python
class NetworkPolicy:
    def __init__(self, config: NetworkConfig)
    def is_request_allowed(self, url: str, method: str) -> bool
    def apply_rate_limit(self, domain: str) -> bool
    def log_request(self, request: NetworkRequest, allowed: bool)
```

### Default Security Posture
- **Default Deny**: All network access blocked unless explicitly allowed
- **Secure Protocols**: HTTPS preferred over HTTP
- **Rate Limiting**: Per-domain request limits to prevent abuse
- **Audit Logging**: All network requests logged for security monitoring

## Alternatives Considered

### 1. Complete Network Isolation
**Rejected**: Too restrictive for legitimate AI agent use cases that require API access or data fetching.

### 2. Proxy-Based Filtering
**Rejected**: Adds complexity and potential single point of failure. Requires additional infrastructure.

### 3. DNS-Based Blocking
**Rejected**: Can be bypassed using IP addresses. Doesn't provide fine-grained control over ports and protocols.

### 4. Firewall Rules Only
**Rejected**: OS-level firewall rules are not portable and don't provide application-level logging and rate limiting.

### 5. VPN/Network Namespace Isolation
**Rejected**: Too complex for the use case and would require significant infrastructure changes.

## Consequences

### Positive
- **Controlled Access**: Only explicitly allowed network resources are accessible
- **Abuse Prevention**: Rate limiting prevents DoS and excessive usage
- **Audit Trail**: Complete visibility into network activity
- **Flexibility**: Policies can be customized per environment
- **Performance**: Minimal overhead for allowed requests

### Negative
- **Configuration Overhead**: Requires maintaining allowlists of permitted domains
- **Potential Blocking**: Legitimate requests may be blocked if not properly configured
- **Maintenance**: Allowlists need regular updates as requirements change
- **Complexity**: Additional layer that needs monitoring and troubleshooting

## Security Features

### Domain Validation
- Exact domain matching (api.github.com)
- Subdomain wildcards (*.github.com) with careful validation
- IP address restrictions (no direct IP access by default)
- Punycode/IDN attack prevention

### Rate Limiting
- Per-domain request limits (e.g., 60 requests/minute)
- Sliding window algorithm for smooth rate limiting
- Burst allowance for legitimate high-frequency use cases
- Exponential backoff for repeated violations

### Request Inspection
- URL and method logging
- Request/response size monitoring
- SSL certificate validation
- Suspicious pattern detection

## Configuration Examples

### Strict Policy (Production)
```yaml
network:
  enabled: true
  default_deny: true
  allowed_domains:
    - "api.github.com"
    - "api.gitlab.com"
  allowed_ports: [443]
  rate_limit: 30
  verify_ssl: true
```

### Permissive Policy (Development)
```yaml
network:
  enabled: true
  default_deny: false
  denied_domains:
    - "malicious-site.com"
  allowed_ports: [80, 443, 8080]
  rate_limit: 120
  verify_ssl: false
```

## Implementation Details

### Request Interception
- HTTP library monkey-patching (requests, urllib)
- Custom session objects with built-in policy enforcement
- Transparent integration with existing code

### Rate Limiting Algorithm
```python
class RateLimiter:
    def __init__(self, requests_per_minute: int)
    def is_allowed(self, domain: str) -> bool
    def record_request(self, domain: str)
```

### Audit Logging
- Request timestamp and duration
- Source domain and destination
- HTTP method and response code
- Request/response sizes
- Policy decision (allowed/denied)

## Monitoring and Alerting

### Metrics
- Requests per domain/minute
- Policy violation counts
- Rate limit hit frequency
- SSL verification failures

### Alerts
- Repeated policy violations
- Unusual traffic patterns
- High rate limit usage
- SSL/TLS security issues

## Testing Strategy

- Unit tests for policy evaluation logic
- Integration tests with real HTTP requests
- Security tests for bypass attempts
- Performance tests for rate limiting
- Mock server tests for various scenarios

## Related ADRs

- ADR-001: Security Architecture Approach
- ADR-002: Execution Sandbox Implementation
- ADR-005: Security Policy Management System