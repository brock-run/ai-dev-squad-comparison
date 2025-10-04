"""Phase 2 Telemetry Logger Integration

This module provides convenience functions for logging Phase 2 events
using the existing telemetry infrastructure.

Integrates with: common/telemetry/logger.py
Requirements: 8.2, 8.6, 9.6
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Import base telemetry logger
from common.telemetry.logger import StructuredLogger

# Import Phase 2 telemetry events
from .telemetry import (
    Phase2EventType,
    Phase2BaseEvent,
    MismatchEvent,
    AIAnalysisEvent,
    ResolutionEvent,
    LearningEvent,
    EquivalenceEvent,
    InteractiveEvent,
    create_phase2_event,
    create_mismatch_detected_event,
    create_ai_analysis_start_event,
    create_ai_analysis_complete_event,
    create_resolution_plan_created_event,
    create_resolution_action_complete_event,
    create_pattern_learned_event,
    create_equivalence_check_complete_event,
    create_user_decision_event,
    create_approval_granted_event
)

# Import Phase 2 enums
from .enums import (
    MismatchType,
    MismatchStatus,
    ResolutionStatus,
    SafetyLevel,
    ResolutionActionType,
    EquivalenceMethod,
    ArtifactType
)


class Phase2TelemetryLogger:
    """Enhanced telemetry logger for Phase 2 AI mismatch resolution operations."""
    
    def __init__(self, base_logger: Optional[StructuredLogger] = None):
        """Initialize Phase 2 telemetry logger.
        
        Args:
            base_logger: Existing structured logger instance. If None, creates a new one.
        """
        self.base_logger = base_logger or StructuredLogger()
        self.logger = logging.getLogger(__name__)
    
    def log_event(self, event: Phase2BaseEvent) -> None:
        """Log a Phase 2 event using the base telemetry logger."""
        try:
            # Log through base logger
            self.base_logger.log_event(event)
        except Exception as e:
            self.logger.error(f"Failed to log Phase 2 event: {e}")
    
    # Mismatch lifecycle logging
    
    def log_mismatch_detected(
        self,
        mismatch_id: str,
        mismatch_type: MismatchType,
        artifact_ids: List[str],
        detectors: List[str],
        confidence_score: float,
        run_id: str,
        **kwargs
    ) -> None:
        """Log mismatch detection event."""
        event = create_mismatch_detected_event(
            mismatch_id=mismatch_id,
            mismatch_type=mismatch_type,
            artifact_ids=artifact_ids,
            detectors=detectors,
            confidence_score=confidence_score,
            run_id=run_id,
            **kwargs
        )
        self.log_event(event)
    
    def log_mismatch_status_change(
        self,
        mismatch_id: str,
        old_status: MismatchStatus,
        new_status: MismatchStatus,
        **kwargs
    ) -> None:
        """Log mismatch status change."""
        event_type_map = {
            MismatchStatus.ANALYZING: Phase2EventType.MISMATCH_ANALYZING,
            MismatchStatus.RESOLVED: Phase2EventType.MISMATCH_RESOLVED,
            MismatchStatus.FAILED: Phase2EventType.MISMATCH_FAILED,
            MismatchStatus.SKIPPED: Phase2EventType.MISMATCH_SKIPPED,
        }
        
        event_type = event_type_map.get(new_status, Phase2EventType.MISMATCH_ANALYZING)
        
        event = MismatchEvent(
            event_type=event_type,
            mismatch_id=mismatch_id,
            status=new_status.value if hasattr(new_status, 'value') else str(new_status),
            message=f"Mismatch status changed from {old_status.value if hasattr(old_status, 'value') else str(old_status)} to {new_status.value if hasattr(new_status, 'value') else str(new_status)}",
            metadata={
                "old_status": old_status.value if hasattr(old_status, 'value') else str(old_status),
                "new_status": new_status.value if hasattr(new_status, 'value') else str(new_status)
            },
            **kwargs
        )
        self.log_event(event)
    
    # AI analysis logging
    
    def log_ai_analysis_start(
        self,
        mismatch_id: str,
        analysis_type: str,
        ai_provider: str,
        ai_model: str,
        **kwargs
    ) -> None:
        """Log AI analysis start."""
        event = create_ai_analysis_start_event(
            mismatch_id=mismatch_id,
            analysis_type=analysis_type,
            ai_provider=ai_provider,
            ai_model=ai_model,
            **kwargs
        )
        self.log_event(event)
    
    def log_ai_analysis_complete(
        self,
        mismatch_id: str,
        analysis_type: str,
        result_confidence: float,
        latency_ms: float,
        cost_estimate: float,
        **kwargs
    ) -> None:
        """Log AI analysis completion."""
        event = create_ai_analysis_complete_event(
            mismatch_id=mismatch_id,
            analysis_type=analysis_type,
            result_confidence=result_confidence,
            latency_ms=latency_ms,
            cost_estimate=cost_estimate,
            **kwargs
        )
        self.log_event(event)
    
    def log_ai_analysis_error(
        self,
        mismatch_id: str,
        analysis_type: str,
        error_message: str,
        **kwargs
    ) -> None:
        """Log AI analysis error."""
        event = AIAnalysisEvent(
            event_type=Phase2EventType.AI_ANALYSIS_ERROR,
            mismatch_id=mismatch_id,
            analysis_type=analysis_type,
            message=f"AI analysis failed: {error_message}",
            metadata={"error_message": error_message},
            **kwargs
        )
        self.log_event(event)    

    # Resolution planning and execution logging
    
    def log_resolution_plan_created(
        self,
        mismatch_id: str,
        resolution_plan_id: str,
        action_count: int,
        safety_level: SafetyLevel,
        **kwargs
    ) -> None:
        """Log resolution plan creation."""
        event = create_resolution_plan_created_event(
            mismatch_id=mismatch_id,
            resolution_plan_id=resolution_plan_id,
            action_count=action_count,
            safety_level=safety_level,
            **kwargs
        )
        self.log_event(event)
    
    def log_resolution_plan_status_change(
        self,
        resolution_plan_id: str,
        new_status: ResolutionStatus,
        **kwargs
    ) -> None:
        """Log resolution plan status change."""
        event_type_map = {
            ResolutionStatus.APPROVED: Phase2EventType.RESOLUTION_PLAN_APPROVED,
            ResolutionStatus.REJECTED: Phase2EventType.RESOLUTION_PLAN_REJECTED,
            ResolutionStatus.APPLIED: Phase2EventType.RESOLUTION_PLAN_APPLIED,
            ResolutionStatus.ROLLED_BACK: Phase2EventType.RESOLUTION_PLAN_ROLLED_BACK,
        }
        
        event_type = event_type_map.get(new_status, Phase2EventType.RESOLUTION_PLAN_CREATED)
        
        event = ResolutionEvent(
            event_type=event_type,
            resolution_plan_id=resolution_plan_id,
            message=f"Resolution plan status changed to {new_status.value if hasattr(new_status, 'value') else str(new_status)}",
            metadata={"new_status": new_status.value if hasattr(new_status, 'value') else str(new_status)},
            **kwargs
        )
        self.log_event(event)
    
    def log_resolution_action_start(
        self,
        resolution_plan_id: str,
        action_type: ResolutionActionType,
        target_artifact_id: str,
        **kwargs
    ) -> None:
        """Log resolution action start."""
        event = ResolutionEvent(
            event_type=Phase2EventType.RESOLUTION_ACTION_START,
            resolution_plan_id=resolution_plan_id,
            action_type=action_type.value if hasattr(action_type, 'value') else str(action_type),
            target_artifact_id=target_artifact_id,
            message=f"Starting resolution action: {action_type.value if hasattr(action_type, 'value') else str(action_type)}",
            **kwargs
        )
        self.log_event(event)
    
    def log_resolution_action_complete(
        self,
        resolution_plan_id: str,
        action_type: ResolutionActionType,
        target_artifact_id: str,
        success: bool,
        **kwargs
    ) -> None:
        """Log resolution action completion."""
        event = create_resolution_action_complete_event(
            resolution_plan_id=resolution_plan_id,
            action_type=action_type,
            target_artifact_id=target_artifact_id,
            success=success,
            **kwargs
        )
        self.log_event(event)
    
    def log_resolution_action_preview(
        self,
        resolution_plan_id: str,
        action_type: ResolutionActionType,
        preview_diff: str,
        impact_assessment: Dict[str, Any],
        **kwargs
    ) -> None:
        """Log resolution action preview."""
        event = ResolutionEvent(
            event_type=Phase2EventType.RESOLUTION_ACTION_PREVIEW,
            resolution_plan_id=resolution_plan_id,
            action_type=action_type.value if hasattr(action_type, 'value') else str(action_type),
            preview_diff=preview_diff,
            impact_assessment=impact_assessment,
            message=f"Generated preview for action: {action_type.value if hasattr(action_type, 'value') else str(action_type)}",
            **kwargs
        )
        self.log_event(event)
    
    # Learning and pattern logging
    
    def log_pattern_learned(
        self,
        pattern_id: str,
        mismatch_type: MismatchType,
        pattern_signature: str,
        success_rate: float,
        **kwargs
    ) -> None:
        """Log pattern learning."""
        event = create_pattern_learned_event(
            pattern_id=pattern_id,
            mismatch_type=mismatch_type,
            pattern_signature=pattern_signature,
            success_rate=success_rate,
            **kwargs
        )
        self.log_event(event)
    
    def log_pattern_matched(
        self,
        pattern_id: str,
        mismatch_id: str,
        similarity_score: float,
        **kwargs
    ) -> None:
        """Log pattern matching."""
        event = LearningEvent(
            event_type=Phase2EventType.PATTERN_MATCHED,
            pattern_id=pattern_id,
            mismatch_id=mismatch_id,
            message=f"Pattern matched with similarity {similarity_score:.3f}",
            metadata={"similarity_score": similarity_score},
            **kwargs
        )
        self.log_event(event)
    
    def log_learning_feedback(
        self,
        pattern_id: str,
        feedback_type: str,
        feedback_score: float,
        feedback_details: Dict[str, Any],
        **kwargs
    ) -> None:
        """Log learning feedback."""
        event = LearningEvent(
            event_type=Phase2EventType.LEARNING_FEEDBACK,
            pattern_id=pattern_id,
            feedback_type=feedback_type,
            feedback_score=feedback_score,
            feedback_details=feedback_details,
            message=f"Learning feedback: {feedback_type} (score: {feedback_score:.3f})",
            **kwargs
        )
        self.log_event(event)
    
    # Equivalence detection logging
    
    def log_equivalence_check_start(
        self,
        artifact_type: ArtifactType,
        methods_to_use: List[EquivalenceMethod],
        **kwargs
    ) -> None:
        """Log equivalence check start."""
        method_names = [m.value if hasattr(m, 'value') else str(m) for m in methods_to_use]
        
        event = EquivalenceEvent(
            event_type=Phase2EventType.EQUIVALENCE_CHECK_START,
            artifact_type=artifact_type.value if hasattr(artifact_type, 'value') else str(artifact_type),
            methods_used=method_names,
            message=f"Starting equivalence check for {artifact_type.value if hasattr(artifact_type, 'value') else str(artifact_type)} using {len(method_names)} methods",
            **kwargs
        )
        self.log_event(event)
    
    def log_equivalence_check_complete(
        self,
        artifact_type: ArtifactType,
        methods_used: List[EquivalenceMethod],
        equivalent: bool,
        combined_score: float,
        **kwargs
    ) -> None:
        """Log equivalence check completion."""
        event = create_equivalence_check_complete_event(
            artifact_type=artifact_type,
            methods_used=methods_used,
            equivalent=equivalent,
            combined_score=combined_score,
            **kwargs
        )
        self.log_event(event)
    
    def log_equivalence_method_result(
        self,
        method: EquivalenceMethod,
        result_score: float,
        duration_ms: float,
        **kwargs
    ) -> None:
        """Log individual equivalence method result."""
        event = EquivalenceEvent(
            event_type=Phase2EventType.EQUIVALENCE_METHOD_RESULT,
            methods_used=[method.value if hasattr(method, 'value') else str(method)],
            method_results={method.value if hasattr(method, 'value') else str(method): result_score},
            method_durations={method.value if hasattr(method, 'value') else str(method): duration_ms},
            message=f"Method {method.value if hasattr(method, 'value') else str(method)} result: {result_score:.3f} ({duration_ms:.1f}ms)",
            **kwargs
        )
        self.log_event(event)
    
    # Interactive session logging
    
    def log_interactive_session_start(
        self,
        session_type: str,
        user_id: str,
        mismatch_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log interactive session start."""
        event = InteractiveEvent(
            event_type=Phase2EventType.INTERACTIVE_SESSION_START,
            session_type=session_type,
            user_id=user_id,
            mismatch_id=mismatch_id,
            interaction_type="session_start",
            message=f"Interactive session started: {session_type} for user {user_id}",
            **kwargs
        )
        self.log_event(event)
    
    def log_interactive_session_end(
        self,
        session_type: str,
        user_id: str,
        session_duration_ms: float,
        **kwargs
    ) -> None:
        """Log interactive session end."""
        event = InteractiveEvent(
            event_type=Phase2EventType.INTERACTIVE_SESSION_END,
            session_type=session_type,
            user_id=user_id,
            session_duration_ms=session_duration_ms,
            interaction_type="session_end",
            message=f"Interactive session ended: {session_type} ({session_duration_ms:.1f}ms)",
            **kwargs
        )
        self.log_event(event)
    
    def log_user_decision(
        self,
        session_type: str,
        user_id: str,
        user_choice: str,
        options_presented: List[str],
        **kwargs
    ) -> None:
        """Log user decision."""
        event = create_user_decision_event(
            session_type=session_type,
            user_id=user_id,
            user_choice=user_choice,
            options_presented=options_presented,
            **kwargs
        )
        self.log_event(event)
    
    def log_approval_request(
        self,
        resolution_plan_id: str,
        approval_type: str,
        required_role: str,
        **kwargs
    ) -> None:
        """Log approval request."""
        event = InteractiveEvent(
            event_type=Phase2EventType.APPROVAL_REQUEST,
            resolution_plan_id=resolution_plan_id,
            interaction_type="approval",
            approval_type=approval_type,
            approver_role=required_role,
            message=f"Approval requested: {approval_type} from {required_role}",
            **kwargs
        )
        self.log_event(event)
    
    def log_approval_granted(
        self,
        resolution_plan_id: str,
        user_id: str,
        approval_type: str,
        approver_role: str,
        **kwargs
    ) -> None:
        """Log approval granted."""
        event = create_approval_granted_event(
            resolution_plan_id=resolution_plan_id,
            user_id=user_id,
            approval_type=approval_type,
            approver_role=approver_role,
            **kwargs
        )
        self.log_event(event)
    
    def log_approval_denied(
        self,
        resolution_plan_id: str,
        user_id: str,
        approval_type: str,
        approver_role: str,
        reason: str,
        **kwargs
    ) -> None:
        """Log approval denied."""
        event = InteractiveEvent(
            event_type=Phase2EventType.APPROVAL_DENIED,
            resolution_plan_id=resolution_plan_id,
            user_id=user_id,
            interaction_type="approval",
            approval_type=approval_type,
            approver_role=approver_role,
            approval_reason=reason,
            message=f"Approval denied by {approver_role} {user_id}: {reason}",
            **kwargs
        )
        self.log_event(event)
    
    # Convenience methods for common workflows
    
    def log_mismatch_workflow(
        self,
        mismatch_id: str,
        mismatch_type: MismatchType,
        artifact_ids: List[str],
        detectors: List[str],
        confidence_score: float,
        run_id: str,
        analysis_results: Optional[Dict[str, Any]] = None,
        resolution_plan_id: Optional[str] = None
    ) -> None:
        """Log a complete mismatch workflow in sequence."""
        # Log detection
        self.log_mismatch_detected(
            mismatch_id=mismatch_id,
            mismatch_type=mismatch_type,
            artifact_ids=artifact_ids,
            detectors=detectors,
            confidence_score=confidence_score,
            run_id=run_id
        )
        
        # Log analysis if provided
        if analysis_results:
            self.log_ai_analysis_complete(
                mismatch_id=mismatch_id,
                analysis_type=analysis_results.get("type", "unknown"),
                result_confidence=analysis_results.get("confidence", 0.0),
                latency_ms=analysis_results.get("latency_ms", 0.0),
                cost_estimate=analysis_results.get("cost", 0.0)
            )
        
        # Log resolution plan if provided
        if resolution_plan_id:
            self.log_resolution_plan_created(
                mismatch_id=mismatch_id,
                resolution_plan_id=resolution_plan_id,
                action_count=1,  # Default
                safety_level=SafetyLevel.ADVISORY  # Default
            )


# Global instance for convenience
_phase2_logger: Optional[Phase2TelemetryLogger] = None


def get_phase2_logger() -> Phase2TelemetryLogger:
    """Get the global Phase 2 telemetry logger instance."""
    global _phase2_logger
    if _phase2_logger is None:
        _phase2_logger = Phase2TelemetryLogger()
    return _phase2_logger


def set_phase2_logger(logger: Phase2TelemetryLogger) -> None:
    """Set the global Phase 2 telemetry logger instance."""
    global _phase2_logger
    _phase2_logger = logger