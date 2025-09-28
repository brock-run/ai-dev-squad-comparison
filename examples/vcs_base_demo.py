#!/usr/bin/env python3
"""
VCS Base Functionality Demonstration

This example demonstrates the VCS base classes and utilities, including:
1. Retry middleware with exponential backoff
2. Rate limit management and detection
3. Request metrics collection
4. Error handling patterns
5. Utility functions for VCS operations
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.vcs.base import (
    VCSProvider, RequestMethod, VCSError, RateLimitError, AuthenticationError,
    RequestMetrics, RateLimitInfo, RetryConfig, Repository, Branch, Commit,
    PullRequest, RetryMiddleware, RateLimitManager, BaseVCSProvider,
    parse_repository_url, validate_branch_name, generate_branch_name
)


class DemoVCSProvider(BaseVCSProvider):
    """Demo VCS provider that simulates various scenarios."""
    
    def __init__(self):
        super().__init__("https://api.demo.com", "demo")
        self.request_count = 0
        self.simulate_rate_limit = False
        self.simulate_errors = False
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {"Authorization": f"Bearer {self.token}"}
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """Parse rate limit headers."""
        if "X-RateLimit-Limit" in headers:
            return RateLimitInfo(
                limit=int(headers["X-RateLimit-Limit"]),
                remaining=int(headers["X-RateLimit-Remaining"]),
                reset_time=datetime.fromtimestamp(int(headers["X-RateLimit-Reset"]))
            )
        return None
    
    async def _make_request(self, method: RequestMethod, endpoint: str,
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Override to simulate various scenarios."""
        self.request_count += 1
        
        # Simulate rate limiting
        if self.simulate_rate_limit and self.request_count > 3:
            reset_time = datetime.utcnow() + timedelta(seconds=5)
            raise RateLimitError(
                "API rate limit exceeded",
                reset_time=reset_time,
                remaining_requests=0
            )
        
        # Simulate random errors
        if self.simulate_errors and self.request_count % 4 == 0:
            raise VCSError("Simulated server error", status_code=500)
        
        # Simulate authentication check
        if endpoint == "/user" and not self.token:
            raise AuthenticationError("No authentication token provided")
        
        # Return mock response
        await asyncio.sleep(0.1)  # Simulate network delay
        return {"status": "success", "endpoint": endpoint, "method": method.value}
    
    # Implement abstract methods with mock implementations
    async def get_repository(self, owner: str, repo: str) -> Repository:
        """Get repository information."""
        await self._make_request(RequestMethod.GET, f"/repos/{owner}/{repo}")
        return Repository(
            name=repo,
            full_name=f"{owner}/{repo}",
            owner=owner,
            url=f"https://demo.com/{owner}/{repo}",
            clone_url=f"https://demo.com/{owner}/{repo}.git",
            description=f"Demo repository {repo}"
        )
    
    async def list_branches(self, owner: str, repo: str) -> List[Branch]:
        """List repository branches."""
        await self._make_request(RequestMethod.GET, f"/repos/{owner}/{repo}/branches")
        return [
            Branch(name="main", sha="abc123def456"),
            Branch(name="develop", sha="def456ghi789"),
            Branch(name="feature/demo", sha="ghi789jkl012")
        ]
    
    async def get_branch(self, owner: str, repo: str, branch: str) -> Branch:
        """Get specific branch information."""
        await self._make_request(RequestMethod.GET, f"/repos/{owner}/{repo}/branches/{branch}")
        return Branch(name=branch, sha="abc123def456")
    
    async def create_branch(self, owner: str, repo: str, branch_name: str,
                          source_branch: str = "main") -> Branch:
        """Create a new branch."""
        data = {"ref": f"refs/heads/{branch_name}", "sha": "abc123def456"}
        await self._make_request(RequestMethod.POST, f"/repos/{owner}/{repo}/git/refs", data=data)
        return Branch(name=branch_name, sha="abc123def456")
    
    async def commit_changes(self, owner: str, repo: str, branch: str,
                           message: str, files: Dict[str, str],
                           author_name: Optional[str] = None,
                           author_email: Optional[str] = None) -> Commit:
        """Commit changes to a branch."""
        data = {
            "message": message,
            "content": files,
            "branch": branch
        }
        await self._make_request(RequestMethod.POST, f"/repos/{owner}/{repo}/contents", data=data)
        return Commit(
            sha="new123commit456",
            message=message,
            author=author_name or "Demo User",
            author_email=author_email or "demo@example.com",
            timestamp=datetime.utcnow()
        )
    
    async def create_pull_request(self, owner: str, repo: str,
                                title: str, description: str,
                                source_branch: str, target_branch: str = "main",
                                draft: bool = False) -> PullRequest:
        """Create a pull request."""
        data = {
            "title": title,
            "body": description,
            "head": source_branch,
            "base": target_branch,
            "draft": draft
        }
        await self._make_request(RequestMethod.POST, f"/repos/{owner}/{repo}/pulls", data=data)
        return PullRequest(
            number=123,
            title=title,
            description=description,
            state="open",
            source_branch=source_branch,
            target_branch=target_branch,
            author="demo-user",
            url=f"https://demo.com/{owner}/{repo}/pull/123",
            created_at=datetime.utcnow()
        )
    
    async def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequest:
        """Get pull request information."""
        await self._make_request(RequestMethod.GET, f"/repos/{owner}/{repo}/pulls/{number}")
        return PullRequest(
            number=number,
            title="Demo Pull Request",
            description="This is a demo pull request",
            state="open",
            source_branch="feature/demo",
            target_branch="main",
            author="demo-user",
            url=f"https://demo.com/{owner}/{repo}/pull/{number}",
            created_at=datetime.utcnow()
        )
    
    async def list_pull_requests(self, owner: str, repo: str,
                               state: str = "open") -> List[PullRequest]:
        """List pull requests."""
        await self._make_request(RequestMethod.GET, f"/repos/{owner}/{repo}/pulls")
        return [await self.get_pull_request(owner, repo, 123)]


def demonstrate_data_classes():
    """Demonstrate VCS data classes."""
    print("=== VCS Data Classes ===")
    
    # Repository
    repo = Repository(
        name="demo-repo",
        full_name="demo-org/demo-repo",
        owner="demo-org",
        url="https://github.com/demo-org/demo-repo",
        clone_url="https://github.com/demo-org/demo-repo.git",
        description="A demonstration repository"
    )
    print(f"Repository: {repo.full_name}")
    print(f"  Owner: {repo.owner_name}")
    print(f"  Name: {repo.repo_name}")
    print(f"  URL: {repo.url}")
    
    # Branch
    branch = Branch(
        name="feature/demo",
        sha="abc123def456",
        protected=False
    )
    print(f"\nBranch: {branch.name}")
    print(f"  SHA: {branch.sha}")
    print(f"  Protected: {branch.protected}")
    
    # Commit
    commit = Commit(
        sha="def456ghi789",
        message="Add demo feature",
        author="Demo User",
        author_email="demo@example.com",
        timestamp=datetime.utcnow()
    )
    print(f"\nCommit: {commit.sha[:8]}")
    print(f"  Message: {commit.message}")
    print(f"  Author: {commit.author} <{commit.author_email}>")
    
    # Pull Request
    pr = PullRequest(
        number=123,
        title="Add demo feature",
        description="This PR adds a demo feature to the repository",
        state="open",
        source_branch="feature/demo",
        target_branch="main",
        author="demo-user",
        url="https://github.com/demo-org/demo-repo/pull/123",
        created_at=datetime.utcnow()
    )
    print(f"\nPull Request #{pr.number}: {pr.title}")
    print(f"  State: {pr.state} (Open: {pr.is_open}, Merged: {pr.is_merged})")
    print(f"  Branches: {pr.source_branch} → {pr.target_branch}")
    print(f"  Author: {pr.author}")


def demonstrate_retry_config():
    """Demonstrate retry configuration."""
    print("\n=== Retry Configuration ===")
    
    # Default configuration
    config = RetryConfig()
    print(f"Default config:")
    print(f"  Max retries: {config.max_retries}")
    print(f"  Base delay: {config.base_delay}s")
    print(f"  Max delay: {config.max_delay}s")
    print(f"  Exponential base: {config.exponential_base}")
    print(f"  Jitter enabled: {config.jitter}")
    
    # Calculate delays for different attempts
    print(f"\nDelay calculations (without jitter):")
    config.jitter = False
    for attempt in range(5):
        delay = config.calculate_delay(attempt)
        print(f"  Attempt {attempt}: {delay:.2f}s")
    
    # Rate limit delay
    print(f"\nRate limit delay:")
    rate_limit_delay = config.calculate_delay(0, rate_limit_reset=60)
    print(f"  Rate limit reset in 60s: {rate_limit_delay:.2f}s")


async def demonstrate_retry_middleware():
    """Demonstrate retry middleware functionality."""
    print("\n=== Retry Middleware ===")
    
    # Create middleware with fast retries for demo
    config = RetryConfig(max_retries=3, base_delay=0.1, jitter=False)
    middleware = RetryMiddleware(config)
    
    # Test successful request
    print("Testing successful request...")
    
    async def successful_request():
        return {"status": "success"}
    
    result = await middleware.execute_with_retry(successful_request)
    print(f"Result: {result}")
    
    # Test request with retries
    print("\nTesting request with retries...")
    call_count = 0
    
    async def failing_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise VCSError(f"Temporary error (attempt {call_count})")
        return {"status": "success", "attempts": call_count}
    
    call_count = 0  # Reset counter
    result = await middleware.execute_with_retry(failing_then_success)
    print(f"Result after retries: {result}")
    
    # Test non-retryable error
    print("\nTesting non-retryable error...")
    
    async def auth_error():
        raise AuthenticationError("Invalid token")
    
    try:
        await middleware.execute_with_retry(auth_error)
    except AuthenticationError as e:
        print(f"Caught expected error: {e}")
    
    # Show metrics
    metrics = middleware.get_metrics()
    print(f"\nMiddleware metrics:")
    print(f"  Total requests: {len(metrics)}")
    print(f"  Success rate: {middleware.get_success_rate():.2%}")
    print(f"  Average response time: {middleware.get_average_response_time():.2f}ms")


def demonstrate_rate_limit_manager():
    """Demonstrate rate limit management."""
    print("\n=== Rate Limit Manager ===")
    
    manager = RateLimitManager()
    
    # Simulate rate limit info
    reset_time = datetime.utcnow() + timedelta(minutes=15)
    rate_limit = RateLimitInfo(
        limit=5000,
        remaining=100,
        reset_time=reset_time,
        used=4900
    )
    
    manager.update_rate_limit("github", rate_limit)
    
    print(f"Rate limit info for GitHub:")
    print(f"  Limit: {rate_limit.limit}")
    print(f"  Remaining: {rate_limit.remaining}")
    print(f"  Used: {rate_limit.used}")
    print(f"  Reset in: {rate_limit.reset_in_seconds}s")
    print(f"  Is exhausted: {rate_limit.is_exhausted}")
    
    # Test rate limiting
    print(f"\nRate limit status:")
    print(f"  Is rate limited: {manager.is_rate_limited('github')}")
    print(f"  Wait time: {manager.get_wait_time('github')}s")
    
    # Record some requests
    for i in range(5):
        manager.record_request("github")
    
    print(f"\nRequest tracking:")
    print(f"  Request rate: {manager.get_request_rate():.2f} req/min")


async def demonstrate_vcs_provider():
    """Demonstrate VCS provider functionality."""
    print("\n=== VCS Provider Demo ===")
    
    provider = DemoVCSProvider()
    
    # Test authentication
    print("Testing authentication...")
    success = await provider.authenticate("demo-token")
    print(f"Authentication successful: {success}")
    
    # Test repository operations
    print("\nTesting repository operations...")
    repo = await provider.get_repository("demo-org", "demo-repo")
    print(f"Repository: {repo.full_name}")
    print(f"  Description: {repo.description}")
    
    # Test branch operations
    print("\nTesting branch operations...")
    branches = await provider.list_branches("demo-org", "demo-repo")
    print(f"Branches ({len(branches)}):")
    for branch in branches:
        print(f"  - {branch.name} ({branch.sha[:8]})")
    
    # Create new branch
    new_branch = await provider.create_branch("demo-org", "demo-repo", "feature/new-demo")
    print(f"\nCreated branch: {new_branch.name}")
    
    # Test commit operations
    print("\nTesting commit operations...")
    files = {
        "demo.py": "print('Hello, World!')",
        "README.md": "# Demo Repository\n\nThis is a demo."
    }
    commit = await provider.commit_changes(
        "demo-org", "demo-repo", "feature/new-demo",
        "Add demo files", files,
        "Demo User", "demo@example.com"
    )
    print(f"Created commit: {commit.sha[:8]} - {commit.message}")
    
    # Test pull request operations
    print("\nTesting pull request operations...")
    pr = await provider.create_pull_request(
        "demo-org", "demo-repo",
        "Add demo feature",
        "This PR adds a demo feature with example files.",
        "feature/new-demo", "main"
    )
    print(f"Created PR #{pr.number}: {pr.title}")
    print(f"  URL: {pr.url}")
    
    # Show provider metrics
    metrics = provider.get_metrics()
    print(f"\nProvider metrics:")
    print(f"  Provider: {metrics['provider']}")
    print(f"  Authenticated: {metrics['authenticated']}")
    print(f"  Success rate: {metrics['success_rate']:.2%}")
    print(f"  Recent requests: {metrics['recent_requests']}")


async def demonstrate_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n=== Error Handling Demo ===")
    
    provider = DemoVCSProvider()
    
    # Test authentication error
    print("Testing authentication error...")
    try:
        await provider.get_repository("demo-org", "demo-repo")  # No token
    except AuthenticationError as e:
        print(f"Caught authentication error: {e}")
    
    # Authenticate for other tests
    await provider.authenticate("demo-token")
    
    # Test rate limiting
    print("\nTesting rate limiting...")
    provider.simulate_rate_limit = True
    
    try:
        # Make requests until rate limited
        for i in range(5):
            await provider.get_repository("demo-org", f"repo-{i}")
    except RateLimitError as e:
        print(f"Caught rate limit error: {e}")
        print(f"  Reset time: {e.reset_time}")
        print(f"  Remaining requests: {e.remaining_requests}")
    
    # Test general errors with retry
    print("\nTesting error retry behavior...")
    provider.simulate_rate_limit = False
    provider.simulate_errors = True
    
    try:
        # This should succeed after retries
        repo = await provider.get_repository("demo-org", "retry-test")
        print(f"Request succeeded after retries: {repo.name}")
    except VCSError as e:
        print(f"Request failed after all retries: {e}")
    
    # Show final metrics
    metrics = provider.get_metrics()
    print(f"\nFinal metrics:")
    print(f"  Success rate: {metrics['success_rate']:.2%}")
    print(f"  Average response time: {metrics['average_response_time_ms']:.2f}ms")


def demonstrate_utility_functions():
    """Demonstrate utility functions."""
    print("\n=== Utility Functions ===")
    
    # Test URL parsing
    print("Testing repository URL parsing...")
    urls = [
        "https://github.com/owner/repo",
        "https://github.com/owner/repo.git",
        "https://gitlab.com/group/project",
        "https://bitbucket.org/workspace/repository"
    ]
    
    for url in urls:
        try:
            parsed = parse_repository_url(url)
            print(f"  {url}")
            print(f"    Owner: {parsed['owner']}")
            print(f"    Repo: {parsed['repo']}")
            print(f"    Host: {parsed['host']}")
        except ValueError as e:
            print(f"  {url} - Error: {e}")
    
    # Test branch name validation
    print(f"\nTesting branch name validation...")
    branch_names = [
        "main",
        "feature/new-feature",
        "bugfix/issue-123",
        "invalid name",  # Invalid: contains space
        "feature~1",     # Invalid: contains tilde
        ".hidden",       # Invalid: starts with dot
        "feature..test", # Invalid: double dots
    ]
    
    for name in branch_names:
        valid = validate_branch_name(name)
        status = "✓" if valid else "✗"
        print(f"  {status} {name}")
    
    # Test branch name generation
    print(f"\nTesting branch name generation...")
    generated_names = [
        generate_branch_name(),
        generate_branch_name("bugfix"),
        generate_branch_name("feature", "user-auth"),
        generate_branch_name("hotfix", "critical-fix")
    ]
    
    for name in generated_names:
        valid = validate_branch_name(name)
        status = "✓" if valid else "✗"
        print(f"  {status} {name}")


async def main():
    """Run all demonstrations."""
    print("VCS Base Functionality Demonstration")
    print("=" * 50)
    
    try:
        demonstrate_data_classes()
        demonstrate_retry_config()
        await demonstrate_retry_middleware()
        demonstrate_rate_limit_manager()
        await demonstrate_vcs_provider()
        await demonstrate_error_handling()
        demonstrate_utility_functions()
        
        print("\n" + "=" * 50)
        print("Demonstration completed successfully!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))