# ADR-006: VCS Integration Architecture

## Status
Accepted

## Date
2024-01-15

## Context

The AI Dev Squad Comparison platform requires robust integration with multiple Version Control Systems (VCS) to enable AI agents to:

1. **Create and manage branches** for isolated development work
2. **Commit code changes** atomically with proper attribution
3. **Create pull/merge requests** with templates and automation
4. **Handle different VCS providers** (GitHub, GitLab, Bitbucket, etc.)
5. **Manage authentication** securely across different token types
6. **Handle rate limits** and API failures gracefully
7. **Provide unified interface** while supporting provider-specific features

The challenge was designing a system that provides a consistent interface across different VCS providers while still allowing access to provider-specific features like GitLab's approval workflows or GitHub's status checks.

## Decision

We will implement a **layered VCS integration architecture** with the following components:

### 1. Base Protocol Layer (`common/vcs/base.py`)
- **VCSProviderProtocol**: Abstract protocol defining common VCS operations
- **BaseVCSProvider**: Shared implementation with retry logic, rate limiting, and metrics
- **Common Data Models**: Repository, Branch, Commit, PullRequest classes
- **Retry Middleware**: Exponential backoff with jitter and rate limit awareness
- **Rate Limit Manager**: Cross-provider rate limit tracking and enforcement

### 2. Provider-Specific Implementations
- **GitHubProvider** (`common/vcs/github.py`): GitHub REST API v4 integration
- **GitLabProvider** (`common/vcs/gitlab.py`): GitLab REST API v4 integration
- **Future providers**: Bitbucket, Azure DevOps, etc.

### 3. Unified Interface with Provider Extensions
- **Common Operations**: All providers implement the same core interface
- **Provider-Specific Extensions**: Additional methods for unique features
- **Polymorphic Usage**: Clients can use any provider through the same interface
- **Feature Detection**: Runtime detection of provider capabilities

### Architecture Principles

#### Abstraction Strategy
- **Common Interface**: All providers implement VCSProviderProtocol
- **Provider Extensions**: Additional methods for provider-specific features
- **Graceful Degradation**: Fallback behavior when features aren't available
- **Type Safety**: Full type hints including provider-specific types

#### Error Handling Strategy
- **Hierarchical Exceptions**: Base VCSError with provider-specific subclasses
- **Retry Logic**: Intelligent retry with exponential backoff and jitter
- **Rate Limit Handling**: Provider-specific rate limit parsing and waiting
- **Circuit Breaking**: Fail-fast when providers are consistently unavailable

#### Authentication Strategy
- **Multiple Token Types**: Support for PATs, OAuth, App tokens, Deploy tokens
- **Secure Storage**: Token encryption and secure handling
- **Scope Management**: Automatic detection of required permissions
- **Token Validation**: Format validation before API calls

## Alternatives Considered

### 1. Single Unified API Client
**Rejected**: Would require lowest-common-denominator approach, losing provider-specific features like GitLab approvals or GitHub status checks.

### 2. Separate Libraries per Provider
**Rejected**: Would create code duplication and inconsistent interfaces. No shared retry logic or rate limiting.

### 3. Adapter Pattern Only
**Rejected**: Pure adapter pattern wouldn't provide shared functionality like retry logic, metrics, and rate limiting that all providers need.

### 4. GraphQL-First Approach
**Rejected**: Not all providers support GraphQL (GitLab's GraphQL is limited), and REST APIs are more stable and feature-complete.

### 5. External VCS Abstraction Library
**Rejected**: Existing libraries don't provide the level of control needed for AI agent workflows, and don't handle our specific requirements like template systems and atomic multi-file commits.

## Consequences

### Positive
- **Consistent Interface**: AI agents can work with any VCS provider using the same code
- **Provider Features**: Full access to provider-specific features when needed
- **Robust Error Handling**: Comprehensive retry logic and rate limit management
- **Extensibility**: Easy to add new VCS providers following the established pattern
- **Observability**: Built-in metrics, logging, and monitoring for all VCS operations
- **Security**: Consistent authentication and token management across providers

### Negative
- **Complexity**: Multiple layers and abstractions increase system complexity
- **Maintenance Overhead**: Need to maintain compatibility with multiple VCS APIs
- **Testing Complexity**: Comprehensive testing required for each provider
- **Learning Curve**: Developers need to understand both common interface and provider specifics

## Implementation Details

### Common Interface Example
```python
# All providers implement this interface
async def create_pull_request(
    self, owner: str, repo: str,
    title: str, description: str,
    source_branch: str, target_branch: str = "main",
    draft: bool = False,
    template_name: str = "default"
) -> PullRequest
```

### Provider-Specific Extensions
```python
# GitLab-specific approval methods
async def approve_merge_request(
    self, owner: str, repo: str, number: int
) -> Dict[str, Any]

# GitHub-specific status checks
async def create_commit_status(
    self, owner: str, repo: str, sha: str,
    state: str, context: str = "default"
) -> Dict[str, Any]
```

### Retry and Rate Limiting
```python
# Shared across all providers
class RetryMiddleware:
    async def execute_with_retry(self, func, *args, **kwargs)

class RateLimitManager:
    def is_rate_limited(self, provider: str) -> bool
    def get_wait_time(self, provider: str) -> int
```

### Template System
```python
# Consistent template system across providers
def set_pr_template(self, template_name: str, content: str)
def get_pr_template(self, template_name: str = "default") -> str
```

## Provider-Specific Considerations

### GitHub Integration
- **Authentication**: Personal Access Tokens, GitHub App tokens, fine-grained PATs
- **Rate Limits**: Core API (5000/hour), Search API (30/minute), GraphQL (5000/hour)
- **Unique Features**: Status checks, GitHub Actions integration, security advisories
- **API Characteristics**: Mature REST API, comprehensive GraphQL API

### GitLab Integration
- **Authentication**: Personal Access Tokens, OAuth tokens, Deploy tokens
- **Rate Limits**: 2000 requests/minute for GitLab.com, configurable for self-hosted
- **Unique Features**: Approval workflows, built-in CI/CD, merge request discussions
- **API Characteristics**: Comprehensive REST API, limited GraphQL API
- **Self-Hosted Support**: Full support for GitLab CE/EE instances

### Shared Patterns
- **Multi-File Commits**: Atomic commits using provider-specific APIs
- **Branch Management**: Consistent branch creation, deletion, and protection
- **Template Systems**: Customizable PR/MR templates with variable substitution
- **Error Recovery**: Intelligent retry with provider-specific error handling

## Security Considerations

### Token Management
- **Encryption**: All tokens encrypted at rest
- **Scope Validation**: Verify tokens have required permissions
- **Rotation**: Support for token rotation and refresh
- **Audit Logging**: Complete audit trail of token usage

### API Security
- **SSL/TLS**: Enforce secure connections to all VCS providers
- **Request Signing**: Use provider-specific request signing when available
- **Rate Limiting**: Respect and enforce provider rate limits
- **Input Validation**: Sanitize all inputs to prevent injection attacks

## Monitoring and Observability

### Metrics Collection
- **Request Metrics**: Success rates, response times, retry counts
- **Rate Limit Tracking**: Usage against limits, reset times
- **Error Tracking**: Error types, frequencies, and patterns
- **Provider Health**: Availability and performance monitoring

### Logging Strategy
- **Structured Logging**: JSON-formatted logs with consistent schema
- **Request Tracing**: Complete request/response logging (excluding sensitive data)
- **Error Context**: Rich error context for debugging
- **Performance Monitoring**: Slow query detection and optimization

## Testing Strategy

### Unit Testing
- **Provider Interface**: Test all common interface methods
- **Error Handling**: Test all error scenarios and recovery
- **Authentication**: Test all token types and validation
- **Rate Limiting**: Test rate limit detection and handling

### Integration Testing
- **Live API Testing**: Test against real VCS provider APIs (with test accounts)
- **Mock Testing**: Comprehensive mocking for CI/CD environments
- **Error Simulation**: Simulate various failure scenarios
- **Performance Testing**: Load testing and rate limit validation

### End-to-End Testing
- **Complete Workflows**: Test full branch → commit → PR → merge workflows
- **Multi-Provider**: Test switching between different VCS providers
- **Template Systems**: Test PR/MR template functionality
- **Authentication Flows**: Test all authentication methods

## Migration and Compatibility

### Backward Compatibility
- **Interface Stability**: Maintain stable interfaces for existing code
- **Deprecation Strategy**: Gradual deprecation of old interfaces
- **Version Management**: Semantic versioning for VCS integration APIs

### Provider Updates
- **API Version Management**: Handle VCS provider API version changes
- **Feature Detection**: Runtime detection of new provider features
- **Graceful Degradation**: Fallback when new features aren't available

## Future Considerations

### Additional Providers
- **Bitbucket**: Atlassian Bitbucket Cloud and Server
- **Azure DevOps**: Microsoft Azure Repos
- **Gitea/Forgejo**: Self-hosted Git services
- **AWS CodeCommit**: Amazon's Git service

### Advanced Features
- **Webhook Integration**: Real-time event processing
- **Advanced Workflows**: Multi-repository operations
- **Compliance Integration**: SOC2, FedRAMP compliance features
- **AI-Specific Features**: AI agent attribution and tracking

## Related ADRs

- ADR-001: Security Architecture Approach
- ADR-002: Execution Sandbox Implementation
- ADR-003: Network Access Control Strategy
- ADR-005: Security Policy Management System

## References

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [GitLab REST API Documentation](https://docs.gitlab.com/ee/api/)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)