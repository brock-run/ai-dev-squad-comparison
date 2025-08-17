# AutoGen AI Development Squad Implementation

This directory contains the implementation of an AI development squad using AutoGen, a framework for building conversational AI agents that can collaborate with each other and humans.

## Overview

AutoGen enables the creation of conversational agents that can work together in a group chat setting to solve complex problems. This implementation demonstrates how to create a development squad with specialized agents (architect, developer, tester) that work together to complete software development tasks.

## Features

- Conversational agent design with specialized capabilities
- Group chat for agent collaboration
- Code execution capabilities
- Human feedback integration
- Integration with GitHub for code operations
- Local execution using Ollama models

## Setup Instructions

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download recommended Ollama models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull codellama:13b
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your GitHub token and other settings
   ```

## Directory Structure

- `agents/`: Contains the implementation of specialized agents
  - `architect_agent.py`: Responsible for system design and architecture decisions
  - `developer_agent.py`: Handles code implementation based on specifications
  - `tester_agent.py`: Creates and runs tests for the implemented code
  - `user_proxy.py`: Represents the human user in the conversation
  
- `workflows/`: Contains the workflow definitions
  - `group_chat_manager.py`: Manages the conversation between agents

## Usage

```python
import autogen
from agents.architect_agent import create_architect_agent
from agents.developer_agent import create_developer_agent
from agents.tester_agent import create_tester_agent
from agents.user_proxy import create_user_proxy
from workflows.group_chat_manager import create_groupchat

# Create agents
architect = create_architect_agent()
developer = create_developer_agent()
tester = create_tester_agent()
user_proxy = create_user_proxy()

# Create group chat
groupchat = create_groupchat([architect, developer, tester, user_proxy])
manager = autogen.GroupChatManager(groupchat=groupchat)

# Start the conversation
user_proxy.initiate_chat(
    manager,
    message="Build a Python function to calculate Fibonacci numbers. It must handle negative numbers and be optimized for performance."
)
```

## Performance Metrics

This implementation will be benchmarked against other frameworks using the standard test suite in the `comparison-results` directory.

## References

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [AutoGen GitHub Repository](https://github.com/microsoft/autogen)