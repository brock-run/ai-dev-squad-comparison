# AI Coding Rules for AI Dev Squad Comparison Project

This document defines the coding standards, architectural guidelines, and best practices for AI agents working on the AI Dev Squad Comparison project. These rules should be followed by all AI assistants and agents when generating or modifying code.

## Language and Framework Standards

### Python Code
- Use Python 3.10+ for all Python implementations
- Follow PEP 8 style guidelines (4-space indentation, 79-character line limit)
- Use type hints for all function signatures and class attributes
- Document all functions, classes, and modules with Google-style docstrings
- Use f-strings for string formatting instead of older methods
- Prefer explicit imports over wildcard imports
- Use virtual environments for dependency management

### C# Code (Semantic Kernel)
- Use C# 10.0+ with .NET 7.0+
- Follow Microsoft C# coding conventions
- Use async/await for asynchronous operations
- Document public APIs with XML comments
- Use nullable reference types
- Implement proper exception handling with specific exception types

### JavaScript/TypeScript (n8n)
- Use TypeScript where possible
- Follow standard JS/TS style guidelines
- Use async/await for asynchronous operations
- Document functions with JSDoc comments
- Use ES6+ features (arrow functions, destructuring, etc.)
- Implement proper error handling

## Architecture Guidelines

### General Principles
- Separate configuration from implementation
- Use dependency injection where appropriate
- Create clear interfaces between components
- Implement proper error handling and logging
- Write unit tests for all core functionality

### Framework-Specific Patterns

#### LangGraph
- Use StateGraph for workflow definition
- Implement proper state management
- Define clear transitions between agents
- Use tools for external integrations
- Implement human-in-the-loop capabilities where needed

#### CrewAI
- Define agents with clear roles, goals, and backstories
- Use tasks with explicit expected outputs
- Implement proper context sharing between tasks
- Use sequential process for development workflows

#### AutoGen
- Use specialized agents for different roles
- Implement group chat for agent collaboration
- Configure proper code execution environments
- Use human feedback mechanisms

#### n8n
- Create modular workflow nodes
- Implement proper error handling for each node
- Use MCP for agent-to-agent communication
- Document node inputs and outputs

#### Semantic Kernel
- Use plugin architecture for agent capabilities
- Implement proper memory management
- Use semantic functions with clear prompts
- Support both C# and Python implementations

## Code Organization

### Directory Structure
- Organize code by framework in separate directories
- Use consistent structure across implementations
- Keep configuration files separate from implementation
- Store agent definitions in dedicated files

### File Naming
- Use snake_case for Python files and directories
- Use PascalCase for C# files and directories
- Use camelCase for JavaScript/TypeScript files

## Documentation Standards

- Document all code with appropriate comments
- Include setup instructions in README.md files
- Document configuration options and environment variables
- Include examples for common use cases
- Document expected outputs and performance characteristics

## Security Guidelines

- Never hardcode credentials or API keys
- Use environment variables for sensitive information
- Implement proper authentication for GitHub integration
- Validate all user inputs
- Handle errors securely without exposing sensitive information

## Performance Considerations

- Optimize prompts for token efficiency
- Implement caching where appropriate
- Use streaming responses for long-running operations
- Monitor and log token usage
- Implement rate limiting for external API calls

## Testing Requirements

- Write unit tests for all core functionality
- Create integration tests for agent workflows
- Document expected outputs for test cases
- Implement performance benchmarks
- Test with different Ollama models

## Do's and Don'ts

### Do
- Use consistent coding style across implementations
- Document all code thoroughly
- Implement proper error handling
- Write modular, reusable code
- Test with different inputs and edge cases

### Don't
- Mix different coding styles
- Hardcode credentials or sensitive information
- Create overly complex implementations
- Ignore error handling
- Implement framework-specific features that can't be compared

## Agent Autonomy Boundaries

AI agents may:
- Generate code for isolated modules
- Suggest improvements to existing code
- Create test cases and documentation
- Analyze code for bugs and performance issues

AI agents may not:
- Modify security-related configuration
- Change core architecture without approval
- Modify CI/CD pipelines
- Access or modify sensitive information