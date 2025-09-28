"""
Configuration Integration for Safety Module
This module integrates the execution sandbox and filesystem controls 
with the configuration management system.
"""
from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path

from common.config import get_config_manager, ConfigurationManager
from .execute import ExecutionSandbox, ExecutionContext, ExecutionResult, SandboxType
from .fs import FilesystemAccessController, FilesystemPolicy
from .net import NetworkAccessController, NetworkPolicy
from .injection import PromptInjectionGuard

logger = logging.getLogger(__name__)

class SafetyManager:
    """
    Safety manager that integrates execution sandbox and filesystem controls 
    with system configuration.
    """
    
    def __init__(self, config_manager: Optional[ConfigurationManager] = None, repo_root: Optional[str] = None):
        self.config_manager = config_manager or get_config_manager()
        self.repo_root = repo_root
        self._sandbox: Optional[ExecutionSandbox] = None
        self._fs_controller: Optional[FilesystemAccessController] = None
        self._net_controller: Optional[NetworkAccessController] = None
        self._injection_guard: Optional[PromptInjectionGuard] = None
    
    @property
    def sandbox(self) -> ExecutionSandbox:
        """Get or create execution sandbox based on configuration."""
        if self._sandbox is None:
            safety_config = self.config_manager.config.safety
            
            # Determine sandbox type from configuration
            if safety_config.sandbox_type == "docker":
                sandbox_type = SandboxType.DOCKER
            else:
                sandbox_type = SandboxType.SUBPROCESS
            
            self._sandbox = ExecutionSandbox(sandbox_type)
            
            logger.info(f"Initialized {self._sandbox.sandbox_type.value} sandbox")
        
        return self._sandbox
    
    @property
    def fs_controller(self) -> FilesystemAccessController:
        """Get or create filesystem access controller based on configuration."""
        if self._fs_controller is None:
            safety_config = self.config_manager.config.safety
            
            # Create filesystem policy from configuration
            policy = FilesystemPolicy(
                restrict_to_repo=safety_config.filesystem_policy.restrict_to_repo,
                temp_dir_access=safety_config.filesystem_policy.temp_dir_access,
                system_access=safety_config.filesystem_policy.system_access,
                audit_enabled=safety_config.enabled,  # Use general safety enabled flag
                max_file_size=safety_config.resource_limits.max_memory_mb * 1024 * 1024,  # Convert MB to bytes
            )
            
            self._fs_controller = FilesystemAccessController(policy, self.repo_root)
            
            logger.info("Initialized filesystem access controller with configuration-based policy")
        
        return self._fs_controller
    
    @property
    def net_controller(self) -> NetworkAccessController:
        """Get or create network access controller based on configuration."""
        if self._net_controller is None:
            safety_config = self.config_manager.config.safety
            
            # Create network policy from configuration
            policy = NetworkPolicy(
                default_deny=safety_config.network_policy.default_deny,
                allowed_domains=set(safety_config.network_policy.allowlist),
                request_timeout=safety_config.resource_limits.timeout_seconds,
                audit_enabled=safety_config.enabled,  # Use general safety enabled flag
            )
            
            self._net_controller = NetworkAccessController(policy)
            
            logger.info("Initialized network access controller with configuration-based policy")
        
        return self._net_controller
    
    @property
    def injection_guard(self) -> PromptInjectionGuard:
        """Get or create prompt injection guard based on configuration."""
        if self._injection_guard is None:
            safety_config = self.config_manager.config.safety
            
            # Get patterns file path from configuration
            patterns_file = None
            if safety_config.injection_detection.enabled and safety_config.injection_detection.patterns_file:
                patterns_file = safety_config.injection_detection.patterns_file
            
            # Create LLM judge if enabled
            llm_judge = None
            if safety_config.llm_judge.enabled:
                # TODO: Implement LLM judge integration when model system is available
                logger.info("LLM judge is enabled but not yet implemented")
            
            self._injection_guard = PromptInjectionGuard(
                patterns_file=patterns_file,
                llm_judge=llm_judge
            )
            
            # Enable/disable based on configuration
            if safety_config.injection_detection.enabled:
                self._injection_guard.enable()
            else:
                self._injection_guard.disable()
            
            logger.info("Initialized prompt injection guard with configuration-based settings")
        
        return self._injection_guard
    
    def execute_code_with_config(self, 
                                code: str,
                                language: str = "python",
                                **kwargs) -> ExecutionResult:
        """
        Execute code using configuration-based safety settings.
        
        Args:
            code: Code to execute
            language: Programming language
            **kwargs: Additional execution parameters (override config)
            
        Returns:
            ExecutionResult with status, output, and resource usage
        """
        safety_config = self.config_manager.config.safety
        
        # Build execution parameters from configuration
        execution_params = {
            'timeout_seconds': safety_config.resource_limits.timeout_seconds,
            'max_memory_mb': safety_config.resource_limits.max_memory_mb,
            'max_cpu_percent': safety_config.resource_limits.max_cpu_percent,
            'network_enabled': not safety_config.network_policy.default_deny,
        }
        
        # Override with provided parameters
        execution_params.update(kwargs)
        
        # Log execution attempt
        logger.info(f"Executing {language} code with safety controls enabled")
        logger.debug(f"Execution parameters: {execution_params}")
        
        # Execute code
        result = self.sandbox.execute_code(
            code=code,
            language=language,
            **execution_params
        )
        
        # Log execution result
        logger.info(f"Code execution completed: {result.status}")
        if result.status != "success":
            logger.warning(f"Execution failed: {result.error_message}")
        
        return result
    
    def is_safety_enabled(self) -> bool:
        """Check if safety controls are enabled."""
        return self.config_manager.config.safety.enabled
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get current resource limits from configuration."""
        limits = self.config_manager.config.safety.resource_limits
        return {
            'max_memory_mb': limits.max_memory_mb,
            'max_cpu_percent': limits.max_cpu_percent,
            'timeout_seconds': limits.timeout_seconds
        }
    
    def get_network_policy(self) -> Dict[str, Any]:
        """Get current network policy from configuration."""
        policy = self.config_manager.config.safety.network_policy
        return {
            'default_deny': policy.default_deny,
            'allowlist': policy.allowlist
        }
    
    def get_filesystem_policy(self) -> Dict[str, Any]:
        """Get current filesystem policy from configuration."""
        policy = self.config_manager.config.safety.filesystem_policy
        return {
            'restrict_to_repo': policy.restrict_to_repo,
            'temp_dir_access': policy.temp_dir_access,
            'system_access': policy.system_access
        }
    
    def validate_safety_configuration(self) -> list[str]:
        """
        Validate safety configuration and return warnings.
        
        Returns:
            List of validation warnings
        """
        warnings = []
        safety_config = self.config_manager.config.safety
        
        # Check if safety is enabled
        if not safety_config.enabled:
            warnings.append("Safety controls are disabled")
        
        # Check resource limits
        if safety_config.resource_limits.max_memory_mb < 128:
            warnings.append("Memory limit is very low (< 128MB)")
        
        if safety_config.resource_limits.max_cpu_percent > 90:
            warnings.append("CPU limit is very high (> 90%)")
        
        if safety_config.resource_limits.timeout_seconds > 3600:
            warnings.append("Timeout is very long (> 1 hour)")
        
        # Check sandbox availability
        if safety_config.sandbox_type == "docker" and not self.sandbox.is_docker_available():
            warnings.append("Docker sandbox requested but Docker is not available")
        
        # Check network policy
        if not safety_config.network_policy.default_deny:
            warnings.append("Network access is not restricted by default")
        
        # Check filesystem policy
        if not safety_config.filesystem_policy.restrict_to_repo:
            warnings.append("Filesystem access is not restricted to repository")
        
        if safety_config.filesystem_policy.system_access:
            warnings.append("System directory access is enabled (security risk)")
        
        # Check network policy
        if not safety_config.network_policy.default_deny:
            warnings.append("Network access is not restricted by default")
        
        if not safety_config.network_policy.allowlist:
            warnings.append("No network allowlist configured - all domains may be accessible")
        
        # Check injection detection
        if safety_config.injection_detection.enabled:
            patterns_file = Path(safety_config.injection_detection.patterns_file)
            if not patterns_file.exists():
                warnings.append(f"Injection patterns file not found: {patterns_file}")
        
        # Check LLM judge configuration
        if safety_config.llm_judge.enabled:
            warnings.append("LLM judge is enabled but not yet fully implemented")
        
        return warnings
    
    def safe_file_operation(self, operation: str, *args, **kwargs):
        """
        Perform safe file operation using configuration-based filesystem controls.
        
        Args:
            operation: Operation name ('read', 'write', 'copy', 'delete', etc.)
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            PermissionError: If access is denied
            ValueError: If operation is not supported
        """
        if not self.is_safety_enabled():
            logger.warning("Safety controls are disabled - performing operation without restrictions")
        
        fs_controller = self.fs_controller
        
        # Map operation names to controller methods
        operation_map = {
            'read': fs_controller.safe_read,
            'write': fs_controller.safe_write,
            'copy': fs_controller.safe_copy,
            'move': fs_controller.safe_move,
            'delete': fs_controller.safe_delete,
            'create_temp_dir': fs_controller.create_temp_dir,
            'http_get': self.net_controller.safe_get,
            'http_post': self.net_controller.safe_post,
            'http_put': self.net_controller.safe_put,
            'http_delete': self.net_controller.safe_delete,
            'dns_lookup': self.net_controller.safe_dns_lookup,
            'filter_input': self.injection_guard.filter_input,
            'filter_output': self.injection_guard.filter_output,
            'detect_injection': self.injection_guard.detect_injection,
        }
        
        if operation not in operation_map:
            raise ValueError(f"Unsupported file operation: {operation}")
        
        logger.info(f"Performing safe file operation: {operation}")
        
        try:
            result = operation_map[operation](*args, **kwargs)
            logger.debug(f"File operation {operation} completed successfully")
            return result
        except Exception as e:
            logger.error(f"File operation {operation} failed: {e}")
            raise
    
    def get_filesystem_statistics(self) -> Dict[str, Any]:
        """Get filesystem access statistics."""
        return self.fs_controller.get_statistics()
    
    def export_filesystem_audit_log(self, output_path: str) -> None:
        """Export filesystem audit log to file."""
        self.fs_controller.export_audit_log(output_path)
        logger.info(f"Filesystem audit log exported to {output_path}")
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """Get network access statistics."""
        return self.net_controller.get_statistics()
    
    def export_network_audit_log(self, output_path: str) -> None:
        """Export network audit log to file."""
        self.net_controller.export_audit_log(output_path)
        logger.info(f"Network audit log exported to {output_path}")
    
    def get_injection_statistics(self) -> Dict[str, Any]:
        """Get injection detection statistics."""
        return self.injection_guard.get_statistics()
    
    def export_injection_audit_log(self, output_path: str) -> None:
        """Export injection detection audit log to file."""
        self.injection_guard.export_audit_log(output_path)
        logger.info(f"Injection audit log exported to {output_path}")
    
    def filter_user_input(self, text: str, user_id: Optional[str] = None, 
                         session_id: Optional[str] = None) -> Tuple[str, Any]:
        """
        Filter user input for injection attempts using configuration-based controls.
        
        Args:
            text: Input text to filter
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            Tuple of (filtered_text, detection_result)
            
        Raises:
            ValueError: If input is blocked due to injection detection
        """
        if not self.is_safety_enabled():
            logger.warning("Safety controls are disabled - input not filtered")
            return text, None
        
        return self.injection_guard.filter_input(text, user_id, session_id)
    
    def filter_system_output(self, text: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, bool]:
        """
        Filter system output to prevent information leakage using configuration-based controls.
        
        Args:
            text: Output text to filter
            context: Optional context information
            
        Returns:
            Tuple of (filtered_text, was_filtered)
        """
        if not self.is_safety_enabled():
            logger.warning("Safety controls are disabled - output not filtered")
            return text, False
        
        return self.injection_guard.filter_output(text, context)
    
    def cleanup_resources(self) -> None:
        """Clean up safety manager resources."""
        if self._fs_controller:
            self._fs_controller.cleanup_temp_dirs()
            logger.info("Cleaned up filesystem resources")
        
        if self._net_controller:
            self._net_controller.clear_rate_limits()
            logger.info("Cleared network rate limits")

# Global safety manager instance
_safety_manager: Optional[SafetyManager] = None

def get_safety_manager(config_manager: Optional[ConfigurationManager] = None) -> SafetyManager:
    """Get the global safety manager instance."""
    global _safety_manager
    if _safety_manager is None:
        _safety_manager = SafetyManager(config_manager)
    return _safety_manager

def execute_code_safely_with_config(code: str, **kwargs) -> ExecutionResult:
    """
    Convenience function for safe code execution with configuration.
    
    Args:
        code: Code to execute
        **kwargs: Additional execution parameters
        
    Returns:
        ExecutionResult with status, output, and resource usage
    """
    safety_manager = get_safety_manager()
    return safety_manager.execute_code_with_config(code, **kwargs)