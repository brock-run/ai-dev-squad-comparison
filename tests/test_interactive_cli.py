"""Tests for Interactive CLI

Tests the interactive mismatch resolution CLI functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from io import StringIO

from common.phase2.cli_interactive import InteractiveCLI, ResolutionChoice
from common.phase2.models import Mismatch, ResolutionPlan, ResolutionAction
from common.phase2.enums import MismatchType, MismatchStatus, ResolutionStatus, ResolutionActionType, SafetyLevel


@pytest.fixture
def sample_mismatch():
    """Create a sample mismatch for testing."""
    return Mismatch(
        id="test_mismatch_001",
        run_id="test_run_001",
        artifact_ids=["artifact_001", "artifact_002"],
        mismatch_type=MismatchType.WHITESPACE,
        detectors=["whitespace_detector"],
        evidence={
            "diff_summary": "Extra whitespace in line 42",
            "diff_content": "- def hello():\n+ def hello(): \n",
            "cost_estimate": 0.001,
            "latency_ms": 50
        },
        status=MismatchStatus.DETECTED,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_resolution_plan():
    """Create a sample resolution plan for testing."""
    action = ResolutionAction(
        type=ResolutionActionType.NORMALIZE_WHITESPACE,
        target_artifact_id="artifact_001",
        transformation="remove_trailing_whitespace",
        parameters={"target_file": "test.py", "line": 42}
    )
    
    return ResolutionPlan(
        mismatch_id="test_mismatch_001",
        strategy="whitespace_normalization",
        actions=[action],
        confidence=0.95,
        safety_level=SafetyLevel.SAFE,
        estimated_impact={
            "risk_level": "low",
            "files_changed": 1,
            "lines_changed": 1,
            "rollback_available": True,
            "warnings": []
        }
    )


@pytest.fixture
def mock_components():
    """Create mock components for testing."""
    resolution_engine = Mock()
    equivalence_runner = Mock()
    telemetry_logger = Mock()
    
    return resolution_engine, equivalence_runner, telemetry_logger


class TestInteractiveCLI:
    """Test cases for InteractiveCLI."""
    
    def test_init(self, mock_components):
        """Test CLI initialization."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger,
            auto_approve_safe=True
        )
        
        assert cli.resolution_engine == resolution_engine
        assert cli.equivalence_runner == equivalence_runner
        assert cli.telemetry_logger == telemetry_logger
        assert cli.auto_approve_safe == True
        assert cli.stats["total_reviewed"] == 0
    
    def test_display_mismatch_plain_text(self, mock_components, sample_mismatch):
        """Test mismatch display in plain text mode."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        cli.console = None  # Force plain text mode
        
        with patch('builtins.print') as mock_print:
            cli.display_mismatch(sample_mismatch)
            
            # Check that print was called with mismatch details
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("test_mismatch_001" in str(call) for call in print_calls)
            assert any("whitespace" in str(call) for call in print_calls)
            assert any("0.95" in str(call) for call in print_calls)
    
    def test_display_resolution_plan_plain_text(self, mock_components, sample_resolution_plan):
        """Test resolution plan display in plain text mode."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        cli.console = None  # Force plain text mode
        
        with patch('builtins.print') as mock_print:
            cli.display_resolution_plan(sample_resolution_plan)
            
            # Check that print was called with plan details
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("whitespace_normalization" in str(call) for call in print_calls)
            assert any("0.95" in str(call) for call in print_calls)
            assert any("safe" in str(call) for call in print_calls)
    
    def test_auto_approve_safe_resolution(self, mock_components, sample_mismatch, sample_resolution_plan):
        """Test auto-approval of safe resolutions."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger,
            auto_approve_safe=True
        )
        
        # Mock print to avoid output during test
        with patch.object(cli, 'print'):
            choice = cli.get_user_choice(sample_mismatch, sample_resolution_plan)
        
        assert choice.action == "approve"
        assert choice.confidence == 1.0
    
    def test_user_choice_approve(self, mock_components, sample_mismatch, sample_resolution_plan):
        """Test user choosing to approve a resolution."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger,
            auto_approve_safe=False  # Disable auto-approval
        )
        
        with patch.object(cli, 'print'), \
             patch.object(cli, 'input', return_value="approve"):
            
            choice = cli.get_user_choice(sample_mismatch, sample_resolution_plan)
        
        assert choice.action == "approve"
        assert choice.confidence == 1.0
    
    def test_user_choice_reject(self, mock_components, sample_mismatch, sample_resolution_plan):
        """Test user choosing to reject a resolution."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger,
            auto_approve_safe=False
        )
        
        with patch.object(cli, 'print'), \
             patch.object(cli, 'input', side_effect=["reject", "Not confident in AI suggestion"]):
            
            choice = cli.get_user_choice(sample_mismatch, sample_resolution_plan)
        
        assert choice.action == "reject"
        assert choice.feedback == "Not confident in AI suggestion"
    
    def test_user_choice_skip(self, mock_components, sample_mismatch, sample_resolution_plan):
        """Test user choosing to skip a resolution."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger,
            auto_approve_safe=False
        )
        
        with patch.object(cli, 'print'), \
             patch.object(cli, 'input', return_value="skip"):
            
            choice = cli.get_user_choice(sample_mismatch, sample_resolution_plan)
        
        assert choice.action == "skip"
    
    def test_apply_resolution_approve_success(self, mock_components, sample_mismatch):
        """Test successful resolution application."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        # Mock successful resolution
        mock_result = Mock()
        mock_result.status = ResolutionStatus.COMPLETED
        resolution_engine.execute_resolution_plan.return_value = mock_result
        resolution_engine.generate_resolution_plan.return_value = Mock()
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        
        choice = ResolutionChoice(action="approve")
        
        with patch.object(cli, 'print'):
            success = cli.apply_resolution(sample_mismatch, choice)
        
        assert success == True
        resolution_engine.generate_resolution_plan.assert_called_once_with(sample_mismatch)
        resolution_engine.execute_resolution_plan.assert_called_once()
    
    def test_apply_resolution_approve_failure(self, mock_components, sample_mismatch):
        """Test failed resolution application."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        # Mock failed resolution
        mock_result = Mock()
        mock_result.status = ResolutionStatus.FAILED
        mock_result.error_message = "Test error"
        resolution_engine.execute_resolution_plan.return_value = mock_result
        resolution_engine.generate_resolution_plan.return_value = Mock()
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        
        choice = ResolutionChoice(action="approve")
        
        with patch.object(cli, 'print'):
            success = cli.apply_resolution(sample_mismatch, choice)
        
        assert success == False
    
    def test_apply_resolution_reject(self, mock_components, sample_mismatch):
        """Test rejecting a resolution."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        
        choice = ResolutionChoice(action="reject")
        
        with patch.object(cli, 'print'):
            success = cli.apply_resolution(sample_mismatch, choice)
        
        assert success == False
        # Should not call resolution engine for rejected resolutions
        resolution_engine.execute_resolution_plan.assert_not_called()
    
    def test_log_user_interaction(self, mock_components, sample_mismatch):
        """Test logging of user interactions."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        
        choice = ResolutionChoice(action="approve", confidence=0.9, feedback="Looks good")
        
        cli.log_user_interaction(sample_mismatch, choice, success=True)
        
        # Check that telemetry was logged
        telemetry_logger.log_event.assert_called_once()
        call_args = telemetry_logger.log_event.call_args
        
        assert call_args[0][0] == "user_resolution_interaction"
        event_data = call_args[0][1]
        assert event_data["mismatch_id"] == sample_mismatch.id
        assert event_data["user_action"] == "approve"
        assert event_data["user_confidence"] == 0.9
        assert event_data["feedback"] == "Looks good"
        assert event_data["success"] == True
    
    def test_process_mismatch_success(self, mock_components, sample_mismatch, sample_resolution_plan):
        """Test successful mismatch processing."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        # Mock successful resolution
        resolution_engine.generate_resolution_plan.return_value = sample_resolution_plan
        mock_result = Mock()
        mock_result.status = ResolutionStatus.COMPLETED
        resolution_engine.execute_resolution_plan.return_value = mock_result
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger,
            auto_approve_safe=True  # Enable auto-approval for test
        )
        
        with patch.object(cli, 'display_mismatch'), \
             patch.object(cli, 'display_resolution_plan'), \
             patch.object(cli, 'display_impact_analysis'), \
             patch.object(cli, 'print'):
            
            success = cli.process_mismatch(sample_mismatch)
        
        assert success == True
        assert cli.stats["total_reviewed"] == 1
        assert cli.stats["approved"] == 1
        assert cli.stats["auto_approved"] == 1
    
    def test_process_mismatches_empty_list(self, mock_components):
        """Test processing empty mismatch list."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        
        with patch.object(cli, 'print'):
            summary = cli.process_mismatches([])
        
        assert summary["total_reviewed"] == 0
        assert summary["success_rate"] == 0
    
    def test_get_summary(self, mock_components):
        """Test summary generation."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        
        # Simulate some processing
        cli.stats["total_reviewed"] = 10
        cli.stats["approved"] = 6
        cli.stats["modified"] = 2
        cli.stats["rejected"] = 1
        cli.stats["skipped"] = 1
        cli.stats["auto_approved"] = 4
        
        summary = cli.get_summary()
        
        assert summary["total_reviewed"] == 10
        assert summary["approved"] == 6
        assert summary["modified"] == 2
        assert summary["rejected"] == 1
        assert summary["skipped"] == 1
        assert summary["auto_approved"] == 4
        assert summary["success_rate"] == 0.8  # (6 + 2) / 10
    
    def test_display_summary_plain_text(self, mock_components):
        """Test summary display in plain text mode."""
        resolution_engine, equivalence_runner, telemetry_logger = mock_components
        
        cli = InteractiveCLI(
            resolution_engine=resolution_engine,
            equivalence_runner=equivalence_runner,
            telemetry_logger=telemetry_logger
        )
        cli.console = None  # Force plain text mode
        
        summary = {
            "total_reviewed": 5,
            "approved": 3,
            "modified": 1,
            "rejected": 1,
            "skipped": 0,
            "auto_approved": 2,
            "success_rate": 0.8
        }
        
        with patch('builtins.print') as mock_print:
            cli.display_summary(summary)
            
            # Check that summary was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Total Reviewed: 5" in str(call) for call in print_calls)
            assert any("80.0%" in str(call) for call in print_calls)


class TestResolutionChoice:
    """Test cases for ResolutionChoice."""
    
    def test_resolution_choice_creation(self):
        """Test ResolutionChoice creation."""
        choice = ResolutionChoice(
            action="approve",
            feedback="Looks good",
            confidence=0.9
        )
        
        assert choice.action == "approve"
        assert choice.feedback == "Looks good"
        assert choice.confidence == 0.9
        assert choice.modified_plan is None
    
    def test_resolution_choice_with_modified_plan(self, sample_resolution_plan):
        """Test ResolutionChoice with modified plan."""
        choice = ResolutionChoice(
            action="modify",
            modified_plan=sample_resolution_plan,
            feedback="Changed parameters",
            confidence=0.8
        )
        
        assert choice.action == "modify"
        assert choice.modified_plan == sample_resolution_plan
        assert choice.feedback == "Changed parameters"
        assert choice.confidence == 0.8


if __name__ == "__main__":
    pytest.main([__file__])