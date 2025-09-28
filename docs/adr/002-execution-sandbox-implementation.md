# ADR-002: Execution Sandbox Implementation

## Status
Accepted

## Date
2024-01-15

## Context

AI agents need to execute code dynamically, which presents significant security risks. We need a sandboxing solution that:

1. Isolates code execution from the host system
2. Provides resource limits (CPU, memory, time)
3. Controls network and filesystem access
4. Supports multiple programming languages
5. Is portable across different operating systems
6. Provides detailed execution monitoring

## Decision

We will implement a **dual-mode execution sandbox** with Docker as the primary isolation mechanism and subprocess as a fallback:

### Primary Mode: Docker Sandbox
- **Container Isolation**: Each execution runs in a separate Docker container
- **Resource Limits**: CPU, memory, and time constraints enforced by Docker
- **Network Isolation**: Containers run without network access by default
- **Filesystem Isolation**: Limited filesystem access through volume mounts
- **Language Support**: Pre-built images for Python, Node.js, and other languages

### Fallback Mode: Subprocess Sandbox
- **Process Isolation**: Code runs in separate processes with restricted permissions
- **Resource Monitoring**: Python-based resource monitoring and limits
- **Signal Handling**: Timeout enforcement through process signals
- **Environment Control**: Restricted environment variables and PATH

### Implementation Details

```python
class SandboxType(Enum):
    DOCKER = "docker"
    SUBPROCESS = "subprocess"

class ExecutionSandbox:
    def __init__(self, sandbox_type: SandboxType, config: ExecutionConfig)
    def execute(self, code: str, language: str) -> ExecutionResult
    def cleanup(self)
```

## Alternatives Considered

### 1. Virtual Machines (VMs)
**Rejected**: Too heavy-weight for short-lived code execution. VM startup time would significantly impact performance.

### 2. WebAssembly (WASM) Sandbox
**Rejected**: Limited language support and ecosystem. Not suitable for general-purpose code execution with file I/O requirements.

### 3. chroot/jail Only
**Rejected**: Not portable across operating systems. Provides limited isolation compared to containers.

### 4. Cloud-Based Execution (AWS Lambda, etc.)
**Rejected**: Introduces network dependencies, latency, and cost. Requires internet connectivity.

### 5. Language-Specific Sandboxes (PyPy sandbox, etc.)
**Rejected**: Would require different implementations for each language. Limited availability and maintenance.

## Consequences

### Positive
- **Strong Isolation**: Docker provides excellent process and filesystem isolation
- **Resource Control**: Precise limits on CPU, memory, and execution time
- **Portability**: Works consistently across different host operating systems
- **Flexibility**: Fallback mode ensures functionality when Docker is unavailable
- **Monitoring**: Detailed execution metrics and resource usage tracking

### Negative
- **Docker Dependency**: Primary mode requires Docker installation
- **Performance Overhead**: Container creation adds latency to execution
- **Complexity**: Managing two different execution modes increases complexity
- **Resource Usage**: Docker containers consume additional system resources

## Security Considerations

### Docker Security
- Containers run as non-root users
- No privileged access or capabilities
- Read-only filesystem with limited writable areas
- Network access disabled by default
- Resource limits prevent DoS attacks

### Subprocess Security
- Process runs with restricted user permissions
- Environment variables sanitized
- Working directory isolated
- Signal-based timeout enforcement
- Resource monitoring prevents resource exhaustion

## Implementation Notes

### Docker Configuration
```yaml
execution:
  sandbox_type: docker
  docker:
    image: "python:3.11-slim"
    memory_limit: "512m"
    cpu_limit: "0.5"
    network_mode: "none"
    read_only: true
    tmpfs:
      - "/tmp:size=100m"
```

### Subprocess Configuration
```yaml
execution:
  sandbox_type: subprocess
  subprocess:
    timeout: 30
    memory_limit_mb: 256
    cpu_percent_limit: 50
    restricted_imports:
      - os
      - subprocess
      - sys
```

## Monitoring and Logging

- Execution start/end timestamps
- Resource usage metrics (CPU, memory, I/O)
- Exit codes and error messages
- Security violations and policy breaches
- Performance metrics for optimization

## Testing Strategy

- Unit tests for both Docker and subprocess modes
- Integration tests with various programming languages
- Security tests for escape attempts
- Performance benchmarks
- Resource limit validation tests

## Related ADRs

- ADR-001: Security Architecture Approach
- ADR-003: Network Access Control Strategy
- ADR-005: Security Policy Management System