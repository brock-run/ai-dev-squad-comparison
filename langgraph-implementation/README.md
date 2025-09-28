# LangGraph Multi-Agent Squad Implementation

This directory contains the enhanced LangGraph-based implementation of the AI agent orchestrator, featuring a multi-agent development squad with integrated safety controls, VCS workflows, and comprehensive telemetry.

## Architecture

The LangGraph implementation uses a state-based workflow with specialized agents:

- **Architect Agent**: Creates system design and architecture
- **Developer Agent**: Implements code based on design
- **Tester Agent**: Creates and runs comprehensive tests
- **Reviewer Agent**: Performs automated code review with optional human-in-the-loop
- **VCS Manager**: Handles version control operations (branches, commits, PRs)

## Features

### Core Capabilities
- ✅ Multi-agent collaboration using LangGraph state graphs
- ✅ Comprehensive state management and persistence
- ✅ Structured error handling with fallback edges
- ✅ Parallel execution where appropriate
- ✅ Human-in-the-loop review process

### Safety & Security
- ✅ Integrated execution sandbox (Docker/subprocess)
- ✅ Filesystem access controls with path validation
- ✅ Network access controls with domain allowlists
- ✅ Prompt injection detection and prevention
- ✅ Configurable security policies

### VCS Integration
- ✅ GitHub and GitLab provider support
- ✅ Automated branch creation and management
- ✅ Intelligent commit message generation
- ✅ Pull request/merge request automation
- ✅ Professional workflow patterns

### Observability
- ✅ Comprehensive telemetry and event emission
- ✅ Agent execution tracking and metrics
- ✅ Structured logging with JSON output
- ✅ Performance monitoring and profiling
- ✅ Error analysis and recovery tracking

## Directory Structure

```
langgraph-implementation/
├── adapter.py                 # Main LangGraph adapter implementation
├── state/
│   └── development_state.py   # State management and artifacts
├── agents/                    # Individual agent implementations (future)
├── workflows/                 # Workflow definitions (future)
├── tools/                     # Safe tool implementations (future)
├── tests/
│   └── test_langgraph_adapter.py  # Comprehensive test suite
├── simple_test.py            # Basic structure validation
├── test_adapter.py           # Integration test (requires deps)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Setup

### 1. Install Dependencies

```bash
# Core LangGraph dependencies
pip install langgraph langchain langchain-community

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

The adapter uses the central security policy system. Ensure you have a policy configured:

```bash
# Check available policies
python -m common.safety.policy list

# Set active policy
python -m common.safety.policy set-active standard
```

## Usage

### Basic Usage

```python
from langgraph_implementation.adapter import create_langgraph_adapter
from common.agent_api import TaskSchema

# Create adapter
adapter = create_langgraph_adapter()

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
    if event.type == "workflow_step":
        print(f"Step: {event.data['node']} - Status: {event.data['status']}")
    elif event.type == "task_complete":
        print(f"Task completed: {event.data['success']}")
```

### Advanced Configuration

```python
config = {
    "language": "python",
    "vcs": {
        "enabled": True,
        "provider": "github",
        "repository": "myorg/myrepo",
        "create_pr": True
    },
    "human_review": {
        "enabled": True,
        "required_for": ["critical", "security"]
    },
    "architect": {
        "model": "gpt-4",
        "temperature": 0.3
    },
    "developer": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.1
    },
    "tester": {
        "model": "gpt-3.5-turbo",
        "coverage_threshold": 80
    }
}

adapter = create_langgraph_adapter(config)
```

### Health Monitoring

```python
# Check adapter health
health = await adapter.health_check()
print(f"Status: {health['status']}")
print(f"Components: {health['components']}")

# Get capabilities
capabilities = await adapter.get_capabilities()
print(f"Features: {capabilities['features']}")
print(f"Safety: {capabilities['safety_features']}")
```

## Workflow States

The LangGraph workflow progresses through these states:

1. **INITIALIZING** → Task setup and validation
2. **DESIGN_IN_PROGRESS** → Architect creates system design
3. **DESIGN_COMPLETE** → Design approved, ready for implementation
4. **IMPLEMENTATION_IN_PROGRESS** → Developer implements code
5. **IMPLEMENTATION_COMPLETE** → Code ready for testing
6. **TESTING_IN_PROGRESS** → Tester creates and runs tests
7. **TESTING_COMPLETE** → Tests pass, ready for review
8. **REVIEW_IN_PROGRESS** → Automated and optional human review
9. **REVIEW_COMPLETE** → Review approved, ready for VCS
10. **VCS_IN_PROGRESS** → Branch creation, commits, PR/MR
11. **COMPLETE** → Task successfully completed

Error states and recovery:
- **ERROR** → Recoverable errors with retry logic
- **CANCELLED** → User-cancelled tasks

## State Artifacts

Each workflow stage produces structured artifacts:

### Design Artifact
```python
DesignArtifact(
    architecture_type="microservices",
    components=[...],
    interfaces=[...],
    data_models=[...],
    design_decisions=[...],
    trade_offs=[...],
    estimated_complexity="medium"
)
```

### Code Artifact
```python
CodeArtifact(
    language="python",
    main_code="...",
    supporting_files={"utils.py": "...", "models.py": "..."},
    dependencies=["fastapi", "pydantic"],
    entry_point="main.py",
    documentation="..."
)
```

### Test Artifact
```python
TestArtifact(
    test_framework="pytest",
    test_code="...",
    test_cases=[...],
    coverage_report={"percent": 85, "lines": 120},
    performance_benchmarks={...}
)
```

### Review Artifact
```python
ReviewArtifact(
    overall_score=87.5,
    approved=True,
    code_quality_score=85.0,
    test_quality_score=90.0,
    design_adherence_score=88.0,
    issues=[],
    suggestions=[...],
    human_feedback="Looks good!"
)
```

### VCS Artifact
```python
VCSArtifact(
    provider="github",
    repository="myorg/myrepo",
    branch_name="feature/user-management-api",
    commit_sha="abc123...",
    commit_message="feat: implement user management API",
    pull_request_number=42,
    pull_request_url="https://github.com/myorg/myrepo/pull/42",
    files_changed=["main.py", "test_main.py", "utils.py"]
)
```

## Testing

### Run Structure Tests
```bash
python simple_test.py
```

### Run Unit Tests
```bash
pytest tests/test_langgraph_adapter.py -v
```

### Run Integration Tests (requires dependencies)
```bash
python test_adapter.py
```

## Safety Controls

The adapter integrates with the central safety system:

### Execution Sandbox
- Docker-based isolation (preferred)
- Subprocess fallback for environments without Docker
- Resource limits (CPU, memory, time)
- Network isolation

### Input Validation
- Prompt injection detection
- Input sanitization
- Pattern-based filtering
- Optional LLM-based validation

### Filesystem Controls
- Path allowlist validation
- Temporary directory management
- File operation logging
- Size limits and quotas

### Network Controls
- Domain allowlist enforcement
- Default-deny policy
- Request logging and monitoring
- Rate limiting

## VCS Integration

### GitHub Integration
```python
# Automatic workflow
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

### GitLab Integration
```python
# Similar to GitHub but with GitLab-specific features
task = TaskSchema(
    description="Add user authentication",
    context={
        "vcs": {
            "provider": "gitlab",
            "owner": "myorg",
            "repo": "myproject",
            "create_mr": True
        }
    }
)
```

## Performance Considerations

### Memory Usage
- State persistence uses memory checkpoints
- Large artifacts are streamed when possible
- Configurable cleanup policies

### Execution Time
- Parallel agent execution where safe
- Caching for repeated operations
- Timeout controls for long-running tasks

### Scalability
- Stateless adapter design
- External state storage support
- Horizontal scaling capabilities

## Troubleshooting

### Common Issues

1. **LangGraph not available**
   ```bash
   pip install langgraph langchain
   ```

2. **Safety policy not found**
   ```bash
   python -m common.safety.policy set-active standard
   ```

3. **VCS authentication failed**
   ```bash
   export GITHUB_TOKEN="your-token"
   export GITLAB_TOKEN="your-token"
   ```

4. **Docker not available**
   - Adapter will fall back to subprocess execution
   - Some safety features may be limited

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

adapter = create_langgraph_adapter()
```

### State Inspection

```python
# Get workflow state
state = await adapter.workflow.aget_state(config)
print(f"Current status: {state.values['status']}")
print(f"Agent executions: {len(state.values['agent_executions'])}")
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure safety controls are properly integrated
5. Test with both Docker and subprocess execution modes

## License

This implementation is part of the AI Dev Squad Comparison project and follows the same license terms.