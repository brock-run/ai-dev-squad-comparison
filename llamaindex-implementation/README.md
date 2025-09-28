# LlamaIndex Agents Implementation

This directory contains the LlamaIndex Agents orchestrator implementation for the AI Dev Squad Comparison platform.

## Overview

LlamaIndex Agents provides retrieval-augmented workflows with:
- AgentWorkflow for structured agent operations
- Data-centric operations with context management
- Repository indexing for code and documentation retrieval
- Query engine integration for code understanding

## Setup

### Prerequisites
- Python 3.8+
- OpenAI API key or local LLM setup
- Sufficient disk space for document indexing

### Installation

1. **Install dependencies:**
```bash
cd llamaindex-implementation
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
# Optional: For local models
export OLLAMA_BASE_URL="http://localhost:11434"
```

3. **Validate installation:**
```bash
python validate_llamaindex.py
```

4. **Run integration test:**
```bash
python simple_integration_test.py
```

## Structure

```
llamaindex-implementation/
├── adapter.py              # AgentAdapter implementation
├── agents/                 # Agent definitions
├── workflows/              # Workflow configurations
├── indexing/               # Repository indexing utilities
├── tests/                  # Unit and integration tests
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Features

- Retrieval-augmented agent workflows
- Repository indexing for code and documentation
- Data-centric agent operations
- Query engine integration for code understanding
- Context management and retrieval optimization
- Comprehensive telemetry for retrieval operations

## Usage

The LlamaIndex implementation provides a powerful retrieval-augmented generation system for development tasks. Here's how to use it:

### Basic Usage

```python
from adapter import create_llamaindex_adapter

# Create adapter with configuration
config = {
    'language': 'python',
    'llamaindex': {
        'model': 'gpt-3.5-turbo',
        'embed_model': 'text-embedding-ada-002'
    }
}

adapter = create_llamaindex_adapter(config)

# Get capabilities
capabilities = await adapter.get_capabilities()
print(f"Features: {capabilities['features']}")

# Run a task
from common.agent_api import TaskSchema, TaskType

task = TaskSchema(
    id='example-task',
    type=TaskType.FEATURE_ADD,
    inputs={
        'description': 'Create a data processing pipeline',
        'requirements': [
            'Process CSV files',
            'Apply data transformations',
            'Generate summary reports'
        ]
    },
    repo_path='.',
    vcs_provider='github'
)

async for result in adapter.run_task(task):
    if hasattr(result, 'status'):
        print(f"Task completed: {result.status}")
        print(f"Generated code: {result.artifacts['output']['implementation']}")
```

### Advanced Configuration

Configure LlamaIndex-specific settings in `config/system.yaml`:

```yaml
orchestrators:
  llamaindex:
    enabled: true
    model_config:
      primary: "gpt-4"
      fallback: "gpt-3.5-turbo"
      embed_model: "text-embedding-ada-002"
    retrieval_config:
      top_k: 10
      similarity_threshold: 0.7
      chunk_size: 512
      chunk_overlap: 50
    timeout_seconds: 1800
    safety:
      enabled: true
      sandbox: true
```

### Repository Indexing

The implementation automatically indexes your repository for context-aware generation:

```python
# Index a repository
from indexing.repository_indexer import RepositoryIndexer

indexer = RepositoryIndexer(config)
result = await indexer.index_repository('/path/to/repo')

print(f"Indexed {result['files_indexed']} files")
print(f"Created {result['documents_processed']} document chunks")
```

### Query Processing

Use the query agent for semantic search:

```python
from agents.query_agent import QueryAgent

query_agent = QueryAgent(config)
result = await query_agent.query("How to implement authentication?", context)

print(f"Found {result['result_count']} relevant results")
for doc in result['search_results']:
    print(f"- {doc['source']}: {doc['content'][:100]}...")
```

### RAG Generation

Generate code with retrieved context:

```python
from agents.rag_agent import RAGAgent

rag_agent = RAGAgent(config)
result = await rag_agent.retrieve_and_generate(
    "Create a user authentication system",
    context={'requirements': ['JWT tokens', 'Password hashing']}
)

print(f"Generated {len(result['generated_response'])} characters of code")
print(f"Used {result['context_used']} context sources")
```

## Architecture

The LlamaIndex implementation follows a modular architecture:

### Core Components

1. **LlamaIndexAdapter**: Main adapter implementing the AgentAdapter protocol
2. **RetrievalWorkflow**: Orchestrates the RAG pipeline
3. **Specialized Agents**: RAG, Query, and Indexing agents
4. **RepositoryIndexer**: Handles document processing and vector store creation
5. **Safety Integration**: Comprehensive security controls

### RAG Pipeline

1. **Repository Indexing**: Documents are processed and indexed
2. **Query Processing**: User queries are analyzed and enhanced
3. **Context Retrieval**: Relevant documents are retrieved via vector similarity
4. **Code Generation**: LLM generates code using retrieved context
5. **Result Assembly**: Final output is formatted and validated

### Agent Specialization

- **RAG Agent**: Handles retrieval-augmented generation tasks
- **Query Agent**: Processes queries with semantic search
- **Indexing Agent**: Manages repository indexing and vector stores

## Development

To work on the LlamaIndex implementation:

### Setup Development Environment

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
export OPENAI_API_KEY="your-api-key"
export LLAMAINDEX_CACHE_DIR="./cache"
```

3. **Run validation:**
```bash
python validate_llamaindex.py
```

### Testing

Run the comprehensive test suite:

```bash
# Structure tests
python tests/test_structure_only.py

# Integration tests
python simple_integration_test.py

# Full test suite
pytest tests/ -v
```

### Code Structure

Follow these guidelines when contributing:

- **Agents**: Implement specific functionality (RAG, Query, Indexing)
- **Workflows**: Orchestrate multi-step processes
- **Indexing**: Handle document processing and vector operations
- **Safety**: Integrate security controls throughout
- **Testing**: Maintain comprehensive test coverage

### Performance Optimization

The implementation includes several performance optimizations:

- **Lazy Loading**: Components are initialized only when needed
- **Caching**: Vector embeddings and query results are cached
- **Chunking**: Documents are intelligently chunked for optimal retrieval
- **Batch Processing**: Multiple documents processed in batches

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure LlamaIndex is installed: `pip install llama-index`
2. **API Key Issues**: Set OPENAI_API_KEY environment variable
3. **Memory Issues**: Reduce chunk_size in configuration
4. **Slow Indexing**: Enable caching and use smaller document sets for testing

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring

Monitor performance with built-in metrics:

```python
metrics = await adapter.get_metrics()
print(f"Tasks completed: {metrics['tasks']['completed']}")
print(f"Retrieval operations: {metrics['retrieval']['retrieval_operations']}")
print(f"Documents indexed: {metrics['retrieval']['documents_indexed']}")
```