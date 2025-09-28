"""
Tests for GitHub VCS provider implementation.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientResponse
import json

from common.vcs.github import (
    GitHubProvider, GitHubError, GitHubRateLimitError,
    parse_github_url, validate_github_token, get_github_scopes_for_operations
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


class TestGitHubProvider:
    """Test GitHubProvider functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.provider = GitHubProvider()
    
    async def teardown_method(self):
        """Clean up after tests."""
        await self.provider.close()
    
    def test_initialization(self):
        """Test provider initialization."""
        assert self.provider.base_url == "https://api.github.com"
        assert self.provider.provider_name == "github"
        assert self.provider.api_version == "2022-11-28"
        assert self.provider.authenticated is False
        assert self.provider.token is None
        assert self.provider.user_info is None
    
    def test_get_base_headers(self):
        """Test base headers generation."""
        headers = self.provider._get_base_headers()
        
        assert headers['User-Agent'] == self.provider.user_agent
        assert headers['Accept'] == 'application/vnd.github+json'
        assert headers['X-GitHub-Api-Version'] == self.provider.api_version
    
    def test_get_auth_headers(self):
        """Test authentication headers for different token types."""
        # No token
        headers = self.provider._get_auth_headers()
        assert headers == {}
        
        # Personal access token (new format)
        self.provider.token = "ghp_1234567890123456789012345678901234567890"
        headers = self.provider._get_auth_headers()
        assert headers['Authorization'] == f"Bearer {self.provider.token}"
        
        # GitHub App installation token
        self.provider.token = "ghs_1234567890123456789012345678901234567890"
        headers = self.provider._get_auth_headers()
        assert headers['Authorization'] == f"token {self.provider.token}"
        
        # Fine-grained personal access token
        self.provider.token = "github_pat_" + "1" * 70
        headers = self.provider._get_auth_headers()
        assert headers['Authorization'] == f"Bearer {self.provider.token}"
    
    def test_parse_rate_limit_headers(self):
        """Test parsing GitHub rate limit headers."""
        headers = {
            'x-ratelimit-limit': '5000',
            'x-ratelimit-remaining': '4500',
            'x-ratelimit-reset': '1640995200',  # 2022-01-01 00:00:00 UTC
            'x-ratelimit-used': '500'
        }
        
        rate_limit = self.provider._parse_rate_limit_headers(headers)
        
        assert rate_limit is not None
        assert rate_limit.limit == 5000
        assert rate_limit.remaining == 4500
        assert rate_limit.used == 500
        assert rate_limit.reset_time == datetime.fromtimestamp(1640995200)
    
    def test_handle_github_error(self):
        """Test GitHub error handling."""
        # Authentication error
        error = self.provider._handle_github_error(401, {"message": "Bad credentials"})
        assert isinstance(error, AuthenticationError)
        assert "Bad credentials" in str(error)
        
        # Rate limit error
        error = self.provider._handle_github_error(403, {
            "message": "API rate limit exceeded",
            "x-ratelimit-reset": "1640995200"
        })
        assert isinstance(error, GitHubRateLimitError)
        
        # Permission error
        error = self.provider._handle_github_error(403, {"message": "Forbidden"})
        assert isinstance(error, PermissionError)
        
        # Not found error
        error = self.provider._handle_github_error(404, {"message": "Not Found"})
        assert isinstance(error, NotFoundError)
        
        # Validation error
        error = self.provider._handle_github_error(422, {
            "message": "Validation Failed",
            "errors": [
                {"field": "name", "message": "is required"},
                {"field": "email", "message": "is invalid"}
            ]
        })
        assert isinstance(error, GitHubError)
        assert "Validation Failed" in str(error)
        assert "name: is required" in str(error)
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful authentication."""
        mock_user_data = {
            "login": "testuser",
            "id": 12345,
            "email": "test@example.com"
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
            mock_request.side_effect = AuthenticationError("Bad credentials")
            
            result = await self.provider.authenticate("invalid-token")
            
            assert result is False
            assert self.provider.authenticated is False
            assert self.provider.user_info is None
    
    @pytest.mark.asyncio
    async def test_get_repository(self):
        """Test getting repository information."""
        mock_repo_data = {
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "owner": {"login": "testuser"},
            "html_url": "https://github.com/testuser/test-repo",
            "clone_url": "https://github.com/testuser/test-repo.git",
            "default_branch": "main",
            "private": False,
            "description": "A test repository"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_repo_data
            
            repo = await self.provider.get_repository("testuser", "test-repo")
            
            assert isinstance(repo, Repository)
            assert repo.name == "test-repo"
            assert repo.full_name == "testuser/test-repo"
            assert repo.owner == "testuser"
            assert repo.url == "https://github.com/testuser/test-repo"
            assert repo.clone_url == "https://github.com/testuser/test-repo.git"
            assert repo.default_branch == "main"
            assert repo.private is False
            assert repo.description == "A test repository"
    
    @pytest.mark.asyncio
    async def test_list_branches(self):
        """Test listing repository branches."""
        mock_branches_data = [
            {
                "name": "main",
                "commit": {"sha": "abc123"},
                "protected": True,
                "_links": {"html": "https://github.com/testuser/test-repo/tree/main"}
            },
            {
                "name": "develop",
                "commit": {"sha": "def456"},
                "protected": False,
                "_links": {"html": "https://github.com/testuser/test-repo/tree/develop"}
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
    async def test_get_branch(self):
        """Test getting specific branch information."""
        mock_branch_data = {
            "name": "feature/test",
            "commit": {"sha": "ghi789"},
            "protected": False,
            "_links": {"html": "https://github.com/testuser/test-repo/tree/feature/test"}
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_branch_data
            
            branch = await self.provider.get_branch("testuser", "test-repo", "feature/test")
            
            assert isinstance(branch, Branch)
            assert branch.name == "feature/test"
            assert branch.sha == "ghi789"
            assert branch.protected is False
    
    @pytest.mark.asyncio
    async def test_create_branch(self):
        """Test creating a new branch."""
        # Mock getting source branch
        mock_source_branch = Branch(name="main", sha="abc123", protected=False)
        
        # Mock branch creation response
        mock_ref_response = {"ref": "refs/heads/feature/new", "object": {"sha": "abc123"}}
        
        # Mock getting new branch
        mock_new_branch_data = {
            "name": "feature/new",
            "commit": {"sha": "abc123"},
            "protected": False
        }
        
        with patch.object(self.provider, 'get_branch', new_callable=AsyncMock) as mock_get_branch, \
             patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            
            # First call returns source branch, second call returns new branch
            mock_get_branch.side_effect = [mock_source_branch, Branch(name="feature/new", sha="abc123", protected=False)]
            mock_request.return_value = mock_ref_response
            
            branch = await self.provider.create_branch("testuser", "test-repo", "feature/new", "main")
            
            assert isinstance(branch, Branch)
            assert branch.name == "feature/new"
            assert branch.sha == "abc123"
            
            # Verify the API call was made correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.POST
            assert call_args[0][1] == "/repos/testuser/test-repo/git/refs"
            assert call_args[1]['data']['ref'] == "refs/heads/feature/new"
            assert call_args[1]['data']['sha'] == "abc123"
    
    @pytest.mark.asyncio
    async def test_delete_branch(self):
        """Test deleting a branch."""
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {}
            
            result = await self.provider.delete_branch("testuser", "test-repo", "feature/old")
            
            assert result is True
            mock_request.assert_called_once_with(
                RequestMethod.DELETE,
                "/repos/testuser/test-repo/git/refs/heads/feature/old"
            )
    
    @pytest.mark.asyncio
    async def test_delete_branch_not_found(self):
        """Test deleting a non-existent branch."""
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = NotFoundError("Branch not found")
            
            result = await self.provider.delete_branch("testuser", "test-repo", "nonexistent")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_file_content(self):
        """Test getting file content."""
        mock_file_data = {
            "type": "file",
            "name": "README.md",
            "path": "README.md",
            "sha": "abc123",
            "content": "IyBUZXN0IFJlcG9zaXRvcnkKClRoaXMgaXMgYSB0ZXN0IHJlcG9zaXRvcnku",  # Base64 encoded
            "encoding": "base64"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_file_data
            
            file_data = await self.provider.get_file_content("testuser", "test-repo", "README.md")
            
            assert file_data['type'] == 'file'
            assert file_data['name'] == 'README.md'
            assert 'decoded_content' in file_data
            assert "# Test Repository" in file_data['decoded_content']
    
    @pytest.mark.asyncio
    async def test_create_or_update_file_new(self):
        """Test creating a new file."""
        mock_response = {
            "content": {
                "name": "new-file.txt",
                "path": "new-file.txt",
                "sha": "def456"
            },
            "commit": {
                "sha": "ghi789",
                "message": "Create new file"
            }
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
            
            assert result['commit']['message'] == "Create new file"
            
            # Verify the API call
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.PUT
            assert 'sha' not in call_args[1]['data']  # No SHA for new file
    
    @pytest.mark.asyncio
    async def test_create_or_update_file_existing(self):
        """Test updating an existing file."""
        mock_existing_file = {
            "sha": "existing123",
            "content": "base64content"
        }
        
        mock_response = {
            "content": {
                "name": "existing-file.txt",
                "path": "existing-file.txt",
                "sha": "updated456"
            },
            "commit": {
                "sha": "newcommit789",
                "message": "Update existing file"
            }
        }
        
        with patch.object(self.provider, 'get_file_content', new_callable=AsyncMock) as mock_get_file, \
             patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            
            mock_get_file.return_value = mock_existing_file
            mock_request.return_value = mock_response
            
            result = await self.provider.create_or_update_file(
                "testuser", "test-repo", "existing-file.txt",
                "Updated content", "Update existing file", "main"
            )
            
            assert result['commit']['message'] == "Update existing file"
            
            # Verify the API call includes SHA for update
            call_args = mock_request.call_args
            assert call_args[1]['data']['sha'] == "existing123"
    
    @pytest.mark.asyncio
    async def test_commit_changes_multiple_files(self):
        """Test committing multiple files atomically."""
        files = {
            "file1.py": "print('Hello from file 1')",
            "file2.py": "print('Hello from file 2')"
        }
        
        # Mock responses for the Git Data API workflow
        mock_branch_ref = {"object": {"sha": "base123"}}
        mock_base_tree = {"sha": "tree123", "tree": []}
        mock_blob1 = {"sha": "blob1"}
        mock_blob2 = {"sha": "blob2"}
        mock_new_tree = {"sha": "newtree456"}
        mock_commit = {
            "sha": "commit789",
            "message": "Add multiple files",
            "author": {
                "name": "Test User",
                "email": "test@example.com",
                "date": "2023-01-01T00:00:00Z"
            },
            "html_url": "https://github.com/testuser/test-repo/commit/commit789",
            "parents": [{"sha": "base123"}]
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                mock_branch_ref,  # Get branch ref
                mock_base_tree,   # Get base tree
                mock_blob1,       # Create blob 1
                mock_blob2,       # Create blob 2
                mock_new_tree,    # Create new tree
                mock_commit,      # Create commit
                {}                # Update branch ref
            ]
            
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
            
            # Verify all API calls were made
            assert mock_request.call_count == 7
    
    def test_pr_templates(self):
        """Test PR template functionality."""
        # Test default template
        default_template = self.provider.get_pr_template()
        assert "## Description" in default_template
        assert "{description}" in default_template
        
        # Test custom template
        custom_template = "Custom PR template: {description}"
        self.provider.set_pr_template("custom", custom_template)
        
        retrieved_template = self.provider.get_pr_template("custom")
        assert retrieved_template == custom_template
        
        # Test non-existent template falls back to default
        fallback_template = self.provider.get_pr_template("nonexistent")
        assert fallback_template == default_template
    
    @pytest.mark.asyncio
    async def test_create_pull_request(self):
        """Test creating a pull request."""
        mock_pr_data = {
            "number": 123,
            "title": "Add new feature",
            "body": "This PR adds a new feature",
            "state": "open",
            "head": {"ref": "feature/new"},
            "base": {"ref": "main"},
            "user": {"login": "testuser"},
            "html_url": "https://github.com/testuser/test-repo/pull/123",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "merged_at": None
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_pr_data
            
            pr = await self.provider.create_pull_request(
                "testuser", "test-repo",
                "Add new feature", "This PR adds a new feature",
                "feature/new", "main", draft=False
            )
            
            assert isinstance(pr, PullRequest)
            assert pr.number == 123
            assert pr.title == "Add new feature"
            assert pr.description == "This PR adds a new feature"
            assert pr.state == "open"
            assert pr.source_branch == "feature/new"
            assert pr.target_branch == "main"
            assert pr.author == "testuser"
            assert pr.is_open is True
            assert pr.is_merged is False
    
    @pytest.mark.asyncio
    async def test_create_pull_request_with_template(self):
        """Test creating a pull request with template."""
        # Set up custom template
        template = "## Feature\n{description}\n\n## Checklist\n- [ ] Tests added"
        self.provider.set_pr_template("feature", template)
        
        mock_pr_data = {
            "number": 124,
            "title": "Add feature",
            "body": "## Feature\nNew awesome feature\n\n## Checklist\n- [ ] Tests added",
            "state": "open",
            "head": {"ref": "feature/awesome"},
            "base": {"ref": "main"},
            "user": {"login": "testuser"},
            "html_url": "https://github.com/testuser/test-repo/pull/124",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "merged_at": None
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_pr_data
            
            pr = await self.provider.create_pull_request(
                "testuser", "test-repo",
                "Add feature", "New awesome feature",
                "feature/awesome", "main",
                template_name="feature"
            )
            
            assert "## Feature" in pr.description
            assert "New awesome feature" in pr.description
            assert "## Checklist" in pr.description
    
    @pytest.mark.asyncio
    async def test_get_pull_request(self):
        """Test getting pull request information."""
        mock_pr_data = {
            "number": 123,
            "title": "Test PR",
            "body": "Test description",
            "state": "open",
            "head": {"ref": "feature/test"},
            "base": {"ref": "main"},
            "user": {"login": "testuser"},
            "html_url": "https://github.com/testuser/test-repo/pull/123",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T01:00:00Z",
            "merged_at": None
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_pr_data
            
            pr = await self.provider.get_pull_request("testuser", "test-repo", 123)
            
            assert isinstance(pr, PullRequest)
            assert pr.number == 123
            assert pr.title == "Test PR"
            assert pr.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_list_pull_requests(self):
        """Test listing pull requests."""
        mock_prs_data = [
            {
                "number": 123,
                "title": "PR 1",
                "body": "Description 1",
                "state": "open",
                "head": {"ref": "feature/1"},
                "base": {"ref": "main"},
                "user": {"login": "user1"},
                "html_url": "https://github.com/testuser/test-repo/pull/123",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "merged_at": None
            },
            {
                "number": 124,
                "title": "PR 2",
                "body": "Description 2",
                "state": "closed",
                "head": {"ref": "feature/2"},
                "base": {"ref": "main"},
                "user": {"login": "user2"},
                "html_url": "https://github.com/testuser/test-repo/pull/124",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "merged_at": "2023-01-01T02:00:00Z"
            }
        ]
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_prs_data
            
            prs = await self.provider.list_pull_requests("testuser", "test-repo", state="all")
            
            assert len(prs) == 2
            assert prs[0].number == 123
            assert prs[0].state == "open"
            assert prs[1].number == 124
            assert prs[1].state == "closed"
            assert prs[1].merged_at is not None
    
    @pytest.mark.asyncio
    async def test_update_pull_request(self):
        """Test updating a pull request."""
        mock_updated_pr = {
            "number": 123,
            "title": "Updated Title",
            "body": "Updated description",
            "state": "open",
            "head": {"ref": "feature/test"},
            "base": {"ref": "main"},
            "user": {"login": "testuser"},
            "html_url": "https://github.com/testuser/test-repo/pull/123",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T02:00:00Z",
            "merged_at": None
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_updated_pr
            
            pr = await self.provider.update_pull_request(
                "testuser", "test-repo", 123,
                title="Updated Title",
                description="Updated description"
            )
            
            assert pr.title == "Updated Title"
            assert pr.description == "Updated description"
            
            # Verify API call
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.PATCH
            assert call_args[1]['data']['title'] == "Updated Title"
            assert call_args[1]['data']['body'] == "Updated description"
    
    @pytest.mark.asyncio
    async def test_merge_pull_request(self):
        """Test merging a pull request."""
        mock_merge_response = {
            "sha": "merge123",
            "merged": True,
            "message": "Pull request successfully merged"
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_merge_response
            
            result = await self.provider.merge_pull_request(
                "testuser", "test-repo", 123,
                commit_title="Merge PR #123",
                merge_method="squash"
            )
            
            assert result['merged'] is True
            assert result['sha'] == "merge123"
            
            # Verify API call
            call_args = mock_request.call_args
            assert call_args[0][0] == RequestMethod.PUT
            assert call_args[1]['data']['merge_method'] == "squash"
            assert call_args[1]['data']['commit_title'] == "Merge PR #123"
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self):
        """Test getting rate limit status."""
        mock_rate_limit = {
            "resources": {
                "core": {
                    "limit": 5000,
                    "remaining": 4999,
                    "reset": 1640995200,
                    "used": 1
                }
            }
        }
        
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_rate_limit
            
            rate_limit = await self.provider.get_rate_limit_status()
            
            assert rate_limit['resources']['core']['limit'] == 5000
            assert rate_limit['resources']['core']['remaining'] == 4999
    
    def test_get_github_metrics(self):
        """Test getting GitHub-specific metrics."""
        self.provider.user_info = {"login": "testuser"}
        self.provider.set_pr_template("custom", "Custom template")
        
        metrics = self.provider.get_github_metrics()
        
        assert 'user_info' in metrics
        assert 'api_version' in metrics
        assert 'pr_templates' in metrics
        assert 'session_active' in metrics
        assert metrics['user_info']['login'] == 'testuser'
        assert 'custom' in metrics['pr_templates']


class TestGitHubUtilities:
    """Test GitHub utility functions."""
    
    def test_parse_github_url(self):
        """Test parsing GitHub URLs."""
        url = "https://github.com/owner/repo"
        result = parse_github_url(url)
        
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo'
        assert result['host'] == 'github.com'
    
    def test_parse_github_url_invalid(self):
        """Test parsing non-GitHub URL."""
        with pytest.raises(ValueError, match="Not a GitHub URL"):
            parse_github_url("https://gitlab.com/owner/repo")
    
    def test_validate_github_token(self):
        """Test GitHub token validation."""
        # Valid tokens
        assert validate_github_token("ghp_" + "1" * 36) is True  # Personal access token
        assert validate_github_token("ghs_" + "1" * 36) is True  # GitHub App token
        assert validate_github_token("github_pat_" + "1" * 70) is True  # Fine-grained PAT
        assert validate_github_token("1" * 40) is True  # Classic format
        
        # Invalid tokens
        assert validate_github_token("") is False
        assert validate_github_token("invalid") is False
        assert validate_github_token("ghp_short") is False
        assert validate_github_token("1" * 39) is False  # Too short
    
    def test_get_github_scopes_for_operations(self):
        """Test getting required scopes for operations."""
        operations = ['read_repo', 'create_pr', 'read_user']
        scopes = get_github_scopes_for_operations(operations)
        
        assert 'repo:status' in scopes or 'public_repo' in scopes
        assert 'repo' in scopes or 'pull_requests:write' in scopes
        assert 'user:email' in scopes
        
        # Test unknown operation
        unknown_scopes = get_github_scopes_for_operations(['unknown_operation'])
        assert unknown_scopes == []


if __name__ == "__main__":
    pytest.main([__file__])