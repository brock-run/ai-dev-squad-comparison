"""
Comprehensive tests for LangGraph Adapter

This test suite validates the LangGraph adapter implementation
including safety controls, VCS integration, and workflow execution.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

# Mock the dependencies that might not be available
import sys
from unittest.mock import MagicMock

# Mock LangGraph components
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()
sys.modules['langgraph.checkpoint'] = MagicMock()
sys.modules['langgraph.checkpoint.memory'] = MagicMock()
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.messages'] = MagicMock()
sys.modules['langchain_community'] = MagicMock()
sys.modules['langchain_community.chat_models'] = MagicMock()

# Create a proper base class for AgentAdapter
class MockAgentAdapter:
    def __init__(self, config=None):
        pass

# Mock modules with proper AgentAdapter
common_agent_api_mock = MagicMock()
common_agent_api_mock.AgentAdapter = MockAgentAdapter
common_agent_api_mock.RunResult = MagicMock()
common_agent_api_mock.Event = MagicMock()
common_agent_api_mock.TaskSchema = MagicMock()
common_agent_api_mock.EventStream = MagicMock()

# Mock common modules
sys.modules['common.agent_api'] = common_agent_api_mock
sys.modules['common.safety'] = MagicMock()
sys.modules['common.safety.policy'] = MagicMock()
sys.modules['common.safety.execute'] = MagicMock()
sys.modules['common.safety.fs'] = MagicMock()
sys.modules['common.safety.net'] = MagicMock()
sys.modules['common.safety.injection'] = MagicMock()
sys.modules['common.safety.config_integration'] = MagicMock()
sys.modules['common.vcs'] = MagicMock()
sys.modules['common.vcs.base'] = MagicMock()
sys.modules['common.vcs.github'] = MagicMock()
sys.modules['common.vcs.gitlab'] = MagicMock()
sys.modules['common.vcs.commit_msgs'] = MagicMock()
sys.modules['common.config'] = MagicMock()

# Now import the adapter
sys.path.append(str(Path(__file__).parent.parent))
from adapter import LangGraphAdapter
from state.development_state import (
    DevelopmentState, WorkflowStatus, AgentRole,
    create_initial_state, StateManager
)


class TestLangGraphAdapter:
    """Test cases for LangGraphAdapter."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {
            'language': 'python',
            'vcs': {
                'enabled': True,
                'repository': 'test/repo'
            },
            'human_review': {
                'enabled': False
            }
        }
    
    @pytest.fixture
    def adapter(self, mock_config):
        """Create adapter instance with mocked dependencies."""
        with patch('adapter.LANGGRAPH_AVAILABLE', True):
            with patch('adapter.get_policy_manager') as mock_policy:
                with patch('adapter.get_config_manager') as mock_config_manager:
                    # Create a proper mock policy
                    mock_active_policy = Mock()
                    mock_active_policy.execution.enabled = True
                    mock_active_policy.execution.sandbox_type = 'docker'
                    mock_active_policy.filesystem = None
                    mock_active_policy.network = None
                    mock_active_policy.injection_patterns = []
                    
                    mock_policy_manager = Mock()
                    mock_policy_manager.get_active_policy.return_value = mock_active_policy
                    mock_policy_manager.set_active_policy.return_value = None
                    mock_policy.return_value = mock_policy_manager
                    mock_config_manager.return_value.config = mock_config
                    adapter = LangGraphAdapter(mock_config)
                    return adapter
    
    def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.name == "LangGraph Multi-Agent Squad"
        assert adapter.version == "2.0.0"
        assert adapter.description is not None
    
    @pytest.mark.asyncio
    async def test_capabilities(self, adapter):
        """Test get_capabilities method."""
        capabilities = await adapter.get_capabilities()
        
        assert 'name' in capabilities
        assert 'version' in capabilities
        assert 'features' in capabilities
        assert 'safety_features' in capabilities
        assert 'vcs_providers' in capabilities
        
        # Check required features
        required_features = [
            'multi_agent_collaboration',
            'safety_controls',
            'vcs_integration',
            'automated_testing',
            'code_review'
        ]
        
        for feature in required_features:
            assert feature in capabilities['features']
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health_check method."""
        health = await adapter.health_check()
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'components' in health
        
        # Check component status
        assert 'langgraph' in health['components']
        assert 'workflow' in health['components']
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, adapter):
        """Test input sanitization."""
        # Test normal input
        safe_input = await adapter._sanitize_input("print('hello world')")
        assert safe_input == "print('hello world')"
        
        # Test with injection guard disabled
        adapter.injection_guard = None
        safe_input = await adapter._sanitize_input("any input")
        assert safe_input == "any input"
    
    @pytest.mark.asyncio
    async def test_code_validation(self, adapter):
        """Test code validation."""
        # Test safe code
        safe_code = "def add(a, b): return a + b"
        validated = await adapter._validate_code(safe_code)
        assert validated == safe_code
        
        # Test potentially dangerous code (should still pass but log warning)
        dangerous_code = "exec('print(1)')"
        validated = await adapter._validate_code(dangerous_code)
        assert validated == dangerous_code  # Still returns code but logs warning
    
    @pytest.mark.asyncio
    async def test_design_creation(self, adapter):
        """Test design creation."""
        task = "Create a calculator"
        requirements = ["Add function", "Subtract function"]
        
        design = await adapter._create_design(task, requirements)
        
        assert 'architecture_type' in design
        assert 'components' in design
        assert 'interfaces' in design
        assert len(design['components']) >= 3  # Should have main, utils, tests
    
    @pytest.mark.asyncio
    async def test_code_implementation(self, adapter):
        """Test code implementation."""
        from state.development_state import DesignArtifact
        
        design = DesignArtifact(
            architecture_type="modular",
            components=[{"name": "main", "type": "core"}]
        )
        
        code_result = await adapter._implement_code("Create calculator", design, "python")
        
        assert 'language' in code_result
        assert 'main_code' in code_result
        assert 'supporting_files' in code_result
        assert code_result['language'] == 'python'
        assert len(code_result['main_code']) > 0
    
    @pytest.mark.asyncio
    async def test_test_creation(self, adapter):
        """Test test creation."""
        from state.development_state import CodeArtifact
        
        code_artifact = CodeArtifact(
            language="python",
            main_code="def add(a, b): return a + b"
        )
        
        test_result = await adapter._create_tests(code_artifact, "Calculator", [])
        
        assert 'test_framework' in test_result
        assert 'test_code' in test_result
        assert 'test_cases' in test_result
        assert test_result['test_framework'] == 'unittest'
    
    @pytest.mark.asyncio
    async def test_automated_review(self, adapter):
        """Test automated review."""
        from state.development_state import CodeArtifact, TestArtifact
        
        state = create_initial_state("Test task", [])
        state["code"] = CodeArtifact(
            language="python",
            main_code="def test(): pass",
            documentation="Test documentation"
        )
        state["tests"] = TestArtifact(
            test_framework="unittest",
            test_code="test code",
            test_cases=[{"name": "test1"}, {"name": "test2"}]
        )
        
        review = await adapter._automated_review(state)
        
        assert 'overall_score' in review
        assert 'approved' in review
        assert 'code_quality_score' in review
        assert 'test_quality_score' in review
        assert isinstance(review['overall_score'], float)
    
    def test_conditional_edges(self, adapter):
        """Test conditional edge functions."""
        # Test should_continue_to_developer
        state = create_initial_state("Test", [])
        state["status"] = WorkflowStatus.DESIGN_COMPLETE
        state["design"] = {"type": "test"}
        
        # This would be async in real implementation
        # result = await adapter._should_continue_to_developer(state)
        # assert result == "continue"
        
        # Test error state
        state["status"] = WorkflowStatus.ERROR
        # result = await adapter._should_continue_to_developer(state)
        # assert result == "error"
    
    @pytest.mark.asyncio
    async def test_vcs_operations(self, adapter):
        """Test VCS operation helpers."""
        state = create_initial_state("Test task", [])
        
        # Test branch creation
        branch = await adapter._create_feature_branch(state)
        assert branch.startswith("feature/langgraph-")
        assert "test-task" in branch
        
        # Test commit message generation
        message = await adapter._generate_commit_message(state)
        assert message.startswith("feat:")
        assert "Test task" in message
        
        # Test commit changes (mock)
        commit_result = await adapter._commit_changes(state, branch, message)
        assert 'sha' in commit_result
        assert 'message' in commit_result
        
        # Test PR creation (mock)
        pr_result = await adapter._create_pull_request(state, branch)
        assert 'number' in pr_result
        assert 'url' in pr_result


class TestDevelopmentState:
    """Test cases for DevelopmentState and related classes."""
    
    def test_initial_state_creation(self):
        """Test initial state creation."""
        state = create_initial_state("Test task", ["req1", "req2"])
        
        assert state["task"] == "Test task"
        assert state["requirements"] == ["req1", "req2"]
        assert state["status"] == WorkflowStatus.INITIALIZING
        assert isinstance(state["workflow_start_time"], datetime)
        assert state["agent_executions"] == []
    
    def test_state_manager_transitions(self):
        """Test state manager transitions."""
        manager = StateManager()
        state = create_initial_state("Test", [])
        
        # Test valid transition
        assert manager.can_transition(WorkflowStatus.INITIALIZING, WorkflowStatus.DESIGN_IN_PROGRESS)
        
        # Test invalid transition
        assert not manager.can_transition(WorkflowStatus.INITIALIZING, WorkflowStatus.COMPLETE)
        
        # Test state transition
        new_state = manager.transition_state(
            state, 
            WorkflowStatus.DESIGN_IN_PROGRESS, 
            AgentRole.ARCHITECT
        )
        assert new_state["status"] == WorkflowStatus.DESIGN_IN_PROGRESS
        assert new_state["current_agent"] == AgentRole.ARCHITECT
        assert len(new_state["events"]) > 0
    
    def test_agent_execution_tracking(self):
        """Test agent execution tracking."""
        from state.development_state import AgentExecution
        
        execution = AgentExecution(
            agent_role=AgentRole.ARCHITECT,
            start_time=datetime.utcnow()
        )
        
        assert execution.agent_role == AgentRole.ARCHITECT
        assert execution.success == False  # Default
        assert execution.duration_seconds is None  # No end time yet
        
        # Complete execution
        execution.end_time = datetime.utcnow()
        execution.success = True
        
        assert execution.duration_seconds is not None
        assert execution.duration_seconds >= 0
    
    def test_artifact_serialization(self):
        """Test artifact serialization."""
        from state.development_state import DesignArtifact, CodeArtifact
        
        # Test DesignArtifact
        design = DesignArtifact(
            architecture_type="modular",
            components=[{"name": "test", "type": "core"}]
        )
        design_dict = design.to_dict()
        assert design_dict["architecture_type"] == "modular"
        assert len(design_dict["components"]) == 1
        
        # Test CodeArtifact
        code = CodeArtifact(
            language="python",
            main_code="def test(): pass\ndef test2(): pass"
        )
        code_dict = code.to_dict()
        assert code_dict["language"] == "python"
        assert code_dict["total_lines"] == 2


# Integration tests
class TestLangGraphIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.mark.asyncio
    async def test_workflow_state_flow(self):
        """Test the complete workflow state flow."""
        # This would test the actual LangGraph workflow execution
        # but requires LangGraph to be installed
        pass
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in workflow."""
        # Test error recovery and state management
        pass
    
    @pytest.mark.asyncio
    async def test_safety_integration(self):
        """Test safety controls integration."""
        # Test that safety controls are properly integrated
        pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])