# AI Dev Squad Comparison — Product Requirements Document _(Last updated: 2025-08-11)_

## 1. Introduction
- **Team**: AI Platform Dev Group
- **Linked Docs**: [Guidelines](/.junie/guidelines.md), [AI Orchestration Options](/docs/research/ai-orchestration-options.md), [Multi-Agent Orchestration Details](/docs/research/multi-agent-orchestration-details.md)
- **Status**: V1.0

## 2. Problem Statement(s)
Software development teams struggle to effectively implement and compare different AI agent orchestration frameworks for building AI development squads. There's a lack of standardized examples and comparison metrics to evaluate the strengths and weaknesses of frameworks like LangGraph, CrewAI, AutoGen, n8n, OpenAI Swarm, and Semantic Kernel in software development workflows.

## 3. Goals
- Provide standardized implementations of AI development squads across major frameworks
- Enable objective comparison of framework capabilities, performance, and ease of use
- Support local execution with Ollama for accessibility and cost-effectiveness
- Demonstrate practical integration with GitHub for real-world development workflows

## 4. User Stories

| Story | Description | Priority | Acceptance Criteria |
|-------|-------------|----------|---------------------|
| Framework Comparison | As a developer, I want to compare different AI agent orchestration frameworks to select the best one for my project | P0 | See acceptance below |
| Local Execution | As a developer, I want to run AI agent squads locally using Ollama to reduce costs and maintain privacy | P0 | See acceptance below |
| GitHub Integration | As a developer, I want AI agents to interact with GitHub repositories for code analysis and generation | P1 | See acceptance below |
| Performance Metrics | As a technical lead, I want objective metrics to evaluate the performance of different frameworks | P1 | See acceptance below |

- **Framework Comparison Acceptance:**
  - [ ] Each framework has a complete, working implementation with the same core functionality
  - [ ] Documentation clearly explains the strengths and weaknesses of each approach
  - [ ] Code structure is consistent across implementations for fair comparison
  - [ ] Edge case: Handles frameworks with different programming language requirements (e.g., C# for Semantic Kernel)

- **Local Execution Acceptance:**
  - [ ] All implementations support Ollama with recommended models
  - [ ] Setup instructions include model download and configuration steps
  - [ ] Performance benchmarks compare execution time and resource usage
  - [ ] Edge case: Gracefully handles limited local resources with fallback options

- **GitHub Integration Acceptance:**
  - [ ] Agents can clone repositories, analyze code, and create pull requests
  - [ ] Authentication uses secure token management
  - [ ] Rate limiting and error handling are implemented
  - [ ] Edge case: Handles repository access permission issues with clear error messages

- **Performance Metrics Acceptance:**
  - [ ] Standard test cases are defined for benchmarking all frameworks
  - [ ] Metrics include execution time, token usage, and success rate
  - [ ] Results are presented in a comparable format (tables, charts)
  - [ ] Edge case: Accounts for different pricing models and resource requirements

## 5. Technical Requirements
- Python 3.10+ for Python-based implementations
- .NET 7.0+ for Semantic Kernel C# implementation
- Docker support for containerized execution
- Ollama for local LLM execution
- GitHub API integration for repository operations
- Standardized logging for performance measurement

## 6. Features/Modules

### 6.1 Framework Implementations
- **Objective**: Create standardized implementations of AI development squads for each framework.
- **Subtasks**:
    1. LangGraph Implementation
       - Description: Implement a development squad using LangGraph with architect, developer, and tester agents.
       - Acceptance Criteria: [ ] Follows graph-based workflow [ ] Supports human-in-the-loop review [ ] Includes state management
       - Implementation: Create a StateGraph with specialized agents and defined transitions between development phases.
       - Example Input/Output:
         ```
         Input: "Build a Python function to calculate Fibonacci numbers"
         Output: Complete implementation with tests and documentation
         ```
       - Estimated effort: 3d

    2. CrewAI Implementation
       - Description: Implement a development squad using CrewAI with role-based agents.
       - Acceptance Criteria: [ ] Uses CrewAI's role-based approach [ ] Implements autonomous collaboration [ ] Supports sequential process
       - Implementation: Define agents with specific roles, goals, and backstories, and create tasks with expected outputs.
       - Estimated effort: 2d

    3. AutoGen Implementation
       - Description: Implement a development squad using AutoGen with conversational agents.
       - Acceptance Criteria: [ ] Uses group chat for agent collaboration [ ] Supports code execution [ ] Implements human feedback
       - Implementation: Create specialized agents and a group chat manager for orchestration.
       - Estimated effort: 2d

    4. n8n Implementation
       - Description: Implement a development squad using n8n with visual workflows.
       - Acceptance Criteria: [ ] Creates visual workflow [ ] Integrates with external tools [ ] Supports agent-to-agent communication
       - Implementation: Define nodes for each agent type and configure connections for workflow.
       - Estimated effort: 3d

    5. Semantic Kernel Implementation
       - Description: Implement a development squad using Semantic Kernel with plugin architecture.
       - Acceptance Criteria: [ ] Uses plugin-based approach [ ] Supports both C# and Python [ ] Integrates with Microsoft ecosystem
       - Implementation: Create plugins for different development roles and orchestrate with kernel.
       - Estimated effort: 4d

### 6.2 Ollama Integration
- **Objective**: Ensure all implementations work with Ollama for local execution.
- **Subtasks**:
    1. Model Configuration
       - Description: Configure each framework to use Ollama models effectively.
       - Acceptance Criteria: [ ] Supports recommended models [ ] Includes performance tuning [ ] Handles model switching
       - Implementation: Create configuration files for each framework with Ollama settings.
       - Estimated effort: 1d

    2. Performance Optimization
       - Description: Optimize prompts and workflows for local execution.
       - Acceptance Criteria: [ ] Reduces token usage [ ] Improves response time [ ] Maintains quality
       - Implementation: Refine prompts and agent interactions for efficiency.
       - Estimated effort: 2d

### 6.3 GitHub Integration
- **Objective**: Enable AI agents to interact with GitHub repositories.
- **Subtasks**:
    1. Authentication and Access
       - Description: Implement secure GitHub authentication for all frameworks.
       - Acceptance Criteria: [ ] Uses token-based auth [ ] Secures credentials [ ] Handles permission errors
       - Implementation: Create authentication modules for each framework.
       - Estimated effort: 1d

    2. Repository Operations
       - Description: Implement common GitHub operations for development workflows.
       - Acceptance Criteria: [ ] Supports code analysis [ ] Creates pull requests [ ] Handles issues and comments
       - Implementation: Create GitHub utility functions for each framework.
       - Estimated effort: 2d

### 6.4 Comparison Metrics
- **Objective**: Develop standardized metrics for framework comparison.
- **Subtasks**:
    1. Benchmark Suite
       - Description: Create a suite of standard tasks for benchmarking.
       - Acceptance Criteria: [ ] Covers simple to complex tasks [ ] Measures performance consistently [ ] Supports all frameworks
       - Implementation: Define test cases and measurement methodology.
       - Estimated effort: 2d

    2. Results Dashboard
       - Description: Create a dashboard for visualizing comparison results.
       - Acceptance Criteria: [ ] Presents data clearly [ ] Supports filtering and sorting [ ] Includes all key metrics
       - Implementation: Generate markdown reports with tables and charts.
       - Estimated effort: 1d

## 7. Interfaces & Dependencies
- **API Endpoints**:
  - GitHub API v3 for repository operations
  - Ollama API for model management and inference

- **External Dependencies**:
  - LangGraph and LangChain for graph-based workflows
  - CrewAI for role-based agent orchestration
  - AutoGen for conversational multi-agent systems
  - n8n for visual workflow automation
  - Semantic Kernel for enterprise agent development
  - Docker for containerized execution

## 8. Coding and Architectural Standards
- **Python Code**:
  - Follow PEP 8 style guidelines
  - Use type hints for all function signatures
  - Document with docstrings in Google format
  - Use pytest for unit and integration tests

- **C# Code** (for Semantic Kernel):
  - Follow Microsoft C# coding conventions
  - Use async/await for asynchronous operations
  - Document with XML comments

- **JavaScript/TypeScript** (for n8n):
  - Follow standard JS/TS style guidelines
  - Use async/await for asynchronous operations
  - Document with JSDoc comments

- **Architecture**:
  - Use repository pattern for data access
  - Implement dependency injection where appropriate
  - Separate configuration from implementation
  - Create clear interfaces between components

## 9. Rules & Personas
- Rules reference: See [./rules/] 
- Agent personas: See [./personas/]

## 10. Analytics
| Metric | Target | Trigger |
|--------|--------|---------|
| Framework setup time | <30min | After installation |
| Task completion rate | >90% | On benchmark completion |
| Token usage | <2000 tokens/task | During execution |
| Response time | <5s for simple tasks | During execution |

## 11. Risks & Open Questions
- How will we handle breaking changes in framework APIs?
  - Mitigation: Pin dependency versions and document upgrade paths
- Will Ollama performance be sufficient for complex tasks?
  - Mitigation: Implement fallback to cloud APIs with clear documentation
- How do we ensure fair comparison across different programming languages?
  - Mitigation: Focus on capabilities and outcomes rather than implementation details

## 12. Appendix
- [Sample agent prompts](/docs/requirements/sample_agent_prompts.md)
- [Benchmark methodology](/docs/requirements/benchmark_methodology.md)
- [Framework selection guide](/docs/requirements/framework_selection_guide.md)