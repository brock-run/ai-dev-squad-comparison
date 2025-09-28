# Safety and Security System

The AI Dev Squad Comparison platform includes a comprehensive safety and security system designed to provide secure code execution, resource management, and protection against malicious or erroneous code.

## Overview

The safety system provides multiple layers of protection:

1. **Execution Sandbox** - Isolated code execution environment
2. **Resource Limits** - CPU, memory, and time constraints
3. **Network Controls** - Default-deny network access with allowlists
4. **Filesystem Controls** - Restricted file system access
5. **Prompt Injection Detection** - Input validation and filtering
6. **Output Filtering** - LLM-based content analysis

## Execution Sandbox

### Architecture

The execution sandbox supports two modes:

- **Docker Sandbox** (Recommended) - Full containerization with strong isolation
- **Subprocess Sandbox** (Fallback) - Process-based isolation when Docker unavailable

### Basic Usage

```python
from common.safety import ExecutionSandbox, SandboxType

# Create sandbox
sandbox = ExecutionSandbox(SandboxType.DOCKER)

# Execute code
result = sandbox.execute_code(
    code="print('Hello World')",
    language="python",
    timeout_seconds=30,
    max_memory_mb=512
)

print(f"Status: {result.status}")
print(f"Output: {result.stdout}")
```

### Configuration Integration

```python
from common.safety.config_integration import get_safety_manager

# Use configuration-based execution
safety_manager = get_safety_manager()
result = safety_manager.execute_code_with_config(
    code="print('Hello World')",
    language="python"
)
```

## Supported Languages

The sandbox supports multiple programming languages:

- **Python** - Full support with package installation
- **JavaScript/Node.js** - NPM package support
- **Bash/Shell** - Shell script execution
- **Custom** - Extensible for additional languages

### Language-Specific Features

#### Python
```python
result = sandbox.execute_code(
    code="""
import json
import requests  # If in requirements

data = {"message": "Hello"}
print(json.dumps(data))
""",
    language="python",
    requirements=["requests"]  # Auto-installed
)
```

#### JavaScript
```python
result = sandbox.execute_code(
    code="""
const fs = require('fs');
console.log('Hello from Node.js');
""",
    language="javascript",
    requirements=["lodash"]  # NPM packages
)
```

#### Bash
```python
result = sandbox.execute_code(
    code="""
echo "System info:"
uname -a
echo "Current directory:"
pwd
ls -la
""",
    language="bash"
)
```

## Resource Management

### Memory Limits

```python
# Limit memory usage to 256MB
result = sandbox.execute_code(
    code="data = [0] * (1024 * 1024 * 100)",  # Try to allocate 100MB
    max_memory_mb=256
)

if result.status == "resource_limit":
    print(f"Memory limit exceeded: {result.error_message}")
```

### CPU Limits

```python
# Limit CPU usage to 50%
result = sandbox.execute_code(
    code="""
import time
for i in range(1000000):
    _ = i * i  # CPU-intensive task
""",
    max_cpu_percent=50
)
```

### Timeout Handling

```python
# Set execution timeout
result = sandbox.execute_code(
    code="""
import time
time.sleep(60)  # Long-running task
""",
    timeout_seconds=10
)

if result.status == "timeout":
    print("Execution timed out")
```

## File Operations

### Working with Files

```python
# Provide files to the execution environment
files = {
    "config.json": '{"debug": true}',
    "data.txt": "Sample data",
    "subdir/helper.py": "def helper(): return 'help'"
}

result = sandbox.execute_code(
    code="""
import json

# Read configuration
with open('config.json', 'r') as f:
    config = json.load(f)
    print(f"Debug mode: {config['debug']}")

# Read data
with open('data.txt', 'r') as f:
    data = f.read()
    print(f"Data: {data}")

# Import helper
import sys
sys.path.append('subdir')
import helper
print(helper.helper())
""",
    files=files
)
```

### File Creation and Modification

```python
result = sandbox.execute_code(
    code="""
# Create new file
with open('output.txt', 'w') as f:
    f.write('Generated output')

# Modify existing file
with open('data.txt', 'a') as f:
    f.write('\\nAppended data')

import os
print("Files created:", os.listdir('.'))
""",
    files={"data.txt": "Original data"}
)

# Check what files were created/modified
print("Files created:", result.files_created)
print("Files modified:", result.files_modified)
```

## Network Controls

### Default Network Policy

By default, network access is **denied** for security:

```python
result = sandbox.execute_code(
    code="""
import urllib.request
try:
    response = urllib.request.urlopen('https://httpbin.org/get')
    print("Network access successful")
except Exception as e:
    print(f"Network access denied: {e}")
""",
    network_enabled=False  # Default
)
```

### Enabling Network Access

```python
# Enable network with allowlist
result = sandbox.execute_code(
    code="""
import urllib.request
response = urllib.request.urlopen('https://api.github.com')
print(f"Response status: {response.status}")
""",
    network_enabled=True,
    allowed_hosts=["api.github.com"]
)
```

## Docker Sandbox

### Advantages

- **Strong Isolation** - Complete containerization
- **Resource Control** - Precise memory and CPU limits
- **Network Isolation** - Container-level network controls
- **Filesystem Isolation** - Read-only root filesystem
- **Security** - Non-root user execution

### Requirements

```bash
# Install Docker
sudo apt-get install docker.io

# Add user to docker group
sudo usermod -aG docker $USER

# Test Docker installation
docker run hello-world
```

### Custom Images

The sandbox automatically builds custom images when requirements are specified:

```python
result = sandbox.execute_code(
    code="""
import numpy as np
import pandas as pd

data = np.array([1, 2, 3, 4, 5])
df = pd.DataFrame({'values': data})
print(df.describe())
""",
    language="python",
    requirements=["numpy", "pandas"]
)
```

### Image Management

```python
# Get sandbox information
sandbox = ExecutionSandbox(SandboxType.DOCKER)
info = sandbox.get_sandbox_info()

print(f"Docker available: {info['docker_available']}")
print(f"Supported languages: {info['supported_languages']}")
```

## Subprocess Sandbox

### When to Use

- Docker not available
- Lightweight execution needs
- Development environments
- CI/CD systems without Docker

### Limitations

- **Less Isolation** - Process-level only
- **Resource Limits** - Best-effort enforcement
- **Network Control** - Limited capabilities
- **Security** - Relies on OS-level controls

### Usage

```python
# Force subprocess sandbox
sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)

result = sandbox.execute_code(
    code="print('Running in subprocess')",
    language="python"
)
```

## Resource Monitoring

### Real-time Monitoring

The sandbox provides real-time resource monitoring:

```python
result = sandbox.execute_code(
    code="""
import time
import os

for i in range(10):
    # Simulate work
    data = [0] * (1024 * 100)  # Allocate memory
    time.sleep(0.5)
    print(f"Step {i+1}/10")
""",
    max_memory_mb=512,
    max_cpu_percent=80
)

print(f"Peak memory usage: {result.memory_usage_mb:.1f} MB")
print(f"Peak CPU usage: {result.cpu_usage_percent:.1f}%")
print(f"Execution time: {result.execution_time:.2f}s")
```

### Resource Violations

```python
result = sandbox.execute_code(
    code="data = [0] * (1024 * 1024 * 1000)",  # Try to allocate 1GB
    max_memory_mb=256
)

if result.status == "resource_limit":
    print(f"Resource violation: {result.error_message}")
```

## Error Handling

### Execution Status

The sandbox returns detailed execution status:

```python
from common.safety import ExecutionStatus

result = sandbox.execute_code(code="invalid python syntax")

if result.status == ExecutionStatus.FAILURE:
    print(f"Syntax error: {result.stderr}")
elif result.status == ExecutionStatus.TIMEOUT:
    print("Execution timed out")
elif result.status == ExecutionStatus.RESOURCE_LIMIT:
    print(f"Resource limit exceeded: {result.error_message}")
elif result.status == ExecutionStatus.SUCCESS:
    print("Execution successful")
```

### Error Recovery

```python
def safe_execute(code, max_retries=3):
    """Execute code with retry logic."""
    for attempt in range(max_retries):
        result = sandbox.execute_code(
            code=code,
            timeout_seconds=30 * (attempt + 1)  # Increase timeout
        )
        
        if result.status == ExecutionStatus.SUCCESS:
            return result
        elif result.status == ExecutionStatus.TIMEOUT and attempt < max_retries - 1:
            print(f"Timeout on attempt {attempt + 1}, retrying...")
            continue
        else:
            return result
    
    return result
```

## Configuration

### System Configuration

Configure sandbox behavior in `config/system.yaml`:

```yaml
safety:
  enabled: true
  sandbox_type: "docker"  # or "subprocess"
  
  resource_limits:
    max_memory_mb: 1024
    max_cpu_percent: 80
    timeout_seconds: 300
  
  network_policy:
    default_deny: true
    allowlist:
      - "api.github.com"
      - "gitlab.com"
  
  filesystem_policy:
    restrict_to_repo: true
    temp_dir_access: true
    system_access: false
```

### Environment Variables

Override configuration with environment variables:

```bash
# Disable safety controls
export AI_DEV_SQUAD_SAFETY_ENABLED=false

# Change sandbox type
export AI_DEV_SQUAD_SAFETY_SANDBOX_TYPE=subprocess

# Adjust resource limits
export AI_DEV_SQUAD_SAFETY_RESOURCE_LIMITS_MAX_MEMORY_MB=2048
export AI_DEV_SQUAD_SAFETY_RESOURCE_LIMITS_TIMEOUT_SECONDS=600
```

### Runtime Configuration

```python
from common.safety.config_integration import get_safety_manager

safety_manager = get_safety_manager()

# Check current configuration
if safety_manager.is_safety_enabled():
    limits = safety_manager.get_resource_limits()
    print(f"Memory limit: {limits['max_memory_mb']} MB")
    print(f"CPU limit: {limits['max_cpu_percent']}%")
    print(f"Timeout: {limits['timeout_seconds']}s")
```

## Security Best Practices

### 1. Always Enable Safety Controls

```python
# Good: Use safety controls
from common.safety.config_integration import execute_code_safely_with_config

result = execute_code_safely_with_config(
    code=user_provided_code,
    language="python"
)

# Bad: Direct execution without safety
exec(user_provided_code)  # Never do this!
```

### 2. Use Appropriate Resource Limits

```python
# Set conservative limits for untrusted code
result = sandbox.execute_code(
    code=untrusted_code,
    max_memory_mb=256,      # Limit memory
    max_cpu_percent=50,     # Limit CPU
    timeout_seconds=30,     # Short timeout
    network_enabled=False   # No network access
)
```

### 3. Validate Inputs

```python
def validate_code(code: str) -> bool:
    """Basic code validation."""
    dangerous_patterns = [
        'import os',
        'import subprocess',
        'eval(',
        'exec(',
        '__import__'
    ]
    
    return not any(pattern in code for pattern in dangerous_patterns)

if validate_code(user_code):
    result = sandbox.execute_code(user_code)
else:
    print("Code contains potentially dangerous patterns")
```

### 4. Monitor Resource Usage

```python
result = sandbox.execute_code(code)

# Log resource usage for monitoring
logger.info(f"Execution completed: {result.status}")
logger.info(f"Memory usage: {result.memory_usage_mb:.1f} MB")
logger.info(f"CPU usage: {result.cpu_usage_percent:.1f}%")
logger.info(f"Execution time: {result.execution_time:.2f}s")

# Alert on high resource usage
if result.memory_usage_mb > 512:
    logger.warning("High memory usage detected")
```

## Filesystem Access Controls

### Overview

The filesystem access control system provides secure file operations with comprehensive path validation, access controls, and audit logging. It prevents unauthorized access to system files, blocks path traversal attacks, and maintains detailed audit trails.

### Basic Usage

```python
from common.safety import FilesystemAccessController, FilesystemPolicy

# Create filesystem controller
policy = FilesystemPolicy(
    restrict_to_repo=True,
    temp_dir_access=True,
    audit_enabled=True
)
controller = FilesystemAccessController(policy, repo_root="/path/to/repo")

# Safe file operations
controller.safe_write("data.txt", "Hello World")
content = controller.safe_read("data.txt")
controller.safe_copy("data.txt", "backup.txt")
```

### Configuration Integration

```python
from common.safety import SafetyManager

# Use configuration-based filesystem controls
safety_manager = SafetyManager(repo_root="/path/to/repo")

# Perform operations using configuration policies
safety_manager.safe_file_operation('write', 'file.txt', 'content')
content = safety_manager.safe_file_operation('read', 'file.txt')
```

### Security Features

#### Path Validation
- **Path traversal protection** - Blocks `../` and similar patterns
- **Allowlist enforcement** - Only allows access to specified directories
- **Denylist checking** - Explicitly blocks dangerous locations
- **Extension filtering** - Controls allowed/denied file extensions

#### Access Controls
- **Repository restriction** - Limits access to repository root
- **Temporary directory management** - Controlled temp file creation
- **System access prevention** - Blocks access to system directories
- **File size limits** - Prevents large file operations

#### Audit Logging
- **Operation tracking** - Logs all file operations with timestamps
- **Access results** - Records allowed/denied/restricted access
- **Checksum calculation** - Tracks file integrity changes
- **Export capabilities** - JSON export for analysis

### File Operations

#### Safe File Reading
```python
# Basic reading
content = controller.safe_read("config.json")

# Binary reading
binary_data = controller.safe_read("image.png", binary=True)

# Context manager
with controller.safe_open("data.txt", 'r') as f:
    for line in f:
        print(line.strip())
```

#### Safe File Writing
```python
# Basic writing
controller.safe_write("output.txt", "Hello World")

# Binary writing
controller.safe_write("data.bin", b"\x00\x01\x02", binary=True)

# Append mode
controller.safe_write("log.txt", "New entry\n", append=True)

# Context manager
with controller.safe_open("report.txt", 'w') as f:
    f.write("Report header\n")
    f.write("Report content\n")
```

#### File Management
```python
# Copy files
controller.safe_copy("source.txt", "destination.txt")

# Move files
controller.safe_move("old_name.txt", "new_name.txt")

# Delete files
controller.safe_delete("unwanted.txt")

# Create temporary directories
temp_dir = controller.create_temp_dir(prefix="work_")
temp_file = temp_dir / "temp_data.txt"
controller.safe_write(temp_file, "temporary data")

# Cleanup
controller.cleanup_temp_dirs()
```

### Policy Configuration

#### Basic Policy
```python
policy = FilesystemPolicy(
    restrict_to_repo=True,        # Limit to repository
    temp_dir_access=True,         # Allow temp directories
    system_access=False,          # Block system access
    max_file_size=100*1024*1024,  # 100MB limit
    audit_enabled=True            # Enable logging
)
```

#### Advanced Policy
```python
policy = FilesystemPolicy(
    allowed_paths=["/safe/path1", "/safe/path2"],
    denied_paths=["/dangerous/path"],
    allowed_extensions={'.py', '.txt', '.json'},
    denied_extensions={'.exe', '.dll', '.so'},
    max_files_created=1000,
    audit_log_path="/var/log/filesystem_audit.log"
)
```

### Global Functions

For convenience, global functions are available:

```python
from common.safety import safe_open, safe_read, safe_write, safe_copy, safe_delete

# Initialize global controller (done automatically)
from common.safety import get_fs_controller
controller = get_fs_controller(repo_root="/path/to/repo")

# Use global functions
safe_write("file.txt", "content")
content = safe_read("file.txt")
safe_copy("file.txt", "backup.txt")

with safe_open("data.txt", 'w') as f:
    f.write("data")
```

### Audit and Monitoring

#### Audit Log Access
```python
# Get recent audit entries
recent_logs = controller.get_audit_log(limit=10)

for log_entry in recent_logs:
    print(f"{log_entry.timestamp}: {log_entry.operation} - {log_entry.result}")
```

#### Statistics
```python
stats = controller.get_statistics()
print(f"Total operations: {stats['total_operations']}")
print(f"Files created: {stats['files_created']}")
print(f"Denied operations: {stats['denied_operations']}")
```

#### Export Audit Log
```python
# Export to JSON file
controller.export_audit_log("filesystem_audit.json")

# The exported file contains detailed operation records
```

### Security Best Practices

#### 1. Use Restrictive Policies
```python
# Recommended for production
policy = FilesystemPolicy(
    restrict_to_repo=True,
    temp_dir_access=True,
    system_access=False,
    max_file_size=10*1024*1024,  # 10MB limit
    allowed_extensions={'.py', '.js', '.json', '.txt', '.md'},
    denied_extensions={'.exe', '.dll', '.so', '.bat', '.sh'}
)
```

#### 2. Monitor Access Patterns
```python
# Regular monitoring
stats = controller.get_statistics()
if stats['denied_operations'] > 0:
    print("Security violations detected!")
    
    # Review denied operations
    audit_log = controller.get_audit_log()
    denied_ops = [op for op in audit_log if op.result == AccessResult.DENIED]
    for op in denied_ops:
        print(f"Denied: {op.operation} on {op.path} - {op.error_message}")
```

#### 3. Validate File Extensions
```python
# Be explicit about allowed file types
policy = FilesystemPolicy(
    allowed_extensions={'.py', '.json', '.txt'},  # Only allow specific types
    denied_extensions={'.exe', '.dll', '.so'}     # Explicitly deny dangerous types
)
```

#### 4. Use Temporary Directories
```python
# Create isolated temporary workspace
temp_dir = controller.create_temp_dir(prefix="agent_work_")

# Perform operations in temp directory
work_file = temp_dir / "processing.txt"
controller.safe_write(work_file, "work data")

# Always cleanup
controller.cleanup_temp_dirs()
```

### Error Handling

#### Common Exceptions
```python
try:
    controller.safe_read("/etc/passwd")
except PermissionError as e:
    print(f"Access denied: {e}")

try:
    controller.safe_write("malware.exe", "bad code")
except PermissionError as e:
    print(f"File type blocked: {e}")
```

#### Graceful Degradation
```python
def safe_file_operation(operation, *args, **kwargs):
    """Wrapper with fallback handling."""
    try:
        return controller.safe_file_operation(operation, *args, **kwargs)
    except PermissionError as e:
        logger.warning(f"File operation blocked: {e}")
        return None
    except Exception as e:
        logger.error(f"File operation failed: {e}")
        raise
```

## Troubleshooting

### Filesystem Issues

1. **Permission denied errors**
   ```python
   # Check policy configuration
   policy = controller.policy
   print(f"Repo restriction: {policy.restrict_to_repo}")
   print(f"Allowed paths: {policy.allowed_paths}")
   ```

2. **Path traversal blocks legitimate files**
   ```python
   # Use absolute paths or ensure proper path resolution
   file_path = Path("data/subdir/file.txt").resolve()
   controller.safe_read(file_path)
   ```

3. **File extension restrictions**
   ```python
   # Check allowed/denied extensions
   policy = FilesystemPolicy(
       allowed_extensions={'.py', '.txt', '.json', '.log'},  # Add .log
       denied_extensions={'.exe', '.dll'}
   )
   ```

### Docker Issues

1. **Docker not available**
   ```bash
   # Check Docker status
   docker --version
   docker ps
   
   # Restart Docker service
   sudo systemctl restart docker
   ```

2. **Permission denied**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Image build failures**
   ```python
   # Check Docker logs
   sandbox = ExecutionSandbox(SandboxType.DOCKER)
   if not sandbox.is_docker_available():
       print("Docker not available, using subprocess fallback")
   ```

### Resource Limit Issues

1. **Memory limits not enforced**
   - Subprocess sandbox has limited memory control
   - Use Docker sandbox for strict limits

2. **CPU limits not working**
   - Check system load
   - Verify cgroup support

### Network Access Problems

1. **Network requests failing**
   ```python
   # Enable network access
   result = sandbox.execute_code(
       code="import urllib.request; urllib.request.urlopen('https://httpbin.org/get')",
       network_enabled=True
   )
   ```

2. **DNS resolution issues**
   - Check Docker DNS configuration
   - Verify network connectivity

## Network Access Controls

### Overview

The network access control system provides secure HTTP/HTTPS requests, DNS lookups, and socket connections with comprehensive domain allowlists, request filtering, and audit logging. It prevents unauthorized network access, blocks malicious domains, and maintains detailed network operation logs.

### Basic Usage

```python
from common.safety import NetworkAccessController, NetworkPolicy

# Create network controller
policy = NetworkPolicy(
    default_deny=True,
    allowed_domains={"api.github.com", "*.example.com"},
    denied_domains={"malicious.com"},
    audit_enabled=True
)
controller = NetworkAccessController(policy)

# Safe HTTP requests
response = controller.safe_get("https://api.github.com/user")
response = controller.safe_post("https://api.github.com/repos", data='{"name": "test"}')
```

### Configuration Integration

```python
from common.safety import SafetyManager

# Use configuration-based network controls
safety_manager = SafetyManager()

# Perform operations using configuration policies
response = safety_manager.safe_file_operation('http_get', 'https://api.github.com/user')
ip = safety_manager.safe_file_operation('dns_lookup', 'api.github.com')
```

### Security Features

#### Domain Control
- **Allowlist enforcement** - Only allows access to specified domains
- **Denylist checking** - Explicitly blocks dangerous domains
- **Wildcard support** - Supports `*.example.com` patterns
- **IP address filtering** - Controls access by IP ranges

#### Protocol Security
- **HTTPS enforcement** - Can restrict to secure protocols only
- **Port restrictions** - Blocks dangerous ports (SSH, Telnet, etc.)
- **Request validation** - Validates URLs and parameters
- **SSL verification** - Configurable certificate validation

#### Rate Limiting
- **Request throttling** - Limits requests per time window
- **Per-host limits** - Separate limits for each destination
- **Burst protection** - Prevents rapid-fire requests
- **Automatic cleanup** - Removes old rate limit entries

### HTTP Operations

#### Safe HTTP Requests
```python
# GET request
response = controller.safe_get("https://api.github.com/user")
print(f"Status: {response['status_code']}")
print(f"Data: {response['data'].decode()}")

# POST request with JSON data
import json
data = json.dumps({"name": "test-repo"})
response = controller.safe_post(
    "https://api.github.com/user/repos",
    data=data,
    headers={"Content-Type": "application/json"}
)

# PUT request
response = controller.safe_put(
    "https://api.github.com/repos/user/repo",
    data='{"description": "Updated description"}'
)

# DELETE request
response = controller.safe_delete("https://api.github.com/repos/user/repo")
```

#### Response Handling
```python
response = controller.safe_get("https://api.github.com/user")

# Access response data
status_code = response['status_code']
headers = response['headers']
data = response['data']
url = response['url']
size = response['size']

# Handle different content types
if headers.get('Content-Type', '').startswith('application/json'):
    json_data = json.loads(data.decode())
elif headers.get('Content-Type', '').startswith('text/'):
    text_data = data.decode()
```

### DNS Operations

#### Safe DNS Lookups
```python
# Basic DNS lookup
ip_address = controller.safe_dns_lookup("api.github.com")
print(f"GitHub API IP: {ip_address}")

# Validate before lookup
result, error = controller.validate_network_access("https://example.com/")
if result == NetworkResult.ALLOWED:
    ip = controller.safe_dns_lookup("example.com")
```

### Socket Operations

#### Safe Socket Connections
```python
# TCP socket connection
with controller.safe_socket("api.github.com", 443, timeout=10) as sock:
    # Use socket for custom protocols
    sock.send(b"GET / HTTP/1.1\r\nHost: api.github.com\r\n\r\n")
    response = sock.recv(1024)
    print(response.decode())
```

### Policy Configuration

#### Basic Policy
```python
policy = NetworkPolicy(
    default_deny=True,              # Deny all by default
    allowed_domains={"api.github.com", "httpbin.org"},
    denied_domains={"malicious.com"},
    allowed_ports={80, 443},        # HTTP and HTTPS only
    request_timeout=30,             # 30 second timeout
    audit_enabled=True              # Enable logging
)
```

#### Advanced Policy
```python
policy = NetworkPolicy(
    default_deny=True,
    allowed_domains={"api.github.com", "*.example.com"},
    denied_domains={"*.evil.com", "malicious.org"},
    allowed_ips={"192.168.1.0/24", "10.0.0.1"},
    denied_ips={"127.0.0.1", "192.168.0.0/16"},
    allowed_ports={80, 443, 8080},
    denied_ports={22, 23, 25, 53},
    allowed_protocols={"http", "https"},
    request_timeout=60,
    max_response_size=10*1024*1024,  # 10MB limit
    max_redirects=5,
    verify_ssl=True,
    rate_limit=100,                  # 100 requests per minute
    rate_window=60,
    user_agent="AI-Dev-Squad-Agent/1.0"
)
```

### Global Functions

For convenience, global functions are available:

```python
from common.safety import safe_get, safe_post, safe_request, safe_dns_lookup

# Initialize global controller (done automatically)
from common.safety import get_net_controller
controller = get_net_controller(policy)

# Use global functions
response = safe_get("https://api.github.com/user")
response = safe_post("https://httpbin.org/post", data="test data")
ip = safe_dns_lookup("api.github.com")
```

### Audit and Monitoring

#### Network Audit Log
```python
# Get recent network operations
recent_logs = controller.get_audit_log(limit=10)

for log_entry in recent_logs:
    print(f"{log_entry.timestamp}: {log_entry.operation}")
    print(f"  URL: {log_entry.url}")
    print(f"  Result: {log_entry.result}")
    print(f"  Duration: {log_entry.duration_ms}ms")
```

#### Network Statistics
```python
stats = controller.get_statistics()
print(f"Total requests: {stats['total_operations']}")
print(f"Allowed requests: {stats['allowed_operations']}")
print(f"Denied requests: {stats['denied_operations']}")
print(f"Hosts accessed: {stats['hosts_accessed']}")
print(f"Data transferred: {stats['total_data_transferred']} bytes")
```

#### Export Network Audit Log
```python
# Export to JSON file
controller.export_audit_log("network_audit.json")

# The exported file contains detailed network operation records
```

### Security Best Practices

#### 1. Use Restrictive Policies
```python
# Recommended for production
policy = NetworkPolicy(
    default_deny=True,
    allowed_domains={"api.github.com", "api.gitlab.com"},  # Specific domains only
    denied_domains={"*.suspicious.com", "malware.org"},
    allowed_ports={443},            # HTTPS only
    denied_ports={22, 23, 25, 53},  # Block dangerous ports
    verify_ssl=True,                # Always verify certificates
    rate_limit=60,                  # Reasonable rate limit
    max_response_size=5*1024*1024   # 5MB response limit
)
```

#### 2. Monitor Network Activity
```python
# Regular monitoring
stats = controller.get_statistics()
if stats['denied_operations'] > 0:
    print("Network security violations detected!")
    
    # Review denied operations
    audit_log = controller.get_audit_log()
    denied_ops = [op for op in audit_log if op.result == NetworkResult.DENIED]
    for op in denied_ops:
        print(f"Denied: {op.operation} to {op.host} - {op.error_message}")
```

#### 3. Validate Domains and IPs
```python
# Be explicit about allowed destinations
policy = NetworkPolicy(
    allowed_domains={"api.github.com", "api.gitlab.com"},  # Specific services
    allowed_ips={"192.168.1.0/24"},                       # Internal network
    denied_ips={"127.0.0.1", "0.0.0.0/8"}                # Localhost and reserved
)
```

#### 4. Use Rate Limiting
```python
# Prevent abuse
policy = NetworkPolicy(
    rate_limit=100,     # 100 requests per window
    rate_window=60,     # 60 second window
)

# Check rate limits programmatically
if not controller._check_rate_limit("api.github.com"):
    print("Rate limit exceeded for GitHub API")
```

### Error Handling

#### Common Exceptions
```python
try:
    response = controller.safe_get("https://malicious.com/")
except PermissionError as e:
    print(f"Network access denied: {e}")

try:
    response = controller.safe_get("https://api.github.com/nonexistent")
except urllib.error.HTTPError as e:
    print(f"HTTP error: {e.code} {e.reason}")

try:
    ip = controller.safe_dns_lookup("nonexistent.domain.invalid")
except Exception as e:
    print(f"DNS lookup failed: {e}")
```

#### Graceful Degradation
```python
def safe_network_operation(operation, *args, **kwargs):
    """Wrapper with fallback handling."""
    try:
        return controller.safe_request(*args, **kwargs)
    except PermissionError as e:
        logger.warning(f"Network operation blocked: {e}")
        return None
    except urllib.error.URLError as e:
        logger.error(f"Network operation failed: {e}")
        return None
```

## Troubleshooting

### Network Issues

1. **Domain access denied**
   ```python
   # Check policy configuration
   policy = controller.policy
   print(f"Default deny: {policy.default_deny}")
   print(f"Allowed domains: {policy.allowed_domains}")
   print(f"Denied domains: {policy.denied_domains}")
   ```

2. **Rate limiting issues**
   ```python
   # Clear rate limits if needed
   controller.clear_rate_limits()
   
   # Check current rate limit status
   allowed = controller._check_rate_limit("api.github.com")
   print(f"Rate limit status: {'OK' if allowed else 'Exceeded'}")
   ```

3. **SSL certificate errors**
   ```python
   # Disable SSL verification for testing (not recommended for production)
   policy = NetworkPolicy(verify_ssl=False)
   
   # Or configure custom SSL context
   import ssl
   ssl_context = ssl.create_default_context()
   ssl_context.check_hostname = False
   ```

### Performance Issues

1. **Slow network requests**
   - Check network connectivity
   - Increase timeout values
   - Monitor response sizes

2. **High memory usage**
   - Reduce max_response_size
   - Monitor for large responses
   - Use streaming for large data

3. **Rate limit exceeded**
   - Increase rate_limit value
   - Implement request queuing
   - Use multiple API keys/endpoints

## Examples

See `examples/sandbox_demo.py` for comprehensive examples demonstrating:

- Basic code execution
- File operations
- Resource limit enforcement
- Timeout handling
- Error scenarios
- Multi-language support

Run the demo:

```bash
python examples/sandbox_demo.py
```

## API Reference

### ExecutionSandbox

Main sandbox class for secure code execution.

#### Methods

- `execute_code(code, language, **kwargs)` - Execute code with safety controls
- `is_docker_available()` - Check Docker availability
- `get_sandbox_info()` - Get sandbox information

### ExecutionResult

Result object containing execution details.

#### Properties

- `status` - Execution status (success, failure, timeout, etc.)
- `stdout` - Standard output
- `stderr` - Standard error
- `exit_code` - Process exit code
- `execution_time` - Execution duration
- `memory_usage_mb` - Peak memory usage
- `cpu_usage_percent` - Peak CPU usage
- `error_message` - Error description

### SafetyManager

Configuration-integrated safety management.

#### Methods

- `execute_code_with_config(code, **kwargs)` - Execute with config-based settings
- `is_safety_enabled()` - Check if safety is enabled
- `get_resource_limits()` - Get current resource limits
- `validate_safety_configuration()` - Validate safety config