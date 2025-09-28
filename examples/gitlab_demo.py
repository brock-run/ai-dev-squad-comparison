#!/usr/bin/env python3
"""
GitLab VCS Provider Demonstration

This example demonstrates the GitLab provider functionality, including:
1. Authentication with GitLab API
2. Project operations (get info, branches)
3. Branch creation and management
4. File operations (create, update, get content)
5. Commit operations (single and multiple files)
6. Merge request workflow (create, update, merge, approve)
7. MR templates and customization
8. Pipeline integration and status checking
9. GitLab-specific features (approvals, discussions)
10. Rate limit monitoring and error handling

Note: This demo requires a GitLab personal access token with appropriate permissions.
Set the GITLAB_TOKEN environment variable or update the token in the script.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.vcs.gitlab import (
    GitLabProvider, GitLabError, GitLabRateLimitError, MergeRequest,
    parse_gitlab_url, validate_gitlab_token, get_gitlab_scopes_for_operations,
    convert_github_to_gitlab_workflow
)
from common.vcs.base import (
    AuthenticationError, NotFoundError, PermissionError,
    RetryConfig
)


# Configuration - Update these for your testing
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN', 'your-gitlab-token-here')
TEST_OWNER = os.getenv('GITLAB_TEST_OWNER', 'your-username')  # Your GitLab username
TEST_REPO = os.getenv('GITLAB_TEST_REPO', 'test-repo')  # A test project you own
GITLAB_URL = os.getenv('GITLAB_URL', 'https://gitlab.com/api/v4')  # GitLab instance URL


def demonstrate_utility_functions():
    """Demonstrate GitLab utility functions."""
    print("=== GitLab Utility Functions ===")
    
    # Test URL parsing
    print("Testing GitLab URL parsing...")
    urls = [
        "https://gitlab.com/gitlab-org/gitlab",
        "https://gitlab.com/gitlab-examples/nodejs.git",
        "https://gitlab.example.com/company/project",
        "https://about.gitlab.com/company/team/"  # Invalid
    ]
    
    for url in urls:
        try:
            parsed = parse_gitlab_url(url)
            print(f"  {url}")
            print(f"    Owner: {parsed['owner']}")
            print(f"    Repo: {parsed['repo']}")
            print(f"    Host: {parsed['host']}")
        except ValueError as e:
            print(f"  {url} - Error: {e}")
    
    # Test token validation
    print(f"\nTesting GitLab token validation...")
    tokens = [
        "glpat-xxxxxxxxxxxxxxxxxxxx",  # Valid PAT
        "gloas-" + "x" * 60,  # Valid OAuth token
        "gldt-xxxxxxxxxxxxxxxxxxxx",  # Valid deploy token
        "legacy_token_format_123",  # Valid legacy format
        "invalid-token",  # Invalid
        ""  # Empty
    ]
    
    for token in tokens:
        valid = validate_gitlab_token(token)
        status = "✓" if valid else "✗"
        display_token = token[:20] + "..." if len(token) > 20 else token
        print(f"  {status} {display_token}")
    
    # Test scope requirements
    print(f"\nTesting scope requirements...")
    operations = ['read_api', 'write_repository', 'read_user', 'api']
    scopes = get_gitlab_scopes_for_operations(operations)
    print(f"  Operations: {operations}")
    print(f"  Required scopes: {scopes}")
    
    # Test GitHub to GitLab workflow conversion
    print(f"\nTesting GitHub Actions to GitLab CI conversion...")
    github_workflow = {
        "name": "CI",
        "jobs": {
            "test": {
                "steps": [
                    {"run": "npm install"},
                    {"run": "npm test"}
                ]
            },
            "build": {
                "steps": [
                    {"run": "npm run build"}
                ]
            }
        }
    }
    
    gitlab_ci = convert_github_to_gitlab_workflow(github_workflow)
    print(f"  Converted GitLab CI stages: {gitlab_ci.get('stages', [])}")
    print(f"  Jobs: {[k for k in gitlab_ci.keys() if k not in ['stages', 'variables', 'before_script', 'after_script']]}")


async def demonstrate_authentication():
    """Demonstrate GitLab authentication."""
    print("\n=== GitLab Authentication ===")
    
    # Validate token format first
    if not validate_gitlab_token(GITLAB_TOKEN):
        print(f"❌ Invalid GitLab token format. Please set a valid GITLAB_TOKEN environment variable.")
        return None
    
    # Create provider with custom retry config
    retry_config = RetryConfig(max_retries=2, base_delay=1.0)
    provider = GitLabProvider(base_url=GITLAB_URL, retry_config=retry_config)
    
    try:
        print(f"Authenticating with GitLab...")
        success = await provider.authenticate(GITLAB_TOKEN)
        
        if success:
            user_info = provider.user_info
            print(f"✅ Authentication successful!")
            print(f"  User: {user_info.get('username', 'unknown')}")
            print(f"  Name: {user_info.get('name', 'N/A')}")
            print(f"  Email: {user_info.get('email', 'N/A')}")
            print(f"  State: {user_info.get('state', 'N/A')}")
            print(f"  Created: {user_info.get('created_at', 'N/A')}")
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


async def demonstrate_project_operations(provider: GitLabProvider):
    """Demonstrate project operations."""
    print(f"\n=== Project Operations ===")
    
    try:
        # Get project information
        print(f"Getting project information for {TEST_OWNER}/{TEST_REPO}...")
        repo = await provider.get_repository(TEST_OWNER, TEST_REPO)
        
        print(f"Project: {repo.full_name}")
        print(f"  Description: {repo.description or 'No description'}")
        print(f"  Default branch: {repo.default_branch}")
        print(f"  Private: {repo.private}")
        print(f"  Clone URL: {repo.clone_url}")
        
        # Get detailed project info
        print(f"\nGetting detailed project information...")
        project_info = await provider.get_project_info(TEST_OWNER, TEST_REPO)
        
        print(f"  Project ID: {project_info.get('id')}")
        print(f"  Visibility: {project_info.get('visibility')}")
        print(f"  Stars: {project_info.get('star_count', 0)}")
        print(f"  Forks: {project_info.get('forks_count', 0)}")
        print(f"  Issues enabled: {project_info.get('issues_enabled', False)}")
        print(f"  MR enabled: {project_info.get('merge_requests_enabled', False)}")
        print(f"  CI/CD enabled: {project_info.get('builds_enabled', False)}")
        
        return repo
        
    except NotFoundError:
        print(f"❌ Project {TEST_OWNER}/{TEST_REPO} not found or not accessible")
        print(f"   Please update TEST_OWNER and TEST_REPO variables")
        return None
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


async def demonstrate_branch_operations(provider: GitLabProvider, repo):
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
        demo_branch_name = f"demo/gitlab-provider-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        print(f"\nCreating demo branch: {demo_branch_name}")
        
        try:
            demo_branch = await provider.create_branch(
                TEST_OWNER, TEST_REPO, demo_branch_name, default_branch
            )
            print(f"✅ Created branch: {demo_branch.name}")
            print(f"  SHA: {demo_branch.sha}")
            return demo_branch_name
            
        except GitLabError as e:
            print(f"❌ Failed to create branch: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Error in branch operations: {e}")
        return None


async def demonstrate_file_operations(provider: GitLabProvider, branch_name: str):
    """Demonstrate file operations."""
    print(f"\n=== File Operations ===")
    
    if not branch_name:
        print("Skipping file operations (no demo branch available)")
        return
    
    try:
        # Create a new file
        print(f"Creating a new file on branch {branch_name}...")
        file_content = f"""# GitLab Provider Demo

This file was created by the GitLab provider demo script.

Created at: {datetime.now().isoformat()}
Branch: {branch_name}

## Features Demonstrated

- Project operations
- Branch management
- File creation and updates
- Commit operations
- Merge request workflow
- Pipeline integration

## GitLab-Specific Features

- Merge request approvals
- Pipeline status checking
- Project member management
- GitLab CI/CD integration

## Next Steps

This file will be used to demonstrate:
1. File updates
2. Multiple file commits
3. Merge request creation
4. Approval workflow
"""
        
        result = await provider.create_or_update_file(
            TEST_OWNER, TEST_REPO, "demo-file.md",
            file_content, "Add demo file via GitLab provider",
            branch_name, "GitLab Demo Bot", "demo@example.com"
        )
        
        print(f"✅ Created file: demo-file.md")
        print(f"  Branch: {result.get('branch', 'unknown')}")
        
        # Update the file
        print(f"\nUpdating the file...")
        updated_content = file_content + f"\n\nUpdated at: {datetime.now().isoformat()}\n"
        
        update_result = await provider.create_or_update_file(
            TEST_OWNER, TEST_REPO, "demo-file.md",
            updated_content, "Update demo file with timestamp",
            branch_name, "GitLab Demo Bot", "demo@example.com"
        )
        
        print(f"✅ Updated file: demo-file.md")
        
        # Get file content to verify
        print(f"\nRetrieving file content...")
        file_data = await provider.get_file_content(TEST_OWNER, TEST_REPO, "demo-file.md", branch_name)
        
        print(f"✅ Retrieved file: {file_data['file_name']}")
        print(f"  Size: {file_data.get('size', 'unknown')} bytes")
        print(f"  Encoding: {file_data.get('encoding', 'unknown')}")
        
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


async def demonstrate_commit_operations(provider: GitLabProvider, branch_name: str):
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
Main application file created by GitLab provider demo.
\"\"\"

def main():
    print("Hello from GitLab provider demo!")
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
            ".gitlab-ci.yml": f"""# GitLab CI/CD Pipeline
# Generated by GitLab provider demo

stages:
  - test
  - build
  - deploy

variables:
  DEMO_VERSION: "1.0.0"
  CREATED_AT: "{datetime.now().isoformat()}"

before_script:
  - echo "Starting GitLab CI/CD pipeline"
  - echo "Demo version: $DEMO_VERSION"

test:
  stage: test
  script:
    - echo "Running tests..."
    - python -m py_compile src/main.py
    - python -m py_compile src/utils.py
    - echo "Tests completed successfully"
  only:
    - merge_requests
    - main

build:
  stage: build
  script:
    - echo "Building application..."
    - mkdir -p dist
    - cp src/*.py dist/
    - echo "Build completed"
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour
  only:
    - main

deploy:
  stage: deploy
  script:
    - echo "Deploying application..."
    - echo "Deployment completed"
  only:
    - main
  when: manual
""",
            "README.md": f"""# GitLab Provider Demo Project

This project was created to demonstrate the GitLab provider functionality.

## Files

- `src/main.py` - Main application
- `src/utils.py` - Utility functions
- `demo-file.md` - Demo documentation
- `.gitlab-ci.yml` - GitLab CI/CD pipeline

## Created

- Date: {datetime.now().strftime('%Y-%m-%d')}
- Branch: {branch_name}
- Via: GitLab Provider Demo Script

## GitLab Features

This project demonstrates:
- Multi-file commits
- GitLab CI/CD integration
- Merge request workflow
- Approval processes
- Pipeline status tracking

## Usage

```bash
python src/main.py
```

## CI/CD Pipeline

The project includes a GitLab CI/CD pipeline with:
- Automated testing on merge requests
- Build artifacts generation
- Manual deployment step
"""
        }
        
        commit = await provider.commit_changes(
            TEST_OWNER, TEST_REPO, branch_name,
            "Add demo project structure with GitLab CI/CD pipeline",
            files, "GitLab Demo Bot", "demo@example.com"
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


async def demonstrate_mr_templates(provider: GitLabProvider):
    """Demonstrate MR template functionality."""
    print(f"\n=== MR Template System ===")
    
    # Show default template
    default_template = provider.get_mr_template()
    print(f"Default MR template preview:")
    lines = default_template.split('\n')[:8]
    for line in lines:
        print(f"  {line}")
    print(f"  ... (truncated)")
    
    # Create custom templates
    print(f"\nCreating custom MR templates...")
    
    feature_template = """## 🚀 Feature Description
{description}

## 📋 Type of Change
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update

## 🧪 Testing
- [ ] Tests pass locally
- [ ] New tests added for changes (if applicable)
- [ ] Manual testing completed
- [ ] Pipeline passes

## 📝 Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Documentation updated (if applicable)
- [ ] No new warnings introduced

## 🔄 Pipeline Status
- [ ] All pipeline jobs pass
- [ ] Security scans complete
- [ ] Code quality checks pass

## 👥 Approvals
- [ ] Required approvals obtained
- [ ] All discussions resolved

## 🔗 Related Issues
Closes #
"""
    
    bugfix_template = """## 🐛 Bug Fix Description
{description}

## 🔍 Root Cause Analysis
<!-- Describe what caused the bug -->

## 🛠️ Solution Implementation
<!-- Describe how you fixed it -->

## 🧪 Testing & Validation
- [ ] Bug reproduction steps verified
- [ ] Fix tested locally
- [ ] Regression tests added
- [ ] All existing tests pass
- [ ] Pipeline passes

## 📋 Type of Change
- [x] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] 💥 Breaking change (fix that would cause existing functionality to not work as expected)

## 📝 Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated (if applicable)

## 🔄 Pipeline & Approvals
- [ ] All pipeline jobs pass
- [ ] Required approvals obtained
- [ ] All discussions resolved

## 🔗 Related Issues
Fixes #
"""
    
    provider.set_mr_template("feature", feature_template)
    provider.set_mr_template("bugfix", bugfix_template)
    
    print(f"✅ Created custom templates:")
    print(f"  - feature: Enhanced template with GitLab-specific sections")
    print(f"  - bugfix: Bug-specific template with pipeline integration")
    
    # Test template retrieval
    feature_preview = provider.get_mr_template("feature")
    print(f"\nFeature template preview:")
    lines = feature_preview.split('\n')[:6]
    for line in lines:
        print(f"  {line}")
    print(f"  ... (truncated)")


async def demonstrate_merge_request_workflow(provider: GitLabProvider, branch_name: str, commit):
    """Demonstrate complete merge request workflow."""
    print(f"\n=== Merge Request Workflow ===")
    
    if not branch_name or not commit:
        print("Skipping MR workflow (no demo branch or commit available)")
        return
    
    try:
        # Create merge request with custom template
        print(f"Creating merge request from {branch_name}...")
        
        mr_description = """This MR demonstrates the GitLab provider functionality by adding:

- Demo documentation file
- Sample Python project structure
- GitLab CI/CD pipeline configuration
- Multiple file commit example
- Automated MR creation

The changes include a complete CI/CD pipeline with testing, building, and deployment stages.
All changes are safe and only add new files for demonstration purposes."""
        
        mr = await provider.create_pull_request(
            TEST_OWNER, TEST_REPO,
            "🚀 Add GitLab Provider Demo Files with CI/CD Pipeline",
            mr_description,
            branch_name, "main",  # Assuming main is the default branch
            draft=False,
            template_name="feature"
        )
        
        print(f"✅ Created merge request:")
        print(f"  Number: #{mr.number} (IID: {mr.iid})")
        print(f"  Title: {mr.title}")
        print(f"  URL: {mr.url}")
        print(f"  State: {mr.state}")
        print(f"  Author: {mr.author}")
        print(f"  Merge status: {mr.merge_status}")
        print(f"  Pipeline status: {mr.pipeline_status}")
        
        # Add a note to the MR
        print(f"\nAdding note to MR...")
        note_result = await provider.add_pr_comment(
            TEST_OWNER, TEST_REPO, mr.iid,  # Use IID for GitLab
            "🤖 This MR was created automatically by the GitLab provider demo script. "
            "It demonstrates the complete workflow from branch creation to MR management, "
            "including GitLab CI/CD pipeline integration."
        )
        
        print(f"✅ Added note to MR #{mr.iid}")
        
        # Update the MR
        print(f"\nUpdating MR title and description...")
        updated_mr = await provider.update_pull_request(
            TEST_OWNER, TEST_REPO, mr.iid,
            title="🚀 [DEMO] GitLab Provider Integration with CI/CD Pipeline",
            description=mr_description + "\n\n---\n**Note**: This is a demonstration MR created by the GitLab provider demo script."
        )
        
        print(f"✅ Updated MR:")
        print(f"  New title: {updated_mr.title}")
        
        # Check if we can get approval information
        try:
            print(f"\nChecking MR approval status...")
            approvals = await provider.get_mr_approvals(TEST_OWNER, TEST_REPO, mr.iid)
            print(f"  Approvals required: {approvals.get('approvals_required', 0)}")
            print(f"  Approvals received: {len(approvals.get('approved_by', []))}")
            print(f"  Can be merged: {approvals.get('merge_status') == 'can_be_merged'}")
        except Exception as e:
            print(f"  ⚠️  Could not get approval info: {e}")
        
        # List all MRs to show our new one
        print(f"\nListing recent merge requests...")
        mrs = await provider.list_pull_requests(TEST_OWNER, TEST_REPO, state="opened")
        
        print(f"Open merge requests ({len(mrs)}):")
        for mr_item in mrs[:5]:  # Show first 5
            status = "🟢" if mr_item.state == "opened" else "🔴"
            print(f"  {status} !{mr_item.iid}: {mr_item.title}")
            print(f"     {mr_item.source_branch} → {mr_item.target_branch}")
        
        return mr
        
    except Exception as e:
        print(f"❌ Error in MR workflow: {e}")
        return None


async def demonstrate_pipeline_integration(provider: GitLabProvider, branch_name: str, commit):
    """Demonstrate GitLab CI/CD pipeline integration."""
    print(f"\n=== Pipeline Integration ===")
    
    if not branch_name or not commit:
        print("Skipping pipeline demo (no demo branch or commit available)")
        return
    
    try:
        # Check pipeline status for the commit
        print(f"Checking pipeline status for commit {commit.sha[:8]}...")
        pipeline_status = await provider.get_pipeline_status(TEST_OWNER, TEST_REPO, commit.sha)
        
        if pipeline_status.get('status') != 'not_found':
            print(f"✅ Pipeline found:")
            print(f"  ID: {pipeline_status.get('id')}")
            print(f"  Status: {pipeline_status.get('status')}")
            print(f"  Ref: {pipeline_status.get('ref')}")
            print(f"  SHA: {pipeline_status.get('sha', '')[:8]}")
            print(f"  URL: {pipeline_status.get('web_url', 'N/A')}")
        else:
            print(f"⚠️  No pipeline found for commit (may not have triggered yet)")
        
        # Try to create a new pipeline
        print(f"\nTrying to create a new pipeline for branch {branch_name}...")
        try:
            new_pipeline = await provider.create_pipeline(
                TEST_OWNER, TEST_REPO, branch_name,
                variables={"DEMO_RUN": "true", "TRIGGER_SOURCE": "demo_script"}
            )
            
            print(f"✅ Created new pipeline:")
            print(f"  ID: {new_pipeline.get('id')}")
            print(f"  Status: {new_pipeline.get('status')}")
            print(f"  Ref: {new_pipeline.get('ref')}")
            print(f"  URL: {new_pipeline.get('web_url', 'N/A')}")
            
        except Exception as e:
            print(f"⚠️  Could not create pipeline: {e}")
            print(f"     This may be due to missing .gitlab-ci.yml or permissions")
        
    except Exception as e:
        print(f"❌ Error in pipeline integration: {e}")


async def demonstrate_project_members(provider: GitLabProvider):
    """Demonstrate project member management."""
    print(f"\n=== Project Members ===")
    
    try:
        print(f"Listing project members...")
        members = await provider.list_project_members(TEST_OWNER, TEST_REPO)
        
        print(f"Project members ({len(members)}):")
        for member in members[:10]:  # Show first 10 members
            access_level = {
                10: "Guest",
                20: "Reporter", 
                30: "Developer",
                40: "Maintainer",
                50: "Owner"
            }.get(member.get('access_level', 0), "Unknown")
            
            print(f"  👤 {member.get('username', 'unknown')} ({member.get('name', 'N/A')})")
            print(f"     Role: {access_level} (Level {member.get('access_level', 0)})")
            print(f"     State: {member.get('state', 'unknown')}")
        
        if len(members) > 10:
            print(f"  ... and {len(members) - 10} more members")
            
    except Exception as e:
        print(f"❌ Error getting project members: {e}")


async def demonstrate_error_handling(provider: GitLabProvider):
    """Demonstrate error handling scenarios."""
    print(f"\n=== Error Handling ===")
    
    # Test various error scenarios
    error_scenarios = [
        {
            "name": "Non-existent project",
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
            "expected": GitLabError
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


async def demonstrate_rate_limiting(provider: GitLabProvider):
    """Demonstrate rate limit monitoring."""
    print(f"\n=== Rate Limit Monitoring ===")
    
    try:
        # Get provider metrics
        print(f"Provider metrics:")
        metrics = provider.get_gitlab_metrics()
        print(f"  Success rate: {metrics['success_rate']:.2%}")
        print(f"  Average response time: {metrics['average_response_time_ms']:.2f}ms")
        print(f"  Request rate: {metrics['request_rate_per_minute']:.2f} req/min")
        print(f"  Recent requests: {metrics['recent_requests']}")
        
        # Check rate limit info if available
        rate_limit = provider.rate_limit_manager.get_rate_limit("gitlab")
        if rate_limit:
            print(f"\nRate limit information:")
            print(f"  Limit: {rate_limit.limit} requests")
            print(f"  Remaining: {rate_limit.remaining} requests")
            print(f"  Used: {rate_limit.used} requests")
            print(f"  Reset: {rate_limit.reset_time}")
            
            # Calculate usage percentage
            usage_percent = (rate_limit.used / rate_limit.limit) * 100 if rate_limit.limit > 0 else 0
            print(f"  Usage: {usage_percent:.1f}%")
        else:
            print(f"\nNo rate limit information available")
        
    except Exception as e:
        print(f"❌ Error checking rate limits: {e}")


async def cleanup_demo_resources(provider: GitLabProvider, branch_name: str, mr_iid: int = None):
    """Clean up demo resources."""
    print(f"\n=== Cleanup ===")
    
    if not branch_name:
        print("No demo branch to clean up")
        return
    
    try:
        # Note: In a real scenario, you might want to:
        # 1. Close the MR if it's still open
        # 2. Delete the demo branch
        # 3. Clean up any other resources
        
        print(f"Demo resources created:")
        print(f"  Branch: {branch_name}")
        if mr_iid:
            print(f"  Merge Request: !{mr_iid}")
        
        print(f"\n⚠️  Manual cleanup required:")
        print(f"  1. Review and close MR !{mr_iid} if desired")
        print(f"  2. Delete branch '{branch_name}' if no longer needed")
        print(f"  3. Remove demo files from project if desired")
        
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
    """Run all GitLab provider demonstrations."""
    print("GitLab VCS Provider Demonstration")
    print("=" * 50)
    
    # Check configuration
    if GITLAB_TOKEN == 'your-gitlab-token-here':
        print("❌ Please set your GitLab token in the GITLAB_TOKEN environment variable")
        print("   or update the GITLAB_TOKEN variable in this script.")
        return 1
    
    if TEST_OWNER == 'your-username' or TEST_REPO == 'test-repo':
        print("❌ Please update TEST_OWNER and TEST_REPO variables with your GitLab username and a test project")
        return 1
    
    provider = None
    branch_name = None
    mr = None
    
    try:
        # Utility functions
        demonstrate_utility_functions()
        
        # Authentication
        provider = await demonstrate_authentication()
        if not provider:
            return 1
        
        # Project operations
        repo = await demonstrate_project_operations(provider)
        if not repo:
            return 1
        
        # Branch operations
        branch_name = await demonstrate_branch_operations(provider, repo)
        
        # File operations
        file_success = await demonstrate_file_operations(provider, branch_name)
        
        # Commit operations
        commit = await demonstrate_commit_operations(provider, branch_name)
        
        # MR templates
        await demonstrate_mr_templates(provider)
        
        # Merge request workflow
        mr = await demonstrate_merge_request_workflow(provider, branch_name, commit)
        
        # Pipeline integration
        await demonstrate_pipeline_integration(provider, branch_name, commit)
        
        # Project members
        await demonstrate_project_members(provider)
        
        # Rate limiting
        await demonstrate_rate_limiting(provider)
        
        # Error handling
        await demonstrate_error_handling(provider)
        
        # Cleanup
        await cleanup_demo_resources(provider, branch_name, mr.iid if mr else None)
        
        print("\n" + "=" * 50)
        print("✅ GitLab provider demonstration completed successfully!")
        print("\nKey features demonstrated:")
        print("  - Authentication and user info retrieval")
        print("  - Project and branch management")
        print("  - File creation, updates, and content retrieval")
        print("  - Multi-file atomic commits")
        print("  - MR templates and customization")
        print("  - Complete merge request workflow")
        print("  - GitLab CI/CD pipeline integration")
        print("  - Project member management")
        print("  - Approval workflow support")
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