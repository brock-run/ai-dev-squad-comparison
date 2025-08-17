# CrewAI Development Squad Implementation

This directory contains the implementation of an AI development squad using CrewAI, a framework for orchestrating role-playing AI agents.

## Overview

CrewAI enables the creation of autonomous AI agents with specific roles, goals, and backstories that can collaborate to accomplish complex tasks. This implementation demonstrates how to create a development squad with specialized agents (architect, developer, tester) that work together to complete software development tasks.

## Features

- Role-based agent design with specialized capabilities
- Autonomous agent collaboration
- Sequential and hierarchical task execution
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
  - `development_process.py`: Defines the crew and task execution process

## Usage

```python
from crewai import Crew
from agents.architect import ArchitectAgent
from agents.developer import DeveloperAgent
from agents.tester import TesterAgent
from workflows.development_process import create_development_tasks

# Initialize agents
architect = ArchitectAgent()
developer = DeveloperAgent()
tester = TesterAgent()

# Create crew
dev_crew = Crew(
    agents=[architect, developer, tester],
    tasks=create_development_tasks(
        "Build a Python function to calculate Fibonacci numbers",
        ["Must handle negative numbers", "Should be optimized for performance"]
    )
)

# Execute the crew's tasks
result = dev_crew.kickoff()
print(result)
```

## Performance Metrics

This implementation will be benchmarked against other frameworks using the standard test suite in the `comparison-results` directory.

## References

- [CrewAI Documentation](https://docs.crewai.com)
- [CrewAI GitHub Repository](https://github.com/joaomdmoura/crewAI)