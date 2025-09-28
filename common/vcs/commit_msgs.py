"""
Commit Message Generator

This module provides intelligent commit message generation using small local models
and diff analysis. It supports:
- Conventional commit format generation
- Diff analysis and summarization
- Template system for different commit types
- Caching for similar diffs to improve performance
- Configuration for commit message style and length limits
- Multiple commit message styles and formats
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
import difflib

logger = logging.getLogger(__name__)


class CommitType(str, Enum):
    """Conventional commit types."""
    FEAT = "feat"        # New feature
    FIX = "fix"          # Bug fix
    DOCS = "docs"        # Documentation changes
    STYLE = "style"      # Code style changes (formatting, etc.)
    REFACTOR = "refactor"  # Code refactoring
    TEST = "test"        # Adding or updating tests
    CHORE = "chore"      # Maintenance tasks
    PERF = "perf"        # Performance improvements
    CI = "ci"            # CI/CD changes
    BUILD = "build"      # Build system changes
    REVERT = "revert"    # Revert previous commit


class MessageStyle(str, Enum):
    """Commit message styles."""
    CONVENTIONAL = "conventional"  # type(scope): description
    SIMPLE = "simple"             # Simple descriptive message
    DETAILED = "detailed"         # Multi-line with body and footer
    GITMOJI = "gitmoji"          # Emoji-based commit messages


@dataclass
class DiffStats:
    """Statistics about a diff."""
    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0
    
    @property
    def total_changes(self) -> int:
        """Total number of line changes."""
        return self.lines_added + self.lines_removed + self.lines_modified
    
    @property
    def net_changes(self) -> int:
        """Net change in lines (added - removed)."""
        return self.lines_added - self.lines_removed


@dataclass
class FileChange:
    """Represents a change to a single file."""
    path: str
    change_type: str  # added, modified, deleted, renamed
    old_path: Optional[str] = None  # For renames
    lines_added: int = 0
    lines_removed: int = 0
    is_binary: bool = False
    language: Optional[str] = None
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return Path(self.path).suffix.lower()
    
    @property
    def file_name(self) -> str:
        """Get file name without path."""
        return Path(self.path).name

@dataclass
class CommitContext:
    """Context information for commit message generation."""
    files: List[FileChange] = field(default_factory=list)
    stats: DiffStats = field(default_factory=DiffStats)
    branch_name: Optional[str] = None
    issue_numbers: List[str] = field(default_factory=list)
    breaking_changes: bool = False
    scope: Optional[str] = None
    
    def get_primary_language(self) -> Optional[str]:
        """Get the primary programming language from changed files."""
        language_counts = {}
        for file_change in self.files:
            if file_change.language:
                language_counts[file_change.language] = language_counts.get(file_change.language, 0) + 1
        
        if language_counts:
            return max(language_counts, key=language_counts.get)
        return None
    
    def get_affected_areas(self) -> Set[str]:
        """Get affected areas/modules from file paths."""
        areas = set()
        for file_change in self.files:
            path_parts = Path(file_change.path).parts
            if len(path_parts) > 1:
                # Use first directory as area
                areas.add(path_parts[0])
            elif file_change.file_extension in ['.py', '.js', '.ts', '.java', '.go']:
                # For root-level code files, use 'core'
                areas.add('core')
        return areas


@dataclass
class CommitMessageConfig:
    """Configuration for commit message generation."""
    style: MessageStyle = MessageStyle.CONVENTIONAL
    max_subject_length: int = 72
    max_body_length: int = 100
    include_stats: bool = False
    include_files: bool = False
    use_emoji: bool = False
    require_scope: bool = False
    require_issue_reference: bool = False
    breaking_change_prefix: str = "!"
    
    # Template configurations
    templates: Dict[CommitType, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default templates."""
        if not self.templates:
            self.templates = self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[CommitType, str]:
        """Get default commit message templates."""
        if self.style == MessageStyle.CONVENTIONAL:
            return {
                CommitType.FEAT: "{type}{scope}: {description}",
                CommitType.FIX: "{type}{scope}: {description}",
                CommitType.DOCS: "{type}{scope}: {description}",
                CommitType.STYLE: "{type}{scope}: {description}",
                CommitType.REFACTOR: "{type}{scope}: {description}",
                CommitType.TEST: "{type}{scope}: {description}",
                CommitType.CHORE: "{type}{scope}: {description}",
                CommitType.PERF: "{type}{scope}: {description}",
                CommitType.CI: "{type}{scope}: {description}",
                CommitType.BUILD: "{type}{scope}: {description}",
                CommitType.REVERT: "revert: {description}",
            }
        elif self.style == MessageStyle.GITMOJI:
            return {
                CommitType.FEAT: "✨ {description}",
                CommitType.FIX: "🐛 {description}",
                CommitType.DOCS: "📚 {description}",
                CommitType.STYLE: "💄 {description}",
                CommitType.REFACTOR: "♻️ {description}",
                CommitType.TEST: "✅ {description}",
                CommitType.CHORE: "🔧 {description}",
                CommitType.PERF: "⚡ {description}",
                CommitType.CI: "👷 {description}",
                CommitType.BUILD: "📦 {description}",
                CommitType.REVERT: "⏪ {description}",
            }
        else:
            return {commit_type: "{description}" for commit_type in CommitType}


class DiffAnalyzer:
    """Analyzes diffs to extract meaningful information for commit messages."""
    
    def __init__(self):
        self.language_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'LESS',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.md': 'Markdown',
            '.rst': 'reStructuredText',
            '.tex': 'LaTeX',
        }
    
    def analyze_diff(self, diff_text: str) -> CommitContext:
        """Analyze a unified diff and extract commit context."""
        context = CommitContext()
        
        # Parse diff to extract file changes
        files = self._parse_diff(diff_text)
        context.files = files
        
        # Calculate statistics
        context.stats = self._calculate_stats(files)
        
        # Detect breaking changes
        context.breaking_changes = self._detect_breaking_changes(files, diff_text)
        
        # Extract scope from file paths
        context.scope = self._determine_scope(files)
        
        return context
    
    def _parse_diff(self, diff_text: str) -> List[FileChange]:
        """Parse unified diff text into FileChange objects."""
        files = []
        current_file = None
        
        for line in diff_text.split('\n'):
            if line.startswith('diff --git'):
                # New file diff
                if current_file:
                    files.append(current_file)
                
                # Extract file paths
                match = re.search(r'diff --git a/(.*?) b/(.*?)$', line)
                if match:
                    old_path, new_path = match.groups()
                    current_file = FileChange(
                        path=new_path,
                        old_path=old_path if old_path != new_path else None,
                        change_type='modified'
                    )
                    
                    # Determine language
                    extension = Path(new_path).suffix.lower()
                    current_file.language = self.language_extensions.get(extension)
            
            elif line.startswith('new file mode'):
                if current_file:
                    current_file.change_type = 'added'
            
            elif line.startswith('deleted file mode'):
                if current_file:
                    current_file.change_type = 'deleted'
            
            elif line.startswith('rename from'):
                if current_file:
                    current_file.change_type = 'renamed'
            
            elif line.startswith('Binary files'):
                if current_file:
                    current_file.is_binary = True
            
            elif line.startswith('+') and not line.startswith('+++'):
                if current_file and not current_file.is_binary:
                    current_file.lines_added += 1
            
            elif line.startswith('-') and not line.startswith('---'):
                if current_file and not current_file.is_binary:
                    current_file.lines_removed += 1
        
        # Add the last file
        if current_file:
            files.append(current_file)
        
        return files
    
    def _calculate_stats(self, files: List[FileChange]) -> DiffStats:
        """Calculate overall diff statistics."""
        stats = DiffStats()
        stats.files_changed = len(files)
        
        for file_change in files:
            stats.lines_added += file_change.lines_added
            stats.lines_removed += file_change.lines_removed
        
        return stats
    
    def _detect_breaking_changes(self, files: List[FileChange], diff_text: str) -> bool:
        """Detect if changes include breaking changes."""
        # Look for breaking change indicators
        breaking_indicators = [
            'BREAKING CHANGE',
            'breaking change',
            'breaking:',
            'BREAKING:',
            'removed',
            'deprecated',
            'incompatible'
        ]
        
        diff_lower = diff_text.lower()
        return any(indicator in diff_lower for indicator in breaking_indicators)
    
    def _determine_scope(self, files: List[FileChange]) -> Optional[str]:
        """Determine the scope based on changed files."""
        if not files:
            return None
        
        # Get affected areas
        areas = set()
        for file_change in files:
            path_parts = Path(file_change.path).parts
            if len(path_parts) > 1:
                areas.add(path_parts[0])
        
        # If all changes are in one area, use that as scope
        if len(areas) == 1:
            return areas.pop()
        
        # If multiple areas but similar, try to find common scope
        if len(areas) <= 3:
            return ','.join(sorted(areas))
        
        return None


class CommitMessageCache:
    """Cache for generated commit messages to improve performance."""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_age_days: int = 30):
        self.cache_dir = cache_dir or Path.home() / '.cache' / 'commit_msgs'
        self.max_age_days = max_age_days
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, diff_text: str, config: CommitMessageConfig) -> str:
        """Generate cache key for diff and config."""
        content = f"{diff_text}{config.style.value}{config.max_subject_length}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get(self, diff_text: str, config: CommitMessageConfig) -> Optional[str]:
        """Get cached commit message if available."""
        cache_key = self._get_cache_key(diff_text, config)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > timedelta(days=self.max_age_days):
                cache_file.unlink()  # Remove expired cache
                return None
            
            return cache_data['message']
        
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file, remove it
            cache_file.unlink()
            return None
    
    def set(self, diff_text: str, config: CommitMessageConfig, message: str):
        """Cache a generated commit message."""
        cache_key = self._get_cache_key(diff_text, config)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cache_data = {
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'config_style': config.style.value
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache commit message: {e}")
    
    def clear_expired(self):
        """Clear expired cache entries."""
        cutoff_time = datetime.now() - timedelta(days=self.max_age_days)
        
        for cache_file in self.cache_dir.glob('*.json'):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                if cached_time < cutoff_time:
                    cache_file.unlink()
            
            except Exception:
                # If we can't read the file, remove it
                cache_file.unlink()


class CommitMessageGenerator:
    """Generates commit messages using diff analysis and templates."""
    
    def __init__(self, config: Optional[CommitMessageConfig] = None, 
                 use_cache: bool = True):
        self.config = config or CommitMessageConfig()
        self.analyzer = DiffAnalyzer()
        self.cache = CommitMessageCache() if use_cache else None
        
        # Simple keyword-based commit type detection
        self.type_keywords = {
            CommitType.FEAT: ['add', 'new', 'feature', 'implement', 'create', 'introduce'],
            CommitType.FIX: ['fix', 'bug', 'issue', 'error', 'problem', 'resolve', 'correct'],
            CommitType.DOCS: ['doc', 'readme', 'comment', 'documentation', 'guide'],
            CommitType.STYLE: ['format', 'style', 'lint', 'prettier', 'whitespace'],
            CommitType.REFACTOR: ['refactor', 'restructure', 'reorganize', 'cleanup', 'simplify'],
            CommitType.TEST: ['test', 'spec', 'coverage', 'mock', 'unit', 'integration'],
            CommitType.CHORE: ['chore', 'maintenance', 'update', 'upgrade', 'dependency'],
            CommitType.PERF: ['performance', 'optimize', 'speed', 'faster', 'efficient'],
            CommitType.CI: ['ci', 'pipeline', 'workflow', 'action', 'build'],
            CommitType.BUILD: ['build', 'compile', 'package', 'bundle', 'webpack'],
        }
    
    def generate(self, diff_text: str, custom_message: Optional[str] = None) -> str:
        """Generate a commit message from diff text."""
        # Check cache first
        if self.cache:
            cached_message = self.cache.get(diff_text, self.config)
            if cached_message:
                logger.debug("Using cached commit message")
                return cached_message
        
        # Analyze the diff
        context = self.analyzer.analyze_diff(diff_text)
        
        # Generate message
        if custom_message:
            message = self._format_custom_message(custom_message, context)
        else:
            message = self._generate_automatic_message(context)
        
        # Cache the result
        if self.cache:
            self.cache.set(diff_text, self.config, message)
        
        return message
    
    def _generate_automatic_message(self, context: CommitContext) -> str:
        """Generate commit message automatically from context."""
        # Determine commit type
        commit_type = self._determine_commit_type(context)
        
        # Generate description
        description = self._generate_description(context, commit_type)
        
        # Format message according to style
        return self._format_message(commit_type, description, context)
    
    def _determine_commit_type(self, context: CommitContext) -> CommitType:
        """Determine the most appropriate commit type."""
        # Check file patterns first
        file_patterns = {
            CommitType.DOCS: ['.md', '.rst', '.txt', 'readme', 'doc/', 'docs/'],
            CommitType.TEST: ['test_', '_test.', 'spec_', '_spec.', 'tests/', '__tests__/'],
            CommitType.CI: ['.github/', '.gitlab-ci', 'Jenkinsfile', '.travis', 'azure-pipelines'],
            CommitType.BUILD: ['package.json', 'requirements.txt', 'Dockerfile', 'Makefile', 'pom.xml'],
        }
        
        for commit_type, patterns in file_patterns.items():
            if any(any(pattern in file_change.path.lower() for pattern in patterns) 
                   for file_change in context.files):
                return commit_type
        
        # Check for new files (likely features)
        if any(fc.change_type == 'added' for fc in context.files):
            return CommitType.FEAT
        
        # Check for deleted files
        if any(fc.change_type == 'deleted' for fc in context.files):
            return CommitType.CHORE
        
        # Default to fix for modifications
        return CommitType.FIX
    
    def _generate_description(self, context: CommitContext, commit_type: CommitType) -> str:
        """Generate a description based on the context and commit type."""
        if not context.files:
            return "update files"
        
        # Generate description based on changes
        if len(context.files) == 1:
            file_change = context.files[0]
            if commit_type == CommitType.FEAT:
                return f"add {file_change.file_name}"
            elif commit_type == CommitType.FIX:
                return f"fix issue in {file_change.file_name}"
            elif commit_type == CommitType.DOCS:
                return f"update {file_change.file_name}"
            else:
                return f"update {file_change.file_name}"
        
        # Multiple files
        primary_language = context.get_primary_language()
        affected_areas = context.get_affected_areas()
        
        if commit_type == CommitType.FEAT:
            if affected_areas:
                area = list(affected_areas)[0] if len(affected_areas) == 1 else "multiple areas"
                return f"add new functionality to {area}"
            else:
                return f"add new {primary_language or 'code'} functionality"
        
        elif commit_type == CommitType.FIX:
            if affected_areas:
                area = list(affected_areas)[0] if len(affected_areas) == 1 else "multiple areas"
                return f"fix issues in {area}"
            else:
                return f"fix {primary_language or 'code'} issues"
        
        elif commit_type == CommitType.DOCS:
            return "update documentation"
        
        elif commit_type == CommitType.TEST:
            return f"update tests for {list(affected_areas)[0] if affected_areas else 'code'}"
        
        else:
            files_desc = f"{context.stats.files_changed} files"
            return f"update {files_desc}"
    
    def _format_message(self, commit_type: CommitType, description: str, 
                       context: CommitContext) -> str:
        """Format the final commit message."""
        # Get template
        template = self.config.templates.get(commit_type, "{description}")
        
        # Prepare template variables
        scope_str = ""
        if context.scope and self.config.require_scope:
            scope_str = f"({context.scope})"
        elif context.scope:
            scope_str = f"({context.scope})"
        
        breaking_prefix = ""
        if context.breaking_changes:
            breaking_prefix = self.config.breaking_change_prefix
        
        # Format the subject line
        subject = template.format(
            type=commit_type.value + breaking_prefix,
            scope=scope_str,
            description=description
        )
        
        # Truncate if too long
        if len(subject) > self.config.max_subject_length:
            max_desc_length = (self.config.max_subject_length - 
                             len(commit_type.value) - len(scope_str) - 3)  # ": " + breaking_prefix
            description = description[:max_desc_length].rstrip()
            subject = template.format(
                type=commit_type.value + breaking_prefix,
                scope=scope_str,
                description=description
            )
        
        # Add body if detailed style
        if self.config.style == MessageStyle.DETAILED:
            body_parts = []
            
            if self.config.include_stats and context.stats.total_changes > 0:
                body_parts.append(
                    f"Changes: {context.stats.files_changed} files, "
                    f"+{context.stats.lines_added}/-{context.stats.lines_removed} lines"
                )
            
            if self.config.include_files and context.files:
                files_list = [f"- {fc.path}" for fc in context.files[:5]]
                if len(context.files) > 5:
                    files_list.append(f"- ... and {len(context.files) - 5} more files")
                body_parts.append("Files changed:\n" + "\n".join(files_list))
            
            if body_parts:
                subject += "\n\n" + "\n\n".join(body_parts)
        
        return subject
    
    def _format_custom_message(self, custom_message: str, context: CommitContext) -> str:
        """Format a custom message with context information."""
        message = custom_message
        
        # Add scope if available and not already present
        if context.scope and f"({context.scope})" not in message:
            # Try to detect if it's conventional format
            if ':' in message and not message.startswith('Merge'):
                parts = message.split(':', 1)
                message = f"{parts[0]}({context.scope}):{parts[1]}"
        
        # Add breaking change indicator if needed
        if context.breaking_changes and self.config.breaking_change_prefix not in message:
            if ':' in message:
                parts = message.split(':', 1)
                message = f"{parts[0]}{self.config.breaking_change_prefix}:{parts[1]}"
        
        return message
    
    def suggest_messages(self, diff_text: str, count: int = 3) -> List[str]:
        """Generate multiple commit message suggestions."""
        context = self.analyzer.analyze_diff(diff_text)
        messages = []
        
        # Try different commit types that might be appropriate
        possible_types = [self._determine_commit_type(context)]
        
        # Add alternative types based on context
        if any(fc.change_type == 'added' for fc in context.files):
            possible_types.append(CommitType.FEAT)
        if any('fix' in fc.path.lower() or 'bug' in fc.path.lower() for fc in context.files):
            possible_types.append(CommitType.FIX)
        if any('.md' in fc.path.lower() or 'doc' in fc.path.lower() for fc in context.files):
            possible_types.append(CommitType.DOCS)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_types = []
        for ct in possible_types:
            if ct not in seen:
                seen.add(ct)
                unique_types.append(ct)
        
        # Generate messages for each type
        for commit_type in unique_types[:count]:
            description = self._generate_description(context, commit_type)
            message = self._format_message(commit_type, description, context)
            messages.append(message)
        
        # If we need more messages, try different styles
        while len(messages) < count:
            # Try simpler descriptions
            simple_desc = f"update {context.stats.files_changed} files"
            simple_msg = self._format_message(CommitType.CHORE, simple_desc, context)
            if simple_msg not in messages:
                messages.append(simple_msg)
            else:
                break
        
        return messages[:count]


# Utility functions for integration with VCS providers

def generate_commit_message(diff_text: str, 
                          config: Optional[CommitMessageConfig] = None,
                          custom_message: Optional[str] = None) -> str:
    """Generate a commit message from diff text."""
    generator = CommitMessageGenerator(config)
    return generator.generate(diff_text, custom_message)


def suggest_commit_messages(diff_text: str, 
                          count: int = 3,
                          config: Optional[CommitMessageConfig] = None) -> List[str]:
    """Generate multiple commit message suggestions."""
    generator = CommitMessageGenerator(config)
    return generator.suggest_messages(diff_text, count)


def analyze_commit_diff(diff_text: str) -> CommitContext:
    """Analyze a diff and return context information."""
    analyzer = DiffAnalyzer()
    return analyzer.analyze_diff(diff_text)


def validate_commit_message(message: str, config: Optional[CommitMessageConfig] = None) -> Tuple[bool, List[str]]:
    """Validate a commit message against configuration rules."""
    config = config or CommitMessageConfig()
    errors = []
    
    lines = message.split('\n')
    subject = lines[0] if lines else ""
    
    # Check subject length
    if len(subject) > config.max_subject_length:
        errors.append(f"Subject line too long ({len(subject)} > {config.max_subject_length})")
    
    # Check conventional commit format if required
    if config.style == MessageStyle.CONVENTIONAL:
        if not re.match(r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?!?: .+', subject):
            errors.append("Subject line doesn't follow conventional commit format")
    
    # Check for scope if required
    if config.require_scope and config.style == MessageStyle.CONVENTIONAL:
        if not re.search(r'\(.+\)', subject):
            errors.append("Scope is required but not found")
    
    # Check for issue reference if required
    if config.require_issue_reference:
        if not re.search(r'#\d+', message):
            errors.append("Issue reference is required but not found")
    
    return len(errors) == 0, errors