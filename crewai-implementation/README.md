# CrewAI Multi-Agent Squad Implementation

This directory contains the enhanced CrewAI-based implementation of the AI agent orchestrator, featuring a multi-agent development squad with integrated safety controls, VCS workflows, and comprehensive telemetry.

## Architecture

The CrewAI implementation uses role-based autonomous agents that collaborate through sequential task execution:

- **Architect Agent**: Creates system design and architecture decisions
- **Developer Agent**: Implements code based on architectural specifications
- **Tester Agent**: Creates comprehensive tests and quality assurance
- **Reviewer Agent**: Performs code review and quality validation

## Features

### Core Capabilities
- ✅ Role-based autonomous agents with specialized capabilities
- ✅ Sequential and hierarchical task execution
- ✅ Agent memory persistence across tasks
- ✅ Tool integration with safety controls
- ✅ Comprehensive guardrails for output validation
- ✅ Event bus integration for real-time monitoring

### Safety & Security
- ✅ Integrated execution sandbox (Docker/subprocess)
- ✅ Filesystem access controls with path validation
- ✅ Network access controls with domain allowlists
- ✅ Prompt injection detection and prevention
- ✅ Configurable security policies per agent

### VCS Integration
- ✅ GitHub and GitLab provider support
- ✅ Automated branch creation and management
- ✅ Intelligent commit message generation
- ✅ Pull request/merge request automation
- ✅ Multi-file change management

### Observability
- ✅ Comprehensive telemetry and event emission
- ✅ Agent interaction tracking and metrics
- ✅ Tool execution monitoring
- ✅ Performance profiling and optimization
- ✅ Crew collaboration analytics

## Directory Structure

```
crewai-implementation/
├── adapter.py                 # Main CrewAI adapter implementation
├── agents/                    # Individual agent implementations (future)
├── workflows/                 # Workflow definitions (future)
├── tools/                     # Safe tool implementations (integrated)
├── tests/
│   └── test_crewai_adapter.py # Comprehensive test suite
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Setup

### 1. Install Dependencies

```bash
# Core CrewAI dependencies
pip install crewai langchain langchain-community

# Optional: For enhanced model support
pip install langchain-openai langchain-anthropic

# Optional: For local model support
pip install langchain-ollama

# Development dependencies
pip install pytest pytest-asyncio
```

### 2. Configure Environment Variables

```bash
# Required for LLM access
export OPENAI_API_KEY="your-openai-key"

# Optional: For VCS integration
export GITHUB_TOKEN="your-github-token"
export GITLAB_TOKEN="your-gitlab-token"

# Optional: For local models
export OLLAMA_BASE_URL="http://localhost:11434"
```

### 3. Configure Security Policies

The adapter uses the central security policy system:

```bash
# Check available policies
python -m common.safety.policy list

# Set active policy
python -m common.safety.policy set-active standard
```

## Usage

### Basic Usage

```python
from crewai_implementation.adapter import create_crewai_adapter
from common.agent_api import TaskSchema

# Create adapter
adapter = create_crewai_adapter()

# Create task
task = TaskSchema(
    id="task-1",
    description="Create a REST API for user management",
    requirements=[
        "Implement CRUD operations for users",
        "Add input validation and error handling",
        "Include comprehensive tests",
        "Add API documentation"
    ],
    context={"language": "python", "framework": "fastapi"}
)

# Execute task
async for event in adapter.run_task(task):
    if event.type == "crew_start":
        print(f"Crew started with {event.data['agents']} agents")
    elif event.type == "task_complete":
        print(f"Task completed: {event.data['success']}")
```

### Advanced Configuration

```python
config = {
    "language": "python",
    "max_rpm": 15,  # Requests per minute limit
    "vcs": {
        "enabled": True,
        "provider": "github",
        "repository": "myorg/myrepo",
        "create_pr": True
    },
    "architect": {
        "max_iterations": 5
    },
    "developer": {
        "max_iterations": 10
    },
    "tester": {
        "max_iterations": 7
    },
    "reviewer": {
        "max_iterations": 5
    }
}

adapter = create_crewai_adapter(config)
```

### Health Monitoring

```python
# Check adapter health
health = await adapter.health_check()
print(f"Status: {health['status']}")
print(f"Agents: {[k for k in health['components'] if k.startswith('agent_')]}")

# Get capabilities
capabilities = await adapter.get_capabilities()
print(f"Crew: {capabilities['crew_composition']}")
print(f"Features: {capabilities['features']}")
```

## Agent Roles and Responsibilities

### 🏗️ Architect Agent
- **Role**: Software Architect
- **Goal**: Design robust and scalable software architectures
- **Capabilities**: System design, component breakdown, interface definition
- **Tools**: Safe code executor, file operations, VCS operations

### 💻 Developer Agent
- **Role**: Senior Developer
- **Goal**: Implement high-quality, well-tested code
- **Capabilities**: Code implementation, documentation, configuration
- **Tools**: Safe code executor, file operations, VCS operations

### 🧪 Tester Agent
- **Role**: QA Engineer
- **Goal**: Create comprehensive tests and ensure quality
- **Capabilities**: Test creation, quality metrics, performance testing
- **Tools**: Safe code executor, file operations

### 👀 Reviewer Agent
- **Role**: Code Reviewer
- **Goal**: Review code for quality, security, and best practices
- **Capabilities**: Code review, security analysis, best practices validation
- **Tools**: Safe code executor, file operations

## Workflow Execution

The CrewAI workflow follows this sequence:

1. **Architecture Phase** → Architect creates system design
2. **Development Phase** → Developer implements based on architecture
3. **Testing Phase** → Tester creates comprehensive test suite
4. **Review Phase** → Reviewer validates quality and security
5. **VCS Phase** → Automated commit and PR/MR creation (optional)

Each phase builds on the previous one, with agents having access to all prior work through task context.

## Safety Controls

### Execution Sandbox
- Docker-based isolation (preferred)
- Subprocess fallback for environments without Docker
- Resource limits (CPU, memory, time)
- Network isolation

### Tool Safety
- All tools wrapped with safety controls
- Input validation and sanitization
- Output filtering and validation
- Execution monitoring and logging

### Agent Guardrails
- Role-specific behavior constraints
- Output validation and quality control
- Memory management and cleanup
- Error handling and recovery

## VCS Integration

### Automated Workflows
```python
# Automatic VCS integration
task = TaskSchema(
    description="Add user authentication",
    context={
        "vcs": {
            "provider": "github",
            "owner": "myorg",
            "repo": "myproject",
            "create_pr": True
        }
    }
)
```

### Generated Artifacts
- Feature branch creation
- Multi-file commits with intelligent messages
- Pull request with detailed description
- Code review integration

## Performance Considerations

### Agent Efficiency
- Role specialization reduces context switching
- Memory persistence improves collaboration
- Tool caching reduces redundant operations
- Parallel execution where safe

### Resource Management
- Configurable rate limiting (max_rpm)
- Memory cleanup between tasks
- Tool execution timeouts
- Agent iteration limits

### Scalability
- Stateless adapter design
- External memory storage support
- Horizontal crew scaling
- Load balancing capabilities

## Testing

### Run Unit Tests
```bash
pytest tests/test_crewai_adapter.py -v
```

### Test Coverage Areas
- Agent creation and configuration
- Task execution and collaboration
- Safety control integration
- VCS workflow automation
- Tool functionality and safety
- Event emission and telemetry

## Troubleshooting

### Common Issues

1. **CrewAI not available**
   ```bash
   pip install crewai langchain
   ```

2. **Agent memory issues**
   - Increase max_iterations in config
   - Clear agent memory between tasks
   - Check memory persistence settings

3. **Tool execution failures**
   - Verify safety policy configuration
   - Check sandbox availability
   - Review tool permissions

4. **VCS integration issues**
   ```bash
   export GITHUB_TOKEN="your-token"
   export GITLAB_TOKEN="your-token"
   ```

### Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

adapter = create_crewai_adapter()
```

### Agent Monitoring

```python
# Monitor agent interactions
capabilities = await adapter.get_capabilities()
print(f"Active agents: {capabilities['crew_composition']['agents']}")

# Check agent health
health = await adapter.health_check()
for component, status in health['components'].items():
    if component.startswith('agent_'):
        print(f"{component}: {status}")
```

## Performance Benchmarks

### Expected Performance
- **Task Initialization**: < 3 seconds
- **Simple Task Execution**: < 60 seconds
- **Complex Task Execution**: < 300 seconds
- **Memory Usage**: < 2GB during normal operation

### Optimization Tips
- Use appropriate max_iterations per agent
- Configure rate limiting based on API limits
- Enable memory persistence for related tasks
- Use tool caching for repeated operations

## Contributing

1. Follow the existing agent role patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure safety controls are properly integrated
5. Test with both sequential and hierarchical processes

## License

This implementation is part of the AI Dev Squad Comparison project and follows the same license terms.