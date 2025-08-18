"""
Pytest configuration file for the AutoGen implementation tests.

This file is automatically loaded by pytest and can be used to configure
the test environment, define fixtures, and set up paths.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Add the parent directory to the Python path to allow importing from the agents module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import mock autogen classes
from tests.mocks.mock_autogen import (
    AssistantAgent,
    UserProxyAgent,
    GroupChat,
    GroupChatManager
)

# Create a mock pyautogen module
mock_autogen = MagicMock()
mock_autogen.AssistantAgent = AssistantAgent
mock_autogen.UserProxyAgent = UserProxyAgent
mock_autogen.GroupChat = GroupChat
mock_autogen.GroupChatManager = GroupChatManager

# Patch the pyautogen module
sys.modules['pyautogen'] = mock_autogen
sys.modules['autogen'] = mock_autogen

@pytest.fixture
def assistant_agent():
    """Fixture for creating an AssistantAgent instance."""
    return AssistantAgent(
        name="TestAssistant",
        system_message="You are a test assistant."
    )

@pytest.fixture
def user_proxy_agent():
    """Fixture for creating a UserProxyAgent instance."""
    return UserProxyAgent(
        name="TestUser",
        human_input_mode="NEVER"
    )

@pytest.fixture
def group_chat(assistant_agent, user_proxy_agent):
    """Fixture for creating a GroupChat instance."""
    return GroupChat(
        agents=[assistant_agent, user_proxy_agent],
        messages=[]
    )

@pytest.fixture
def group_chat_manager(group_chat):
    """Fixture for creating a GroupChatManager instance."""
    return GroupChatManager(groupchat=group_chat)