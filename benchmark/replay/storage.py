"""
Storage Manager for Record-Replay Artifacts

Manages the storage, retrieval, and lifecycle of recording artifacts
following the ADR-009 storage format specification.
"""

import shutil
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .recorder import Recorder
from .player import Player


class StorageManager:
    """Manages record-replay artifact storage and lifecycle."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("artifacts")
        self.storage_path.mkdir(exist_ok=True)
    
    def list_recordings(self) -> List[Dict[str, Any]]:
        """
        List all available recordings with metadata.
        
        Returns:
            List of recording metadata dictionaries
        """
        recordings = []
        
        for run_dir in self.storage_path.iterdir():
            if not run_dir.is_dir():
                continue
                
            manifest_file = run_dir / "manifest.yaml"
            if not manifest_file.exists():
                continue
            
            try:
                with open(manifest_file, 'r') as f:
                    manifest = yaml.safe_load(f)
                
                # Add directory info
                manifest['run_dir'] = str(run_dir)
                manifest['size_mb'] = self._calculate_dir_size(run_dir) / (1024 * 1024)
                
                recordings.append(manifest)
                
            except Exception as e:
                print(f"Warning: Failed to read manifest for {run_dir}: {e}")
                continue
        
        # Sort by creation time (newest first)
        recordings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return recordings
    
    def get_recording_info(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific recording.
        
        Args:
            run_id: ID of the recording
            
        Returns:
            Recording metadata dictionary or None if not found
        """
        run_dir = self.storage_path / run_id
        if not run_dir.exists():
            return None
        
        manifest_file = run_dir / "manifest.yaml"
        if not manifest_file.exists():
            return None
        
        try:
            with open(manifest_file, 'r') as f:
                manifest = yaml.safe_load(f)
            
            # Add additional info
            manifest['run_dir'] = str(run_dir)
            manifest['size_mb'] = self._calculate_dir_size(run_dir) / (1024 * 1024)
            
            # Count files in subdirectories
            manifest['file_counts'] = {
                'inputs': len(list((run_dir / "inputs").glob("*"))) if (run_dir / "inputs").exists() else 0,
                'outputs': len(list((run_dir / "outputs").glob("*"))) if (run_dir / "outputs").exists() else 0,
                'diffs': len(list((run_dir / "diffs").glob("*"))) if (run_dir / "diffs").exists() else 0,
            }
            
            return manifest
            
        except Exception as e:
            print(f"Error reading recording info for {run_id}: {e}")
            return None
    
    def delete_recording(self, run_id: str) -> bool:
        """
        Delete a recording and all its artifacts.
        
        Args:
            run_id: ID of the recording to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        run_dir = self.storage_path / run_id
        if not run_dir.exists():
            return False
        
        try:
            shutil.rmtree(run_dir)
            return True
        except Exception as e:
            print(f"Error deleting recording {run_id}: {e}")
            return False
    
    def export_recording(self, run_id: str, export_path: Path) -> bool:
        """
        Export a recording to a tar.gz archive.
        
        Args:
            run_id: ID of the recording to export
            export_path: Path where to save the exported archive
            
        Returns:
            True if exported successfully, False otherwise
        """
        run_dir = self.storage_path / run_id
        if not run_dir.exists():
            return False
        
        try:
            import tarfile
            
            with tarfile.open(export_path, "w:gz") as tar:
                tar.add(run_dir, arcname=run_id)
            
            return True
            
        except Exception as e:
            print(f"Error exporting recording {run_id}: {e}")
            return False
    
    def import_recording(self, archive_path: Path) -> Optional[str]:
        """
        Import a recording from a tar.gz archive.
        
        Args:
            archive_path: Path to the archive to import
            
        Returns:
            Run ID of the imported recording or None if failed
        """
        try:
            import tarfile
            
            with tarfile.open(archive_path, "r:gz") as tar:
                # Extract to temporary location first
                temp_dir = self.storage_path / "temp_import"
                temp_dir.mkdir(exist_ok=True)
                
                try:
                    tar.extractall(temp_dir)
                    
                    # Find the run directory
                    extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
                    if not extracted_dirs:
                        return None
                    
                    run_dir = extracted_dirs[0]
                    run_id = run_dir.name
                    
                    # Move to final location
                    final_dir = self.storage_path / run_id
                    if final_dir.exists():
                        # Generate unique name
                        import uuid
                        run_id = f"{run_id}_{uuid.uuid4().hex[:8]}"
                        final_dir = self.storage_path / run_id
                    
                    shutil.move(str(run_dir), str(final_dir))
                    
                    return run_id
                    
                finally:
                    # Clean up temp directory
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
            
        except Exception as e:
            print(f"Error importing recording from {archive_path}: {e}")
            return None
    
    def cleanup_old_recordings(self, keep_count: int = 10, max_age_days: int = 30) -> int:
        """
        Clean up old recordings based on count and age limits.
        
        Args:
            keep_count: Maximum number of recordings to keep
            max_age_days: Maximum age in days for recordings
            
        Returns:
            Number of recordings deleted
        """
        recordings = self.list_recordings()
        deleted_count = 0
        
        # Delete recordings beyond keep_count
        if len(recordings) > keep_count:
            for recording in recordings[keep_count:]:
                run_id = Path(recording['run_dir']).name
                if self.delete_recording(run_id):
                    deleted_count += 1
        
        # Delete recordings older than max_age_days
        cutoff_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=max_age_days)
        
        for recording in recordings:
            try:
                created_at = datetime.fromisoformat(recording.get('created_at', ''))
                if created_at < cutoff_date:
                    run_id = Path(recording['run_dir']).name
                    if self.delete_recording(run_id):
                        deleted_count += 1
            except:
                continue  # Skip recordings with invalid dates
        
        return deleted_count
    
    def verify_recording_integrity(self, run_id: str) -> Dict[str, Any]:
        """
        Verify the integrity of a recording.
        
        Args:
            run_id: ID of the recording to verify
            
        Returns:
            Dictionary with verification results
        """
        result = {
            'run_id': run_id,
            'valid': False,
            'errors': [],
            'warnings': []
        }
        
        run_dir = self.storage_path / run_id
        if not run_dir.exists():
            result['errors'].append(f"Recording directory not found: {run_dir}")
            return result
        
        # Check manifest exists
        manifest_file = run_dir / "manifest.yaml"
        if not manifest_file.exists():
            result['errors'].append("manifest.yaml not found")
            return result
        
        try:
            with open(manifest_file, 'r') as f:
                manifest = yaml.safe_load(f)
        except Exception as e:
            result['errors'].append(f"Failed to parse manifest.yaml: {e}")
            return result
        
        # Verify file hashes
        file_hashes = manifest.get('file_hashes', {})
        for filename, expected_hash in file_hashes.items():
            file_path = run_dir / filename
            if not file_path.exists():
                result['errors'].append(f"Referenced file not found: {filename}")
                continue
            
            try:
                import hashlib
                with open(file_path, 'rb') as f:
                    content = f.read()
                    actual_hash = hashlib.blake2b(content).hexdigest()
                    
                if actual_hash != expected_hash:
                    result['errors'].append(
                        f"Hash mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
                    )
            except Exception as e:
                result['errors'].append(f"Failed to verify hash for {filename}: {e}")
        
        # Check required directories
        required_dirs = ['inputs', 'outputs', 'diffs']
        for dir_name in required_dirs:
            dir_path = run_dir / dir_name
            if not dir_path.exists():
                result['warnings'].append(f"Directory not found: {dir_name}")
        
        result['valid'] = len(result['errors']) == 0
        return result
    
    def _calculate_dir_size(self, directory: Path) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except:
            pass  # Ignore permission errors
        return total_size
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get overall storage statistics."""
        recordings = self.list_recordings()
        
        total_size = sum(r.get('size_mb', 0) for r in recordings)
        
        return {
            'total_recordings': len(recordings),
            'total_size_mb': total_size,
            'storage_path': str(self.storage_path),
            'oldest_recording': recordings[-1].get('created_at') if recordings else None,
            'newest_recording': recordings[0].get('created_at') if recordings else None
        }