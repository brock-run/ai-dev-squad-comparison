"""
GitLab VCS Provider Implementation

This module provides a comprehensive GitLab API integration with:
- Full GitLab REST API v4 support
- Merge request workflow with approval handling
- GitLab-specific authentication and scope management
- MR template system matching GitHub functionality
- GitLab-specific error handling and pipeline integration
- Rate limit handling and retry logic
- Project and group management
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from urllib.parse import quote, urljoin

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from .base import (
    BaseVCSProvider, VCSError, RateLimitError, AuthenticationError,
    NotFoundError, PermissionError, RequestMethod, Repository, Branch,
    Commit, PullRequest, RateLimitInfo, RetryConfig
)

logger = logging.getLogger(__name__)


class GitLabError(VCSError):
    """GitLab-specific error."""
    
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[Dict[str, Any]] = None,
                 error_code: Optional[str] = None):
        super().__init__(message, status_code, response_data)
        self.error_code = error_code


class GitLabRateLimitError(RateLimitError):
    """GitLab-specific rate limit error."""
    
    def __init__(self, message: str, reset_time: Optional[datetime] = None,
                 remaining_requests: Optional[int] = None,
                 limit_type: str = "api"):
        super().__init__(message, reset_time, remaining_requests)
        self.limit_type = limit_type  # api, search, etc.


class MergeRequest(PullRequest):
    """GitLab Merge Request (extends PullRequest for compatibility)."""
    
    def __init__(self, *args, **kwargs):
        # Extract GitLab-specific fields
        self.iid = kwargs.pop('iid', None)  # Internal ID
        self.project_id = kwargs.pop('project_id', None)
        self.target_project_id = kwargs.pop('target_project_id', None)
        self.source_project_id = kwargs.pop('source_project_id', None)
        self.merge_status = kwargs.pop('merge_status', None)
        self.pipeline_status = kwargs.pop('pipeline_status', None)
        self.approvals_required = kwargs.pop('approvals_required', 0)
        self.approvals_received = kwargs.pop('approvals_received', 0)
        self.blocking_discussions_resolved = kwargs.pop('blocking_discussions_resolved', True)
        
        super().__init__(*args, **kwargs)
    
    @property
    def can_merge(self) -> bool:
        """Check if MR can be merged."""
        return (
            self.merge_status == 'can_be_merged' and
            self.approvals_received >= self.approvals_required and
            self.blocking_discussions_resolved
        )


class GitLabProvider(BaseVCSProvider):
    """GitLab VCS provider implementation."""
    
    def __init__(self, 
                 base_url: str = "https://gitlab.com/api/v4",
                 retry_config: Optional[RetryConfig] = None,
                 timeout: int = 30):
        super().__init__(base_url, "gitlab", retry_config)
        self.timeout = ClientTimeout(total=timeout)
        self.session: Optional[ClientSession] = None
        self.user_info: Optional[Dict[str, Any]] = None
        
        # GitLab-specific settings
        self.api_version = "v4"
        self.user_agent = "ai-dev-squad-comparison/1.0"
        
        # Template settings
        self.mr_templates: Dict[str, str] = {}
        self.default_mr_template = """## Description
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
- [ ] Pipeline passes

## Merge Request Guidelines
- [ ] Target branch is correct
- [ ] Source branch will be deleted after merge
- [ ] Squash commits if appropriate
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
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if not self.token:
            return {}
        
        # GitLab supports multiple authentication methods
        if self.token.startswith('glpat-'):
            # Personal Access Token
            return {'Private-Token': self.token}
        elif self.token.startswith('gloas-'):
            # OAuth Application Secret
            return {'Authorization': f'Bearer {self.token}'}
        elif self.token.startswith('gldt-'):
            # Deploy Token
            return {'Deploy-Token': self.token}
        else:
            # Assume Personal Access Token format
            return {'Private-Token': self.token}
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """Parse GitLab rate limit headers."""
        if 'ratelimit-limit' in headers:
            reset_timestamp = int(headers.get('ratelimit-reset', 0))
            return RateLimitInfo(
                limit=int(headers['ratelimit-limit']),
                remaining=int(headers.get('ratelimit-remaining', 0)),
                reset_time=datetime.fromtimestamp(reset_timestamp),
                used=int(headers.get('ratelimit-observed', 0))
            )
        return None
    
    def _handle_gitlab_error(self, status_code: int, response_data: Dict[str, Any]) -> GitLabError:
        """Handle GitLab-specific error responses."""
        if isinstance(response_data, dict):
            message = response_data.get('message', f'GitLab API error: {status_code}')
            error_code = response_data.get('error', None)
        else:
            message = f'GitLab API error: {status_code}'
            error_code = None
        
        if status_code == 401:
            return AuthenticationError(f"GitLab authentication failed: {message}")
        elif status_code == 403:
            # Check if it's a rate limit error
            if 'rate limit' in message.lower() or 'too many requests' in message.lower():
                return GitLabRateLimitError(message, remaining_requests=0)
            else:
                return PermissionError(f"GitLab permission denied: {message}")
        elif status_code == 404:
            return NotFoundError(f"GitLab resource not found: {message}")
        elif status_code == 422:
            # Validation error
            error_details = ""
            if isinstance(response_data, dict) and 'error' in response_data:
                if isinstance(response_data['error'], dict):
                    error_details = '; '.join([f"{k}: {v}" for k, v in response_data['error'].items()])
                else:
                    error_details = str(response_data['error'])
            return GitLabError(f"GitLab validation error: {message}. Details: {error_details}", 
                             status_code, response_data, error_code)
        elif status_code == 429:
            return GitLabRateLimitError(message, remaining_requests=0)
        else:
            return GitLabError(message, status_code, response_data, error_code)
    
    async def _make_request(self, 
                          method: RequestMethod, 
                          endpoint: str,
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make HTTP request to GitLab API."""
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
                raise GitLabRateLimitError(
                    f"GitLab rate limit exceeded, reset in {wait_time}s",
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
                        error = self._handle_gitlab_error(response.status, response_data)
                        raise error
                    
                    return response_data
                    
            except aiohttp.ClientError as e:
                raise GitLabError(f"GitLab API request failed: {e}")
        
        return await self.retry_middleware.execute_with_retry(
            _request,
            method=method,
            url=url
        )
    
    def _get_project_path(self, owner: str, repo: str) -> str:
        """Get GitLab project path (URL encoded)."""
        return quote(f"{owner}/{repo}", safe='')
    
    async def authenticate(self, token: str) -> bool:
        """Authenticate with GitLab using a personal access token or other token type."""
        self.token = token
        
        try:
            # Test authentication by getting user info
            user_data = await self._make_request(RequestMethod.GET, "/user")
            self.user_info = user_data
            self.authenticated = True
            
            logger.info(f"Successfully authenticated with GitLab as {user_data.get('username', 'unknown')}")
            return True
            
        except (AuthenticationError, PermissionError) as e:
            self.authenticated = False
            self.user_info = None
            logger.error(f"GitLab authentication failed: {e}")
            return False
    
    async def get_repository(self, owner: str, repo: str) -> Repository:
        """Get repository (project) information."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}"
        project_data = await self._make_request(RequestMethod.GET, endpoint)
        
        return Repository(
            name=project_data['name'],
            full_name=project_data['path_with_namespace'],
            owner=project_data['namespace']['path'],
            url=project_data['web_url'],
            clone_url=project_data['http_url_to_repo'],
            default_branch=project_data.get('default_branch', 'main'),
            private=project_data['visibility'] == 'private',
            description=project_data.get('description')
        )
    
    async def list_branches(self, owner: str, repo: str, 
                          search: Optional[str] = None) -> List[Branch]:
        """List repository branches."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/repository/branches"
        params = {}
        if search:
            params['search'] = search
        
        branches_data = await self._make_request(RequestMethod.GET, endpoint, params=params)
        
        branches = []
        for branch_data in branches_data:
            branches.append(Branch(
                name=branch_data['name'],
                sha=branch_data['commit']['id'],
                protected=branch_data.get('protected', False),
                url=branch_data.get('web_url')
            ))
        
        return branches
    
    async def get_branch(self, owner: str, repo: str, branch: str) -> Branch:
        """Get specific branch information."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/repository/branches/{quote(branch, safe='')}"
        branch_data = await self._make_request(RequestMethod.GET, endpoint)
        
        return Branch(
            name=branch_data['name'],
            sha=branch_data['commit']['id'],
            protected=branch_data.get('protected', False),
            url=branch_data.get('web_url')
        )
    
    async def create_branch(self, owner: str, repo: str, branch_name: str,
                          source_branch: str = "main") -> Branch:
        """Create a new branch from source branch."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/repository/branches"
        
        data = {
            "branch": branch_name,
            "ref": source_branch
        }
        
        branch_data = await self._make_request(RequestMethod.POST, endpoint, data=data)
        
        return Branch(
            name=branch_data['name'],
            sha=branch_data['commit']['id'],
            protected=branch_data.get('protected', False),
            url=branch_data.get('web_url')
        )
    
    async def delete_branch(self, owner: str, repo: str, branch: str) -> bool:
        """Delete a branch."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/repository/branches/{quote(branch, safe='')}"
        
        try:
            await self._make_request(RequestMethod.DELETE, endpoint)
            return True
        except NotFoundError:
            return False
    
    async def get_file_content(self, owner: str, repo: str, path: str, 
                             branch: str = "main") -> Dict[str, Any]:
        """Get file content from repository."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/repository/files/{quote(path, safe='')}"
        params = {"ref": branch}
        
        file_data = await self._make_request(RequestMethod.GET, endpoint, params=params)
        
        # Decode base64 content
        if 'content' in file_data:
            content = base64.b64decode(file_data['content']).decode('utf-8')
            file_data['decoded_content'] = content
        
        return file_data
    
    async def create_or_update_file(self, owner: str, repo: str, path: str,
                                  content: str, message: str, branch: str,
                                  author_name: Optional[str] = None,
                                  author_email: Optional[str] = None) -> Dict[str, Any]:
        """Create or update a file in the repository."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/repository/files/{quote(path, safe='')}"
        
        # Check if file exists to determine if we should create or update
        try:
            await self.get_file_content(owner, repo, path, branch)
            method = RequestMethod.PUT  # File exists, update it
        except NotFoundError:
            method = RequestMethod.POST  # File doesn't exist, create it
        
        # Prepare commit data
        data = {
            "branch": branch,
            "content": content,
            "commit_message": message,
            "encoding": "text"
        }
        
        if author_name:
            data["author_name"] = author_name
        if author_email:
            data["author_email"] = author_email
        
        return await self._make_request(method, endpoint, data=data)
    
    async def commit_changes(self, owner: str, repo: str, branch: str,
                           message: str, files: Dict[str, str],
                           author_name: Optional[str] = None,
                           author_email: Optional[str] = None) -> Commit:
        """Commit multiple file changes to a branch."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/repository/commits"
        
        # Prepare actions for each file
        actions = []
        for file_path, file_content in files.items():
            # Check if file exists to determine action
            try:
                await self.get_file_content(owner, repo, file_path, branch)
                action = "update"
            except NotFoundError:
                action = "create"
            
            actions.append({
                "action": action,
                "file_path": file_path,
                "content": file_content,
                "encoding": "text"
            })
        
        # Prepare commit data
        data = {
            "branch": branch,
            "commit_message": message,
            "actions": actions
        }
        
        if author_name:
            data["author_name"] = author_name
        if author_email:
            data["author_email"] = author_email
        
        commit_data = await self._make_request(RequestMethod.POST, endpoint, data=data)
        
        # Return commit info
        return Commit(
            sha=commit_data['id'],
            message=commit_data['message'],
            author=commit_data['author_name'],
            author_email=commit_data['author_email'],
            timestamp=datetime.fromisoformat(commit_data['created_at'].replace('Z', '+00:00')),
            url=commit_data.get('web_url'),
            parents=[parent['id'] for parent in commit_data.get('parent_ids', [])]
        )
    
    def set_mr_template(self, template_name: str, template_content: str):
        """Set a custom MR template."""
        self.mr_templates[template_name] = template_content
    
    def get_mr_template(self, template_name: str = "default") -> str:
        """Get MR template content."""
        if template_name == "default":
            return self.default_mr_template
        return self.mr_templates.get(template_name, self.default_mr_template)
    
    async def create_pull_request(self, owner: str, repo: str,
                                title: str, description: str,
                                source_branch: str, target_branch: str = "main",
                                draft: bool = False,
                                template_name: str = "default") -> PullRequest:
        """Create a merge request (GitLab's equivalent of pull request)."""
        # Format description with template if requested
        if template_name and description:
            template = self.get_mr_template(template_name)
            if "{description}" in template:
                description = template.format(description=description)
        
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests"
        
        data = {
            "title": title,
            "description": description,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "remove_source_branch": True  # GitLab default behavior
        }
        
        # GitLab uses work_in_progress for draft MRs
        if draft:
            data["title"] = f"Draft: {title}"
        
        mr_data = await self._make_request(RequestMethod.POST, endpoint, data=data)
        
        return MergeRequest(
            number=mr_data['id'],  # Use ID for compatibility
            iid=mr_data['iid'],    # Internal ID
            project_id=mr_data['project_id'],
            title=mr_data['title'],
            description=mr_data['description'] or '',
            state=mr_data['state'],
            source_branch=mr_data['source_branch'],
            target_branch=mr_data['target_branch'],
            author=mr_data['author']['username'],
            url=mr_data['web_url'],
            created_at=datetime.fromisoformat(mr_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(mr_data['updated_at'].replace('Z', '+00:00')) if mr_data.get('updated_at') else None,
            merged_at=datetime.fromisoformat(mr_data['merged_at'].replace('Z', '+00:00')) if mr_data.get('merged_at') else None,
            merge_status=mr_data.get('merge_status'),
            pipeline_status=mr_data.get('pipeline', {}).get('status') if mr_data.get('pipeline') else None
        )
    
    async def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequest:
        """Get merge request information."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests/{number}"
        mr_data = await self._make_request(RequestMethod.GET, endpoint)
        
        return MergeRequest(
            number=mr_data['id'],
            iid=mr_data['iid'],
            project_id=mr_data['project_id'],
            title=mr_data['title'],
            description=mr_data['description'] or '',
            state=mr_data['state'],
            source_branch=mr_data['source_branch'],
            target_branch=mr_data['target_branch'],
            author=mr_data['author']['username'],
            url=mr_data['web_url'],
            created_at=datetime.fromisoformat(mr_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(mr_data['updated_at'].replace('Z', '+00:00')) if mr_data.get('updated_at') else None,
            merged_at=datetime.fromisoformat(mr_data['merged_at'].replace('Z', '+00:00')) if mr_data.get('merged_at') else None,
            merge_status=mr_data.get('merge_status'),
            pipeline_status=mr_data.get('pipeline', {}).get('status') if mr_data.get('pipeline') else None
        )
    
    async def list_pull_requests(self, owner: str, repo: str,
                               state: str = "opened",
                               sort: str = "created_at",
                               order_by: str = "desc") -> List[PullRequest]:
        """List merge requests."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests"
        params = {
            "state": state,
            "sort": sort,
            "order_by": order_by
        }
        
        mrs_data = await self._make_request(RequestMethod.GET, endpoint, params=params)
        
        merge_requests = []
        for mr_data in mrs_data:
            merge_requests.append(MergeRequest(
                number=mr_data['id'],
                iid=mr_data['iid'],
                project_id=mr_data['project_id'],
                title=mr_data['title'],
                description=mr_data['description'] or '',
                state=mr_data['state'],
                source_branch=mr_data['source_branch'],
                target_branch=mr_data['target_branch'],
                author=mr_data['author']['username'],
                url=mr_data['web_url'],
                created_at=datetime.fromisoformat(mr_data['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(mr_data['updated_at'].replace('Z', '+00:00')) if mr_data.get('updated_at') else None,
                merged_at=datetime.fromisoformat(mr_data['merged_at'].replace('Z', '+00:00')) if mr_data.get('merged_at') else None,
                merge_status=mr_data.get('merge_status'),
                pipeline_status=mr_data.get('pipeline', {}).get('status') if mr_data.get('pipeline') else None
            ))
        
        return merge_requests
    
    async def update_pull_request(self, owner: str, repo: str, number: int,
                                title: Optional[str] = None,
                                description: Optional[str] = None,
                                state: Optional[str] = None) -> PullRequest:
        """Update merge request."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests/{number}"
        data = {}
        
        if title is not None:
            data['title'] = title
        if description is not None:
            data['description'] = description
        if state is not None:
            data['state_event'] = state  # GitLab uses state_event
        
        mr_data = await self._make_request(RequestMethod.PUT, endpoint, data=data)
        
        return MergeRequest(
            number=mr_data['id'],
            iid=mr_data['iid'],
            project_id=mr_data['project_id'],
            title=mr_data['title'],
            description=mr_data['description'] or '',
            state=mr_data['state'],
            source_branch=mr_data['source_branch'],
            target_branch=mr_data['target_branch'],
            author=mr_data['author']['username'],
            url=mr_data['web_url'],
            created_at=datetime.fromisoformat(mr_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(mr_data['updated_at'].replace('Z', '+00:00')) if mr_data.get('updated_at') else None,
            merged_at=datetime.fromisoformat(mr_data['merged_at'].replace('Z', '+00:00')) if mr_data.get('merged_at') else None,
            merge_status=mr_data.get('merge_status'),
            pipeline_status=mr_data.get('pipeline', {}).get('status') if mr_data.get('pipeline') else None
        )
    
    async def merge_pull_request(self, owner: str, repo: str, number: int,
                               commit_title: Optional[str] = None,
                               commit_message: Optional[str] = None,
                               merge_method: str = "merge") -> Dict[str, Any]:
        """Merge a merge request."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests/{number}/merge"
        
        data = {}
        if commit_title:
            data['merge_commit_message'] = commit_title
        if commit_message:
            data['merge_commit_message'] = f"{commit_title}\n\n{commit_message}" if commit_title else commit_message
        
        # GitLab merge options
        if merge_method == "squash":
            data['squash'] = True
        elif merge_method == "rebase":
            data['should_remove_source_branch'] = True
        
        return await self._make_request(RequestMethod.PUT, endpoint, data=data)
    
    async def add_pr_comment(self, owner: str, repo: str, number: int,
                           comment: str) -> Dict[str, Any]:
        """Add a note to a merge request."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests/{number}/notes"
        data = {"body": comment}
        
        return await self._make_request(RequestMethod.POST, endpoint, data=data)
    
    async def get_mr_approvals(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        """Get merge request approval information."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests/{number}/approvals"
        return await self._make_request(RequestMethod.GET, endpoint)
    
    async def approve_merge_request(self, owner: str, repo: str, number: int,
                                  approval_password: Optional[str] = None) -> Dict[str, Any]:
        """Approve a merge request."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests/{number}/approve"
        
        data = {}
        if approval_password:
            data['approval_password'] = approval_password
        
        return await self._make_request(RequestMethod.POST, endpoint, data=data)
    
    async def unapprove_merge_request(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        """Remove approval from a merge request."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/merge_requests/{number}/unapprove"
        return await self._make_request(RequestMethod.POST, endpoint)
    
    async def get_pipeline_status(self, owner: str, repo: str, sha: str) -> Dict[str, Any]:
        """Get pipeline status for a commit."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/pipelines"
        params = {"sha": sha}
        
        pipelines = await self._make_request(RequestMethod.GET, endpoint, params=params)
        
        if pipelines:
            # Return the most recent pipeline
            return pipelines[0]
        else:
            return {"status": "not_found"}
    
    async def create_pipeline(self, owner: str, repo: str, branch: str,
                            variables: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a new pipeline."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/pipeline"
        
        data = {"ref": branch}
        if variables:
            data["variables"] = [{"key": k, "value": v} for k, v in variables.items()]
        
        return await self._make_request(RequestMethod.POST, endpoint, data=data)
    
    async def get_project_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed project information."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}"
        return await self._make_request(RequestMethod.GET, endpoint)
    
    async def list_project_members(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List project members."""
        project_path = self._get_project_path(owner, repo)
        endpoint = f"/projects/{project_path}/members"
        return await self._make_request(RequestMethod.GET, endpoint)
    
    def get_gitlab_metrics(self) -> Dict[str, Any]:
        """Get GitLab-specific metrics."""
        base_metrics = self.get_metrics()
        
        gitlab_metrics = {
            **base_metrics,
            'user_info': self.user_info,
            'api_version': self.api_version,
            'mr_templates': list(self.mr_templates.keys()),
            'session_active': self.session is not None and not self.session.closed
        }
        
        return gitlab_metrics


# Utility functions for GitLab operations

def parse_gitlab_url(url: str) -> Dict[str, str]:
    """Parse GitLab repository URL to extract owner and repo."""
    from .base import parse_repository_url
    
    parsed = parse_repository_url(url)
    
    # Validate it's a GitLab URL
    if 'gitlab' not in parsed['host']:
        raise ValueError(f"Not a GitLab URL: {url}")
    
    return parsed


def validate_gitlab_token(token: str) -> bool:
    """Validate GitLab token format."""
    if not token:
        return False
    
    # GitLab personal access tokens
    if token.startswith('glpat-') and len(token) >= 20:
        return True
    
    # GitLab OAuth application secrets
    if token.startswith('gloas-') and len(token) >= 64:
        return True
    
    # GitLab deploy tokens
    if token.startswith('gldt-') and len(token) >= 20:
        return True
    
    # Legacy format (still supported)
    if len(token) >= 20 and all(c.isalnum() or c in '-_' for c in token):
        return True
    
    return False


def get_gitlab_scopes_for_operations(operations: List[str]) -> List[str]:
    """Get required GitLab token scopes for specific operations."""
    scope_mapping = {
        'read_api': ['read_api'],
        'read_repository': ['read_repository'],
        'write_repository': ['write_repository'],
        'read_user': ['read_user'],
        'api': ['api'],  # Full API access
        'read_registry': ['read_registry'],
        'write_registry': ['write_registry']
    }
    
    required_scopes = set()
    for operation in operations:
        if operation in scope_mapping:
            required_scopes.update(scope_mapping[operation])
    
    return list(required_scopes)


def convert_github_to_gitlab_workflow(github_workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Convert GitHub Actions workflow to GitLab CI format."""
    # This is a basic converter - real implementation would be more comprehensive
    gitlab_ci = {
        'stages': ['build', 'test', 'deploy'],
        'variables': {},
        'before_script': [],
        'after_script': []
    }
    
    # Convert jobs
    if 'jobs' in github_workflow:
        for job_name, job_config in github_workflow['jobs'].items():
            gitlab_job = {
                'stage': 'build',  # Default stage
                'script': []
            }
            
            # Convert steps to script
            if 'steps' in job_config:
                for step in job_config['steps']:
                    if 'run' in step:
                        gitlab_job['script'].append(step['run'])
            
            gitlab_ci[job_name] = gitlab_job
    
    return gitlab_ci