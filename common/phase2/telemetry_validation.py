"""Phase 2 Telemetry Validation

This module provides validation functions for Phase 2 telemetry events
to ensure schema compliance and data quality.

Requirements: 8.2, 8.6, 9.6
"""

import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

from .telemetry import (
    Phase2EventType,
    Phase2BaseEvent,
    MismatchEvent,
    AIAnalysisEvent,
    ResolutionEvent,
    LearningEvent,
    EquivalenceEvent,
    InteractiveEvent,
    PHASE2_SCHEMA_VERSION
)

from .enums import (
    MismatchType,
    MismatchStatus,
    ResolutionStatus,
    SafetyLevel,
    ResolutionActionType,
    EquivalenceMethod,
    ArtifactType
)


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when telemetry event validation fails."""
    pass


class Phase2TelemetryValidator:
    """Validator for Phase 2 telemetry events."""
    
    def __init__(self):
        """Initialize the validator with schema rules."""
        self.required_fields = {
            "base": {
                "schema_version", "event_id", "timestamp", "event_type", "level"
            },
            "mismatch": {
                "mismatch_id", "mismatch_type", "artifact_ids", "detectors"
            },
            "ai_analysis": {
                "analysis_type", "ai_provider", "ai_model"
            },
            "resolution": {
                "resolution_plan_id", "action_type"
            },
            "learning": {
                "pattern_id", "pattern_type"
            },
            "equivalence": {
                "artifact_type", "methods_used"
            },
            "interactive": {
                "session_type", "user_id", "interaction_type"
            }
        }
        
        self.valid_enum_values = {
            "mismatch_type": {mt.value for mt in MismatchType},
            "mismatch_status": {ms.value for ms in MismatchStatus},
            "resolution_status": {rs.value for rs in ResolutionStatus},
            "safety_level": {sl.value for sl in SafetyLevel},
            "action_type": {at.value for at in ResolutionActionType},
            "equivalence_method": {em.value for em in EquivalenceMethod},
            "artifact_type": {at.value for at in ArtifactType}
        }
    
    def validate_event(self, event: Phase2BaseEvent) -> Tuple[bool, List[str]]:
        """Validate a Phase 2 telemetry event.
        
        Args:
            event: The event to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Convert to dict for validation
            event_dict = event.to_dict()
            
            # Validate base fields
            base_errors = self._validate_base_fields(event_dict)
            errors.extend(base_errors)
            
            # Validate event-specific fields
            event_errors = self._validate_event_specific_fields(event, event_dict)
            errors.extend(event_errors)
            
            # Validate enum values
            enum_errors = self._validate_enum_values(event_dict)
            errors.extend(enum_errors)
            
            # Validate data types
            type_errors = self._validate_data_types(event_dict)
            errors.extend(type_errors)
            
            # Validate business logic
            logic_errors = self._validate_business_logic(event, event_dict)
            errors.extend(logic_errors)
            
        except Exception as e:
            errors.append(f"Validation exception: {e}")
        
        return len(errors) == 0, errors
    
    def _validate_base_fields(self, event_dict: Dict[str, Any]) -> List[str]:
        """Validate base event fields."""
        errors = []
        
        # Check required base fields
        missing_fields = self.required_fields["base"] - set(event_dict.keys())
        if missing_fields:
            errors.append(f"Missing required base fields: {missing_fields}")
        
        # Validate schema version
        if event_dict.get("schema_version") != PHASE2_SCHEMA_VERSION:
            errors.append(f"Invalid schema version: {event_dict.get('schema_version')}, expected {PHASE2_SCHEMA_VERSION}")
        
        # Validate timestamp format
        timestamp = event_dict.get("timestamp")
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                errors.append(f"Invalid timestamp format: {timestamp}")
        
        # Validate event_id format (should be UUID)
        event_id = event_dict.get("event_id")
        if event_id and not isinstance(event_id, str):
            errors.append(f"Event ID must be string: {type(event_id)}")
        
        return errors
    
    def _validate_event_specific_fields(self, event: Phase2BaseEvent, event_dict: Dict[str, Any]) -> List[str]:
        """Validate event-specific required fields."""
        errors = []
        
        # Determine event category and required fields
        if isinstance(event, MismatchEvent):
            required = self.required_fields["mismatch"]
        elif isinstance(event, AIAnalysisEvent):
            required = self.required_fields["ai_analysis"]
        elif isinstance(event, ResolutionEvent):
            required = self.required_fields["resolution"]
        elif isinstance(event, LearningEvent):
            required = self.required_fields["learning"]
        elif isinstance(event, EquivalenceEvent):
            required = self.required_fields["equivalence"]
        elif isinstance(event, InteractiveEvent):
            required = self.required_fields["interactive"]
        else:
            # Base event, no additional requirements
            return errors
        
        # Check for missing required fields
        missing_fields = required - set(event_dict.keys())
        if missing_fields:
            errors.append(f"Missing required {type(event).__name__} fields: {missing_fields}")
        
        return errors
    
    def _validate_enum_values(self, event_dict: Dict[str, Any]) -> List[str]:
        """Validate enum field values."""
        errors = []
        
        # Check mismatch_type
        mismatch_type = event_dict.get("mismatch_type")
        if mismatch_type and mismatch_type not in self.valid_enum_values["mismatch_type"]:
            errors.append(f"Invalid mismatch_type: {mismatch_type}")
        
        # Check status fields
        status = event_dict.get("status")
        if status and status not in self.valid_enum_values["mismatch_status"]:
            errors.append(f"Invalid status: {status}")
        
        # Check safety_level
        safety_level = event_dict.get("safety_level")
        if safety_level and safety_level not in self.valid_enum_values["safety_level"]:
            errors.append(f"Invalid safety_level: {safety_level}")
        
        # Check action_type
        action_type = event_dict.get("action_type")
        if action_type and action_type not in self.valid_enum_values["action_type"]:
            errors.append(f"Invalid action_type: {action_type}")
        
        # Check artifact_type
        artifact_type = event_dict.get("artifact_type")
        if artifact_type and artifact_type not in self.valid_enum_values["artifact_type"]:
            errors.append(f"Invalid artifact_type: {artifact_type}")
        
        # Check methods_used (list of equivalence methods)
        methods_used = event_dict.get("methods_used", [])
        if methods_used:
            invalid_methods = set(methods_used) - self.valid_enum_values["equivalence_method"]
            if invalid_methods:
                errors.append(f"Invalid equivalence methods: {invalid_methods}")
        
        return errors
    
    def _validate_data_types(self, event_dict: Dict[str, Any]) -> List[str]:
        """Validate data types of event fields."""
        errors = []
        
        # Numeric fields that should be non-negative
        numeric_fields = {
            "confidence_score": (0.0, 1.0),
            "cost_estimate": (0.0, None),
            "latency_ms": (0.0, None),
            "analysis_duration_ms": (0.0, None),
            "session_duration_ms": (0.0, None),
            "success_rate": (0.0, 1.0),
            "combined_score": (0.0, 1.0),
            "result_confidence": (0.0, 1.0),
            "similarity_threshold": (0.0, 1.0)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            value = event_dict.get(field)
            if value is not None:
                if not isinstance(value, (int, float)):
                    errors.append(f"{field} must be numeric, got {type(value)}")
                elif value < min_val:
                    errors.append(f"{field} must be >= {min_val}, got {value}")
                elif max_val is not None and value > max_val:
                    errors.append(f"{field} must be <= {max_val}, got {value}")
        
        # List fields
        list_fields = {
            "artifact_ids", "detectors", "evidence_ids", "methods_used",
            "options_presented", "changes_made", "matched_patterns"
        }
        
        for field in list_fields:
            value = event_dict.get(field)
            if value is not None and not isinstance(value, list):
                errors.append(f"{field} must be a list, got {type(value)}")
        
        # Dictionary fields
        dict_fields = {
            "similarity_scores", "result_data", "feedback_details",
            "method_results", "method_durations", "decision_context",
            "impact_assessment"
        }
        
        for field in dict_fields:
            value = event_dict.get(field)
            if value is not None and not isinstance(value, dict):
                errors.append(f"{field} must be a dictionary, got {type(value)}")
        
        # Boolean fields
        bool_fields = {
            "destructive", "reversible", "success", "equivalent",
            "cache_hit", "calibration_applied", "user_override"
        }
        
        for field in bool_fields:
            value = event_dict.get(field)
            if value is not None and not isinstance(value, bool):
                errors.append(f"{field} must be boolean, got {type(value)}")
        
        return errors
    
    def _validate_business_logic(self, event: Phase2BaseEvent, event_dict: Dict[str, Any]) -> List[str]:
        """Validate business logic constraints."""
        errors = []
        
        # Validate ID format constraints
        mismatch_id = event_dict.get("mismatch_id")
        if mismatch_id and not mismatch_id.startswith("mis_"):
            errors.append(f"Mismatch ID must start with 'mis_': {mismatch_id}")
        
        resolution_plan_id = event_dict.get("resolution_plan_id")
        if resolution_plan_id and not resolution_plan_id.startswith("plan_"):
            errors.append(f"Resolution plan ID must start with 'plan_': {resolution_plan_id}")
        
        pattern_id = event_dict.get("pattern_id")
        if pattern_id and not pattern_id.startswith("pat_"):
            errors.append(f"Pattern ID must start with 'pat_': {pattern_id}")
        
        # Validate confidence scores are reasonable
        confidence_score = event_dict.get("confidence_score")
        if confidence_score is not None and confidence_score == 0.0:
            # Zero confidence might indicate an issue
            logger.warning(f"Event has zero confidence score: {event_dict.get('event_id')}")
        
        # Validate cost estimates are reasonable
        cost_estimate = event_dict.get("cost_estimate")
        if cost_estimate is not None and cost_estimate > 10.0:
            errors.append(f"Cost estimate seems too high: ${cost_estimate}")
        
        # Validate AI analysis events have required AI fields
        if isinstance(event, AIAnalysisEvent):
            if not event_dict.get("ai_provider"):
                errors.append("AI analysis events must specify ai_provider")
            if not event_dict.get("ai_model"):
                errors.append("AI analysis events must specify ai_model")
        
        # Validate resolution events have consistent action data
        if isinstance(event, ResolutionEvent):
            destructive = event_dict.get("destructive", False)
            action_type = event_dict.get("action_type")
            
            # Check if destructive flag matches action type
            if action_type in {"replace_artifact", "rewrite_formatting", "apply_transform"}:
                if not destructive:
                    logger.warning(f"Destructive action {action_type} not marked as destructive")
        
        # Validate equivalence events have consistent method data
        if isinstance(event, EquivalenceEvent):
            methods_used = event_dict.get("methods_used", [])
            method_results = event_dict.get("method_results", {})
            
            # Check that all methods have results
            missing_results = set(methods_used) - set(method_results.keys())
            if missing_results:
                errors.append(f"Missing method results for: {missing_results}")
        
        return errors
    
    def validate_event_sequence(self, events: List[Phase2BaseEvent]) -> Tuple[bool, List[str]]:
        """Validate a sequence of events for logical consistency."""
        errors = []
        
        # Group events by mismatch_id
        mismatch_events = {}
        for event in events:
            event_dict = event.to_dict()
            mismatch_id = event_dict.get("mismatch_id")
            if mismatch_id:
                if mismatch_id not in mismatch_events:
                    mismatch_events[mismatch_id] = []
                mismatch_events[mismatch_id].append(event)
        
        # Validate each mismatch workflow
        for mismatch_id, mismatch_event_list in mismatch_events.items():
            workflow_errors = self._validate_mismatch_workflow(mismatch_id, mismatch_event_list)
            errors.extend(workflow_errors)
        
        return len(errors) == 0, errors
    
    def _validate_mismatch_workflow(self, mismatch_id: str, events: List[Phase2BaseEvent]) -> List[str]:
        """Validate the workflow for a single mismatch."""
        errors = []
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        # Check for required event sequence
        event_types = [e.event_type for e in sorted_events if hasattr(e, 'event_type')]
        
        # Should start with MISMATCH_DETECTED
        if event_types and event_types[0] != Phase2EventType.MISMATCH_DETECTED:
            errors.append(f"Mismatch {mismatch_id} workflow should start with MISMATCH_DETECTED")
        
        # Check for logical event ordering
        status_progression = []
        for event in sorted_events:
            if isinstance(event, MismatchEvent):
                event_dict = event.to_dict()
                status = event_dict.get("status")
                if status:
                    status_progression.append(status)
        
        # Validate status progression makes sense
        if status_progression:
            # Should not go backwards in status
            status_order = ["detected", "analyzing", "analyzed", "resolved"]
            for i in range(1, len(status_progression)):
                prev_status = status_progression[i-1]
                curr_status = status_progression[i]
                
                if prev_status in status_order and curr_status in status_order:
                    prev_idx = status_order.index(prev_status)
                    curr_idx = status_order.index(curr_status)
                    
                    if curr_idx < prev_idx:
                        errors.append(f"Mismatch {mismatch_id} status went backwards: {prev_status} -> {curr_status}")
        
        return errors


# Global validator instance
_validator: Optional[Phase2TelemetryValidator] = None


def get_validator() -> Phase2TelemetryValidator:
    """Get the global telemetry validator instance."""
    global _validator
    if _validator is None:
        _validator = Phase2TelemetryValidator()
    return _validator


def validate_event(event: Phase2BaseEvent) -> Tuple[bool, List[str]]:
    """Validate a single Phase 2 telemetry event."""
    return get_validator().validate_event(event)


def validate_event_sequence(events: List[Phase2BaseEvent]) -> Tuple[bool, List[str]]:
    """Validate a sequence of Phase 2 telemetry events."""
    return get_validator().validate_event_sequence(events)


def validate_event_dict(event_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate an event dictionary without creating an event object."""
    validator = get_validator()
    errors = []
    
    # Validate basic structure
    base_errors = validator._validate_base_fields(event_dict)
    errors.extend(base_errors)
    
    # Validate enum values
    enum_errors = validator._validate_enum_values(event_dict)
    errors.extend(enum_errors)
    
    # Validate data types
    type_errors = validator._validate_data_types(event_dict)
    errors.extend(type_errors)
    
    return len(errors) == 0, errors