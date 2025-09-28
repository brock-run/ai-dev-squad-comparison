"""
Unit tests for Filesystem Access Controls.
These tests validate path validation, access controls, audit logging,
and safe file operations across different scenarios.
"""
import pytest
import tempfile
import os
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from common.safety.fs import (
    FilesystemAccessController, FilesystemPolicy, AccessType, AccessResult,
    FileOperation, get_fs_controller, safe_open, safe_read, safe_write,
    safe_copy, safe_delete
)

class TestFilesystemPolicy:
    """Test cases for FilesystemPolicy."""
    
    def test_filesystem_policy_defaults(self):
        """Test default filesystem policy values."""
        policy = FilesystemPolicy()
        
        assert policy.restrict_to_repo is True
        assert policy.temp_dir_access is True
        assert policy.system_access is False
        assert policy.max_file_size == 100 * 1024 * 1024  # 100MB
        assert policy.max_files_created == 1000
        assert policy.audit_enabled is True
        
        # Check default allowed extensions
        assert '.py' in policy.allowed_extensions
        assert '.js' in policy.allowed_extensions
        assert '.json' in policy.allowed_extensions
        
        # Check default denied extensions
        assert '.exe' in policy.denied_extensions
        assert '.dll' in policy.denied_extensions
    
    def test_filesystem_policy_custom(self):
        """Test custom filesystem policy configuration."""
        policy = FilesystemPolicy(
            allowed_paths=['/custom/path'],
            denied_paths=['/forbidden/path'],
            restrict_to_repo=False,
            max_file_size=50 * 1024 * 1024,  # 50MB
            allowed_extensions={'.txt', '.log'},
            denied_extensions={'.tmp'},
            audit_enabled=False
        )
        
        assert policy.allowed_paths == ['/custom/path']
        assert policy.denied_paths == ['/forbidden/path']
        assert policy.restrict_to_repo is False
        assert policy.max_file_size == 50 * 1024 * 1024
        assert policy.allowed_extensions == {'.txt', '.log'}
        assert policy.denied_extensions == {'.tmp'}
        assert policy.audit_enabled is False

class TestFileOperation:
    """Test cases for FileOperation."""
    
    def test_file_operation_creation(self):
        """Test file operation record creation."""
        timestamp = datetime.utcnow()
        operation = FileOperation(
            timestamp=timestamp,
            operation='read',
            path='/test/file.txt',
            access_type=AccessType.READ,
            result=AccessResult.ALLOWED,
            size_bytes=1024,
            checksum='abc123'
        )
        
        assert operation.timestamp == timestamp
        assert operation.operation == 'read'
        assert operation.path == '/test/file.txt'
        assert operation.access_type == AccessType.READ
        assert operation.result == AccessResult.ALLOWED
        assert operation.size_bytes == 1024
        assert operation.checksum == 'abc123'

class TestFilesystemAccessController:
    """Test cases for FilesystemAccessController."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_root = self.temp_dir / "repo"
        self.repo_root.mkdir()
        
        # Create test policy
        self.policy = FilesystemPolicy(
            restrict_to_repo=True,
            temp_dir_access=True,
            system_access=False,
            audit_enabled=True
        )
        
        self.controller = FilesystemAccessController(self.policy, str(self.repo_root))
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_controller_initialization(self):
        """Test filesystem access controller initialization."""
        assert self.controller.policy == self.policy
        assert self.controller.repo_root == self.repo_root.resolve()
        assert len(self.controller.temp_dirs) == 0
        assert len(self.controller.created_files) == 0
        assert len(self.controller.audit_log) == 0
    
    def test_path_traversal_detection(self):
        """Test path traversal attack detection."""
        # Test various path traversal patterns
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/repo/../../../etc/passwd",
            "legitimate/../../etc/passwd"
        ]
        
        for path in traversal_paths:
            assert self.controller._is_path_traversal(path) is True
        
        # Test legitimate paths
        legitimate_paths = [
            "file.txt",
            "subdir/file.txt",
            "/repo/file.txt",
            "data/config.json"
        ]
        
        for path in legitimate_paths:
            assert self.controller._is_path_traversal(path) is False
    
    def test_path_under_validation(self):
        """Test path hierarchy validation."""
        parent = "/home/user/project"
        
        # Paths under parent
        under_paths = [
            "/home/user/project/file.txt",
            "/home/user/project/subdir/file.txt",
            "/home/user/project"
        ]
        
        for path in under_paths:
            assert self.controller._is_path_under(path, parent) is True
        
        # Paths not under parent
        not_under_paths = [
            "/home/user/other/file.txt",
            "/home/other/project/file.txt",
            "/etc/passwd"
        ]
        
        for path in not_under_paths:
            assert self.controller._is_path_under(path, parent) is False
    
    def test_validate_path_allowed(self):
        """Test path validation for allowed paths."""
        # Create test file in repo
        test_file = self.repo_root / "test.py"
        test_file.write_text("print('hello')")
        
        # Test allowed access
        result, error = self.controller.validate_path(test_file, AccessType.READ)
        assert result == AccessResult.ALLOWED
        assert error is None
        
        result, error = self.controller.validate_path(test_file, AccessType.WRITE)
        assert result == AccessResult.ALLOWED
        assert error is None
    
    def test_validate_path_denied_location(self):
        """Test path validation for denied locations."""
        # Test access to system file
        system_file = "/etc/passwd"
        
        result, error = self.controller.validate_path(system_file, AccessType.READ)
        assert result == AccessResult.DENIED
        assert "not in allowed locations" in error
    
    def test_validate_path_denied_extension(self):
        """Test path validation for denied file extensions."""
        # Test denied extension
        exe_file = self.repo_root / "malware.exe"
        
        result, error = self.controller.validate_path(exe_file, AccessType.CREATE)
        assert result == AccessResult.DENIED
        assert "File extension not allowed" in error
    
    def test_validate_path_restricted_extension(self):
        """Test path validation for restricted file extensions."""
        # Create policy with limited allowed extensions
        policy = FilesystemPolicy(allowed_extensions={'.py', '.txt'})
        controller = FilesystemAccessController(policy, str(self.repo_root))
        
        # Test restricted extension
        log_file = self.repo_root / "app.log"
        
        result, error = controller.validate_path(log_file, AccessType.CREATE)
        assert result == AccessResult.RESTRICTED
        assert "not in allowlist" in error
    
    def test_validate_path_traversal_denied(self):
        """Test path validation denies traversal attempts."""
        traversal_path = self.repo_root / "../../../etc/passwd"
        
        result, error = self.controller.validate_path(traversal_path, AccessType.READ)
        assert result == AccessResult.DENIED
        assert "Path traversal attempt detected" in error
    
    def test_safe_open_read_success(self):
        """Test safe file opening for reading."""
        # Create test file
        test_file = self.repo_root / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        # Test safe opening
        with self.controller.safe_open(test_file, 'r') as f:
            content = f.read()
            assert content == test_content
        
        # Check audit log
        assert len(self.controller.audit_log) == 1
        assert self.controller.audit_log[0].operation == 'open'
        assert self.controller.audit_log[0].access_type == AccessType.READ
        assert self.controller.audit_log[0].result == AccessResult.ALLOWED
    
    def test_safe_open_write_success(self):
        """Test safe file opening for writing."""
        test_file = self.repo_root / "output.txt"
        test_content = "Output content"
        
        # Test safe writing
        with self.controller.safe_open(test_file, 'w') as f:
            f.write(test_content)
        
        # Verify file was created
        assert test_file.exists()
        assert test_file.read_text() == test_content
        
        # Check tracking
        assert test_file.resolve() in self.controller.created_files
        
        # Check audit log
        assert len(self.controller.audit_log) >= 1
        open_log = next(log for log in self.controller.audit_log if log.operation == 'open')
        assert open_log.access_type == AccessType.CREATE
        assert open_log.result == AccessResult.ALLOWED
    
    def test_safe_open_denied(self):
        """Test safe file opening denial."""
        # Try to open system file
        system_file = "/etc/passwd"
        
        with pytest.raises(PermissionError, match="Access denied"):
            with self.controller.safe_open(system_file, 'r'):
                pass
        
        # Check audit log
        assert len(self.controller.audit_log) == 1
        assert self.controller.audit_log[0].result == AccessResult.DENIED
    
    def test_safe_read_success(self):
        """Test safe file reading."""
        # Create test file
        test_file = self.repo_root / "data.txt"
        test_content = "Test data content"
        test_file.write_text(test_content)
        
        # Test safe reading
        content = self.controller.safe_read(test_file)
        assert content == test_content
        
        # Test binary reading
        binary_content = self.controller.safe_read(test_file, binary=True)
        assert binary_content == test_content.encode('utf-8')
    
    def test_safe_write_success(self):
        """Test safe file writing."""
        test_file = self.repo_root / "output.txt"
        test_content = "Written content"
        
        # Test safe writing
        bytes_written = self.controller.safe_write(test_file, test_content)
        assert bytes_written == len(test_content)
        
        # Verify content
        assert test_file.read_text() == test_content
        
        # Test append mode
        append_content = "\nAppended line"
        self.controller.safe_write(test_file, append_content, append=True)
        
        final_content = test_file.read_text()
        assert final_content == test_content + append_content
    
    def test_safe_copy_success(self):
        """Test safe file copying."""
        # Create source file
        src_file = self.repo_root / "source.txt"
        src_content = "Source content"
        src_file.write_text(src_content)
        
        # Test safe copying
        dst_file = self.repo_root / "destination.txt"
        self.controller.safe_copy(src_file, dst_file)
        
        # Verify copy
        assert dst_file.exists()
        assert dst_file.read_text() == src_content
        assert dst_file.resolve() in self.controller.created_files
        
        # Check audit log
        copy_logs = [log for log in self.controller.audit_log if log.operation == 'copy']
        assert len(copy_logs) == 1
        assert copy_logs[0].result == AccessResult.ALLOWED
    
    def test_safe_copy_denied(self):
        """Test safe file copying denial."""
        # Try to copy from system file
        src_file = "/etc/passwd"
        dst_file = self.repo_root / "copied_passwd.txt"
        
        with pytest.raises(PermissionError, match="Source read access denied"):
            self.controller.safe_copy(src_file, dst_file)
    
    def test_safe_move_success(self):
        """Test safe file moving."""
        # Create source file
        src_file = self.repo_root / "moveme.txt"
        src_content = "Move this content"
        src_file.write_text(src_content)
        
        # Add to created files tracking
        self.controller.created_files.add(src_file.resolve())
        
        # Test safe moving
        dst_file = self.repo_root / "moved.txt"
        self.controller.safe_move(src_file, dst_file)
        
        # Verify move
        assert not src_file.exists()
        assert dst_file.exists()
        assert dst_file.read_text() == src_content
        
        # Check tracking updates
        assert src_file.resolve() not in self.controller.created_files
        assert dst_file.resolve() in self.controller.created_files
    
    def test_safe_delete_success(self):
        """Test safe file deletion."""
        # Create test file
        test_file = self.repo_root / "deleteme.txt"
        test_content = "Delete this file"
        test_file.write_text(test_content)
        
        # Add to created files tracking
        self.controller.created_files.add(test_file.resolve())
        
        # Test safe deletion
        self.controller.safe_delete(test_file)
        
        # Verify deletion
        assert not test_file.exists()
        assert test_file.resolve() not in self.controller.created_files
        
        # Check audit log
        delete_logs = [log for log in self.controller.audit_log if log.operation == 'delete']
        assert len(delete_logs) == 1
        assert delete_logs[0].result == AccessResult.ALLOWED
    
    def test_create_temp_dir_success(self):
        """Test temporary directory creation."""
        # Test temp directory creation
        temp_dir = self.controller.create_temp_dir(prefix="test_", suffix="_dir")
        
        # Verify creation
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        assert temp_dir in self.controller.temp_dirs
        assert "test_" in temp_dir.name
        assert "_dir" in temp_dir.name
        
        # Check audit log
        temp_logs = [log for log in self.controller.audit_log if log.operation == 'create_temp_dir']
        assert len(temp_logs) == 1
        assert temp_logs[0].result == AccessResult.ALLOWED
    
    def test_create_temp_dir_denied(self):
        """Test temporary directory creation denial."""
        # Disable temp directory access
        self.controller.policy.temp_dir_access = False
        
        with pytest.raises(PermissionError, match="Temporary directory access is not allowed"):
            self.controller.create_temp_dir()
    
    def test_cleanup_temp_dirs(self):
        """Test temporary directory cleanup."""
        # Create multiple temp directories
        temp_dir1 = self.controller.create_temp_dir(prefix="cleanup1_")
        temp_dir2 = self.controller.create_temp_dir(prefix="cleanup2_")
        
        # Create files in temp directories
        (temp_dir1 / "file1.txt").write_text("temp file 1")
        (temp_dir2 / "file2.txt").write_text("temp file 2")
        
        # Verify directories exist
        assert temp_dir1.exists()
        assert temp_dir2.exists()
        assert len(self.controller.temp_dirs) == 2
        
        # Test cleanup
        self.controller.cleanup_temp_dirs()
        
        # Verify cleanup
        assert not temp_dir1.exists()
        assert not temp_dir2.exists()
        assert len(self.controller.temp_dirs) == 0
    
    def test_audit_log_functionality(self):
        """Test audit logging functionality."""
        # Perform various operations
        test_file = self.repo_root / "audit_test.txt"
        
        # Write file
        self.controller.safe_write(test_file, "audit content")
        
        # Read file
        self.controller.safe_read(test_file)
        
        # Delete file
        self.controller.safe_delete(test_file)
        
        # Check audit log
        audit_log = self.controller.get_audit_log()
        assert len(audit_log) >= 3
        
        # Check operation types
        operations = [log.operation for log in audit_log]
        assert 'open' in operations  # from safe_write
        assert 'open' in operations  # from safe_read
        assert 'delete' in operations
    
    def test_export_audit_log(self):
        """Test audit log export functionality."""
        # Perform some operations
        test_file = self.repo_root / "export_test.txt"
        self.controller.safe_write(test_file, "export content")
        
        # Export audit log
        export_file = self.temp_dir / "audit_export.json"
        self.controller.export_audit_log(export_file)
        
        # Verify export
        assert export_file.exists()
        
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        assert isinstance(exported_data, list)
        assert len(exported_data) > 0
        
        # Check structure of exported data
        first_entry = exported_data[0]
        assert 'timestamp' in first_entry
        assert 'operation' in first_entry
        assert 'path' in first_entry
        assert 'access_type' in first_entry
        assert 'result' in first_entry
    
    def test_get_statistics(self):
        """Test statistics generation."""
        # Perform various operations
        test_file = self.repo_root / "stats_test.txt"
        
        # Successful operations
        self.controller.safe_write(test_file, "stats content")
        self.controller.safe_read(test_file)
        
        # Failed operation (try to access denied path)
        try:
            self.controller.safe_read("/etc/passwd")
        except PermissionError:
            pass
        
        # Get statistics
        stats = self.controller.get_statistics()
        
        assert 'total_operations' in stats
        assert 'allowed_operations' in stats
        assert 'denied_operations' in stats
        assert 'files_created' in stats
        assert 'operations_by_type' in stats
        assert 'operations_by_access_type' in stats
        
        assert stats['total_operations'] > 0
        assert stats['allowed_operations'] > 0
        assert stats['denied_operations'] > 0
        assert stats['files_created'] > 0
    
    def test_checksum_calculation(self):
        """Test file checksum calculation."""
        # Create test file
        test_file = self.repo_root / "checksum_test.txt"
        test_content = "Content for checksum testing"
        test_file.write_text(test_content)
        
        # Calculate checksum
        checksum = self.controller._calculate_checksum(test_file)
        
        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 hex digest length
        
        # Verify checksum consistency
        checksum2 = self.controller._calculate_checksum(test_file)
        assert checksum == checksum2
        
        # Test with non-existent file
        non_existent = self.repo_root / "non_existent.txt"
        checksum_none = self.controller._calculate_checksum(non_existent)
        assert checksum_none is None

class TestGlobalFunctions:
    """Test cases for global convenience functions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_root = self.temp_dir / "repo"
        self.repo_root.mkdir()
        
        # Reset global controller
        import common.safety.fs
        common.safety.fs._fs_controller = None
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        
        # Reset global controller
        import common.safety.fs
        common.safety.fs._fs_controller = None
    
    def test_get_fs_controller(self):
        """Test global filesystem controller retrieval."""
        controller1 = get_fs_controller(repo_root=str(self.repo_root))
        controller2 = get_fs_controller()
        
        # Should return the same instance
        assert controller1 is controller2
        assert isinstance(controller1, FilesystemAccessController)
    
    def test_safe_open_global(self):
        """Test global safe_open function."""
        test_file = self.repo_root / "global_test.txt"
        test_content = "Global function test"
        
        # Initialize controller with repo root
        get_fs_controller(repo_root=str(self.repo_root))
        
        # Test global safe_open
        with safe_open(test_file, 'w') as f:
            f.write(test_content)
        
        # Verify file was created
        assert test_file.exists()
        assert test_file.read_text() == test_content
    
    def test_safe_read_global(self):
        """Test global safe_read function."""
        test_file = self.repo_root / "global_read_test.txt"
        test_content = "Global read test content"
        test_file.write_text(test_content)
        
        # Initialize controller
        get_fs_controller(repo_root=str(self.repo_root))
        
        # Test global safe_read
        content = safe_read(test_file)
        assert content == test_content
        
        # Test binary read
        binary_content = safe_read(test_file, binary=True)
        assert binary_content == test_content.encode('utf-8')
    
    def test_safe_write_global(self):
        """Test global safe_write function."""
        test_file = self.repo_root / "global_write_test.txt"
        test_content = "Global write test content"
        
        # Initialize controller
        get_fs_controller(repo_root=str(self.repo_root))
        
        # Test global safe_write
        bytes_written = safe_write(test_file, test_content)
        assert bytes_written == len(test_content)
        
        # Verify content
        assert test_file.read_text() == test_content
    
    def test_safe_copy_global(self):
        """Test global safe_copy function."""
        src_file = self.repo_root / "global_src.txt"
        dst_file = self.repo_root / "global_dst.txt"
        test_content = "Global copy test"
        src_file.write_text(test_content)
        
        # Initialize controller
        get_fs_controller(repo_root=str(self.repo_root))
        
        # Test global safe_copy
        safe_copy(src_file, dst_file)
        
        # Verify copy
        assert dst_file.exists()
        assert dst_file.read_text() == test_content
    
    def test_safe_delete_global(self):
        """Test global safe_delete function."""
        test_file = self.repo_root / "global_delete_test.txt"
        test_file.write_text("Delete me")
        
        # Initialize controller
        get_fs_controller(repo_root=str(self.repo_root))
        
        # Test global safe_delete
        safe_delete(test_file)
        
        # Verify deletion
        assert not test_file.exists()

class TestIntegration:
    """Integration tests for filesystem access controls."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_root = self.temp_dir / "repo"
        self.repo_root.mkdir()
        
        # Create subdirectories
        (self.repo_root / "src").mkdir()
        (self.repo_root / "tests").mkdir()
        (self.repo_root / "docs").mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_complex_file_operations(self):
        """Test complex file operations workflow."""
        policy = FilesystemPolicy(
            restrict_to_repo=True,
            temp_dir_access=True,
            audit_enabled=True,
            max_file_size=1024 * 1024  # 1MB
        )
        
        controller = FilesystemAccessController(policy, str(self.repo_root))
        
        # Create source files
        src_file = self.repo_root / "src" / "main.py"
        controller.safe_write(src_file, "print('Hello, World!')")
        
        config_file = self.repo_root / "config.json"
        config_data = '{"debug": true, "version": "1.0.0"}'
        controller.safe_write(config_file, config_data)
        
        # Copy files
        backup_file = self.repo_root / "src" / "main_backup.py"
        controller.safe_copy(src_file, backup_file)
        
        # Read and modify
        content = controller.safe_read(src_file)
        modified_content = content + "\nprint('Modified!')"
        controller.safe_write(src_file, modified_content)
        
        # Create temp directory and files
        temp_dir = controller.create_temp_dir(prefix="workflow_")
        temp_file = temp_dir / "temp_data.txt"
        controller.safe_write(temp_file, "Temporary data")
        
        # Verify all operations
        assert src_file.exists()
        assert backup_file.exists()
        assert config_file.exists()
        assert temp_file.exists()
        
        # Check audit log
        audit_log = controller.get_audit_log()
        assert len(audit_log) > 5  # Multiple operations logged
        
        # Check statistics
        stats = controller.get_statistics()
        assert stats['files_created'] >= 4
        assert stats['allowed_operations'] > 0
        assert stats['denied_operations'] == 0
        
        # Cleanup
        controller.cleanup_temp_dirs()
        assert not temp_dir.exists()
    
    def test_security_violation_scenarios(self):
        """Test various security violation scenarios."""
        policy = FilesystemPolicy(
            restrict_to_repo=True,
            temp_dir_access=False,
            system_access=False,
            denied_extensions={'.exe', '.bat'},
            max_file_size=1024  # 1KB limit
        )
        
        controller = FilesystemAccessController(policy, str(self.repo_root))
        
        # Test path traversal
        with pytest.raises(PermissionError):
            controller.safe_read("../../../etc/passwd")
        
        # Test denied extension
        with pytest.raises(PermissionError):
            controller.safe_write(self.repo_root / "malware.exe", "malicious code")
        
        # Test system access
        with pytest.raises(PermissionError):
            controller.safe_read("/etc/passwd")
        
        # Test temp directory access
        with pytest.raises(PermissionError):
            controller.create_temp_dir()
        
        # Test file size limit
        large_content = "x" * 2048  # 2KB content
        with pytest.raises(Exception):  # May be PermissionError or other
            large_file = self.repo_root / "large.txt"
            large_file.write_text(large_content)  # Create large file first
            controller.safe_read(large_file)  # Then try to access it
        
        # Check that violations were logged
        audit_log = controller.get_audit_log()
        denied_operations = [log for log in audit_log if log.result == AccessResult.DENIED]
        assert len(denied_operations) > 0
        
        # Check statistics
        stats = controller.get_statistics()
        assert stats['denied_operations'] > 0

if __name__ == "__main__":
    pytest.main([__file__])