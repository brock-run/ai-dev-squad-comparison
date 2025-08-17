# LangGraph AI Development Squad Implementation

This directory contains the implementation of an AI development squad using LangGraph, a framework for building stateful, multi-agent applications with LangChain.

## Overview

LangGraph enables the creation of graph-based workflows where agents can collaborate through a defined state machine. This implementation demonstrates how to create a development squad with specialized agents (architect, developer, tester) that work together to complete software development tasks.

## Features

- Graph-based workflow with state management
- Specialized agents with different roles and capabilities
- Human-in-the-loop review process
- Integration with GitHub for code operations
- Local execution using Ollama models

## Setup Instructions

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download recommended Ollama models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull codellama:13b
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your GitHub token and other settings
   ```

## Directory Structure

- `agents/`: Contains the implementation of specialized agents
  - `architect.py`: Responsible for system design and architecture decisions
  - `developer.py`: Handles code implementation based on specifications
  - `tester.py`: Creates and runs tests for the implemented code
  
- `workflows/`: Contains the workflow definitions
  - `development_workflow.py`: Defines the state graph and transitions

## Usage

```python
from workflows.development_workflow import development_workflow

# Initialize the workflow
workflow = development_workflow()

# Run the workflow with a task
result = workflow.invoke({
    "task": "Build a Python function to calculate Fibonacci numbers",
    "requirements": ["Must handle negative numbers", "Should be optimized for performance"]
})

print(result)
```

## Performance Metrics

This implementation will be benchmarked against other frameworks using the standard test suite in the `comparison-results` directory.

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)