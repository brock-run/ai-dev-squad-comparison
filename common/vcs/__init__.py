"""
VCS (Version Control System) Integration Module

This module provides unified interfaces and implementations for integrating with
various VCS providers like GitHub, GitLab, Bitbucket, and Azure DevOps.

Key Components:
- Base provider protocol and abstract classes
- Retry middleware with exponential backoff and jitter
- Rate limit detection and handling
- Request logging and metrics collection
- Common error handling patterns

Usage:
    from common.vcs import VCSProvider, GitHubProvider, GitLabProvider
    
    # Create provider instance
    github = GitHubProvider()
    
    # Authenticate
    await github.authenticate(token)
    
    # Create branch and commit changes
    branch = await github.create_branch("owner", "repo", "feature/new-feature")
    commit = await github.commit_changes("owner", "repo", "feature/new-feature", 
                                       "Add new feature", {"file.py": "content"})
    
    # Create pull request
    pr = await github.create_pull_request("owner", "repo", "New Feature", 
                                         "Description", "feature/new-feature")
"""

from .base import (
    # Enums
    VCSProvider,
    RequestMethod,
    
    # Exceptions
    VCSError,
    RateLimitError,
    AuthenticationError,
    NotFoundError,
    PermissionError,
    
    # Data classes
    RequestMetrics,
    RateLimitInfo,
    RetryConfig,
    Repository,
    Branch,
    Commit,
    PullRequest,
    
    # Protocols and base classes
    VCSProviderProtocol,
    BaseVCSProvider,
    RetryMiddleware,
    RateLimitManager,
    
    # Utility functions
    parse_repository_url,
    validate_branch_name,
    generate_branch_name,
)

from .github import (
    GitHubProvider,
    GitHubError,
    GitHubRateLimitError,
    parse_github_url,
    validate_github_token,
    get_github_scopes_for_operations,
)

from .gitlab import (
    GitLabProvider,
    GitLabError,
    GitLabRateLimitError,
    MergeRequest,
    parse_gitlab_url,
    validate_gitlab_token,
    get_gitlab_scopes_for_operations,
    convert_github_to_gitlab_workflow,
)

from .commit_msgs import (
    CommitMessageGenerator,
    CommitMessageConfig,
    CommitContext,
    DiffAnalyzer,
    CommitType,
    MessageStyle,
    FileChange,
    DiffStats,
    generate_commit_message,
    suggest_commit_messages,
    analyze_commit_diff,
    validate_commit_message,
)

__all__ = [
    # Enums
    "VCSProvider",
    "RequestMethod",
    
    # Exceptions
    "VCSError",
    "RateLimitError", 
    "AuthenticationError",
    "NotFoundError",
    "PermissionError",
    
    # Data classes
    "RequestMetrics",
    "RateLimitInfo",
    "RetryConfig",
    "Repository",
    "Branch",
    "Commit",
    "PullRequest",
    
    # Protocols and base classes
    "VCSProviderProtocol",
    "BaseVCSProvider",
    "RetryMiddleware",
    "RateLimitManager",
    
    # Utility functions
    "parse_repository_url",
    "validate_branch_name",
    "generate_branch_name",
    
    # GitHub provider
    "GitHubProvider",
    "GitHubError",
    "GitHubRateLimitError",
    "parse_github_url",
    "validate_github_token",
    "get_github_scopes_for_operations",
    
    # GitLab provider
    "GitLabProvider",
    "GitLabError",
    "GitLabRateLimitError",
    "MergeRequest",
    "parse_gitlab_url",
    "validate_gitlab_token",
    "get_gitlab_scopes_for_operations",
    "convert_github_to_gitlab_workflow",
    
    # Commit message generation
    "CommitMessageGenerator",
    "CommitMessageConfig",
    "CommitContext",
    "DiffAnalyzer",
    "CommitType",
    "MessageStyle",
    "FileChange",
    "DiffStats",
    "generate_commit_message",
    "suggest_commit_messages",
    "analyze_commit_diff",
    "validate_commit_message",
]