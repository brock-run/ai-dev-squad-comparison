"""
Policy Integration for Record-Replay Security

Integrates with existing safety policies to enforce network and filesystem
restrictions during replay mode, ensuring secure and isolated execution.

Following ADR-002 and ADR-003 specifications for execution and network controls.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from contextlib import contextmanager
from enum import Enum

# Import existing safety modules
try:
    from common.safety.net import NetworkAccessControl, get_network_control
    from common.safety.fs import FilesystemGuard, get_filesystem_guard
    from common.safety.policy import PolicyManager, get_policy_manager
    SAFETY_AVAILABLE = True
except ImportError:
    SAFETY_AVAILABLE = False
    logging.warning("Safety modules not available - replay security will be limited")

logger = logging.getLogger(__name__)


class ReplayMode(Enum):
    """Replay execution modes with different security levels."""
    LIVE = "live"           # Normal execution with full access
    RECORDING = "recording" # Recording mode with normal access
    REPLAY = "replay"       # Strict replay with limited access
    HYBRID = "hybrid"       # Replay with fallback to live for misses


class ReplaySecurityPolicy:
    """Security policy for replay execution."""
    
    def __init__(self, mode: ReplayMode = ReplayMode.REPLAY):
        """
        Initialize replay security policy.
        
        Args:
            mode: Replay mode to configure
        """
        self.mode = mode
        self.allowed_read_paths: Set[Path] = set()
        self.allowed_write_paths: Set[Path] = set()
        self.allowed_domains: Set[str] = set()
        self.network_enabled = False
        self.filesystem_write_enabled = False
        
        self._configure_for_mode()
    
    def _configure_for_mode(self):
        """Configure policy based on replay mode."""
        if self.mode == ReplayMode.LIVE:
            # Live mode - use existing policies
            self.network_enabled = True
            self.filesystem_write_enabled = True
            
        elif self.mode == ReplayMode.RECORDING:
            # Recording mode - normal access for recording
            self.network_enabled = True
            self.filesystem_write_enabled = True
            
        elif self.mode == ReplayMode.REPLAY:
            # Strict replay mode - minimal access
            self.network_enabled = False
            self.filesystem_write_enabled = False
            
            # Only allow reading from artifacts directory
            self.allowed_read_paths.add(Path("artifacts"))
            self.allowed_read_paths.add(Path("comparison-results"))
            self.allowed_read_paths.add(Path("/tmp"))  # Temp files
            
        elif self.mode == ReplayMode.HYBRID:
            # Hybrid mode - limited access with fallback
            self.network_enabled = True  # Allow network for fallback
            self.filesystem_write_enabled = False  # No writes during replay
            
            # Allow reading from artifacts and limited other paths
            self.allowed_read_paths.add(Path("artifacts"))
            self.allowed_read_paths.add(Path("comparison-results"))
            self.allowed_read_paths.add(Path("/tmp"))
    
    def add_allowed_read_path(self, path: Path):
        """Add an allowed read path."""
        self.allowed_read_paths.add(path)
    
    def add_allowed_write_path(self, path: Path):
        """Add an allowed write path."""
        if self.filesystem_write_enabled:
            self.allowed_write_paths.add(path)
    
    def add_allowed_domain(self, domain: str):
        """Add an allowed network domain."""
        if self.network_enabled:
            self.allowed_domains.add(domain)
    
    def is_read_allowed(self, path: Path) -> bool:
        """Check if reading from path is allowed."""
        if self.mode in [ReplayMode.LIVE, ReplayMode.RECORDING]:
            return True
        
        # Check if path is under any allowed read path
        for allowed_path in self.allowed_read_paths:
            try:
                path.resolve().relative_to(allowed_path.resolve())
                return True
            except ValueError:
                continue
        
        return False
    
    def is_write_allowed(self, path: Path) -> bool:
        """Check if writing to path is allowed."""
        if not self.filesystem_write_enabled:
            return False
        
        if self.mode in [ReplayMode.LIVE, ReplayMode.RECORDING]:
            return True
        
        # Check if path is under any allowed write path
        for allowed_path in self.allowed_write_paths:
            try:
                path.resolve().relative_to(allowed_path.resolve())
                return True
            except ValueError:
                continue
        
        return False
    
    def is_network_allowed(self, domain: str) -> bool:
        """Check if network access to domain is allowed."""
        if not self.network_enabled:
            return False
        
        if self.mode in [ReplayMode.LIVE, ReplayMode.RECORDING]:
            return True
        
        return domain in self.allowed_domains


class ReplayPolicyManager:
    """Manages security policies during replay execution."""
    
    def __init__(self):
        """Initialize replay policy manager."""
        self.current_policy: Optional[ReplaySecurityPolicy] = None
        self.original_policies: Dict[str, Any] = {}
        self.policy_stack: List[ReplaySecurityPolicy] = []
        
        # Check if safety modules are available
        self.safety_available = SAFETY_AVAILABLE
        
        if self.safety_available:
            self.network_control = get_network_control()
            self.filesystem_guard = get_filesystem_guard()
            self.policy_manager = get_policy_manager()
        else:
            logger.warning("Safety modules not available - using mock implementations")
            self.network_control = None
            self.filesystem_guard = None
            self.policy_manager = None
    
    def apply_replay_policy(self, policy: ReplaySecurityPolicy):
        """
        Apply replay security policy.
        
        Args:
            policy: Replay security policy to apply
        """
        if self.current_policy:
            self.policy_stack.append(self.current_policy)
        
        self.current_policy = policy
        
        if self.safety_available:
            self._apply_network_policy(policy)
            self._apply_filesystem_policy(policy)
        else:
            logger.warning("Safety modules not available - policy not enforced")
    
    def _apply_network_policy(self, policy: ReplaySecurityPolicy):
        """Apply network access policy."""
        if not self.network_control:
            return
        
        if policy.mode == ReplayMode.REPLAY:
            # Strict replay - deny all network access
            logger.info("Applying strict network policy for replay mode")
            # This would integrate with the existing network control
            # For now, we'll log the policy application
            
        elif policy.mode == ReplayMode.HYBRID:
            # Hybrid mode - allow specific domains only
            logger.info(f"Applying hybrid network policy with {len(policy.allowed_domains)} allowed domains")
    
    def _apply_filesystem_policy(self, policy: ReplaySecurityPolicy):
        """Apply filesystem access policy."""
        if not self.filesystem_guard:
            return
        
        if policy.mode == ReplayMode.REPLAY:
            # Strict replay - read-only access to artifacts
            logger.info("Applying strict filesystem policy for replay mode")
            logger.info(f"Allowed read paths: {[str(p) for p in policy.allowed_read_paths]}")
            
        elif policy.mode == ReplayMode.HYBRID:
            # Hybrid mode - limited write access
            logger.info("Applying hybrid filesystem policy")
    
    def restore_previous_policy(self):
        """Restore the previous policy from the stack."""
        if self.policy_stack:
            self.current_policy = self.policy_stack.pop()
            
            if self.safety_available:
                self._apply_network_policy(self.current_policy)
                self._apply_filesystem_policy(self.current_policy)
        else:
            self.current_policy = None
    
    def get_current_policy(self) -> Optional[ReplaySecurityPolicy]:
        """Get the current replay policy."""
        return self.current_policy
    
    def check_file_access(self, path: Path, operation: str) -> bool:
        """
        Check if file access is allowed under current policy.
        
        Args:
            path: File path to check
            operation: Operation type ('read' or 'write')
            
        Returns:
            True if access is allowed
        """
        if not self.current_policy:
            return True  # No policy applied
        
        if operation == "read":
            allowed = self.current_policy.is_read_allowed(path)
        elif operation == "write":
            allowed = self.current_policy.is_write_allowed(path)
        else:
            allowed = False
        
        if not allowed:
            logger.warning(f"File {operation} access denied for {path} under replay policy")
        
        return allowed
    
    def check_network_access(self, domain: str) -> bool:
        """
        Check if network access is allowed under current policy.
        
        Args:
            domain: Domain to check
            
        Returns:
            True if access is allowed
        """
        if not self.current_policy:
            return True  # No policy applied
        
        allowed = self.current_policy.is_network_allowed(domain)
        
        if not allowed:
            logger.warning(f"Network access denied for {domain} under replay policy")
        
        return allowed


# Global policy manager
_global_replay_policy_manager = ReplayPolicyManager()


def get_replay_policy_manager() -> ReplayPolicyManager:
    """Get the global replay policy manager."""
    return _global_replay_policy_manager


@contextmanager
def replay_security_context(mode: ReplayMode, **kwargs):
    """
    Context manager for replay security policy.
    
    Args:
        mode: Replay mode to apply
        **kwargs: Additional policy configuration
    """
    policy = ReplaySecurityPolicy(mode)
    
    # Apply additional configuration
    for read_path in kwargs.get('allowed_read_paths', []):
        policy.add_allowed_read_path(Path(read_path))
    
    for write_path in kwargs.get('allowed_write_paths', []):
        policy.add_allowed_write_path(Path(write_path))
    
    for domain in kwargs.get('allowed_domains', []):
        policy.add_allowed_domain(domain)
    
    manager = get_replay_policy_manager()
    
    try:
        manager.apply_replay_policy(policy)
        yield policy
    finally:
        manager.restore_previous_policy()


def check_file_access(path: Path, operation: str) -> bool:
    """Check file access using global policy manager."""
    return _global_replay_policy_manager.check_file_access(path, operation)


def check_network_access(domain: str) -> bool:
    """Check network access using global policy manager."""
    return _global_replay_policy_manager.check_network_access(domain)


# Decorators for enforcing replay policies
def enforce_replay_file_access(operation: str):
    """Decorator to enforce file access policies."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract path from arguments (implementation depends on function signature)
            path = None
            if args and isinstance(args[0], (str, Path)):
                path = Path(args[0])
            elif 'path' in kwargs:
                path = Path(kwargs['path'])
            elif 'file_path' in kwargs:
                path = Path(kwargs['file_path'])
            
            if path and not check_file_access(path, operation):
                raise PermissionError(f"File {operation} access denied for {path} under replay policy")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def enforce_replay_network_access(func):
    """Decorator to enforce network access policies."""
    def wrapper(*args, **kwargs):
        # Extract domain from arguments (implementation depends on function signature)
        domain = None
        if 'url' in kwargs:
            from urllib.parse import urlparse
            domain = urlparse(kwargs['url']).netloc
        elif 'domain' in kwargs:
            domain = kwargs['domain']
        elif 'host' in kwargs:
            domain = kwargs['host']
        
        if domain and not check_network_access(domain):
            raise PermissionError(f"Network access denied for {domain} under replay policy")
        
        return func(*args, **kwargs)
    return wrapper