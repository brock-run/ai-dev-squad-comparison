# Code Lenses for AI Dev Squad Comparison Project

This document defines the code lenses (inline action prompts) that can be used within IDEs like Cursor and Windsurf to enhance the development experience with AI assistance. These code lenses provide contextual actions that can be triggered directly from the code editor.

## General Code Lenses

These code lenses are applicable across all frameworks and implementations:

### Documentation Lenses

1. **Generate Docstring**
   - **Trigger**: Appears above function/method definitions without docstrings
   - **Action**: Generates appropriate docstring in the framework's standard format
   - **Example**: For Python, generates Google-style docstring with parameters, return values, and examples
   - **PRD Reference**: Section 8 - Coding and Architectural Standards

2. **Explain Code**
   - **Trigger**: Appears on complex code blocks
   - **Action**: Provides a natural language explanation of what the code does
   - **Example**: Explains a complex algorithm or data transformation
   - **PRD Reference**: Section 6.1 - Framework Implementations

3. **Document Edge Cases**
   - **Trigger**: Appears on conditional blocks or error handling code
   - **Action**: Identifies and documents edge cases being handled
   - **Example**: Lists all the edge cases handled in a try/except block
   - **PRD Reference**: Section 4 - User Stories (Edge Cases)

### Testing Lenses

1. **Generate Unit Tests**
   - **Trigger**: Appears above function/method definitions
   - **Action**: Generates comprehensive unit tests for the function
   - **Example**: Creates pytest tests with multiple test cases including edge cases
   - **PRD Reference**: Section 6.1 - Framework Implementations (Unit Testing)

2. **Add Test Case**
   - **Trigger**: Appears within test functions
   - **Action**: Suggests additional test cases for better coverage
   - **Example**: Adds edge case tests or boundary condition tests
   - **PRD Reference**: Section 4 - Performance Metrics Acceptance

3. **Generate Mock Data**
   - **Trigger**: Appears in test functions with external dependencies
   - **Action**: Creates mock data for testing
   - **Example**: Generates sample API responses or database records
   - **PRD Reference**: Section 6.3 - GitHub Integration

### Code Quality Lenses

1. **Refactor Code**
   - **Trigger**: Appears on complex or repetitive code blocks
   - **Action**: Suggests refactoring to improve readability or performance
   - **Example**: Extracts repeated code into a helper function
   - **PRD Reference**: Section 8 - Coding and Architectural Standards

2. **Optimize Performance**
   - **Trigger**: Appears on potentially inefficient code
   - **Action**: Suggests performance optimizations
   - **Example**: Replaces multiple list operations with a more efficient approach
   - **PRD Reference**: Section 6.2 - Performance Optimization

3. **Fix Code Style**
   - **Trigger**: Appears on code that violates style guidelines
   - **Action**: Fixes style issues automatically
   - **Example**: Corrects indentation or line length issues
   - **PRD Reference**: Section 8 - Coding and Architectural Standards

## Framework-Specific Code Lenses

These code lenses are tailored to specific AI agent orchestration frameworks:

### LangGraph Lenses

1. **Add State Transition**
   - **Trigger**: Appears in StateGraph definition
   - **Action**: Adds a new state transition with appropriate condition
   - **Example**: Adds a transition between two agent states with a condition function
   - **PRD Reference**: Section 6.1.1 - LangGraph Implementation

2. **Add Agent Node**
   - **Trigger**: Appears in StateGraph definition
   - **Action**: Adds a new agent node to the graph
   - **Example**: Creates a new specialized agent and adds it to the workflow
   - **PRD Reference**: Section 6.1.1 - LangGraph Implementation

3. **Implement Tool**
   - **Trigger**: Appears in tool references
   - **Action**: Implements a tool function for an agent
   - **Example**: Creates a GitHub integration tool for the developer agent
   - **PRD Reference**: Section 6.3 - GitHub Integration

### CrewAI Lenses

1. **Define Agent**
   - **Trigger**: Appears in crew definition
   - **Action**: Creates a new agent with role, goal, and backstory
   - **Example**: Defines a code reviewer agent with appropriate expertise
   - **PRD Reference**: Section 6.1.2 - CrewAI Implementation

2. **Create Task**
   - **Trigger**: Appears in crew definition
   - **Action**: Defines a new task with description and expected output
   - **Example**: Creates a code review task assigned to the reviewer agent
   - **PRD Reference**: Section 6.1.2 - CrewAI Implementation

3. **Add Context Sharing**
   - **Trigger**: Appears in task definition
   - **Action**: Adds context sharing between tasks
   - **Example**: Links the output of a development task to a testing task
   - **PRD Reference**: Section 6.1.2 - CrewAI Implementation

### AutoGen Lenses

1. **Define Agent**
   - **Trigger**: Appears in group chat definition
   - **Action**: Creates a new agent with system message
   - **Example**: Defines a project manager agent with appropriate instructions
   - **PRD Reference**: Section 6.1.3 - AutoGen Implementation

2. **Configure Group Chat**
   - **Trigger**: Appears in group chat manager
   - **Action**: Configures group chat parameters
   - **Example**: Sets up max rounds, memory, and termination conditions
   - **PRD Reference**: Section 6.1.3 - AutoGen Implementation

3. **Add Human Feedback**
   - **Trigger**: Appears in conversation flow
   - **Action**: Adds human feedback integration point
   - **Example**: Creates a prompt for human input at a critical decision point
   - **PRD Reference**: Section 6.1.3 - AutoGen Implementation

### n8n Lenses

1. **Add Workflow Node**
   - **Trigger**: Appears in workflow definition
   - **Action**: Adds a new node to the workflow
   - **Example**: Creates an AI agent node for code review
   - **PRD Reference**: Section 6.1.4 - n8n Implementation

2. **Configure Node Parameters**
   - **Trigger**: Appears in node definition
   - **Action**: Sets up node parameters and connections
   - **Example**: Configures an AI agent's system message and tools
   - **PRD Reference**: Section 6.1.4 - n8n Implementation

3. **Add Error Handling**
   - **Trigger**: Appears in workflow nodes
   - **Action**: Adds error handling paths
   - **Example**: Creates error handling for API rate limits
   - **PRD Reference**: Section 6.3 - GitHub Integration

### Semantic Kernel Lenses

1. **Create Plugin**
   - **Trigger**: Appears in kernel definition
   - **Action**: Creates a new plugin for the kernel
   - **Example**: Defines a code generation plugin with semantic functions
   - **PRD Reference**: Section 6.1.5 - Semantic Kernel Implementation

2. **Define Semantic Function**
   - **Trigger**: Appears in plugin definition
   - **Action**: Creates a new semantic function with prompt
   - **Example**: Defines a function for code review with appropriate prompt
   - **PRD Reference**: Section 6.1.5 - Semantic Kernel Implementation

3. **Add Memory Integration**
   - **Trigger**: Appears in kernel configuration
   - **Action**: Adds memory integration for context persistence
   - **Example**: Configures semantic memory for the kernel
   - **PRD Reference**: Section 6.1.5 - Semantic Kernel Implementation

## Ollama Integration Lenses

These code lenses are specific to Ollama integration:

1. **Configure Ollama Model**
   - **Trigger**: Appears in model configuration
   - **Action**: Sets up Ollama model parameters
   - **Example**: Configures temperature, top_k, and other parameters
   - **PRD Reference**: Section 6.2.1 - Model Configuration

2. **Optimize Prompt**
   - **Trigger**: Appears in prompt definitions
   - **Action**: Optimizes prompts for token efficiency
   - **Example**: Rewrites a verbose prompt to be more concise
   - **PRD Reference**: Section 6.2.2 - Performance Optimization

3. **Add Model Fallback**
   - **Trigger**: Appears in model initialization
   - **Action**: Adds fallback options for different models
   - **Example**: Creates a fallback from larger to smaller model based on resource availability
   - **PRD Reference**: Section 6.2.1 - Model Configuration

## GitHub Integration Lenses

These code lenses are specific to GitHub integration:

1. **Configure GitHub Auth**
   - **Trigger**: Appears in GitHub configuration
   - **Action**: Sets up secure authentication
   - **Example**: Configures token-based authentication with environment variables
   - **PRD Reference**: Section 6.3.1 - Authentication and Access

2. **Add Repository Operation**
   - **Trigger**: Appears in GitHub utility functions
   - **Action**: Adds a new repository operation
   - **Example**: Implements a function to create a pull request
   - **PRD Reference**: Section 6.3.2 - Repository Operations

3. **Handle API Rate Limits**
   - **Trigger**: Appears in GitHub API calls
   - **Action**: Adds rate limit handling
   - **Example**: Implements exponential backoff for API requests
   - **PRD Reference**: Section 6.3.1 - Authentication and Access

## Benchmark and Metrics Lenses

These code lenses are related to performance measurement and comparison:

1. **Add Benchmark Test**
   - **Trigger**: Appears in benchmark suite
   - **Action**: Adds a new benchmark test case
   - **Example**: Creates a standardized test for comparing framework performance
   - **PRD Reference**: Section 6.4.1 - Benchmark Suite

2. **Measure Performance**
   - **Trigger**: Appears in framework implementation
   - **Action**: Adds performance measurement code
   - **Example**: Adds timing and token counting for a workflow
   - **PRD Reference**: Section 6.4.1 - Benchmark Suite

3. **Generate Comparison Report**
   - **Trigger**: Appears in results processing code
   - **Action**: Creates a formatted comparison report
   - **Example**: Generates a markdown table comparing metrics across frameworks
   - **PRD Reference**: Section 6.4.2 - Results Dashboard

## Usage Instructions

To use these code lenses in Cursor or Windsurf:

1. Position your cursor on the relevant code section
2. Look for the code lens indicator (usually a light bulb or similar icon)
3. Click on the indicator to see available actions
4. Select the desired action to execute it

Code lenses can significantly accelerate development by providing contextual AI assistance directly within your code editor, reducing the need to switch contexts or manually invoke AI tools.