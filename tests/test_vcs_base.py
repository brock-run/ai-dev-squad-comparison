"""
Tests for VCS base functionality including retry middleware, rate limiting, and provider protocols.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from common.vcs.base import (
    VCSProvider, RequestMethod, VCSError, RateLimitError, AuthenticationError,
    NotFoundError, PermissionError, RequestMetrics, RateLimitInfo, RetryConfig,
    Repository, Branch, Commit, PullRequest, RetryMiddleware, RateLimitManager,
    BaseVCSProvider, parse_repository_url, validate_branch_name, generate_branch_name
)


class TestVCSExceptions:
    """Test VCS exception classes."""
    
    def test_vcs_error_basic(self):
        """Test basic VCSError functionality."""
        error = VCSError("Test error", status_code=500, response_data={"key": "value"})
        
        assert str(error) == "Test error"
        assert error.status_code == 500
        assert error.response_data == {"key": "value"}
    
    def test_rate_limit_error(self):
        """Test RateLimitError with reset time."""
        reset_time = datetime.utcnow() + timedelta(minutes=15)
        error = RateLimitError("Rate limited", reset_time=reset_time, remaining_requests=0)
        
        assert error.status_code == 429
        assert error.reset_time == reset_time
        assert error.remaining_requests == 0
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid token")
        
        assert str(error) == "Invalid token"
        assert error.status_code == 401
    
    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Repository not found", resource_type="repository")
        
        assert str(error) == "Repository not found"
        assert error.status_code == 404
        assert error.resource_type == "repository"
    
    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Access denied")
        
        assert str(error) == "Access denied"
        assert error.status_code == 403


class TestRequestMetrics:
    """Test RequestMetrics functionality."""
    
    def test_metrics_creation(self):
        """Test creating request metrics."""
        timestamp = datetime.utcnow()
        metrics = RequestMetrics(
            timestamp=timestamp,
            method=RequestMethod.GET,
            url="https://api.github.com/user",
            status_code=200,
            response_time_ms=150.5,
            retry_count=1,
            rate_limited=False
        )
        
        assert metrics.timestamp == timestamp
        assert metrics.method == RequestMethod.GET
        assert metrics.url == "https://api.github.com/user"
        assert metrics.status_code == 200
        assert metrics.response_time_ms == 150.5
        assert metrics.retry_count == 1
        assert metrics.rate_limited is False
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        timestamp = datetime.utcnow()
        metrics = RequestMetrics(
            timestamp=timestamp,
            method=RequestMethod.POST,
            url="https://api.github.com/repos/owner/repo/pulls",
            status_code=201,
            response_time_ms=250.0,
            error="Test error"
        )
        
        result = metrics.to_dict()
        
        assert result['timestamp'] == timestamp.isoformat()
        assert result['method'] == 'POST'
        assert result['url'] == "https://api.github.com/repos/owner/repo/pulls"
        assert result['status_code'] == 201
        assert result['response_time_ms'] == 250.0
        assert result['error'] == "Test error"


class TestRateLimitInfo:
    """Test RateLimitInfo functionality."""
    
    def test_rate_limit_info_creation(self):
        """Test creating rate limit info."""
        reset_time = datetime.utcnow() + timedelta(hours=1)
        rate_limit = RateLimitInfo(
            limit=5000,
            remaining=4500,
            reset_time=reset_time,
            used=500
        )
        
        assert rate_limit.limit == 5000
        assert rate_limit.remaining == 4500
        assert rate_limit.reset_time == reset_time
        assert rate_limit.used == 500
    
    def test_is_exhausted(self):
        """Test rate limit exhaustion check."""
        reset_time = datetime.utcnow() + timedelta(hours=1)
        
        # Not exhausted
        rate_limit = RateLimitInfo(limit=5000, remaining=100, reset_time=reset_time)
        assert rate_limit.is_exhausted is False
        
        # Exhausted
        rate_limit = RateLimitInfo(limit=5000, remaining=0, reset_time=reset_time)
        assert rate_limit.is_exhausted is True
    
    def test_reset_in_seconds(self):
        """Test calculating seconds until reset."""
        reset_time = datetime.utcnow() + timedelta(minutes=30)
        rate_limit = RateLimitInfo(limit=5000, remaining=100, reset_time=reset_time)
        
        reset_seconds = rate_limit.reset_in_seconds
        assert 1700 <= reset_seconds <= 1800  # Approximately 30 minutes


class TestRetryConfig:
    """Test RetryConfig functionality."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.retry_on_rate_limit is True
    
    def test_calculate_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(jitter=False)  # Disable jitter for predictable testing
        
        # Test exponential backoff
        assert config.calculate_delay(0) == 1.0  # base_delay * 2^0
        assert config.calculate_delay(1) == 2.0  # base_delay * 2^1
        assert config.calculate_delay(2) == 4.0  # base_delay * 2^2
        assert config.calculate_delay(3) == 8.0  # base_delay * 2^3
    
    def test_calculate_delay_max_limit(self):
        """Test delay calculation respects max limit."""
        config = RetryConfig(max_delay=5.0, jitter=False)
        
        # Should be capped at max_delay
        assert config.calculate_delay(10) == 5.0
    
    def test_calculate_delay_rate_limit(self):
        """Test delay calculation for rate limit."""
        config = RetryConfig()
        
        # Rate limit reset in 60 seconds
        delay = config.calculate_delay(0, rate_limit_reset=60)
        expected = 60 * config.rate_limit_delay_factor
        assert delay == expected
    
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation includes jitter."""
        config = RetryConfig(jitter=True)
        
        # With jitter, delay should vary
        delays = [config.calculate_delay(1) for _ in range(10)]
        
        # All delays should be around 2.0 but with variation
        assert all(1.5 <= delay <= 2.5 for delay in delays)
        assert len(set(delays)) > 1  # Should have variation


class TestDataClasses:
    """Test VCS data classes."""
    
    def test_repository(self):
        """Test Repository data class."""
        repo = Repository(
            name="test-repo",
            full_name="owner/test-repo",
            owner="owner",
            url="https://github.com/owner/test-repo",
            clone_url="https://github.com/owner/test-repo.git",
            default_branch="main",
            private=False,
            description="Test repository"
        )
        
        assert repo.repo_name == "test-repo"
        assert repo.owner_name == "owner"
        assert repo.default_branch == "main"
        assert repo.private is False
    
    def test_branch(self):
        """Test Branch data class."""
        branch = Branch(
            name="feature/test",
            sha="abc123def456",
            protected=False,
            url="https://github.com/owner/repo/tree/feature/test"
        )
        
        assert branch.name == "feature/test"
        assert branch.sha == "abc123def456"
        assert branch.protected is False
    
    def test_commit(self):
        """Test Commit data class."""
        timestamp = datetime.utcnow()
        commit = Commit(
            sha="abc123def456",
            message="Add new feature",
            author="John Doe",
            author_email="john@example.com",
            timestamp=timestamp,
            url="https://github.com/owner/repo/commit/abc123def456",
            parents=["parent1", "parent2"]
        )
        
        assert commit.sha == "abc123def456"
        assert commit.message == "Add new feature"
        assert commit.author == "John Doe"
        assert commit.timestamp == timestamp
    
    def test_pull_request(self):
        """Test PullRequest data class."""
        created_at = datetime.utcnow()
        pr = PullRequest(
            number=123,
            title="Add new feature",
            description="This PR adds a new feature",
            state="open",
            source_branch="feature/test",
            target_branch="main",
            author="john-doe",
            url="https://github.com/owner/repo/pull/123",
            created_at=created_at
        )
        
        assert pr.number == 123
        assert pr.is_open is True
        assert pr.is_merged is False
        
        # Test merged state
        pr.state = "merged"
        assert pr.is_open is False
        assert pr.is_merged is True


class TestRetryMiddleware:
    """Test RetryMiddleware functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = RetryConfig(max_retries=2, base_delay=0.01)  # Fast retries for testing
        self.middleware = RetryMiddleware(self.config)
    
    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Test successful request without retries."""
        async def mock_func():
            return {"status": "success"}
        
        result = await self.middleware.execute_with_retry(mock_func)
        
        assert result == {"status": "success"}
        
        metrics = self.middleware.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].retry_count == 0
        assert metrics[0].error is None
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry behavior on failures."""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise VCSError("Temporary error")
            return {"status": "success"}
        
        result = await self.middleware.execute_with_retry(mock_func)
        
        assert result == {"status": "success"}
        assert call_count == 3
        
        metrics = self.middleware.get_metrics()
        assert len(metrics) == 3  # 2 failures + 1 success
        assert metrics[-1].error is None  # Last one succeeded
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        async def mock_func():
            raise VCSError("Persistent error")
        
        with pytest.raises(VCSError, match="Persistent error"):
            await self.middleware.execute_with_retry(mock_func)
        
        metrics = self.middleware.get_metrics()
        assert len(metrics) == 3  # max_retries + 1
        assert all(m.error == "Persistent error" for m in metrics)
    
    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self):
        """Test that authentication errors are not retried."""
        async def mock_func():
            raise AuthenticationError("Invalid token")
        
        with pytest.raises(AuthenticationError):
            await self.middleware.execute_with_retry(mock_func)
        
        metrics = self.middleware.get_metrics()
        assert len(metrics) == 1  # No retries
    
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self):
        """Test retry behavior on rate limit errors."""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                reset_time = datetime.utcnow() + timedelta(seconds=1)
                raise RateLimitError("Rate limited", reset_time=reset_time)
            return {"status": "success"}
        
        result = await self.middleware.execute_with_retry(mock_func)
        
        assert result == {"status": "success"}
        assert call_count == 2
        
        metrics = self.middleware.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].rate_limited is True
    
    def test_get_success_rate(self):
        """Test success rate calculation."""
        # Add some mock metrics
        self.middleware.metrics = [
            RequestMetrics(datetime.utcnow(), RequestMethod.GET, "url1", error=None),
            RequestMetrics(datetime.utcnow(), RequestMethod.GET, "url2", error="Error"),
            RequestMetrics(datetime.utcnow(), RequestMethod.GET, "url3", error=None),
        ]
        
        success_rate = self.middleware.get_success_rate()
        assert success_rate == 2/3  # 2 successful out of 3
    
    def test_get_average_response_time(self):
        """Test average response time calculation."""
        self.middleware.metrics = [
            RequestMetrics(datetime.utcnow(), RequestMethod.GET, "url1", response_time_ms=100.0),
            RequestMetrics(datetime.utcnow(), RequestMethod.GET, "url2", response_time_ms=200.0),
            RequestMetrics(datetime.utcnow(), RequestMethod.GET, "url3", response_time_ms=300.0),
        ]
        
        avg_time = self.middleware.get_average_response_time()
        assert avg_time == 200.0


class TestRateLimitManager:
    """Test RateLimitManager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = RateLimitManager()
    
    def test_update_and_get_rate_limit(self):
        """Test updating and retrieving rate limit info."""
        reset_time = datetime.utcnow() + timedelta(hours=1)
        rate_limit = RateLimitInfo(limit=5000, remaining=4500, reset_time=reset_time)
        
        self.manager.update_rate_limit("github", rate_limit)
        
        retrieved = self.manager.get_rate_limit("github")
        assert retrieved == rate_limit
    
    def test_is_rate_limited(self):
        """Test rate limit checking."""
        reset_time = datetime.utcnow() + timedelta(hours=1)
        
        # Not rate limited
        rate_limit = RateLimitInfo(limit=5000, remaining=100, reset_time=reset_time)
        self.manager.update_rate_limit("github", rate_limit)
        assert self.manager.is_rate_limited("github") is False
        
        # Rate limited
        rate_limit = RateLimitInfo(limit=5000, remaining=0, reset_time=reset_time)
        self.manager.update_rate_limit("github", rate_limit)
        assert self.manager.is_rate_limited("github") is True
    
    def test_get_wait_time(self):
        """Test wait time calculation."""
        reset_time = datetime.utcnow() + timedelta(minutes=30)
        rate_limit = RateLimitInfo(limit=5000, remaining=0, reset_time=reset_time)
        
        self.manager.update_rate_limit("github", rate_limit)
        
        wait_time = self.manager.get_wait_time("github")
        assert 1700 <= wait_time <= 1800  # Approximately 30 minutes
    
    def test_record_request(self):
        """Test request recording."""
        self.manager.record_request("github")
        self.manager.record_request("github")
        
        assert len(self.manager.request_history) == 2
    
    def test_get_request_rate(self):
        """Test request rate calculation."""
        # Record some requests
        for _ in range(5):
            self.manager.record_request("github")
        
        rate = self.manager.get_request_rate(window_minutes=60)
        assert rate == 5 / 60  # 5 requests in 60 minutes


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_parse_repository_url_github(self):
        """Test parsing GitHub repository URL."""
        url = "https://github.com/owner/repo-name"
        result = parse_repository_url(url)
        
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo-name'
        assert result['host'] == 'github.com'
    
    def test_parse_repository_url_with_git_suffix(self):
        """Test parsing repository URL with .git suffix."""
        url = "https://github.com/owner/repo-name.git"
        result = parse_repository_url(url)
        
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo-name'  # .git suffix removed
    
    def test_parse_repository_url_invalid(self):
        """Test parsing invalid repository URL."""
        with pytest.raises(ValueError, match="Invalid repository URL format"):
            parse_repository_url("https://github.com/invalid")
    
    def test_validate_branch_name_valid(self):
        """Test valid branch names."""
        valid_names = [
            "main",
            "feature/new-feature",
            "bugfix/issue-123",
            "release/v1.0.0",
            "hotfix-urgent"
        ]
        
        for name in valid_names:
            assert validate_branch_name(name) is True
    
    def test_validate_branch_name_invalid(self):
        """Test invalid branch names."""
        invalid_names = [
            "",  # Empty
            "feature with spaces",  # Spaces
            "feature~1",  # Tilde
            "feature^1",  # Caret
            "feature:1",  # Colon
            "feature?1",  # Question mark
            "feature*1",  # Asterisk
            "feature[1]",  # Brackets
            "feature\\1",  # Backslash
            ".hidden",  # Starts with dot
            "feature.",  # Ends with dot
            "feature..branch",  # Double dots
        ]
        
        for name in invalid_names:
            assert validate_branch_name(name) is False
    
    def test_generate_branch_name(self):
        """Test branch name generation."""
        # Test with default prefix
        branch_name = generate_branch_name()
        assert branch_name.startswith("feature/")
        assert validate_branch_name(branch_name) is True
        
        # Test with custom prefix and suffix
        branch_name = generate_branch_name("bugfix", "issue-123")
        assert branch_name.startswith("bugfix/issue-123-")
        assert validate_branch_name(branch_name) is True


class MockVCSProvider(BaseVCSProvider):
    """Mock VCS provider for testing BaseVCSProvider functionality."""
    
    def __init__(self):
        super().__init__("https://api.mock.com", "mock")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"token {self.token}"}
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        if "X-RateLimit-Limit" in headers:
            return RateLimitInfo(
                limit=int(headers["X-RateLimit-Limit"]),
                remaining=int(headers["X-RateLimit-Remaining"]),
                reset_time=datetime.fromtimestamp(int(headers["X-RateLimit-Reset"]))
            )
        return None
    
    # Implement abstract methods with mock behavior
    async def get_repository(self, owner: str, repo: str) -> Repository:
        return Repository(
            name=repo,
            full_name=f"{owner}/{repo}",
            owner=owner,
            url=f"https://mock.com/{owner}/{repo}",
            clone_url=f"https://mock.com/{owner}/{repo}.git"
        )
    
    async def list_branches(self, owner: str, repo: str) -> List[Branch]:
        return [Branch(name="main", sha="abc123")]
    
    async def get_branch(self, owner: str, repo: str, branch: str) -> Branch:
        return Branch(name=branch, sha="abc123")
    
    async def create_branch(self, owner: str, repo: str, branch_name: str, 
                          source_branch: str = "main") -> Branch:
        return Branch(name=branch_name, sha="def456")
    
    async def commit_changes(self, owner: str, repo: str, branch: str,
                           message: str, files: Dict[str, str],
                           author_name: Optional[str] = None,
                           author_email: Optional[str] = None) -> Commit:
        return Commit(
            sha="ghi789",
            message=message,
            author=author_name or "Test Author",
            author_email=author_email or "test@example.com",
            timestamp=datetime.utcnow()
        )
    
    async def create_pull_request(self, owner: str, repo: str,
                                title: str, description: str,
                                source_branch: str, target_branch: str = "main",
                                draft: bool = False) -> PullRequest:
        return PullRequest(
            number=123,
            title=title,
            description=description,
            state="open",
            source_branch=source_branch,
            target_branch=target_branch,
            author="test-user",
            url=f"https://mock.com/{owner}/{repo}/pull/123",
            created_at=datetime.utcnow()
        )
    
    async def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequest:
        return PullRequest(
            number=number,
            title="Test PR",
            description="Test description",
            state="open",
            source_branch="feature/test",
            target_branch="main",
            author="test-user",
            url=f"https://mock.com/{owner}/{repo}/pull/{number}",
            created_at=datetime.utcnow()
        )
    
    async def list_pull_requests(self, owner: str, repo: str, 
                               state: str = "open") -> List[PullRequest]:
        return [await self.get_pull_request(owner, repo, 123)]


class TestBaseVCSProvider:
    """Test BaseVCSProvider functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.provider = MockVCSProvider()
    
    def test_initialization(self):
        """Test provider initialization."""
        assert self.provider.base_url == "https://api.mock.com"
        assert self.provider.provider_name == "mock"
        assert self.provider.authenticated is False
        assert self.provider.token is None
    
    def test_get_headers(self):
        """Test header generation."""
        headers = self.provider._get_headers()
        
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Content-Type" in headers
        
        # Test with token
        self.provider.token = "test-token"
        headers = self.provider._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "token test-token"
    
    def test_handle_error_response(self):
        """Test error response handling."""
        # Test different error types
        error = self.provider._handle_error_response(401, {"message": "Unauthorized"})
        assert isinstance(error, AuthenticationError)
        
        error = self.provider._handle_error_response(403, {"message": "Forbidden"})
        assert isinstance(error, PermissionError)
        
        error = self.provider._handle_error_response(404, {"message": "Not found"})
        assert isinstance(error, NotFoundError)
        
        error = self.provider._handle_error_response(429, {"message": "Rate limited"})
        assert isinstance(error, RateLimitError)
        
        error = self.provider._handle_error_response(500, {"message": "Server error"})
        assert isinstance(error, VCSError)
        assert error.status_code == 500
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful authentication."""
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"login": "test-user"}
            
            result = await self.provider.authenticate("test-token")
            
            assert result is True
            assert self.provider.authenticated is True
            assert self.provider.token == "test-token"
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self):
        """Test authentication failure."""
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = AuthenticationError("Invalid token")
            
            result = await self.provider.authenticate("invalid-token")
            
            assert result is False
            assert self.provider.authenticated is False
    
    def test_get_metrics(self):
        """Test metrics collection."""
        metrics = self.provider.get_metrics()
        
        assert "provider" in metrics
        assert "authenticated" in metrics
        assert "success_rate" in metrics
        assert "average_response_time_ms" in metrics
        assert "request_rate_per_minute" in metrics
        
        assert metrics["provider"] == "mock"
        assert metrics["authenticated"] is False


if __name__ == "__main__":
    pytest.main([__file__])