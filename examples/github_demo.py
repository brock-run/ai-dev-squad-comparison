#!/usr/bin/env python3
"""
GitHub VCS Provider Demonstration

This example demonstrates the GitHub provider functionality, including:
1. Authentication with GitHub API
2. Repository operations (get info, branches)
3. Branch creation and management
4. File operations (create, update, get content)
5. Commit operations (single and multiple files)
6. Pull request workflow (create, update, merge)
7. PR templates and customization
8. Rate limit monitoring
9. Error handling scenarios

Note: This demo requires a GitHub personal access token with appropriate permissions.
Set the GITHUB_TOKEN environment variable or update the token in the script.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.vcs.github import (
    GitHubProvider, GitHubError, GitHubRateLimitError,
    parse_github_url, validate_github_token, get_github_scopes_for_operations
)
from common.vcs.base import (
    AuthenticationError, NotFoundError, PermissionError,
    RetryConfig
)


# Configuration - Update these for your testing
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'your-github-token-here')
TEST_OWNER = os.getenv('GITHUB_TEST_OWNER', 'your-username')  # Your GitHub username
TEST_REPO = os.getenv('GITHUB_TEST_REPO', 'test-repo')  # A test repository you own


def demonstrate_utility_functions():
    """Demonstrate GitHub utility functions."""
    print("=== GitHub Utility Functions ===")
    
    # Test URL parsing
    print("Testing GitHub URL parsing...")
    urls = [
        "https://github.com/octocat/Hello-World",
        "https://github.com/microsoft/vscode.git",
        "https://github.com/python/cpython"
    ]
    
    for url in urls:
        try:
            parsed = parse_github_url(url)
            print(f"  {url}")
            print(f"    Owner: {parsed['owner']}")
            print(f"    Repo: {parsed['repo']}")
        except ValueError as e:
            print(f"  {url} - Error: {e}")
    
    # Test token validation
    print(f"\nTesting GitHub token validation...")
    tokens = [
        "ghp_1234567890123456789012345678901234567890",  # Valid PAT
        "ghs_1234567890123456789012345678901234567890",  # Valid App token
        "github_pat_" + "1" * 70,  # Valid fine-grained PAT
        "invalid-token",  # Invalid
        ""  # Empty
    ]
    
    for token in tokens:
        valid = validate_github_token(token)
        status = "✓" if valid else "✗"
        display_token = token[:20] + "..." if len(token) > 20 else token
        print(f"  {status} {display_token}")
    
    # Test scope requirements
    print(f"\nTesting scope requirements...")
    operations = ['read_repo', 'create_pr', 'merge_pr', 'read_user']
    scopes = get_github_scopes_for_operations(operations)
    print(f"  Operations: {operations}")
    print(f"  Required scopes: {scopes}")


async def demonstrate_authentication():
    """Demonstrate GitHub authentication."""
    print("\n=== GitHub Authentication ===")
    
    # Validate token format first
    if not validate_github_token(GITHUB_TOKEN):
        print(f"❌ Invalid GitHub token format. Please set a valid GITHUB_TOKEN environment variable.")
        return None
    
    # Create provider with custom retry config
    retry_config = RetryConfig(max_retries=2, base_delay=1.0)
    provider = GitHubProvider(retry_config=retry_config)
    
    try:
        print(f"Authenticating with GitHub...")
        success = await provider.authenticate(GITHUB_TOKEN)
        
        if success:
            user_info = provider.user_info
            print(f"✅ Authentication successful!")
            print(f"  User: {user_info.get('login', 'unknown')}")
            print(f"  Name: {user_info.get('name', 'N/A')}")
            print(f"  Email: {user_info.get('email', 'N/A')}")
            print(f"  Public repos: {user_info.get('public_repos', 'N/A')}")
            return provider
        else:
            print(f"❌ Authentication failed")
            return None
            
    except AuthenticationError as e:
        print(f"❌ Authentication error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


async def demonstrate_repository_operations(provider: GitHubProvider):
    """Demonstrate repository operations."""
    print(f"\n=== Repository Operations ===")
    
    try:
        # Get repository information
        print(f"Getting repository information for {TEST_OWNER}/{TEST_REPO}...")
        repo = await provider.get_repository(TEST_OWNER, TEST_REPO)
        
        print(f"Repository: {repo.full_name}")
        print(f"  Description: {repo.description or 'No description'}")
        print(f"  Default branch: {repo.default_branch}")
        print(f"  Private: {repo.private}")
        print(f"  Clone URL: {repo.clone_url}")
        
        return repo
        
    except NotFoundError:
        print(f"❌ Repository {TEST_OWNER}/{TEST_REPO} not found or not accessible")
        print(f"   Please update TEST_OWNER and TEST_REPO variables")
        return None
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
        return None
    except Exception as e:
        print(f"❌ Error getting repository: {e}")
        return None


async def demonstrate_branch_operations(provider: GitHubProvider, repo):
    """Demonstrate branch operations."""
    print(f"\n=== Branch Operations ===")
    
    try:
        # List branches
        print(f"Listing branches...")
        branches = await provider.list_branches(TEST_OWNER, TEST_REPO)
        
        print(f"Found {len(branches)} branches:")
        for branch in branches[:5]:  # Show first 5 branches
            protection = "🔒" if branch.protected else "🔓"
            print(f"  {protection} {branch.name} ({branch.sha[:8]})")
        
        if len(branches) > 5:
            print(f"  ... and {len(branches) - 5} more")
        
        # Get specific branch
        default_branch = repo.default_branch
        print(f"\nGetting {default_branch} branch details...")
        main_branch = await provider.get_branch(TEST_OWNER, TEST_REPO, default_branch)
        print(f"  Branch: {main_branch.name}")
        print(f"  SHA: {main_branch.sha}")
        print(f"  Protected: {main_branch.protected}")
        
        # Create a new branch for demo
        demo_branch_name = f"demo/github-provider-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        print(f"\nCreating demo branch: {demo_branch_name}")
        
        try:
            demo_branch = await provider.create_branch(
                TEST_OWNER, TEST_REPO, demo_branch_name, default_branch
            )
            print(f"✅ Created branch: {demo_branch.name}")
            print(f"  SHA: {demo_branch.sha}")
            return demo_branch_name
            
        except GitHubError as e:
            print(f"❌ Failed to create branch: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Error in branch operations: {e}")
        return None


async def demonstrate_file_operations(provider: GitHubProvider, branch_name: str):
    """Demonstrate file operations."""
    print(f"\n=== File Operations ===")
    
    if not branch_name:
        print("Skipping file operations (no demo branch available)")
        return
    
    try:
        # Create a new file
        print(f"Creating a new file on branch {branch_name}...")
        file_content = f"""# GitHub Provider Demo

This file was created by the GitHub provider demo script.

Created at: {datetime.now().isoformat()}
Branch: {branch_name}

## Features Demonstrated

- Repository operations
- Branch management
- File creation and updates
- Commit operations
- Pull request workflow

## Next Steps

This file will be used to demonstrate:
1. File updates
2. Multiple file commits
3. Pull request creation
"""
        
        result = await provider.create_or_update_file(
            TEST_OWNER, TEST_REPO, "demo-file.md",
            file_content, "Add demo file via GitHub provider",
            branch_name, "GitHub Demo Bot", "demo@example.com"
        )
        
        print(f"✅ Created file: demo-file.md")
        print(f"  Commit SHA: {result['commit']['sha'][:8]}")
        
        # Update the file
        print(f"\nUpdating the file...")
        updated_content = file_content + f"\n\nUpdated at: {datetime.now().isoformat()}\n"
        
        update_result = await provider.create_or_update_file(
            TEST_OWNER, TEST_REPO, "demo-file.md",
            updated_content, "Update demo file with timestamp",
            branch_name, "GitHub Demo Bot", "demo@example.com"
        )
        
        print(f"✅ Updated file: demo-file.md")
        print(f"  Commit SHA: {update_result['commit']['sha'][:8]}")
        
        # Get file content to verify
        print(f"\nRetrieving file content...")
        file_data = await provider.get_file_content(TEST_OWNER, TEST_REPO, "demo-file.md", branch_name)
        
        print(f"✅ Retrieved file: {file_data['name']}")
        print(f"  Size: {file_data.get('size', 'unknown')} bytes")
        print(f"  SHA: {file_data['sha'][:8]}")
        
        # Show first few lines of content
        if 'decoded_content' in file_data:
            lines = file_data['decoded_content'].split('\n')[:5]
            print(f"  Content preview:")
            for line in lines:
                print(f"    {line}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in file operations: {e}")
        return False


async def demonstrate_commit_operations(provider: GitHubProvider, branch_name: str):
    """Demonstrate multi-file commit operations."""
    print(f"\n=== Commit Operations ===")
    
    if not branch_name:
        print("Skipping commit operations (no demo branch available)")
        return
    
    try:
        # Create multiple files in a single commit
        print(f"Creating multiple files in a single commit...")
        
        files = {
            "src/main.py": """#!/usr/bin/env python3
\"\"\"
Main application file created by GitHub provider demo.
\"\"\"

def main():
    print("Hello from GitHub provider demo!")
    print(f"Created at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
""",
            "src/utils.py": """\"\"\"
Utility functions for the demo application.
\"\"\"

from datetime import datetime

def get_timestamp():
    \"\"\"Get current timestamp.\"\"\"
    return datetime.now().isoformat()

def format_message(message: str) -> str:
    \"\"\"Format a message with timestamp.\"\"\"
    return f"[{get_timestamp()}] {message}"
""",
            "README.md": f"""# GitHub Provider Demo Project

This project was created to demonstrate the GitHub provider functionality.

## Files

- `src/main.py` - Main application
- `src/utils.py` - Utility functions
- `demo-file.md` - Demo documentation

## Created

- Date: {datetime.now().strftime('%Y-%m-%d')}
- Branch: {branch_name}
- Via: GitHub Provider Demo Script

## Usage

```bash
python src/main.py
```
""",
            "requirements.txt": """# Demo project requirements
# (No external dependencies for this demo)
"""
        }
        
        commit = await provider.commit_changes(
            TEST_OWNER, TEST_REPO, branch_name,
            "Add demo project structure with multiple files",
            files, "GitHub Demo Bot", "demo@example.com"
        )
        
        print(f"✅ Created multi-file commit:")
        print(f"  SHA: {commit.sha[:8]}")
        print(f"  Message: {commit.message}")
        print(f"  Author: {commit.author} <{commit.author_email}>")
        print(f"  Files: {len(files)} files committed")
        print(f"  Timestamp: {commit.timestamp}")
        
        return commit
        
    except Exception as e:
        print(f"❌ Error in commit operations: {e}")
        return None


async def demonstrate_pr_templates(provider: GitHubProvider):
    """Demonstrate PR template functionality."""
    print(f"\n=== PR Template System ===")
    
    # Show default template
    default_template = provider.get_pr_template()
    print(f"Default PR template preview:")
    lines = default_template.split('\n')[:8]
    for line in lines:
        print(f"  {line}")
    print(f"  ... (truncated)")
    
    # Create custom templates
    print(f"\nCreating custom PR templates...")
    
    feature_template = """## 🚀 Feature Description
{description}

## 📋 Type of Change
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update

## 🧪 Testing
- [ ] Tests pass locally with `pytest`
- [ ] New tests added for changes (if applicable)
- [ ] Manual testing completed

## 📝 Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Documentation updated (if applicable)
- [ ] No new warnings introduced

## 📸 Screenshots (if applicable)
<!-- Add screenshots here -->

## 🔗 Related Issues
<!-- Link to related issues -->
Closes #
"""
    
    bugfix_template = """## 🐛 Bug Fix Description
{description}

## 🔍 Root Cause
<!-- Describe what caused the bug -->

## 🛠️ Solution
<!-- Describe how you fixed it -->

## 🧪 Testing
- [ ] Bug reproduction steps verified
- [ ] Fix tested locally
- [ ] Regression tests added
- [ ] All existing tests pass

## 📋 Type of Change
- [x] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] 💥 Breaking change (fix that would cause existing functionality to not work as expected)

## 📝 Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated (if applicable)

## 🔗 Related Issues
Fixes #
"""
    
    provider.set_pr_template("feature", feature_template)
    provider.set_pr_template("bugfix", bugfix_template)
    
    print(f"✅ Created custom templates:")
    print(f"  - feature: Enhanced template with emojis and detailed sections")
    print(f"  - bugfix: Bug-specific template with root cause analysis")
    
    # Test template retrieval
    feature_preview = provider.get_pr_template("feature")
    print(f"\nFeature template preview:")
    lines = feature_preview.split('\n')[:6]
    for line in lines:
        print(f"  {line}")
    print(f"  ... (truncated)")


async def demonstrate_pull_request_workflow(provider: GitHubProvider, branch_name: str, commit):
    """Demonstrate complete pull request workflow."""
    print(f"\n=== Pull Request Workflow ===")
    
    if not branch_name or not commit:
        print("Skipping PR workflow (no demo branch or commit available)")
        return
    
    try:
        # Create pull request with custom template
        print(f"Creating pull request from {branch_name}...")
        
        pr_description = """This PR demonstrates the GitHub provider functionality by adding:

- Demo documentation file
- Sample Python project structure
- Multiple file commit example
- Automated PR creation

The changes are safe and only add new files for demonstration purposes."""
        
        pr = await provider.create_pull_request(
            TEST_OWNER, TEST_REPO,
            "🚀 Add GitHub Provider Demo Files",
            pr_description,
            branch_name, "main",  # Assuming main is the default branch
            draft=False,
            template_name="feature"
        )
        
        print(f"✅ Created pull request:")
        print(f"  Number: #{pr.number}")
        print(f"  Title: {pr.title}")
        print(f"  URL: {pr.url}")
        print(f"  State: {pr.state}")
        print(f"  Author: {pr.author}")
        
        # Add a comment to the PR
        print(f"\nAdding comment to PR...")
        comment_result = await provider.add_pr_comment(
            TEST_OWNER, TEST_REPO, pr.number,
            "🤖 This PR was created automatically by the GitHub provider demo script. "
            "It demonstrates the complete workflow from branch creation to PR management."
        )
        
        print(f"✅ Added comment to PR #{pr.number}")
        
        # Update the PR
        print(f"\nUpdating PR title and description...")
        updated_pr = await provider.update_pull_request(
            TEST_OWNER, TEST_REPO, pr.number,
            title="🚀 [DEMO] GitHub Provider Integration Example",
            description=pr_description + "\n\n---\n**Note**: This is a demonstration PR created by the GitHub provider demo script."
        )
        
        print(f"✅ Updated PR:")
        print(f"  New title: {updated_pr.title}")
        
        # List all PRs to show our new one
        print(f"\nListing recent pull requests...")
        prs = await provider.list_pull_requests(TEST_OWNER, TEST_REPO, state="open")
        
        print(f"Open pull requests ({len(prs)}):")
        for pr_item in prs[:5]:  # Show first 5
            status = "🟢" if pr_item.state == "open" else "🔴"
            print(f"  {status} #{pr_item.number}: {pr_item.title}")
            print(f"     {pr_item.source_branch} → {pr_item.target_branch}")
        
        return pr
        
    except Exception as e:
        print(f"❌ Error in PR workflow: {e}")
        return None


async def demonstrate_rate_limiting(provider: GitHubProvider):
    """Demonstrate rate limit monitoring."""
    print(f"\n=== Rate Limit Monitoring ===")
    
    try:
        # Get current rate limit status
        print(f"Checking current rate limit status...")
        rate_limit_data = await provider.get_rate_limit_status()
        
        core_limits = rate_limit_data['resources']['core']
        print(f"Core API rate limits:")
        print(f"  Limit: {core_limits['limit']} requests/hour")
        print(f"  Remaining: {core_limits['remaining']} requests")
        print(f"  Used: {core_limits['used']} requests")
        print(f"  Reset: {datetime.fromtimestamp(core_limits['reset'])}")
        
        # Calculate usage percentage
        usage_percent = (core_limits['used'] / core_limits['limit']) * 100
        print(f"  Usage: {usage_percent:.1f}%")
        
        # Show other rate limits if available
        for resource_name, limits in rate_limit_data['resources'].items():
            if resource_name != 'core':
                print(f"\n{resource_name.title()} API rate limits:")
                print(f"  Limit: {limits['limit']}")
                print(f"  Remaining: {limits['remaining']}")
                print(f"  Used: {limits['used']}")
        
        # Get provider metrics
        print(f"\nProvider metrics:")
        metrics = provider.get_github_metrics()
        print(f"  Success rate: {metrics['success_rate']:.2%}")
        print(f"  Average response time: {metrics['average_response_time_ms']:.2f}ms")
        print(f"  Request rate: {metrics['request_rate_per_minute']:.2f} req/min")
        print(f"  Recent requests: {metrics['recent_requests']}")
        
    except Exception as e:
        print(f"❌ Error checking rate limits: {e}")


async def demonstrate_error_handling(provider: GitHubProvider):
    """Demonstrate error handling scenarios."""
    print(f"\n=== Error Handling ===")
    
    # Test various error scenarios
    error_scenarios = [
        {
            "name": "Non-existent repository",
            "action": lambda: provider.get_repository("nonexistent-user", "nonexistent-repo"),
            "expected": NotFoundError
        },
        {
            "name": "Non-existent branch",
            "action": lambda: provider.get_branch(TEST_OWNER, TEST_REPO, "nonexistent-branch"),
            "expected": NotFoundError
        },
        {
            "name": "Invalid branch name",
            "action": lambda: provider.create_branch(TEST_OWNER, TEST_REPO, "invalid branch name", "main"),
            "expected": GitHubError
        }
    ]
    
    for scenario in error_scenarios:
        print(f"\nTesting: {scenario['name']}")
        try:
            await scenario['action']()
            print(f"  ❌ Expected error but operation succeeded")
        except scenario['expected'] as e:
            print(f"  ✅ Caught expected {type(e).__name__}: {e}")
        except Exception as e:
            print(f"  ⚠️  Caught unexpected error: {type(e).__name__}: {e}")


async def cleanup_demo_resources(provider: GitHubProvider, branch_name: str, pr_number: int = None):
    """Clean up demo resources."""
    print(f"\n=== Cleanup ===")
    
    if not branch_name:
        print("No demo branch to clean up")
        return
    
    try:
        # Note: In a real scenario, you might want to:
        # 1. Close the PR if it's still open
        # 2. Delete the demo branch
        # 3. Clean up any other resources
        
        print(f"Demo resources created:")
        print(f"  Branch: {branch_name}")
        if pr_number:
            print(f"  Pull Request: #{pr_number}")
        
        print(f"\n⚠️  Manual cleanup required:")
        print(f"  1. Review and close PR #{pr_number} if desired")
        print(f"  2. Delete branch '{branch_name}' if no longer needed")
        print(f"  3. Remove demo files from repository if desired")
        
        # Uncomment the following lines if you want automatic cleanup:
        # print(f"Deleting demo branch: {branch_name}")
        # deleted = await provider.delete_branch(TEST_OWNER, TEST_REPO, branch_name)
        # if deleted:
        #     print(f"✅ Deleted branch: {branch_name}")
        # else:
        #     print(f"❌ Failed to delete branch: {branch_name}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")


async def main():
    """Run all GitHub provider demonstrations."""
    print("GitHub VCS Provider Demonstration")
    print("=" * 50)
    
    # Check configuration
    if GITHUB_TOKEN == 'your-github-token-here':
        print("❌ Please set your GitHub token in the GITHUB_TOKEN environment variable")
        print("   or update the GITHUB_TOKEN variable in this script.")
        return 1
    
    if TEST_OWNER == 'your-username' or TEST_REPO == 'test-repo':
        print("❌ Please update TEST_OWNER and TEST_REPO variables with your GitHub username and a test repository")
        return 1
    
    provider = None
    branch_name = None
    pr = None
    
    try:
        # Utility functions
        demonstrate_utility_functions()
        
        # Authentication
        provider = await demonstrate_authentication()
        if not provider:
            return 1
        
        # Repository operations
        repo = await demonstrate_repository_operations(provider)
        if not repo:
            return 1
        
        # Branch operations
        branch_name = await demonstrate_branch_operations(provider, repo)
        
        # File operations
        file_success = await demonstrate_file_operations(provider, branch_name)
        
        # Commit operations
        commit = await demonstrate_commit_operations(provider, branch_name)
        
        # PR templates
        await demonstrate_pr_templates(provider)
        
        # Pull request workflow
        pr = await demonstrate_pull_request_workflow(provider, branch_name, commit)
        
        # Rate limiting
        await demonstrate_rate_limiting(provider)
        
        # Error handling
        await demonstrate_error_handling(provider)
        
        # Cleanup
        await cleanup_demo_resources(provider, branch_name, pr.number if pr else None)
        
        print("\n" + "=" * 50)
        print("✅ GitHub provider demonstration completed successfully!")
        print("\nKey features demonstrated:")
        print("  - Authentication and user info retrieval")
        print("  - Repository and branch management")
        print("  - File creation, updates, and content retrieval")
        print("  - Multi-file atomic commits")
        print("  - PR templates and customization")
        print("  - Complete pull request workflow")
        print("  - Rate limit monitoring")
        print("  - Comprehensive error handling")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Unexpected error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Always close the provider
        if provider:
            await provider.close()


if __name__ == "__main__":
    exit(asyncio.run(main()))