# VCS Integration Guide

This guide covers the Version Control System (VCS) integration capabilities of the AI Dev Squad Comparison platform, including setup, usage, and best practices for working with GitHub, GitLab, and other VCS providers.

## Overview

The VCS integration system provides a unified interface for AI agents to interact with various version control systems while maintaining access to provider-specific features. The system supports:

- **Multiple VCS Providers**: GitHub, GitLab, with extensible architecture for additional providers
- **Unified Interface**: Consistent API across all providers for common operations
- **Provider-Specific Features**: Access to unique features like GitLab approvals or GitHub status checks
- **Robust Error Handling**: Intelligent retry logic, rate limiting, and comprehensive error recovery
- **Security**: Secure token management, encryption, and audit logging
- **Observability**: Comprehensive metrics, logging, and monitoring

## Supported Providers

### GitHub
- **API Version**: REST API v4, GraphQL API v4
- **Authentication**: Personal Access Tokens, GitHub App tokens, Fine-grained PATs
- **Unique Features**: Status checks, GitHub Actions integration, security advisories
- **Rate Limits**: 5000 requests/hour (authenticated), 60 requests/hour (unauthenticated)

### GitLab
- **API Version**: REST API v4
- **Authentication**: Personal Access Tokens, OAuth tokens, Deploy tokens
- **Unique Features**: Approval workflows, built-in CI/CD, merge request discussions
- **Rate Limits**: 2000 requests/minute (GitLab.com), configurable (self-hosted)
- **Self-Hosted**: Full support for GitLab CE/EE instances

## Commit Message Generation

The VCS integration includes an intelligent commit message generator that analyzes diffs and creates meaningful commit messages automatically:

- **Multiple Styles**: Conventional commits, Gitmoji, Simple, and Detailed formats
- **Intelligent Analysis**: Automatic commit type detection based on file changes
- **Context Awareness**: Scope detection, language identification, and breaking change detection
- **Performance Caching**: Caches generated messages for improved performance
- **Customizable Templates**: Configurable templates for different commit types and styles
- **Validation**: Built-in validation against configurable rules

## Quick Start

### Basic Usage

```python
from common.vcs import GitHubProvider, GitLabProvider

# GitHub integration
async with GitHubProvider() as github:
    await github.authenticate(github_token)
    
    # Create branch and commit changes
    branch = await github.create_branch("owner", "repo", "feature/new-feature")
    commit = await github.commit_changes(
        "owner", "repo", "feature/new-feature",
        "Add new feature", {"file.py": "print('Hello, World!')"}
    )
    
    # Create pull request
    pr = await github.create_pull_request(
        "owner", "repo", "Add New Feature",
        "This PR adds a new feature", "feature/new-feature"
    )

# GitLab integration
async with GitLabProvider() as gitlab:
    await gitlab.authenticate(gitlab_token)
    
    # Same interface, different provider
    branch = await gitlab.create_branch("owner", "project", "feature/new-feature")
    commit = await gitlab.commit_changes(
        "owner", "project", "feature/new-feature",
        "Add new feature", {"file.py": "print('Hello, World!')"}
    )
    
    # Create merge request with GitLab-specific features
    mr = await gitlab.create_pull_request(
        "owner", "project", "Add New Feature",
        "This MR adds a new feature", "feature/new-feature"
    )
    
    # GitLab-specific: Approve merge request
    await gitlab.approve_merge_request("owner", "project", mr.iid)
```

### Configuration

Create configuration files for each VCS provider:

#### GitHub Configuration (`config/github.yaml`)
```yaml
github:
  base_url: "https://api.github.com"
  auth:
    token: "${GITHUB_TOKEN}"
    type: "pat"
  retry:
    max_retries: 3
    base_delay: 1.0
  pr_templates:
    default: |
      ## Description
      {description}
      
      ## Type of Change
      - [ ] Bug fix
      - [ ] New feature
      - [ ] Breaking change
      - [ ] Documentation update
```

#### GitLab Configuration (`config/gitlab.yaml`)
```yaml
gitlab:
  base_url: "https://gitlab.com/api/v4"
  auth:
    token: "${GITLAB_TOKEN}"
    type: "pat"
  retry:
    max_retries: 3
    base_delay: 1.0
  mr_templates:
    default: |
      ## Description
      {description}
      
      ## Type of Change
      - [ ] Bug fix
      - [ ] New feature
      - [ ] Breaking change
      - [ ] Documentation update
      
      ## Pipeline
      - [ ] Pipeline passes
```

## Authentication

### GitHub Authentication

#### Personal Access Tokens (Recommended)
```python
# Classic PAT (40 characters)
github_token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Fine-grained PAT (starts with github_pat_)
github_token = "github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

await github.authenticate(github_token)
```

#### GitHub App Tokens
```python
# GitHub App installation token
github_token = "ghs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

await github.authenticate(github_token)
```

#### Required Scopes
- `repo` - Full repository access
- `pull_requests:write` - Create and update PRs
- `contents:write` - Create and update files
- `metadata:read` - Read repository metadata

### GitLab Authentication

#### Personal Access Tokens
```python
# GitLab PAT (starts with glpat-)
gitlab_token = "glpat-xxxxxxxxxxxxxxxxxxxx"

await gitlab.authenticate(gitlab_token)
```

#### OAuth Tokens
```python
# OAuth application secret
gitlab_token = "gloas-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

await gitlab.authenticate(gitlab_token)
```

#### Deploy Tokens
```python
# Deploy token (starts with gldt-)
gitlab_token = "gldt-xxxxxxxxxxxxxxxxxxxx"

await gitlab.authenticate(gitlab_token)
```

#### Required Scopes
- `api` - Full API access
- `read_repository` - Read repository content
- `write_repository` - Write repository content
- `read_user` - Read user information

## Common Operations

### Repository Management

```python
# Get repository information
repo = await provider.get_repository("owner", "repo")
print(f"Repository: {repo.full_name}")
print(f"Default branch: {repo.default_branch}")
print(f"Private: {repo.private}")

# List branches
branches = await provider.list_branches("owner", "repo")
for branch in branches:
    print(f"Branch: {branch.name} ({branch.sha[:8]})")

# Create new branch
new_branch = await provider.create_branch(
    "owner", "repo", "feature/new-feature", "main"
)
```

### File Operations

```python
# Get file content
file_data = await provider.get_file_content("owner", "repo", "README.md")
content = file_data['decoded_content']

# Create or update single file
await provider.create_or_update_file(
    "owner", "repo", "new-file.txt",
    "File content", "Add new file", "main"
)

# Commit multiple files atomically
files = {
    "src/main.py": "print('Hello, World!')",
    "src/utils.py": "def helper(): pass",
    "README.md": "# My Project\n\nDescription here."
}

commit = await provider.commit_changes(
    "owner", "repo", "feature/new-feature",
    "Add project structure", files,
    "AI Agent", "ai@example.com"
)
```

### Pull/Merge Request Workflow

```python
# Create PR/MR with template
pr = await provider.create_pull_request(
    "owner", "repo",
    "Add New Feature",
    "This adds a new feature to the project",
    "feature/new-feature", "main",
    draft=False,
    template_name="feature"
)

# Add comment
await provider.add_pr_comment(
    "owner", "repo", pr.number,
    "This looks good! Ready for review."
)

# Update PR/MR
updated_pr = await provider.update_pull_request(
    "owner", "repo", pr.number,
    title="[UPDATED] Add New Feature",
    description="Updated description with more details"
)

# Merge PR/MR
merge_result = await provider.merge_pull_request(
    "owner", "repo", pr.number,
    commit_title="Merge feature branch",
    merge_method="squash"
)
```

### Commit Message Generation

```python
from common.vcs import generate_commit_message, CommitMessageConfig, MessageStyle

# Generate commit message from diff
diff_text = """diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,10 @@
+def authenticate(username, password):
+    # New authentication function
+    return validate_credentials(username, password)
"""

# Simple generation
message = generate_commit_message(diff_text)
print(message)  # "feat(auth): add authentication function"

# Custom configuration
config = CommitMessageConfig(
    style=MessageStyle.GITMOJI,
    require_scope=True,
    include_stats=True
)
message = generate_commit_message(diff_text, config)
print(message)  # "✨ add authentication function"

# Multiple suggestions
from common.vcs import suggest_commit_messages
suggestions = suggest_commit_messages(diff_text, count=3)
for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion}")

# Use with VCS providers
commit = await provider.commit_changes(
    "owner", "repo", "feature/auth",
    generate_commit_message(diff_text), files
)
```

## Provider-Specific Features

### GitHub-Specific Features

#### Status Checks
```python
# Create commit status
await github.create_commit_status(
    "owner", "repo", commit_sha,
    state="success",
    description="All tests passed",
    context="continuous-integration"
)

# Get commit status
status = await github.get_commit_status("owner", "repo", commit_sha)
```

#### Reviews
```python
# Create PR review
await github.create_pr_review(
    "owner", "repo", pr_number,
    event="APPROVE",
    body="Looks good to me!"
)

# Get PR reviews
reviews = await github.get_pr_reviews("owner", "repo", pr_number)
```

### GitLab-Specific Features

#### Approval Workflow
```python
# Get approval information
approvals = await gitlab.get_mr_approvals("owner", "project", mr_iid)
print(f"Approvals required: {approvals['approvals_required']}")
print(f"Approvals received: {len(approvals['approved_by'])}")

# Approve merge request
await gitlab.approve_merge_request("owner", "project", mr_iid)

# Remove approval
await gitlab.unapprove_merge_request("owner", "project", mr_iid)
```

#### Pipeline Integration
```python
# Get pipeline status
pipeline = await gitlab.get_pipeline_status("owner", "project", commit_sha)
print(f"Pipeline status: {pipeline['status']}")

# Create new pipeline
new_pipeline = await gitlab.create_pipeline(
    "owner", "project", "main",
    variables={"DEPLOY_ENV": "staging"}
)

# Check if MR can be merged
mr = await gitlab.get_pull_request("owner", "project", mr_iid)
if isinstance(mr, MergeRequest) and mr.can_merge:
    await gitlab.merge_pull_request("owner", "project", mr_iid)
```

#### Project Management
```python
# Get project information
project_info = await gitlab.get_project_info("owner", "project")
print(f"Project ID: {project_info['id']}")
print(f"Visibility: {project_info['visibility']}")

# List project members
members = await gitlab.list_project_members("owner", "project")
for member in members:
    print(f"Member: {member['username']} (Level: {member['access_level']})")
```

## Template System

### PR/MR Templates

Both GitHub and GitLab providers support customizable templates:

```python
# Set custom template
provider.set_pr_template("feature", """
## 🚀 Feature Description
{description}

## 📋 Type of Change
- [ ] ✨ New feature
- [ ] 🐛 Bug fix
- [ ] 💥 Breaking change
- [ ] 📚 Documentation

## 🧪 Testing
- [ ] Tests pass locally
- [ ] New tests added

## 📝 Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
""")

# Use template when creating PR/MR
pr = await provider.create_pull_request(
    "owner", "repo", "Add Feature",
    "This adds a new authentication feature",
    "feature/auth", "main",
    template_name="feature"
)
```

### Built-in Templates

- **default**: Basic template with common sections
- **feature**: Enhanced template for new features
- **bugfix**: Template focused on bug fixes
- **docs**: Template for documentation updates

## Error Handling

### Retry Logic

The VCS integration includes intelligent retry logic:

```python
from common.vcs.base import RetryConfig

# Custom retry configuration
retry_config = RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0,
    exponential_base=2.0,
    jitter=True,
    retry_on_rate_limit=True
)

provider = GitHubProvider(retry_config=retry_config)
```

### Error Types

```python
from common.vcs import (
    VCSError, AuthenticationError, NotFoundError,
    PermissionError, RateLimitError
)

try:
    await provider.get_repository("owner", "repo")
except AuthenticationError:
    print("Invalid or expired token")
except NotFoundError:
    print("Repository not found or not accessible")
except PermissionError:
    print("Insufficient permissions")
except RateLimitError as e:
    print(f"Rate limited, reset in {e.reset_time}")
except VCSError as e:
    print(f"VCS error: {e}")
```

### Rate Limiting

```python
# Check rate limit status
rate_limit = provider.rate_limit_manager.get_rate_limit("github")
if rate_limit:
    print(f"Remaining: {rate_limit.remaining}/{rate_limit.limit}")
    print(f"Reset: {rate_limit.reset_time}")

# Wait for rate limit reset
if provider.rate_limit_manager.is_rate_limited("github"):
    wait_time = provider.rate_limit_manager.get_wait_time("github")
    print(f"Rate limited, waiting {wait_time} seconds")
    await asyncio.sleep(wait_time)
```

## Monitoring and Observability

### Metrics Collection

```python
# Get provider metrics
metrics = provider.get_metrics()  # or get_github_metrics(), get_gitlab_metrics()

print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Average response time: {metrics['average_response_time_ms']:.2f}ms")
print(f"Request rate: {metrics['request_rate_per_minute']:.2f} req/min")
print(f"Recent requests: {metrics['recent_requests']}")

# Export metrics to file
provider.export_metrics("vcs_metrics.json")
```

### Logging Configuration

```python
import logging

# Configure VCS logging
logging.getLogger('common.vcs').setLevel(logging.INFO)

# Enable request logging
logging.getLogger('common.vcs.github').setLevel(logging.DEBUG)
logging.getLogger('common.vcs.gitlab').setLevel(logging.DEBUG)
```

## Best Practices

### Security
1. **Use environment variables** for tokens, never hardcode them
2. **Use minimal scopes** required for your operations
3. **Rotate tokens regularly** and monitor for unauthorized usage
4. **Enable audit logging** for compliance and security monitoring

### Performance
1. **Use async/await** patterns for concurrent operations
2. **Implement caching** for frequently accessed data
3. **Respect rate limits** and implement backoff strategies
4. **Use batch operations** when available (multi-file commits)

### Error Handling
1. **Implement retry logic** with exponential backoff
2. **Handle rate limits gracefully** with appropriate delays
3. **Log errors with context** for debugging and monitoring
4. **Provide fallback strategies** when possible

### Testing
1. **Use mock providers** for unit tests
2. **Test with real APIs** in integration tests (with test accounts)
3. **Test error scenarios** including rate limits and network failures
4. **Validate token permissions** before operations

## Troubleshooting

### Common Issues

#### Authentication Failures
```bash
# Check token format
python -c "from common.vcs import validate_github_token; print(validate_github_token('your-token'))"

# Test authentication
python -c "
import asyncio
from common.vcs import GitHubProvider
async def test():
    async with GitHubProvider() as gh:
        result = await gh.authenticate('your-token')
        print(f'Auth result: {result}')
asyncio.run(test())
"
```

#### Rate Limiting
```bash
# Check current rate limits
python -c "
import asyncio
from common.vcs import GitHubProvider
async def check():
    async with GitHubProvider() as gh:
        await gh.authenticate('your-token')
        limits = await gh.get_rate_limit_status()
        print(limits)
asyncio.run(check())
"
```

#### Network Issues
```bash
# Test connectivity
curl -H "Authorization: Bearer your-token" https://api.github.com/user
curl -H "Private-Token: your-token" https://gitlab.com/api/v4/user
```

### Debug Mode

Enable debug logging for detailed request/response information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will log all HTTP requests and responses
provider = GitHubProvider()
```

## Migration Guide

### From Direct API Usage

If you're currently using VCS APIs directly:

```python
# Before: Direct GitHub API usage
import requests
response = requests.post(
    "https://api.github.com/repos/owner/repo/pulls",
    headers={"Authorization": f"Bearer {token}"},
    json={"title": "My PR", "head": "feature", "base": "main"}
)

# After: Using VCS integration
async with GitHubProvider() as github:
    await github.authenticate(token)
    pr = await github.create_pull_request(
        "owner", "repo", "My PR", "Description", "feature", "main"
    )
```

### From Other VCS Libraries

The VCS integration provides a more comprehensive and AI-agent-focused interface than general-purpose libraries, with built-in retry logic, rate limiting, and template systems.

## Examples

See the `examples/` directory for complete working examples:

- `examples/github_demo.py` - Comprehensive GitHub integration demo
- `examples/gitlab_demo.py` - Comprehensive GitLab integration demo
- `examples/vcs_base_demo.py` - Base functionality and utilities demo
- `examples/commit_msgs_demo.py` - Commit message generation demo

## API Reference

For detailed API documentation, see:

- [VCS Base Classes](../common/vcs/base.py)
- [GitHub Provider](../common/vcs/github.py)
- [GitLab Provider](../common/vcs/gitlab.py)
- [Commit Message Generator](../common/vcs/commit_msgs.py)

## Related Guides

- [Commit Message Generator Guide](commit-message-generator.md) - Detailed guide for commit message generation
- [Configuration Guide](configuration.md) - System configuration documentation
- [Safety Documentation](safety.md) - Security and safety features

## Contributing

When adding new VCS providers:

1. Implement the `VCSProviderProtocol` interface
2. Extend `BaseVCSProvider` for shared functionality
3. Add provider-specific error handling
4. Include comprehensive tests
5. Update documentation and examples
6. Add configuration templates

For detailed contribution guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).