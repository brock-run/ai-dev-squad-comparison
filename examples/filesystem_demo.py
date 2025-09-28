#!/usr/bin/env python3
"""
Filesystem Access Controls Demo
This script demonstrates the capabilities of the filesystem access control system
with various file operations and security scenarios.
"""
import sys
import tempfile
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.safety.fs import (
    FilesystemAccessController, FilesystemPolicy, AccessType, AccessResult,
    safe_open, safe_read, safe_write, safe_copy, safe_delete
)
from common.safety.config_integration import SafetyManager

def demo_basic_file_operations():
    """Demo basic file operations with access controls."""
    print("=== Basic File Operations Demo ===")
    
    # Create temporary repository
    with tempfile.TemporaryDirectory(prefix="fs_demo_repo_") as repo_dir:
        repo_path = Path(repo_dir)
        
        # Create filesystem controller
        policy = FilesystemPolicy(
            restrict_to_repo=True,
            temp_dir_access=True,
            audit_enabled=True
        )
        controller = FilesystemAccessController(policy, str(repo_path))
        
        print(f"Repository root: {repo_path}")
        
        # 1. Safe file writing
        print("\n1. Creating files with safe_write:")
        config_file = repo_path / "config.json"
        config_data = {
            "app_name": "FilesystemDemo",
            "version": "1.0.0",
            "debug": True
        }
        
        controller.safe_write(config_file, json.dumps(config_data, indent=2))
        print(f"   Created: {config_file.name}")
        
        # Create source file
        src_file = repo_path / "main.py"
        src_code = '''#!/usr/bin/env python3
"""
Demo application
"""
import json

def main():
    with open("config.json", "r") as f:
        config = json.load(f)
    print(f"Running {config['app_name']} v{config['version']}")

if __name__ == "__main__":
    main()
'''
        controller.safe_write(src_file, src_code)
        print(f"   Created: {src_file.name}")
        
        # 2. Safe file reading
        print("\n2. Reading files with safe_read:")
        config_content = controller.safe_read(config_file)
        loaded_config = json.loads(config_content)
        print(f"   Config app_name: {loaded_config['app_name']}")
        
        src_content = controller.safe_read(src_file)
        print(f"   Source file length: {len(src_content)} characters")
        
        # 3. Safe file copying
        print("\n3. Copying files with safe_copy:")
        backup_file = repo_path / "main_backup.py"
        controller.safe_copy(src_file, backup_file)
        print(f"   Copied {src_file.name} -> {backup_file.name}")
        
        # 4. Context manager usage
        print("\n4. Using safe_open context manager:")
        log_file = repo_path / "app.log"
        with controller.safe_open(log_file, 'w') as f:
            f.write("Application started\n")
            f.write("Configuration loaded\n")
            f.write("Ready to process requests\n")
        print(f"   Created log file: {log_file.name}")
        
        # 5. Temporary directory creation
        print("\n5. Creating temporary directory:")
        temp_dir = controller.create_temp_dir(prefix="demo_", suffix="_temp")
        temp_file = temp_dir / "temp_data.txt"
        controller.safe_write(temp_file, "Temporary processing data")
        print(f"   Created temp dir: {temp_dir}")
        print(f"   Created temp file: {temp_file}")
        
        # 6. Show statistics
        print("\n6. Access statistics:")
        stats = controller.get_statistics()
        print(f"   Total operations: {stats['total_operations']}")
        print(f"   Allowed operations: {stats['allowed_operations']}")
        print(f"   Files created: {stats['files_created']}")
        print(f"   Active temp dirs: {stats['temp_dirs_active']}")
        
        # Cleanup
        controller.cleanup_temp_dirs()
        print(f"   Cleaned up temporary directories")

def demo_security_controls():
    """Demo security controls and access restrictions."""
    print("\n=== Security Controls Demo ===")
    
    with tempfile.TemporaryDirectory(prefix="fs_demo_secure_") as repo_dir:
        repo_path = Path(repo_dir)
        
        # Create restrictive policy
        policy = FilesystemPolicy(
            restrict_to_repo=True,
            temp_dir_access=False,  # Disable temp access
            system_access=False,
            denied_extensions={'.exe', '.bat', '.sh'},
            allowed_extensions={'.py', '.txt', '.json', '.md'},
            max_file_size=1024,  # 1KB limit
            audit_enabled=True
        )
        controller = FilesystemAccessController(policy, str(repo_path))
        
        print(f"Secure repository root: {repo_path}")
        
        # 1. Test path traversal protection
        print("\n1. Testing path traversal protection:")
        try:
            controller.safe_read("../../../etc/passwd")
            print("   ERROR: Path traversal should have been blocked!")
        except PermissionError as e:
            print(f"   ✓ Path traversal blocked: {e}")
        
        # 2. Test denied file extensions
        print("\n2. Testing denied file extensions:")
        try:
            malware_file = repo_path / "malware.exe"
            controller.safe_write(malware_file, "malicious code")
            print("   ERROR: .exe file should have been blocked!")
        except PermissionError as e:
            print(f"   ✓ Denied extension blocked: {e}")
        
        # 3. Test system file access
        print("\n3. Testing system file access:")
        try:
            controller.safe_read("/etc/passwd")
            print("   ERROR: System file access should have been blocked!")
        except PermissionError as e:
            print(f"   ✓ System access blocked: {e}")
        
        # 4. Test temporary directory restriction
        print("\n4. Testing temporary directory restriction:")
        try:
            controller.create_temp_dir()
            print("   ERROR: Temp directory creation should have been blocked!")
        except PermissionError as e:
            print(f"   ✓ Temp directory blocked: {e}")
        
        # 5. Test file size limits
        print("\n5. Testing file size limits:")
        try:
            large_content = "x" * 2048  # 2KB content, exceeds 1KB limit
            large_file = repo_path / "large.txt"
            # Create file outside controller first
            large_file.write_text(large_content)
            # Then try to read it through controller
            controller.safe_read(large_file)
            print("   WARNING: Large file access was allowed (size check may be on write only)")
        except Exception as e:
            print(f"   ✓ Large file blocked: {e}")
        
        # 6. Show security statistics
        print("\n6. Security statistics:")
        stats = controller.get_statistics()
        print(f"   Total operations: {stats['total_operations']}")
        print(f"   Denied operations: {stats['denied_operations']}")
        print(f"   Allowed operations: {stats['allowed_operations']}")
        
        if stats['denied_operations'] > 0:
            print("   ✓ Security controls are working correctly")
        else:
            print("   ⚠ No operations were denied (check test scenarios)")

def demo_audit_logging():
    """Demo audit logging and monitoring capabilities."""
    print("\n=== Audit Logging Demo ===")
    
    with tempfile.TemporaryDirectory(prefix="fs_demo_audit_") as repo_dir:
        repo_path = Path(repo_dir)
        
        # Create policy with audit logging
        audit_log_file = repo_path / "filesystem_audit.log"
        policy = FilesystemPolicy(
            restrict_to_repo=True,
            audit_enabled=True,
            audit_log_path=str(audit_log_file)
        )
        controller = FilesystemAccessController(policy, str(repo_path))
        
        print(f"Audit repository root: {repo_path}")
        print(f"Audit log file: {audit_log_file}")
        
        # Perform various operations
        print("\n1. Performing monitored operations:")
        
        # Create files
        data_file = repo_path / "data.txt"
        controller.safe_write(data_file, "Initial data content")
        print("   Created data.txt")
        
        # Read file
        content = controller.safe_read(data_file)
        print("   Read data.txt")
        
        # Modify file
        controller.safe_write(data_file, content + "\nAppended line", append=True)
        print("   Modified data.txt")
        
        # Copy file
        backup_file = repo_path / "data_backup.txt"
        controller.safe_copy(data_file, backup_file)
        print("   Copied data.txt -> data_backup.txt")
        
        # Try unauthorized operation
        try:
            controller.safe_read("/etc/passwd")
        except PermissionError:
            print("   Attempted unauthorized access (logged)")
        
        # 2. Show audit log
        print("\n2. Audit log entries:")
        audit_log = controller.get_audit_log()
        
        for i, entry in enumerate(audit_log[-5:], 1):  # Show last 5 entries
            print(f"   {i}. {entry.timestamp.strftime('%H:%M:%S')} - "
                  f"{entry.operation} - {entry.access_type.value} - "
                  f"{entry.result.value} - {Path(entry.path).name}")
        
        # 3. Export audit log
        print("\n3. Exporting audit log:")
        export_file = repo_path / "audit_export.json"
        controller.export_audit_log(export_file)
        
        if export_file.exists():
            with open(export_file, 'r') as f:
                exported_data = json.load(f)
            print(f"   Exported {len(exported_data)} audit entries to {export_file.name}")
            
            # Show sample entry
            if exported_data:
                sample_entry = exported_data[0]
                print(f"   Sample entry: {sample_entry['operation']} on {Path(sample_entry['path']).name}")
        
        # 4. Check audit log file
        if audit_log_file.exists():
            print(f"\n4. Audit log file contains {len(audit_log_file.read_text().splitlines())} lines")

def demo_configuration_integration():
    """Demo integration with configuration system."""
    print("\n=== Configuration Integration Demo ===")
    
    with tempfile.TemporaryDirectory(prefix="fs_demo_config_") as repo_dir:
        repo_path = Path(repo_dir)
        
        # Create safety manager with configuration
        safety_manager = SafetyManager(repo_root=str(repo_path))
        
        print(f"Configuration-based repository root: {repo_path}")
        
        # 1. Check safety status
        print("\n1. Safety configuration status:")
        print(f"   Safety enabled: {safety_manager.is_safety_enabled()}")
        
        resource_limits = safety_manager.get_resource_limits()
        print(f"   Memory limit: {resource_limits['max_memory_mb']} MB")
        print(f"   CPU limit: {resource_limits['max_cpu_percent']}%")
        print(f"   Timeout: {resource_limits['timeout_seconds']}s")
        
        filesystem_policy = safety_manager.get_filesystem_policy()
        print(f"   Repo restriction: {filesystem_policy['restrict_to_repo']}")
        print(f"   Temp access: {filesystem_policy['temp_dir_access']}")
        print(f"   System access: {filesystem_policy['system_access']}")
        
        # 2. Perform safe file operations through safety manager
        print("\n2. Configuration-based file operations:")
        
        try:
            # Write file
            test_file = repo_path / "config_test.txt"
            safety_manager.safe_file_operation('write', test_file, "Configuration-based write")
            print("   ✓ File write successful")
            
            # Read file
            content = safety_manager.safe_file_operation('read', test_file)
            print(f"   ✓ File read successful: {len(content)} characters")
            
            # Create temp directory
            temp_dir = safety_manager.safe_file_operation('create_temp_dir', prefix="config_")
            print(f"   ✓ Temp directory created: {temp_dir}")
            
        except Exception as e:
            print(f"   ✗ Operation failed: {e}")
        
        # 3. Get filesystem statistics
        print("\n3. Filesystem statistics:")
        stats = safety_manager.get_filesystem_statistics()
        print(f"   Total operations: {stats['total_operations']}")
        print(f"   Files created: {stats['files_created']}")
        print(f"   Operations by type: {dict(list(stats['operations_by_type'].items())[:3])}")
        
        # 4. Export audit log
        print("\n4. Exporting audit log:")
        audit_export = repo_path / "config_audit.json"
        safety_manager.export_filesystem_audit_log(str(audit_export))
        
        if audit_export.exists():
            print(f"   ✓ Audit log exported to {audit_export.name}")
        
        # Cleanup
        safety_manager.cleanup_resources()
        print("   ✓ Resources cleaned up")

def demo_global_functions():
    """Demo global convenience functions."""
    print("\n=== Global Functions Demo ===")
    
    with tempfile.TemporaryDirectory(prefix="fs_demo_global_") as repo_dir:
        repo_path = Path(repo_dir)
        
        # Initialize global controller
        from common.safety.fs import get_fs_controller
        controller = get_fs_controller(repo_root=str(repo_path))
        
        print(f"Global functions repository root: {repo_path}")
        
        # 1. Use global safe functions
        print("\n1. Using global safe functions:")
        
        # Write using global function
        test_file = repo_path / "global_test.txt"
        safe_write(test_file, "Content written with global function")
        print("   ✓ Global safe_write successful")
        
        # Read using global function
        content = safe_read(test_file)
        print(f"   ✓ Global safe_read successful: {len(content)} characters")
        
        # Copy using global function
        copy_file = repo_path / "global_copy.txt"
        safe_copy(test_file, copy_file)
        print("   ✓ Global safe_copy successful")
        
        # Use context manager
        with safe_open(repo_path / "global_context.txt", 'w') as f:
            f.write("Written using global safe_open context manager")
        print("   ✓ Global safe_open context manager successful")
        
        # 2. Show that operations are tracked
        print("\n2. Global operations tracking:")
        stats = controller.get_statistics()
        print(f"   Operations tracked: {stats['total_operations']}")
        print(f"   Files created: {stats['files_created']}")
        
        # Delete using global function
        safe_delete(copy_file)
        print("   ✓ Global safe_delete successful")
        
        # Final stats
        final_stats = controller.get_statistics()
        print(f"   Final operations: {final_stats['total_operations']}")

def main():
    """Run all filesystem demos."""
    print("AI Dev Squad Comparison - Filesystem Access Controls Demo")
    print("=" * 70)
    
    try:
        demo_basic_file_operations()
        demo_security_controls()
        demo_audit_logging()
        demo_configuration_integration()
        demo_global_functions()
        
        print("\n" + "=" * 70)
        print("Filesystem demo completed successfully!")
        print("\nKey takeaways:")
        print("• Filesystem access controls provide comprehensive security")
        print("• All file operations are audited and logged")
        print("• Path traversal and dangerous extensions are blocked")
        print("• Integration with configuration system enables policy management")
        print("• Global functions provide convenient access to safety controls")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()