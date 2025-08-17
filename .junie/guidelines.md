# AI Dev Squad Comparison Project Guidelines

## Project Overview

This project compares different AI agent orchestration frameworks for building AI development squads. The goal is to evaluate and contrast various approaches to multi-agent orchestration in software development workflows, including frameworks like LangGraph, CrewAI, AutoGen, n8n, OpenAI Swarm, and Semantic Kernel.

The repository contains research documents and implementation examples that demonstrate how these frameworks can be used to create AI development teams with specialized roles (architects, developers, testers, etc.) that collaborate to accomplish software development tasks.

## Project Structure

```
ai-dev-squad-comparison/
├── README.md                                      # Project overview
├── docs/
│   └── research/
│       ├── ai-orchestration-options.md            # Comprehensive comparison of frameworks
│       └── multi-agent-orchestration-details.md   # Detailed implementation guides
├── [framework]-implementation/                    # Implementation directories (to be created)
│   ├── requirements.txt
│   ├── agents/
│   └── workflows/
└── comparison-results/                            # Comparison metrics (to be created)
```

## Development Guidelines

### Implementation Requirements

When implementing new framework examples:

1. **Environment Setup**: 
   - Use virtual environments for Python implementations
   - Include detailed setup instructions in each implementation directory
   - Support Ollama for local model execution where possible

2. **Code Structure**:
   - Organize code by framework in separate directories
   - Maintain consistent structure across implementations for easier comparison
   - Include comprehensive comments and documentation

3. **Testing**:
   - Create simple test cases that demonstrate the capabilities of each framework
   - Include scripts to verify the functionality of agent workflows
   - Document expected outputs and performance characteristics

### Testing Instructions

For testing implementations:

1. **Local Testing**:
   - Test with Ollama using recommended models (llama3.1:8b, codellama:13b, etc.)
   - Verify that agents can communicate and collaborate effectively
   - Test with simple development tasks before complex workflows

2. **Integration Testing**:
   - Test GitHub integration where applicable
   - Verify that agents can access and modify repository content
   - Ensure proper error handling for API rate limits and authentication issues

### Build Instructions

No specific build process is required for this project. Each implementation should include:

1. Clear installation instructions in a README.md file
2. Requirements.txt or equivalent dependency management
3. Step-by-step setup guide for the specific framework

## Code Style Guidelines

1. **Python Code**:
   - Follow PEP 8 style guidelines
   - Use type hints where appropriate
   - Document functions and classes with docstrings

2. **JavaScript/TypeScript Code** (for n8n implementations):
   - Follow standard JS/TS style guidelines
   - Use async/await for asynchronous operations
   - Document functions with JSDoc comments

3. **Documentation**:
   - Use Markdown for all documentation
   - Include code examples with syntax highlighting
   - Document configuration options and environment variables

## Contribution Guidelines

When contributing to this project:

1. Create a new branch for each implementation or feature
2. Include comprehensive documentation for your implementation
3. Add your implementation to the comparison metrics in the comparison-results directory
4. Update the main README.md with information about your implementation

## Resources

- [Ollama Documentation](https://ollama.com/docs)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- Framework-specific documentation:
  - [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
  - [CrewAI Documentation](https://docs.crewai.com)
  - [AutoGen Documentation](https://microsoft.github.io/autogen/)
  - [n8n Documentation](https://docs.n8n.io)
  - [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)