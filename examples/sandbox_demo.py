#!/usr/bin/env python3
"""
Execution Sandbox Demo
This script demonstrates the capabilities of the execution sandbox
with various code examples and safety scenarios.
"""
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.safety.execute import ExecutionSandbox, SandboxType, ExecutionStatus

def demo_basic_execution():
    """Demo basic code execution."""
    print("=== Basic Code Execution Demo ===")
    
    sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
    
    # Python code execution
    print("\n1. Python Hello World:")
    result = sandbox.execute_code(
        code="print('Hello from Python sandbox!')",
        language="python",
        timeout_seconds=10
    )
    print(f"Status: {result.status}")
    print(f"Output: {result.stdout.strip()}")
    print(f"Execution time: {result.execution_time:.2f}s")
    
    # JavaScript code execution (if Node.js is available)
    print("\n2. JavaScript Hello World:")
    result = sandbox.execute_code(
        code="console.log('Hello from JavaScript sandbox!');",
        language="javascript",
        timeout_seconds=10
    )
    print(f"Status: {result.status}")
    if result.status == ExecutionStatus.SUCCESS:
        print(f"Output: {result.stdout.strip()}")
    else:
        print(f"Error: {result.error_message}")
    
    # Bash script execution
    print("\n3. Bash Script:")
    result = sandbox.execute_code(
        code="""
echo "Hello from Bash sandbox!"
echo "Current directory: $(pwd)"
echo "Available files: $(ls -la)"
""",
        language="bash",
        timeout_seconds=10
    )
    print(f"Status: {result.status}")
    print(f"Output: {result.stdout.strip()}")

def demo_file_operations():
    """Demo file operations in sandbox."""
    print("\n=== File Operations Demo ===")
    
    sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
    
    # Code that works with files
    code = """
import json
import os

# Read configuration file
with open('config.json', 'r') as f:
    config = json.load(f)
    print(f"Loaded config: {config['app_name']} v{config['version']}")

# Read data file
with open('data.txt', 'r') as f:
    data = f.read().strip()
    print(f"Data content: {data}")

# Create output file
output = {
    "processed": True,
    "timestamp": "2024-01-01T00:00:00Z",
    "data_length": len(data)
}

with open('output.json', 'w') as f:
    json.dump(output, f, indent=2)
    print("Created output.json")

# List all files
print("Files in workspace:")
for file in os.listdir('.'):
    print(f"  - {file}")
"""
    
    files = {
        "config.json": json.dumps({
            "app_name": "SandboxDemo",
            "version": "1.0.0",
            "debug": True
        }, indent=2),
        "data.txt": "This is sample data for processing.\nIt contains multiple lines.\nAnd some numbers: 123, 456, 789"
    }
    
    result = sandbox.execute_code(
        code=code,
        language="python",
        files=files,
        timeout_seconds=15
    )
    
    print(f"Status: {result.status}")
    print(f"Output:\n{result.stdout}")
    if result.stderr:
        print(f"Errors:\n{result.stderr}")

def demo_resource_limits():
    """Demo resource limit enforcement."""
    print("\n=== Resource Limits Demo ===")
    
    sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
    
    # Memory-intensive code
    print("\n1. Memory Usage Test:")
    result = sandbox.execute_code(
        code="""
import sys
print("Starting memory allocation test...")

# Allocate memory in chunks
data = []
for i in range(100):
    chunk = [0] * (1024 * 1024)  # 1MB per chunk
    data.append(chunk)
    if i % 10 == 0:
        print(f"Allocated {i+1} MB")

print(f"Total allocated: {len(data)} MB")
print("Memory test completed")
""",
        language="python",
        timeout_seconds=30,
        max_memory_mb=256  # Limit to 256MB
    )
    
    print(f"Status: {result.status}")
    print(f"Peak memory usage: {result.memory_usage_mb:.1f} MB")
    print(f"Output:\n{result.stdout}")
    if result.error_message:
        print(f"Resource limit message: {result.error_message}")
    
    # CPU-intensive code
    print("\n2. CPU Usage Test:")
    result = sandbox.execute_code(
        code="""
import time
print("Starting CPU-intensive task...")

# CPU-intensive calculation
start_time = time.time()
total = 0
for i in range(10000000):
    total += i * i
    if i % 1000000 == 0:
        elapsed = time.time() - start_time
        print(f"Processed {i} iterations in {elapsed:.2f}s")

print(f"Final result: {total}")
print("CPU test completed")
""",
        language="python",
        timeout_seconds=10,
        max_cpu_percent=50  # Limit to 50% CPU
    )
    
    print(f"Status: {result.status}")
    print(f"Peak CPU usage: {result.cpu_usage_percent:.1f}%")
    print(f"Execution time: {result.execution_time:.2f}s")
    print(f"Output:\n{result.stdout}")

def demo_timeout_handling():
    """Demo timeout handling."""
    print("\n=== Timeout Handling Demo ===")
    
    sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
    
    print("Running code that exceeds timeout...")
    result = sandbox.execute_code(
        code="""
import time
print("Starting long-running task...")

for i in range(10):
    print(f"Step {i+1}/10")
    time.sleep(2)  # Sleep for 2 seconds each step

print("Task completed (this should not appear)")
""",
        language="python",
        timeout_seconds=5  # Timeout after 5 seconds
    )
    
    print(f"Status: {result.status}")
    print(f"Execution time: {result.execution_time:.2f}s")
    print(f"Output:\n{result.stdout}")
    print(f"Error message: {result.error_message}")

def demo_error_handling():
    """Demo error handling and failure scenarios."""
    print("\n=== Error Handling Demo ===")
    
    sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
    
    # Syntax error
    print("\n1. Syntax Error:")
    result = sandbox.execute_code(
        code="print('Hello World'  # Missing closing parenthesis",
        language="python",
        timeout_seconds=10
    )
    print(f"Status: {result.status}")
    print(f"Exit code: {result.exit_code}")
    print(f"Error output:\n{result.stderr}")
    
    # Runtime error
    print("\n2. Runtime Error:")
    result = sandbox.execute_code(
        code="""
print("Starting execution...")
undefined_variable = some_undefined_variable
print("This line should not execute")
""",
        language="python",
        timeout_seconds=10
    )
    print(f"Status: {result.status}")
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.stdout}")
    print(f"Error output:\n{result.stderr}")
    
    # Division by zero
    print("\n3. Division by Zero:")
    result = sandbox.execute_code(
        code="""
print("Calculating result...")
numerator = 10
denominator = 0
result = numerator / denominator
print(f"Result: {result}")
""",
        language="python",
        timeout_seconds=10
    )
    print(f"Status: {result.status}")
    print(f"Output: {result.stdout}")
    print(f"Error output:\n{result.stderr}")

def demo_sandbox_info():
    """Demo sandbox information and capabilities."""
    print("\n=== Sandbox Information Demo ===")
    
    # Test different sandbox types
    for sandbox_type in [SandboxType.SUBPROCESS, SandboxType.DOCKER]:
        print(f"\n{sandbox_type.value.upper()} Sandbox:")
        
        try:
            sandbox = ExecutionSandbox(sandbox_type)
            info = sandbox.get_sandbox_info()
            
            print(f"  Type: {info['type']}")
            print(f"  Docker available: {info['docker_available']}")
            print(f"  Supported languages: {', '.join(info['supported_languages'])}")
            
            # Test basic execution
            result = sandbox.execute_code(
                code="print('Sandbox test successful')",
                language="python",
                timeout_seconds=5
            )
            print(f"  Test execution: {result.status}")
            
        except Exception as e:
            print(f"  Error: {e}")

def main():
    """Run all demos."""
    print("AI Dev Squad Comparison - Execution Sandbox Demo")
    print("=" * 60)
    
    try:
        demo_basic_execution()
        demo_file_operations()
        demo_resource_limits()
        demo_timeout_handling()
        demo_error_handling()
        demo_sandbox_info()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()