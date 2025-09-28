# Haystack RAG Development Squad

This directory contains the implementation of the AgentAdapter using Haystack AI framework with RAG-enhanced multi-agent workflows.

## Overview

Haystack AI provides a powerful framework for building RAG (Retrieval-Augmented Generation) applications with pipeline-based architecture. This implementation creates a comprehensive RAG-enhanced development squad that combines document retrieval with specialized agents for different development tasks.

## Features

- **RAG-Enhanced Development**: Document retrieval augments all development phases
- **Multi-Agent Coordination**: Specialized agents for research, architecture, and implementation
- **Pipeline Orchestration**: Structured workflows with knowledge integration
- **Safety Controls**: Integrated security policies and sandboxing
- **VCS Integration**: GitHub/GitLab support with intelligent commit messages
- **Comprehensive Telemetry**: Detailed metrics and event tracking
- **Fallback Modes**: Graceful degradation when components unavailable

## Key Features

### RAG-Enhanced Workflows
- **Document Store Integration**: In-memory knowledge base with development best practices
- **Retrieval-Augmented Generation**: Context-aware responses using retrieved knowledge
- **Pipeline Orchestration**: Specialized pipelines for research, implementation, review, and testing
- **Knowledge Augmentation**: All agent responses enhanced with relevant documentation

### Specialized Agents
- **Research Agent**: Knowledge gathering and analysis with document retrieval
- **Knowledge Architect Agent**: System design using retrieved architectural patterns
- **RAG Developer Agent**: Code implementation with best practices integration
- **Pipeline Coordination**: Seamless knowledge sharing between agents

### Advanced Capabilities
- **Safety Controls**: Integrated security policies and sandboxing
- **VCS Integration**: GitHub/GitLab support with intelligent commit messages
- **Comprehensive Telemetry**: Detailed metrics and event tracking
- **Fallback Modes**: Graceful degradation when components unavailable

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Haystack RAG Squad                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Research   │  │ Knowledge   │  │    RAG      │     │
│  │   Agent     │  │ Architect   │  │ Developer   │     │
│  │             │  │   Agent     │  │   Agent     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Research   │  │Implementat. │  │   Review    │     │
│  │  Pipeline   │  │  Pipeline   │  │  Pipeline   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │           Document Store & Retrieval            │   │
│  │    (Development Knowledge & Best Practices)     │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Safety    │  │     VCS     │  │ Telemetry   │     │
│  │  Controls   │  │Integration  │  │   System    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Structure

```
haystack-implementation/
├── adapter.py                           # Main RAG adapter implementation
├── agents/                              # Specialized RAG agents
│   ├── rag_developer_agent.py          # RAG-enhanced code implementation
│   ├── knowledge_architect_agent.py    # Architecture with knowledge retrieval
│   └── research_agent.py               # Knowledge gathering and analysis
├── pipelines/                           # RAG pipelines
│   └── development_pipeline.py         # Development workflow pipelines
├── tests/                               # Comprehensive test suite
│   └── test_haystack_adapter.py        # Adapter and RAG functionality tests
├── simple_integration_test.py          # Quick integration verification
├── requirements.txt                     # Dependencies with RAG support
└── README.md                           # This documentation
```

## Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- Optional: GitHub/GitLab tokens for VCS integration

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
export GITHUB_TOKEN="your-github-token"  # Optional
export GITLAB_TOKEN="your-gitlab-token"  # Optional
```

3. **Run integration test:**
```bash
python simple_integration_test.py
```

4. **Run comprehensive tests:**
```bash
python -m pytest tests/ -v
```

## Usage

### Basic Usage

```python
from adapter import HaystackAdapter

# Initialize RAG-enhanced adapter
adapter = HaystackAdapter()

# Get adapter information
info = await adapter.get_info()
print(f"RAG Squad: {info['name']} v{info['version']}")
print(f"Agents: {list(info['agents'].keys())}")
print(f"RAG Features: {info['rag_features']}")

# Check health and RAG components
health = await adapter.health_check()
print(f"Status: {health['status']}")
print(f"Document Store: {health['components']['document_store']['document_count']} docs")
```

### Task Execution with RAG

```python
from common.agent_api import TaskSchema

# Create a development task
task = TaskSchema(
    id="rag-enhanced-task",
    type="code_generation",
    inputs={
        "description": "Create a user authentication system",
        "requirements": [
            "Support email/password authentication",
            "Include password hashing",
            "Add session management",
            "Implement security best practices"
        ]
    }
)

# Execute with RAG enhancement
async for result in adapter.run_task(task):
    if result.status == "completed":
        print("RAG-Enhanced Results:")
        print(f"- Research: {result.result['research'][:100]}...")
        print(f"- Architecture: {result.result['architecture'][:100]}...")
        print(f"- Implementation: {result.result['implementation'][:100]}...")
        print(f"- RAG Queries: {result.result['rag_queries']}")
        print(f"- Documents Retrieved: {result.result['document_retrievals']}")
```

## Configuration

Configure Haystack-specific settings in `config/system.yaml`:

```yaml
orchestrators:
  haystack:
    enabled: true
    model_config:
      primary: "gpt-3.5-turbo"
      fallback: "gpt-3.5-turbo"
    timeout_seconds: 1800
    rag:
      document_store: "inmemory"
      retriever: "bm25"
      top_k: 5
      temperature: 0.7
```

## Development

To work on the Haystack RAG implementation:

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest tests/ -v`
3. Run integration test: `python simple_integration_test.py`
4. Follow the AgentAdapter protocol defined in `common/agent_api.py`
5. Ensure RAG components are properly integrated with safety controls