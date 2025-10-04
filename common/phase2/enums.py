"""
Phase 2 Core Enumerations

This module defines all enums used throughout Phase 2 AI-powered mismatch resolution.
These enums are the single source of truth and must match the database schema exactly.

All downstream modules should import from this module to ensure consistency.
"""

from enum import Enum
from typing import Set


class MismatchType(Enum):
    """
    Types of replay mismatches that can be detected and analyzed.
    
    These values must match the database enum 'mismatch_type' exactly.
    """
    WHITESPACE = "whitespace"
    MARKDOWN_FORMATTING = "markdown_formatting"
    JSON_ORDERING = "json_ordering"
    NUMERIC_EPSILON = "numeric_epsilon"
    NONDETERMINISM = "nondeterminism"
    SEMANTICS_TEXT = "semantics_text"
    SEMANTICS_CODE = "semantics_code"
    POLICY_VIOLATION = "policy_violation"
    INFRA_ENV_DRIFT = "infra_env_drift"

    @classmethod
    def safe_for_auto_resolve(cls) -> Set['MismatchType']:
        """Return mismatch types that are safe for automatic resolution."""
        return {cls.WHITESPACE, cls.JSON_ORDERING}
    
    @classmethod
    def requires_human_review(cls) -> Set['MismatchType']:
        """Return mismatch types that require human review."""
        return {
            cls.SEMANTICS_TEXT,
            cls.SEMANTICS_CODE,
            cls.POLICY_VIOLATION,
        }
    
    @classmethod
    def analysis_only(cls) -> Set['MismatchType']:
        """Return mismatch types that are analysis-only (no auto-resolution)."""
        return {
            cls.NONDETERMINISM,
            cls.POLICY_VIOLATION,
            cls.INFRA_ENV_DRIFT,
        }


class MismatchStatus(Enum):
    """
    Status of a mismatch throughout its lifecycle.
    
    These values are used in the database 'mismatch.status' field.
    """
    DETECTED = "detected"
    ANALYZING = "analyzing"
    RESOLVED = "resolved"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    INCONCLUSIVE = "inconclusive"


class ResolutionStatus(Enum):
    """
    Status of a resolution plan throughout its lifecycle.
    
    These values must match the database enum 'resolution_status' exactly.
    """
    PROPOSED = "proposed"
    APPROVED = "approved"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"
    ERROR = "error"


class SafetyLevel(Enum):
    """
    Safety levels for resolution operations.
    
    These values must match the database enum 'safety_level' exactly.
    """
    EXPERIMENTAL = "experimental"  # Requires explicit approval
    ADVISORY = "advisory"          # Shows preview, asks for approval
    AUTOMATIC = "automatic"        # Applies automatically if confidence high

    def requires_approval(self) -> bool:
        """Return True if this safety level requires human approval."""
        return self in {self.EXPERIMENTAL, self.ADVISORY}
    
    def allows_auto_apply(self) -> bool:
        """Return True if this safety level allows automatic application."""
        return self == self.AUTOMATIC


class ResolutionActionType(Enum):
    """
    Types of resolution actions that can be performed.
    """
    REPLACE_ARTIFACT = "replace_artifact"
    UPDATE_METADATA = "update_metadata"
    APPLY_TRANSFORM = "apply_transform"
    IGNORE_MISMATCH = "ignore_mismatch"
    CANONICALIZE_JSON = "canonicalize_json"
    NORMALIZE_WHITESPACE = "normalize_whitespace"
    REWRITE_FORMATTING = "rewrite_formatting"

    def is_destructive(self) -> bool:
        """Return True if this action type is considered destructive."""
        return self in {
            self.REPLACE_ARTIFACT,
            self.APPLY_TRANSFORM,
            self.REWRITE_FORMATTING,
        }


class EquivalenceMethod(Enum):
    """
    Methods for determining semantic equivalence between artifacts.
    """
    EXACT = "exact"
    COSINE_SIMILARITY = "cosine_similarity"
    LLM_RUBRIC_JUDGE = "llm_rubric_judge"
    AST_NORMALIZED = "ast_normalized"
    CANONICAL_JSON = "canonical_json"
    TEST_EXECUTION = "test_execution"

    def requires_ai(self) -> bool:
        """Return True if this method requires AI services."""
        return self in {
            self.COSINE_SIMILARITY,
            self.LLM_RUBRIC_JUDGE,
        }


class ArtifactType(Enum):
    """
    Types of artifacts that can be analyzed for mismatches.
    """
    TEXT = "text"
    JSON = "json"
    CODE = "code"
    BINARY = "binary"

    def default_equivalence_methods(self) -> Set[EquivalenceMethod]:
        """Return default equivalence methods for this artifact type."""
        if self == self.TEXT:
            return {
                EquivalenceMethod.EXACT,
                EquivalenceMethod.COSINE_SIMILARITY,
                EquivalenceMethod.LLM_RUBRIC_JUDGE,
            }
        elif self == self.JSON:
            return {
                EquivalenceMethod.EXACT,
                EquivalenceMethod.CANONICAL_JSON,
            }
        elif self == self.CODE:
            return {
                EquivalenceMethod.EXACT,
                EquivalenceMethod.AST_NORMALIZED,
                EquivalenceMethod.TEST_EXECUTION,
            }
        else:  # BINARY
            return {EquivalenceMethod.EXACT}


class Environment(Enum):
    """
    Deployment environments with different safety policies.
    """
    DEVELOPMENT = "dev"
    STAGING = "stage"
    PRODUCTION = "prod"

    def allows_experimental(self) -> bool:
        """Return True if this environment allows experimental features."""
        return self in {self.DEVELOPMENT, self.STAGING}
    
    def requires_dual_key(self) -> bool:
        """Return True if this environment requires dual-key approval."""
        return self == self.PRODUCTION


class ConfidenceLevel(Enum):
    """
    Confidence levels for AI decisions and analysis.
    """
    VERY_LOW = "very_low"      # 0.0 - 0.2
    LOW = "low"                # 0.2 - 0.4
    MEDIUM = "medium"          # 0.4 - 0.6
    HIGH = "high"              # 0.6 - 0.8
    VERY_HIGH = "very_high"    # 0.8 - 1.0

    @classmethod
    def from_score(cls, score: float) -> 'ConfidenceLevel':
        """Convert a numeric confidence score to a confidence level."""
        if score < 0.2:
            return cls.VERY_LOW
        elif score < 0.4:
            return cls.LOW
        elif score < 0.6:
            return cls.MEDIUM
        elif score < 0.8:
            return cls.HIGH
        else:
            return cls.VERY_HIGH
    
    def min_score(self) -> float:
        """Return the minimum score for this confidence level."""
        return {
            self.VERY_LOW: 0.0,
            self.LOW: 0.2,
            self.MEDIUM: 0.4,
            self.HIGH: 0.6,
            self.VERY_HIGH: 0.8,
        }[self]


class LearningMode(Enum):
    """
    Modes for the learning system behavior.
    """
    DISABLED = "disabled"      # No learning
    PASSIVE = "passive"        # Learn but don't apply
    ACTIVE = "active"          # Learn and apply improvements
    AGGRESSIVE = "aggressive"  # Learn aggressively with lower thresholds


class CircuitBreakerState(Enum):
    """
    States for circuit breaker functionality.
    """
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Circuit breaker triggered, blocking operations
    HALF_OPEN = "half_open"    # Testing if service has recovered


# Validation functions to ensure enum consistency
def validate_enum_consistency():
    """
    Validate that enums are consistent with database schema and policies.
    
    This function should be called during startup to catch configuration errors.
    """
    # Validate that all mismatch types have corresponding policy rules
    # This will be implemented when policy loading is added
    
    # Validate that safety levels are properly ordered
    safety_order = [SafetyLevel.AUTOMATIC, SafetyLevel.ADVISORY, SafetyLevel.EXPERIMENTAL]
    assert len(safety_order) == len(SafetyLevel), "Missing safety levels in validation"
    
    # Validate that confidence levels cover the full range
    levels = list(ConfidenceLevel)
    assert len(levels) == 5, "Expected 5 confidence levels"
    
    # Validate artifact type coverage
    artifact_types = set(ArtifactType)
    expected_types = {ArtifactType.TEXT, ArtifactType.JSON, ArtifactType.CODE, ArtifactType.BINARY}
    assert artifact_types == expected_types, "Artifact types don't match expected set"


# Export all enums for easy importing
__all__ = [
    "MismatchType",
    "MismatchStatus",
    "ResolutionStatus", 
    "SafetyLevel",
    "ResolutionActionType",
    "EquivalenceMethod",
    "ArtifactType",
    "Environment",
    "ConfidenceLevel",
    "LearningMode",
    "CircuitBreakerState",
    "validate_enum_consistency",
]