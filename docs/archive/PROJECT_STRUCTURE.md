# AI Dev Squad Comparison - Project Structure

This document outlines the enhanced project structure for the AI Dev Squad Comparison platform.

## Overview

The project is organized into logical components with clear separation of concerns:

```
ai-dev-squad-comparison/
├── common/                          # Shared components and utilities
│   ├── agent_api.py                # Common Agent API Protocol
│   ├── safety/                     # Safety and security components
│   ├── vcs/                        # Version control system integration
│   ├── telemetry/                  # Telemetry and observability
│   └── ollama_integration.py       # Ollama model integration
├── config/                         # Configuration files and templates
│   ├── system.example.yaml         # System configuration template
│   ├── model_pricing.example.yaml  # Model pricing configuration
│   └── injection_patterns.example.yaml # Security patterns
├── benchmark/                      # Benchmarking system
│   ├── benchmark_suite.py          # Main benchmark CLI
│   ├── tasks/                      # Benchmark task definitions
│   ├── verifier/                   # Verification and quality assessment
│   └── replay/                     # Record-replay functionality
├── docs/                           # Documentation
│   ├── guides/                     # User and developer guides
│   └── ...                         # Existing documentation
├── comparison-results/             # Results analysis and dashboard
│   └── dashboard.py                # Web dashboard
├── [framework]-implementation/     # Orchestrator implementations
│   ├── adapter.py                  # AgentAdapter implementation
│   ├── agents/                     # Agent definitions
│   ├── workflows/                  # Workflow configurations
│   ├── tests/                      # Unit and integration tests
│   ├── requirements.txt            # Dependencies
│   └── README.md                   # Framework-specific documentation
└── ...                             # Other project files
```

## Framework Implementations

### Existing Frameworks (Enhanced)
- `langgraph-implementation/` - LangGraph with enhanced error handling
- `crewai-implementation/` - CrewAI v2 with guardrails
- `autogen-implementation/` - AutoGen with persistent memory
- `n8n-implementation/` - n8n with API-driven workflows
- `semantic-kernel-implementation/` - Semantic Kernel (Python/C#)
- `claude-code-subagents/` - Claude Code Subagents

### New Framework Implementations
- `langroid-implementation/` - Conversation-style multi-agent interactions
- `llamaindex-implementation/` - Retrieval-augmented workflows
- `haystack-implementation/` - ReAct-style tool usage
- `strands-implementation/` - Enterprise-grade observability

## Common Components

### Agent API (`common/agent_api.py`)
- `AgentAdapter` protocol for standardized interfaces
- `TaskSchema` for consistent task input format
- `RunResult` for standardized output format
- `EventStream` for real-time event emission

### Safety Controls (`common/safety/`)
- Execution sandbox with Docker integration
- Filesystem and network access controls
- Prompt injection detection and output filtering
- Configurable security policy system

### VCS Integration (`common/vcs/`)
- Unified GitHub and GitLab API integration
- Professional workflow patterns with branching
- Rate limiting and error handling
- Commit message generation using local models

### Telemetry (`common/telemetry/`)
- Structured logging with consistent schema
- OpenTelemetry integration with distributed tracing
- Cost and token tracking for all model interactions
- Real-time metrics collection and aggregation

## Benchmark System

### Task Definitions (`benchmark/tasks/`)
- Single-file Bug Fix scenarios
- Multi-step Feature Addition tasks
- Question Answering with codebase/logs
- Code Optimization challenges
- Edge Case handling with incorrect issues

### Verification (`benchmark/verifier/`)
- Automated test execution with pytest
- Static analysis with linting and type checking
- Semantic correctness validation
- Quality metrics calculation

### Record-Replay (`benchmark/replay/`)
- Execution trace capture and storage
- Deterministic replay functionality
- Prompt and tool I/O preservation
- Replay validation and verification

## Configuration

### System Configuration (`config/system.yaml`)
- Orchestrator-specific settings
- Safety and security policies
- VCS provider configuration
- Observability and telemetry settings
- Ollama model management

### Security Configuration (`config/injection_patterns.yaml`)
- Prompt injection detection patterns
- Code execution security rules
- Network and filesystem access policies
- Output filtering configurations

### Pricing Configuration (`config/model_pricing.yaml`)
- API model pricing (per 1K tokens)
- Local model cost estimation
- Hardware cost calculations
- Usage tracking and optimization

## Documentation

### User Guides (`docs/guides/`)
- `running_locally.md` - Docker + Ollama setup
- `vcs_setup.md` - GitHub/GitLab integration
- `safety.md` - Security policies and sandbox usage
- `benchmark.md` - CLI usage and result interpretation
- `telemetry.md` - Observability and Jaeger setup

### Developer Documentation
- `parity_matrix.md` - Framework comparison matrix
- API documentation for all interfaces
- Architecture diagrams and component interactions
- Contribution guidelines and development workflow

## Key Design Principles

1. **Standardization**: All orchestrators implement the same `AgentAdapter` interface
2. **Safety First**: All code execution goes through safety controls
3. **Observability**: Comprehensive telemetry and tracing throughout
4. **Reproducibility**: Deterministic execution with seed control
5. **Modularity**: Clear separation of concerns and component boundaries
6. **Extensibility**: Easy addition of new orchestrators and capabilities

## Development Workflow

1. **Common Components**: Shared functionality in `common/`
2. **Framework Adapters**: Implement `AgentAdapter` protocol
3. **Safety Integration**: Route all operations through safety controls
4. **VCS Integration**: Use unified VCS providers for repository operations
5. **Telemetry**: Emit events for all operations and state changes
6. **Testing**: Comprehensive unit, integration, and security tests
7. **Documentation**: Keep guides and API docs up to date

This structure provides a solid foundation for the enhanced AI Dev Squad Comparison platform with enterprise-grade capabilities for safety, observability, and reproducibility.