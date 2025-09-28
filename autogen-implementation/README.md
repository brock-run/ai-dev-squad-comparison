# AutoGen AI Development Squad Implementation

This directory contains the implementation of an AI development squad using AutoGen, a framework for building conversational AI agents that can collaborate with each other and humans to solve complex software development tasks.

## Overview

AutoGen enables the creation of conversational agents that can work together in a group chat setting to solve complex problems. This implementation demonstrates how to create a development squad with specialized agents (architect, developer, tester) that work together to complete software development tasks through natural conversation and collaboration.

The AutoGen framework excels at multi-agent conversations where agents can take turns, build on each other's work, and collectively solve problems that would be difficult for a single agent to handle alone.

## Features

### Core Capabilities
- **Conversational Multi-Agent System**: Agents communicate through natural language in group chat format
- **Specialized Agent Roles**: Each agent has distinct capabilities and responsibilities
- **Group Chat Orchestration**: Intelligent conversation management and turn-taking
- **Code Execution Environment**: Safe code execution with result sharing
- **Human-in-the-Loop**: Integration points for human feedback and guidance
- **Version Control Integration**: Seamless GitHub operations and code management
- **Local LLM Support**: Full compatibility with Ollama models for privacy and cost control

### Advanced Features
- **Dynamic Agent Selection**: Automatic selection of the most appropriate agent for each task
- **Conversation Memory**: Persistent context across multi-turn conversations
- **Code Review Workflows**: Automated peer review between agents
- **Test-Driven Development**: Integrated testing workflows with the tester agent
- **Architecture Planning**: Systematic design phase before implementation
- **Error Recovery**: Intelligent error handling and retry mechanisms

## Setup

### Prerequisites
- Python 3.8+
- Ollama (for local LLM execution)
- Git (for version control operations)
- GitHub account and token (for VCS integration)

### Installation

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   cd autogen-implementation
   pip install -r requirements.txt
   ```

3. **Download recommended Ollama models:**
   ```bash
   # Primary models for development tasks
   ollama pull llama3.1:8b
   ollama pull codellama:13b
   
   # Alternative models for different use cases
   ollama pull llama3.1:70b  # For complex reasoning (if you have sufficient resources)
   ollama pull deepseek-coder:6.7b  # Specialized for coding tasks
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration:
   # GITHUB_TOKEN=your_github_token_here
   # OLLAMA_BASE_URL=http://localhost:11434
   # AUTOGEN_USE_DOCKER=false
   ```

5. **Validate installation:**
   ```bash
   python validate_autogen.py
   ```

6. **Run integration test:**
   ```bash
   python simple_integration_test.py
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

The AutoGen implementation provides a conversational multi-agent development environment. Here's how to use it:

### Basic Usage

```python
from adapter import create_autogen_adapter

# Create adapter with configuration
config = {
    'language': 'python',
    'autogen': {
        'model': 'llama3.1:8b',
        'code_model': 'codellama:13b'
    },
    'vcs': {
        'github': {'enabled': True}
    }
}

adapter = create_autogen_adapter(config)

# Get capabilities
capabilities = await adapter.get_capabilities()
print(f"Features: {capabilities['features']}")

# Run a task
from common.agent_api import TaskSchema, TaskType

task = TaskSchema(
    id='fibonacci-task',
    type=TaskType.FEATURE_ADD,
    inputs={
        'description': 'Create a Fibonacci calculator with optimization',
        'requirements': [
            'Handle negative numbers gracefully',
            'Optimize for performance with memoization',
            'Include comprehensive error handling',
            'Add unit tests with edge cases'
        ]
    },
    repo_path='.',
    vcs_provider='github'
)

async for result in adapter.run_task(task):
    if hasattr(result, 'status'):
        print(f"Task completed: {result.status}")
        print(f"Conversation log: {result.artifacts['conversation_log']}")
```

### Advanced Multi-Agent Workflow

```python
import autogen
from agents.architect_agent import create_architect_agent
from agents.developer_agent import create_developer_agent
from agents.tester_agent import create_tester_agent
from agents.user_proxy import create_user_proxy
from workflows.group_chat_manager import create_groupchat

# Create specialized agents
architect = create_architect_agent()
developer = create_developer_agent()
tester = create_tester_agent()
user_proxy = create_user_proxy()

# Create group chat with intelligent orchestration
groupchat = create_groupchat([architect, developer, tester, user_proxy])
manager = autogen.GroupChatManager(groupchat=groupchat)

# Start collaborative development session
user_proxy.initiate_chat(
    manager,
    message="""
    Build a Python web API for user authentication with the following requirements:
    - JWT token-based authentication
    - Password hashing with bcrypt
    - Rate limiting for login attempts
    - User registration and login endpoints
    - Comprehensive test suite
    - OpenAPI documentation
    """
)
```

### Agent Specialization

Each agent has specific capabilities and conversation patterns:

#### Architect Agent
```python
# The architect focuses on system design and planning
architect_response = await architect.generate_reply(
    "Design a scalable microservices architecture for an e-commerce platform"
)
```

#### Developer Agent
```python
# The developer implements code based on specifications
developer_response = await developer.generate_reply(
    "Implement the user authentication service according to the architect's design"
)
```

#### Tester Agent
```python
# The tester creates comprehensive test suites
tester_response = await tester.generate_reply(
    "Create unit and integration tests for the authentication service"
)
```

### Configuration Options

Configure AutoGen-specific settings in your config:

```python
config = {
    'autogen': {
        'model': 'llama3.1:8b',           # Primary model for conversation
        'code_model': 'codellama:13b',     # Specialized model for coding
        'temperature': 0.7,                # Creativity vs consistency
        'max_consecutive_auto_reply': 10,  # Conversation length limit
        'human_input_mode': 'NEVER',       # Automation level
        'code_execution_config': {
            'work_dir': './autogen_workspace',
            'use_docker': False
        }
    },
    'conversation': {
        'max_turns': 50,                   # Maximum conversation turns
        'enable_code_execution': True,     # Allow code execution
        'save_conversation': True          # Save conversation logs
    }
}
```

## Architecture

The AutoGen implementation follows a conversational multi-agent architecture:

### Core Components

1. **AutoGenAdapter**: Main adapter implementing the AgentAdapter protocol
2. **Specialized Agents**: Architect, Developer, Tester, and User Proxy agents
3. **Group Chat Manager**: Orchestrates conversations between agents
4. **Conversation Workflows**: Manages multi-turn development sessions
5. **Code Execution Environment**: Safe execution of generated code
6. **Safety Integration**: Comprehensive security controls

### Conversation Flow

1. **Task Analysis**: User proxy analyzes the development task
2. **Architecture Phase**: Architect designs the system structure
3. **Implementation Phase**: Developer writes code based on design
4. **Testing Phase**: Tester creates and runs comprehensive tests
5. **Review Phase**: Agents collaborate on code review and refinement
6. **Integration**: Final code is integrated and committed to VCS

### Agent Specialization

- **Architect Agent**: System design, architecture decisions, technology selection
- **Developer Agent**: Code implementation, algorithm design, optimization
- **Tester Agent**: Test creation, quality assurance, edge case analysis
- **User Proxy Agent**: Human interaction, requirement clarification, approval

## Development

To work on the AutoGen implementation:

### Setup Development Environment

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up Ollama:**
```bash
# Install Ollama (see https://ollama.ai)
ollama serve
ollama pull llama3.1:8b
```

3. **Run validation:**
```bash
python validate_autogen.py
```

### Testing

Run the comprehensive test suite:

```bash
# Structure tests
python tests/test_structure_only.py

# Integration tests
python simple_integration_test.py

# AutoGen-specific tests
python test_pyautogen_imports.py

# Full test suite
pytest tests/ -v
```

### Code Structure

Follow these guidelines when contributing:

- **Agents**: Implement specialized agent behaviors and capabilities
- **Workflows**: Define conversation patterns and orchestration logic
- **Safety**: Integrate security controls throughout the conversation flow
- **Testing**: Maintain comprehensive test coverage for all components

### Conversation Patterns

The implementation supports various conversation patterns:

- **Sequential**: Agents take turns in a predefined order
- **Dynamic**: Intelligent agent selection based on context
- **Collaborative**: Multiple agents work together on complex tasks
- **Human-in-the-Loop**: Human intervention at key decision points

## Troubleshooting

### Common Issues

1. **Ollama Connection**: Ensure Ollama is running: `ollama serve`
2. **Model Loading**: Download required models: `ollama pull llama3.1:8b`
3. **Memory Issues**: Use smaller models or reduce conversation length
4. **Conversation Loops**: Adjust `max_consecutive_auto_reply` setting

### Debug Mode

Enable debug logging for detailed conversation analysis:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring

Monitor conversation performance with built-in metrics:

```python
metrics = await adapter.get_metrics()
print(f"Conversations completed: {metrics['conversations']['completed']}")
print(f"Average turns per conversation: {metrics['conversations']['avg_turns']}")
print(f"Code execution success rate: {metrics['code_execution']['success_rate']}")
```

## Performance Metrics

This implementation is benchmarked against other frameworks using the standard test suite. Key performance indicators include:

- **Conversation Quality**: Measured by task completion success rate
- **Code Quality**: Evaluated through automated code analysis
- **Collaboration Effectiveness**: Agent interaction and turn-taking efficiency
- **Resource Usage**: Memory and compute requirements for conversations

## Advanced Features

### Custom Agent Creation

Create specialized agents for specific domains:

```python
from autogen import ConversableAgent

def create_security_agent():
    return ConversableAgent(
        name="SecurityExpert",
        system_message="You are a cybersecurity expert specializing in secure coding practices...",
        llm_config={"model": "llama3.1:8b"},
        human_input_mode="NEVER"
    )
```

### Conversation Persistence

Save and resume conversations:

```python
# Save conversation state
conversation_state = groupchat.save_state()

# Resume conversation later
groupchat.load_state(conversation_state)
```

### Integration with External Tools

Connect agents to external APIs and tools:

```python
def github_integration_tool(repo_url, action):
    """Tool for GitHub operations"""
    # Implementation for GitHub API calls
    pass

# Register tool with agents
developer.register_function(github_integration_tool)
```

## References

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [AutoGen GitHub Repository](https://github.com/microsoft/autogen)
- [Ollama Documentation](https://ollama.ai/docs)
- [Multi-Agent Conversation Patterns](https://microsoft.github.io/autogen/docs/Use-Cases/agent_chat)