"""
VCS Provider Base Classes and Protocols

This module provides the foundational interfaces and utilities for VCS (Version Control System)
integrations. It includes:
- Provider protocol definitions for GitHub, GitLab, etc.
- Retry middleware with exponential backoff and jitter
- Rate limit detection and handling
- Request logging and metrics collection
- Common error handling patterns
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Callable, Awaitable
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)


class VCSProvider(str, Enum):
    """Supported VCS providers."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"


class RequestMethod(str, Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class VCSError(Exception):
    """Base exception for VCS operations."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class RateLimitError(VCSError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str, reset_time: Optional[datetime] = None,
                 remaining_requests: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.reset_time = reset_time
        self.remaining_requests = remaining_requests


class AuthenticationError(VCSError):
    """Exception raised for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class NotFoundError(VCSError):
    """Exception raised when resource is not found."""
    
    def __init__(self, message: str, resource_type: str = "resource"):
        super().__init__(message, status_code=404)
        self.resource_type = resource_type


class PermissionError(VCSError):
    """Exception raised for permission/authorization failures."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


@dataclass
class RequestMetrics:
    """Metrics for VCS API requests."""
    timestamp: datetime
    method: RequestMethod
    url: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    retry_count: int = 0
    rate_limited: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'method': self.method.value,
            'url': self.url,
            'status_code': self.status_code,
            'response_time_ms': self.response_time_ms,
            'retry_count': self.retry_count,
            'rate_limited': self.rate_limited,
            'error': self.error
        }


@dataclass
class RateLimitInfo:
    """Rate limit information from API responses."""
    limit: int
    remaining: int
    reset_time: datetime
    used: int = 0
    
    @property
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted."""
        return self.remaining <= 0
    
    @property
    def reset_in_seconds(self) -> int:
        """Get seconds until rate limit resets."""
        return max(0, int((self.reset_time - datetime.utcnow()).total_seconds()))


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_rate_limit: bool = True
    rate_limit_delay_factor: float = 1.1
    
    def calculate_delay(self, attempt: int, rate_limit_reset: Optional[int] = None) -> float:
        """Calculate delay for retry attempt."""
        if rate_limit_reset is not None and self.retry_on_rate_limit:
            # For rate limit errors, wait until reset time plus a small buffer
            return rate_limit_reset * self.rate_limit_delay_factor
        
        # Exponential backoff with jitter
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter (±25% of delay)
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


@dataclass
class Repository:
    """Repository information."""
    name: str
    full_name: str
    owner: str
    url: str
    clone_url: str
    default_branch: str = "main"
    private: bool = False
    description: Optional[str] = None
    
    @property
    def repo_name(self) -> str:
        """Get repository name without owner."""
        return self.name
    
    @property
    def owner_name(self) -> str:
        """Get repository owner name."""
        return self.owner


@dataclass
class Branch:
    """Branch information."""
    name: str
    sha: str
    protected: bool = False
    url: Optional[str] = None


@dataclass
class Commit:
    """Commit information."""
    sha: str
    message: str
    author: str
    author_email: str
    timestamp: datetime
    url: Optional[str] = None
    parents: List[str] = field(default_factory=list)


@dataclass
class PullRequest:
    """Pull/Merge request information."""
    number: int
    title: str
    description: str
    state: str
    source_branch: str
    target_branch: str
    author: str
    url: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    
    @property
    def is_open(self) -> bool:
        """Check if PR/MR is open."""
        return self.state.lower() in ('open', 'opened')
    
    @property
    def is_merged(self) -> bool:
        """Check if PR/MR is merged."""
        return self.state.lower() == 'merged'


class VCSProviderProtocol(ABC):
    """Protocol for VCS provider implementations."""
    
    @abstractmethod
    async def authenticate(self, token: str) -> bool:
        """Authenticate with the VCS provider."""
        pass
    
    @abstractmethod
    async def get_repository(self, owner: str, repo: str) -> Repository:
        """Get repository information."""
        pass
    
    @abstractmethod
    async def list_branches(self, owner: str, repo: str) -> List[Branch]:
        """List repository branches."""
        pass
    
    @abstractmethod
    async def get_branch(self, owner: str, repo: str, branch: str) -> Branch:
        """Get specific branch information."""
        pass
    
    @abstractmethod
    async def create_branch(self, owner: str, repo: str, branch_name: str, 
                          source_branch: str = "main") -> Branch:
        """Create a new branch."""
        pass
    
    @abstractmethod
    async def commit_changes(self, owner: str, repo: str, branch: str,
                           message: str, files: Dict[str, str],
                           author_name: Optional[str] = None,
                           author_email: Optional[str] = None) -> Commit:
        """Commit changes to a branch."""
        pass
    
    @abstractmethod
    async def create_pull_request(self, owner: str, repo: str,
                                title: str, description: str,
                                source_branch: str, target_branch: str = "main",
                                draft: bool = False) -> PullRequest:
        """Create a pull/merge request."""
        pass
    
    @abstractmethod
    async def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequest:
        """Get pull/merge request information."""
        pass
    
    @abstractmethod
    async def list_pull_requests(self, owner: str, repo: str, 
                               state: str = "open") -> List[PullRequest]:
        """List pull/merge requests."""
        pass


class RetryMiddleware:
    """Middleware for handling retries with exponential backoff and jitter."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.metrics: List[RequestMetrics] = []
    
    async def execute_with_retry(self, 
                               func: Callable[..., Awaitable[Any]], 
                               *args, 
                               **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            start_time = time.time()
            metrics = RequestMetrics(
                timestamp=datetime.utcnow(),
                method=kwargs.get('method', RequestMethod.GET),
                url=kwargs.get('url', 'unknown'),
                retry_count=attempt
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # Record successful metrics
                metrics.response_time_ms = (time.time() - start_time) * 1000
                metrics.status_code = getattr(result, 'status_code', 200)
                self.metrics.append(metrics)
                
                logger.debug(f"Request succeeded on attempt {attempt + 1}")
                return result
                
            except RateLimitError as e:
                metrics.rate_limited = True
                metrics.error = str(e)
                metrics.response_time_ms = (time.time() - start_time) * 1000
                self.metrics.append(metrics)
                
                last_exception = e
                
                if attempt < self.config.max_retries and self.config.retry_on_rate_limit:
                    delay = self.config.calculate_delay(attempt, e.reset_time.timestamp() if e.reset_time else None)
                    logger.warning(f"Rate limited on attempt {attempt + 1}, retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Rate limit exceeded, no more retries")
                    break
                    
            except (VCSError, Exception) as e:
                metrics.error = str(e)
                metrics.status_code = getattr(e, 'status_code', None)
                metrics.response_time_ms = (time.time() - start_time) * 1000
                self.metrics.append(metrics)
                
                last_exception = e
                
                # Don't retry on authentication or permission errors
                if isinstance(e, (AuthenticationError, PermissionError)):
                    logger.error(f"Non-retryable error: {e}")
                    break
                
                if attempt < self.config.max_retries:
                    delay = self.config.calculate_delay(attempt)
                    logger.warning(f"Request failed on attempt {attempt + 1}, retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Request failed after {self.config.max_retries + 1} attempts: {e}")
                    break
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise VCSError("Request failed after all retries")
    
    def get_metrics(self, limit: Optional[int] = None) -> List[RequestMetrics]:
        """Get request metrics."""
        if limit:
            return self.metrics[-limit:]
        return self.metrics.copy()
    
    def clear_metrics(self):
        """Clear stored metrics."""
        self.metrics.clear()
    
    def get_success_rate(self) -> float:
        """Calculate success rate of requests."""
        if not self.metrics:
            return 0.0
        
        successful = sum(1 for m in self.metrics if m.error is None)
        return successful / len(self.metrics)
    
    def get_average_response_time(self) -> float:
        """Calculate average response time in milliseconds."""
        if not self.metrics:
            return 0.0
        
        times = [m.response_time_ms for m in self.metrics if m.response_time_ms is not None]
        return sum(times) / len(times) if times else 0.0


class RateLimitManager:
    """Manager for tracking and handling rate limits."""
    
    def __init__(self):
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.request_history: List[datetime] = []
    
    def update_rate_limit(self, provider: str, rate_limit_info: RateLimitInfo):
        """Update rate limit information for a provider."""
        self.rate_limits[provider] = rate_limit_info
        logger.debug(f"Updated rate limit for {provider}: {rate_limit_info.remaining}/{rate_limit_info.limit}")
    
    def get_rate_limit(self, provider: str) -> Optional[RateLimitInfo]:
        """Get current rate limit information for a provider."""
        return self.rate_limits.get(provider)
    
    def is_rate_limited(self, provider: str) -> bool:
        """Check if provider is currently rate limited."""
        rate_limit = self.get_rate_limit(provider)
        if not rate_limit:
            return False
        
        return rate_limit.is_exhausted
    
    def get_wait_time(self, provider: str) -> int:
        """Get seconds to wait before next request."""
        rate_limit = self.get_rate_limit(provider)
        if not rate_limit or not rate_limit.is_exhausted:
            return 0
        
        return rate_limit.reset_in_seconds
    
    def record_request(self, provider: str):
        """Record a request for rate limiting purposes."""
        now = datetime.utcnow()
        self.request_history.append(now)
        
        # Clean up old requests (keep last hour)
        cutoff = now - timedelta(hours=1)
        self.request_history = [req for req in self.request_history if req > cutoff]
    
    def get_request_rate(self, window_minutes: int = 60) -> float:
        """Get current request rate (requests per minute)."""
        if not self.request_history:
            return 0.0
        
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_requests = [req for req in self.request_history if req > cutoff]
        
        return len(recent_requests) / window_minutes


class BaseVCSProvider(VCSProviderProtocol):
    """Base implementation for VCS providers with common functionality."""
    
    def __init__(self, 
                 base_url: str,
                 provider_name: str,
                 retry_config: Optional[RetryConfig] = None):
        self.base_url = base_url.rstrip('/')
        self.provider_name = provider_name
        self.retry_middleware = RetryMiddleware(retry_config)
        self.rate_limit_manager = RateLimitManager()
        self.token: Optional[str] = None
        self.authenticated = False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests."""
        headers = {
            'User-Agent': f'ai-dev-squad-comparison/{self.provider_name}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.token:
            headers.update(self._get_auth_headers())
        
        return headers
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers. Override in subclasses."""
        return {}
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """Parse rate limit information from response headers. Override in subclasses."""
        return None
    
    def _handle_error_response(self, status_code: int, response_data: Dict[str, Any]) -> VCSError:
        """Handle error responses and create appropriate exceptions."""
        message = response_data.get('message', f'HTTP {status_code} error')
        
        if status_code == 401:
            return AuthenticationError(message)
        elif status_code == 403:
            return PermissionError(message)
        elif status_code == 404:
            return NotFoundError(message)
        elif status_code == 429:
            return RateLimitError(message)
        else:
            return VCSError(message, status_code, response_data)
    
    async def _make_request(self, 
                          method: RequestMethod, 
                          endpoint: str,
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request with retry and rate limiting."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async def _request():
            # Check rate limits before making request
            if self.rate_limit_manager.is_rate_limited(self.provider_name):
                wait_time = self.rate_limit_manager.get_wait_time(self.provider_name)
                raise RateLimitError(
                    f"Rate limit exceeded, reset in {wait_time}s",
                    reset_time=datetime.utcnow() + timedelta(seconds=wait_time)
                )
            
            # Record request for rate limiting
            self.rate_limit_manager.record_request(self.provider_name)
            
            # This would be implemented with actual HTTP client (aiohttp, httpx, etc.)
            # For now, we'll simulate the request structure
            headers = self._get_headers()
            
            # Simulate HTTP request
            logger.debug(f"Making {method.value} request to {url}")
            
            # This is where you would make the actual HTTP request
            # response = await http_client.request(method.value, url, headers=headers, json=data, params=params)
            
            # For demonstration, we'll return a mock response
            # In real implementation, parse the actual response
            response_data = {"status": "success"}
            status_code = 200
            response_headers = {}
            
            # Update rate limit information
            rate_limit_info = self._parse_rate_limit_headers(response_headers)
            if rate_limit_info:
                self.rate_limit_manager.update_rate_limit(self.provider_name, rate_limit_info)
            
            # Handle error responses
            if status_code >= 400:
                error = self._handle_error_response(status_code, response_data)
                raise error
            
            return response_data
        
        return await self.retry_middleware.execute_with_retry(
            _request,
            method=method,
            url=url
        )
    
    async def authenticate(self, token: str) -> bool:
        """Authenticate with the VCS provider."""
        self.token = token
        
        try:
            # Test authentication with a simple API call
            await self._make_request(RequestMethod.GET, "/user")
            self.authenticated = True
            logger.info(f"Successfully authenticated with {self.provider_name}")
            return True
            
        except AuthenticationError:
            self.authenticated = False
            logger.error(f"Authentication failed for {self.provider_name}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get provider metrics."""
        return {
            'provider': self.provider_name,
            'authenticated': self.authenticated,
            'success_rate': self.retry_middleware.get_success_rate(),
            'average_response_time_ms': self.retry_middleware.get_average_response_time(),
            'request_rate_per_minute': self.rate_limit_manager.get_request_rate(),
            'rate_limit_info': self.rate_limit_manager.get_rate_limit(self.provider_name),
            'recent_requests': len(self.retry_middleware.get_metrics(100))
        }
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        metrics_data = {
            'provider_metrics': self.get_metrics(),
            'request_history': [m.to_dict() for m in self.retry_middleware.get_metrics()],
            'exported_at': datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        logger.info(f"Exported metrics to {filepath}")


# Utility functions for common VCS operations

def parse_repository_url(url: str) -> Dict[str, str]:
    """Parse repository URL to extract owner and repo name."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = path_parts[1]
        
        # Remove .git suffix if present
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        return {
            'owner': owner,
            'repo': repo,
            'host': parsed.netloc
        }
    
    raise ValueError(f"Invalid repository URL format: {url}")


def validate_branch_name(branch_name: str) -> bool:
    """Validate branch name according to Git naming rules."""
    if not branch_name:
        return False
    
    # Basic validation - can be extended
    invalid_chars = [' ', '~', '^', ':', '?', '*', '[', '\\']
    if any(char in branch_name for char in invalid_chars):
        return False
    
    if branch_name.startswith('.') or branch_name.endswith('.'):
        return False
    
    if '..' in branch_name:
        return False
    
    return True


def generate_branch_name(prefix: str = "feature", suffix: Optional[str] = None) -> str:
    """Generate a valid branch name with timestamp."""
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    
    if suffix:
        return f"{prefix}/{suffix}-{timestamp}"
    else:
        return f"{prefix}/{timestamp}"