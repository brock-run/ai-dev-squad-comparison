"""
Development State Management for LangGraph

This module defines the state schema and management for the LangGraph development workflow.
It includes comprehensive state tracking, validation, and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, field
import json


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    INITIALIZING = "initializing"
    DESIGN_IN_PROGRESS = "design_in_progress"
    DESIGN_COMPLETE = "design_complete"
    IMPLEMENTATION_IN_PROGRESS = "implementation_in_progress"
    IMPLEMENTATION_COMPLETE = "implementation_complete"
    TESTING_IN_PROGRESS = "testing_in_progress"
    TESTING_COMPLETE = "testing_complete"
    REVIEW_IN_PROGRESS = "review_in_progress"
    REVIEW_COMPLETE = "review_complete"
    VCS_IN_PROGRESS = "vcs_in_progress"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


class AgentRole(str, Enum):
    """Agent roles in the development workflow."""
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    VCS_MANAGER = "vcs_manager"


@dataclass
class AgentExecution:
    """Represents an agent execution within the workflow."""
    agent_role: AgentRole
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'agent_role': self.agent_role.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'retry_count': self.retry_count,
            'duration_seconds': self.duration_seconds
        }


@dataclass
class DesignArtifact:
    """Design artifact created by the architect."""
    architecture_type: str
    components: List[Dict[str, Any]] = field(default_factory=list)
    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    data_models: List[Dict[str, Any]] = field(default_factory=list)
    design_decisions: List[str] = field(default_factory=list)
    trade_offs: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'architecture_type': self.architecture_type,
            'components': self.components,
            'interfaces': self.interfaces,
            'data_models': self.data_models,
            'design_decisions': self.design_decisions,
            'trade_offs': self.trade_offs,
            'estimated_complexity': self.estimated_complexity
        }


@dataclass
class CodeArtifact:
    """Code artifact created by the developer."""
    language: str
    main_code: str
    supporting_files: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    entry_point: Optional[str] = None
    documentation: Optional[str] = None
    
    @property
    def total_lines(self) -> int:
        """Get total lines of code."""
        lines = len(self.main_code.split('\n'))
        for file_content in self.supporting_files.values():
            lines += len(file_content.split('\n'))
        return lines
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'language': self.language,
            'main_code': self.main_code,
            'supporting_files': self.supporting_files,
            'dependencies': self.dependencies,
            'entry_point': self.entry_point,
            'documentation': self.documentation,
            'total_lines': self.total_lines
        }


@dataclass
class TestArtifact:
    """Test artifact created by the tester."""
    test_framework: str
    test_code: str
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    coverage_report: Optional[Dict[str, Any]] = None
    performance_benchmarks: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'test_framework': self.test_framework,
            'test_code': self.test_code,
            'test_cases': self.test_cases,
            'coverage_report': self.coverage_report,
            'performance_benchmarks': self.performance_benchmarks
        }


@dataclass
class ReviewArtifact:
    """Review artifact created by the reviewer."""
    overall_score: float
    approved: bool
    code_quality_score: float
    test_quality_score: float
    design_adherence_score: float
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    human_feedback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'overall_score': self.overall_score,
            'approved': self.approved,
            'code_quality_score': self.code_quality_score,
            'test_quality_score': self.test_quality_score,
            'design_adherence_score': self.design_adherence_score,
            'issues': self.issues,
            'suggestions': self.suggestions,
            'human_feedback': self.human_feedback
        }


@dataclass
class VCSArtifact:
    """VCS operations artifact."""
    provider: str  # github, gitlab, etc.
    repository: str
    branch_name: str
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    pull_request_number: Optional[int] = None
    pull_request_url: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'provider': self.provider,
            'repository': self.repository,
            'branch_name': self.branch_name,
            'commit_sha': self.commit_sha,
            'commit_message': self.commit_message,
            'pull_request_number': self.pull_request_number,
            'pull_request_url': self.pull_request_url,
            'files_changed': self.files_changed
        }


class DevelopmentState(TypedDict):
    """
    State schema for the LangGraph development workflow.
    
    This TypedDict defines the complete state that flows through the workflow,
    including all artifacts, execution history, and metadata.
    """
    # Task information
    task: str
    requirements: List[str]
    context: Optional[Dict[str, Any]]
    
    # Workflow status
    status: WorkflowStatus
    current_agent: Optional[AgentRole]
    error: Optional[str]
    
    # Artifacts
    design: Optional[DesignArtifact]
    code: Optional[CodeArtifact]
    tests: Optional[TestArtifact]
    review: Optional[ReviewArtifact]
    vcs_operations: Optional[VCSArtifact]
    
    # Execution history
    agent_executions: List[AgentExecution]
    workflow_start_time: datetime
    workflow_end_time: Optional[datetime]
    
    # Safety and compliance
    safety_violations: List[Dict[str, Any]]
    policy_checks: List[Dict[str, Any]]
    
    # Telemetry
    events: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    
    # Human interaction
    human_feedback: Optional[str]
    human_approval_required: bool
    human_approval_received: bool


class StateManager:
    """Manages state transitions and validation for the development workflow."""
    
    def __init__(self):
        self.valid_transitions = {
            WorkflowStatus.INITIALIZING: [WorkflowStatus.DESIGN_IN_PROGRESS, WorkflowStatus.ERROR],
            WorkflowStatus.DESIGN_IN_PROGRESS: [WorkflowStatus.DESIGN_COMPLETE, WorkflowStatus.ERROR],
            WorkflowStatus.DESIGN_COMPLETE: [WorkflowStatus.IMPLEMENTATION_IN_PROGRESS, WorkflowStatus.ERROR],
            WorkflowStatus.IMPLEMENTATION_IN_PROGRESS: [WorkflowStatus.IMPLEMENTATION_COMPLETE, WorkflowStatus.ERROR],
            WorkflowStatus.IMPLEMENTATION_COMPLETE: [WorkflowStatus.TESTING_IN_PROGRESS, WorkflowStatus.ERROR],
            WorkflowStatus.TESTING_IN_PROGRESS: [WorkflowStatus.TESTING_COMPLETE, WorkflowStatus.ERROR],
            WorkflowStatus.TESTING_COMPLETE: [WorkflowStatus.REVIEW_IN_PROGRESS, WorkflowStatus.IMPLEMENTATION_IN_PROGRESS, WorkflowStatus.ERROR],
            WorkflowStatus.REVIEW_IN_PROGRESS: [WorkflowStatus.REVIEW_COMPLETE, WorkflowStatus.ERROR],
            WorkflowStatus.REVIEW_COMPLETE: [WorkflowStatus.VCS_IN_PROGRESS, WorkflowStatus.COMPLETE, WorkflowStatus.DESIGN_IN_PROGRESS, WorkflowStatus.ERROR],
            WorkflowStatus.VCS_IN_PROGRESS: [WorkflowStatus.COMPLETE, WorkflowStatus.ERROR],
            WorkflowStatus.COMPLETE: [],
            WorkflowStatus.ERROR: [WorkflowStatus.DESIGN_IN_PROGRESS, WorkflowStatus.IMPLEMENTATION_IN_PROGRESS, WorkflowStatus.TESTING_IN_PROGRESS],
            WorkflowStatus.CANCELLED: []
        }
    
    def can_transition(self, current_status: WorkflowStatus, new_status: WorkflowStatus) -> bool:
        """Check if a status transition is valid."""
        return new_status in self.valid_transitions.get(current_status, [])
    
    def transition_state(self, state: DevelopmentState, new_status: WorkflowStatus, 
                        agent_role: Optional[AgentRole] = None) -> DevelopmentState:
        """Transition state to new status with validation."""
        current_status = WorkflowStatus(state["status"])
        
        if not self.can_transition(current_status, new_status):
            raise ValueError(f"Invalid state transition: {current_status} -> {new_status}")
        
        # Update state
        state["status"] = new_status
        if agent_role:
            state["current_agent"] = agent_role
        
        # Record transition event
        transition_event = {
            "type": "state_transition",
            "timestamp": datetime.utcnow().isoformat(),
            "from_status": current_status.value,
            "to_status": new_status.value,
            "agent": agent_role.value if agent_role else None
        }
        state["events"].append(transition_event)
        
        return state
    
    def add_agent_execution(self, state: DevelopmentState, execution: AgentExecution) -> DevelopmentState:
        """Add agent execution to state history."""
        state["agent_executions"].append(execution)
        return state
    
    def add_safety_violation(self, state: DevelopmentState, violation: Dict[str, Any]) -> DevelopmentState:
        """Add safety violation to state."""
        state["safety_violations"].append(violation)
        return state
    
    def add_policy_check(self, state: DevelopmentState, check: Dict[str, Any]) -> DevelopmentState:
        """Add policy check result to state."""
        state["policy_checks"].append(check)
        return state
    
    def get_execution_summary(self, state: DevelopmentState) -> Dict[str, Any]:
        """Get execution summary from state."""
        executions = state.get("agent_executions", [])
        
        summary = {
            "total_executions": len(executions),
            "successful_executions": sum(1 for ex in executions if ex.success),
            "failed_executions": sum(1 for ex in executions if not ex.success),
            "total_retries": sum(ex.retry_count for ex in executions),
            "agents_used": list(set(ex.agent_role.value for ex in executions)),
            "total_duration": None
        }
        
        if state.get("workflow_start_time") and state.get("workflow_end_time"):
            duration = state["workflow_end_time"] - state["workflow_start_time"]
            summary["total_duration"] = duration.total_seconds()
        
        return summary
    
    def serialize_state(self, state: DevelopmentState) -> str:
        """Serialize state to JSON string."""
        serializable_state = {}
        
        for key, value in state.items():
            if key in ["workflow_start_time", "workflow_end_time"]:
                serializable_state[key] = value.isoformat() if value else None
            elif key == "agent_executions":
                serializable_state[key] = [ex.to_dict() for ex in value]
            elif hasattr(value, 'to_dict'):
                serializable_state[key] = value.to_dict()
            else:
                serializable_state[key] = value
        
        return json.dumps(serializable_state, indent=2)
    
    def deserialize_state(self, state_json: str) -> DevelopmentState:
        """Deserialize state from JSON string."""
        data = json.loads(state_json)
        
        # Convert datetime strings back to datetime objects
        if data.get("workflow_start_time"):
            data["workflow_start_time"] = datetime.fromisoformat(data["workflow_start_time"])
        if data.get("workflow_end_time"):
            data["workflow_end_time"] = datetime.fromisoformat(data["workflow_end_time"])
        
        # Convert agent executions
        if data.get("agent_executions"):
            executions = []
            for ex_data in data["agent_executions"]:
                execution = AgentExecution(
                    agent_role=AgentRole(ex_data["agent_role"]),
                    start_time=datetime.fromisoformat(ex_data["start_time"]),
                    end_time=datetime.fromisoformat(ex_data["end_time"]) if ex_data["end_time"] else None,
                    success=ex_data["success"],
                    output=ex_data["output"],
                    error=ex_data["error"],
                    retry_count=ex_data["retry_count"]
                )
                executions.append(execution)
            data["agent_executions"] = executions
        
        return DevelopmentState(**data)


def create_initial_state(task: str, requirements: List[str], 
                        context: Optional[Dict[str, Any]] = None) -> DevelopmentState:
    """Create initial state for a development task."""
    return DevelopmentState(
        # Task information
        task=task,
        requirements=requirements,
        context=context or {},
        
        # Workflow status
        status=WorkflowStatus.INITIALIZING,
        current_agent=None,
        error=None,
        
        # Artifacts (initially empty)
        design=None,
        code=None,
        tests=None,
        review=None,
        vcs_operations=None,
        
        # Execution history
        agent_executions=[],
        workflow_start_time=datetime.utcnow(),
        workflow_end_time=None,
        
        # Safety and compliance
        safety_violations=[],
        policy_checks=[],
        
        # Telemetry
        events=[],
        metrics={},
        
        # Human interaction
        human_feedback=None,
        human_approval_required=False,
        human_approval_received=False
    )


def validate_state(state: DevelopmentState) -> List[str]:
    """Validate state consistency and completeness."""
    errors = []
    
    # Check required fields
    if not state.get("task"):
        errors.append("Task description is required")
    
    if not isinstance(state.get("requirements", []), list):
        errors.append("Requirements must be a list")
    
    # Check status consistency
    status = WorkflowStatus(state["status"])
    
    if status == WorkflowStatus.DESIGN_COMPLETE and not state.get("design"):
        errors.append("Design artifact missing for DESIGN_COMPLETE status")
    
    if status == WorkflowStatus.IMPLEMENTATION_COMPLETE and not state.get("code"):
        errors.append("Code artifact missing for IMPLEMENTATION_COMPLETE status")
    
    if status == WorkflowStatus.TESTING_COMPLETE and not state.get("tests"):
        errors.append("Test artifact missing for TESTING_COMPLETE status")
    
    if status == WorkflowStatus.REVIEW_COMPLETE and not state.get("review"):
        errors.append("Review artifact missing for REVIEW_COMPLETE status")
    
    if status == WorkflowStatus.COMPLETE and not state.get("vcs_operations"):
        vcs_config = state.get("context", {}).get("vcs", {})
        if vcs_config.get("enabled", False):
            errors.append("VCS operations missing for COMPLETE status when VCS is enabled")
    
    # Check execution history consistency
    executions = state.get("agent_executions", [])
    for execution in executions:
        if execution.success and not execution.output:
            errors.append(f"Successful execution missing output: {execution.agent_role}")
        
        if not execution.success and not execution.error:
            errors.append(f"Failed execution missing error: {execution.agent_role}")
    
    return errors