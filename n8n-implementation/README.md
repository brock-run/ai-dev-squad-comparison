# n8n AI Development Squad Implementation

This directory contains the implementation of an AI development squad using n8n, a workflow automation platform that can be used to orchestrate AI agents through visual workflows.

## Overview

n8n enables the creation of visual workflows that connect different services and APIs. This implementation demonstrates how to create a development squad with specialized AI agents (architect, developer, tester) that work together through n8n workflows to complete software development tasks.

## Features

- Visual workflow design for agent orchestration
- Integration with external tools and services
- Agent-to-agent communication through workflow nodes
- Integration with GitHub for code operations
- Local execution using Ollama models

## Setup Instructions

1. Install n8n:
   ```bash
   npm install
   ```

2. Start n8n:
   ```bash
   npx n8n start
   ```

3. Import the workflows from the `workflows` directory.

4. Configure Ollama:
   - Ensure Ollama is running locally
   - Download recommended models:
     ```bash
     ollama pull llama3.1:8b
     ollama pull codellama:13b
     ```

5. Set up environment variables in n8n:
   - GitHub API token
   - Ollama API endpoint
   - Other required credentials

## Directory Structure

- `agents/`: Contains the implementation of specialized agent nodes
  - `architect_node.js`: Responsible for system design and architecture decisions
  - `developer_node.js`: Handles code implementation based on specifications
  - `tester_node.js`: Creates and runs tests for the implemented code
  
- `workflows/`: Contains the workflow definitions
  - `development_workflow.json`: Defines the complete development process workflow

## Usage

1. Open the n8n web interface (typically at http://localhost:5678).
2. Import the development workflow from `workflows/development_workflow.json`.
3. Configure the workflow with your GitHub credentials and other settings.
4. Activate the workflow.
5. Trigger the workflow with a webhook or manually with input data:
   ```json
   {
     "task": "Build a JavaScript function to calculate Fibonacci numbers",
     "requirements": ["Must handle negative numbers", "Should be optimized for performance"]
   }
   ```

## Performance Metrics

This implementation will be benchmarked against other frameworks using the standard test suite in the `comparison-results` directory.

## References

- [n8n Documentation](https://docs.n8n.io)
- [n8n GitHub Repository](https://github.com/n8n-io/n8n)