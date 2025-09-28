# Technology Stack & Build System

## Core Technologies

### Languages & Frameworks
- **Python 3.8+**: Primary language for all framework implementations
- **TypeScript/Next.js**: Web UI and dashboard components
- **Node.js 14+**: N8N implementation and JavaScript tooling
- **C#/.NET 7.0+**: Semantic Kernel implementation

### AI Orchestration Frameworks
- **LangGraph**: Graph-based workflows with state management
- **Haystack**: RAG-enhanced development with document retrieval
- **CrewAI**: Role-based agent coordination
- **AutoGen**: Multi-agent conversational systems
- **Langroid**: Conversation-style multi-agent framework
- **LlamaIndex**: Retrieval-augmented multi-agent workflows
- **Semantic Kernel**: Plugin-based AI applications
- **N8N**: Visual workflow automation
- **Claude Subagents**: Specialized role-based prompts

### Infrastructure & Tools
- **Docker**: Containerization and sandboxed execution
- **Kubernetes**: Production deployment orchestration
- **Ollama**: Local LLM execution and model management
- **Redis**: Caching and session management
- **PostgreSQL**: Structured data storage
- **Vector Stores**: Semantic search and RAG capabilities

## Build System

### Package Management
- **Python**: `pip` with `requirements.txt` files per implementation
- **Node.js**: `npm` with `package.json` and `package-lock.json`
- **C#**: `dotnet` with `.csproj` files

### Common Commands

#### Setup & Installation
```bash
# Install all dependencies
make install

# Install specific framework
make install-framework F=langgraph

# Create virtual environment
make venv

# Setup Ollama models
make setup-ollama
```

#### Testing
```bash
# Run all tests
make test

# Test specific framework
make test-framework F=crewai

# Run structure validation
python validate_structure.py
```

#### Development
```bash
# Run benchmarks
make benchmark

# Start dashboard
make dashboard

# Run example workflow
make run-example F=haystack
```

#### Cleanup
```bash
# Clean temporary files
make clean

# Clean all artifacts
make clean-all
```

## Architecture Patterns

### Common Framework Layer
- **AgentAdapter Protocol**: Standardized interface for all implementations
- **Safety Framework**: Multi-layer security controls (sandboxing, network, filesystem)
- **VCS Integration**: GitHub/GitLab providers with AI commit messages
- **Configuration Management**: Centralized config with validation

### Implementation Structure
```
{framework}-implementation/
├── adapter.py              # AgentAdapter implementation
├── agents/                 # Framework-specific agents
├── workflows/              # Orchestration workflows
├── tests/                  # Comprehensive test suite
├── requirements.txt        # Dependencies
└── README.md              # Framework documentation
```

### Safety-First Design
- All implementations must integrate safety controls
- Sandboxed execution for code operations
- Network access controls with allowlists
- Filesystem restrictions and audit logging
- Prompt injection detection and prevention

## Development Guidelines

### Code Quality
- **Type Hints**: Full type annotations required
- **Async-First**: Use async/await for all I/O operations
- **Error Handling**: Comprehensive exception handling with fallbacks
- **Logging**: Structured logging with correlation IDs
- **Testing**: Minimum 80% test coverage for production implementations

### Security Requirements
- All user inputs must be validated and sanitized
- Code execution must use sandboxed environments
- Network requests must go through access controls
- File operations must use filesystem guards
- Sensitive data must be handled securely

### Performance Considerations
- Use connection pooling for external services
- Implement caching for expensive operations
- Design for horizontal scaling
- Monitor resource usage and set limits
- Optimize for sub-5 second response times