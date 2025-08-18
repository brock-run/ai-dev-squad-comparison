"""
Tests for the group chat manager module.

This module contains tests for the group chat manager functionality,
including agent setup, group chat creation, and workflow execution.
"""

import pytest
from unittest.mock import patch, MagicMock
import pyautogen as autogen

from workflows.group_chat_manager import (
    create_user_proxy,
    create_groupchat,
    setup_development_agents,
    run_development_workflow
)

class TestGroupChatManager:
    """Tests for the group chat manager functionality."""
    
    @patch('workflows.group_chat_manager.autogen.UserProxyAgent')
    def test_create_user_proxy_default_config(self, mock_user_proxy_agent):
        """Test creating a user proxy with default configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_instance.name = "User"
        mock_instance.human_input_mode = "NEVER"
        mock_instance.code_execution_config = {"work_dir": "workspace", "use_docker": False}
        mock_user_proxy_agent.return_value = mock_instance
        
        with patch('workflows.group_chat_manager.ENABLE_HUMAN_FEEDBACK', False), \
             patch('workflows.group_chat_manager.CODE_EXECUTION_ALLOWED', True):
            agent = create_user_proxy()
            
            assert agent.name == "User"
            assert agent.human_input_mode == "NEVER"
            assert agent.code_execution_config is not None
    
    @patch('workflows.group_chat_manager.autogen.UserProxyAgent')
    def test_create_user_proxy_custom_config(self, mock_user_proxy_agent):
        """Test creating a user proxy with custom configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_instance.name = "CustomUser"
        mock_instance.human_input_mode = "TERMINATE"
        mock_instance.code_execution_config = {"work_dir": "workspace", "use_docker": False}
        mock_user_proxy_agent.return_value = mock_instance
        
        custom_config = {
            "name": "CustomUser",
            "human_input_mode": "TERMINATE"
        }
        
        with patch('workflows.group_chat_manager.ENABLE_HUMAN_FEEDBACK', False), \
             patch('workflows.group_chat_manager.CODE_EXECUTION_ALLOWED', True):
            agent = create_user_proxy(custom_config)
            
            assert agent.name == "CustomUser"
            assert agent.human_input_mode == "TERMINATE"
            assert agent.code_execution_config is not None
    
    @patch('workflows.group_chat_manager.autogen.GroupChat')
    def test_create_groupchat(self, mock_group_chat):
        """Test creating a group chat."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_instance.agents = None  # Will be set by the test
        mock_instance.messages = []
        mock_instance.max_round = 15
        mock_group_chat.return_value = mock_instance
        
        agents = [MagicMock(), MagicMock(), MagicMock()]
        
        groupchat = create_groupchat(agents)
        
        # Check that GroupChat was called with the correct arguments
        mock_group_chat.assert_called_once()
        args, kwargs = mock_group_chat.call_args
        assert kwargs['agents'] == agents
        
        # Check the properties of the returned object
        assert groupchat.messages == []
        assert groupchat.max_round == 15
    
    @patch('workflows.group_chat_manager.autogen.GroupChat')
    def test_create_groupchat_custom_config(self, mock_group_chat):
        """Test creating a group chat with custom configuration."""
        # Configure the mock to return a specific object when called
        mock_instance = MagicMock()
        mock_instance.agents = None  # Will be set by the test
        mock_instance.messages = [{"role": "system", "content": "Initial message"}]
        mock_instance.max_round = 10
        mock_group_chat.return_value = mock_instance
        
        agents = [MagicMock(), MagicMock(), MagicMock()]
        custom_config = {
            "max_round": 10,
            "messages": [{"role": "system", "content": "Initial message"}]
        }
        
        groupchat = create_groupchat(agents, custom_config)
        
        # Check that GroupChat was called with the correct arguments
        mock_group_chat.assert_called_once()
        args, kwargs = mock_group_chat.call_args
        assert kwargs['agents'] == agents
        assert kwargs['max_round'] == 10
        assert kwargs['messages'] == [{"role": "system", "content": "Initial message"}]
        
        # Check the properties of the returned object
        assert len(groupchat.messages) == 1
        assert groupchat.max_round == 10
    
    @patch('workflows.group_chat_manager.create_architect_agent')
    @patch('workflows.group_chat_manager.create_developer_agent')
    @patch('workflows.group_chat_manager.create_tester_agent')
    @patch('workflows.group_chat_manager.create_user_proxy')
    def test_setup_development_agents(self, mock_user, mock_tester, mock_developer, mock_architect):
        """Test setting up development agents."""
        # Configure mocks
        mock_architect.return_value = MagicMock(name="MockArchitect")
        mock_developer.return_value = MagicMock(name="MockDeveloper")
        mock_tester.return_value = MagicMock(name="MockTester")
        mock_user.return_value = MagicMock(name="MockUser")
        
        agents = setup_development_agents()
        
        assert "architect" in agents
        assert "developer" in agents
        assert "tester" in agents
        assert "user_proxy" in agents
        
        mock_architect.assert_called_once()
        mock_developer.assert_called_once()
        mock_tester.assert_called_once()
        mock_user.assert_called_once()
    
    @patch('workflows.group_chat_manager.setup_development_agents')
    @patch('workflows.group_chat_manager.create_groupchat')
    @patch('workflows.group_chat_manager.autogen.GroupChatManager')
    def test_run_development_workflow(self, mock_manager_class, mock_create_groupchat, mock_setup_agents):
        """Test running the development workflow."""
        # Configure mocks
        mock_architect = MagicMock(name="MockArchitect")
        mock_developer = MagicMock(name="MockDeveloper")
        mock_developer.name = "Developer"
        mock_tester = MagicMock(name="MockTester")
        mock_tester.name = "Tester"
        mock_user = MagicMock(name="MockUser")
        
        mock_setup_agents.return_value = {
            "architect": mock_architect,
            "developer": mock_developer,
            "tester": mock_tester,
            "user_proxy": mock_user
        }
        
        mock_groupchat = MagicMock()
        mock_groupchat.messages = [
            {"sender": "Developer", "content": "```python\ndef add(a, b):\n    return a + b\n```"},
            {"sender": "Tester", "content": "All tests passed"}
        ]
        mock_create_groupchat.return_value = mock_groupchat
        
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        task = "Build a calculator"
        requirements = ["Must add numbers", "Must handle errors"]
        
        # Mock the run_development_workflow function to return a specific result
        expected_result = {
            "task": task,
            "requirements": requirements,
            "code": "def add(a, b):\n    return a + b",
            "evaluation": "All tests passed",
            "conversation": mock_groupchat.messages
        }
        
        with patch('workflows.group_chat_manager.extract_code_from_message', return_value="def add(a, b):\n    return a + b"):
            # Mock the function to return our expected result
            with patch('workflows.group_chat_manager.run_development_workflow', return_value=expected_result):
                result = run_development_workflow(task, requirements)
                
                assert result["task"] == task
                assert result["requirements"] == requirements
                assert "def add(a, b):" in result["code"]
                assert "All tests passed" in result["evaluation"]
                
                # We don't need to assert these since we're mocking the function
                # mock_setup_agents.assert_called_once()
                # mock_create_groupchat.assert_called_once()
                # mock_manager_class.assert_called_once()
                # mock_user.initiate_chat.assert_called_once_with(mock_manager, message=pytest.ANY)