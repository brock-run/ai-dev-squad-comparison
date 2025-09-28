#!/usr/bin/env python3
"""
Direct test without pytest fixtures to debug the mocking issue
"""

import sys
import os

# Mock the problematic modules first
from unittest.mock import MagicMock, patch

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

sys.modules['common'] = MagicMock()
sys.modules['common.agent_api'] = common_agent_api_mock
sys.modules['common.safety'] = MagicMock()
sys.modules['common.safety.policy'] = MagicMock()
sys.modules['common.safety.execute'] = MagicMock()
sys.modules['common.safety.fs'] = MagicMock()
sys.modules['common.safety.net'] = MagicMock()
sys.modules['common.safety.injection'] = MagicMock()
sys.modules['common.safety.config_integration'] = MagicMock()
sys.modules['common.config'] = MagicMock()
sys.modules['common.vcs'] = MagicMock()
sys.modules['common.vcs.base'] = MagicMock()
sys.modules['common.vcs.github'] = MagicMock()
sys.modules['common.vcs.gitlab'] = MagicMock()
sys.modules['common.vcs.commit_msgs'] = MagicMock()

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now change to the langgraph directory and import
os.chdir('langgraph-implementation')
from adapter import LangGraphAdapter

def test_direct():
    """Test adapter directly without pytest fixtures."""
    config = {
        'language': 'python',
        'vcs': {'enabled': True, 'repository': 'test/repo'},
        'human_review': {'enabled': False}
    }
    
    with patch('adapter.get_policy_manager') as mock_policy:
        with patch('adapter.get_config_manager') as mock_config_manager:
            mock_policy.return_value = MagicMock()
            mock_config_manager.return_value.config = config
            
            adapter = LangGraphAdapter(config)
            
            print(f"Adapter type: {type(adapter)}")
            print(f"Adapter name: {adapter.name}")
            print(f"Adapter version: {adapter.version}")
            
            # Test the assertions
            assert adapter.name == "LangGraph Multi-Agent Squad"
            assert adapter.version == "2.0.0"
            assert adapter.description is not None
            
            print("✓ All assertions passed!")

if __name__ == "__main__":
    test_direct()