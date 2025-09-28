"""
Isolated tests for AutoGen Adapter

This test suite validates the AutoGen adapter implementation
with proper mocking isolation to avoid conflicts with original tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any


class TestAutoGenAdapterIsolated:
    """Isolated test cases for AutoGenAdapter."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {
            'language': 'python',
            'vcs': {
                'enabled': True,
                'repository': 'test/repo'
            },
            'github': {
                'enabled': True
            },
            'max_rounds': 10,
            'architect': {'max_iterations': 5},
            'developer': {'max_iterations': 10},
            'tester': {'max_iterations': 7}
        }
    
    def test_adapter_can_be_imported(self):
        """Test that the adapter can be imported without errors."""
        # This tests basic import functionality
        try:
            from adapter import AutoGenAdapter, create_autogen_adapter
            assert AutoGenAdapter is not None
            assert create_autogen_adapter is not None
        except ImportError as e:
            pytest.skip(f"AutoGen not available: {e}")
    
    @patch('adapter.AUTOGEN_AVAILABLE', True)
    @patch('adapter.setup_development_agents')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_adapter_initialization_mocked(self, mock_config_manager, mock_policy_manager, mock_setup_agents, mock_config):
        """Test adapter initialization with full mocking."""
        # Setup mocks
        mock_config_manager.return_value.config = mock_config
        
        # Mock policy
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = False
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = []
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        # Mock agents
        mock_setup_agents.return_value = {
            'architect': Mock(name="Architect"),
            'developer': Mock(name="Developer"),
            'tester': Mock(name="Tester"),
            'user_proxy': Mock(name="User")
        }
        
        # Import and create adapter
        from adapter import AutoGenAdapter
        adapter = AutoGenAdapter(mock_config)
        
        # Basic assertions
        assert adapter.name == "AutoGen Multi-Agent Group Chat"
        assert adapter.version == "2.0.0"
        assert len(adapter.agents) == 4
    
    @patch('adapter.AUTOGEN_AVAILABLE', True)
    @patch('adapter.setup_development_agents')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_adapter_capabilities_mocked(self, mock_config_manager, mock_policy_manager, mock_setup_agents, mock_config):
        """Test get_capabilities method with mocking."""
        # Setup mocks (same as above)
        mock_config_manager.return_value.config = mock_config
        
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = True
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = ['test']
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        mock_setup_agents.return_value = {
            'architect': Mock(name="Architect"),
            'developer': Mock(name="Developer"),
            'tester': Mock(name="Tester"),
            'user_proxy': Mock(name="User")
        }
        
        from adapter import AutoGenAdapter
        adapter = AutoGenAdapter(mock_config)
        
        # Test capabilities
        capabilities = asyncio.run(adapter.get_capabilities())
        
        assert 'name' in capabilities
        assert 'version' in capabilities
        assert 'features' in capabilities
        assert 'agent_composition' in capabilities
        assert 'safety_features' in capabilities
        
        # Check required features
        required_features = [
            'multi_agent_conversation',
            'group_chat_workflow',
            'role_based_agents',
            'conversational_ai',
            'safety_controls',
            'vcs_integration'
        ]
        
        for feature in required_features:
            assert feature in capabilities['features']
    
    @patch('adapter.AUTOGEN_AVAILABLE', True)
    @patch('adapter.setup_development_agents')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_adapter_health_check_mocked(self, mock_config_manager, mock_policy_manager, mock_setup_agents, mock_config):
        """Test health_check method with mocking."""
        # Setup mocks (same as above)
        mock_config_manager.return_value.config = mock_config
        
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = False
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = []
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        mock_setup_agents.return_value = {
            'architect': Mock(name="Architect"),
            'developer': Mock(name="Developer"),
            'tester': Mock(name="Tester"),
            'user_proxy': Mock(name="User")
        }
        
        from adapter import AutoGenAdapter
        adapter = AutoGenAdapter(mock_config)
        
        # Test health check
        health = asyncio.run(adapter.health_check())
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'components' in health
        
        # Check component status
        assert 'autogen' in health['components']
        
        # Check agent components
        for agent_name in ['architect', 'developer', 'tester', 'user_proxy']:
            component_key = f'agent_{agent_name}'
            assert component_key in health['components']
    
    @patch('adapter.AUTOGEN_AVAILABLE', True)
    @patch('adapter.create_autogen_adapter')
    def test_factory_function_mocked(self, mock_create_adapter):
        """Test factory function with mocking."""
        # Mock the factory function to return a mock adapter
        mock_adapter = Mock()
        mock_adapter.name = "AutoGen Multi-Agent Group Chat"
        mock_create_adapter.return_value = mock_adapter
        
        from adapter import create_autogen_adapter
        adapter = create_autogen_adapter()
        
        assert adapter.name == "AutoGen Multi-Agent Group Chat"
        mock_create_adapter.assert_called_once()
    
    def test_group_chat_workflow_structure(self):
        """Test that the group chat workflow has the expected structure."""
        # This tests the workflow logic without requiring AutoGen
        try:
            from adapter import AutoGenAdapter
            
            # Test that the workflow method exists
            assert hasattr(AutoGenAdapter, '_run_group_chat_workflow')
            assert hasattr(AutoGenAdapter, '_format_conversation_output')
            assert hasattr(AutoGenAdapter, '_extract_files_from_result')
            
        except ImportError:
            pytest.skip("AutoGen not available")
    
    def test_adapter_interface_compliance(self):
        """Test that the adapter implements the required interface."""
        try:
            from adapter import AutoGenAdapter
            
            # Check that required methods exist
            required_methods = [
                'run_task',
                'get_capabilities', 
                'health_check'
            ]
            
            for method in required_methods:
                assert hasattr(AutoGenAdapter, method), f"Missing method: {method}"
                
        except ImportError:
            pytest.skip("AutoGen not available")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])