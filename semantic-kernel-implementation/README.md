# Semantic Kernel AI Development Squad Implementation

This directory contains the implementation of an AI development squad using Semantic Kernel, Microsoft's framework for building AI applications with a plugin-based architecture that seamlessly integrates with both C# and Python ecosystems.

## Overview

Semantic Kernel enables the creation of sophisticated AI applications through a plugin-based architecture that promotes modularity, reusability, and extensibility. This implementation demonstrates how to create a development squad with specialized AI agents (architect, developer, tester) that work together through Semantic Kernel plugins to complete complex software development tasks.

The Semantic Kernel approach excels at creating composable AI solutions where different capabilities can be mixed and matched, allowing for flexible and powerful development workflows that can adapt to various project requirements.

## Features

### Core Capabilities
- **Plugin-Based Architecture**: Modular design with specialized agent plugins
- **Multi-Language Support**: Native support for both C# and Python implementations
- **Microsoft Ecosystem Integration**: Seamless integration with Azure, Office, and other Microsoft services
- **Composable AI Functions**: Mix and match different AI capabilities as needed
- **Memory and Context Management**: Persistent context across plugin executions
- **Function Calling**: Direct integration with external APIs and services

### Advanced Features
- **Semantic Functions**: Natural language-based function definitions
- **Native Functions**: Traditional code-based functions for complex operations
- **Planner Integration**: Automatic planning and orchestration of plugin sequences
- **Template Engine**: Powerful templating system for dynamic content generation
- **Connector Ecosystem**: Built-in connectors for various AI services and data sources
- **Enterprise Security**: Built-in security features for enterprise deployments

## Setup

### Prerequisites
- Python 3.8+ (for Python implementation)
- .NET 7.0+ SDK (for C# implementation)
- Ollama (for local LLM execution)
- Git (for version control operations)
- GitHub account and token (for VCS integration)

### Installation

#### Python Implementation

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   cd semantic-kernel-implementation
   pip install -r requirements.txt
   ```

3. **Download recommended Ollama models:**
   ```bash
   # Primary models for development tasks
   ollama pull llama3.1:8b
   ollama pull codellama:13b
   
   # Alternative models for different use cases
   ollama pull llama3.1:70b  # For complex reasoning (if you have sufficient resources)
   ollama pull deepseek-coder:6.7b  # Specialized for coding tasks
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration:
   # GITHUB_TOKEN=your_github_token_here
   # OLLAMA_BASE_URL=http://localhost:11434
   # SEMANTIC_KERNEL_LOG_LEVEL=INFO
   ```

5. **Validate Python installation:**
   ```bash
   python validate_semantic_kernel.py
   ```

#### C# Implementation

1. **Install .NET 7.0 SDK or later:**
   ```bash
   # On macOS with Homebrew
   brew install dotnet
   
   # On Ubuntu/Debian
   sudo apt-get update && sudo apt-get install -y dotnet-sdk-7.0
   
   # On Windows, download from https://dotnet.microsoft.com/download
   ```

2. **Build the project:**
   ```bash
   dotnet build SemanticKernelAIDevSquad.csproj
   ```

3. **Configure Ollama:**
   ```bash
   # Ensure Ollama is running locally
   ollama serve
   
   # Download recommended models
   ollama pull llama3.1:8b
   ollama pull codellama:13b
   ```

4. **Set up configuration:**
   ```bash
   cp appsettings.example.json appsettings.json
   # Edit appsettings.json with your configuration:
   # - GitHub token and repository settings
   # - Ollama endpoint configuration
   # - Logging and telemetry settings
   ```

5. **Run integration test:**
   ```bash
   dotnet run --project SemanticKernelAIDevSquad.csproj
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

The Semantic Kernel implementation provides a plugin-based AI development environment. Here's how to use it:

### Basic Usage

```python
from adapter import create_semantic_kernel_adapter

# Create adapter with configuration
config = {
    'language': 'python',
    'semantic_kernel': {
        'model': 'llama3.1:8b',
        'code_model': 'codellama:13b'
    },
    'vcs': {
        'github': {'enabled': True}
    }
}

adapter = create_semantic_kernel_adapter(config)

# Get capabilities
capabilities = await adapter.get_capabilities()
print(f"Features: {capabilities['features']}")

# Run a task
from common.agent_api import TaskSchema, TaskType

task = TaskSchema(
    id='fibonacci-task',
    type=TaskType.FEATURE_ADD,
    inputs={
        'description': 'Create a Fibonacci calculator with optimization',
        'requirements': [
            'Handle negative numbers gracefully',
            'Optimize for performance with memoization',
            'Include comprehensive error handling',
            'Add unit tests with edge cases'
        ]
    },
    repo_path='.',
    vcs_provider='github'
)

async for result in adapter.run_task(task):
    if hasattr(result, 'status'):
        print(f"Task completed: {result.status}")
        print(f"Plugin execution log: {result.artifacts['plugin_log']}")
```

### Advanced Plugin Workflow

#### Python Implementation

```python
import semantic_kernel as sk
from workflows.development_workflow import create_development_kernel

# Initialize the kernel with specialized plugins
kernel = create_development_kernel()

# Configure plugins with specific capabilities
architect_plugin = kernel.plugins["ArchitectPlugin"]
developer_plugin = kernel.plugins["DeveloperPlugin"]
tester_plugin = kernel.plugins["TesterPlugin"]

# Execute a complex development workflow
async def run_development_workflow(task_description: str):
    # Phase 1: Architecture Design
    design_result = await kernel.invoke(
        architect_plugin["design_system"],
        task_description=task_description
    )
    
    # Phase 2: Code Implementation
    implementation_result = await kernel.invoke(
        developer_plugin["implement_code"],
        design=design_result.value,
        requirements=task_description
    )
    
    # Phase 3: Test Creation
    test_result = await kernel.invoke(
        tester_plugin["create_tests"],
        implementation=implementation_result.value,
        requirements=task_description
    )
    
    return {
        "design": design_result.value,
        "implementation": implementation_result.value,
        "tests": test_result.value
    }

# Run the workflow
result = await run_development_workflow(
    "Build a web API for user authentication with JWT tokens, "
    "password hashing with bcrypt, and rate limiting for login attempts"
)
```

#### C# Implementation

```csharp
using Microsoft.SemanticKernel;
using Workflows;

// Initialize the kernel with specialized plugins
var kernel = DevelopmentWorkflow.CreateDevelopmentKernel();

// Configure plugins with specific capabilities
var architectPlugin = kernel.Plugins["ArchitectPlugin"];
var developerPlugin = kernel.Plugins["DeveloperPlugin"];
var testerPlugin = kernel.Plugins["TesterPlugin"];

// Execute a complex development workflow
public async Task<DevelopmentResult> RunDevelopmentWorkflowAsync(string taskDescription)
{
    // Phase 1: Architecture Design
    var designResult = await kernel.InvokeAsync(
        architectPlugin["DesignSystem"],
        new() { ["task_description"] = taskDescription }
    );
    
    // Phase 2: Code Implementation
    var implementationResult = await kernel.InvokeAsync(
        developerPlugin["ImplementCode"],
        new() { 
            ["design"] = designResult.GetValue<string>(),
            ["requirements"] = taskDescription
        }
    );
    
    // Phase 3: Test Creation
    var testResult = await kernel.InvokeAsync(
        testerPlugin["CreateTests"],
        new() { 
            ["implementation"] = implementationResult.GetValue<string>(),
            ["requirements"] = taskDescription
        }
    );
    
    return new DevelopmentResult
    {
        Design = designResult.GetValue<string>(),
        Implementation = implementationResult.GetValue<string>(),
        Tests = testResult.GetValue<string>()
    };
}
```

### Plugin Specialization

Each plugin has specific capabilities and semantic functions:

#### Architect Plugin
```python
# The architect plugin focuses on system design and planning
architect_result = await kernel.invoke(
    "ArchitectPlugin", 
    "DesignMicroservicesArchitecture",
    requirements="Design a scalable e-commerce platform"
)
```

#### Developer Plugin
```python
# The developer plugin implements code based on specifications
developer_result = await kernel.invoke(
    "DeveloperPlugin",
    "ImplementService", 
    specification=architect_result.value
)
```

#### Tester Plugin
```python
# The tester plugin creates comprehensive test suites
tester_result = await kernel.invoke(
    "TesterPlugin",
    "GenerateTestSuite",
    implementation=developer_result.value
)
```

### Configuration Options

Configure Semantic Kernel-specific settings:

```python
config = {
    'semantic_kernel': {
        'model': 'llama3.1:8b',           # Primary model for semantic functions
        'code_model': 'codellama:13b',     # Specialized model for coding
        'temperature': 0.7,                # Creativity vs consistency
        'max_tokens': 2048,                # Maximum response length
        'execution_settings': {
            'max_auto_invoke_attempts': 3,
            'function_choice_behavior': 'auto'
        }
    },
    'plugins': {
        'architect': {
            'enabled': True,
            'semantic_functions_path': './plugins/architect',
            'native_functions': ['design_system', 'analyze_requirements']
        },
        'developer': {
            'enabled': True,
            'semantic_functions_path': './plugins/developer',
            'native_functions': ['implement_code', 'optimize_performance']
        },
        'tester': {
            'enabled': True,
            'semantic_functions_path': './plugins/tester',
            'native_functions': ['create_tests', 'validate_coverage']
        }
    }
}
```

## Architecture

The Semantic Kernel implementation follows a plugin-based architecture:

### Core Components

1. **SemanticKernelAdapter**: Main adapter implementing the AgentAdapter protocol
2. **Specialized Plugins**: Architect, Developer, and Tester plugins with semantic functions
3. **Development Workflow**: Orchestrates plugin execution and manages state
4. **Function Registry**: Manages both semantic and native functions
5. **Memory System**: Persistent context and conversation history
6. **Safety Integration**: Comprehensive security controls

### Plugin Architecture

1. **Semantic Functions**: Natural language-based function definitions stored as text
2. **Native Functions**: Traditional code-based functions for complex operations
3. **Plugin Composition**: Mix and match plugins based on task requirements
4. **Function Chaining**: Automatic orchestration of plugin sequences
5. **Context Management**: Shared context across plugin executions
6. **Result Aggregation**: Combine outputs from multiple plugins

### Plugin Specialization

- **Architect Plugin**: System design, architecture decisions, technology selection
- **Developer Plugin**: Code implementation, algorithm design, optimization
- **Tester Plugin**: Test creation, quality assurance, coverage analysis

## Development

To work on the Semantic Kernel implementation:

### Setup Development Environment

1. **Install dependencies:**
```bash
# Python
pip install -r requirements.txt

# C#
dotnet restore
```

2. **Set up Ollama:**
```bash
# Install Ollama (see https://ollama.ai)
ollama serve
ollama pull llama3.1:8b
```

3. **Run validation:**
```bash
python validate_semantic_kernel.py
```

### Testing

Run the comprehensive test suite:

```bash
# Structure tests
python tests/test_structure_only.py

# Integration tests
python simple_integration_test.py

# C# tests
dotnet test

# Full test suite
pytest tests/ -v
```

### Code Structure

Follow these guidelines when contributing:

- **Plugins**: Implement specialized plugin behaviors and semantic functions
- **Workflows**: Define orchestration patterns and execution flows
- **Safety**: Integrate security controls throughout the plugin execution
- **Testing**: Maintain comprehensive test coverage for all components

### Plugin Development

Create new plugins following the established patterns:

```python
from semantic_kernel.plugin_definition import sk_function

class CustomPlugin:
    @sk_function(
        description="Custom function description",
        name="custom_function"
    )
    def custom_function(self, input: str) -> str:
        """Implementation of custom functionality."""
        return f"Processed: {input}"
```

## Troubleshooting

### Common Issues

1. **Semantic Kernel Import**: Ensure semantic-kernel is installed: `pip install semantic-kernel`
2. **Model Loading**: Download required models: `ollama pull llama3.1:8b`
3. **Plugin Loading**: Check plugin paths and semantic function definitions
4. **Memory Issues**: Adjust max_tokens and context window settings

### Debug Mode

Enable debug logging for detailed plugin execution analysis:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring

Monitor plugin performance with built-in metrics:

```python
metrics = await adapter.get_metrics()
print(f"Plugins executed: {metrics['plugins']['total_executions']}")
print(f"Average execution time: {metrics['plugins']['avg_execution_time']}")
print(f"Function calls: {metrics['functions']['total_calls']}")
```

## Performance Metrics

This implementation is benchmarked against other frameworks using the standard test suite. Key performance indicators include:

- **Plugin Execution Speed**: Measured by function call latency
- **Memory Efficiency**: Context management and plugin loading optimization
- **Semantic Function Quality**: Evaluated through automated code analysis
- **Composition Effectiveness**: Plugin interaction and orchestration efficiency

## Advanced Features

### Custom Semantic Functions

Create domain-specific semantic functions:

```python
# Create a semantic function from text
semantic_function = kernel.create_semantic_function(
    prompt_template="""
    You are an expert {{$domain}} developer.
    Task: {{$task}}
    Requirements: {{$requirements}}
    
    Provide a detailed implementation plan:
    """,
    function_name="create_implementation_plan",
    skill_name="ArchitectPlugin"
)
```

### Plugin Composition

Combine multiple plugins for complex workflows:

```python
# Create a composed workflow
async def complex_development_workflow(kernel, task):
    # Step 1: Analyze requirements
    analysis = await kernel.invoke("ArchitectPlugin", "analyze_requirements", task=task)
    
    # Step 2: Design system
    design = await kernel.invoke("ArchitectPlugin", "design_system", analysis=analysis.value)
    
    # Step 3: Implement code
    code = await kernel.invoke("DeveloperPlugin", "implement_code", design=design.value)
    
    # Step 4: Create tests
    tests = await kernel.invoke("TesterPlugin", "create_tests", code=code.value)
    
    return {
        "analysis": analysis.value,
        "design": design.value,
        "implementation": code.value,
        "tests": tests.value
    }
```

### Integration with External Services

Connect plugins to external APIs and services:

```python
@sk_function(description="Integrate with external API")
def call_external_api(self, endpoint: str, data: str) -> str:
    """Call external API with safety controls."""
    # Implementation with network access controls
    pass
```

## References

- [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
- [Semantic Kernel GitHub Repository](https://github.com/microsoft/semantic-kernel)
- [Plugin Development Guide](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins/)
- [Semantic Functions Reference](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/semantic-functions/)