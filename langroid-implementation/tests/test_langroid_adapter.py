"""
Comprehensive tests for Langroid adapter implementation.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from adapter import (
    LangroidAdapter, 
    create_langroid_adapter,
    SafeChatAgent,
    LANGROID_AVAILABLE,
    AGENTS_AVAILABLE
)
from common.agent_api import TaskSchema, TaskType, TaskStatus


class TestLangroidAdapter:
    """Test suite for LangroidAdapter."""
    
    @pytest.fixture
    def adapter_config(self):
        """Test configuration for adapter."""
        return {
            'language': 'python',
            'langroid': {
                'model': 'gpt-3.5-turbo'
            },
            'vcs': {
                'github': {
                    'enabled': True,
                    'token': 'test-token',
                    'owner': 'test-owner',
                    'repo': 'test-repo'
                }
            }
        }
    
    @pytest.fixture
    def sample_task(self):
        """Sample task for testing."""
        return TaskSchema(
            id='test-task-1',
            type=TaskType.FEATURE_ADD,
            inputs={
                'description': 'Create a conversation-based data processor',
                'requirements': [
                    'Process data through agent conversations',
                    'Include turn-taking logic',
                    'Add comprehensive logging'
                ],
                'context': {}
            },
            repo_path='.',
            vcs_provider='github'
        )
    
    def test_adapter_initialization(self, adapter_config):
        """Test adapter initialization."""
        adapter = LangroidAdapter(adapter_config)
        
        assert adapter.name == "Langroid Conversation Orchestrator"
        assert adapter.version == "2.0.0"
        assert adapter.description == "Conversation-style multi-agent interactions with turn-taking logic"
        assert adapter.config == adapter_config
    
    def test_factory_function(self, adapter_config):
        """Test factory function."""
        adapter = create_langroid_adapter(adapter_config)
        
        assert isinstance(adapter, LangroidAdapter)
        assert adapter.config == adapter_config
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, adapter_config):
        """Test capabilities reporting."""
        adapter = LangroidAdapter(adapter_config)
        capabilities = await adapter.get_capabilities()
        
        assert capabilities['name'] == adapter.name
        assert capabilities['version'] == adapter.version
        
        # Check required features
        required_features = [
            'conversation_style_interactions',
            'turn_taking_logic',
            'agent_role_specialization',
            'multi_agent_conversations'
        ]
        
        for feature in required_features:
            assert feature in capabilities['features']
        
        # Check agent architecture
        assert 'agent_architecture' in capabilities
        agent_arch = capabilities['agent_architecture']
        
        assert 'developer' in agent_arch
        assert 'reviewer' in agent_arch
        assert 'tester' in agent_arch
        
        # Check conversation features
        assert 'conversation_features' in capabilities
        conv_features = capabilities['conversation_features']
        
        assert conv_features['turn_taking'] is True
        assert conv_features['role_specialization'] is True
        assert conv_features['natural_language'] is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter_config):
        """Test health check functionality."""
        adapter = LangroidAdapter(adapter_config)
        health = await adapter.health_check()
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'components' in health
        
        # Check component statuses
        components = health['components']
        expected_components = [
            'langroid',
            'agents',
            'conversation_workflow',
            'sandbox',
            'filesystem_guard',
            'network_guard',
            'injection_guard',
            'github_provider',
            'gitlab_provider'
        ]
        
        for component in expected_components:
            assert component in components
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, adapter_config):
        """Test input sanitization."""
        adapter = LangroidAdapter(adapter_config)
        
        # Test normal input
        safe_input = await adapter._sanitize_input("normal input")
        assert safe_input == "normal input"
        
        # Test with injection guard disabled (should pass through)
        if not adapter.injection_guard:
            malicious_input = "SELECT * FROM users; DROP TABLE users;"
            safe_input = await adapter._sanitize_input(malicious_input)
            assert safe_input == malicious_input
    
    @pytest.mark.asyncio
    async def test_task_validation(self, adapter_config, sample_task):
        """Test task validation and sanitization."""
        adapter = LangroidAdapter(adapter_config)
        
        validated_task = await adapter._validate_task(sample_task)
        
        assert validated_task.id == sample_task.id
        assert validated_task.type == sample_task.type
        assert validated_task.inputs['description'] == sample_task.inputs['description']
        assert len(validated_task.inputs['requirements']) == len(sample_task.inputs['requirements'])
    
    @pytest.mark.asyncio
    async def test_conversation_workflow_fallback(self, adapter_config):
        """Test conversation workflow fallback mode."""
        adapter = LangroidAdapter(adapter_config)
        
        # Test fallback workflow
        result = adapter._run_fallback_workflow(
            "Test conversation task",
            ["Requirement 1", "Requirement 2"]
        )
        
        assert result['success'] is True
        assert result['fallback'] is True
        assert 'conversation_log' in result
        assert 'agents_used' in result
        assert 'conversation_turns' in result
        
        # Check agents used
        expected_agents = ['developer', 'reviewer', 'tester']
        for agent in expected_agents:
            assert agent in result['agents_used']
    
    @pytest.mark.asyncio
    async def test_vcs_operations(self, adapter_config, sample_task):
        """Test VCS operations."""
        adapter = LangroidAdapter(adapter_config)
        
        workflow_result = {
            'implementation': 'def main(): pass',
            'tests': 'def test_main(): assert True',
            'agents_used': ['developer', 'reviewer', 'tester'],
            'conversation_turns': 5
        }
        
        # Test with VCS disabled
        adapter.config['vcs'] = {'enabled': False}
        vcs_result = await adapter._handle_vcs_operations(sample_task, workflow_result)
        assert vcs_result['status'] == 'skipped'
        assert vcs_result['reason'] == 'vcs_not_enabled'
        
        # Test with VCS enabled but no provider
        adapter.config['vcs'] = {'enabled': True}
        adapter.github_provider = None
        adapter.gitlab_provider = None
        vcs_result = await adapter._handle_vcs_operations(sample_task, workflow_result)
        assert vcs_result['status'] == 'failed'
        assert vcs_result['reason'] == 'no_provider_available'
    
    @pytest.mark.asyncio
    async def test_file_extraction(self, adapter_config):
        """Test file extraction from workflow results."""
        adapter = LangroidAdapter(adapter_config)
        
        workflow_result = {
            'implementation': 'def main(): print("Hello Langroid")',
            'tests': 'def test_main(): assert True',
            'architecture': 'Conversation-based architecture',
            'conversation_log': 'Agent conversation log',
            'agents_used': ['developer', 'reviewer', 'tester']
        }
        
        files = adapter._extract_files_from_result(workflow_result)
        
        assert 'main.py' in files
        assert 'test_main.py' in files
        assert 'ARCHITECTURE.md' in files
        assert 'CONVERSATION_LOG.md' in files
        assert 'AGENTS.md' in files
        
        # Check content
        assert 'Hello Langroid' in files['main.py']
        assert 'assert True' in files['test_main.py']
    
    @pytest.mark.asyncio
    async def test_run_task_success(self, adapter_config, sample_task):
        """Test successful task execution."""
        adapter = LangroidAdapter(adapter_config)
        
        results = []
        async for item in adapter.run_task(sample_task):
            results.append(item)
        
        # Should have start event, completion event, and result
        assert len(results) >= 2
        
        # Find the RunResult
        run_result = None
        for item in results:
            if hasattr(item, 'status'):
                run_result = item
                break
        
        assert run_result is not None
        assert run_result.status == TaskStatus.COMPLETED
        assert 'output' in run_result.artifacts
        
        # Check metadata
        metadata = run_result.metadata
        assert 'agents_used' in metadata
        assert 'conversation_turns' in metadata
        assert 'conversation_style' in metadata
        assert metadata['conversation_style'] == 'turn_taking'
    
    @pytest.mark.asyncio
    async def test_run_task_with_error(self, adapter_config):
        """Test task execution with error."""
        adapter = LangroidAdapter(adapter_config)
        
        # Create invalid task
        invalid_task = TaskSchema(
            id='invalid-task',
            type=TaskType.FEATURE_ADD,
            inputs={},  # Missing required fields
            repo_path='.',
            vcs_provider='github'
        )
        
        results = []
        async for item in adapter.run_task(invalid_task):
            results.append(item)
        
        # Should handle gracefully and return results
        assert len(results) >= 1
    
    def test_output_formatting(self, adapter_config):
        """Test workflow output formatting."""
        adapter = LangroidAdapter(adapter_config)
        
        workflow_result = {
            'architecture': 'Test architecture' * 100,  # Long text
            'implementation': 'def main(): pass',
            'tests': 'def test_main(): assert True',
            'conversation_log': 'Agent conversation' * 50,  # Long text
            'agents_used': ['developer', 'reviewer'],
            'conversation_turns': 3
        }
        
        formatted = adapter._format_workflow_output(workflow_result)
        
        assert 'Architecture' in formatted
        assert 'Implementation' in formatted
        assert 'Tests' in formatted
        assert 'Conversation Log' in formatted
        assert 'Agents: developer, reviewer' in formatted
        assert 'Conversation turns: 3' in formatted


class TestSafeChatAgent:
    """Test suite for SafeChatAgent wrapper."""
    
    @pytest.fixture
    def mock_agent(self):
        """Mock Langroid agent."""
        agent = Mock()
        agent.llm_response_async = AsyncMock(return_value="Mock response")
        return agent
    
    @pytest.fixture
    def mock_policy(self):
        """Mock safety policy."""
        policy = Mock()
        policy.execution.enabled = True
        return policy
    
    def test_safe_agent_initialization(self, mock_agent, mock_policy):
        """Test SafeChatAgent initialization."""
        safe_agent = SafeChatAgent(mock_agent, mock_policy)
        
        assert safe_agent.agent == mock_agent
        assert safe_agent.safety_policy == mock_policy
        assert safe_agent.conversation_count == 0
    
    @pytest.mark.asyncio
    async def test_safe_response(self, mock_agent, mock_policy):
        """Test safe response generation."""
        safe_agent = SafeChatAgent(mock_agent, mock_policy)
        
        response = await safe_agent.respond_safe("Test message")
        
        assert response == "Mock response"
        assert safe_agent.conversation_count == 1
        mock_agent.llm_response_async.assert_called_once_with("Test message")


class TestConversationWorkflow:
    """Test suite for conversation workflow components."""
    
    def test_mock_workflow_creation(self):
        """Test mock conversation workflow creation."""
        from adapter import MockConversationWorkflow
        
        mock_agents = {
            'developer': Mock(),
            'reviewer': Mock(),
            'tester': Mock()
        }
        
        workflow = MockConversationWorkflow(mock_agents)
        assert workflow.agents == mock_agents
    
    @pytest.mark.asyncio
    async def test_mock_workflow_execution(self):
        """Test mock conversation workflow execution."""
        from adapter import MockConversationWorkflow
        
        mock_agents = {
            'developer': Mock(),
            'reviewer': Mock(),
            'tester': Mock()
        }
        
        workflow = MockConversationWorkflow(mock_agents)
        result = await workflow.execute_development_conversation(
            "Test task",
            ["Requirement 1", "Requirement 2"],
            "python"
        )
        
        assert result['success'] is True
        assert result['fallback'] is False
        assert 'conversation_log' in result
        assert 'agents_used' in result
        assert 'conversation_turns' in result


@pytest.mark.integration
class TestLangroidIntegration:
    """Integration tests for Langroid adapter."""
    
    @pytest.mark.skipif(not LANGROID_AVAILABLE, reason="Langroid not available")
    @pytest.mark.asyncio
    async def test_real_langroid_integration(self):
        """Test with real Langroid if available."""
        config = {
            'langroid': {
                'model': 'gpt-3.5-turbo'
            }
        }
        
        adapter = LangroidAdapter(config)
        
        # Test capabilities
        capabilities = await adapter.get_capabilities()
        assert 'conversation_style_interactions' in capabilities['features']
        
        # Test health check
        health = await adapter.health_check()
        assert 'langroid' in health['components']
    
    @pytest.mark.skipif(not AGENTS_AVAILABLE, reason="Langroid agents not available")
    def test_real_agents_integration(self):
        """Test with real Langroid agents if available."""
        # This would test actual Langroid agent creation
        # when the full Langroid API is available
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])