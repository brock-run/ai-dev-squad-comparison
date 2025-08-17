# Semantic Kernel AI Development Squad Implementation

This directory contains the implementation of an AI development squad using Semantic Kernel, a framework for building AI applications with plugins that can be used in both C# and Python.

## Overview

Semantic Kernel enables the creation of AI applications with a plugin-based architecture. This implementation demonstrates how to create a development squad with specialized AI agents (architect, developer, tester) that work together through Semantic Kernel plugins to complete software development tasks.

## Features

- Plugin-based architecture for agent capabilities
- Support for both C# and Python implementations
- Integration with Microsoft ecosystem
- Integration with GitHub for code operations
- Local execution using Ollama models

## Setup Instructions

### Python Implementation

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

### C# Implementation

1. Install .NET 7.0 SDK or later.

2. Build the project:
   ```bash
   dotnet build
   ```

3. Configure Ollama:
   - Ensure Ollama is running locally
   - Download recommended models:
     ```bash
     ollama pull llama3.1:8b
     ollama pull codellama:13b
     ```

4. Set up configuration:
   ```bash
   cp appsettings.example.json appsettings.json
   # Edit appsettings.json with your GitHub token and other settings
   ```

## Directory Structure

### Python Implementation

- `python/`: Contains the Python implementation
  - `plugins/`: Contains the implementation of specialized agent plugins
    - `architect_plugin/`: Responsible for system design and architecture decisions
    - `developer_plugin/`: Handles code implementation based on specifications
    - `tester_plugin/`: Creates and runs tests for the implemented code
  - `workflows/`: Contains the workflow definitions
    - `development_workflow.py`: Orchestrates the plugins for the development process

### C# Implementation

- `csharp/`: Contains the C# implementation
  - `Plugins/`: Contains the implementation of specialized agent plugins
    - `ArchitectPlugin/`: Responsible for system design and architecture decisions
    - `DeveloperPlugin/`: Handles code implementation based on specifications
    - `TesterPlugin/`: Creates and runs tests for the implemented code
  - `Workflows/`: Contains the workflow definitions
    - `DevelopmentWorkflow.cs`: Orchestrates the plugins for the development process

## Usage

### Python Implementation

```python
import semantic_kernel as sk
from workflows.development_workflow import create_development_kernel

# Initialize the kernel with plugins
kernel = create_development_kernel()

# Run the workflow with a task
result = kernel.run_async(
    "Build a Python function to calculate Fibonacci numbers. "
    "It must handle negative numbers and be optimized for performance."
)

print(result)
```

### C# Implementation

```csharp
using Microsoft.SemanticKernel;
using Workflows;

// Initialize the kernel with plugins
var kernel = DevelopmentWorkflow.CreateDevelopmentKernel();

// Run the workflow with a task
var result = await kernel.RunAsync(
    "Build a C# function to calculate Fibonacci numbers. " +
    "It must handle negative numbers and be optimized for performance."
);

Console.WriteLine(result);
```

## Performance Metrics

This implementation will be benchmarked against other frameworks using the standard test suite in the `comparison-results` directory.

## References

- [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
- [Semantic Kernel GitHub Repository](https://github.com/microsoft/semantic-kernel)