# Langroid Implementation

This directory contains the Langroid orchestrator implementation for the AI Dev Squad Comparison platform.

## Overview

Langroid provides conversation-style multi-agent interactions with:
- Task orchestration without LangChain dependencies
- Lightweight architecture
- Natural conversation flow between agents

## Structure

```
langroid-implementation/
├── adapter.py                         # Main AgentAdapter implementation
├── simple_integration_test.py         # Basic integration test
├── production_readiness_test.py       # Production readiness validation
├── agents/                            # Specialized agent implementations
│   ├── developer_agent.py             # Developer agent for code implementation
│   ├── reviewer_agent.py              # Reviewer agent for quality assurance
│   └── tester_agent.py                # Tester agent for test creation
├── workflows/                         # Conversation workflow management
│   └── conversation_workflow.py       # Multi-phase conversation orchestration
├── tests/                             # Comprehensive test suite
│   ├── test_langroid_adapter.py       # Unit tests for adapter
│   └── test_external_dependencies.py  # External integration tests
├── requirements.txt                   # Python dependencies
├── COMPLETION_SUMMARY.md              # Implementation completion summary
└── README.md                          # This file
```

## Features

### Core Capabilities
- **Conversation-Style Interactions**: Natural dialogue between specialized agents
- **Turn-Taking Logic**: Structured conversation flow with proper agent coordination
- **Agent Role Specialization**: Dedicated agents for development, review, and testing
- **Multi-Phase Workflows**: Requirements → Implementation → Review → Testing → Validation
- **Context Preservation**: Full conversation history maintained throughout development

### Safety & Security
- **Conversation-Level Controls**: Safety measures integrated into agent conversations
- **Input Sanitization**: Prompt injection detection for all agent messages
- **Execution Sandbox**: Sandboxed execution for code-related conversations
- **Agent Isolation**: Each agent operates within defined safety boundaries

### Integration Features
- **VCS Integration**: GitHub and GitLab support with conversation attribution
- **Comprehensive Telemetry**: Real-time monitoring of conversation flow and decisions

## Setup

### Prerequisites
- Python 3.8+ (recommended 3.11)
- OpenAI API key for LLM integration
- Optional: GitHub/GitLab tokens for VCS integration

### Installation

1. **Install dependencies:**
   ```bash
   cd langroid-implementation
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export GITHUB_TOKEN="your-github-token"  # Optional
   export GITLAB_TOKEN="your-gitlab-token"  # Optional
   ```

3. **Validate installation:**
   ```bash
   python validate_langroid.py
   ```

4. **Run integration test:**
   ```bash
   python simple_integration_test.py
   ```

### Configuration

Configure Langroid-specific settings in your system configuration:

```yaml
langroid:
  model: "gpt-3.5-turbo"
  max_turns: 10
  conversation_timeout: 300
  
agents:
  developer:
    temperature: 0.3
    max_tokens: 1500
  reviewer:
    temperature: 0.1
    max_tokens: 1000
  tester:
    temperature: 0.2
    max_tokens: 1200
```
- **Health Monitoring**: Component-level health checks and workflow status
- **Graceful Fallbacks**: Robust fallback mode when dependencies unavailable

## Usage

### Basic Usage

The Langroid implementation is automatically available when the system is configured. It implements the standard AgentAdapter interface for seamless integration with the benchmark suite.

```python
from langroid_implementation.adapter import create_langroid_adapter
from common.agent_api import TaskSchema, TaskType

# Create adapter with configuration
config = {
    'language': 'python',
    'langroid': {
        'model': 'gpt-3.5-turbo'
    },
    'vcs': {
        'github': {
            'enabled': True
        }
    }
}

adapter = create_langroid_adapter(config)

# Create a task
task = TaskSchema(
    id='example-task',
    type=TaskType.FEATURE_ADD,
    inputs={
        'description': 'Create a conversation-based data processor',
        'requirements': [
            'Process data through agent conversations',
            'Include comprehensive error handling',
            'Add detailed logging'
        ]
    },
    repo_path='.',
    vcs_provider='github'
)

# Execute task with conversation workflow
async for result in adapter.run_task(task):
    if hasattr(result, 'status'):
        print(f"Task completed: {result.status}")
        print(f"Conversation turns: {result.metadata.get('conversation_turns', 0)}")
        print(f"Agents used: {result.metadata.get('agents_used', [])}")
```

### Conversation Workflow

The Langroid implementation uses a structured conversation workflow:

1. **Requirements Analysis**: Developer and Reviewer agents collaborate to understand requirements
2. **Implementation**: Developer agent creates code based on architectural guidance
3. **Review**: Reviewer agent provides quality feedback and suggestions
4. **Testing**: Tester agent creates comprehensive tests
5. **Validation**: Multi-agent review ensures all requirements are met

### Agent Specialization

- **Developer Agent**: Handles code implementation through technical discussions
- **Reviewer Agent**: Provides quality assurance through quality-focused dialogue
- **Tester Agent**: Creates tests through test-driven development conversations

## Configuration

Configure Langroid-specific settings in `config/system.yaml`:

```yaml
orchestrators:
  langroid:
    enabled: true
    model_config:
      primary: "codellama:13b"
      fallback: "llama2:7b"
    timeout_seconds: 1800
```

## Testing

### Run Basic Integration Test
```bash
cd langroid-implementation
python simple_integration_test.py
```

### Run Comprehensive Test Suite
```bash
cd langroid-implementation
pytest tests/ -v
```

### Run Production Readiness Test
```bash
cd langroid-implementation
python production_readiness_test.py
```

### Run External Dependency Tests
```bash
cd langroid-implementation
pytest tests/test_external_dependencies.py -v -m external
```

## Development

To work on the Langroid implementation:

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Install Langroid**: `pip install langroid` (for full functionality)
3. **Set environment variables** (optional):
   - `OPENAI_API_KEY`: For OpenAI integration
   - `GITHUB_TOKEN`: For GitHub VCS integration
   - `GITLAB_TOKEN`: For GitLab VCS integration
4. **Run tests**: `pytest tests/ -v`
5. **Follow the AgentAdapter protocol** defined in `common/agent_api.py`

### Architecture Overview

The Langroid implementation follows a conversation-based architecture:

```
LangroidAdapter
├── SafeChatAgent (wrapper for safety controls)
├── ConversationWorkflow (multi-phase orchestration)
├── Specialized Agents
│   ├── DeveloperAgent (technical implementation)
│   ├── ReviewerAgent (quality assurance)
│   └── TesterAgent (test creation)
└── Safety & VCS Integration
```

### Adding New Agent Types

To add new specialized agents:

1. Create agent class in `agents/` directory
2. Implement conversation interface with `llm_response_async` method
3. Add safety wrapper in adapter initialization
4. Update conversation workflow to include new agent
5. Add tests for new agent functionality

### Conversation Patterns

The framework supports various conversation patterns:
- **Sequential**: Agents take turns in predefined order
- **Collaborative**: Multiple agents contribute to single phase
- **Iterative**: Agents refine work through multiple rounds
- **Validation**: Cross-agent validation and approval