"""
Replay System Failure Mode Handling

This module provides comprehensive failure mode detection, recovery strategies,
and error handling for the record-replay system. Following the adjustment plan
for Week 1, Day 5: "Harden: hashing, manifest integrity, failure modes."
"""

import logging
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
import traceback

logger = logging.getLogger(__name__)


class FailureMode(Enum):
    """Types of failure modes in the replay system."""
    
    # Recording failures
    RECORDING_INIT_FAILED = "recording_init_failed"
    RECORDING_IO_ERROR = "recording_io_error"
    RECORDING_DISK_FULL = "recording_disk_full"
    RECORDING_PERMISSION_DENIED = "recording_permission_denied"
    
    # Replay failures
    REPLAY_RECORDING_NOT_FOUND = "replay_recording_not_found"
    REPLAY_INTEGRITY_CHECK_FAILED = "replay_integrity_check_failed"
    REPLAY_MANIFEST_CORRUPTED = "replay_manifest_corrupted"
    REPLAY_EVENTS_CORRUPTED = "replay_events_corrupted"
    REPLAY_LOOKUP_MISMATCH = "replay_lookup_mismatch"
    REPLAY_INPUT_FINGERPRINT_MISMATCH = "replay_input_fingerprint_mismatch"
    
    # System failures
    SYSTEM_OUT_OF_MEMORY = "system_out_of_memory"
    SYSTEM_DEPENDENCY_MISSING = "system_dependency_missing"
    SYSTEM_PERMISSION_ERROR = "system_permission_error"
    
    # Data corruption
    DATA_CORRUPTION_DETECTED = "data_corruption_detected"
    DATA_PARTIAL_CORRUPTION = "data_partial_corruption"
    DATA_SCHEMA_MISMATCH = "data_schema_mismatch"


class RecoveryStrategy(Enum):
    """Recovery strategies for different failure modes."""
    
    FAIL_FAST = "fail_fast"                    # Immediately raise exception
    FALLBACK_GRACEFUL = "fallback_graceful"    # Fall back to normal execution
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry with exponential backoff
    REPAIR_AND_CONTINUE = "repair_and_continue" # Attempt repair and continue
    SKIP_AND_LOG = "skip_and_log"             # Skip operation and log warning


class FailureContext:
    """Context information for a failure."""
    
    def __init__(self, failure_mode: FailureMode, error: Exception, 
                 context: Dict[str, Any], timestamp: Optional[datetime] = None):
        self.failure_mode = failure_mode
        self.error = error
        self.context = context
        self.timestamp = timestamp or datetime.utcnow()
        self.traceback = traceback.format_exc()
        self.recovery_attempted = False
        self.recovery_successful = False


class FailureModeHandler:
    """
    Comprehensive failure mode handler for the replay system.
    
    Provides detection, logging, recovery strategies, and monitoring for various
    failure scenarios that can occur during recording and replay operations.
    """
    
    def __init__(self, recovery_strategies: Optional[Dict[FailureMode, RecoveryStrategy]] = None):
        """
        Initialize failure mode handler.
        
        Args:
            recovery_strategies: Custom recovery strategies for specific failure modes
        """
        self.recovery_strategies = recovery_strategies or self._get_default_strategies()
        self.failure_history: List[FailureContext] = []
        self.recovery_callbacks: Dict[FailureMode, List[Callable]] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def handle_failure(self, failure_mode: FailureMode, error: Exception, 
                      context: Dict[str, Any]) -> Any:
        """
        Handle a failure according to the configured strategy.
        
        Args:
            failure_mode: Type of failure that occurred
            error: The exception that was raised
            context: Additional context about the failure
            
        Returns:
            Result of recovery attempt or raises exception
            
        Raises:
            Exception: If recovery fails or strategy is FAIL_FAST
        """
        failure_context = FailureContext(failure_mode, error, context)
        self.failure_history.append(failure_context)
        
        self.logger.error(
            f"Failure detected: {failure_mode.value} - {error} "
            f"Context: {context}"
        )
        
        strategy = self.recovery_strategies.get(failure_mode, RecoveryStrategy.FAIL_FAST)
        
        try:
            result = self._execute_recovery_strategy(strategy, failure_context)
            failure_context.recovery_attempted = True
            failure_context.recovery_successful = True
            return result
            
        except Exception as recovery_error:
            failure_context.recovery_attempted = True
            failure_context.recovery_successful = False
            
            self.logger.error(
                f"Recovery failed for {failure_mode.value}: {recovery_error}"
            )
            
            # Execute failure callbacks
            self._execute_failure_callbacks(failure_mode, failure_context)
            
            # Re-raise the original error if recovery fails
            raise error
    
    def _execute_recovery_strategy(self, strategy: RecoveryStrategy, 
                                 failure_context: FailureContext) -> Any:
        """Execute the specified recovery strategy."""
        
        if strategy == RecoveryStrategy.FAIL_FAST:
            raise failure_context.error
        
        elif strategy == RecoveryStrategy.FALLBACK_GRACEFUL:
            return self._fallback_graceful(failure_context)
        
        elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            return self._retry_with_backoff(failure_context)
        
        elif strategy == RecoveryStrategy.REPAIR_AND_CONTINUE:
            return self._repair_and_continue(failure_context)
        
        elif strategy == RecoveryStrategy.SKIP_AND_LOG:
            return self._skip_and_log(failure_context)
        
        else:
            raise ValueError(f"Unknown recovery strategy: {strategy}")
    
    def _fallback_graceful(self, failure_context: FailureContext) -> Any:
        """Gracefully fall back to normal operation."""
        self.logger.warning(
            f"Falling back to normal operation due to {failure_context.failure_mode.value}"
        )
        
        # Return a safe default or None to indicate fallback
        return None
    
    def _retry_with_backoff(self, failure_context: FailureContext) -> Any:
        """Retry the operation with exponential backoff."""
        import time
        
        max_retries = failure_context.context.get('max_retries', 3)
        base_delay = failure_context.context.get('base_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                delay = base_delay * (2 ** attempt)
                self.logger.info(f"Retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                
                # Try to re-execute the original operation
                retry_func = failure_context.context.get('retry_func')
                if retry_func:
                    return retry_func()
                else:
                    self.logger.warning("No retry function provided, falling back")
                    return self._fallback_graceful(failure_context)
                    
            except Exception as retry_error:
                if attempt == max_retries - 1:
                    raise retry_error
                continue
        
        # If we get here, all retries failed
        raise failure_context.error
    
    def _repair_and_continue(self, failure_context: FailureContext) -> Any:
        """Attempt to repair the issue and continue."""
        failure_mode = failure_context.failure_mode
        
        if failure_mode == FailureMode.REPLAY_MANIFEST_CORRUPTED:
            return self._repair_corrupted_manifest(failure_context)
        
        elif failure_mode == FailureMode.REPLAY_EVENTS_CORRUPTED:
            return self._repair_corrupted_events(failure_context)
        
        elif failure_mode == FailureMode.DATA_PARTIAL_CORRUPTION:
            return self._repair_partial_corruption(failure_context)
        
        else:
            self.logger.warning(f"No repair strategy for {failure_mode.value}, falling back")
            return self._fallback_graceful(failure_context)
    
    def _skip_and_log(self, failure_context: FailureContext) -> Any:
        """Skip the operation and log a warning."""
        self.logger.warning(
            f"Skipping operation due to {failure_context.failure_mode.value}: "
            f"{failure_context.error}"
        )
        return None
    
    def _repair_corrupted_manifest(self, failure_context: FailureContext) -> Any:
        """Attempt to repair a corrupted manifest."""
        recording_path = failure_context.context.get('recording_path')
        if not recording_path:
            raise ValueError("No recording path provided for manifest repair")
        
        recording_path = Path(recording_path)
        manifest_path = recording_path / "manifest.yaml"
        backup_path = recording_path / "manifest.yaml.backup"
        
        try:
            # Try to restore from backup if available
            if backup_path.exists():
                self.logger.info("Restoring manifest from backup")
                shutil.copy2(backup_path, manifest_path)
                return True
            
            # Try to reconstruct manifest from available files
            self.logger.info("Attempting to reconstruct manifest")
            return self._reconstruct_manifest(recording_path)
            
        except Exception as repair_error:
            self.logger.error(f"Manifest repair failed: {repair_error}")
            raise failure_context.error
    
    def _repair_corrupted_events(self, failure_context: FailureContext) -> Any:
        """Attempt to repair corrupted events file."""
        recording_path = failure_context.context.get('recording_path')
        if not recording_path:
            raise ValueError("No recording path provided for events repair")
        
        recording_path = Path(recording_path)
        
        try:
            # Try to recover partial events
            events_file = recording_path / "events.jsonl.zst"
            if not events_file.exists():
                events_file = recording_path / "events.jsonl"
            
            if events_file.exists():
                self.logger.info("Attempting to recover partial events")
                return self._recover_partial_events(events_file)
            
        except Exception as repair_error:
            self.logger.error(f"Events repair failed: {repair_error}")
            raise failure_context.error
    
    def _repair_partial_corruption(self, failure_context: FailureContext) -> Any:
        """Attempt to repair partial data corruption."""
        # This is a placeholder for more sophisticated corruption repair
        self.logger.warning("Partial corruption detected, attempting basic repair")
        return self._fallback_graceful(failure_context)
    
    def _reconstruct_manifest(self, recording_path: Path) -> bool:
        """Reconstruct manifest from available files."""
        try:
            from .integrity import create_integrity_checker
            
            integrity_checker = create_integrity_checker()
            
            # Basic manifest structure
            manifest = {
                "run_id": recording_path.name,
                "timestamp": datetime.utcnow().isoformat(),
                "schema_version": "1.1.0",
                "reconstructed": True,
                "file_hashes": {}
            }
            
            # Calculate hashes for all files
            for file_path in recording_path.rglob("*"):
                if file_path.is_file() and file_path.name != "manifest.yaml":
                    rel_path = file_path.relative_to(recording_path)
                    file_hash = integrity_checker.calculate_file_hash(file_path)
                    manifest["file_hashes"][str(rel_path)] = {
                        "hash": file_hash,
                        "size": file_path.stat().st_size,
                        "algorithm": integrity_checker.hash_algorithm
                    }
            
            # Write reconstructed manifest
            manifest_path = recording_path / "manifest.yaml"
            import yaml
            with open(manifest_path, 'w', encoding='utf-8') as f:
                yaml.dump(manifest, f, default_flow_style=False, sort_keys=True)
            
            self.logger.info(f"Successfully reconstructed manifest for {recording_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reconstruct manifest: {e}")
            return False
    
    def _recover_partial_events(self, events_file: Path) -> bool:
        """Recover partial events from corrupted file."""
        try:
            # Try to read as much as possible from the events file
            recovered_events = []
            
            if events_file.suffix == '.zst':
                try:
                    import zstandard as zstd
                    with open(events_file, 'rb') as f:
                        dctx = zstd.ZstdDecompressor()
                        content = dctx.decompress(f.read()).decode('utf-8')
                except ImportError:
                    self.logger.error("zstandard not available for recovery")
                    return False
            else:
                with open(events_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Try to parse each line, skipping corrupted ones
            lines = content.strip().split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    try:
                        import json
                        event = json.loads(line)
                        recovered_events.append(event)
                    except json.JSONDecodeError:
                        self.logger.warning(f"Skipping corrupted event on line {i + 1}")
                        continue
            
            # Write recovered events to a new file
            recovery_file = events_file.parent / f"{events_file.stem}_recovered{events_file.suffix}"
            
            if events_file.suffix == '.zst':
                try:
                    import zstandard as zstd
                    cctx = zstd.ZstdCompressor()
                    recovered_content = '\n'.join(json.dumps(event) for event in recovered_events)
                    compressed_data = cctx.compress(recovered_content.encode('utf-8'))
                    
                    with open(recovery_file, 'wb') as f:
                        f.write(compressed_data)
                except ImportError:
                    # Fall back to uncompressed
                    recovery_file = events_file.parent / f"{events_file.stem}_recovered.jsonl"
                    with open(recovery_file, 'w', encoding='utf-8') as f:
                        for event in recovered_events:
                            f.write(json.dumps(event) + '\n')
            else:
                with open(recovery_file, 'w', encoding='utf-8') as f:
                    for event in recovered_events:
                        f.write(json.dumps(event) + '\n')
            
            self.logger.info(f"Recovered {len(recovered_events)} events to {recovery_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Event recovery failed: {e}")
            return False
    
    def _get_default_strategies(self) -> Dict[FailureMode, RecoveryStrategy]:
        """Get default recovery strategies for each failure mode."""
        return {
            # Recording failures - mostly fail fast to avoid corrupted recordings
            FailureMode.RECORDING_INIT_FAILED: RecoveryStrategy.RETRY_WITH_BACKOFF,
            FailureMode.RECORDING_IO_ERROR: RecoveryStrategy.RETRY_WITH_BACKOFF,
            FailureMode.RECORDING_DISK_FULL: RecoveryStrategy.FAIL_FAST,
            FailureMode.RECORDING_PERMISSION_DENIED: RecoveryStrategy.FAIL_FAST,
            
            # Replay failures - try to recover or fall back gracefully
            FailureMode.REPLAY_RECORDING_NOT_FOUND: RecoveryStrategy.FAIL_FAST,
            FailureMode.REPLAY_INTEGRITY_CHECK_FAILED: RecoveryStrategy.REPAIR_AND_CONTINUE,
            FailureMode.REPLAY_MANIFEST_CORRUPTED: RecoveryStrategy.REPAIR_AND_CONTINUE,
            FailureMode.REPLAY_EVENTS_CORRUPTED: RecoveryStrategy.REPAIR_AND_CONTINUE,
            FailureMode.REPLAY_LOOKUP_MISMATCH: RecoveryStrategy.FALLBACK_GRACEFUL,
            FailureMode.REPLAY_INPUT_FINGERPRINT_MISMATCH: RecoveryStrategy.FALLBACK_GRACEFUL,
            
            # System failures
            FailureMode.SYSTEM_OUT_OF_MEMORY: RecoveryStrategy.FAIL_FAST,
            FailureMode.SYSTEM_DEPENDENCY_MISSING: RecoveryStrategy.FALLBACK_GRACEFUL,
            FailureMode.SYSTEM_PERMISSION_ERROR: RecoveryStrategy.FAIL_FAST,
            
            # Data corruption
            FailureMode.DATA_CORRUPTION_DETECTED: RecoveryStrategy.REPAIR_AND_CONTINUE,
            FailureMode.DATA_PARTIAL_CORRUPTION: RecoveryStrategy.REPAIR_AND_CONTINUE,
            FailureMode.DATA_SCHEMA_MISMATCH: RecoveryStrategy.FALLBACK_GRACEFUL,
        }
    
    def register_failure_callback(self, failure_mode: FailureMode, 
                                callback: Callable[[FailureContext], None]) -> None:
        """Register a callback to be executed when a specific failure occurs."""
        if failure_mode not in self.recovery_callbacks:
            self.recovery_callbacks[failure_mode] = []
        self.recovery_callbacks[failure_mode].append(callback)
    
    def _execute_failure_callbacks(self, failure_mode: FailureMode, 
                                 failure_context: FailureContext) -> None:
        """Execute registered callbacks for a failure mode."""
        callbacks = self.recovery_callbacks.get(failure_mode, [])
        for callback in callbacks:
            try:
                callback(failure_context)
            except Exception as callback_error:
                self.logger.error(f"Failure callback error: {callback_error}")
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get statistics about failures and recovery attempts."""
        total_failures = len(self.failure_history)
        if total_failures == 0:
            return {"total_failures": 0}
        
        recovery_attempted = sum(1 for f in self.failure_history if f.recovery_attempted)
        recovery_successful = sum(1 for f in self.failure_history if f.recovery_successful)
        
        failure_counts = {}
        for failure in self.failure_history:
            mode = failure.failure_mode.value
            failure_counts[mode] = failure_counts.get(mode, 0) + 1
        
        return {
            "total_failures": total_failures,
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_successful,
            "recovery_rate": recovery_successful / recovery_attempted if recovery_attempted > 0 else 0,
            "failure_counts": failure_counts,
            "most_recent_failure": self.failure_history[-1].timestamp.isoformat() if self.failure_history else None
        }


# Global failure handler instance
_global_failure_handler: Optional[FailureModeHandler] = None


def get_failure_handler() -> FailureModeHandler:
    """Get the global failure handler instance."""
    global _global_failure_handler
    if _global_failure_handler is None:
        _global_failure_handler = FailureModeHandler()
    return _global_failure_handler


def handle_failure(failure_mode: FailureMode, error: Exception, 
                  context: Dict[str, Any]) -> Any:
    """Convenience function to handle a failure using the global handler."""
    return get_failure_handler().handle_failure(failure_mode, error, context)