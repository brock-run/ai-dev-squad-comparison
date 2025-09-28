"""
GitHub VCS Provider Implementation

This module provides a comprehensive GitHub API integration with:
- Full GitHub REST API v4 support
- Branch creation, commit, and pull request workflows
- Authentication with minimal-scope token management
- PR template system with customizable templates
- GitHub-specific error handling and status checking
- Rate limit handling and retry logic
- Webhook and status check integration
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from urllib.parse import quote

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from .base import (
    BaseVCSProvider, VCSError, RateLimitError, AuthenticationError,
    NotFoundError, PermissionError, RequestMethod, Repository, Branch,
    Commit, PullRequest, RateLimitInfo, RetryConfig
)

logger = logging.getLogger(__name__)


class GitHubError(VCSError):
    """GitHub-specific error."""
    
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[Dict[str, Any]] = None,
                 documentation_url: Optional[str] = None):
        super().__init__(message, status_code, response_data)
        self.documentation_url = documentation_url


class GitHubRateLimitError(RateLimitError):
    """GitHub-specific rate limit error."""
    
    def __init__(self, message: str, reset_time: Optional[datetime] = None,
                 remaining_requests: Optional[int] = None,
                 limit_type: str = "core"):
        super().__init__(message, reset_time, remaining_requests)
        self.limit_type = limit_type  # core, search, graphql, etc.


class GitHubProvider(BaseVCSProvider):
    """GitHub VCS provider implementation."""
    
    def __init__(self, 
                 base_url: str = "https://api.github.com",
                 retry_config: Optional[RetryConfig] = None,
                 timeout: int = 30):
        super().__init__(base_url, "github", retry_config)
        self.timeout = ClientTimeout(total=timeout)
        self.session: Optional[ClientSession] = None
        self.user_info: Optional[Dict[str, Any]] = None
        
        # GitHub-specific settings
        self.api_version = "2022-11-28"
        self.user_agent = "ai-dev-squad-comparison/1.0"
        
        # Template settings
        self.pr_templates: Dict[str, str] = {}
        self.default_pr_template = """## Description
{description}

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for changes (if applicable)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if applicable)
"""
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if self.session is None or self.session.closed:
            self.session = ClientSession(
                timeout=self.timeout,
                headers=self._get_base_headers()
            )
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _get_base_headers(self) -> Dict[str, str]:
        """Get base headers for all requests."""
        return {
            'User-Agent': self.user_agent,
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': self.api_version
        }
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if not self.token:
            return {}
        
        # Support both personal access tokens and GitHub App tokens
        if self.token.startswith('ghp_') or self.token.startswith('github_pat_'):
            # Personal access token
            return {'Authorization': f'Bearer {self.token}'}
        elif self.token.startswith('ghs_'):
            # GitHub App installation token
            return {'Authorization': f'token {self.token}'}
        else:
            # Assume personal access token format
            return {'Authorization': f'Bearer {self.token}'}
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """Parse GitHub rate limit headers."""
        if 'x-ratelimit-limit' in headers:
            reset_timestamp = int(headers.get('x-ratelimit-reset', 0))
            return RateLimitInfo(
                limit=int(headers['x-ratelimit-limit']),
                remaining=int(headers.get('x-ratelimit-remaining', 0)),
                reset_time=datetime.fromtimestamp(reset_timestamp),
                used=int(headers.get('x-ratelimit-used', 0))
            )
        return None
    
    def _handle_github_error(self, status_code: int, response_data: Dict[str, Any]) -> GitHubError:
        """Handle GitHub-specific error responses."""
        message = response_data.get('message', f'GitHub API error: {status_code}')
        documentation_url = response_data.get('documentation_url')
        
        if status_code == 401:
            return AuthenticationError(f"GitHub authentication failed: {message}")
        elif status_code == 403:
            # Check if it's a rate limit error
            if 'rate limit' in message.lower() or 'api rate limit' in message.lower():
                reset_time = None
                if 'x-ratelimit-reset' in response_data:
                    reset_time = datetime.fromtimestamp(int(response_data['x-ratelimit-reset']))
                return GitHubRateLimitError(
                    message, 
                    reset_time=reset_time,
                    remaining_requests=0
                )
            else:
                return PermissionError(f"GitHub permission denied: {message}")
        elif status_code == 404:
            return NotFoundError(f"GitHub resource not found: {message}")
        elif status_code == 422:
            # Validation error
            errors = response_data.get('errors', [])
            error_details = '; '.join([f"{e.get('field', 'field')}: {e.get('message', 'error')}" 
                                     for e in errors])
            return GitHubError(f"GitHub validation error: {message}. Details: {error_details}", 
                             status_code, response_data, documentation_url)
        else:
            return GitHubError(message, status_code, response_data, documentation_url)
    
    async def _make_request(self, 
                          method: RequestMethod, 
                          endpoint: str,
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make HTTP request to GitHub API."""
        await self._ensure_session()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Prepare headers
        request_headers = self._get_base_headers()
        request_headers.update(self._get_auth_headers())
        if headers:
            request_headers.update(headers)
        
        async def _request():
            # Check rate limits before making request
            if self.rate_limit_manager.is_rate_limited(self.provider_name):
                wait_time = self.rate_limit_manager.get_wait_time(self.provider_name)
                raise GitHubRateLimitError(
                    f"GitHub rate limit exceeded, reset in {wait_time}s",
                    reset_time=datetime.utcnow() + timedelta(seconds=wait_time)
                )
            
            # Record request for rate limiting
            self.rate_limit_manager.record_request(self.provider_name)
            
            logger.debug(f"Making {method.value} request to {url}")
            
            try:
                async with self.session.request(
                    method.value,
                    url,
                    json=data,
                    params=params,
                    headers=request_headers
                ) as response:
                    # Update rate limit information
                    rate_limit_info = self._parse_rate_limit_headers(dict(response.headers))
                    if rate_limit_info:
                        self.rate_limit_manager.update_rate_limit(self.provider_name, rate_limit_info)
                    
                    # Get response data
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                    else:
                        response_text = await response.text()
                        response_data = {'content': response_text}
                    
                    # Handle error responses
                    if response.status >= 400:
                        error = self._handle_github_error(response.status, response_data)
                        raise error
                    
                    return response_data
                    
            except aiohttp.ClientError as e:
                raise GitHubError(f"GitHub API request failed: {e}")
        
        return await self.retry_middleware.execute_with_retry(
            _request,
            method=method,
            url=url
        )
    
    async def authenticate(self, token: str) -> bool:
        """Authenticate with GitHub using a personal access token or GitHub App token."""
        self.token = token
        
        try:
            # Test authentication by getting user info
            user_data = await self._make_request(RequestMethod.GET, "/user")
            self.user_info = user_data
            self.authenticated = True
            
            logger.info(f"Successfully authenticated with GitHub as {user_data.get('login', 'unknown')}")
            return True
            
        except (AuthenticationError, PermissionError) as e:
            self.authenticated = False
            self.user_info = None
            logger.error(f"GitHub authentication failed: {e}")
            return False
    
    async def get_repository(self, owner: str, repo: str) -> Repository:
        """Get repository information."""
        endpoint = f"/repos/{owner}/{repo}"
        repo_data = await self._make_request(RequestMethod.GET, endpoint)
        
        return Repository(
            name=repo_data['name'],
            full_name=repo_data['full_name'],
            owner=repo_data['owner']['login'],
            url=repo_data['html_url'],
            clone_url=repo_data['clone_url'],
            default_branch=repo_data.get('default_branch', 'main'),
            private=repo_data['private'],
            description=repo_data.get('description')
        )
    
    async def list_branches(self, owner: str, repo: str, 
                          protected: Optional[bool] = None) -> List[Branch]:
        """List repository branches."""
        endpoint = f"/repos/{owner}/{repo}/branches"
        params = {}
        if protected is not None:
            params['protected'] = str(protected).lower()
        
        branches_data = await self._make_request(RequestMethod.GET, endpoint, params=params)
        
        branches = []
        for branch_data in branches_data:
            branches.append(Branch(
                name=branch_data['name'],
                sha=branch_data['commit']['sha'],
                protected=branch_data.get('protected', False),
                url=branch_data.get('_links', {}).get('html')
            ))
        
        return branches
    
    async def get_branch(self, owner: str, repo: str, branch: str) -> Branch:
        """Get specific branch information."""
        endpoint = f"/repos/{owner}/{repo}/branches/{branch}"
        branch_data = await self._make_request(RequestMethod.GET, endpoint)
        
        return Branch(
            name=branch_data['name'],
            sha=branch_data['commit']['sha'],
            protected=branch_data.get('protected', False),
            url=branch_data.get('_links', {}).get('html')
        )
    
    async def create_branch(self, owner: str, repo: str, branch_name: str,
                          source_branch: str = "main") -> Branch:
        """Create a new branch from source branch."""
        # First, get the SHA of the source branch
        source_branch_info = await self.get_branch(owner, repo, source_branch)
        
        # Create the new branch reference
        endpoint = f"/repos/{owner}/{repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": source_branch_info.sha
        }
        
        await self._make_request(RequestMethod.POST, endpoint, data=data)
        
        # Return the new branch info
        return await self.get_branch(owner, repo, branch_name)
    
    async def delete_branch(self, owner: str, repo: str, branch: str) -> bool:
        """Delete a branch."""
        endpoint = f"/repos/{owner}/{repo}/git/refs/heads/{branch}"
        
        try:
            await self._make_request(RequestMethod.DELETE, endpoint)
            return True
        except NotFoundError:
            return False
    
    async def get_file_content(self, owner: str, repo: str, path: str, 
                             branch: str = "main") -> Dict[str, Any]:
        """Get file content from repository."""
        endpoint = f"/repos/{owner}/{repo}/contents/{quote(path)}"
        params = {"ref": branch}
        
        file_data = await self._make_request(RequestMethod.GET, endpoint, params=params)
        
        # Decode base64 content if it's a file
        if file_data.get('type') == 'file' and 'content' in file_data:
            content = base64.b64decode(file_data['content']).decode('utf-8')
            file_data['decoded_content'] = content
        
        return file_data
    
    async def create_or_update_file(self, owner: str, repo: str, path: str,
                                  content: str, message: str, branch: str,
                                  author_name: Optional[str] = None,
                                  author_email: Optional[str] = None) -> Dict[str, Any]:
        """Create or update a file in the repository."""
        endpoint = f"/repos/{owner}/{repo}/contents/{quote(path)}"
        
        # Check if file exists to get SHA for updates
        sha = None
        try:
            existing_file = await self.get_file_content(owner, repo, path, branch)
            sha = existing_file['sha']
        except NotFoundError:
            pass  # File doesn't exist, will create new
        
        # Prepare commit data
        data = {
            "message": message,
            "content": base64.b64encode(content.encode('utf-8')).decode('ascii'),
            "branch": branch
        }
        
        if sha:
            data["sha"] = sha
        
        if author_name and author_email:
            data["author"] = {
                "name": author_name,
                "email": author_email
            }
        
        return await self._make_request(RequestMethod.PUT, endpoint, data=data)
    
    async def commit_changes(self, owner: str, repo: str, branch: str,
                           message: str, files: Dict[str, str],
                           author_name: Optional[str] = None,
                           author_email: Optional[str] = None) -> Commit:
        """Commit multiple file changes to a branch."""
        # For multiple files, we need to use the Git Data API
        # This is more complex but allows atomic commits of multiple files
        
        # Get the current branch reference
        branch_ref = await self._make_request(
            RequestMethod.GET, 
            f"/repos/{owner}/{repo}/git/refs/heads/{branch}"
        )
        base_sha = branch_ref['object']['sha']
        
        # Get the base tree
        base_tree = await self._make_request(
            RequestMethod.GET,
            f"/repos/{owner}/{repo}/git/trees/{base_sha}"
        )
        
        # Create blobs for each file
        tree_items = []
        for file_path, file_content in files.items():
            # Create blob
            blob_data = {
                "content": file_content,
                "encoding": "utf-8"
            }
            blob_response = await self._make_request(
                RequestMethod.POST,
                f"/repos/{owner}/{repo}/git/blobs",
                data=blob_data
            )
            
            # Add to tree
            tree_items.append({
                "path": file_path,
                "mode": "100644",  # Regular file
                "type": "blob",
                "sha": blob_response['sha']
            })
        
        # Create new tree
        tree_data = {
            "base_tree": base_sha,
            "tree": tree_items
        }
        tree_response = await self._make_request(
            RequestMethod.POST,
            f"/repos/{owner}/{repo}/git/trees",
            data=tree_data
        )
        
        # Create commit
        commit_data = {
            "message": message,
            "tree": tree_response['sha'],
            "parents": [base_sha]
        }
        
        if author_name and author_email:
            commit_data["author"] = {
                "name": author_name,
                "email": author_email
            }
        
        commit_response = await self._make_request(
            RequestMethod.POST,
            f"/repos/{owner}/{repo}/git/commits",
            data=commit_data
        )
        
        # Update branch reference
        ref_data = {
            "sha": commit_response['sha']
        }
        await self._make_request(
            RequestMethod.PATCH,
            f"/repos/{owner}/{repo}/git/refs/heads/{branch}",
            data=ref_data
        )
        
        # Return commit info
        return Commit(
            sha=commit_response['sha'],
            message=commit_response['message'],
            author=commit_response['author']['name'],
            author_email=commit_response['author']['email'],
            timestamp=datetime.fromisoformat(commit_response['author']['date'].replace('Z', '+00:00')),
            url=commit_response['html_url'],
            parents=[parent['sha'] for parent in commit_response['parents']]
        )
    
    def set_pr_template(self, template_name: str, template_content: str):
        """Set a custom PR template."""
        self.pr_templates[template_name] = template_content
    
    def get_pr_template(self, template_name: str = "default") -> str:
        """Get PR template content."""
        if template_name == "default":
            return self.default_pr_template
        return self.pr_templates.get(template_name, self.default_pr_template)
    
    async def create_pull_request(self, owner: str, repo: str,
                                title: str, description: str,
                                source_branch: str, target_branch: str = "main",
                                draft: bool = False,
                                template_name: str = "default") -> PullRequest:
        """Create a pull request."""
        # Format description with template if requested
        if template_name and description:
            template = self.get_pr_template(template_name)
            if "{description}" in template:
                description = template.format(description=description)
        
        endpoint = f"/repos/{owner}/{repo}/pulls"
        data = {
            "title": title,
            "body": description,
            "head": source_branch,
            "base": target_branch,
            "draft": draft
        }
        
        pr_data = await self._make_request(RequestMethod.POST, endpoint, data=data)
        
        return PullRequest(
            number=pr_data['number'],
            title=pr_data['title'],
            description=pr_data['body'] or '',
            state=pr_data['state'],
            source_branch=pr_data['head']['ref'],
            target_branch=pr_data['base']['ref'],
            author=pr_data['user']['login'],
            url=pr_data['html_url'],
            created_at=datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(pr_data['updated_at'].replace('Z', '+00:00')) if pr_data.get('updated_at') else None,
            merged_at=datetime.fromisoformat(pr_data['merged_at'].replace('Z', '+00:00')) if pr_data.get('merged_at') else None
        )
    
    async def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequest:
        """Get pull request information."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{number}"
        pr_data = await self._make_request(RequestMethod.GET, endpoint)
        
        return PullRequest(
            number=pr_data['number'],
            title=pr_data['title'],
            description=pr_data['body'] or '',
            state=pr_data['state'],
            source_branch=pr_data['head']['ref'],
            target_branch=pr_data['base']['ref'],
            author=pr_data['user']['login'],
            url=pr_data['html_url'],
            created_at=datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(pr_data['updated_at'].replace('Z', '+00:00')) if pr_data.get('updated_at') else None,
            merged_at=datetime.fromisoformat(pr_data['merged_at'].replace('Z', '+00:00')) if pr_data.get('merged_at') else None
        )
    
    async def list_pull_requests(self, owner: str, repo: str,
                               state: str = "open",
                               sort: str = "created",
                               direction: str = "desc") -> List[PullRequest]:
        """List pull requests."""
        endpoint = f"/repos/{owner}/{repo}/pulls"
        params = {
            "state": state,
            "sort": sort,
            "direction": direction
        }
        
        prs_data = await self._make_request(RequestMethod.GET, endpoint, params=params)
        
        pull_requests = []
        for pr_data in prs_data:
            pull_requests.append(PullRequest(
                number=pr_data['number'],
                title=pr_data['title'],
                description=pr_data['body'] or '',
                state=pr_data['state'],
                source_branch=pr_data['head']['ref'],
                target_branch=pr_data['base']['ref'],
                author=pr_data['user']['login'],
                url=pr_data['html_url'],
                created_at=datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(pr_data['updated_at'].replace('Z', '+00:00')) if pr_data.get('updated_at') else None,
                merged_at=datetime.fromisoformat(pr_data['merged_at'].replace('Z', '+00:00')) if pr_data.get('merged_at') else None
            ))
        
        return pull_requests
    
    async def update_pull_request(self, owner: str, repo: str, number: int,
                                title: Optional[str] = None,
                                description: Optional[str] = None,
                                state: Optional[str] = None) -> PullRequest:
        """Update pull request."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{number}"
        data = {}
        
        if title is not None:
            data['title'] = title
        if description is not None:
            data['body'] = description
        if state is not None:
            data['state'] = state
        
        pr_data = await self._make_request(RequestMethod.PATCH, endpoint, data=data)
        
        return PullRequest(
            number=pr_data['number'],
            title=pr_data['title'],
            description=pr_data['body'] or '',
            state=pr_data['state'],
            source_branch=pr_data['head']['ref'],
            target_branch=pr_data['base']['ref'],
            author=pr_data['user']['login'],
            url=pr_data['html_url'],
            created_at=datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(pr_data['updated_at'].replace('Z', '+00:00')) if pr_data.get('updated_at') else None,
            merged_at=datetime.fromisoformat(pr_data['merged_at'].replace('Z', '+00:00')) if pr_data.get('merged_at') else None
        )
    
    async def merge_pull_request(self, owner: str, repo: str, number: int,
                               commit_title: Optional[str] = None,
                               commit_message: Optional[str] = None,
                               merge_method: str = "merge") -> Dict[str, Any]:
        """Merge a pull request."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{number}/merge"
        data = {
            "merge_method": merge_method  # merge, squash, or rebase
        }
        
        if commit_title:
            data['commit_title'] = commit_title
        if commit_message:
            data['commit_message'] = commit_message
        
        return await self._make_request(RequestMethod.PUT, endpoint, data=data)
    
    async def add_pr_comment(self, owner: str, repo: str, number: int,
                           comment: str) -> Dict[str, Any]:
        """Add a comment to a pull request."""
        endpoint = f"/repos/{owner}/{repo}/issues/{number}/comments"
        data = {"body": comment}
        
        return await self._make_request(RequestMethod.POST, endpoint, data=data)
    
    async def get_pr_reviews(self, owner: str, repo: str, number: int) -> List[Dict[str, Any]]:
        """Get pull request reviews."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{number}/reviews"
        return await self._make_request(RequestMethod.GET, endpoint)
    
    async def create_pr_review(self, owner: str, repo: str, number: int,
                             event: str, body: Optional[str] = None,
                             comments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a pull request review."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{number}/reviews"
        data = {"event": event}  # APPROVE, REQUEST_CHANGES, COMMENT
        
        if body:
            data['body'] = body
        if comments:
            data['comments'] = comments
        
        return await self._make_request(RequestMethod.POST, endpoint, data=data)
    
    async def get_commit_status(self, owner: str, repo: str, sha: str) -> Dict[str, Any]:
        """Get commit status checks."""
        endpoint = f"/repos/{owner}/{repo}/commits/{sha}/status"
        return await self._make_request(RequestMethod.GET, endpoint)
    
    async def create_commit_status(self, owner: str, repo: str, sha: str,
                                 state: str, target_url: Optional[str] = None,
                                 description: Optional[str] = None,
                                 context: str = "default") -> Dict[str, Any]:
        """Create a commit status."""
        endpoint = f"/repos/{owner}/{repo}/statuses/{sha}"
        data = {
            "state": state,  # pending, success, error, failure
            "context": context
        }
        
        if target_url:
            data['target_url'] = target_url
        if description:
            data['description'] = description
        
        return await self._make_request(RequestMethod.POST, endpoint, data=data)
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        endpoint = "/rate_limit"
        return await self._make_request(RequestMethod.GET, endpoint)
    
    def get_github_metrics(self) -> Dict[str, Any]:
        """Get GitHub-specific metrics."""
        base_metrics = self.get_metrics()
        
        github_metrics = {
            **base_metrics,
            'user_info': self.user_info,
            'api_version': self.api_version,
            'pr_templates': list(self.pr_templates.keys()),
            'session_active': self.session is not None and not self.session.closed
        }
        
        return github_metrics


# Utility functions for GitHub operations

def parse_github_url(url: str) -> Dict[str, str]:
    """Parse GitHub repository URL to extract owner and repo."""
    from .base import parse_repository_url
    
    parsed = parse_repository_url(url)
    
    # Validate it's a GitHub URL
    if 'github.com' not in parsed['host']:
        raise ValueError(f"Not a GitHub URL: {url}")
    
    return parsed


def validate_github_token(token: str) -> bool:
    """Validate GitHub token format."""
    if not token:
        return False
    
    # GitHub personal access tokens
    if token.startswith('ghp_') and len(token) == 40:
        return True
    
    # GitHub App installation tokens
    if token.startswith('ghs_') and len(token) >= 40:
        return True
    
    # Fine-grained personal access tokens
    if token.startswith('github_pat_') and len(token) >= 82:
        return True
    
    # Classic format (deprecated but still valid)
    if len(token) == 40 and all(c.isalnum() for c in token):
        return True
    
    return False


def get_github_scopes_for_operations(operations: List[str]) -> List[str]:
    """Get required GitHub token scopes for specific operations."""
    scope_mapping = {
        'read_repo': ['repo:status', 'public_repo'],
        'write_repo': ['repo'],
        'create_pr': ['repo', 'pull_requests:write'],
        'merge_pr': ['repo'],
        'create_status': ['repo:status'],
        'read_user': ['user:email'],
        'read_org': ['read:org']
    }
    
    required_scopes = set()
    for operation in operations:
        if operation in scope_mapping:
            required_scopes.update(scope_mapping[operation])
    
    return list(required_scopes)