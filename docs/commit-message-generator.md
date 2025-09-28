# Commit Message Generator Guide

The AI Dev Squad Comparison platform includes an intelligent commit message generator that analyzes code diffs and automatically creates meaningful, well-formatted commit messages. This guide covers setup, usage, and customization of the commit message generation system.

## Overview

The commit message generator provides:

- **Intelligent Analysis**: Analyzes diffs to understand the nature and scope of changes
- **Multiple Styles**: Support for Conventional Commits, Gitmoji, Simple, and Detailed formats
- **Automatic Type Detection**: Determines commit type (feat, fix, docs, etc.) based on file changes
- **Context Awareness**: Detects scope, programming language, and breaking changes
- **Performance Caching**: Caches generated messages for improved performance
- **Customizable Templates**: Configurable templates for different commit types and styles
- **Validation**: Built-in validation against configurable rules

## Quick Start

### Basic Usage

```python
from common.vcs import generate_commit_message

# Generate commit message from diff
diff_text = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,5 @@
 # My Project
+
+## Installation
+pip install -r requirements.txt
+
 Description here.
"""

message = generate_commit_message(diff_text)
print(message)  # "docs: update README with installation instructions"
```

### With VCS Providers

```python
from common.vcs import GitHubProvider, generate_commit_message

async with GitHubProvider() as github:
    await github.authenticate(token)
    
    # Get diff for current changes
    diff = await github.get_diff("owner", "repo", "feature-branch")
    
    # Generate commit message
    message = generate_commit_message(diff)
    
    # Commit with generated message
    commit = await github.commit_changes(
        "owner", "repo", "feature-branch", message, files
    )
```

## Configuration

### Message Styles

The generator supports multiple commit message styles:

#### Conventional Commits (Default)
```python
from common.vcs import CommitMessageConfig, MessageStyle

config = CommitMessageConfig(style=MessageStyle.CONVENTIONAL)
# Output: "feat(auth): add user authentication"
```

#### Gitmoji
```python
config = CommitMessageConfig(style=MessageStyle.GITMOJI)
# Output: "✨ add user authentication"
```

#### Simple
```python
config = CommitMessageConfig(style=MessageStyle.SIMPLE)
# Output: "add user authentication"
```

#### Detailed
```python
config = CommitMessageConfig(style=MessageStyle.DETAILED)
# Output: Multi-line message with body and footer
```

### Configuration Options

```python
from common.vcs import CommitMessageConfig, MessageStyle

config = CommitMessageConfig(
    style=MessageStyle.CONVENTIONAL,
    max_subject_length=72,          # Maximum subject line length
    max_body_length=100,            # Maximum body line length
    include_stats=False,            # Include change statistics
    include_files=False,            # Include file list in body
    use_emoji=False,                # Use emoji in messages
    require_scope=False,            # Require scope in conventional commits
    require_issue_reference=False,  # Require issue reference
    breaking_change_prefix="!",     # Breaking change indicator
)
```

### Custom Templates

```python
config = CommitMessageConfig()

# Customize templates for specific commit types
config.templates[CommitType.FEAT] = "🚀 {type}{scope}: {description}"
config.templates[CommitType.FIX] = "🔧 {type}{scope}: {description}"

# Use custom configuration
generator = CommitMessageGenerator(config)
message = generator.generate(diff_text)
```

## Commit Types

The generator automatically detects commit types based on file changes:

### Feature (feat)
- New files added
- New functionality implemented
- Keywords: add, new, feature, implement, create

### Bug Fix (fix)
- Existing files modified with bug-related changes
- Keywords: fix, bug, issue, error, resolve

### Documentation (docs)
- Markdown, text, or documentation files
- Files: `*.md`, `*.rst`, `*.txt`, `docs/`, `README*`

### Tests (test)
- Test files added or modified
- Files: `test_*`, `*_test.*`, `tests/`, `__tests__/`

### CI/CD (ci)
- CI/CD configuration files
- Files: `.github/`, `.gitlab-ci*`, `Jenkinsfile`

### Build (build)
- Build system files
- Files: `package.json`, `requirements.txt`, `Dockerfile`

### Style (style)
- Code formatting changes
- Keywords: format, style, lint, prettier

### Refactor (refactor)
- Code restructuring without functional changes
- Keywords: refactor, restructure, cleanup

### Performance (perf)
- Performance improvements
- Keywords: performance, optimize, speed

### Chore (chore)
- Maintenance tasks
- Keywords: chore, maintenance, update

## Advanced Features

### Multiple Suggestions

```python
from common.vcs import suggest_commit_messages

# Generate multiple message options
suggestions = suggest_commit_messages(diff_text, count=5)

print("Suggested commit messages:")
for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion}")

# Let user choose or use the first suggestion
chosen_message = suggestions[0]
```

### Diff Analysis

```python
from common.vcs import analyze_commit_diff

# Analyze diff to get detailed context
context = analyze_commit_diff(diff_text)

print(f"Files changed: {len(context.files)}")
print(f"Primary language: {context.get_primary_language()}")
print(f"Affected areas: {context.get_affected_areas()}")
print(f"Breaking changes: {context.breaking_changes}")
print(f"Scope: {context.scope}")

# Statistics
print(f"Lines added: {context.stats.lines_added}")
print(f"Lines removed: {context.stats.lines_removed}")
print(f"Net change: {context.stats.net_changes}")
```

### Message Validation

```python
from common.vcs import validate_commit_message, CommitMessageConfig

config = CommitMessageConfig(
    style=MessageStyle.CONVENTIONAL,
    max_subject_length=50,
    require_scope=True
)

message = "feat(auth): add user authentication"
is_valid, errors = validate_commit_message(message, config)

if is_valid:
    print("✅ Message is valid")
else:
    print("❌ Message validation failed:")
    for error in errors:
        print(f"  - {error}")
```

### Breaking Change Detection

```python
# The generator automatically detects breaking changes
breaking_diff = """diff --git a/api.py b/api.py
--- a/api.py
+++ b/api.py
@@ -1,3 +1,3 @@
-def authenticate(username, password):
+def authenticate(credentials):
     # BREAKING CHANGE: function signature changed
     pass
"""

message = generate_commit_message(breaking_diff)
print(message)  # "feat!: change authentication method"
```

### Caching

The generator includes intelligent caching for improved performance:

```python
from common.vcs import CommitMessageGenerator

# Caching is enabled by default
generator = CommitMessageGenerator(use_cache=True)

# First generation (slower)
message1 = generator.generate(diff_text)

# Second generation (faster, uses cache)
message2 = generator.generate(diff_text)  # Same diff = cached result

# Clear cache if needed
generator.cache.clear_expired()
```

## Configuration File

Create a configuration file for consistent settings across your project:

```yaml
# config/commit_messages.yaml
commit_messages:
  style: "conventional"
  max_subject_length: 72
  require_scope: true
  include_stats: false
  enable_cache: true
  
  templates:
    conventional:
      feat: "{type}({scope}): {description}"
      fix: "{type}({scope}): {description}"
      docs: "{type}({scope}): {description}"
  
  validation:
    enabled: true
    rules:
      conventional:
        require_format: true
        valid_types: ["feat", "fix", "docs", "style", "refactor", "test", "chore"]
```

Load configuration:

```python
import yaml
from common.vcs import CommitMessageConfig

with open('config/commit_messages.yaml', 'r') as f:
    config_data = yaml.safe_load(f)

config = CommitMessageConfig(**config_data['commit_messages'])
```

## Integration Examples

### With GitHub

```python
from common.vcs import GitHubProvider, generate_commit_message

async def commit_with_generated_message(files_to_commit):
    async with GitHubProvider() as github:
        await github.authenticate(token)
        
        # Create branch
        branch = await github.create_branch("owner", "repo", "feature/auto-commit")
        
        # Commit files
        commit = await github.commit_changes(
            "owner", "repo", "feature/auto-commit",
            generate_commit_message(get_diff(files_to_commit)),
            files_to_commit
        )
        
        # Create PR with generated title
        pr_title = f"Add {', '.join(files_to_commit.keys())}"
        pr = await github.create_pull_request(
            "owner", "repo", pr_title,
            "Automatically generated PR", "feature/auto-commit"
        )
        
        return pr
```

### With GitLab

```python
from common.vcs import GitLabProvider, CommitMessageConfig, MessageStyle

async def gitlab_workflow():
    config = CommitMessageConfig(
        style=MessageStyle.CONVENTIONAL,
        require_scope=True
    )
    
    async with GitLabProvider() as gitlab:
        await gitlab.authenticate(token)
        
        # Generate message with custom config
        message = generate_commit_message(diff_text, config)
        
        # Commit changes
        commit = await gitlab.commit_changes(
            "owner", "project", "main", message, files
        )
        
        return commit
```

### AI Agent Integration

```python
from common.vcs import CommitMessageConfig, MessageStyle

# Configuration for AI-generated commits
ai_config = CommitMessageConfig(
    style=MessageStyle.CONVENTIONAL,
    templates={
        CommitType.FEAT: "[AI] feat{scope}: {description}",
        CommitType.FIX: "[AI] fix{scope}: {description}",
        CommitType.DOCS: "[AI] docs{scope}: {description}",
    }
)

def ai_commit_workflow(agent_changes):
    # Generate commit message for AI changes
    message = generate_commit_message(agent_changes['diff'], ai_config)
    
    # Add agent metadata
    message += f"\n\nGenerated by: {agent_changes['agent_name']}"
    message += f"\nConfidence: {agent_changes['confidence']:.2%}"
    
    return message
```

## Best Practices

### Message Quality
1. **Review Generated Messages**: Always review generated messages before committing
2. **Customize Templates**: Adapt templates to match your project's conventions
3. **Use Appropriate Styles**: Choose the style that fits your team's workflow
4. **Validate Messages**: Enable validation to ensure consistency

### Performance
1. **Enable Caching**: Use caching for repeated operations
2. **Configure Cache Size**: Set appropriate cache limits for your environment
3. **Clean Cache Regularly**: Remove expired cache entries periodically

### Team Consistency
1. **Shared Configuration**: Use shared configuration files across the team
2. **Validation Rules**: Enforce consistent message format with validation
3. **Template Standards**: Establish team-wide template standards
4. **Review Process**: Include commit message review in your process

### AI Agent Usage
1. **Prefix AI Commits**: Clearly mark AI-generated commits
2. **Include Metadata**: Add agent information and confidence scores
3. **Human Review**: Always have human review for AI-generated commits
4. **Fallback Messages**: Provide fallback for generation failures

## Troubleshooting

### Common Issues

#### Generation Fails
```python
try:
    message = generate_commit_message(diff_text)
except Exception as e:
    # Fallback to simple message
    message = "update files"
    logger.warning(f"Commit message generation failed: {e}")
```

#### Invalid Diff Format
```python
from common.vcs import analyze_commit_diff

try:
    context = analyze_commit_diff(diff_text)
    if not context.files:
        raise ValueError("No files found in diff")
except Exception as e:
    logger.error(f"Diff analysis failed: {e}")
    # Use manual commit message
```

#### Cache Issues
```python
# Clear cache if corrupted
generator.cache.clear_expired()

# Disable cache temporarily
generator = CommitMessageGenerator(use_cache=False)
```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.getLogger('common.vcs.commit_msgs').setLevel(logging.DEBUG)

# Generate with detailed logging
message = generate_commit_message(diff_text)
```

## Examples

See the `examples/commit_msgs_demo.py` file for comprehensive examples demonstrating:

- Diff analysis and context extraction
- Multiple message styles
- Custom configuration
- Commit type detection
- Message validation
- Caching performance
- VCS provider integration

## API Reference

For detailed API documentation, see:

- [Commit Message Generator](../common/vcs/commit_msgs.py)
- [VCS Integration Guide](vcs-integration.md)
- [Configuration Examples](../config/commit_messages.example.yaml)

## Contributing

When contributing to the commit message generator:

1. Add tests for new features
2. Update documentation
3. Follow existing code patterns
4. Test with various diff formats
5. Validate performance impact

For detailed contribution guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).