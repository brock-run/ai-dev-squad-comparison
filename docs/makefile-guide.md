# AI Dev Squad Comparison Makefile Guide

## Introduction

The AI Dev Squad Comparison project includes a comprehensive Makefile that automates common tasks related to installation, testing, execution, and maintenance of the project. This document explains what the Makefile does and how to use it effectively.

The Makefile serves as a central automation tool for the project, providing consistent commands across different framework implementations (AutoGen, CrewAI, LangGraph, n8n, and Semantic Kernel). It simplifies complex operations and ensures that all dependencies and configurations are properly set up.

## Makefile Structure

The Makefile is organized into several logical sections:

1. **Configuration Variables**: Defines interpreters, commands, and directory paths
2. **Help Target**: Provides comprehensive help information (default target)
3. **Installation Targets**: For installing dependencies for each framework
4. **Testing Targets**: For running tests across frameworks
5. **Execution Targets**: For benchmarking, dashboard, and examples
6. **Utility Targets**: For Ollama setup, cleaning, and virtual environments

Each section contains related targets that can be invoked with the `make` command.

## Configuration Variables

The Makefile defines several configuration variables that are used throughout the targets:

```makefile
# Shell to use for commands
SHELL := /bin/bash

# Interpreters and commands
PYTHON := python3      # Python interpreter
NODE := node           # Node.js interpreter
DOTNET := dotnet       # .NET CLI
OLLAMA := ollama       # Ollama command for LLM management

# Directory paths
ROOT_DIR := $(shell pwd)
AUTOGEN_DIR := $(ROOT_DIR)/autogen-implementation
CREWAI_DIR := $(ROOT_DIR)/crewai-implementation
LANGGRAPH_DIR := $(ROOT_DIR)/langgraph-implementation
N8N_DIR := $(ROOT_DIR)/n8n-implementation
SEMANTIC_KERNEL_DIR := $(ROOT_DIR)/semantic-kernel-implementation
BENCHMARK_DIR := $(ROOT_DIR)/benchmark
COMPARISON_DIR := $(ROOT_DIR)/comparison-results
COMMON_DIR := $(ROOT_DIR)/common
```

These variables ensure consistency across targets and make it easy to update paths or commands if needed.

## Help Target (Default)

The `help` target is the default target that runs when you type `make` without any arguments. It displays comprehensive help information about all available targets:

```bash
$ make
```

This will show a formatted list of all available targets organized by category (Installation, Testing, Execution, and Utilities), along with examples of common usage patterns.

## Installation Targets

The installation targets handle the installation of dependencies for each framework implementation, benchmarking tools, and the visualization dashboard:

### Main Installation Targets

- `make install`: Installs all dependencies for all frameworks, benchmarking, and dashboard
- `make install-framework F=<framework>`: Installs dependencies for a specific framework
- `make install-benchmark`: Installs benchmark dependencies
- `make install-dashboard`: Installs dashboard dependencies
- `make venv`: Creates a Python virtual environment

### Framework-Specific Installation Targets

- `make install-autogen`: Installs AutoGen dependencies
- `make install-crewai`: Installs CrewAI dependencies
- `make install-langgraph`: Installs LangGraph dependencies
- `make install-n8n`: Installs n8n dependencies
- `make install-semantic-kernel`: Installs Semantic Kernel dependencies (both Python and C#)

### Usage Examples

```bash
# Install all dependencies
$ make install

# Install dependencies for a specific framework
$ make install-framework F=autogen

# Create a virtual environment
$ make venv
```

## Testing Targets

The testing targets run tests for each framework implementation to ensure functionality is working as expected:

### Main Testing Targets

- `make test`: Runs all tests across all frameworks
- `make test-framework F=<framework>`: Runs tests for a specific framework

### Framework-Specific Testing Targets

- `make test-autogen`: Runs AutoGen tests
- `make test-crewai`: Runs CrewAI tests
- `make test-langgraph`: Runs LangGraph tests
- `make test-n8n`: Runs n8n tests
- `make test-semantic-kernel`: Runs Semantic Kernel tests (both Python and C#)

### Usage Examples

```bash
# Run all tests
$ make test

# Run tests for a specific framework
$ make test-framework F=langgraph
```

## Execution Targets

The execution targets run benchmarks, start the visualization dashboard, and execute example workflows for each framework implementation:

### Benchmark Targets

- `make benchmark`: Runs all benchmarks across all frameworks
- `make benchmark-framework F=<framework>`: Runs benchmarks for a specific framework

### Dashboard Target

- `make dashboard`: Starts the comparison dashboard web application

### Example Execution Target

- `make run-example F=<framework>`: Runs an example workflow for a specific framework

### Usage Examples

```bash
# Run all benchmarks
$ make benchmark

# Run benchmarks for a specific framework
$ make benchmark-framework F=crewai

# Start the dashboard
$ make dashboard

# Run an example for a specific framework
$ make run-example F=semantic-kernel
```

## Utility Targets

The utility targets provide helper functions such as setting up Ollama models, cleaning temporary files, and creating virtual environments:

### Ollama Setup Target

- `make setup-ollama`: Sets up Ollama with the required models for the project

### Cleaning Targets

- `make clean`: Cleans up temporary Python and test files
- `make clean-all`: Cleans up all build artifacts including virtual environments and dependencies

### Usage Examples

```bash
# Set up Ollama with required models
$ make setup-ollama

# Clean temporary files
$ make clean

# Clean all build artifacts
$ make clean-all
```

## Common Usage Patterns

Here are some common usage patterns for the Makefile:

### Initial Setup

```bash
# Create a virtual environment
$ make venv

# Activate the virtual environment
$ source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
$ make install

# Set up Ollama with required models
$ make setup-ollama
```

### Development Workflow

```bash
# Install dependencies for the framework you're working on
$ make install-framework F=autogen

# Run tests for the framework
$ make test-framework F=autogen

# Run an example for the framework
$ make run-example F=autogen
```

### Benchmarking and Comparison

```bash
# Run benchmarks for all frameworks
$ make benchmark

# Start the dashboard to visualize results
$ make dashboard
```

### Cleanup

```bash
# Clean temporary files
$ make clean

# Clean all build artifacts when needed
$ make clean-all
```

## Troubleshooting

Here are solutions to common issues you might encounter when using the Makefile:

### Missing Dependencies

If you encounter errors about missing dependencies:

```bash
# Make sure you've installed all dependencies
$ make install

# For a specific framework
$ make install-framework F=<framework>
```

### Ollama Model Issues

If you encounter issues with Ollama models:

```bash
# Make sure Ollama is installed and running
$ ollama list

# Set up the required models
$ make setup-ollama
```

### Framework-Specific Issues

If you encounter issues with a specific framework:

```bash
# Clean and reinstall the framework
$ make clean
$ make install-framework F=<framework>
```

### Path Issues

If the Makefile can't find certain directories or files:

```bash
# Make sure you're running make from the project root directory
$ cd /path/to/ai-dev-squad-comparison
$ make <target>
```

## Extending the Makefile

If you need to add new targets or modify existing ones:

1. Follow the existing structure and naming conventions
2. Add appropriate documentation comments
3. Update the `help` target if adding new categories
4. Test your changes with various inputs

## Conclusion

The Makefile provides a consistent and convenient interface for working with the AI Dev Squad Comparison project. By using these targets, you can streamline your workflow and ensure that all components are properly set up and tested.

For more information about the project itself, refer to the main [README.md](../README.md) file.