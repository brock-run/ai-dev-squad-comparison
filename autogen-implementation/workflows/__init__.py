"""
Workflows package for the AutoGen implementation.

This package contains the workflow implementations for the AutoGen framework,
including the group chat manager for orchestrating agent interactions.
"""

from workflows.group_chat_manager import (
    create_user_proxy,
    create_groupchat,
    setup_development_agents,
    run_development_workflow
)

__all__ = [
    'create_user_proxy',
    'create_groupchat',
    'setup_development_agents',
    'run_development_workflow'
]