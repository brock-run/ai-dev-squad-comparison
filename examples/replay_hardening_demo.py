"""
Replay System Hardening Demo

This example demonstrates the enhanced integrity checking, manifest validation,
and failure mode handling implemented for Week 1, Day 5 of the adjustment plan.
"""

import logging
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from benchmark.replay.integrity import (
    create_integrity_checker, verify_recording_comprehensive, 
    IntegrityError, ManifestValidationError
)
from benchmark.replay.failure_modes import (
    FailureModeHandler, FailureMode, RecoveryStrategy, handle_failure
)

# Set up logging to see the hardening in action
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def demo_integrity_checking():
    """Demonstrate enhanced integrity checking capabilities."""
    print("=== Enhanced Integrity Checking Demo ===")
    
    # Create integrity checker with different algorithms
    checker_blake3 = create_integrity_checker('blake3')  # Will fall back to blake2b
    checker_sha256 = create_integrity_checker('sha256')
    
    print(f"BLAKE3 checker algorithm: {checker_blake3.hash_algorithm}")
    print(f"SHA256 checker algorithm: {checker_sha256.hash_algorithm}")
    
    # Test data hashing
    test_data = "This is test data for integrity checking"
    hash_blake = checker_blake3.calculate_data_hash(test_data)
    hash_sha256 = checker_sha256.calculate_data_hash(test_data)
    
    print(f"BLAKE hash: {hash_blake[:32]}...")
    print(f"SHA256 hash: {hash_sha256[:32]}...")
    print(f"Hashes are different: {hash_blake != hash_sha256}")
    
    # Test file integrity
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test file content for integrity verification")
        temp_file = Path(f.name)
    
    try:
        file_hash = checker_blake3.calculate_file_hash(temp_file)
        print(f"File hash: {file_hash[:32]}...")
        
        # Verify integrity (should pass)
        result = checker_blake3.verify_file_integrity(temp_file, file_hash)
        print(f"Integrity verification passed: {result}")
        
        # Test with wrong hash (should fail)
        try:
            checker_blake3.verify_file_integrity(temp_file, "wrong_hash_value_123456789")
            print("ERROR: Should have failed!")
        except IntegrityError as e:
            print(f"✓ Correctly detected integrity failure: {str(e)[:50]}...")
            
    finally:
        temp_file.unlink()
    
    print()


def demo_manifest_validation():
    """Demonstrate comprehensive manifest validation."""
    print("=== Manifest Validation Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a mock recording structure
        events_file = temp_path / "events.jsonl"
        events_file.write_text('{"event": "test1"}\n{"event": "test2"}')
        
        checker = create_integrity_checker()
        events_hash = checker.calculate_file_hash(events_file)
        
        # Create valid manifest with new format
        manifest = {
            "run_id": "demo_run_001",
            "timestamp": "2024-01-01T00:00:00Z",
            "schema_version": "1.1.0",
            "hash_algorithm": checker.hash_algorithm,
            "file_hashes": {
                "events.jsonl": {
                    "hash": events_hash,
                    "size": events_file.stat().st_size,
                    "algorithm": checker.hash_algorithm
                }
            },
            "event_count": 2,
            "total_size": events_file.stat().st_size
        }
        
        manifest_path = temp_path / "manifest.yaml"
        import yaml
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f)
        
        # Test manifest validation
        try:
            validated_manifest = checker.verify_manifest_integrity(manifest_path)
            print(f"✓ Manifest validation passed for run: {validated_manifest['run_id']}")
            print(f"  Schema version: {validated_manifest['schema_version']}")
            print(f"  Hash algorithm: {validated_manifest['hash_algorithm']}")
            print(f"  Event count: {validated_manifest['event_count']}")
        except ManifestValidationError as e:
            print(f"✗ Manifest validation failed: {e}")
        
        # Test comprehensive recording verification
        print("\nRunning comprehensive recording verification...")
        report = verify_recording_comprehensive(temp_path)
        
        print(f"Verification success: {report['success']}")
        print(f"Files checked: {report['files_checked']}")
        print(f"Files passed: {report['files_passed']}")
        print(f"Files failed: {report['files_failed']}")
        
        if report['errors']:
            print(f"Errors: {report['errors']}")
        if report['warnings']:
            print(f"Warnings: {report['warnings']}")
    
    print()


def demo_failure_mode_handling():
    """Demonstrate comprehensive failure mode handling."""
    print("=== Failure Mode Handling Demo ===")
    
    # Create failure handler with custom strategies
    custom_strategies = {
        FailureMode.REPLAY_LOOKUP_MISMATCH: RecoveryStrategy.FALLBACK_GRACEFUL,
        FailureMode.REPLAY_INTEGRITY_CHECK_FAILED: RecoveryStrategy.REPAIR_AND_CONTINUE,
        FailureMode.SYSTEM_DEPENDENCY_MISSING: RecoveryStrategy.SKIP_AND_LOG,
    }
    
    handler = FailureModeHandler(custom_strategies)
    
    # Demo 1: Graceful fallback
    print("Demo 1: Graceful fallback for lookup mismatch")
    try:
        result = handler.handle_failure(
            FailureMode.REPLAY_LOOKUP_MISMATCH,
            Exception("Input fingerprint mismatch"),
            {"lookup_key": "llm_call:test:agent:0", "expected": "abc", "actual": "def"}
        )
        print(f"✓ Graceful fallback result: {result}")
    except Exception as e:
        print(f"✗ Unexpected failure: {e}")
    
    # Demo 2: Skip and log
    print("\nDemo 2: Skip and log for missing dependency")
    try:
        result = handler.handle_failure(
            FailureMode.SYSTEM_DEPENDENCY_MISSING,
            ImportError("zstandard library not available"),
            {"operation": "decompress_events", "fallback_available": True}
        )
        print(f"✓ Skip and log result: {result}")
    except Exception as e:
        print(f"✗ Unexpected failure: {e}")
    
    # Demo 3: Fail fast
    print("\nDemo 3: Fail fast for critical errors")
    try:
        handler.handle_failure(
            FailureMode.RECORDING_DISK_FULL,
            OSError("No space left on device"),
            {"disk_usage": "100%", "required_space": "1GB"}
        )
        print("✗ Should have failed fast!")
    except OSError:
        print("✓ Correctly failed fast for critical error")
    
    # Demo 4: Failure statistics
    print("\nDemo 4: Failure statistics")
    stats = handler.get_failure_statistics()
    print(f"Total failures: {stats['total_failures']}")
    print(f"Recovery attempted: {stats['recovery_attempted']}")
    print(f"Recovery successful: {stats['recovery_successful']}")
    print(f"Recovery rate: {stats['recovery_rate']:.2%}")
    print(f"Failure counts: {stats['failure_counts']}")
    
    print()


def demo_failure_callbacks():
    """Demonstrate failure callback system."""
    print("=== Failure Callback System Demo ===")
    
    handler = FailureModeHandler()
    
    # Register callbacks for different failure modes
    integrity_failures = []
    corruption_events = []
    
    def integrity_callback(failure_context):
        integrity_failures.append({
            'timestamp': failure_context.timestamp,
            'error': str(failure_context.error),
            'context': failure_context.context
        })
        print(f"📊 Integrity failure logged: {failure_context.failure_mode.value}")
    
    def corruption_callback(failure_context):
        corruption_events.append(failure_context)
        print(f"🚨 Corruption detected: {failure_context.context.get('file', 'unknown')}")
    
    handler.register_failure_callback(FailureMode.REPLAY_INTEGRITY_CHECK_FAILED, integrity_callback)
    handler.register_failure_callback(FailureMode.DATA_CORRUPTION_DETECTED, corruption_callback)
    
    # Trigger failures to test callbacks
    try:
        handler.handle_failure(
            FailureMode.DATA_CORRUPTION_DETECTED,
            Exception("Corrupted event stream"),
            {"file": "events.jsonl", "corrupted_lines": [5, 12, 18]}
        )
    except:
        pass
    
    print(f"Integrity failures logged: {len(integrity_failures)}")
    print(f"Corruption events logged: {len(corruption_events)}")
    
    print()


def demo_recovery_strategies():
    """Demonstrate different recovery strategies."""
    print("=== Recovery Strategies Demo ===")
    
    # Test retry with backoff
    print("Testing retry with backoff strategy...")
    
    retry_handler = FailureModeHandler({
        FailureMode.RECORDING_IO_ERROR: RecoveryStrategy.RETRY_WITH_BACKOFF
    })
    
    retry_count = 0
    def mock_retry_func():
        nonlocal retry_count
        retry_count += 1
        if retry_count < 2:
            raise Exception(f"Retry attempt {retry_count} failed")
        return f"Success on attempt {retry_count}"
    
    try:
        result = retry_handler.handle_failure(
            FailureMode.RECORDING_IO_ERROR,
            Exception("Initial IO error"),
            {
                "max_retries": 3,
                "base_delay": 0.1,  # Short delay for demo
                "retry_func": mock_retry_func
            }
        )
        print(f"✓ Retry strategy result: {result}")
        print(f"  Total retry attempts: {retry_count}")
    except Exception as e:
        print(f"✗ Retry strategy failed: {e}")
    
    print()


def main():
    """Run the complete hardening demo."""
    print("Replay System Hardening Demo")
    print("=" * 50)
    print("This demo showcases the enhanced integrity checking, manifest validation,")
    print("and failure mode handling implemented for Week 1, Day 5.\n")
    
    # Run all demos
    demo_integrity_checking()
    demo_manifest_validation()
    demo_failure_mode_handling()
    demo_failure_callbacks()
    demo_recovery_strategies()
    
    print("=== Demo Complete ===")
    print("✅ Enhanced integrity checking with multiple hash algorithms")
    print("✅ Comprehensive manifest validation with schema versioning")
    print("✅ Robust failure mode handling with recovery strategies")
    print("✅ Failure callback system for monitoring and alerting")
    print("✅ Multiple recovery strategies (fail fast, graceful fallback, retry, repair)")
    print("✅ Detailed failure statistics and reporting")
    print("\n🎉 The replay system is now hardened and production-ready!")


if __name__ == "__main__":
    main()