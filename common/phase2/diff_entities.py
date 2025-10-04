"""Phase 2 Diff and Evaluation Entities

This module defines the core entities for representing differences between
artifacts and their evaluations. These form the evidence substrate for
mismatch analysis.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from .enums import ArtifactType, EquivalenceMethod, ConfidenceLevel


class DiffType(Enum):
    """Types of differences that can be detected."""
    TEXTUAL = "textual"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    FORMATTING = "formatting"
    ORDERING = "ordering"
    NUMERIC = "numeric"
    TEMPORAL = "temporal"


class DiffOperation(Enum):
    """Types of diff operations."""
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    MOVE = "move"
    COPY = "copy"


class DiffHunk(BaseModel):
    """A single diff hunk representing a localized change."""
    
    operation: DiffOperation = Field(..., description="Type of operation")
    source_start: int = Field(..., ge=0, description="Start position in source")
    source_length: int = Field(..., ge=0, description="Length in source")
    target_start: int = Field(..., ge=0, description="Start position in target")
    target_length: int = Field(..., ge=0, description="Length in target")
    source_content: str = Field("", description="Content from source")
    target_content: str = Field("", description="Content from target")
    context_before: str = Field("", description="Context before the change")
    context_after: str = Field("", description="Context after the change")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in this hunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Diff(BaseModel):
    """Represents a difference between two artifacts."""
    model_config = {"extra": "forbid"}
    
    id: str = Field(default_factory=lambda: f"diff_{uuid4().hex[:8]}", description="Unique diff ID")
    source_artifact_id: str = Field(..., description="Source artifact identifier")
    target_artifact_id: str = Field(..., description="Target artifact identifier")
    diff_type: DiffType = Field(..., description="Type of difference")
    artifact_type: ArtifactType = Field(..., description="Type of artifacts being compared")
    hunks: List[DiffHunk] = Field(default_factory=list, description="Individual diff hunks")
    summary: str = Field("", description="Human-readable summary of differences")
    similarity_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall similarity score")
    total_changes: int = Field(0, ge=0, description="Total number of changes")
    lines_added: int = Field(0, ge=0, description="Lines added")
    lines_removed: int = Field(0, ge=0, description="Lines removed")
    lines_modified: int = Field(0, ge=0, description="Lines modified")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        if not v.startswith('diff_') or len(v) != 13:
            raise ValueError('Diff ID must be format diff_XXXXXXXX')
        return v
    
    def get_signature(self) -> str:
        """Generate a signature for this diff for caching/deduplication."""
        signature_data = {
            'source_artifact_id': self.source_artifact_id,
            'target_artifact_id': self.target_artifact_id,
            'diff_type': self.diff_type.value,
            'artifact_type': self.artifact_type.value,
            'total_changes': self.total_changes,
            'similarity_score': round(self.similarity_score, 3)
        }
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.sha256(signature_str.encode()).hexdigest()[:16]
    
    def is_significant(self, threshold: float = 0.1) -> bool:
        """Check if this diff represents a significant change."""
        return self.similarity_score < (1.0 - threshold) or self.total_changes > 0
    
    def get_change_density(self) -> float:
        """Calculate the density of changes (changes per hunk)."""
        if not self.hunks:
            return 0.0
        return self.total_changes / len(self.hunks)


class EvaluationStatus(Enum):
    """Status of an evaluation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationResult(BaseModel):
    """Result of a single evaluation method."""
    
    method: EquivalenceMethod = Field(..., description="Evaluation method used")
    equivalent: bool = Field(..., description="Whether artifacts are equivalent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in result")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    reasoning: str = Field("", description="Explanation of the result")
    cost: float = Field(0.0, ge=0.0, description="Cost of evaluation in USD")
    latency_ms: int = Field(0, ge=0, description="Evaluation duration in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Method-specific metadata")
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """Get confidence level enum from numeric score."""
        return ConfidenceLevel.from_score(self.confidence)


class Evaluation(BaseModel):
    """Comprehensive evaluation of artifact equivalence."""
    model_config = {"extra": "forbid"}
    
    id: str = Field(default_factory=lambda: f"eval_{uuid4().hex[:8]}", description="Unique evaluation ID")
    diff_id: str = Field(..., description="Associated diff ID")
    source_artifact_id: str = Field(..., description="Source artifact identifier")
    target_artifact_id: str = Field(..., description="Target artifact identifier")
    artifact_type: ArtifactType = Field(..., description="Type of artifacts")
    status: EvaluationStatus = Field(default=EvaluationStatus.PENDING, description="Evaluation status")
    results: List[EvaluationResult] = Field(default_factory=list, description="Individual method results")
    consensus_result: Optional[bool] = Field(None, description="Consensus equivalence result")
    consensus_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in consensus")
    total_cost: float = Field(0.0, ge=0.0, description="Total evaluation cost")
    total_latency_ms: int = Field(0, ge=0, description="Total evaluation time")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        if not v.startswith('eval_') or len(v) != 13:
            raise ValueError('Evaluation ID must be format eval_XXXXXXXX')
        return v
    
    def add_result(self, result: EvaluationResult) -> 'Evaluation':
        """Add an evaluation result and update totals."""
        self.results.append(result)
        self.total_cost += result.cost
        self.total_latency_ms += result.latency_ms
        self._update_consensus()
        return self
    
    def _update_consensus(self):
        """Update consensus result based on all results."""
        if not self.results:
            self.consensus_result = None
            self.consensus_confidence = 0.0
            return
        
        # Simple majority voting with confidence weighting
        equivalent_votes = []
        total_weight = 0.0
        
        for result in self.results:
            weight = result.confidence
            equivalent_votes.append((result.equivalent, weight))
            total_weight += weight
        
        if total_weight == 0:
            self.consensus_result = None
            self.consensus_confidence = 0.0
            return
        
        # Calculate weighted consensus
        equivalent_weight = sum(weight for equiv, weight in equivalent_votes if equiv)
        equivalent_ratio = equivalent_weight / total_weight
        
        self.consensus_result = equivalent_ratio > 0.5
        self.consensus_confidence = max(equivalent_ratio, 1.0 - equivalent_ratio)
    
    def is_complete(self) -> bool:
        """Check if evaluation is complete."""
        return self.status == EvaluationStatus.COMPLETED
    
    def is_successful(self) -> bool:
        """Check if evaluation completed successfully."""
        return self.status == EvaluationStatus.COMPLETED and self.error_message is None
    
    def get_best_result(self) -> Optional[EvaluationResult]:
        """Get the result with highest confidence."""
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.confidence)
    
    def get_average_similarity(self) -> float:
        """Get average similarity score across all results."""
        if not self.results:
            return 0.0
        return sum(r.similarity_score for r in self.results) / len(self.results)
    
    def complete(self, success: bool = True, error_message: Optional[str] = None) -> 'Evaluation':
        """Mark evaluation as complete."""
        self.status = EvaluationStatus.COMPLETED if success else EvaluationStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        if error_message:
            self.error_message = error_message
        return self


# Factory functions for creating diff and evaluation entities
def create_diff(source_artifact_id: str, target_artifact_id: str, 
                diff_type: DiffType, artifact_type: ArtifactType) -> Diff:
    """Factory function to create a new diff."""
    return Diff(
        source_artifact_id=source_artifact_id,
        target_artifact_id=target_artifact_id,
        diff_type=diff_type,
        artifact_type=artifact_type
    )


def create_evaluation(diff_id: str, source_artifact_id: str, target_artifact_id: str,
                     artifact_type: ArtifactType) -> Evaluation:
    """Factory function to create a new evaluation."""
    return Evaluation(
        diff_id=diff_id,
        source_artifact_id=source_artifact_id,
        target_artifact_id=target_artifact_id,
        artifact_type=artifact_type
    )


def create_diff_hunk(operation: DiffOperation, source_start: int, source_length: int,
                    target_start: int, target_length: int, 
                    source_content: str = "", target_content: str = "") -> DiffHunk:
    """Factory function to create a diff hunk."""
    return DiffHunk(
        operation=operation,
        source_start=source_start,
        source_length=source_length,
        target_start=target_start,
        target_length=target_length,
        source_content=source_content,
        target_content=target_content
    )


if __name__ == "__main__":
    # Test diff and evaluation creation
    print("🧪 Testing diff and evaluation entities...")
    
    # Test diff creation
    diff = create_diff(
        source_artifact_id="art_001",
        target_artifact_id="art_002", 
        diff_type=DiffType.TEXTUAL,
        artifact_type=ArtifactType.TEXT
    )
    print(f"✅ Created diff: {diff.id}")
    
    # Test evaluation creation
    evaluation = create_evaluation(
        diff_id=diff.id,
        source_artifact_id="art_001",
        target_artifact_id="art_002",
        artifact_type=ArtifactType.TEXT
    )
    print(f"✅ Created evaluation: {evaluation.id}")
    
    # Test adding results
    result = EvaluationResult(
        method=EquivalenceMethod.EXACT,
        equivalent=False,
        confidence=0.95,
        similarity_score=0.85,
        reasoning="Minor textual differences detected"
    )
    evaluation.add_result(result)
    print(f"✅ Added result, consensus: {evaluation.consensus_result}")
    
    print("\n🎉 All diff and evaluation entities working correctly!")