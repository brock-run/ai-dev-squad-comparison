"""Phase 2 Telemetry Schema Extension

This module extends the base telemetry schema with AI-specific event types
for mismatch analysis, resolution planning, and learning operations.

Extends: common/telemetry/schema.py (ADR-008)
Requirements: 8.2, 8.6, 9.6
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Import base telemetry components
from common.telemetry.schema import BaseEvent, EventType, LogLevel, SCHEMA_VERSION

# Import Phase 2 enums for type safety
from .enums import (
    MismatchType,
    MismatchStatus,
    ResolutionStatus,
    SafetyLevel,
    ResolutionActionType,
    EquivalenceMethod,
    ArtifactType,
    Environment
)

# Phase 2 schema version
PHASE2_SCHEMA_VERSION = "2.0"


class Phase2EventType(Enum):
    """Phase 2 specific event types for AI mismatch resolution."""
    
    # Mismatch detection and analysis events
    MISMATCH_DETECTED = "mismatch.detected"
    MISMATCH_ANALYZING = "mismatch.analyzing"
    MISMATCH_ANALYZED = "mismatch.analyzed"
    MISMATCH_RESOLVED = "mismatch.resolved"
    MISMATCH_FAILED = "mismatch.failed"
    MISMATCH_SKIPPED = "mismatch.skipped"
    
    # AI analysis events
    AI_ANALYSIS_START = "ai.analysis.start"
    AI_ANALYSIS_COMPLETE = "ai.analysis.complete"
    AI_ANALYSIS_ERROR = "ai.analysis.error"
    AI_EMBEDDING_REQUEST = "ai.embedding.request"
    AI_EMBEDDING_RESPONSE = "ai.embedding.response"
    AI_LLM_JUDGE_REQUEST = "ai.llm_judge.request"
    AI_LLM_JUDGE_RESPONSE = "ai.llm_judge.response"
    
    # Resolution planning events
    RESOLUTION_PLAN_CREATED = "resolution.plan.created"
    RESOLUTION_PLAN_APPROVED = "resolution.plan.approved"
    RESOLUTION_PLAN_REJECTED = "resolution.plan.rejected"
    RESOLUTION_PLAN_APPLIED = "resolution.plan.applied"
    RESOLUTION_PLAN_ROLLED_BACK = "resolution.plan.rolled_back"
    
    # Resolution action events
    RESOLUTION_ACTION_START = "resolution.action.start"
    RESOLUTION_ACTION_COMPLETE = "resolution.action.complete"
    RESOLUTION_ACTION_ERROR = "resolution.action.error"
    RESOLUTION_ACTION_PREVIEW = "resolution.action.preview"
    
    # Learning and pattern events
    PATTERN_LEARNED = "pattern.learned"
    PATTERN_MATCHED = "pattern.matched"
    PATTERN_UPDATED = "pattern.updated"
    LEARNING_FEEDBACK = "learning.feedback"
    
    # Equivalence detection events
    EQUIVALENCE_CHECK_START = "equivalence.check.start"
    EQUIVALENCE_CHECK_COMPLETE = "equivalence.check.complete"
    EQUIVALENCE_METHOD_RESULT = "equivalence.method.result"
    
    # Interactive resolution events
    INTERACTIVE_SESSION_START = "interactive.session.start"
    INTERACTIVE_SESSION_END = "interactive.session.end"
    USER_DECISION = "user.decision"
    APPROVAL_REQUEST = "approval.request"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"


@dataclass
class Phase2BaseEvent(BaseEvent):
    """Base event class for Phase 2 with additional AI-specific fields."""
    
    # Override schema version for Phase 2
    schema_version: str = PHASE2_SCHEMA_VERSION
    
    # Phase 2 specific context
    mismatch_id: Optional[str] = None
    resolution_plan_id: Optional[str] = None
    pattern_id: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    confidence_score: Optional[float] = None
    cost_estimate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary with Phase 2 fields."""
        data = super().to_dict()
        data.update({
            "mismatch_id": self.mismatch_id,
            "resolution_plan_id": self.resolution_plan_id,
            "pattern_id": self.pattern_id,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "confidence_score": self.confidence_score,
            "cost_estimate": self.cost_estimate
        })
        return data


@dataclass
class MismatchEvent(Phase2BaseEvent):
    """Event for mismatch detection and lifecycle tracking."""
    
    # Mismatch details
    mismatch_type: Optional[str] = None
    artifact_ids: List[str] = field(default_factory=list)
    detectors: List[str] = field(default_factory=list)
    diff_id: Optional[str] = None
    
    # Analysis results
    similarity_scores: Dict[str, float] = field(default_factory=dict)
    evidence_ids: List[str] = field(default_factory=list)
    root_cause: Optional[str] = None
    
    # Status tracking
    status: Optional[str] = None
    error_code: Optional[str] = None
    
    # Performance metrics
    analysis_duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "mismatch_type": self.mismatch_type,
            "artifact_ids": self.artifact_ids,
            "detectors": self.detectors,
            "diff_id": self.diff_id,
            "similarity_scores": self.similarity_scores,
            "evidence_ids": self.evidence_ids,
            "root_cause": self.root_cause,
            "status": self.status,
            "error_code": self.error_code,
            "analysis_duration_ms": self.analysis_duration_ms
        })
        return data


@dataclass
class AIAnalysisEvent(Phase2BaseEvent):
    """Event for AI-powered analysis operations."""
    
    # Analysis type and method
    analysis_type: Optional[str] = None  # "semantic", "embedding", "llm_judge"
    method: Optional[str] = None
    
    # Input/output data
    input_size_bytes: Optional[int] = None
    output_size_bytes: Optional[int] = None
    
    # AI service details
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    # Results
    result_confidence: Optional[float] = None
    result_data: Dict[str, Any] = field(default_factory=dict)
    
    # Performance
    latency_ms: Optional[float] = None
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "analysis_type": self.analysis_type,
            "method": self.method,
            "input_size_bytes": self.input_size_bytes,
            "output_size_bytes": self.output_size_bytes,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "result_confidence": self.result_confidence,
            "result_data": self.result_data,
            "latency_ms": self.latency_ms,
            "cache_hit": self.cache_hit
        })
        return data


@dataclass
class ResolutionEvent(Phase2BaseEvent):
    """Event for resolution planning and execution."""
    
    # Resolution plan details
    action_count: Optional[int] = None
    safety_level: Optional[str] = None
    required_approvals: Optional[int] = None
    received_approvals: Optional[int] = None
    
    # Action details
    action_type: Optional[str] = None
    target_artifact_id: Optional[str] = None
    transformation: Optional[str] = None
    destructive: bool = False
    reversible: bool = True
    
    # Execution results
    success: Optional[bool] = None
    changes_made: List[str] = field(default_factory=list)
    rollback_checkpoint: Optional[str] = None
    
    # Preview information
    preview_diff: Optional[str] = None
    impact_assessment: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "action_count": self.action_count,
            "safety_level": self.safety_level,
            "required_approvals": self.required_approvals,
            "received_approvals": self.received_approvals,
            "action_type": self.action_type,
            "target_artifact_id": self.target_artifact_id,
            "transformation": self.transformation,
            "destructive": self.destructive,
            "reversible": self.reversible,
            "success": self.success,
            "changes_made": self.changes_made,
            "rollback_checkpoint": self.rollback_checkpoint,
            "preview_diff": self.preview_diff,
            "impact_assessment": self.impact_assessment
        })
        return data


@dataclass
class LearningEvent(Phase2BaseEvent):
    """Event for learning and pattern recognition operations."""
    
    # Pattern information
    pattern_signature: Optional[str] = None
    pattern_type: Optional[str] = None
    similarity_threshold: Optional[float] = None
    
    # Learning metrics
    success_rate: Optional[float] = None
    usage_count: Optional[int] = None
    learning_rate: Optional[float] = None
    
    # Feedback data
    feedback_type: Optional[str] = None  # "success", "failure", "partial"
    feedback_score: Optional[float] = None
    feedback_details: Dict[str, Any] = field(default_factory=dict)
    
    # Pattern matching
    matched_patterns: List[str] = field(default_factory=list)
    match_scores: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "pattern_signature": self.pattern_signature,
            "pattern_type": self.pattern_type,
            "similarity_threshold": self.similarity_threshold,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "learning_rate": self.learning_rate,
            "feedback_type": self.feedback_type,
            "feedback_score": self.feedback_score,
            "feedback_details": self.feedback_details,
            "matched_patterns": self.matched_patterns,
            "match_scores": self.match_scores
        })
        return data


@dataclass
class EquivalenceEvent(Phase2BaseEvent):
    """Event for equivalence detection operations."""
    
    # Equivalence check details
    artifact_type: Optional[str] = None
    methods_used: List[str] = field(default_factory=list)
    method_weights: List[float] = field(default_factory=list)
    
    # Individual method results
    method_results: Dict[str, float] = field(default_factory=dict)
    method_durations: Dict[str, float] = field(default_factory=dict)
    
    # Final decision
    equivalent: Optional[bool] = None
    combined_score: Optional[float] = None
    decision_threshold: Optional[float] = None
    
    # Calibration data
    calibration_applied: bool = False
    calibration_adjustment: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "artifact_type": self.artifact_type,
            "methods_used": self.methods_used,
            "method_weights": self.method_weights,
            "method_results": self.method_results,
            "method_durations": self.method_durations,
            "equivalent": self.equivalent,
            "combined_score": self.combined_score,
            "decision_threshold": self.decision_threshold,
            "calibration_applied": self.calibration_applied,
            "calibration_adjustment": self.calibration_adjustment
        })
        return data


@dataclass
class InteractiveEvent(Phase2BaseEvent):
    """Event for interactive resolution sessions."""
    
    # Session information
    session_type: Optional[str] = None  # "cli", "web", "api"
    user_id: Optional[str] = None
    session_duration_ms: Optional[float] = None
    
    # User interaction
    interaction_type: Optional[str] = None  # "decision", "approval", "input"
    user_choice: Optional[str] = None
    options_presented: List[str] = field(default_factory=list)
    
    # Decision context
    decision_context: Dict[str, Any] = field(default_factory=dict)
    recommendation: Optional[str] = None
    user_override: bool = False
    
    # Approval workflow
    approval_type: Optional[str] = None  # "standard", "dual_key"
    approver_role: Optional[str] = None
    approval_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "session_type": self.session_type,
            "user_id": self.user_id,
            "session_duration_ms": self.session_duration_ms,
            "interaction_type": self.interaction_type,
            "user_choice": self.user_choice,
            "options_presented": self.options_presented,
            "decision_context": self.decision_context,
            "recommendation": self.recommendation,
            "user_override": self.user_override,
            "approval_type": self.approval_type,
            "approver_role": self.approver_role,
            "approval_reason": self.approval_reason
        })
        return data


# Event factory function for Phase 2 events
def create_phase2_event(event_type: Phase2EventType, **kwargs) -> Phase2BaseEvent:
    """Create an appropriate Phase 2 event instance based on event type."""
    
    event_mapping = {
        # Mismatch events
        Phase2EventType.MISMATCH_DETECTED: MismatchEvent,
        Phase2EventType.MISMATCH_ANALYZING: MismatchEvent,
        Phase2EventType.MISMATCH_ANALYZED: MismatchEvent,
        Phase2EventType.MISMATCH_RESOLVED: MismatchEvent,
        Phase2EventType.MISMATCH_FAILED: MismatchEvent,
        Phase2EventType.MISMATCH_SKIPPED: MismatchEvent,
        
        # AI analysis events
        Phase2EventType.AI_ANALYSIS_START: AIAnalysisEvent,
        Phase2EventType.AI_ANALYSIS_COMPLETE: AIAnalysisEvent,
        Phase2EventType.AI_ANALYSIS_ERROR: AIAnalysisEvent,
        Phase2EventType.AI_EMBEDDING_REQUEST: AIAnalysisEvent,
        Phase2EventType.AI_EMBEDDING_RESPONSE: AIAnalysisEvent,
        Phase2EventType.AI_LLM_JUDGE_REQUEST: AIAnalysisEvent,
        Phase2EventType.AI_LLM_JUDGE_RESPONSE: AIAnalysisEvent,
        
        # Resolution events
        Phase2EventType.RESOLUTION_PLAN_CREATED: ResolutionEvent,
        Phase2EventType.RESOLUTION_PLAN_APPROVED: ResolutionEvent,
        Phase2EventType.RESOLUTION_PLAN_REJECTED: ResolutionEvent,
        Phase2EventType.RESOLUTION_PLAN_APPLIED: ResolutionEvent,
        Phase2EventType.RESOLUTION_PLAN_ROLLED_BACK: ResolutionEvent,
        Phase2EventType.RESOLUTION_ACTION_START: ResolutionEvent,
        Phase2EventType.RESOLUTION_ACTION_COMPLETE: ResolutionEvent,
        Phase2EventType.RESOLUTION_ACTION_ERROR: ResolutionEvent,
        Phase2EventType.RESOLUTION_ACTION_PREVIEW: ResolutionEvent,
        
        # Learning events
        Phase2EventType.PATTERN_LEARNED: LearningEvent,
        Phase2EventType.PATTERN_MATCHED: LearningEvent,
        Phase2EventType.PATTERN_UPDATED: LearningEvent,
        Phase2EventType.LEARNING_FEEDBACK: LearningEvent,
        
        # Equivalence events
        Phase2EventType.EQUIVALENCE_CHECK_START: EquivalenceEvent,
        Phase2EventType.EQUIVALENCE_CHECK_COMPLETE: EquivalenceEvent,
        Phase2EventType.EQUIVALENCE_METHOD_RESULT: EquivalenceEvent,
        
        # Interactive events
        Phase2EventType.INTERACTIVE_SESSION_START: InteractiveEvent,
        Phase2EventType.INTERACTIVE_SESSION_END: InteractiveEvent,
        Phase2EventType.USER_DECISION: InteractiveEvent,
        Phase2EventType.APPROVAL_REQUEST: InteractiveEvent,
        Phase2EventType.APPROVAL_GRANTED: InteractiveEvent,
        Phase2EventType.APPROVAL_DENIED: InteractiveEvent,
    }
    
    event_class = event_mapping.get(event_type, Phase2BaseEvent)
    
    # Convert event_type to the base EventType if needed for compatibility
    if hasattr(event_type, 'value'):
        kwargs['event_type'] = event_type
    
    return event_class(**kwargs)


# Convenience functions for creating common Phase 2 events

def create_mismatch_detected_event(
    mismatch_id: str,
    mismatch_type: MismatchType,
    artifact_ids: List[str],
    detectors: List[str],
    confidence_score: float,
    run_id: str,
    **kwargs
) -> MismatchEvent:
    """Create a mismatch detected event."""
    return MismatchEvent(
        event_type=Phase2EventType.MISMATCH_DETECTED,
        mismatch_id=mismatch_id,
        run_id=run_id,
        mismatch_type=mismatch_type.value if hasattr(mismatch_type, 'value') else str(mismatch_type),
        artifact_ids=artifact_ids,
        detectors=detectors,
        confidence_score=confidence_score,
        status=MismatchStatus.DETECTED.value,
        message=f"Mismatch detected: {mismatch_type.value if hasattr(mismatch_type, 'value') else str(mismatch_type)}",
        **kwargs
    )


def create_ai_analysis_start_event(
    mismatch_id: str,
    analysis_type: str,
    ai_provider: str,
    ai_model: str,
    **kwargs
) -> AIAnalysisEvent:
    """Create an AI analysis start event."""
    return AIAnalysisEvent(
        event_type=Phase2EventType.AI_ANALYSIS_START,
        mismatch_id=mismatch_id,
        analysis_type=analysis_type,
        ai_provider=ai_provider,
        ai_model=ai_model,
        message=f"Starting {analysis_type} analysis with {ai_provider}/{ai_model}",
        **kwargs
    )


def create_ai_analysis_complete_event(
    mismatch_id: str,
    analysis_type: str,
    result_confidence: float,
    latency_ms: float,
    cost_estimate: float,
    **kwargs
) -> AIAnalysisEvent:
    """Create an AI analysis complete event."""
    return AIAnalysisEvent(
        event_type=Phase2EventType.AI_ANALYSIS_COMPLETE,
        mismatch_id=mismatch_id,
        analysis_type=analysis_type,
        result_confidence=result_confidence,
        latency_ms=latency_ms,
        cost_estimate=cost_estimate,
        message=f"Completed {analysis_type} analysis (confidence: {result_confidence:.3f})",
        **kwargs
    )


def create_resolution_plan_created_event(
    mismatch_id: str,
    resolution_plan_id: str,
    action_count: int,
    safety_level: SafetyLevel,
    **kwargs
) -> ResolutionEvent:
    """Create a resolution plan created event."""
    return ResolutionEvent(
        event_type=Phase2EventType.RESOLUTION_PLAN_CREATED,
        mismatch_id=mismatch_id,
        resolution_plan_id=resolution_plan_id,
        action_count=action_count,
        safety_level=safety_level.value if hasattr(safety_level, 'value') else str(safety_level),
        message=f"Created resolution plan with {action_count} actions (safety: {safety_level.value if hasattr(safety_level, 'value') else str(safety_level)})",
        **kwargs
    )


def create_resolution_action_complete_event(
    resolution_plan_id: str,
    action_type: ResolutionActionType,
    target_artifact_id: str,
    success: bool,
    **kwargs
) -> ResolutionEvent:
    """Create a resolution action complete event."""
    return ResolutionEvent(
        event_type=Phase2EventType.RESOLUTION_ACTION_COMPLETE,
        resolution_plan_id=resolution_plan_id,
        action_type=action_type.value if hasattr(action_type, 'value') else str(action_type),
        target_artifact_id=target_artifact_id,
        success=success,
        message=f"Resolution action {action_type.value if hasattr(action_type, 'value') else str(action_type)} {'succeeded' if success else 'failed'}",
        **kwargs
    )


def create_pattern_learned_event(
    pattern_id: str,
    mismatch_type: MismatchType,
    pattern_signature: str,
    success_rate: float,
    **kwargs
) -> LearningEvent:
    """Create a pattern learned event."""
    return LearningEvent(
        event_type=Phase2EventType.PATTERN_LEARNED,
        pattern_id=pattern_id,
        pattern_signature=pattern_signature,
        pattern_type=mismatch_type.value if hasattr(mismatch_type, 'value') else str(mismatch_type),
        success_rate=success_rate,
        message=f"Learned new pattern for {mismatch_type.value if hasattr(mismatch_type, 'value') else str(mismatch_type)} (success rate: {success_rate:.3f})",
        **kwargs
    )


def create_equivalence_check_complete_event(
    artifact_type: ArtifactType,
    methods_used: List[EquivalenceMethod],
    equivalent: bool,
    combined_score: float,
    **kwargs
) -> EquivalenceEvent:
    """Create an equivalence check complete event."""
    method_names = [m.value if hasattr(m, 'value') else str(m) for m in methods_used]
    
    return EquivalenceEvent(
        event_type=Phase2EventType.EQUIVALENCE_CHECK_COMPLETE,
        artifact_type=artifact_type.value if hasattr(artifact_type, 'value') else str(artifact_type),
        methods_used=method_names,
        equivalent=equivalent,
        combined_score=combined_score,
        message=f"Equivalence check: {'equivalent' if equivalent else 'not equivalent'} (score: {combined_score:.3f})",
        **kwargs
    )


def create_user_decision_event(
    session_type: str,
    user_id: str,
    user_choice: str,
    options_presented: List[str],
    **kwargs
) -> InteractiveEvent:
    """Create a user decision event."""
    return InteractiveEvent(
        event_type=Phase2EventType.USER_DECISION,
        session_type=session_type,
        user_id=user_id,
        interaction_type="decision",
        user_choice=user_choice,
        options_presented=options_presented,
        message=f"User {user_id} chose '{user_choice}' from {len(options_presented)} options",
        **kwargs
    )


def create_approval_granted_event(
    resolution_plan_id: str,
    user_id: str,
    approval_type: str,
    approver_role: str,
    **kwargs
) -> InteractiveEvent:
    """Create an approval granted event."""
    return InteractiveEvent(
        event_type=Phase2EventType.APPROVAL_GRANTED,
        resolution_plan_id=resolution_plan_id,
        user_id=user_id,
        interaction_type="approval",
        approval_type=approval_type,
        approver_role=approver_role,
        message=f"Approval granted by {approver_role} {user_id} (type: {approval_type})",
        **kwargs
    )