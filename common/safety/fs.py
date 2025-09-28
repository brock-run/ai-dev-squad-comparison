"""
Filesystem Access Controls for AI Dev Squad Comparison
This module provides secure filesystem operations with path validation,
access controls, and comprehensive audit logging.
"""
import os
import sys
import shutil
import tempfile
import hashlib
import json
import time
from pathlib import Path, PurePath
from typing import Dict, Any, List, Optional, Union, Set, Tuple, IO
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class AccessType(str, Enum):
    """File access type enumeration."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    CREATE = "create"
    MODIFY = "modify"

class AccessResult(str, Enum):
    """Access control result enumeration."""
    ALLOWED = "allowed"
    DENIED = "denied"
    RESTRICTED = "restricted"

@dataclass
class FileOperation:
    """Record of a file operation for audit logging."""
    timestamp: datetime
    operation: str
    path: str
    access_type: AccessType
    result: AccessResult
    user_id: Optional[str] = None
    process_id: Optional[int] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FilesystemPolicy:
    """Filesystem access policy configuration."""
    # Base paths that are allowed for access
    allowed_paths: List[str] = field(default_factory=list)
    
    # Paths that are explicitly denied (takes precedence over allowed)
    denied_paths: List[str] = field(default_factory=list)
    
    # Whether to restrict access to repository root only
    restrict_to_repo: bool = True
    
    # Whether to allow temporary directory access
    temp_dir_access: bool = True
    
    # Whether to allow system directory access
    system_access: bool = False
    
    # Maximum file size for operations (bytes)
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Maximum number of files that can be created
    max_files_created: int = 1000
    
    # File extensions that are allowed
    allowed_extensions: Set[str] = field(default_factory=lambda: {
        '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.txt', '.md', 
        '.csv', '.xml', '.html', '.css', '.sh', '.bat', '.sql'
    })
    
    # File extensions that are denied
    denied_extensions: Set[str] = field(default_factory=lambda: {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.deb', '.rpm'
    })
    
    # Whether to enable audit logging
    audit_enabled: bool = True
    
    # Audit log file path
    audit_log_path: Optional[str] = None

class FilesystemAccessController:
    """
    Filesystem access controller with path validation and audit logging.
    """
    
    def __init__(self, policy: Optional[FilesystemPolicy] = None, repo_root: Optional[str] = None):
        self.policy = policy or FilesystemPolicy()
        self.repo_root = Path(repo_root or os.getcwd()).resolve()
        self.temp_dirs: Set[Path] = set()
        self.created_files: Set[Path] = set()
        self.audit_log: List[FileOperation] = []
        self._lock = threading.Lock()
        
        # Initialize allowed paths
        self._initialize_allowed_paths()
        
        logger.info(f"Filesystem access controller initialized with repo root: {self.repo_root}")
    
    def _initialize_allowed_paths(self):
        """Initialize default allowed paths based on policy."""
        allowed_paths = []
        
        # Add repository root if restriction is enabled
        if self.policy.restrict_to_repo:
            allowed_paths.append(str(self.repo_root))
        
        # Add system temp directory if allowed
        if self.policy.temp_dir_access:
            allowed_paths.append(tempfile.gettempdir())
        
        # Add system paths if allowed
        if self.policy.system_access:
            if sys.platform.startswith('win'):
                allowed_paths.extend(['C:\\Windows\\System32', 'C:\\Program Files'])
            else:
                allowed_paths.extend(['/usr', '/bin', '/lib', '/etc'])
        
        # Add explicitly configured paths
        allowed_paths.extend(self.policy.allowed_paths)
        
        # Resolve and normalize all paths
        self.policy.allowed_paths = [str(Path(p).resolve()) for p in allowed_paths]
        self.policy.denied_paths = [str(Path(p).resolve()) for p in self.policy.denied_paths]
    
    def validate_path(self, path: Union[str, Path], access_type: AccessType) -> Tuple[AccessResult, Optional[str]]:
        """
        Validate if a path is allowed for the specified access type.
        
        Args:
            path: Path to validate
            access_type: Type of access requested
            
        Returns:
            Tuple of (AccessResult, error_message)
        """
        try:
            # Normalize path
            normalized_path = Path(path).resolve()
            path_str = str(normalized_path)
            
            # Check for path traversal attempts
            if self._is_path_traversal(path_str):
                return AccessResult.DENIED, "Path traversal attempt detected"
            
            # Check denied paths first (takes precedence)
            for denied_path in self.policy.denied_paths:
                if self._is_path_under(path_str, denied_path):
                    return AccessResult.DENIED, f"Path is in denied location: {denied_path}"
            
            # Check allowed paths
            path_allowed = False
            for allowed_path in self.policy.allowed_paths:
                if self._is_path_under(path_str, allowed_path):
                    path_allowed = True
                    break
            
            if not path_allowed:
                return AccessResult.DENIED, "Path is not in allowed locations"
            
            # Check file extension
            extension = normalized_path.suffix.lower()
            if extension in self.policy.denied_extensions:
                return AccessResult.DENIED, f"File extension not allowed: {extension}"
            
            if self.policy.allowed_extensions and extension not in self.policy.allowed_extensions:
                return AccessResult.RESTRICTED, f"File extension not in allowlist: {extension}"
            
            # Check file size for write operations
            if access_type in [AccessType.WRITE, AccessType.CREATE, AccessType.MODIFY]:
                if normalized_path.exists():
                    file_size = normalized_path.stat().st_size
                    if file_size > self.policy.max_file_size:
                        return AccessResult.DENIED, f"File size exceeds limit: {file_size} > {self.policy.max_file_size}"
            
            # Check maximum files created limit
            if access_type == AccessType.CREATE:
                if len(self.created_files) >= self.policy.max_files_created:
                    return AccessResult.DENIED, f"Maximum files created limit reached: {self.policy.max_files_created}"
            
            return AccessResult.ALLOWED, None
            
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return AccessResult.DENIED, f"Path validation error: {e}"
    
    def _is_path_traversal(self, path: str) -> bool:
        """Check if path contains traversal attempts."""
        dangerous_patterns = ['../', '..\\', '/../', '\\..\\']
        return any(pattern in path for pattern in dangerous_patterns)
    
    def _is_path_under(self, path: str, parent: str) -> bool:
        """Check if path is under parent directory."""
        try:
            path_obj = Path(path).resolve()
            parent_obj = Path(parent).resolve()
            return str(path_obj).startswith(str(parent_obj))
        except Exception:
            return False
    
    def _log_operation(self, operation: str, path: str, access_type: AccessType, 
                      result: AccessResult, **kwargs):
        """Log file operation for audit trail."""
        if not self.policy.audit_enabled:
            return
        
        with self._lock:
            file_op = FileOperation(
                timestamp=datetime.utcnow(),
                operation=operation,
                path=path,
                access_type=access_type,
                result=result,
                process_id=os.getpid(),
                **kwargs
            )
            
            self.audit_log.append(file_op)
            
            # Write to audit log file if configured
            if self.policy.audit_log_path:
                self._write_audit_log(file_op)
    
    def _write_audit_log(self, file_op: FileOperation):
        """Write audit log entry to file."""
        try:
            log_entry = {
                'timestamp': file_op.timestamp.isoformat(),
                'operation': file_op.operation,
                'path': file_op.path,
                'access_type': file_op.access_type.value,
                'result': file_op.result.value,
                'process_id': file_op.process_id,
                'size_bytes': file_op.size_bytes,
                'checksum': file_op.checksum,
                'error_message': file_op.error_message,
                'metadata': file_op.metadata
            }
            
            with open(self.policy.audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def _calculate_checksum(self, file_path: Path) -> Optional[str]:
        """Calculate SHA-256 checksum of file."""
        try:
            if not file_path.exists() or not file_path.is_file():
                return None
            
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return None
    
    @contextmanager
    def safe_open(self, path: Union[str, Path], mode: str = 'r', **kwargs):
        """
        Safe file opening with access control validation.
        
        Args:
            path: File path to open
            mode: File open mode
            **kwargs: Additional arguments for open()
            
        Yields:
            File object if access is allowed
            
        Raises:
            PermissionError: If access is denied
            FileNotFoundError: If file doesn't exist and creation not allowed
        """
        path_obj = Path(path)
        
        # Determine access type from mode
        if 'w' in mode or 'a' in mode:
            access_type = AccessType.CREATE if not path_obj.exists() else AccessType.WRITE
        elif 'x' in mode:
            access_type = AccessType.CREATE
        else:
            access_type = AccessType.READ
        
        # Validate access
        result, error_msg = self.validate_path(path, access_type)
        
        if result == AccessResult.DENIED:
            self._log_operation('open', str(path), access_type, result, error_message=error_msg)
            raise PermissionError(f"Access denied: {error_msg}")
        
        # Calculate initial checksum for existing files
        initial_checksum = self._calculate_checksum(path_obj) if path_obj.exists() else None
        
        try:
            # Open file
            file_obj = open(path, mode, **kwargs)
            
            # Track created files
            if access_type == AccessType.CREATE:
                self.created_files.add(path_obj.resolve())
            
            self._log_operation('open', str(path), access_type, AccessResult.ALLOWED)
            
            yield file_obj
            
        except Exception as e:
            self._log_operation('open', str(path), access_type, AccessResult.DENIED, error_message=str(e))
            raise
        
        finally:
            if 'file_obj' in locals():
                file_obj.close()
                
                # Log file changes
                if path_obj.exists():
                    final_checksum = self._calculate_checksum(path_obj)
                    file_size = path_obj.stat().st_size
                    
                    if initial_checksum != final_checksum:
                        self._log_operation(
                            'modify', str(path), AccessType.MODIFY, AccessResult.ALLOWED,
                            size_bytes=file_size, checksum=final_checksum
                        )
    
    def safe_read(self, path: Union[str, Path], binary: bool = False) -> Union[str, bytes]:
        """
        Safely read file contents with access control.
        
        Args:
            path: File path to read
            binary: Whether to read in binary mode
            
        Returns:
            File contents as string or bytes
            
        Raises:
            PermissionError: If access is denied
            FileNotFoundError: If file doesn't exist
        """
        mode = 'rb' if binary else 'r'
        encoding = None if binary else 'utf-8'
        
        with self.safe_open(path, mode, encoding=encoding) as f:
            return f.read()
    
    def safe_write(self, path: Union[str, Path], content: Union[str, bytes], 
                   binary: bool = False, append: bool = False) -> int:
        """
        Safely write content to file with access control.
        
        Args:
            path: File path to write
            content: Content to write
            binary: Whether to write in binary mode
            append: Whether to append to existing file
            
        Returns:
            Number of bytes written
            
        Raises:
            PermissionError: If access is denied
        """
        if binary:
            mode = 'ab' if append else 'wb'
        else:
            mode = 'a' if append else 'w'
            
        encoding = None if binary else 'utf-8'
        
        with self.safe_open(path, mode, encoding=encoding) as f:
            if binary:
                return f.write(content)
            else:
                return f.write(content)
    
    def safe_copy(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """
        Safely copy file with access control validation.
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Raises:
            PermissionError: If access is denied
        """
        src_path = Path(src)
        dst_path = Path(dst)
        
        # Validate source read access
        result, error_msg = self.validate_path(src, AccessType.READ)
        if result == AccessResult.DENIED:
            self._log_operation('copy_read', str(src), AccessType.READ, result, error_message=error_msg)
            raise PermissionError(f"Source read access denied: {error_msg}")
        
        # Validate destination write access
        access_type = AccessType.CREATE if not dst_path.exists() else AccessType.WRITE
        result, error_msg = self.validate_path(dst, access_type)
        if result == AccessResult.DENIED:
            self._log_operation('copy_write', str(dst), access_type, result, error_message=error_msg)
            raise PermissionError(f"Destination write access denied: {error_msg}")
        
        try:
            # Perform copy
            shutil.copy2(src, dst)
            
            # Track created files
            if access_type == AccessType.CREATE:
                self.created_files.add(dst_path.resolve())
            
            # Log successful operation
            file_size = dst_path.stat().st_size
            checksum = self._calculate_checksum(dst_path)
            
            self._log_operation(
                'copy', f"{src} -> {dst}", access_type, AccessResult.ALLOWED,
                size_bytes=file_size, checksum=checksum
            )
            
        except Exception as e:
            self._log_operation('copy', f"{src} -> {dst}", access_type, AccessResult.DENIED, error_message=str(e))
            raise
    
    def safe_move(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """
        Safely move file with access control validation.
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Raises:
            PermissionError: If access is denied
        """
        src_path = Path(src)
        dst_path = Path(dst)
        
        # Validate source delete access
        result, error_msg = self.validate_path(src, AccessType.DELETE)
        if result == AccessResult.DENIED:
            self._log_operation('move_delete', str(src), AccessType.DELETE, result, error_message=error_msg)
            raise PermissionError(f"Source delete access denied: {error_msg}")
        
        # Validate destination write access
        access_type = AccessType.CREATE if not dst_path.exists() else AccessType.WRITE
        result, error_msg = self.validate_path(dst, access_type)
        if result == AccessResult.DENIED:
            self._log_operation('move_write', str(dst), access_type, result, error_message=error_msg)
            raise PermissionError(f"Destination write access denied: {error_msg}")
        
        try:
            # Perform move
            shutil.move(src, dst)
            
            # Update tracking
            if src_path.resolve() in self.created_files:
                self.created_files.remove(src_path.resolve())
            if access_type == AccessType.CREATE:
                self.created_files.add(dst_path.resolve())
            
            # Log successful operation
            self._log_operation('move', f"{src} -> {dst}", AccessType.MODIFY, AccessResult.ALLOWED)
            
        except Exception as e:
            self._log_operation('move', f"{src} -> {dst}", AccessType.MODIFY, AccessResult.DENIED, error_message=str(e))
            raise
    
    def safe_delete(self, path: Union[str, Path]) -> None:
        """
        Safely delete file with access control validation.
        
        Args:
            path: File path to delete
            
        Raises:
            PermissionError: If access is denied
        """
        path_obj = Path(path)
        
        # Validate delete access
        result, error_msg = self.validate_path(path, AccessType.DELETE)
        if result == AccessResult.DENIED:
            self._log_operation('delete', str(path), AccessType.DELETE, result, error_message=error_msg)
            raise PermissionError(f"Delete access denied: {error_msg}")
        
        try:
            # Calculate checksum before deletion
            checksum = self._calculate_checksum(path_obj)
            file_size = path_obj.stat().st_size if path_obj.exists() else 0
            
            # Perform deletion
            if path_obj.is_file():
                path_obj.unlink()
            elif path_obj.is_dir():
                shutil.rmtree(path)
            
            # Update tracking
            if path_obj.resolve() in self.created_files:
                self.created_files.remove(path_obj.resolve())
            
            # Log successful operation
            self._log_operation(
                'delete', str(path), AccessType.DELETE, AccessResult.ALLOWED,
                size_bytes=file_size, checksum=checksum
            )
            
        except Exception as e:
            self._log_operation('delete', str(path), AccessType.DELETE, AccessResult.DENIED, error_message=str(e))
            raise
    
    def create_temp_dir(self, prefix: str = "ai_dev_squad_", suffix: str = "") -> Path:
        """
        Create a temporary directory with proper tracking.
        
        Args:
            prefix: Directory name prefix
            suffix: Directory name suffix
            
        Returns:
            Path to created temporary directory
            
        Raises:
            PermissionError: If temp directory access is not allowed
        """
        if not self.policy.temp_dir_access:
            raise PermissionError("Temporary directory access is not allowed")
        
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix, suffix=suffix))
            self.temp_dirs.add(temp_dir)
            
            self._log_operation('create_temp_dir', str(temp_dir), AccessType.CREATE, AccessResult.ALLOWED)
            
            logger.info(f"Created temporary directory: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            self._log_operation('create_temp_dir', 'unknown', AccessType.CREATE, AccessResult.DENIED, error_message=str(e))
            raise
    
    def cleanup_temp_dirs(self) -> None:
        """Clean up all created temporary directories."""
        for temp_dir in list(self.temp_dirs):
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                
                self.temp_dirs.remove(temp_dir)
                self._log_operation('cleanup_temp_dir', str(temp_dir), AccessType.DELETE, AccessResult.ALLOWED)
                
            except Exception as e:
                logger.error(f"Failed to cleanup temporary directory {temp_dir}: {e}")
                self._log_operation('cleanup_temp_dir', str(temp_dir), AccessType.DELETE, AccessResult.DENIED, error_message=str(e))
    
    def get_audit_log(self, limit: Optional[int] = None) -> List[FileOperation]:
        """
        Get audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of file operations
        """
        with self._lock:
            if limit:
                return self.audit_log[-limit:]
            return self.audit_log.copy()
    
    def export_audit_log(self, output_path: Union[str, Path]) -> None:
        """
        Export audit log to JSON file.
        
        Args:
            output_path: Path to output file
        """
        audit_data = []
        
        for file_op in self.audit_log:
            audit_data.append({
                'timestamp': file_op.timestamp.isoformat(),
                'operation': file_op.operation,
                'path': file_op.path,
                'access_type': file_op.access_type.value,
                'result': file_op.result.value,
                'process_id': file_op.process_id,
                'size_bytes': file_op.size_bytes,
                'checksum': file_op.checksum,
                'error_message': file_op.error_message,
                'metadata': file_op.metadata
            })
        
        with open(output_path, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"Exported audit log to {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get filesystem access statistics.
        
        Returns:
            Dictionary with access statistics
        """
        stats = {
            'total_operations': len(self.audit_log),
            'allowed_operations': sum(1 for op in self.audit_log if op.result == AccessResult.ALLOWED),
            'denied_operations': sum(1 for op in self.audit_log if op.result == AccessResult.DENIED),
            'restricted_operations': sum(1 for op in self.audit_log if op.result == AccessResult.RESTRICTED),
            'files_created': len(self.created_files),
            'temp_dirs_active': len(self.temp_dirs),
            'operations_by_type': {},
            'operations_by_access_type': {}
        }
        
        # Count operations by type
        for op in self.audit_log:
            stats['operations_by_type'][op.operation] = stats['operations_by_type'].get(op.operation, 0) + 1
            stats['operations_by_access_type'][op.access_type.value] = stats['operations_by_access_type'].get(op.access_type.value, 0) + 1
        
        return stats

# Global filesystem access controller
_fs_controller: Optional[FilesystemAccessController] = None

def get_fs_controller(policy: Optional[FilesystemPolicy] = None, 
                     repo_root: Optional[str] = None) -> FilesystemAccessController:
    """Get the global filesystem access controller."""
    global _fs_controller
    if _fs_controller is None:
        _fs_controller = FilesystemAccessController(policy, repo_root)
    return _fs_controller

def safe_open(path: Union[str, Path], mode: str = 'r', **kwargs):
    """Convenience function for safe file opening."""
    controller = get_fs_controller()
    return controller.safe_open(path, mode, **kwargs)

def safe_read(path: Union[str, Path], binary: bool = False) -> Union[str, bytes]:
    """Convenience function for safe file reading."""
    controller = get_fs_controller()
    return controller.safe_read(path, binary)

def safe_write(path: Union[str, Path], content: Union[str, bytes], 
               binary: bool = False, append: bool = False) -> int:
    """Convenience function for safe file writing."""
    controller = get_fs_controller()
    return controller.safe_write(path, content, binary, append)

def safe_copy(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Convenience function for safe file copying."""
    controller = get_fs_controller()
    return controller.safe_copy(src, dst)

def safe_delete(path: Union[str, Path]) -> None:
    """Convenience function for safe file deletion."""
    controller = get_fs_controller()
    return controller.safe_delete(path)