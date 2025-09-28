"""
Execution Sandbox for AI Dev Squad Comparison
This module provides secure code execution with Docker integration, resource limits,
network isolation, and comprehensive safety controls.
"""
import os
import sys
import time
import json
import tempfile
import subprocess
import threading
import signal
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import shutil
import docker
from docker.errors import DockerException, ContainerError, ImageNotFound
import psutil

logger = logging.getLogger(__name__)

class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_VIOLATION = "security_violation"
    DOCKER_ERROR = "docker_error"
    SYSTEM_ERROR = "system_error"

class SandboxType(str, Enum):
    """Sandbox type enumeration."""
    DOCKER = "docker"
    SUBPROCESS = "subprocess"

@dataclass
class ExecutionContext:
    """Context for code execution."""
    code: str
    language: str = "python"
    working_dir: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    files: Dict[str, str] = field(default_factory=dict)  # filename -> content
    requirements: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    max_memory_mb: int = 1024
    max_cpu_percent: int = 80
    network_enabled: bool = False
    allowed_hosts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    """Result of code execution."""
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    network_calls: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    container_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResourceMonitor:
    """Monitor resource usage during execution."""
    
    def __init__(self, max_memory_mb: int, max_cpu_percent: int):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.monitoring = False
        self.peak_memory_mb = 0.0
        self.peak_cpu_percent = 0.0
        self.violations = []
        self._monitor_thread = None
        self._process = None
    
    def start_monitoring(self, process_or_container):
        """Start monitoring resource usage."""
        self.monitoring = True
        self._process = process_or_container
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring resource usage."""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                if hasattr(self._process, 'stats'):  # Docker container
                    self._monitor_docker_container()
                else:  # Process
                    self._monitor_process()
                time.sleep(0.1)  # Monitor every 100ms
            except Exception as e:
                logger.warning(f"Resource monitoring error: {e}")
                break
    
    def _monitor_docker_container(self):
        """Monitor Docker container resources."""
        try:
            stats = self._process.stats(stream=False)
            
            # Memory usage
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_mb = memory_usage / (1024 * 1024)
            self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
            
            if memory_mb > self.max_memory_mb:
                self.violations.append(f"Memory limit exceeded: {memory_mb:.1f}MB > {self.max_memory_mb}MB")
                self.monitoring = False
                return
            
            # CPU usage
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            if cpu_stats and precpu_stats:
                cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100.0
                    self.peak_cpu_percent = max(self.peak_cpu_percent, cpu_percent)
                    
                    if cpu_percent > self.max_cpu_percent:
                        self.violations.append(f"CPU limit exceeded: {cpu_percent:.1f}% > {self.max_cpu_percent}%")
                        self.monitoring = False
                        return
        
        except Exception as e:
            logger.debug(f"Docker monitoring error: {e}")
    
    def _monitor_process(self):
        """Monitor subprocess resources."""
        try:
            if not self._process or self._process.poll() is not None:
                return
            
            process = psutil.Process(self._process.pid)
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
            
            if memory_mb > self.max_memory_mb:
                self.violations.append(f"Memory limit exceeded: {memory_mb:.1f}MB > {self.max_memory_mb}MB")
                self.monitoring = False
                return
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            self.peak_cpu_percent = max(self.peak_cpu_percent, cpu_percent)
            
            if cpu_percent > self.max_cpu_percent:
                self.violations.append(f"CPU limit exceeded: {cpu_percent:.1f}% > {self.max_cpu_percent}%")
                self.monitoring = False
                return
        
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.debug(f"Process monitoring error: {e}")

class DockerSandbox:
    """Docker-based execution sandbox."""
    
    def __init__(self):
        self.client = None
        self.base_images = {
            'python': 'python:3.11-slim',
            'javascript': 'node:18-slim',
            'bash': 'ubuntu:22.04',
            'shell': 'ubuntu:22.04'
        }
        self._initialize_docker()
    
    def _initialize_docker(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            # Test Docker connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Docker is available."""
        return self.client is not None
    
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute code in Docker container."""
        if not self.is_available():
            return ExecutionResult(
                status=ExecutionStatus.DOCKER_ERROR,
                error_message="Docker is not available"
            )
        
        start_time = time.time()
        container = None
        monitor = ResourceMonitor(context.max_memory_mb, context.max_cpu_percent)
        
        try:
            # Prepare execution environment
            temp_dir = self._prepare_execution_environment(context)
            
            # Get or build image
            image = self._get_or_build_image(context.language, context.requirements)
            
            # Create container
            container = self._create_container(image, context, temp_dir)
            
            # Start monitoring
            monitor.start_monitoring(container)
            
            # Execute code
            result = self._execute_in_container(container, context, monitor)
            
            # Calculate execution time
            result.execution_time = time.time() - start_time
            result.memory_usage_mb = monitor.peak_memory_mb
            result.cpu_usage_percent = monitor.peak_cpu_percent
            result.container_id = container.id[:12]
            
            # Check for resource violations
            if monitor.violations:
                result.status = ExecutionStatus.RESOURCE_LIMIT
                result.error_message = "; ".join(monitor.violations)
            
            return result
        
        except Exception as e:
            logger.error(f"Docker execution error: {e}")
            return ExecutionResult(
                status=ExecutionStatus.DOCKER_ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
        
        finally:
            monitor.stop_monitoring()
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")
    
    def _prepare_execution_environment(self, context: ExecutionContext) -> str:
        """Prepare temporary directory with code and files."""
        temp_dir = tempfile.mkdtemp(prefix="ai_dev_squad_")
        
        # Write main code file
        code_file = self._get_code_filename(context.language)
        with open(os.path.join(temp_dir, code_file), 'w') as f:
            f.write(context.code)
        
        # Write additional files
        for filename, content in context.files.items():
            file_path = os.path.join(temp_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Create requirements file if needed
        if context.requirements:
            if context.language == 'python':
                with open(os.path.join(temp_dir, 'requirements.txt'), 'w') as f:
                    f.write('\n'.join(context.requirements))
            elif context.language == 'javascript':
                package_json = {
                    "name": "ai-dev-squad-execution",
                    "version": "1.0.0",
                    "dependencies": {req: "latest" for req in context.requirements}
                }
                with open(os.path.join(temp_dir, 'package.json'), 'w') as f:
                    json.dump(package_json, f, indent=2)
        
        return temp_dir
    
    def _get_code_filename(self, language: str) -> str:
        """Get appropriate filename for code."""
        extensions = {
            'python': 'main.py',
            'javascript': 'main.js',
            'bash': 'main.sh',
            'shell': 'main.sh'
        }
        return extensions.get(language, 'main.txt')
    
    def _get_or_build_image(self, language: str, requirements: List[str]) -> str:
        """Get or build Docker image for execution."""
        base_image = self.base_images.get(language, 'ubuntu:22.04')
        
        if not requirements:
            # Use base image if no requirements
            try:
                self.client.images.get(base_image)
                return base_image
            except ImageNotFound:
                logger.info(f"Pulling base image: {base_image}")
                self.client.images.pull(base_image)
                return base_image
        
        # Build custom image with requirements
        dockerfile_content = self._generate_dockerfile(language, base_image, requirements)
        
        # Create temporary directory for build context
        build_dir = tempfile.mkdtemp(prefix="ai_dev_squad_build_")
        dockerfile_path = os.path.join(build_dir, 'Dockerfile')
        
        try:
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            # Build image
            image_tag = f"ai-dev-squad-{language}-{hash(tuple(requirements)) % 10000}"
            
            try:
                # Check if image already exists
                self.client.images.get(image_tag)
                return image_tag
            except ImageNotFound:
                logger.info(f"Building custom image: {image_tag}")
                self.client.images.build(
                    path=build_dir,
                    tag=image_tag,
                    rm=True,
                    forcerm=True
                )
                return image_tag
        
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)
    
    def _generate_dockerfile(self, language: str, base_image: str, requirements: List[str]) -> str:
        """Generate Dockerfile for custom image."""
        if language == 'python':
            return f"""
FROM {base_image}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set working directory
WORKDIR /workspace

# Create non-root user
RUN useradd -m -u 1000 sandbox
USER sandbox
"""
        elif language == 'javascript':
            return f"""
FROM {base_image}

# Install dependencies
COPY package.json /tmp/package.json
WORKDIR /tmp
RUN npm install

# Set working directory
WORKDIR /workspace

# Create non-root user
RUN useradd -m -u 1000 sandbox
USER sandbox
"""
        else:
            return f"""
FROM {base_image}

# Install basic tools
RUN apt-get update && apt-get install -y \\
    curl \\
    wget \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Create non-root user
RUN useradd -m -u 1000 sandbox
USER sandbox
"""
    
    def _create_container(self, image: str, context: ExecutionContext, temp_dir: str):
        """Create Docker container for execution."""
        # Container configuration
        container_config = {
            'image': image,
            'working_dir': '/workspace',
            'volumes': {temp_dir: {'bind': '/workspace', 'mode': 'rw'}},
            'environment': context.environment,
            'mem_limit': f"{context.max_memory_mb}m",
            'memswap_limit': f"{context.max_memory_mb}m",
            'cpu_period': 100000,
            'cpu_quota': int(100000 * context.max_cpu_percent / 100),
            'network_disabled': not context.network_enabled,
            'user': '1000:1000',  # Run as non-root user
            'security_opt': ['no-new-privileges:true'],
            'cap_drop': ['ALL'],
            'read_only': False,  # Allow writes to workspace
            'tmpfs': {'/tmp': 'noexec,nosuid,size=100m'},
            'detach': True,
            'stdin_open': True,
            'tty': True
        }
        
        # Create and start container
        container = self.client.containers.create(**container_config)
        container.start()
        
        return container
    
    def _execute_in_container(self, container, context: ExecutionContext, monitor: ResourceMonitor) -> ExecutionResult:
        """Execute code inside container."""
        # Prepare execution command
        cmd = self._get_execution_command(context.language)
        
        try:
            # Execute command with timeout
            exec_result = container.exec_run(
                cmd,
                workdir='/workspace',
                user='1000:1000',
                environment=context.environment,
                demux=True
            )
            
            # Wait for completion with timeout
            start_time = time.time()
            while container.status == 'running':
                if time.time() - start_time > context.timeout_seconds:
                    container.kill()
                    return ExecutionResult(
                        status=ExecutionStatus.TIMEOUT,
                        error_message=f"Execution timed out after {context.timeout_seconds} seconds"
                    )
                
                if monitor.violations:
                    container.kill()
                    break
                
                time.sleep(0.1)
            
            # Get execution results
            stdout = exec_result.output[0].decode('utf-8') if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode('utf-8') if exec_result.output[1] else ""
            
            # Determine status
            if monitor.violations:
                status = ExecutionStatus.RESOURCE_LIMIT
            elif exec_result.exit_code == 0:
                status = ExecutionStatus.SUCCESS
            else:
                status = ExecutionStatus.FAILURE
            
            return ExecutionResult(
                status=status,
                stdout=stdout,
                stderr=stderr,
                exit_code=exec_result.exit_code
            )
        
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.DOCKER_ERROR,
                error_message=f"Container execution error: {e}"
            )
    
    def _get_execution_command(self, language: str) -> List[str]:
        """Get execution command for language."""
        commands = {
            'python': ['python', 'main.py'],
            'javascript': ['node', 'main.js'],
            'bash': ['bash', 'main.sh'],
            'shell': ['bash', 'main.sh']
        }
        return commands.get(language, ['cat', 'main.txt'])

class SubprocessSandbox:
    """Subprocess-based execution sandbox (fallback when Docker is unavailable)."""
    
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute code in subprocess."""
        start_time = time.time()
        temp_dir = None
        process = None
        monitor = ResourceMonitor(context.max_memory_mb, context.max_cpu_percent)
        
        try:
            # Prepare execution environment
            temp_dir = self._prepare_execution_environment(context)
            
            # Prepare execution command
            cmd = self._get_execution_command(context.language, temp_dir)
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, **context.environment},
                text=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Start monitoring
            monitor.start_monitoring(process)
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=context.timeout_seconds)
                exit_code = process.returncode
                
                # Check for resource violations
                if monitor.violations:
                    status = ExecutionStatus.RESOURCE_LIMIT
                    error_message = "; ".join(monitor.violations)
                elif exit_code == 0:
                    status = ExecutionStatus.SUCCESS
                    error_message = None
                else:
                    status = ExecutionStatus.FAILURE
                    error_message = None
                
                return ExecutionResult(
                    status=status,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    execution_time=time.time() - start_time,
                    memory_usage_mb=monitor.peak_memory_mb,
                    cpu_usage_percent=monitor.peak_cpu_percent,
                    error_message=error_message
                )
            
            except subprocess.TimeoutExpired:
                # Kill process group to ensure all child processes are terminated
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                process.wait(timeout=5)
                
                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    error_message=f"Execution timed out after {context.timeout_seconds} seconds",
                    execution_time=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Subprocess execution error: {e}")
            return ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
        
        finally:
            monitor.stop_monitoring()
            if process and process.poll() is None:
                try:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
                except Exception:
                    pass
            
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _prepare_execution_environment(self, context: ExecutionContext) -> str:
        """Prepare temporary directory with code and files."""
        temp_dir = tempfile.mkdtemp(prefix="ai_dev_squad_subprocess_")
        
        # Write main code file
        code_file = self._get_code_filename(context.language)
        with open(os.path.join(temp_dir, code_file), 'w') as f:
            f.write(context.code)
        
        # Write additional files
        for filename, content in context.files.items():
            file_path = os.path.join(temp_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
        
        return temp_dir
    
    def _get_code_filename(self, language: str) -> str:
        """Get appropriate filename for code."""
        extensions = {
            'python': 'main.py',
            'javascript': 'main.js',
            'bash': 'main.sh',
            'shell': 'main.sh'
        }
        return extensions.get(language, 'main.txt')
    
    def _get_execution_command(self, language: str, temp_dir: str) -> List[str]:
        """Get execution command for language."""
        code_file = self._get_code_filename(language)
        file_path = os.path.join(temp_dir, code_file)
        
        commands = {
            'python': [sys.executable, file_path],
            'javascript': ['node', file_path],
            'bash': ['bash', file_path],
            'shell': ['bash', file_path]
        }
        return commands.get(language, ['cat', file_path])

class ExecutionSandbox:
    """Main execution sandbox that chooses between Docker and subprocess."""
    
    def __init__(self, sandbox_type: Optional[SandboxType] = None):
        self.sandbox_type = sandbox_type or SandboxType.DOCKER
        self.docker_sandbox = DockerSandbox()
        self.subprocess_sandbox = SubprocessSandbox()
        
        # Auto-detect best available sandbox
        if self.sandbox_type == SandboxType.DOCKER and not self.docker_sandbox.is_available():
            logger.warning("Docker not available, falling back to subprocess sandbox")
            self.sandbox_type = SandboxType.SUBPROCESS
    
    def execute_code(self, 
                    code: str,
                    language: str = "python",
                    timeout_seconds: int = 300,
                    max_memory_mb: int = 1024,
                    max_cpu_percent: int = 80,
                    network_enabled: bool = False,
                    files: Optional[Dict[str, str]] = None,
                    requirements: Optional[List[str]] = None,
                    environment: Optional[Dict[str, str]] = None,
                    **kwargs) -> ExecutionResult:
        """
        Execute code in a secure sandbox.
        
        Args:
            code: Code to execute
            language: Programming language (python, javascript, bash, shell)
            timeout_seconds: Maximum execution time
            max_memory_mb: Maximum memory usage
            max_cpu_percent: Maximum CPU usage
            network_enabled: Whether to allow network access
            files: Additional files to create in workspace
            requirements: Package requirements to install
            environment: Environment variables
            **kwargs: Additional context parameters
            
        Returns:
            ExecutionResult with status, output, and resource usage
        """
        context = ExecutionContext(
            code=code,
            language=language,
            timeout_seconds=timeout_seconds,
            max_memory_mb=max_memory_mb,
            max_cpu_percent=max_cpu_percent,
            network_enabled=network_enabled,
            files=files or {},
            requirements=requirements or [],
            environment=environment or {},
            **kwargs
        )
        
        logger.info(f"Executing {language} code in {self.sandbox_type.value} sandbox")
        
        if self.sandbox_type == SandboxType.DOCKER:
            return self.docker_sandbox.execute(context)
        else:
            return self.subprocess_sandbox.execute(context)
    
    def is_docker_available(self) -> bool:
        """Check if Docker sandbox is available."""
        return self.docker_sandbox.is_available()
    
    def get_sandbox_info(self) -> Dict[str, Any]:
        """Get information about the current sandbox."""
        return {
            'type': self.sandbox_type.value,
            'docker_available': self.is_docker_available(),
            'supported_languages': ['python', 'javascript', 'bash', 'shell']
        }

# Global sandbox instance
_sandbox: Optional[ExecutionSandbox] = None

def get_sandbox(sandbox_type: Optional[SandboxType] = None) -> ExecutionSandbox:
    """Get the global sandbox instance."""
    global _sandbox
    if _sandbox is None or (sandbox_type and _sandbox.sandbox_type != sandbox_type):
        _sandbox = ExecutionSandbox(sandbox_type)
    return _sandbox

def execute_code_safely(code: str, **kwargs) -> ExecutionResult:
    """
    Convenience function for safe code execution.
    
    Args:
        code: Code to execute
        **kwargs: Additional execution parameters
        
    Returns:
        ExecutionResult with status, output, and resource usage
    """
    sandbox = get_sandbox()
    return sandbox.execute_code(code, **kwargs)