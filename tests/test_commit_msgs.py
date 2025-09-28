"""
Tests for commit message generation functionality.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from common.vcs.commit_msgs import (
    CommitMessageGenerator, CommitMessageConfig, CommitContext, DiffAnalyzer,
    CommitType, MessageStyle, FileChange, DiffStats, CommitMessageCache,
    generate_commit_message, suggest_commit_messages, analyze_commit_diff,
    validate_commit_message
)


class TestCommitType:
    """Test CommitType enum."""
    
    def test_commit_types(self):
        """Test all commit types are available."""
        expected_types = [
            "feat", "fix", "docs", "style", "refactor", 
            "test", "chore", "perf", "ci", "build", "revert"
        ]
        
        for expected in expected_types:
            assert hasattr(CommitType, expected.upper())
            assert getattr(CommitType, expected.upper()).value == expected


class TestMessageStyle:
    """Test MessageStyle enum."""
    
    def test_message_styles(self):
        """Test all message styles are available."""
        expected_styles = ["conventional", "simple", "detailed", "gitmoji"]
        
        for expected in expected_styles:
            assert hasattr(MessageStyle, expected.upper())
            assert getattr(MessageStyle, expected.upper()).value == expected


class TestDiffStats:
    """Test DiffStats functionality."""
    
    def test_diff_stats_creation(self):
        """Test creating DiffStats."""
        stats = DiffStats(
            files_changed=3,
            lines_added=50,
            lines_removed=20,
            lines_modified=10
        )
        
        assert stats.files_changed == 3
        assert stats.lines_added == 50
        assert stats.lines_removed == 20
        assert stats.lines_modified == 10
    
    def test_total_changes(self):
        """Test total changes calculation."""
        stats = DiffStats(lines_added=50, lines_removed=20, lines_modified=10)
        assert stats.total_changes == 80
    
    def test_net_changes(self):
        """Test net changes calculation."""
        stats = DiffStats(lines_added=50, lines_removed=20)
        assert stats.net_changes == 30


class TestFileChange:
    """Test FileChange functionality."""
    
    def test_file_change_creation(self):
        """Test creating FileChange."""
        file_change = FileChange(
            path="src/main.py",
            change_type="modified",
            lines_added=10,
            lines_removed=5,
            language="Python"
        )
        
        assert file_change.path == "src/main.py"
        assert file_change.change_type == "modified"
        assert file_change.lines_added == 10
        assert file_change.lines_removed == 5
        assert file_change.language == "Python"
    
    def test_file_extension(self):
        """Test file extension extraction."""
        file_change = FileChange(path="src/main.py", change_type="added")
        assert file_change.file_extension == ".py"
        
        file_change = FileChange(path="README.md", change_type="added")
        assert file_change.file_extension == ".md"
    
    def test_file_name(self):
        """Test file name extraction."""
        file_change = FileChange(path="src/utils/helper.py", change_type="added")
        assert file_change.file_name == "helper.py"


class TestCommitContext:
    """Test CommitContext functionality."""
    
    def test_commit_context_creation(self):
        """Test creating CommitContext."""
        files = [
            FileChange(path="src/main.py", change_type="modified", language="Python"),
            FileChange(path="src/utils.py", change_type="added", language="Python")
        ]
        stats = DiffStats(files_changed=2, lines_added=30, lines_removed=10)
        
        context = CommitContext(
            files=files,
            stats=stats,
            branch_name="feature/new-feature",
            breaking_changes=False
        )
        
        assert len(context.files) == 2
        assert context.stats.files_changed == 2
        assert context.branch_name == "feature/new-feature"
        assert context.breaking_changes is False
    
    def test_get_primary_language(self):
        """Test primary language detection."""
        files = [
            FileChange(path="main.py", change_type="modified", language="Python"),
            FileChange(path="utils.py", change_type="added", language="Python"),
            FileChange(path="script.js", change_type="modified", language="JavaScript")
        ]
        
        context = CommitContext(files=files)
        assert context.get_primary_language() == "Python"
    
    def test_get_affected_areas(self):
        """Test affected areas detection."""
        files = [
            FileChange(path="src/main.py", change_type="modified"),
            FileChange(path="src/utils.py", change_type="added"),
            FileChange(path="tests/test_main.py", change_type="added")
        ]
        
        context = CommitContext(files=files)
        areas = context.get_affected_areas()
        assert "src" in areas
        assert "tests" in areas


class TestCommitMessageConfig:
    """Test CommitMessageConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = CommitMessageConfig()
        
        assert config.style == MessageStyle.CONVENTIONAL
        assert config.max_subject_length == 72
        assert config.max_body_length == 100
        assert config.include_stats is False
        assert config.include_files is False
        assert config.use_emoji is False
    
    def test_conventional_templates(self):
        """Test conventional commit templates."""
        config = CommitMessageConfig(style=MessageStyle.CONVENTIONAL)
        
        assert CommitType.FEAT in config.templates
        assert CommitType.FIX in config.templates
        assert "{type}{scope}: {description}" in config.templates[CommitType.FEAT]
    
    def test_gitmoji_templates(self):
        """Test gitmoji templates."""
        config = CommitMessageConfig(style=MessageStyle.GITMOJI)
        
        assert CommitType.FEAT in config.templates
        assert "✨" in config.templates[CommitType.FEAT]
        assert "🐛" in config.templates[CommitType.FIX]


class TestDiffAnalyzer:
    """Test DiffAnalyzer functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.analyzer = DiffAnalyzer()
    
    def test_language_detection(self):
        """Test programming language detection."""
        assert self.analyzer.language_extensions['.py'] == 'Python'
        assert self.analyzer.language_extensions['.js'] == 'JavaScript'
        assert self.analyzer.language_extensions['.java'] == 'Java'
    
    def test_parse_simple_diff(self):
        """Test parsing a simple diff."""
        diff_text = """diff --git a/main.py b/main.py
index 1234567..abcdefg 100644
--- a/main.py
+++ b/main.py
@@ -1,3 +1,4 @@
 def main():
+    print("Hello, World!")
     pass
"""
        
        files = self.analyzer._parse_diff(diff_text)
        
        assert len(files) == 1
        assert files[0].path == "main.py"
        assert files[0].change_type == "modified"
        assert files[0].lines_added == 1
        assert files[0].lines_removed == 0
        assert files[0].language == "Python"
    
    def test_parse_new_file_diff(self):
        """Test parsing diff with new file."""
        diff_text = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,3 @@
+def hello():
+    print("Hello!")
+    return True
"""
        
        files = self.analyzer._parse_diff(diff_text)
        
        assert len(files) == 1
        assert files[0].path == "new_file.py"
        assert files[0].change_type == "added"
        assert files[0].lines_added == 3
        assert files[0].lines_removed == 0
    
    def test_parse_deleted_file_diff(self):
        """Test parsing diff with deleted file."""
        diff_text = """diff --git a/old_file.py b/old_file.py
deleted file mode 100644
index 1234567..0000000
--- a/old_file.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_function():
-    pass
-    return None
"""
        
        files = self.analyzer._parse_diff(diff_text)
        
        assert len(files) == 1
        assert files[0].path == "old_file.py"
        assert files[0].change_type == "deleted"
        assert files[0].lines_added == 0
        assert files[0].lines_removed == 3
    
    def test_analyze_diff_context(self):
        """Test complete diff analysis."""
        diff_text = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,7 @@
 def main():
+    # New feature implementation
+    feature_enabled = True
     print("Hello, World!")
-    old_code()
+    new_code()
     return 0
"""
        
        context = self.analyzer.analyze_diff(diff_text)
        
        assert len(context.files) == 1
        assert context.stats.files_changed == 1
        assert context.stats.lines_added == 3
        assert context.stats.lines_removed == 1
        assert context.scope == "src"
    
    def test_detect_breaking_changes(self):
        """Test breaking change detection."""
        diff_text = """diff --git a/api.py b/api.py
--- a/api.py
+++ b/api.py
@@ -1,3 +1,3 @@
-def old_function(param):
+def new_function(param, new_param):
     # BREAKING CHANGE: function signature changed
     pass
"""
        
        files = [FileChange(path="api.py", change_type="modified")]
        breaking = self.analyzer._detect_breaking_changes(files, diff_text)
        
        assert breaking is True
    
    def test_determine_scope_single_area(self):
        """Test scope determination for single area."""
        files = [
            FileChange(path="src/main.py", change_type="modified"),
            FileChange(path="src/utils.py", change_type="added")
        ]
        
        scope = self.analyzer._determine_scope(files)
        assert scope == "src"
    
    def test_determine_scope_multiple_areas(self):
        """Test scope determination for multiple areas."""
        files = [
            FileChange(path="src/main.py", change_type="modified"),
            FileChange(path="tests/test_main.py", change_type="added"),
            FileChange(path="docs/readme.md", change_type="modified")
        ]
        
        scope = self.analyzer._determine_scope(files)
        assert scope == "docs,src,tests"  # Sorted


class TestCommitMessageCache:
    """Test CommitMessageCache functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = CommitMessageCache(cache_dir=self.temp_dir, max_age_days=1)
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        diff_text = "sample diff"
        config = CommitMessageConfig()
        
        key1 = self.cache._get_cache_key(diff_text, config)
        key2 = self.cache._get_cache_key(diff_text, config)
        
        assert key1 == key2
        assert len(key1) == 16  # SHA256 truncated to 16 chars
    
    def test_cache_set_and_get(self):
        """Test caching and retrieval."""
        diff_text = "sample diff"
        config = CommitMessageConfig()
        message = "feat: add new feature"
        
        # Cache should be empty initially
        assert self.cache.get(diff_text, config) is None
        
        # Set cache
        self.cache.set(diff_text, config, message)
        
        # Should retrieve cached message
        cached = self.cache.get(diff_text, config)
        assert cached == message
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        diff_text = "sample diff"
        config = CommitMessageConfig()
        message = "feat: add new feature"
        
        # Create cache with very short expiration
        short_cache = CommitMessageCache(cache_dir=self.temp_dir, max_age_days=0)
        
        short_cache.set(diff_text, config, message)
        
        # Should be expired immediately
        cached = short_cache.get(diff_text, config)
        assert cached is None


class TestCommitMessageGenerator:
    """Test CommitMessageGenerator functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = CommitMessageConfig(style=MessageStyle.CONVENTIONAL)
        self.generator = CommitMessageGenerator(self.config, use_cache=False)
    
    def test_determine_commit_type_feat(self):
        """Test commit type determination for features."""
        context = CommitContext(
            files=[FileChange(path="src/new_feature.py", change_type="added")]
        )
        
        commit_type = self.generator._determine_commit_type(context)
        assert commit_type == CommitType.FEAT
    
    def test_determine_commit_type_docs(self):
        """Test commit type determination for documentation."""
        context = CommitContext(
            files=[FileChange(path="README.md", change_type="modified")]
        )
        
        commit_type = self.generator._determine_commit_type(context)
        assert commit_type == CommitType.DOCS
    
    def test_determine_commit_type_test(self):
        """Test commit type determination for tests."""
        context = CommitContext(
            files=[FileChange(path="tests/test_main.py", change_type="added")]
        )
        
        commit_type = self.generator._determine_commit_type(context)
        assert commit_type == CommitType.TEST
    
    def test_generate_description_single_file(self):
        """Test description generation for single file."""
        context = CommitContext(
            files=[FileChange(path="src/main.py", change_type="modified")]
        )
        
        description = self.generator._generate_description(context, CommitType.FIX)
        assert "main.py" in description
    
    def test_generate_description_multiple_files(self):
        """Test description generation for multiple files."""
        context = CommitContext(
            files=[
                FileChange(path="src/main.py", change_type="modified", language="Python"),
                FileChange(path="src/utils.py", change_type="added", language="Python")
            ]
        )
        
        description = self.generator._generate_description(context, CommitType.FEAT)
        assert "functionality" in description.lower()
    
    def test_format_conventional_message(self):
        """Test conventional commit message formatting."""
        context = CommitContext(
            scope="api",
            breaking_changes=False
        )
        
        message = self.generator._format_message(
            CommitType.FEAT, "add user authentication", context
        )
        
        assert message == "feat(api): add user authentication"
    
    def test_format_breaking_change_message(self):
        """Test breaking change message formatting."""
        context = CommitContext(
            scope="api",
            breaking_changes=True
        )
        
        message = self.generator._format_message(
            CommitType.FEAT, "change authentication method", context
        )
        
        assert message == "feat(api)!: change authentication method"
    
    def test_generate_full_message(self):
        """Test complete message generation."""
        diff_text = """diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,5 @@
+def authenticate(user, password):
+    # New authentication function
+    if validate_credentials(user, password):
+        return create_token(user)
+    return None
"""
        
        message = self.generator.generate(diff_text)
        
        assert message.startswith("feat")
        assert "auth.py" in message or "authentication" in message.lower()
    
    def test_suggest_multiple_messages(self):
        """Test generating multiple message suggestions."""
        diff_text = """diff --git a/main.py b/main.py
index 1234567..abcdefg 100644
--- a/main.py
+++ b/main.py
@@ -1,3 +1,4 @@
 def main():
+    print("Hello, World!")
     pass
"""
        
        suggestions = self.generator.suggest_messages(diff_text, count=3)
        
        assert len(suggestions) <= 3
        assert all(isinstance(msg, str) for msg in suggestions)
        assert all(len(msg) > 0 for msg in suggestions)
    
    def test_format_custom_message(self):
        """Test custom message formatting."""
        context = CommitContext(scope="api", breaking_changes=False)
        custom_message = "feat: add new feature"
        
        formatted = self.generator._format_custom_message(custom_message, context)
        
        assert formatted == "feat(api): add new feature"


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_generate_commit_message(self):
        """Test generate_commit_message utility function."""
        diff_text = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Project
+This is a test project.
 Description here.
"""
        
        message = generate_commit_message(diff_text)
        
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_suggest_commit_messages(self):
        """Test suggest_commit_messages utility function."""
        diff_text = """diff --git a/main.py b/main.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/main.py
@@ -0,0 +1,2 @@
+def main():
+    pass
"""
        
        suggestions = suggest_commit_messages(diff_text, count=2)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 2
        assert all(isinstance(msg, str) for msg in suggestions)
    
    def test_analyze_commit_diff(self):
        """Test analyze_commit_diff utility function."""
        diff_text = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 import unittest
+# New test case
 class TestCase(unittest.TestCase):
"""
        
        context = analyze_commit_diff(diff_text)
        
        assert isinstance(context, CommitContext)
        assert len(context.files) == 1
        assert context.files[0].path == "test.py"
    
    def test_validate_commit_message_valid(self):
        """Test commit message validation - valid message."""
        message = "feat(api): add user authentication"
        config = CommitMessageConfig(style=MessageStyle.CONVENTIONAL)
        
        is_valid, errors = validate_commit_message(message, config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_commit_message_invalid_format(self):
        """Test commit message validation - invalid format."""
        message = "Add user authentication"  # Not conventional format
        config = CommitMessageConfig(style=MessageStyle.CONVENTIONAL)
        
        is_valid, errors = validate_commit_message(message, config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "conventional commit format" in errors[0]
    
    def test_validate_commit_message_too_long(self):
        """Test commit message validation - too long."""
        message = "feat: " + "x" * 100  # Very long message
        config = CommitMessageConfig(max_subject_length=50)
        
        is_valid, errors = validate_commit_message(message, config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "too long" in errors[0]
    
    def test_validate_commit_message_missing_scope(self):
        """Test commit message validation - missing required scope."""
        message = "feat: add feature"  # No scope
        config = CommitMessageConfig(
            style=MessageStyle.CONVENTIONAL,
            require_scope=True
        )
        
        is_valid, errors = validate_commit_message(message, config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "scope" in errors[0].lower()


if __name__ == "__main__":
    pytest.main([__file__])