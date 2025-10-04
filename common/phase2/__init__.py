"""
Phase 2: AI-Powered Mismatch Resolution

This package contains the core data models, enums, and utilities for Phase 2
AI-powered mismatch resolution functionality.
"""

__version__ = "1.0.0"
__author__ = "AI Dev Squad Platform Team"

# Import core enums and models for easy access
from .enums import (
    MismatchType,
    MismatchStatus,
    ResolutionStatus,
    SafetyLevel,
    ResolutionActionType,
    EquivalenceMethod,
    ArtifactType,
)

from .models import (
    Mismatch,
    ResolutionPlan,
    ResolutionAction,
    EquivalenceCriterion,
    MismatchPattern,
)

__all__ = [
    # Enums
    "MismatchType",
    "MismatchStatus", 
    "ResolutionStatus",
    "SafetyLevel",
    "ResolutionActionType",
    "EquivalenceMethod",
    "ArtifactType",
    # Models
    "Mismatch",
    "ResolutionPlan",
    "ResolutionAction",
    "EquivalenceCriterion",
    "MismatchPattern",
]