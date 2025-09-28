#!/usr/bin/env python3
"""
Commit Message Generator Demonstration

This example demonstrates the commit message generation functionality, including:
1. Diff analysis and context extraction
2. Automatic commit message generation
3. Multiple message style support (conventional, gitmoji, etc.)
4. Custom templates and configuration
5. Caching for performance
6. Integration with VCS providers
7. Message validation and suggestions
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.vcs.commit_msgs import (
    CommitMessageGenerator, CommitMessageConfig, CommitContext, DiffAnalyzer,
    CommitType, MessageStyle, FileChange, DiffStats, CommitMessageCache,
    generate_commit_message, suggest_commit_messages, analyze_commit_diff,
    validate_commit_message
)


def demonstrate_diff_analysis():
    """Demonstrate diff analysis capabilities."""
    print("=== Diff Analysis ===")
    
    # Sample diff for a new feature
    feature_diff = """diff --git a/src/auth/login.py b/src/auth/login.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth/login.py
@@ -0,0 +1,25 @@
+"""
+User authentication module.
+"""
+
+import hashlib
+from typing import Optional
+
+class LoginManager:
+    def __init__(self, user_db):
+        self.user_db = user_db
+    
+    def authenticate(self, username: str, password: str) -> Optional[str]:
+        \"\"\"Authenticate user and return token if successful.\"\"\"
+        user = self.user_db.get_user(username)
+        if user and self._verify_password(password, user.password_hash):
+            return self._generate_token(user)
+        return None
+    
+    def _verify_password(self, password: str, hash: str) -> bool:
+        \"\"\"Verify password against stored hash.\"\"\"
+        return hashlib.sha256(password.encode()).hexdigest() == hash
+    
+    def _generate_token(self, user) -> str:
+        \"\"\"Generate authentication token for user.\"\"\"
+        return f"token_{user.id}_{datetime.now().timestamp()}"
diff --git a/tests/test_auth.py b/tests/test_auth.py
new file mode 100644
index 0000000..abcdefg
--- /dev/null
+++ b/tests/test_auth.py
@@ -0,0 +1,15 @@
+import unittest
+from src.auth.login import LoginManager
+
+class TestLoginManager(unittest.TestCase):
+    def setUp(self):
+        self.login_manager = LoginManager(mock_user_db)
+    
+    def test_successful_authentication(self):
+        token = self.login_manager.authenticate("user", "password")
+        self.assertIsNotNone(token)
+    
+    def test_failed_authentication(self):
+        token = self.login_manager.authenticate("user", "wrong_password")
+        self.assertIsNone(token)
+"""
    
    analyzer = DiffAnalyzer()
    context = analyzer.analyze_diff(feature_diff)
    
    print(f"Files changed: {len(context.files)}")
    for file_change in context.files:
        print(f"  - {file_change.path} ({file_change.change_type})")
        print(f"    Language: {file_change.language}")
        print(f"    Lines: +{file_change.lines_added}/-{file_change.lines_removed}")
    
    print(f"\nStatistics:")
    print(f"  Total files: {context.stats.files_changed}")
    print(f"  Lines added: {context.stats.lines_added}")
    print(f"  Lines removed: {context.stats.lines_removed}")
    print(f"  Net change: {context.stats.net_changes}")
    
    print(f"\nContext:")
    print(f"  Primary language: {context.get_primary_language()}")
    print(f"  Affected areas: {context.get_affected_areas()}")
    print(f"  Scope: {context.scope}")
    print(f"  Breaking changes: {context.breaking_changes}")
    
    return context


def demonstrate_message_styles():
    """Demonstrate different commit message styles."""
    print("\n=== Message Styles ===")
    
    # Sample diff for demonstration
    sample_diff = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,6 @@
 # My Project
 
+## Features
+- User authentication
+- Data processing
+
 This is a sample project.
"""
    
    styles = [
        (MessageStyle.CONVENTIONAL, "Conventional Commits"),
        (MessageStyle.GITMOJI, "Gitmoji Style"),
        (MessageStyle.SIMPLE, "Simple Style"),
        (MessageStyle.DETAILED, "Detailed Style")
    ]
    
    for style, description in styles:
        print(f"\n{description}:")
        config = CommitMessageConfig(style=style)
        generator = CommitMessageGenerator(config, use_cache=False)
        
        message = generator.generate(sample_diff)
        print(f"  {message}")


def demonstrate_custom_configuration():
    """Demonstrate custom configuration options."""
    print("\n=== Custom Configuration ===")
    
    # Create custom configuration
    config = CommitMessageConfig(
        style=MessageStyle.CONVENTIONAL,
        max_subject_length=50,  # Shorter than default
        include_stats=True,
        include_files=True,
        require_scope=True,
        use_emoji=False
    )
    
    # Custom templates
    config.templates[CommitType.FEAT] = "✨ {type}{scope}: {description}"
    config.templates[CommitType.FIX] = "🐛 {type}{scope}: {description}"
    
    print(f"Configuration:")
    print(f"  Style: {config.style.value}")
    print(f"  Max subject length: {config.max_subject_length}")
    print(f"  Include stats: {config.include_stats}")
    print(f"  Include files: {config.include_files}")
    print(f"  Require scope: {config.require_scope}")
    
    # Generate message with custom config
    sample_diff = """diff --git a/src/api/users.py b/src/api/users.py
index 1234567..abcdefg 100644
--- a/src/api/users.py
+++ b/src/api/users.py
@@ -10,6 +10,8 @@ class UserAPI:
     def get_user(self, user_id: int):
+        if not user_id:
+            raise ValueError("User ID is required")
         return self.db.get_user(user_id)
"""
    
    generator = CommitMessageGenerator(config, use_cache=False)
    message = generator.generate(sample_diff)
    
    print(f"\nGenerated message:")
    print(f"  {message}")


def demonstrate_commit_type_detection():
    """Demonstrate automatic commit type detection."""
    print("\n=== Commit Type Detection ===")
    
    test_cases = [
        ("New feature", """diff --git a/src/features/notifications.py b/src/features/notifications.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/features/notifications.py
@@ -0,0 +1,10 @@
+class NotificationService:
+    def send_notification(self, user, message):
+        pass
"""),
        ("Bug fix", """diff --git a/src/utils/validator.py b/src/utils/validator.py
index 1234567..abcdefg 100644
--- a/src/utils/validator.py
+++ b/src/utils/validator.py
@@ -5,7 +5,7 @@ def validate_email(email):
     if not email:
-        return True  # Bug: should return False
+        return False
     return "@" in email
"""),
        ("Documentation", """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,8 @@
 # Project
+
+## Installation
+
+```bash
+pip install -r requirements.txt
+```
+
 Description
"""),
        ("Tests", """diff --git a/tests/test_validator.py b/tests/test_validator.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/tests/test_validator.py
@@ -0,0 +1,8 @@
+import unittest
+from src.utils.validator import validate_email
+
+class TestValidator(unittest.TestCase):
+    def test_validate_email(self):
+        self.assertTrue(validate_email("test@example.com"))
+        self.assertFalse(validate_email("invalid"))
"""),
        ("CI/CD", """diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/.github/workflows/ci.yml
@@ -0,0 +1,15 @@
+name: CI
+on: [push, pull_request]
+jobs:
+  test:
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v2
+      - name: Run tests
+        run: pytest
""")
    ]
    
    generator = CommitMessageGenerator(use_cache=False)
    
    for description, diff in test_cases:
        context = generator.analyzer.analyze_diff(diff)
        commit_type = generator._determine_commit_type(context)
        message = generator.generate(diff)
        
        print(f"\n{description}:")
        print(f"  Detected type: {commit_type.value}")
        print(f"  Generated message: {message}")


def demonstrate_message_suggestions():
    """Demonstrate multiple message suggestions."""
    print("\n=== Message Suggestions ===")
    
    sample_diff = """diff --git a/src/database/models.py b/src/database/models.py
index 1234567..abcdefg 100644
--- a/src/database/models.py
+++ b/src/database/models.py
@@ -15,6 +15,12 @@ class User(Model):
     email = CharField(unique=True)
     created_at = DateTimeField(auto_now_add=True)
     
+    def get_full_name(self):
+        return f"{self.first_name} {self.last_name}"
+    
+    def is_active(self):
+        return self.status == 'active'
+    
     class Meta:
         table_name = 'users'
diff --git a/tests/test_models.py b/tests/test_models.py
index abcdefg..1234567 100644
--- a/tests/test_models.py
+++ b/tests/test_models.py
@@ -8,4 +8,8 @@ class TestUser(unittest.TestCase):
     def test_user_creation(self):
         user = User(name="Test", email="test@example.com")
         self.assertEqual(user.name, "Test")
+    
+    def test_get_full_name(self):
+        user = User(first_name="John", last_name="Doe")
+        self.assertEqual(user.get_full_name(), "John Doe")
"""
    
    suggestions = suggest_commit_messages(sample_diff, count=5)
    
    print(f"Generated {len(suggestions)} suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")


def demonstrate_message_validation():
    """Demonstrate commit message validation."""
    print("\n=== Message Validation ===")
    
    config = CommitMessageConfig(
        style=MessageStyle.CONVENTIONAL,
        max_subject_length=50,
        require_scope=True,
        require_issue_reference=False
    )
    
    test_messages = [
        "feat(auth): add user login",  # Valid
        "Add user login functionality",  # Invalid: not conventional
        "feat: " + "x" * 60,  # Invalid: too long
        "feat: add login",  # Invalid: missing scope
        "fix(api): resolve authentication bug #123",  # Valid with issue
    ]
    
    print(f"Validation rules:")
    print(f"  Style: {config.style.value}")
    print(f"  Max length: {config.max_subject_length}")
    print(f"  Require scope: {config.require_scope}")
    
    for message in test_messages:
        is_valid, errors = validate_commit_message(message, config)
        status = "✅" if is_valid else "❌"
        
        print(f"\n{status} \"{message}\"")
        if errors:
            for error in errors:
                print(f"    - {error}")


def demonstrate_caching():
    """Demonstrate commit message caching."""
    print("\n=== Caching Demonstration ===")
    
    import tempfile
    import time
    
    # Create temporary cache directory
    cache_dir = Path(tempfile.mkdtemp())
    print(f"Cache directory: {cache_dir}")
    
    # Create generator with caching enabled
    config = CommitMessageConfig()
    generator = CommitMessageGenerator(config, use_cache=True)
    generator.cache.cache_dir = cache_dir
    
    sample_diff = """diff --git a/example.py b/example.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/example.py
@@ -0,0 +1,3 @@
+def example():
+    print("Hello, World!")
+    return True
"""
    
    # First generation (should be slow)
    print("First generation (no cache)...")
    start_time = time.time()
    message1 = generator.generate(sample_diff)
    time1 = time.time() - start_time
    print(f"  Message: {message1}")
    print(f"  Time: {time1:.4f}s")
    
    # Second generation (should use cache)
    print("\nSecond generation (with cache)...")
    start_time = time.time()
    message2 = generator.generate(sample_diff)
    time2 = time.time() - start_time
    print(f"  Message: {message2}")
    print(f"  Time: {time2:.4f}s")
    
    print(f"\nCache performance:")
    print(f"  Messages match: {message1 == message2}")
    print(f"  Speed improvement: {time1/time2:.1f}x faster" if time2 > 0 else "  Instant cache hit")
    
    # Check cache files
    cache_files = list(cache_dir.glob("*.json"))
    print(f"  Cache files created: {len(cache_files)}")


def demonstrate_integration_with_vcs():
    """Demonstrate integration with VCS providers."""
    print("\n=== VCS Integration ===")
    
    # This would typically be used with actual VCS providers
    print("Example integration with GitHub/GitLab providers:")
    
    # Simulate getting a diff from VCS
    simulated_diff = """diff --git a/src/api/endpoints.py b/src/api/endpoints.py
index 1234567..abcdefg 100644
--- a/src/api/endpoints.py
+++ b/src/api/endpoints.py
@@ -20,6 +20,10 @@ def get_users():
     return jsonify(users)

+@app.route('/users/<int:user_id>')
+def get_user(user_id):
+    user = User.get_by_id(user_id)
+    return jsonify(user.to_dict()) if user else abort(404)
+
 @app.route('/users', methods=['POST'])
 def create_user():
"""
    
    # Generate commit message
    config = CommitMessageConfig(
        style=MessageStyle.CONVENTIONAL,
        include_stats=False
    )
    
    message = generate_commit_message(simulated_diff, config)
    
    print(f"Generated commit message: {message}")
    print(f"\nThis message could be used with VCS providers like:")
    print(f"  await github.commit_changes(owner, repo, branch, '{message}', files)")
    print(f"  await gitlab.commit_changes(owner, project, branch, '{message}', files)")
    
    # Show how to customize for different scenarios
    print(f"\nCustomization examples:")
    
    # For AI-generated commits
    ai_config = CommitMessageConfig(style=MessageStyle.CONVENTIONAL)
    ai_message = f"[AI] {message}"
    print(f"  AI commit: {ai_message}")
    
    # For automated commits
    auto_config = CommitMessageConfig(style=MessageStyle.SIMPLE)
    auto_generator = CommitMessageGenerator(auto_config, use_cache=False)
    auto_message = auto_generator.generate(simulated_diff)
    print(f"  Automated: {auto_message}")


def demonstrate_advanced_features():
    """Demonstrate advanced features."""
    print("\n=== Advanced Features ===")
    
    # Breaking change detection
    breaking_diff = """diff --git a/src/api/auth.py b/src/api/auth.py
index 1234567..abcdefg 100644
--- a/src/api/auth.py
+++ b/src/api/auth.py
@@ -5,8 +5,10 @@ class AuthService:
-    def authenticate(self, username, password):
+    def authenticate(self, credentials):
         # BREAKING CHANGE: authentication method signature changed
+        username = credentials.get('username')
+        password = credentials.get('password')
         return self._verify_credentials(username, password)
"""
    
    context = analyze_commit_diff(breaking_diff)
    print(f"Breaking change detected: {context.breaking_changes}")
    
    config = CommitMessageConfig(breaking_change_prefix="!")
    generator = CommitMessageGenerator(config, use_cache=False)
    message = generator.generate(breaking_diff)
    print(f"Breaking change message: {message}")
    
    # Scope detection
    multi_area_diff = """diff --git a/frontend/src/components/Login.js b/frontend/src/components/Login.js
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/frontend/src/components/Login.js
@@ -0,0 +1,5 @@
+export function Login() {
+  return <div>Login Form</div>;
+}
diff --git a/backend/auth/views.py b/backend/auth/views.py
index abcdefg..1234567 100644
--- a/backend/auth/views.py
+++ b/backend/auth/views.py
@@ -1,3 +1,6 @@
+def login_view(request):
+    return JsonResponse({'status': 'ok'})
+
 def logout_view(request):
     pass
"""
    
    multi_context = analyze_commit_diff(multi_area_diff)
    print(f"\nMulti-area changes:")
    print(f"  Affected areas: {multi_context.get_affected_areas()}")
    print(f"  Detected scope: {multi_context.scope}")
    
    multi_message = generator.generate(multi_area_diff)
    print(f"  Generated message: {multi_message}")


def main():
    """Run all demonstrations."""
    print("Commit Message Generator Demonstration")
    print("=" * 50)
    
    try:
        demonstrate_diff_analysis()
        demonstrate_message_styles()
        demonstrate_custom_configuration()
        demonstrate_commit_type_detection()
        demonstrate_message_suggestions()
        demonstrate_message_validation()
        demonstrate_caching()
        demonstrate_integration_with_vcs()
        demonstrate_advanced_features()
        
        print("\n" + "=" * 50)
        print("✅ Commit message generator demonstration completed!")
        print("\nKey features demonstrated:")
        print("  - Intelligent diff analysis and context extraction")
        print("  - Multiple commit message styles (conventional, gitmoji, etc.)")
        print("  - Automatic commit type detection")
        print("  - Custom templates and configuration")
        print("  - Message validation and suggestions")
        print("  - Performance caching")
        print("  - Breaking change detection")
        print("  - Multi-area scope detection")
        print("  - VCS provider integration")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())