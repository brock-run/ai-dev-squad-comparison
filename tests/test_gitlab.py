"""
Tests for GitLab VCS provider implementation.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientResponse
import json

from common.vcs.gitlab import (
    GitLabProvider, GitLabError, GitLabRateLimitError, MergeRequest,
    parse_gitlab_url, validate_gitlab_token, get_gitlab_scopes_for_operations,
    convert_github_to_gitlab_workflow
)
from common.vcs.base import (
    Repository, Branch, Commit, PullRequest, AuthenticationError,
    NotFoundError, PermissionError, RequestMethod
)


class MockResponse:
    """Mock aiohttp response for testing."""
    
    def __init__(self, status: int, data: dict, headers: dict = None):
        self.status = status
        self.data = data
        self.headers = headers or {}
        self.content_type = 'application/json'
    
    async def json(self):
        return self.data
    
    async def text(self):
        return json.dumps(self.data)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestMergeRequest:
    """Test MergeRequest class functionality."""
    
    def test_merge_request_creation(self):
        """Test creating a MergeRequest instance."""
        mr = MergeRequest(
            number=123,
            iid=45,
            project_id=678,
            title="Test MR",
            description="Test description",
            state="opened",
            source_branch="feature/test",
            target_branch="main",
            author="testuser",
            url="https://gitlab.com/owner/repo/-/merge_requests/45",
            created_at=datetime.utcnow(),
            merge_status="can_be_merged",
            pipeline_status="success",
            approvals_required=2,
            approvals_received=1,
            blocking_discussions_resolved=True
        )
        
        assert mr.number == 123
        assert mr.iid == 45
        assert mr.project_id == 678
        assert mr.merge_status == "can_be_merged"
        assert mr.pipeline_status == "success"
        assert mr.approvals_required == 2
        assert mr.approvals_received == 1
        assert mr.blocking_discussions_resolved is True
    
    def test_can_merge_property(self):
        """Test can_merge property logic."""
        # Can merge - all conditions met
        mr = MergeRequest(
            number=123, title="Test", description="", state="opened",
            source_branch="feature", target_branch="main", author="user",
            url="https://gitlab.com/test", created_at=datetime.utcnow(),
            merge_status="can_be_merged",
            approvals_required=2,
            approvals_received=2,
            blocking_discussions_resolved=True
        )
        assert mr.can_merge is True
        
        # Cannot merge - insufficient approvals
        mr.approvals_received = 1
        assert mr.can_merge is False
        
        # Cannot merge - blocking discussions
        mr.approvals_received = 2
        mr.blocking_discussions_resolved = False
        assert mr.can_merge is False
        
        # Cannot merge - merge conflicts
        mr.blocking_discussions_resolved = True
        mr.merge_status = "cannot_be_merged"
        assert mr.can_merge is False


class TestGitLabProvider:
    """Test GitLabProvider functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.provider = GitLabProvider()
    
    async def teardown_method(self):
        """Clean up after tests."""
        await self.provider.close()
    
    def test_initialization(self):
        """Test provider initialization."""
        assert self.provider.base_url == "https://gitlab.com/api/v4"
        assert self.provider.provider_name == "gitlab"
        assert self.provider.api_version == "v4"
        assert self.provider.authenticated is False
        assert self.provider.token is None
        assert self.provider.user_info is None
    
    def test_get_base_headers(self):
        """Test base headers generation."""
        headers = self.provider._get_base_headers()
        
        assert headers['User-Agent'] == self.provider.user_agent
        assert headers['Accept'] == 'application/json'
        assert headers['Content-Type'] == 'application/json'
    
    def test_get_auth_headers(self):
        """Test authentication headers for different token types."""
        # No token
        headers = self.provider._get_auth_headers()
        assert headers == {}
        
        # Personal access token
        self.provider.token = "glpat-xxxxxxxxxxxxxxxxxxxx"
        headers = self.provider._get_auth_headers()
        assert headers['Private-Token'] == self.provider.token
        
        # OAuth application secret
        self.provider.token = "gloas-" + "x" * 60
        headers = self.provider._get_auth_headers()
        assert headers['Authorization'] == f"Bearer {self.provider.token}"
        
        # Deploy token
        self.provider.token = "gldt-xxxxxxxxxxxxxxxxxxxx"
        headers = self.provider._get_auth_headers()
        assert headers['Deploy-Token'] == self.provider.token
        
        # Legacy format
        self.provider.token = "legacy_token_format_123"
        headers = self.provider._get_auth_headers()
        assert headers['Private-Token'] == self.provider.token
    
    def test_parse_rate_limit_headers(self):
        """Test parsing GitLab rate limit headers."""
        headers = {
            'ratelimit-limit': '2000',
            'ratelimit-remaining': '1500',
            'ratelimit-reset': '1640995200',  # 2022-01-01 00:00:00 UTC
            'ratelimit-observed': '500'
        }
        
        rate_limit = self.provider._parse_rate_limit_headers(headers)
        
        assert rate_limit is not None
        assert rate_limit.limit == 2000
        assert rate_limit.remaining == 1500
        assert rate_limit.used == 500
        assert rate_limit.reset_time == datetime.fromtimestamp(1640995200)
    
    def test_get_project_path(self):
        """Test project path encoding."""
        path = self.provider._get_project_path("owner", "repo")
        assert path == "owner%2Frepo"
        
        # Test with special characters
        path = self.provider._get_project_path("owner-name", "repo.name")
        assert path == "owner-name%2Frepo.name"
    
    def test_handle_gitlab_error(self):
        """Test GitLab error handling."""
        # Authentication error
        error = self.provider._handle_gitlab_error(401, {"message": "401 Unauthorized"})
        assert isinstance(error, AuthenticationError)
        assert "401 Unauthorized" in str(error)
        
        # Rate limit error
        error = self.provider._handle_gitlab_error(429, {"message": "Too Many Requests"})
        assert isinstance(error, GitLabRateLimitError)
        
        # Permission error
        error = self.provider._handle_gitlab_error(403, {"message": "Forbidden"})
        assert isinstance(error, PermissionError)
        
        # Not found error
        error = self.provider._handle_gitlab_error(404, {"message": "404 Project Not Found"})
        assert isinstance(error, NotFoundError)
        
        # Validation error
        error = self.provider._handle_gitlab_error(422, {
            "message": "Validation failed",
            "error": {"name": ["can't be blank"], "email": ["is invalid"]}
        })
        assert isinstance(error, GitLabError)
        assert "Validation failed" in str(error)
        assert "name: ['can't be blank']" in str(error)
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful authentication."""
        mock_user_data = {
            "username": "testuser",
            "id": 12345,
            "email": "test@example.com",
            "name": "Test User"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_user_data
            
            result = await self.provider.authenticate("test-token")
            
            assert result is True
            assert self.provider.authenticated is True
            assert self.provider.token == "test-token"
            assert self.provider.user_info == mock_user_data
            mock_request.assert_called_once_with(RequestMethod.GET, "/user")
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self):
        """Test authentication failure."""
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = AuthenticationError("401 Unauthorized")
            
            result = await self.provider.authenticate("invalid-token")
            
            assert result is False
            assert self.provider.authenticated is False
            assert self.provider.user_info is None
    
    @pytest.mark.asyncio
    async def test_get_repository(self):
        """Test getting repository information."""
        mock_project_data = {
            "name": "test-repo",
            "path_with_namespace": "testuser/test-repo",
            "namespace": {"path": "testuser"},
            "web_url": "https://gitlab.com/testuser/test-repo",
            "http_url_to_repo": "https://gitlab.com/testuser/test-repo.git",
            "default_branch": "main",
            "visibility": "private",
            "description": "A test repository"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_project_data
            
            repo = await self.provider.get_repository("testuser", "test-repo")
            
            assert isinstance(repo, Repository)
            assert repo.name == "test-repo"
            assert repo.full_name == "testuser/test-repo"
            assert repo.owner == "testuser"
            assert repo.url == "https://gitlab.com/testuser/test-repo"
            assert repo.clone_url == "https://gitlab.com/testuser/test-repo.git"
            assert repo.default_branch == "main"
            assert repo.private is True
            assert repo.description == "A test repository"
    
    @pytest.mark.asyncio
    async def test_list_branches(self):
        """Test listing repository branches."""
        mock_branches_data = [
            {
                "name": "main",
                "commit": {"id": "abc123"},
                "protected": True,
                "web_url": "https://gitlab.com/testuser/test-repo/-/tree/main"
            },
            {
                "name": "develop",
                "commit": {"id": "def456"},
                "protected": False,
                "web_url": "https://gitlab.com/testuser/test-repo/-/tree/develop"
            }
        ]
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_branches_data
            
            branches = await self.provider.list_branches("testuser", "test-repo")
            
            assert len(branches) == 2
            
            main_branch = branches[0]
            assert isinstance(main_branch, Branch)
            assert main_branch.name == "main"
            assert main_branch.sha == "abc123"
            assert main_branch.protected is True
            
            develop_branch = branches[1]
            assert develop_branch.name == "develop"
            assert develop_branch.sha == "def456"
            assert develop_branch.protected is False
    
    @pytest.mark.asyncio
    async def test_create_branch(self):
        """Test creating a new branch."""
        mock_branch_data = {
            "name": "feature/new",
            "commit": {"id": "abc123"},
            "protected": False,
            "web_url": "https://gitlab.com/testuser/test-repo/-/tree/feature/new"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_branch_data
            
            branch = await self.provider.create_branch("testuser", "test-repo", "feature/new", "main")
            
            assert isinstance(branch, Branch)
            assert branch.name == "feature/new"
            assert branch.sha == "abc123"
            
            # Verify the API call was made correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.POST
            assert "branches" in call_args[0][1]
            assert call_args[1]['data']['branch'] == "feature/new"
            assert call_args[1]['data']['ref'] == "main"
    
    @pytest.mark.asyncio
    async def test_get_file_content(self):
        """Test getting file content."""
        mock_file_data = {
            "file_name": "README.md",
            "file_path": "README.md",
            "size": 1024,
            "encoding": "base64",
            "content": "IyBUZXN0IFJlcG9zaXRvcnkKClRoaXMgaXMgYSB0ZXN0IHJlcG9zaXRvcnku",  # Base64 encoded
            "content_sha256": "abc123",
            "ref": "main",
            "blob_id": "def456",
            "commit_id": "ghi789"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_file_data
            
            file_data = await self.provider.get_file_content("testuser", "test-repo", "README.md")
            
            assert file_data['file_name'] == 'README.md'
            assert 'decoded_content' in file_data
            assert "# Test Repository" in file_data['decoded_content']
    
    @pytest.mark.asyncio
    async def test_create_or_update_file_new(self):
        """Test creating a new file."""
        mock_response = {
            "file_path": "new-file.txt",
            "branch": "main"
        }
        
        with patch.object(self.provider, 'get_file_content', new_callable=AsyncMock) as mock_get_file, \
             patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            
            # File doesn't exist
            mock_get_file.side_effect = NotFoundError("File not found")
            mock_request.return_value = mock_response
            
            result = await self.provider.create_or_update_file(
                "testuser", "test-repo", "new-file.txt",
                "Hello, World!", "Create new file", "main"
            )
            
            assert result['file_path'] == "new-file.txt"
            
            # Verify the API call used POST (create)
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.POST
    
    @pytest.mark.asyncio
    async def test_create_or_update_file_existing(self):
        """Test updating an existing file."""
        mock_existing_file = {
            "file_path": "existing-file.txt",
            "content": "base64content"
        }
        
        mock_response = {
            "file_path": "existing-file.txt",
            "branch": "main"
        }
        
        with patch.object(self.provider, 'get_file_content', new_callable=AsyncMock) as mock_get_file, \
             patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            
            mock_get_file.return_value = mock_existing_file
            mock_request.return_value = mock_response
            
            result = await self.provider.create_or_update_file(
                "testuser", "test-repo", "existing-file.txt",
                "Updated content", "Update existing file", "main"
            )
            
            assert result['file_path'] == "existing-file.txt"
            
            # Verify the API call used PUT (update)
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.PUT
    
    @pytest.mark.asyncio
    async def test_commit_changes_multiple_files(self):
        """Test committing multiple files atomically."""
        files = {
            "file1.py": "print('Hello from file 1')",
            "file2.py": "print('Hello from file 2')"
        }
        
        mock_commit = {
            "id": "commit789",
            "message": "Add multiple files",
            "author_name": "Test User",
            "author_email": "test@example.com",
            "created_at": "2023-01-01T00:00:00.000Z",
            "web_url": "https://gitlab.com/testuser/test-repo/-/commit/commit789",
            "parent_ids": ["base123"]
        }
        
        with patch.object(self.provider, 'get_file_content', new_callable=AsyncMock) as mock_get_file, \
             patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            
            # Both files don't exist (will be created)
            mock_get_file.side_effect = NotFoundError("File not found")
            mock_request.return_value = mock_commit
            
            commit = await self.provider.commit_changes(
                "testuser", "test-repo", "main",
                "Add multiple files", files,
                "Test User", "test@example.com"
            )
            
            assert isinstance(commit, Commit)
            assert commit.sha == "commit789"
            assert commit.message == "Add multiple files"
            assert commit.author == "Test User"
            assert commit.author_email == "test@example.com"
            assert len(commit.parents) == 1
            assert commit.parents[0] == "base123"
            
            # Verify the API call structure
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.POST
            assert "commits" in call_args[0][1]
            assert len(call_args[1]['data']['actions']) == 2
            assert all(action['action'] == 'create' for action in call_args[1]['data']['actions'])
    
    def test_mr_templates(self):
        """Test MR template functionality."""
        # Test default template
        default_template = self.provider.get_mr_template()
        assert "## Description" in default_template
        assert "{description}" in default_template
        assert "Pipeline passes" in default_template  # GitLab-specific
        
        # Test custom template
        custom_template = "Custom MR template: {description}"
        self.provider.set_mr_template("custom", custom_template)
        
        retrieved_template = self.provider.get_mr_template("custom")
        assert retrieved_template == custom_template
        
        # Test non-existent template falls back to default
        fallback_template = self.provider.get_mr_template("nonexistent")
        assert fallback_template == default_template
    
    @pytest.mark.asyncio
    async def test_create_pull_request(self):
        """Test creating a merge request."""
        mock_mr_data = {
            "id": 123,
            "iid": 45,
            "project_id": 678,
            "title": "Add new feature",
            "description": "This MR adds a new feature",
            "state": "opened",
            "source_branch": "feature/new",
            "target_branch": "main",
            "author": {"username": "testuser"},
            "web_url": "https://gitlab.com/testuser/test-repo/-/merge_requests/45",
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T00:00:00.000Z",
            "merged_at": None,
            "merge_status": "can_be_merged",
            "pipeline": {"status": "success"}
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_mr_data
            
            mr = await self.provider.create_pull_request(
                "testuser", "test-repo",
                "Add new feature", "This MR adds a new feature",
                "feature/new", "main", draft=False
            )
            
            assert isinstance(mr, MergeRequest)
            assert mr.number == 123
            assert mr.iid == 45
            assert mr.project_id == 678
            assert mr.title == "Add new feature"
            assert mr.description == "This MR adds a new feature"
            assert mr.state == "opened"
            assert mr.source_branch == "feature/new"
            assert mr.target_branch == "main"
            assert mr.author == "testuser"
            assert mr.merge_status == "can_be_merged"
            assert mr.pipeline_status == "success"
    
    @pytest.mark.asyncio
    async def test_create_pull_request_draft(self):
        """Test creating a draft merge request."""
        mock_mr_data = {
            "id": 124,
            "iid": 46,
            "project_id": 678,
            "title": "Draft: Add feature",
            "description": "Work in progress",
            "state": "opened",
            "source_branch": "feature/wip",
            "target_branch": "main",
            "author": {"username": "testuser"},
            "web_url": "https://gitlab.com/testuser/test-repo/-/merge_requests/46",
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T00:00:00.000Z",
            "merged_at": None
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_mr_data
            
            mr = await self.provider.create_pull_request(
                "testuser", "test-repo",
                "Add feature", "Work in progress",
                "feature/wip", "main", draft=True
            )
            
            assert mr.title == "Draft: Add feature"
            
            # Verify the API call
            call_args = mock_request.call_args
            assert call_args[1]['data']['title'] == "Draft: Add feature"
    
    @pytest.mark.asyncio
    async def test_merge_pull_request(self):
        """Test merging a merge request."""
        mock_merge_response = {
            "id": "merge123",
            "message": "Merge request successfully merged"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_merge_response
            
            result = await self.provider.merge_pull_request(
                "testuser", "test-repo", 123,
                commit_title="Merge MR #123",
                merge_method="squash"
            )
            
            assert result['message'] == "Merge request successfully merged"
            
            # Verify API call
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.PUT
            assert "merge" in call_args[0][1]
            assert call_args[1]['data']['squash'] is True
    
    @pytest.mark.asyncio
    async def test_approve_merge_request(self):
        """Test approving a merge request."""
        mock_approval_response = {
            "user": {"username": "approver"},
            "created_at": "2023-01-01T00:00:00.000Z"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_approval_response
            
            result = await self.provider.approve_merge_request("testuser", "test-repo", 123)
            
            assert result['user']['username'] == "approver"
            
            # Verify API call
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.POST
            assert "approve" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_get_pipeline_status(self):
        """Test getting pipeline status."""
        mock_pipelines = [
            {
                "id": 123,
                "status": "success",
                "ref": "main",
                "sha": "abc123",
                "web_url": "https://gitlab.com/testuser/test-repo/-/pipelines/123"
            }
        ]
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_pipelines
            
            pipeline = await self.provider.get_pipeline_status("testuser", "test-repo", "abc123")
            
            assert pipeline['status'] == "success"
            assert pipeline['sha'] == "abc123"
    
    def test_get_gitlab_metrics(self):
        """Test getting GitLab-specific metrics."""
        self.provider.user_info = {"username": "testuser"}
        self.provider.set_mr_template("custom", "Custom template")
        
        metrics = self.provider.get_gitlab_metrics()
        
        assert 'user_info' in metrics
        assert 'api_version' in metrics
        assert 'mr_templates' in metrics
        assert 'session_active' in metrics
        assert metrics['user_info']['username'] == 'testuser'
        assert 'custom' in metrics['mr_templates']


class TestGitLabUtilities:
    """Test GitLab utility functions."""
    
    def test_parse_gitlab_url(self):
        """Test parsing GitLab URLs."""
        url = "https://gitlab.com/owner/repo"
        result = parse_gitlab_url(url)
        
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo'
        assert result['host'] == 'gitlab.com'
        
        # Test self-hosted GitLab
        url = "https://gitlab.example.com/owner/repo"
        result = parse_gitlab_url(url)
        assert result['host'] == 'gitlab.example.com'
    
    def test_parse_gitlab_url_invalid(self):
        """Test parsing non-GitLab URL."""
        with pytest.raises(ValueError, match="Not a GitLab URL"):
            parse_gitlab_url("https://github.com/owner/repo")
    
    def test_validate_gitlab_token(self):
        """Test GitLab token validation."""
        # Valid tokens
        assert validate_gitlab_token("glpat-xxxxxxxxxxxxxxxxxxxx") is True  # Personal access token
        assert validate_gitlab_token("gloas-" + "x" * 60) is True  # OAuth application secret
        assert validate_gitlab_token("gldt-xxxxxxxxxxxxxxxxxxxx") is True  # Deploy token
        assert validate_gitlab_token("legacy_token_format_123") is True  # Legacy format
        
        # Invalid tokens
        assert validate_gitlab_token("") is False
        assert validate_gitlab_token("invalid") is False
        assert validate_gitlab_token("glpat-short") is False
        assert validate_gitlab_token("x" * 10) is False  # Too short
    
    def test_get_gitlab_scopes_for_operations(self):
        """Test getting required scopes for operations."""
        operations = ['read_api', 'write_repository', 'read_user']
        scopes = get_gitlab_scopes_for_operations(operations)
        
        assert 'read_api' in scopes
        assert 'write_repository' in scopes
        assert 'read_user' in scopes
        
        # Test unknown operation
        unknown_scopes = get_gitlab_scopes_for_operations(['unknown_operation'])
        assert unknown_scopes == []
    
    def test_convert_github_to_gitlab_workflow(self):
        """Test converting GitHub Actions to GitLab CI."""
        github_workflow = {
            "name": "CI",
            "on": ["push", "pull_request"],
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"name": "Checkout", "uses": "actions/checkout@v2"},
                        {"name": "Setup Python", "uses": "actions/setup-python@v2"},
                        {"name": "Install deps", "run": "pip install -r requirements.txt"},
                        {"name": "Run tests", "run": "pytest"}
                    ]
                },
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"name": "Build", "run": "python setup.py build"}
                    ]
                }
            }
        }
        
        gitlab_ci = convert_github_to_gitlab_workflow(github_workflow)
        
        assert 'stages' in gitlab_ci
        assert 'test' in gitlab_ci
        assert 'build' in gitlab_ci
        assert isinstance(gitlab_ci['test']['script'], list)
        assert isinstance(gitlab_ci['build']['script'], list)
        
        # Check that run commands were converted
        test_scripts = gitlab_ci['test']['script']
        assert "pip install -r requirements.txt" in test_scripts
        assert "pytest" in test_scripts


if __name__ == "__main__":
    pytest.main([__file__])