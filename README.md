# AI Dev Squad Comparison

A comprehensive comparison of different AI agent orchestration frameworks for building AI development squads. This project evaluates and contrasts various approaches to multi-agent orchestration in software development workflows.

## Overview

This project compares different frameworks for building AI development squads, including:

- **LangGraph**: A library for building stateful, multi-actor applications with LLMs
- **CrewAI**: A framework for orchestrating role-playing agents
- **AutoGen**: A framework for building LLM applications with multiple conversational agents
- **n8n**: A workflow automation platform with AI capabilities
- **Semantic Kernel**: A framework for building AI applications with plugins
- **Claude Code Subagents**: Extensive Claude Code subagent catalog for specialized roles. See [claude-code-subagents/agents/README.md](claude-code-subagents/agents/README.md)
- **Langroid**: A conversation-style multi-agent framework with turn-taking logic
- **LlamaIndex Agents**: Retrieval-augmented multi-agent workflows

Each implementation demonstrates how these frameworks can be used to create AI development teams with specialized roles (architects, developers, testers) that collaborate to accomplish software development tasks.

## Project Structure

```
ai-dev-squad-comparison/
├── README.md                                      # Project overview (this file)
├── docs/
│   ├── observability.md                           # Complete observability guide
│   ├── observability-user-guide.md                # Quick start user guide
│   ├── observability-developer-guide.md           # Technical integration guide
│   ├── benchmark/                                 # Benchmarking methodology
│   │   ├── benchmark_methodology.md               # Detailed benchmarking approach
│   │   └── unit_test_framework.md                 # Common test framework
│   ├── research/
│   │   ├── ai-orchestration-options.md            # Comprehensive comparison of frameworks
│   │   └── multi-agent-orchestration-details.md   # Detailed implementation guides
│   └── templates/
│       └── implementation_documentation_template.md # Documentation template
├── common/
│   ├── telemetry/                                 # Observability components
│   │   ├── logger.py                              # Structured logging
│   │   ├── otel.py                                # OpenTelemetry tracing
│   │   ├── cost_tracker.py                        # Cost and token tracking
│   │   └── dashboard.py                           # Web dashboard
│   ├── ollama_integration.py                      # Common Ollama integration module
│   └── ollama_config.json                         # Ollama configuration
├── benchmark/
│   ├── benchmark_suite.py                         # Benchmark implementation
│   └── requirements.txt                           # Benchmark dependencies
├── comparison-results/
│   ├── dashboard.py                               # Results visualization dashboard
│   └── requirements.txt                           # Dashboard dependencies
├── [framework]-implementation/                    # Framework-specific implementations
│   ├── README.md                                  # Framework-specific documentation
│   ├── requirements.txt                           # Framework-specific dependencies
│   ├── agents/                                    # Agent implementations
│   ├── workflows/                                 # Workflow definitions
│   └── tests/                                     # Framework-specific tests
```

## Getting Started

For a complete setup guide including observability configuration, see the [Getting Started Guide](docs/getting-started.md).

### Quick Start

1. **Clone and Setup**:
   ```bash
   git clone https://github.com/yourusername/ai-dev-squad-comparison.git
   cd ai-dev-squad-comparison
   ```

2. **Choose a Framework** (LangGraph recommended for beginners):
   ```bash
   cd langgraph-implementation
   pip install -r requirements.txt
   python simple_test.py
   ```

3. **Enable Observability** (optional but recommended):
   ```bash
   pip install opentelemetry-api opentelemetry-sdk flask flask-socketio
   python examples/dashboard_demo.py
   # Visit http://localhost:8080 for the dashboard
   ```

4. **Run Consistency Evaluation** (assess reliability):
   ```bash
   # Quick consistency check
   make consistency F=langgraph T=simple_code_generation
   
   # View results in dashboard
   make dashboard  # Navigate to /consistency tab
   
   # See quick reference for more options
   ```

### Prerequisites

- Python 3.8+ for Python-based implementations
- Node.js 14+ for n8n and JavaScript implementations
- .NET 7.0+ for C# Semantic Kernel implementation
- [Ollama](https://ollama.ai/) for local model execution

## Framework Implementations

Each framework implementation follows a consistent structure and includes:

- Specialized agents (Architect, Developer, Tester)
- Workflow orchestration
- Documentation and examples
- Tests and benchmarks

### LangGraph Implementation

LangGraph is a library for building stateful, multi-actor applications with LLMs. See [langgraph-implementation/README.md](langgraph-implementation/README.md) for details.

### CrewAI Implementation

CrewAI is a framework for orchestrating role-playing agents. See [crewai-implementation/README.md](crewai-implementation/README.md) for details.

### AutoGen Implementation

AutoGen is a framework for building LLM applications with multiple conversational agents. See [autogen-implementation/README.md](autogen-implementation/README.md) for details.

### n8n Implementation

n8n is a workflow automation platform with AI capabilities. See [n8n-implementation/README.md](n8n-implementation/README.md) for details.

### Semantic Kernel Implementation

Semantic Kernel is a framework for building AI applications with plugins. See [semantic-kernel-implementation/README.md](semantic-kernel-implementation/README.md) for details.

## Observability

The platform includes comprehensive observability capabilities for monitoring AI agent operations, costs, and performance:

- **Structured Logging**: JSON-formatted event tracking with filtering and real-time processing
- **OpenTelemetry Tracing**: Distributed tracing for agent operations and LLM interactions
- **Cost & Token Tracking**: Real-time cost monitoring with budget management and optimization recommendations
- **Enhanced Dashboard**: Web-based visualization with real-time updates and framework comparisons

### Quick Start with Observability

```python
from common.telemetry import (
    configure_logging,
    configure_tracing,
    configure_cost_tracking,
    create_dashboard
)

# Configure observability
logger = configure_logging(log_dir="logs", enable_console=True)
tracer = configure_tracing(service_name="my-ai-service")
cost_tracker = configure_cost_tracking(enable_budget_alerts=True)

# Start dashboard
dashboard = create_dashboard(host="localhost", port=8080)
dashboard.run()
```

For complete setup and usage instructions, see:
- [Observability User Guide](docs/observability-user-guide.md) - Quick start guide
- [Observability Guide](docs/observability.md) - Complete technical reference
- [Developer Guide](docs/observability-developer-guide.md) - Advanced integration patterns

## Ollama Integration

All implementations can use Ollama for local model execution. The common integration module provides:

- Consistent interface across frameworks
- Model management
- Performance tracking
- Role-specific configurations

To use Ollama integration:

```python
from common.ollama_integration import create_agent

# Create an agent for a specific role
architect = create_agent("architect")

# Generate content
design = architect.generate("Design a system for a real-time chat application")

# Chat with the agent
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What are the key components of a microservice architecture?"}
]
response = architect.chat(messages)
```

## Benchmarking and Verification

The project includes comprehensive benchmarking and verification systems for evaluating AI agent frameworks across multiple dimensions.

### Benchmarking System

The benchmarking system provides framework-agnostic evaluation across performance, quality, cost, and reliability metrics:

```python
from common.benchmarking import run_quick_benchmark, create_comprehensive_benchmark_suite

# Quick benchmark comparison
frameworks = ["langgraph", "crewai", "haystack"]
results = run_quick_benchmark(frameworks)

# Comprehensive evaluation
suite = create_comprehensive_benchmark_suite(frameworks)
# Includes coding, architecture, testing, and debugging tasks
```

**Key Features:**
- **Multi-dimensional evaluation**: Performance, quality, cost, reliability
- **Flexible task definitions**: Coding, architecture, testing, debugging, documentation
- **Comprehensive reporting**: Rankings, recommendations, outlier detection
- **Integration with observability**: Cost tracking, telemetry, caching

### Code Verification System

The verification system ensures code quality through multi-layered analysis:

```python
from benchmark.verifier import verify_function_complete, verify_code_strict

# Function verification with test cases
result = verify_function_complete(code, "factorial", test_cases, "recursion")

# Comprehensive verification (functional, static, semantic)
result = verify_code_strict(code, test_code=test_code, expected_functions=["main"])
```

**Verification Layers:**
- **Functional Testing**: Automated test execution with multiple frameworks
- **Static Analysis**: Linting, type checking, security scanning
- **Semantic Verification**: Logic correctness, algorithm verification, behavioral testing

### Running Benchmarks and Verification

```bash
# Install dependencies
pip install -r requirements.txt

# Run benchmarking demo
python examples/benchmarking_demo.py

# Run verification demo
python examples/verification_demo.py

# Run comprehensive tests
python -m pytest tests/test_benchmarking.py tests/test_verification_system.py -v
```

### Viewing Results

Access results through the enhanced dashboard:

```bash
cd comparison-results
python dashboard.py
# Open http://localhost:8050 for benchmarking results
# Open http://localhost:8080 for observability dashboard
```

For detailed guides, see:
- [Benchmarking User Guide](docs/guides/benchmarking-user-guide.md)
- [Verification User Guide](docs/guides/verification-user-guide.md)
- [Developer Guides](docs/guides/) for customization and extension

## Testing

Each implementation includes unit tests following the common test framework defined in [docs/benchmark/unit_test_framework.md](docs/benchmark/unit_test_framework.md).

To run tests for a specific implementation:

```bash
# For example, to run tests for the AutoGen implementation:
cd autogen-implementation
pytest
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature
3. Add your implementation or improvements
4. Add tests for your changes
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The creators and maintainers of all the frameworks compared in this project
- The open-source AI community for their valuable resources and tools

---

## Capabilities and Roadmap

This repository provides a practical, apples-to-apples comparison of multiple AI agent orchestration frameworks for software development squads. Here is what is implemented today and what is planned next.

### Implemented Capabilities (current state)
- **Comprehensive Benchmarking and Verification System**:
  - Multi-dimensional framework benchmarking (performance, quality, cost, reliability)
  - Advanced code verification with functional testing, static analysis, and semantic verification
  - Flexible task definitions for coding, architecture, testing, and debugging scenarios
  - Comprehensive reporting with rankings, recommendations, and outlier detection
  - See [Benchmarking User Guide](docs/guides/benchmarking-user-guide.md) and [Verification User Guide](docs/guides/verification-user-guide.md)
- **Self-Consistency Evaluation System**:
  - Multi-run reliability assessment with parallel execution
  - Multiple consensus strategies (majority, weighted, unanimous, threshold, best-of-n)
  - Comprehensive variance analysis (duration, tokens, quality scores)
  - Production readiness scoring with reliability labels (High/Medium/Low)
  - Dashboard integration with interactive visualizations and CI/CD support
  - See [Consistency User Guide](docs/guides/consistency-user-guide.md) and [Quick Reference](docs/consistency-quick-reference.md)
- **Comprehensive Observability System**:
  - Structured logging with JSON Lines format and event filtering
  - OpenTelemetry distributed tracing for agent operations
  - Real-time cost and token tracking with budget management
  - Enhanced web dashboard with live metrics and framework comparisons
  - See [Observability Guide](docs/observability.md) for complete documentation
- Consistent per-framework scaffolds with agents, workflows, and docs:
  - LangGraph: agents, workflow scaffold, tests present; see langgraph-implementation/README.md
  - CrewAI: agents and workflow scaffold; see crewai-implementation/README.md
  - AutoGen: agents, group chat manager scaffold, and tests; see autogen-implementation/README.md
  - n8n: visual workflow (JSON) and custom agent nodes; see n8n-implementation/README.md
  - Semantic Kernel: documented Python/C# structures; see semantic-kernel-implementation/README.md
- Common Ollama integration (local-first execution): common/ollama_integration.py with role-based model selection and shared parameters (see common/ollama_config.json)
- Benchmarking suite and dashboard:
  - Benchmarks: benchmark/benchmark_suite.py
  - Results visualization: comparison-results/dashboard.py
- Standard development workflows and prompts:
  - Workflows: workflows/development_workflow.md
  - Requirements and prompts: docs/requirements/*
- Documentation and planning artifacts:
  - PRD and methodology: docs/requirements/prd.md, docs/requirements/benchmark_methodology.md
  - Selection guide: docs/requirements/framework_selection_guide.md
  - Improvement plan: docs/plan.md

### Planned/Upcoming Enhancements
- Centralized GitHub integration utilities with retries/backoff and least-privilege auth
- Parity of tests across all frameworks with shared fixtures and deterministic runs
- Dependency pinning and Makefile targets for setup/test/bench/dash
- Confirm and/or scaffold Semantic Kernel Python and C# code to match README structure
- Unified configuration docs and .env.example parity across implementations

For details and the actionable backlog, see docs/enhancements.md. Raw review notes with TODO and POTENTIAL PROBLEM tags live in docs/review-scratchpad.md.

### Framework Status Snapshot (high level)
- LangGraph: In progress (agents, workflow, and tests present)
- CrewAI: In progress (agents and workflows)
- AutoGen: In progress (agents, group chat, tests)
- n8n: In progress (nodes and workflow JSON)
- Semantic Kernel: In progress (README structure; verify/scaffold code)
- Claude Code Subagents: Available as a prompt and role library; see claude-code-subagents/agents/README.md

## Deep Dives and Requirements
- Product Requirements: docs/requirements/prd.md
- Benchmark Methodology: docs/requirements/benchmark_methodology.md
- Framework Selection Guide: docs/requirements/framework_selection_guide.md
- Sample Agent Prompts: docs/requirements/sample_agent_prompts.md
- Research Prompt (for AI agent to extend this project): docs/research/agent_research_prompt.md
- Enhancements Backlog: docs/enhancements.md
- Review Scratchpad (raw notes): docs/review-scratchpad.md

Additional research documents:
- docs/research/ai-orchestration-options.md
- docs/research/multi-agent-orchestration-details.md

## Benchmark Quickstart (recap)
- Run benchmarks using benchmark/benchmark_suite.py (see section above). Results will populate comparison-results.
- Launch the dashboard from comparison-results/dashboard.py to explore comparisons.

## Contributing Roadmap
- Before contributing, review docs/plan.md and docs/enhancements.md to align with capability parity and benchmarking requirements.
- Contributions should include tests and a benchmark run where applicable to maintain comparability across frameworks.
