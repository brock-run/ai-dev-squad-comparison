# Project Organization & Structure

## Repository Structure

### Root Level Organization
```
ai-dev-squad-comparison/
├── README.md                    # Main project documentation
├── Makefile                     # Build automation and common commands
├── package.json                 # Next.js web interface dependencies
├── requirements-*.txt           # Python dependency specifications
├── test_all_implementations.py  # Cross-framework testing script
└── comprehensive_test_report.json # Latest test results
```

### Framework Implementations
Each AI framework has its own isolated implementation directory:

```
{framework}-implementation/
├── adapter.py              # AgentAdapter protocol implementation
├── agents/                 # Framework-specific agent definitions
│   ├── __init__.py
│   ├── architect_agent.py  # System design and planning
│   ├── developer_agent.py  # Code implementation
│   └── tester_agent.py     # Testing and validation
├── workflows/              # Orchestration and process definitions
├── tests/                  # Comprehensive test suite
│   ├── test_structure_only.py     # Structure validation
│   ├── test_{framework}_adapter.py # Adapter integration tests
│   └── mocks/              # Test fixtures and mocks
├── config/                 # Framework-specific configuration
├── requirements.txt        # Python dependencies
├── README.md              # Implementation documentation
├── COMPLETION_SUMMARY.md  # Development status and metrics
└── simple_integration_test.py # Basic functionality test
```

### Common Framework Layer
Shared utilities and interfaces used across all implementations:

```
common/
├── agent_api.py           # AgentAdapter protocol and base classes
├── config.py              # Configuration management system
├── config_cli.py          # Command-line configuration tools
├── ollama_integration.py  # Local LLM integration
├── safety/                # Security and safety controls
│   ├── execute.py         # Sandboxed code execution
│   ├── fs.py              # Filesystem access controls
│   ├── net.py             # Network access controls
│   ├── injection.py       # Prompt injection detection
│   └── policy.py          # Security policy management
├── vcs/                   # Version control integration
│   ├── base.py            # VCS provider interface
│   ├── github.py          # GitHub integration
│   ├── gitlab.py          # GitLab integration
│   └── commit_msgs.py     # AI-powered commit messages
└── telemetry/             # Monitoring and observability
```

### Configuration Management
Centralized configuration with environment-specific overrides:

```
config/
├── policies/              # Security policy definitions
│   ├── development.yaml   # Development environment settings
│   ├── production.yaml    # Production security controls
│   └── balanced.yaml      # Balanced development/security
├── *.example.yaml         # Configuration templates
└── system.example.yaml    # System-wide configuration template
```

### Documentation Structure
Comprehensive documentation organized by purpose:

```
docs/
├── technical-architecture.md    # System architecture overview
├── safety.md                   # Security and safety documentation
├── configuration.md            # Configuration guide
├── deployment-operations-guide.md # Operations manual
├── adr/                        # Architecture Decision Records
├── guides/                     # User and developer guides
├── requirements/               # Product requirements and specs
└── research/                   # Research and analysis documents
```

### Testing Infrastructure
Multi-layer testing approach with shared utilities:

```
tests/                     # Common test utilities
benchmark/                 # Performance benchmarking suite
comparison-results/        # Benchmark results and dashboard
examples/                  # Usage examples and demos
```

## Naming Conventions

### File Naming
- **Python files**: `snake_case.py`
- **TypeScript files**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Configuration files**: `kebab-case.yaml` or `snake_case.json`
- **Documentation**: `kebab-case.md`

### Directory Naming
- **Implementation directories**: `{framework}-implementation`
- **Common modules**: `snake_case`
- **Documentation sections**: `kebab-case`

### Code Conventions
- **Classes**: `PascalCase` (e.g., `AgentAdapter`, `LangGraphAdapter`)
- **Functions/Methods**: `snake_case` (e.g., `run_task`, `get_capabilities`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Variables**: `snake_case` (e.g., `task_result`, `config_manager`)

## Import Organization

### Standard Import Order
1. Standard library imports
2. Third-party library imports
3. Framework-specific imports
4. Common framework imports
5. Local module imports

### Example Import Structure
```python
# Standard library
import asyncio
import logging
from typing import Dict, Any, Optional

# Third-party
from pydantic import BaseModel

# Framework-specific
from langgraph.graph import StateGraph

# Common framework
from common.agent_api import AgentAdapter
from common.safety.execute import ExecutionSandbox

# Local
from .agents import DeveloperAgent
```

## Configuration Hierarchy

### Configuration Loading Order
1. Default values in code
2. System configuration files (`config/system.yaml`)
3. Framework-specific configuration
4. Environment variables
5. Runtime parameters

### Environment Variable Naming
- Prefix: `AI_DEV_SQUAD_`
- Structure: `AI_DEV_SQUAD_{SECTION}_{SUBSECTION}_{SETTING}`
- Example: `AI_DEV_SQUAD_SAFETY_SANDBOX_TYPE=docker`

## Development Workflow

### Branch Structure
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/{framework}-{description}`: Feature development
- `hotfix/{issue-description}`: Critical fixes

### Commit Message Format
Follow conventional commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
Scopes: `langgraph`, `crewai`, `common`, `safety`, `docs`, etc.

### File Organization Best Practices

1. **Keep implementations isolated**: Each framework should be self-contained
2. **Share common utilities**: Use the `common/` directory for shared code
3. **Maintain consistent structure**: Follow the established patterns
4. **Document everything**: Include comprehensive README files
5. **Test thoroughly**: Maintain high test coverage with multiple test types
6. **Version control**: Track all configuration and documentation changes