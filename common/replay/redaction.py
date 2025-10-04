"""
Redaction and Retention System for Record-Replay

Provides configurable redaction of sensitive data and retention policies
for recorded artifacts, following ADR-014 specifications for privacy
and artifact retention.
"""

import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RedactionLevel(Enum):
    """Redaction levels for different environments."""
    NONE = "none"           # No redaction (development only)
    BASIC = "basic"         # Basic secret patterns
    STANDARD = "standard"   # Standard production redaction
    STRICT = "strict"       # Maximum redaction for sensitive environments


class RetentionClass(Enum):
    """Retention classes for different artifact types."""
    DEVELOPMENT = "development"     # Short-term development artifacts
    CI = "ci"                      # CI/CD pipeline artifacts
    PRODUCTION = "production"      # Production debugging artifacts
    AUDIT = "audit"               # Long-term audit artifacts


@dataclass
class RedactionRule:
    """Rule for redacting sensitive data."""
    
    name: str
    pattern: Union[str, Pattern]
    replacement: str = "[REDACTED]"
    description: str = ""
    enabled: bool = True
    
    def __post_init__(self):
        """Compile pattern if it's a string."""
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)


@dataclass
class RetentionPolicy:
    """Policy for artifact retention."""
    
    retention_class: RetentionClass
    max_age_days: int
    max_size_mb: int
    auto_cleanup: bool = True
    compression_enabled: bool = True
    description: str = ""


class RedactionFilter:
    """Filters sensitive data from recorded artifacts."""
    
    def __init__(self, level: RedactionLevel = RedactionLevel.STANDARD):
        """
        Initialize redaction filter.
        
        Args:
            level: Redaction level to apply
        """
        self.level = level
        self.rules: List[RedactionRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default redaction rules based on level."""
        if self.level == RedactionLevel.NONE:
            return
        
        # Basic rules (all levels)
        basic_rules = [
            RedactionRule(
                name="github_token",
                pattern=r"gh[pousr]_[A-Za-z0-9_]{36,255}",
                description="GitHub personal access tokens"
            ),
            RedactionRule(
                name="gitlab_token",
                pattern=r"glpat-[A-Za-z0-9_-]{20,255}",
                description="GitLab personal access tokens"
            ),
            RedactionRule(
                name="api_key_header",
                pattern=r"(?i)(authorization|x-api-key|api-key):\s*['\"]?[A-Za-z0-9+/=_-]{20,}['\"]?",
                replacement=r"\1: [REDACTED]",
                description="API keys in headers"
            ),
            RedactionRule(
                name="bearer_token",
                pattern=r"(?i)bearer\s+[A-Za-z0-9+/=_-]{20,}",
                replacement="Bearer [REDACTED]",
                description="Bearer tokens"
            ),
            RedactionRule(
                name="basic_auth",
                pattern=r"(?i)basic\s+[A-Za-z0-9+/=]{20,}",
                replacement="Basic [REDACTED]",
                description="Basic authentication"
            ),
            RedactionRule(
                name="url_credentials",
                pattern=r"(https?://)([^:]+):([^@]+)@",
                replacement=r"\1[REDACTED]:[REDACTED]@",
                description="Credentials in URLs"
            ),
            RedactionRule(
                name="env_secrets",
                pattern=r"(?i)(password|secret|key|token)=['\"]?[A-Za-z0-9+/=_-]{8,}['\"]?",
                replacement=r"\1=[REDACTED]",
                description="Environment variable secrets"
            )
        ]
        
        self.rules.extend(basic_rules)
        
        if self.level in [RedactionLevel.STANDARD, RedactionLevel.STRICT]:
            # Standard rules
            standard_rules = [
                RedactionRule(
                    name="ssh_private_key",
                    pattern=r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
                    replacement="-----BEGIN PRIVATE KEY-----\n[REDACTED]\n-----END PRIVATE KEY-----",
                    description="SSH private keys"
                ),
                RedactionRule(
                    name="aws_access_key",
                    pattern=r"AKIA[0-9A-Z]{16}",
                    description="AWS access keys"
                ),
                RedactionRule(
                    name="aws_secret_key",
                    pattern=r"(?i)aws.{0,20}['\"][A-Za-z0-9+/]{40}['\"]",
                    replacement="aws_secret_access_key=\"[REDACTED]\"",
                    description="AWS secret keys"
                ),
                RedactionRule(
                    name="email_addresses",
                    pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                    replacement="[EMAIL_REDACTED]",
                    description="Email addresses"
                ),
                RedactionRule(
                    name="ip_addresses",
                    pattern=r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
                    replacement="[IP_REDACTED]",
                    description="IP addresses"
                )
            ]
            
            self.rules.extend(standard_rules)
        
        if self.level == RedactionLevel.STRICT:
            # Strict rules
            strict_rules = [
                RedactionRule(
                    name="file_paths",
                    pattern=r"(?i)(/[a-zA-Z0-9._/-]+|[a-zA-Z]:\\[a-zA-Z0-9._\\-]+)",
                    replacement="[PATH_REDACTED]",
                    description="File system paths"
                ),
                RedactionRule(
                    name="hostnames",
                    pattern=r"\b[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\b",
                    replacement="[HOSTNAME_REDACTED]",
                    description="Hostnames and domains"
                ),
                RedactionRule(
                    name="user_names",
                    pattern=r"(?i)(user|username|login)[:=]\s*['\"]?[a-zA-Z0-9._-]+['\"]?",
                    replacement=r"\1: [USER_REDACTED]",
                    description="Usernames"
                )
            ]
            
            self.rules.extend(strict_rules)
    
    def add_rule(self, rule: RedactionRule):
        """Add a custom redaction rule."""
        self.rules.append(rule)
    
    def remove_rule(self, name: str) -> bool:
        """Remove a redaction rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                del self.rules[i]
                return True
        return False
    
    def redact_text(self, text: str) -> str:
        """
        Redact sensitive data from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        if self.level == RedactionLevel.NONE:
            return text
        
        redacted_text = text
        
        for rule in self.rules:
            if rule.enabled:
                try:
                    redacted_text = rule.pattern.sub(rule.replacement, redacted_text)
                except Exception as e:
                    logger.warning(f"Error applying redaction rule '{rule.name}': {e}")
        
        return redacted_text
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive data from dictionary.
        
        Args:
            data: Dictionary to redact
            
        Returns:
            Redacted dictionary
        """
        if self.level == RedactionLevel.NONE:
            return data
        
        return self._redact_recursive(data)
    
    def _redact_recursive(self, obj: Any) -> Any:
        """Recursively redact data structures."""
        if isinstance(obj, dict):
            return {
                key: self._redact_recursive(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [self._redact_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self.redact_text(obj)
        else:
            return obj
    
    def redact_json(self, json_str: str) -> str:
        """
        Redact sensitive data from JSON string.
        
        Args:
            json_str: JSON string to redact
            
        Returns:
            Redacted JSON string
        """
        try:
            data = json.loads(json_str)
            redacted_data = self.redact_dict(data)
            return json.dumps(redacted_data, indent=2)
        except json.JSONDecodeError:
            # If not valid JSON, treat as plain text
            return self.redact_text(json_str)


class RetentionManager:
    """Manages artifact retention policies and cleanup."""
    
    def __init__(self):
        """Initialize retention manager."""
        self.policies: Dict[RetentionClass, RetentionPolicy] = {}
        self._setup_default_policies()
    
    def _setup_default_policies(self):
        """Setup default retention policies."""
        self.policies = {
            RetentionClass.DEVELOPMENT: RetentionPolicy(
                retention_class=RetentionClass.DEVELOPMENT,
                max_age_days=7,
                max_size_mb=100,
                auto_cleanup=True,
                compression_enabled=True,
                description="Short-term development artifacts"
            ),
            RetentionClass.CI: RetentionPolicy(
                retention_class=RetentionClass.CI,
                max_age_days=30,
                max_size_mb=500,
                auto_cleanup=True,
                compression_enabled=True,
                description="CI/CD pipeline artifacts"
            ),
            RetentionClass.PRODUCTION: RetentionPolicy(
                retention_class=RetentionClass.PRODUCTION,
                max_age_days=90,
                max_size_mb=1000,
                auto_cleanup=False,
                compression_enabled=True,
                description="Production debugging artifacts"
            ),
            RetentionClass.AUDIT: RetentionPolicy(
                retention_class=RetentionClass.AUDIT,
                max_age_days=365,
                max_size_mb=5000,
                auto_cleanup=False,
                compression_enabled=True,
                description="Long-term audit artifacts"
            )
        }
    
    def set_policy(self, policy: RetentionPolicy):
        """Set retention policy for a class."""
        self.policies[policy.retention_class] = policy
    
    def get_policy(self, retention_class: RetentionClass) -> Optional[RetentionPolicy]:
        """Get retention policy for a class."""
        return self.policies.get(retention_class)
    
    def should_retain(self, 
                     file_path: Path,
                     retention_class: RetentionClass) -> bool:
        """
        Check if a file should be retained based on policy.
        
        Args:
            file_path: Path to the file
            retention_class: Retention class to check against
            
        Returns:
            True if file should be retained
        """
        policy = self.get_policy(retention_class)
        if not policy:
            return True  # Default to retain if no policy
        
        if not file_path.exists():
            return False
        
        # Check age
        file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_age.days > policy.max_age_days:
            return False
        
        # Check size (in MB)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > policy.max_size_mb:
            return False
        
        return True
    
    def cleanup_directory(self, 
                         directory: Path,
                         retention_class: RetentionClass,
                         dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up directory based on retention policy.
        
        Args:
            directory: Directory to clean up
            retention_class: Retention class to apply
            dry_run: If True, don't actually delete files
            
        Returns:
            Cleanup statistics
        """
        policy = self.get_policy(retention_class)
        if not policy or not policy.auto_cleanup:
            return {"cleaned": 0, "retained": 0, "errors": []}
        
        if not directory.exists():
            return {"cleaned": 0, "retained": 0, "errors": ["Directory does not exist"]}
        
        stats = {"cleaned": 0, "retained": 0, "errors": []}
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    if self.should_retain(file_path, retention_class):
                        stats["retained"] += 1
                    else:
                        if not dry_run:
                            file_path.unlink()
                        stats["cleaned"] += 1
                        logger.info(f"{'Would delete' if dry_run else 'Deleted'} {file_path}")
                except Exception as e:
                    stats["errors"].append(f"Error processing {file_path}: {e}")
                    logger.error(f"Error processing {file_path}: {e}")
        
        return stats


# Global instances
_global_redaction_filter = RedactionFilter()
_global_retention_manager = RetentionManager()


def get_redaction_filter() -> RedactionFilter:
    """Get the global redaction filter."""
    return _global_redaction_filter


def get_retention_manager() -> RetentionManager:
    """Get the global retention manager."""
    return _global_retention_manager


def set_redaction_level(level: RedactionLevel):
    """Set global redaction level."""
    global _global_redaction_filter
    _global_redaction_filter = RedactionFilter(level)


def redact_text(text: str) -> str:
    """Redact text using global filter."""
    return _global_redaction_filter.redact_text(text)


def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact dictionary using global filter."""
    return _global_redaction_filter.redact_dict(data)


def redact_json(json_str: str) -> str:
    """Redact JSON string using global filter."""
    return _global_redaction_filter.redact_json(json_str)