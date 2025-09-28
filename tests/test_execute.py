"""
Unit tests for the Execution Sandbox.
These tests validate secure code execution, resource monitoring,
and safety controls across Docker and subprocess environments.
"""
import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import docker
from docker.errors import DockerException

from common.safety.execute import (
    ExecutionSandbox, DockerSandbox, SubprocessSandbox,
    ExecutionContext, ExecutionResult, ExecutionStatus, SandboxType,
    ResourceMonitor, get_sandbox, execute_code_safely
)

class TestExecutionContext:
    """Test cases for ExecutionContext."""
    
    def test_execution_context_creation(self):
        """Test basic execution context creation."""
        context = ExecutionContext(
            code="print('hello world')",
            language="python",
            timeout_seconds=60,
            max_memory_mb=512
        )
        
        assert context.code == "print('hello world')"
        assert context.language == "python"
        assert context.timeout_seconds == 60
        assert context.max_memory_mb == 512
        assert context.max_cpu_percent == 80  # default
        assert context.network_enabled is False  # default
        assert len(context.files) == 0
        assert len(context.requirements) == 0
    
    def test_execution_context_with_files(self):
        """Test execution context with additional files."""
        files = {
            "helper.py": "def helper(): return 'help'",
            "data.txt": "some data"
        }
        
        context = ExecutionContext(
            code="import helper; print(helper.helper())",
            files=files
        )
        
        assert context.files == files
        assert "helper.py" in context.files
        assert "data.txt" in context.files
    
    def test_execution_context_with_requirements(self):
        """Test execution context with package requirements."""
        requirements = ["requests", "numpy"]
        
        context = ExecutionContext(
            code="import requests",
            requirements=requirements
        )
        
        assert context.requirements == requirements

class TestExecutionResult:
    """Test cases for ExecutionResult."""
    
    def test_execution_result_success(self):
        """Test successful execution result."""
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="Hello World",
            stderr="",
            exit_code=0,
            execution_time=1.5,
            memory_usage_mb=50.0
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.stdout == "Hello World"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.execution_time == 1.5
        assert result.memory_usage_mb == 50.0
    
    def test_execution_result_failure(self):
        """Test failed execution result."""
        result = ExecutionResult(
            status=ExecutionStatus.FAILURE,
            stdout="",
            stderr="NameError: name 'undefined_var' is not defined",
            exit_code=1,
            error_message="Python execution failed"
        )
        
        assert result.status == ExecutionStatus.FAILURE
        assert result.exit_code == 1
        assert "NameError" in result.stderr
        assert result.error_message == "Python execution failed"

class TestResourceMonitor:
    """Test cases for ResourceMonitor."""
    
    def test_resource_monitor_initialization(self):
        """Test resource monitor initialization."""
        monitor = ResourceMonitor(max_memory_mb=1024, max_cpu_percent=80)
        
        assert monitor.max_memory_mb == 1024
        assert monitor.max_cpu_percent == 80
        assert monitor.monitoring is False
        assert monitor.peak_memory_mb == 0.0
        assert monitor.peak_cpu_percent == 0.0
        assert len(monitor.violations) == 0
    
    def test_resource_monitor_start_stop(self):
        """Test resource monitor start and stop."""
        monitor = ResourceMonitor(max_memory_mb=1024, max_cpu_percent=80)
        mock_process = Mock()
        
        monitor.start_monitoring(mock_process)
        assert monitor.monitoring is True
        assert monitor._process is mock_process
        
        monitor.stop_monitoring()
        assert monitor.monitoring is False
    
    @patch('psutil.Process')
    def test_resource_monitor_process_monitoring(self, mock_psutil_process):
        """Test process resource monitoring."""
        # Mock process with memory and CPU usage
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100MB
        mock_process_instance.cpu_percent.return_value = 50.0
        mock_psutil_process.return_value = mock_process_instance
        
        # Mock subprocess
        mock_subprocess = Mock()
        mock_subprocess.pid = 12345
        mock_subprocess.poll.return_value = None  # Still running
        
        monitor = ResourceMonitor(max_memory_mb=1024, max_cpu_percent=80)
        monitor._process = mock_subprocess
        
        # Test monitoring loop (single iteration)
        monitor._monitor_process()
        
        assert monitor.peak_memory_mb >= 100.0
        assert monitor.peak_cpu_percent >= 50.0
        assert len(monitor.violations) == 0  # Within limits

class TestSubprocessSandbox:
    """Test cases for SubprocessSandbox."""
    
    def test_subprocess_sandbox_initialization(self):
        """Test subprocess sandbox initialization."""
        sandbox = SubprocessSandbox()
        assert sandbox is not None
    
    def test_prepare_execution_environment(self):
        """Test execution environment preparation."""
        sandbox = SubprocessSandbox()
        context = ExecutionContext(
            code="print('hello')",
            language="python",
            files={"test.txt": "test content"}
        )
        
        temp_dir = sandbox._prepare_execution_environment(context)
        
        try:
            # Check main code file
            main_file = os.path.join(temp_dir, "main.py")
            assert os.path.exists(main_file)
            with open(main_file, 'r') as f:
                assert f.read() == "print('hello')"
            
            # Check additional file
            test_file = os.path.join(temp_dir, "test.txt")
            assert os.path.exists(test_file)
            with open(test_file, 'r') as f:
                assert f.read() == "test content"
        
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_get_code_filename(self):
        """Test code filename generation."""
        sandbox = SubprocessSandbox()
        
        assert sandbox._get_code_filename("python") == "main.py"
        assert sandbox._get_code_filename("javascript") == "main.js"
        assert sandbox._get_code_filename("bash") == "main.sh"
        assert sandbox._get_code_filename("shell") == "main.sh"
        assert sandbox._get_code_filename("unknown") == "main.txt"
    
    @pytest.mark.integration
    def test_subprocess_execute_python_success(self):
        """Test successful Python code execution in subprocess."""
        sandbox = SubprocessSandbox()
        context = ExecutionContext(
            code="print('Hello from subprocess')",
            language="python",
            timeout_seconds=10
        )
        
        result = sandbox.execute(context)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello from subprocess" in result.stdout
        assert result.exit_code == 0
        assert result.execution_time > 0
    
    @pytest.mark.integration
    def test_subprocess_execute_python_failure(self):
        """Test failed Python code execution in subprocess."""
        sandbox = SubprocessSandbox()
        context = ExecutionContext(
            code="print(undefined_variable)",
            language="python",
            timeout_seconds=10
        )
        
        result = sandbox.execute(context)
        
        assert result.status == ExecutionStatus.FAILURE
        assert result.exit_code != 0
        assert "NameError" in result.stderr or "undefined_variable" in result.stderr
    
    @pytest.mark.integration
    def test_subprocess_execute_timeout(self):
        """Test timeout handling in subprocess execution."""
        sandbox = SubprocessSandbox()
        context = ExecutionContext(
            code="import time; time.sleep(10)",
            language="python",
            timeout_seconds=1
        )
        
        result = sandbox.execute(context)
        
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timed out" in result.error_message.lower()

class TestDockerSandbox:
    """Test cases for DockerSandbox."""
    
    def test_docker_sandbox_initialization(self):
        """Test Docker sandbox initialization."""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_docker.return_value = mock_client
            
            sandbox = DockerSandbox()
            
            assert sandbox.client is mock_client
            mock_client.ping.assert_called_once()
    
    def test_docker_sandbox_initialization_failure(self):
        """Test Docker sandbox initialization failure."""
        with patch('docker.from_env') as mock_docker:
            mock_docker.side_effect = DockerException("Docker not available")
            
            sandbox = DockerSandbox()
            
            assert sandbox.client is None
            assert not sandbox.is_available()
    
    def test_docker_sandbox_is_available(self):
        """Test Docker availability check."""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_docker.return_value = mock_client
            
            sandbox = DockerSandbox()
            
            assert sandbox.is_available() is True
    
    def test_prepare_execution_environment(self):
        """Test Docker execution environment preparation."""
        with patch('docker.from_env'):
            sandbox = DockerSandbox()
            context = ExecutionContext(
                code="print('hello')",
                language="python",
                files={"config.json": '{"test": true}'},
                requirements=["requests"]
            )
            
            temp_dir = sandbox._prepare_execution_environment(context)
            
            try:
                # Check main code file
                main_file = os.path.join(temp_dir, "main.py")
                assert os.path.exists(main_file)
                
                # Check additional file
                config_file = os.path.join(temp_dir, "config.json")
                assert os.path.exists(config_file)
                
                # Check requirements file
                req_file = os.path.join(temp_dir, "requirements.txt")
                assert os.path.exists(req_file)
                with open(req_file, 'r') as f:
                    assert "requests" in f.read()
            
            finally:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_generate_dockerfile_python(self):
        """Test Dockerfile generation for Python."""
        with patch('docker.from_env'):
            sandbox = DockerSandbox()
            dockerfile = sandbox._generate_dockerfile("python", "python:3.11-slim", ["requests"])
            
            assert "FROM python:3.11-slim" in dockerfile
            assert "pip install" in dockerfile
            assert "requirements.txt" in dockerfile
            assert "useradd" in dockerfile
    
    def test_generate_dockerfile_javascript(self):
        """Test Dockerfile generation for JavaScript."""
        with patch('docker.from_env'):
            sandbox = DockerSandbox()
            dockerfile = sandbox._generate_dockerfile("javascript", "node:18-slim", ["express"])
            
            assert "FROM node:18-slim" in dockerfile
            assert "npm install" in dockerfile
            assert "package.json" in dockerfile
            assert "useradd" in dockerfile
    
    def test_get_execution_command(self):
        """Test execution command generation."""
        with patch('docker.from_env'):
            sandbox = DockerSandbox()
            
            assert sandbox._get_execution_command("python") == ["python", "main.py"]
            assert sandbox._get_execution_command("javascript") == ["node", "main.js"]
            assert sandbox._get_execution_command("bash") == ["bash", "main.sh"]
            assert sandbox._get_execution_command("unknown") == ["cat", "main.txt"]
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("TEST_DOCKER"), reason="Docker tests disabled")
    def test_docker_execute_python_success(self):
        """Test successful Python code execution in Docker."""
        sandbox = DockerSandbox()
        
        if not sandbox.is_available():
            pytest.skip("Docker not available")
        
        context = ExecutionContext(
            code="print('Hello from Docker')",
            language="python",
            timeout_seconds=30
        )
        
        result = sandbox.execute(context)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello from Docker" in result.stdout
        assert result.exit_code == 0
        assert result.container_id is not None

class TestExecutionSandbox:
    """Test cases for main ExecutionSandbox."""
    
    def test_execution_sandbox_initialization_docker(self):
        """Test execution sandbox initialization with Docker."""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_docker.return_value = mock_client
            
            sandbox = ExecutionSandbox(SandboxType.DOCKER)
            
            assert sandbox.sandbox_type == SandboxType.DOCKER
            assert sandbox.docker_sandbox.client is mock_client
    
    def test_execution_sandbox_initialization_subprocess(self):
        """Test execution sandbox initialization with subprocess."""
        sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
        
        assert sandbox.sandbox_type == SandboxType.SUBPROCESS
        assert sandbox.subprocess_sandbox is not None
    
    def test_execution_sandbox_fallback_to_subprocess(self):
        """Test fallback to subprocess when Docker unavailable."""
        with patch('docker.from_env') as mock_docker:
            mock_docker.side_effect = DockerException("Docker not available")
            
            sandbox = ExecutionSandbox(SandboxType.DOCKER)
            
            assert sandbox.sandbox_type == SandboxType.SUBPROCESS
    
    def test_execute_code_parameters(self):
        """Test execute_code method parameter handling."""
        with patch('docker.from_env'):
            sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
            
            with patch.object(sandbox.subprocess_sandbox, 'execute') as mock_execute:
                mock_execute.return_value = ExecutionResult(status=ExecutionStatus.SUCCESS)
                
                result = sandbox.execute_code(
                    code="print('test')",
                    language="python",
                    timeout_seconds=60,
                    max_memory_mb=512,
                    network_enabled=True,
                    files={"test.py": "# test"},
                    requirements=["requests"]
                )
                
                mock_execute.assert_called_once()
                context = mock_execute.call_args[0][0]
                
                assert context.code == "print('test')"
                assert context.language == "python"
                assert context.timeout_seconds == 60
                assert context.max_memory_mb == 512
                assert context.network_enabled is True
                assert context.files == {"test.py": "# test"}
                assert context.requirements == ["requests"]
    
    def test_get_sandbox_info(self):
        """Test sandbox information retrieval."""
        with patch('docker.from_env'):
            sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
            
            info = sandbox.get_sandbox_info()
            
            assert info['type'] == 'subprocess'
            assert 'docker_available' in info
            assert 'supported_languages' in info
            assert 'python' in info['supported_languages']

class TestGlobalFunctions:
    """Test cases for global functions."""
    
    def test_get_sandbox_default(self):
        """Test getting default sandbox instance."""
        # Reset global state
        import common.safety.execute
        common.safety.execute._sandbox = None
        
        with patch('docker.from_env'):
            sandbox1 = get_sandbox()
            sandbox2 = get_sandbox()
            
            # Should return the same instance
            assert sandbox1 is sandbox2
            assert isinstance(sandbox1, ExecutionSandbox)
    
    def test_get_sandbox_with_type(self):
        """Test getting sandbox with specific type."""
        # Reset global state
        import common.safety.execute
        common.safety.execute._sandbox = None
        
        sandbox = get_sandbox(SandboxType.SUBPROCESS)
        
        assert sandbox.sandbox_type == SandboxType.SUBPROCESS
    
    def test_execute_code_safely(self):
        """Test convenience function for safe code execution."""
        with patch('common.safety.execute.get_sandbox') as mock_get_sandbox:
            mock_sandbox = Mock()
            mock_result = ExecutionResult(status=ExecutionStatus.SUCCESS, stdout="test output")
            mock_sandbox.execute_code.return_value = mock_result
            mock_get_sandbox.return_value = mock_sandbox
            
            result = execute_code_safely("print('test')", language="python")
            
            assert result is mock_result
            mock_sandbox.execute_code.assert_called_once_with("print('test')", language="python")

class TestIntegration:
    """Integration tests for the complete execution system."""
    
    @pytest.mark.integration
    def test_end_to_end_python_execution(self):
        """Test complete Python code execution workflow."""
        sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
        
        # Test successful execution
        result = sandbox.execute_code(
            code="""
import json
import os

# Test basic functionality
data = {"message": "Hello World", "number": 42}
print(json.dumps(data))

# Test file operations
with open("output.txt", "w") as f:
    f.write("Test output")

print("Execution completed successfully")
""",
            language="python",
            timeout_seconds=10,
            max_memory_mb=256
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello World" in result.stdout
        assert "Execution completed successfully" in result.stdout
        assert result.exit_code == 0
        assert result.execution_time > 0
        assert result.memory_usage_mb >= 0
    
    @pytest.mark.integration
    def test_end_to_end_resource_limits(self):
        """Test resource limit enforcement."""
        sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
        
        # Test memory limit (this might not trigger in subprocess mode)
        result = sandbox.execute_code(
            code="""
import time
# Simulate some work
for i in range(1000):
    data = [0] * 1000
    time.sleep(0.001)
print("Memory test completed")
""",
            language="python",
            timeout_seconds=5,
            max_memory_mb=64  # Very low limit
        )
        
        # Should complete successfully or hit resource limit
        assert result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.RESOURCE_LIMIT]
    
    @pytest.mark.integration
    def test_end_to_end_timeout(self):
        """Test timeout enforcement."""
        sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
        
        result = sandbox.execute_code(
            code="""
import time
print("Starting long operation...")
time.sleep(10)  # Sleep longer than timeout
print("This should not be printed")
""",
            language="python",
            timeout_seconds=2
        )
        
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timed out" in result.error_message.lower()
        assert "Starting long operation" in result.stdout
        assert "This should not be printed" not in result.stdout
    
    @pytest.mark.integration
    def test_end_to_end_with_files(self):
        """Test execution with additional files."""
        sandbox = ExecutionSandbox(SandboxType.SUBPROCESS)
        
        result = sandbox.execute_code(
            code="""
# Read from provided file
with open("config.json", "r") as f:
    import json
    config = json.load(f)
    print(f"Config loaded: {config['name']}")

# Read from data file
with open("data.txt", "r") as f:
    data = f.read().strip()
    print(f"Data: {data}")

print("File operations completed")
""",
            language="python",
            files={
                "config.json": '{"name": "test_config", "version": "1.0"}',
                "data.txt": "Sample data content"
            },
            timeout_seconds=10
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Config loaded: test_config" in result.stdout
        assert "Data: Sample data content" in result.stdout
        assert "File operations completed" in result.stdout

if __name__ == "__main__":
    pytest.main([__file__])