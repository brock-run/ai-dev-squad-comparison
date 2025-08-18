"""
Mock implementations of autogen classes for testing.

This module provides mock implementations of the autogen classes used in the code,
allowing tests to run without depending on the actual pyautogen implementation.
"""

from typing import Dict, List, Any, Optional, Callable


class AssistantAgent:
    """Mock implementation of autogen.AssistantAgent."""
    
    def __init__(self, name: str, system_message: str = "", llm_config: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize a mock AssistantAgent."""
        self.name = name
        self.system_message = system_message
        self.llm_config = llm_config or {}
        self.kwargs = kwargs
        self.messages = []
    
    def receive(self, message: str, sender: str):
        """Mock implementation of receive method."""
        self.messages.append({"content": message, "sender": sender})
        return True
    
    def send(self, message: str, recipient: str):
        """Mock implementation of send method."""
        return {"content": message, "recipient": recipient}


class UserProxyAgent:
    """Mock implementation of autogen.UserProxyAgent."""
    
    def __init__(self, name: str, human_input_mode: str = "ALWAYS", 
                 code_execution_config: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize a mock UserProxyAgent."""
        self.name = name
        self.human_input_mode = human_input_mode
        self.code_execution_config = code_execution_config
        self.kwargs = kwargs
        self.messages = []
    
    def receive(self, message: str, sender: str):
        """Mock implementation of receive method."""
        self.messages.append({"content": message, "sender": sender})
        return True
    
    def send(self, message: str, recipient: str):
        """Mock implementation of send method."""
        return {"content": message, "recipient": recipient}
    
    def initiate_chat(self, manager, message: str):
        """Mock implementation of initiate_chat method."""
        self.messages.append({"content": message, "recipient": "manager"})
        return {"content": "Response from manager", "sender": "manager"}


class GroupChat:
    """Mock implementation of autogen.GroupChat."""
    
    def __init__(self, agents: List[Any], messages: List[Dict[str, Any]] = None, 
                 max_round: int = 10, **kwargs):
        """Initialize a mock GroupChat."""
        self.agents = agents
        self.messages = messages or []
        self.max_round = max_round
        self.kwargs = kwargs
    
    def reset(self):
        """Mock implementation of reset method."""
        self.messages = []


class GroupChatManager:
    """Mock implementation of autogen.GroupChatManager."""
    
    def __init__(self, groupchat: GroupChat, **kwargs):
        """Initialize a mock GroupChatManager."""
        self.groupchat = groupchat
        self.kwargs = kwargs
    
    def run(self, message: str):
        """Mock implementation of run method."""
        self.groupchat.messages.append({"role": "user", "content": message})
        return {"status": "success", "messages": self.groupchat.messages}