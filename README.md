# AI Dev Squad Comparison

A comprehensive comparison of different AI agent orchestration frameworks for building AI development squads. This project evaluates and contrasts various approaches to multi-agent orchestration in software development workflows.

## Overview

This project compares different frameworks for building AI development squads, including:

- **LangGraph**: A library for building stateful, multi-actor applications with LLMs
- **CrewAI**: A framework for orchestrating role-playing agents
- **AutoGen**: A framework for building LLM applications with multiple conversational agents
- **n8n**: A workflow automation platform with AI capabilities
- **Semantic Kernel**: A framework for building AI applications with plugins

Each implementation demonstrates how these frameworks can be used to create AI development teams with specialized roles (architects, developers, testers) that collaborate to accomplish software development tasks.

## Project Structure

```
ai-dev-squad-comparison/
├── README.md                                      # Project overview (this file)
├── docs/
│   ├── benchmark/                                 # Benchmarking methodology
│   │   ├── benchmark_methodology.md               # Detailed benchmarking approach
│   │   └── unit_test_framework.md                 # Common test framework
│   ├── research/
│   │   ├── ai-orchestration-options.md            # Comprehensive comparison of frameworks
│   │   └── multi-agent-orchestration-details.md   # Detailed implementation guides
│   └── templates/
│       └── implementation_documentation_template.md # Documentation template
├── common/
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

### Prerequisites

- Python 3.8+ for Python-based implementations
- Node.js 14+ for n8n and JavaScript implementations
- .NET 7.0+ for C# Semantic Kernel implementation
- [Ollama](https://ollama.ai/) for local model execution

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-dev-squad-comparison.git
   cd ai-dev-squad-comparison
   ```

2. Set up Ollama:
   ```bash
   # Install Ollama following instructions at https://ollama.ai/
   
   # Pull recommended models
   ollama pull llama3.1:8b
   ollama pull codellama:13b
   ```

3. Install framework-specific dependencies:
   ```bash
   # For example, to set up the LangGraph implementation:
   cd langgraph-implementation
   pip install -r requirements.txt
   ```

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

## Benchmarking

The project includes a comprehensive benchmarking suite to compare the performance of different implementations.

### Running Benchmarks

```bash
# Install benchmark dependencies
cd benchmark
pip install -r requirements.txt

# Run benchmarks for a specific framework
python benchmark_suite.py langgraph langgraph-implementation

# Run benchmarks for all frameworks
python benchmark_suite.py --all
```

### Viewing Results

The benchmark results are stored in the `comparison-results` directory. You can view them using the dashboard:

```bash
cd comparison-results
pip install -r requirements.txt
python dashboard.py
```

Then open your browser to http://localhost:8050 to view the dashboard.

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