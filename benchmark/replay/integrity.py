"""
Replay System Integrity Checking

This module provides robust integrity checking, manifest validation, and failure mode
handling for the record-replay system. Following the adjustment plan for Week 1, Day 5:
"Harden: hashing, manifest integrity, failure modes."
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import yaml

logger = logging.getLogger(__name__)


class IntegrityError(Exception):
    """Raised when integrity checks fail."""
    pass


class ManifestValidationError(Exception):
    """Raised when manifest validation fails."""
    pass


class CorruptionDetectedError(Exception):
    """Raised when data corruption is detected."""
    pass


class IntegrityChecker:
    """
    Comprehensive integrity checking for replay recordings.
    
    Provides multiple hash algorithms, manifest validation, and corruption detection.
    """
    
    SUPPORTED_HASH_ALGORITHMS = ['blake3', 'blake2b', 'sha256', 'sha3_256']
    DEFAULT_HASH_ALGORITHM = 'blake3'
    
    def __init__(self, hash_algorithm: str = DEFAULT_HASH_ALGORITHM):
        """
        Initialize integrity checker.
        
        Args:
            hash_algorithm: Hash algorithm to use for integrity checking
        """
        if hash_algorithm not in self.SUPPORTED_HASH_ALGORITHMS:
            raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
        
        self.hash_algorithm = hash_algorithm
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate hash of a file using the configured algorithm.
        
        Args:
            file_path: Path to file to hash
            
        Returns:
            Hex digest of file hash
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            hasher = self._get_hasher()
            
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except IOError as e:
            raise IOError(f"Failed to read file {file_path}: {e}")
    
    def calculate_data_hash(self, data: Union[str, bytes]) -> str:
        """
        Calculate hash of data using the configured algorithm.
        
        Args:
            data: Data to hash (string or bytes)
            
        Returns:
            Hex digest of data hash
        """
        hasher = self._get_hasher()
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        hasher.update(data)
        return hasher.hexdigest()
    
    def verify_file_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """
        Verify file integrity against expected hash.
        
        Args:
            file_path: Path to file to verify
            expected_hash: Expected hash value
            
        Returns:
            True if integrity check passes
            
        Raises:
            IntegrityError: If integrity check fails
        """
        try:
            actual_hash = self.calculate_file_hash(file_path)
            
            if actual_hash != expected_hash:
                raise IntegrityError(
                    f"Integrity check failed for {file_path}: "
                    f"expected {expected_hash}, got {actual_hash}"
                )
            
            self.logger.debug(f"Integrity check passed for {file_path}")
            return True
            
        except FileNotFoundError:
            raise IntegrityError(f"File not found during integrity check: {file_path}")
        except IOError as e:
            raise IntegrityError(f"IO error during integrity check: {e}")
    
    def verify_manifest_integrity(self, manifest_path: Path) -> Dict[str, Any]:
        """
        Verify and load manifest with comprehensive validation.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            Validated manifest data
            
        Raises:
            ManifestValidationError: If manifest validation fails
        """
        if not manifest_path.exists():
            raise ManifestValidationError(f"Manifest file not found: {manifest_path}")
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = yaml.safe_load(f)
            
            # Validate manifest structure
            self._validate_manifest_structure(manifest)
            
            # Verify manifest self-integrity
            self._verify_manifest_self_integrity(manifest_path, manifest)
            
            return manifest
            
        except yaml.YAMLError as e:
            raise ManifestValidationError(f"Invalid YAML in manifest: {e}")
        except Exception as e:
            raise ManifestValidationError(f"Manifest validation failed: {e}")
    
    def verify_recording_integrity(self, recording_path: Path) -> Dict[str, Any]:
        """
        Comprehensive integrity check of entire recording.
        
        Args:
            recording_path: Path to recording directory
            
        Returns:
            Integrity report with detailed results
            
        Raises:
            IntegrityError: If any integrity check fails
        """
        report = {
            "recording_path": str(recording_path),
            "timestamp": datetime.utcnow().isoformat(),
            "hash_algorithm": self.hash_algorithm,
            "files_checked": 0,
            "files_passed": 0,
            "files_failed": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Load and validate manifest
            manifest_path = recording_path / "manifest.yaml"
            manifest = self.verify_manifest_integrity(manifest_path)
            report["manifest_valid"] = True
            
            # Check all files referenced in manifest
            file_hashes = manifest.get("file_hashes", {})
            
            for filename, hash_info in file_hashes.items():
                file_path = recording_path / filename
                report["files_checked"] += 1
                
                try:
                    # Extract hash from either string or dict format
                    if isinstance(hash_info, str):
                        expected_hash = hash_info
                    elif isinstance(hash_info, dict):
                        expected_hash = hash_info.get('hash')
                    else:
                        raise IntegrityError(f"Invalid hash format for {filename}")
                    
                    self.verify_file_integrity(file_path, expected_hash)
                    report["files_passed"] += 1
                    
                except IntegrityError as e:
                    report["files_failed"] += 1
                    report["errors"].append(str(e))
            
            # Check for orphaned files (files not in manifest)
            self._check_orphaned_files(recording_path, manifest, report)
            
            # Validate event stream integrity
            self._validate_event_stream_integrity(recording_path, manifest, report)
            
            # Overall success determination
            report["success"] = (report["files_failed"] == 0 and 
                               len(report["errors"]) == 0)
            
            return report
            
        except Exception as e:
            report["success"] = False
            report["errors"].append(f"Critical error during integrity check: {e}")
            return report
    
    def _get_hasher(self):
        """Get hasher instance for configured algorithm."""
        import hashlib
        
        if self.hash_algorithm == 'blake3':
            try:
                return hashlib.blake3()
            except AttributeError:
                # Fallback if blake3 not available
                self.logger.warning("BLAKE3 not available, falling back to BLAKE2b")
                return hashlib.blake2b()
        elif self.hash_algorithm == 'blake2b':
            return hashlib.blake2b()
        elif self.hash_algorithm == 'sha256':
            return hashlib.sha256()
        elif self.hash_algorithm == 'sha3_256':
            return hashlib.sha3_256()
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")
    
    def _validate_manifest_structure(self, manifest: Dict[str, Any]) -> None:
        """Validate manifest has required structure."""
        required_fields = ['run_id', 'timestamp', 'schema_version']
        
        for field in required_fields:
            if field not in manifest:
                raise ManifestValidationError(f"Missing required field: {field}")
        
        # Validate schema version compatibility
        schema_version = manifest.get('schema_version', '1.0.0')
        if not self._is_schema_compatible(schema_version):
            raise ManifestValidationError(f"Incompatible schema version: {schema_version}")
        
        # Validate file_hashes structure
        file_hashes = manifest.get('file_hashes', {})
        if not isinstance(file_hashes, dict):
            raise ManifestValidationError("file_hashes must be a dictionary")
        
        # Validate hash format (support both old string format and new dict format)
        for filename, hash_value in file_hashes.items():
            if isinstance(hash_value, str):
                # Old format: just the hash string
                if len(hash_value) < 32:
                    raise ManifestValidationError(f"Invalid hash for {filename}: {hash_value}")
            elif isinstance(hash_value, dict):
                # New format: dict with hash, size, algorithm
                if 'hash' not in hash_value or not isinstance(hash_value['hash'], str):
                    raise ManifestValidationError(f"Invalid hash structure for {filename}: {hash_value}")
                if len(hash_value['hash']) < 32:
                    raise ManifestValidationError(f"Invalid hash for {filename}: {hash_value['hash']}")
            else:
                raise ManifestValidationError(f"Invalid hash format for {filename}: {hash_value}")
    
    def _verify_manifest_self_integrity(self, manifest_path: Path, manifest: Dict[str, Any]) -> None:
        """Verify manifest's own integrity if self-hash is present."""
        manifest_hash = manifest.get('manifest_hash')
        if manifest_hash:
            # Calculate hash of manifest content (excluding the hash field itself)
            manifest_copy = manifest.copy()
            manifest_copy.pop('manifest_hash', None)
            
            manifest_content = yaml.dump(manifest_copy, sort_keys=True)
            actual_hash = self.calculate_data_hash(manifest_content)
            
            if actual_hash != manifest_hash:
                raise ManifestValidationError(
                    f"Manifest self-integrity check failed: "
                    f"expected {manifest_hash}, got {actual_hash}"
                )
    
    def _is_schema_compatible(self, schema_version: str) -> bool:
        """Check if schema version is compatible."""
        # Simple version compatibility check
        try:
            major, minor, patch = map(int, schema_version.split('.'))
            # Compatible with 1.x.x versions
            return major == 1
        except (ValueError, AttributeError):
            return False
    
    def _check_orphaned_files(self, recording_path: Path, manifest: Dict[str, Any], 
                            report: Dict[str, Any]) -> None:
        """Check for files not referenced in manifest."""
        file_hashes = manifest.get('file_hashes', {})
        manifest_files = set(file_hashes.keys())
        
        # Find all files in recording directory
        actual_files = set()
        for file_path in recording_path.rglob('*'):
            if file_path.is_file() and file_path.name != 'manifest.yaml':
                rel_path = file_path.relative_to(recording_path)
                actual_files.add(str(rel_path))
        
        # Check for orphaned files
        orphaned_files = actual_files - manifest_files
        if orphaned_files:
            report["warnings"].append(f"Orphaned files found: {list(orphaned_files)}")
        
        # Check for missing files
        missing_files = manifest_files - actual_files
        if missing_files:
            report["errors"].append(f"Missing files: {list(missing_files)}")
    
    def _validate_event_stream_integrity(self, recording_path: Path, manifest: Dict[str, Any],
                                       report: Dict[str, Any]) -> None:
        """Validate event stream integrity and consistency."""
        events_file = recording_path / "events.jsonl.zst"
        if not events_file.exists():
            events_file = recording_path / "events.jsonl"
        
        if not events_file.exists():
            report["warnings"].append("No events file found")
            return
        
        try:
            # Load and validate events
            events = self._load_events_safely(events_file)
            
            # Validate event count
            expected_count = manifest.get('event_count')
            if expected_count is not None and len(events) != expected_count:
                report["errors"].append(
                    f"Event count mismatch: expected {expected_count}, got {len(events)}"
                )
            
            # Validate event sequence integrity
            self._validate_event_sequence(events, report)
            
        except Exception as e:
            report["errors"].append(f"Event stream validation failed: {e}")
    
    def _load_events_safely(self, events_file: Path) -> List[Dict[str, Any]]:
        """Safely load events from file with error handling."""
        events = []
        
        try:
            if events_file.suffix == '.zst':
                # Try to import zstandard
                try:
                    import zstandard as zstd
                    with open(events_file, 'rb') as f:
                        dctx = zstd.ZstdDecompressor()
                        content = dctx.decompress(f.read()).decode('utf-8')
                except ImportError:
                    raise ImportError("zstandard library required for compressed files")
            else:
                with open(events_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Parse JSONL
            for line_num, line in enumerate(content.strip().split('\n'), 1):
                if line.strip():
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON on line {line_num}: {e}")
            
            return events
            
        except Exception as e:
            raise IOError(f"Failed to load events from {events_file}: {e}")
    
    def _validate_event_sequence(self, events: List[Dict[str, Any]], 
                                report: Dict[str, Any]) -> None:
        """Validate event sequence for consistency."""
        if not events:
            return
        
        # Check for required fields in events
        required_event_fields = ['timestamp', 'event_type']
        
        for i, event in enumerate(events):
            for field in required_event_fields:
                if field not in event:
                    report["warnings"].append(
                        f"Event {i} missing required field: {field}"
                    )
        
        # Check timestamp ordering (should be monotonic)
        timestamps = []
        for event in events:
            if 'timestamp' in event:
                try:
                    # Parse ISO timestamp
                    ts = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    timestamps.append(ts)
                except (ValueError, AttributeError):
                    # Skip invalid timestamps
                    continue
        
        if len(timestamps) > 1:
            for i in range(1, len(timestamps)):
                if timestamps[i] < timestamps[i-1]:
                    report["warnings"].append(
                        f"Non-monotonic timestamp at event {i}"
                    )
                    break


def create_integrity_checker(hash_algorithm: str = 'blake3') -> IntegrityChecker:
    """
    Factory function to create an integrity checker.
    
    Args:
        hash_algorithm: Hash algorithm to use
        
    Returns:
        IntegrityChecker instance
    """
    return IntegrityChecker(hash_algorithm)


def verify_recording_quick(recording_path: Path) -> bool:
    """
    Quick integrity check for a recording (basic validation only).
    
    Args:
        recording_path: Path to recording directory
        
    Returns:
        True if basic integrity checks pass
    """
    try:
        checker = create_integrity_checker()
        
        # Check manifest exists and is valid
        manifest_path = recording_path / "manifest.yaml"
        manifest = checker.verify_manifest_integrity(manifest_path)
        
        # Check events file exists
        events_file = recording_path / "events.jsonl.zst"
        if not events_file.exists():
            events_file = recording_path / "events.jsonl"
        
        if not events_file.exists():
            return False
        
        # Quick hash check of events file
        file_hashes = manifest.get('file_hashes', {})
        events_filename = events_file.name
        
        if events_filename in file_hashes:
            checker.verify_file_integrity(events_file, file_hashes[events_filename])
        
        return True
        
    except Exception:
        return False


def verify_recording_comprehensive(recording_path: Path) -> Dict[str, Any]:
    """
    Comprehensive integrity check for a recording.
    
    Args:
        recording_path: Path to recording directory
        
    Returns:
        Detailed integrity report
    """
    checker = create_integrity_checker()
    return checker.verify_recording_integrity(recording_path)