"""
Test the replay wrapper functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

def test_replay_wrapper_imports():
    """Test that we can import the replay wrapper components."""
    # Mock all the complex dependencies
    with patch.dict('sys.modules', {
        'langgraph.graph': Mock(),
        'langgraph.checkpoint.memory': Mock(),
        'langchain_core.messages': Mock(),
        'langchain_community.chat_models': Mock(),
        'common.config': Mock(),
        'common.safety.policy': Mock(),
        'common.safety.execute': Mock(),
        'common.safety.fs': Mock(),
        'common.safety.net': Mock(),
        'common.safety.injection': Mock(),
        'common.vcs.github': Mock(),
        'common.vcs.gitlab': Mock(),
        'common.vcs.commit_msgs': Mock(),
    }):
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "langgraph-implementation"))
        
        # Mock the get_config_manager function
        mock_config_manager = Mock()
        mock_config_manager.config = {
            'github': {'enabled': False},
            'gitlab': {'enabled': False}
        }
        
        with patch('common.config.get_config_manager', return_value=mock_config_manager):
            from replay_wrapper import ReplayLangGraphAdapter, create_replay_adapter
            
            # Test that we can create the wrapper
            assert ReplayLangGraphAdapter is not None
            assert create_replay_adapter is not None

def test_replay_interception_decorators():
    """Test that the interception decorators work correctly."""
    from benchmark.replay.player import (
        intercept_llm_call, intercept_tool_call, intercept_sandbox_exec, intercept_vcs_operation
    )
    
    # Test that decorators can be applied
    @intercept_llm_call(adapter_name="test", agent_id="test_agent")
    def mock_llm_function():
        return "llm_result"
    
    @intercept_tool_call(adapter_name="test", agent_id="test_agent", tool_name="test_tool")
    def mock_tool_function():
        return "tool_result"
    
    @intercept_sandbox_exec(adapter_name="test", agent_id="test_agent")
    def mock_sandbox_function():
        return "sandbox_result"
    
    @intercept_vcs_operation(adapter_name="test", agent_id="test_agent", operation="test_op")
    def mock_vcs_function():
        return "vcs_result"
    
    # Test that functions still work normally when no player is set
    assert mock_llm_function() == "llm_result"
    assert mock_tool_function() == "tool_result"
    assert mock_sandbox_function() == "sandbox_result"
    assert mock_vcs_function() == "vcs_result"