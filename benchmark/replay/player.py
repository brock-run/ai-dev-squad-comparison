"""
Enhanced Replay Engine with Streaming Support and Telemetry Integration

Replays recorded sessions by substituting IO edges with recorded outputs,
with enhanced support for streaming data and comprehensive telemetry.

Phase 1: Enhanced Telemetry Integration
"""

import json
import gzip
import zstandard as zstd
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Iterator, AsyncIterator
from datetime import datetime
import asyncio
import logging

import yaml

# Import foundation components
from common.replay import (
    get_ordering_manager,
    create_ordered_event,
    get_determinism_manager,
    get_redaction_filter,
    create_io_key
)

# Import streaming support
from common.replay.streaming import (
    StreamToken,
    StreamReplay,
    analyze_stream_timing,
    merge_stream_chunks
)

# Import telemetry components
try:
    from common.telemetry.schema import (
        EventType,
        ReplayEvent,
        StreamingLLMEvent,
        create_replay_start_event,
        create_replay_mismatch_event,
        create_streaming_llm_start_event,
        create_streaming_llm_chunk_event,
        create_streaming_llm_finish_event
    )
    from common.telemetry.logger import get_telemetry_logger
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    logging.warning("Telemetry modules not available - using basic logging")

from typing import Callable, TypeVar
from functools import wraps

T = TypeVar('T')
logger = logging.getLogger(__name__)


class ReplayMismatchError(Exception):
    """Raised when replay encounters a mismatch with recorded data."""
    pass


class EnhancedPlayer:
    """Enhanced replay engine with streaming support and telemetry integration."""
    
    def __init__(self, 
                 storage_path: Optional[Path] = None,
                 replay_mode: str = "strict",
                 enable_streaming: bool = True):
        """
        Initialize enhanced player.
        
        Args:
            storage_path: Path to stored recordings
            replay_mode: Replay mode (strict, warn, hybrid)
            enable_streaming: Enable streaming replay support
        """
        self.storage_path = storage_path or Path("artifacts")
        self.replay_mode = replay_mode
        self.enable_streaming = enable_streaming
        
        # Recording data
        self._recorded_ios: Dict[str, Dict[str, Any]] = {}
        self._recorded_streams: Dict[str, List[StreamToken]] = {}
        self._current_run_id: Optional[str] = None
        self._recording_manifest: Optional[Dict[str, Any]] = None
        
        # Replay state
        self._replay_session_id: Optional[str] = None
        self._call_counters: Dict[str, int] = {}
        self._mismatch_count = 0
        self._total_replays = 0
        
        # Telemetry integration
        self._telemetry_logger = get_telemetry_logger() if TELEMETRY_AVAILABLE else None
        self._ordering_manager = get_ordering_manager()
        self._redaction_filter = get_redaction_filter()
        
        logger.info(f"Initialized enhanced player: mode={replay_mode}, streaming={enable_streaming}")
        
    def load_recording(self, run_id: str) -> bool:
        """
        Load a recorded session for replay.
        
        Args:
            run_id: ID of the recorded run to load
            
        Returns:
            True if recording loaded successfully, False otherwise
        """
        run_dir = self.storage_path / run_id
        if not run_dir.exists():
            return False
        
        # Verify manifest and integrity using enhanced integrity checker
        try:
            from .integrity import create_integrity_checker, IntegrityError, ManifestValidationError
            
            integrity_checker = create_integrity_checker()
            manifest_file = run_dir / "manifest.yaml"
            
            # Comprehensive manifest validation
            manifest = integrity_checker.verify_manifest_integrity(manifest_file)
            
            # Verify events file integrity
            events_file = run_dir / "events.jsonl.zst"
            if not events_file.exists():
                events_file = run_dir / "events.jsonl"
            
            if events_file.exists():
                file_hashes = manifest.get('file_hashes', {})
                events_filename = events_file.name
                
                if events_filename in file_hashes:
                    hash_info = file_hashes[events_filename]
                    # Extract hash from either string or dict format
                    if isinstance(hash_info, str):
                        expected_hash = hash_info
                    elif isinstance(hash_info, dict):
                        expected_hash = hash_info.get('hash')
                    else:
                        logger.warning(f"Invalid hash format for {events_filename}")
                        expected_hash = None
                    
                    if expected_hash:
                        integrity_checker.verify_file_integrity(events_file, expected_hash)
                else:
                    logger.warning(f"No hash found for events file: {events_filename}")
            
        except (IntegrityError, ManifestValidationError) as e:
            # Use failure mode handler for integrity failures
            try:
                from .failure_modes import handle_failure, FailureMode
                
                if "Integrity check failed" in str(e):
                    failure_mode = FailureMode.REPLAY_INTEGRITY_CHECK_FAILED
                else:
                    failure_mode = FailureMode.REPLAY_MANIFEST_CORRUPTED
                
                context = {
                    'recording_path': run_dir,
                    'run_id': run_id,
                    'error_details': str(e)
                }
                
                # Attempt recovery
                handle_failure(failure_mode, e, context)
                
                # If recovery succeeded, try loading again
                manifest = integrity_checker.verify_manifest_integrity(manifest_file)
                
            except ImportError:
                logger.error(f"Integrity check failed for recording {run_id}: {e}")
                return False
            except Exception:
                logger.error(f"Integrity check failed for recording {run_id}: {e}")
                return False
                
        except ImportError:
            # Fallback to basic integrity checking if enhanced checker not available
            try:
                from .failure_modes import handle_failure, FailureMode
                
                context = {
                    'recording_path': run_dir,
                    'run_id': run_id,
                    'fallback_reason': 'enhanced_checker_unavailable'
                }
                
                handle_failure(FailureMode.SYSTEM_DEPENDENCY_MISSING, 
                             ImportError("Enhanced integrity checker not available"), context)
                
            except ImportError:
                pass  # Failure handler also not available
            
            logger.warning("Enhanced integrity checker not available, using basic validation")
            manifest_file = run_dir / "manifest.yaml"
            if not manifest_file.exists():
                return False
            
            with open(manifest_file, 'r') as f:
                manifest = yaml.safe_load(f)
                
        except Exception as e:
            # Handle other unexpected errors
            try:
                from .failure_modes import handle_failure, FailureMode
                
                context = {
                    'recording_path': run_dir,
                    'run_id': run_id,
                    'operation': 'load_recording'
                }
                
                handle_failure(FailureMode.REPLAY_RECORDING_NOT_FOUND, e, context)
                
            except ImportError:
                pass  # Failure handler not available
            
            logger.error(f"Failed to load recording {run_id}: {e}")
            return False
        
        # Load recorded IO edges and streaming data
        self._recorded_ios.clear()
        self._recorded_streams.clear()
        
        # Find events file
        events_file = run_dir / "events.jsonl.zst"
        if not events_file.exists():
            events_file = run_dir / "events.jsonl"
        
        if events_file.exists():
            self._load_events_from_file(events_file)
        
        # Load streaming chunks if available
        chunks_file = run_dir / f"{run_id}_chunks.jsonl"
        if not chunks_file.exists():
            chunks_file = run_dir / "chunks.jsonl"
        
        if chunks_file.exists() and self.enable_streaming:
            self._load_streaming_chunks(chunks_file)
        
        # Store manifest for reference
        self._recording_manifest = manifest
        self._current_run_id = run_id
        
        logger.info(f"Loaded recording: {run_id}")
        logger.info(f"IO edges: {len(self._recorded_ios)}, Streams: {len(self._recorded_streams)}")
        
        return True
    
    def start_replay(self, 
                    new_run_id: Optional[str] = None,
                    session_id: Optional[str] = None,
                    task_id: Optional[str] = None) -> str:
        """
        Start replay mode with enhanced telemetry and session tracking.
        
        Args:
            new_run_id: Optional new run ID, generated if not provided
            session_id: Session ID for telemetry correlation
            task_id: Task ID for telemetry correlation
            
        Returns:
            The replay run ID
        """
        if not self._current_run_id:
            raise ValueError("No recording loaded. Call load_recording() first.")
        
        if not new_run_id:
            import uuid
            new_run_id = f"replay_{self._current_run_id}_{uuid.uuid4().hex[:8]}"
        
        self._replay_session_id = new_run_id
        
        # Reset counters
        self._call_counters.clear()
        self._mismatch_count = 0
        self._total_replays = 0
        
        # Create replay directory
        replay_dir = self.storage_path / new_run_id
        replay_dir.mkdir(exist_ok=True)
        
        # Create telemetry event for replay start
        if self._telemetry_logger:
            replay_start_event = create_replay_start_event(
                recording_session=self._current_run_id,
                replay_mode=self.replay_mode,
                agent_id="player",
                session_id=session_id,
                task_id=task_id,
                original_manifest=self._recording_manifest,
                streaming_enabled=self.enable_streaming
            )
            self._telemetry_logger.log_event(replay_start_event)
        
        logger.info(f"Started replay session: {new_run_id}")
        logger.info(f"Original recording: {self._current_run_id}")
        logger.info(f"Replay mode: {self.replay_mode}")
        
        return new_run_id
    
    def get_recorded_output(self, 
                          io_type: str, 
                          tool_name: str, 
                          input_data: Dict[str, Any], 
                          call_index: int, 
                          agent_id: str = "",
                          session_id: Optional[str] = None,
                          task_id: Optional[str] = None) -> Tuple[bool, Any]:
        """
        Get recorded output for an IO edge with enhanced matching and telemetry.
        
        Args:
            io_type: Type of IO operation
            tool_name: Name of the tool/model
            input_data: Input parameters to match
            call_index: Sequential call index
            agent_id: Agent ID for context
            session_id: Session ID for telemetry
            task_id: Task ID for telemetry
            
        Returns:
            Tuple of (match_found, output_data)
        """
        self._total_replays += 1
        
        # Create IO key using foundation components
        io_key = create_io_key(
            event_type=io_type,
            adapter="player",  # Would be passed from caller
            agent_id=agent_id,
            tool_name=tool_name,
            call_index=call_index,
            input_data=input_data
        )
        
        lookup_key = io_key.to_string()
        
        if lookup_key not in self._recorded_ios:
            self._handle_replay_mismatch(
                "missing_recording",
                lookup_key,
                f"No recorded IO found for key: {lookup_key}",
                session_id=session_id,
                task_id=task_id
            )
            return False, None
        
        recorded_io = self._recorded_ios[lookup_key]
        
        # Verify input fingerprint matches
        recorded_fingerprint = recorded_io.get('input_fingerprint')
        actual_fingerprint = io_key.input_fingerprint
        
        if recorded_fingerprint != actual_fingerprint:
            mismatch_details = {
                "expected_fingerprint": recorded_fingerprint,
                "actual_fingerprint": actual_fingerprint,
                "input_diff": self._compute_input_diff(
                    recorded_io.get('input_data', {}),
                    input_data
                )
            }
            
            self._handle_replay_mismatch(
                "fingerprint_mismatch",
                lookup_key,
                f"Input fingerprint mismatch for {lookup_key}",
                mismatch_details,
                session_id=session_id,
                task_id=task_id
            )
            
            # In hybrid mode, try to continue with recorded output
            if self.replay_mode == "hybrid":
                logger.warning(f"Hybrid mode: using recorded output despite mismatch")
                return True, recorded_io.get('output_data')
            
            return False, None
        
        # Log successful match
        self._log_replay_success(lookup_key, session_id=session_id, task_id=task_id)
        
        return True, recorded_io.get('output_data')
    
    def get_stream_tokens(self, stream_id: str) -> Optional[List[StreamToken]]:
        """
        Get recorded streaming tokens for a stream ID.
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            List of StreamToken instances or None if not found
        """
        if not self.enable_streaming:
            return None
        
        return self._recorded_streams.get(stream_id)
    
    def replay_stream(self, 
                     stream_id: str,
                     preserve_timing: bool = True) -> Optional[StreamReplay]:
        """
        Create a stream replay instance for recorded streaming data.
        
        Args:
            stream_id: Stream identifier
            preserve_timing: Whether to preserve original timing
            
        Returns:
            StreamReplay instance or None if stream not found
        """
        tokens = self.get_stream_tokens(stream_id)
        if not tokens:
            return None
        
        replay = StreamReplay(tokens)
        replay.set_timing_mode(preserve_timing)
        return replay
    
    def replay_streaming_llm_call(self,
                                 prompt: str,
                                 model: str,
                                 agent_id: str,
                                 call_index: int,
                                 session_id: Optional[str] = None,
                                 task_id: Optional[str] = None) -> Optional[Iterator[str]]:
        """
        Replay a streaming LLM call.
        
        Args:
            prompt: Original prompt
            model: Model identifier
            agent_id: Agent identifier
            call_index: Call index
            session_id: Session ID for telemetry
            task_id: Task ID for telemetry
            
        Returns:
            Iterator of content chunks or None if not found
        """
        if not self.enable_streaming:
            return None
        
        # Create stream ID (same logic as recorder)
        stream_id = f"llm_stream_{agent_id}_{call_index}_{hash(prompt) % 10000}"
        
        tokens = self.get_stream_tokens(stream_id)
        if not tokens:
            logger.warning(f"No recorded stream found for ID: {stream_id}")
            return None
        
        # Create telemetry events for stream replay
        if self._telemetry_logger:
            start_event = create_streaming_llm_start_event(
                prompt=prompt,
                model=model,
                agent_id=agent_id,
                stream_id=stream_id,
                session_id=session_id,
                task_id=task_id,
                recording_session=self._current_run_id,
                replay_mode=self.replay_mode
            )
            self._telemetry_logger.log_event(start_event)
        
        # Create replay iterator
        replay = StreamReplay(tokens)
        
        def stream_generator():
            chunk_count = 0
            for token in replay.replay_sync():
                if not token.is_final:
                    # Log chunk event
                    if self._telemetry_logger:
                        chunk_event = create_streaming_llm_chunk_event(
                            chunk_content=token.content,
                            stream_id=stream_id,
                            chunk_index=token.index,
                            agent_id=agent_id,
                            session_id=session_id,
                            task_id=task_id,
                            recording_session=self._current_run_id,
                            replay_mode=self.replay_mode
                        )
                        self._telemetry_logger.log_event(chunk_event)
                    
                    chunk_count += 1
                    yield token.content
            
            # Log finish event
            if self._telemetry_logger:
                finish_event = create_streaming_llm_finish_event(
                    stream_id=stream_id,
                    total_chunks=chunk_count,
                    total_tokens=len(tokens),
                    agent_id=agent_id,
                    session_id=session_id,
                    task_id=task_id,
                    recording_session=self._current_run_id,
                    replay_mode=self.replay_mode
                )
                self._telemetry_logger.log_event(finish_event)
        
        return stream_generator()
    
    async def replay_streaming_llm_call_async(self,
                                            prompt: str,
                                            model: str,
                                            agent_id: str,
                                            call_index: int,
                                            session_id: Optional[str] = None,
                                            task_id: Optional[str] = None) -> Optional[AsyncIterator[str]]:
        """
        Async replay of a streaming LLM call.
        
        Args:
            prompt: Original prompt
            model: Model identifier
            agent_id: Agent identifier
            call_index: Call index
            session_id: Session ID for telemetry
            task_id: Task ID for telemetry
            
        Returns:
            Async iterator of content chunks or None if not found
        """
        if not self.enable_streaming:
            return None
        
        # Create stream ID (same logic as recorder)
        stream_id = f"llm_stream_{agent_id}_{call_index}_{hash(prompt) % 10000}"
        
        tokens = self.get_stream_tokens(stream_id)
        if not tokens:
            logger.warning(f"No recorded stream found for ID: {stream_id}")
            return None
        
        # Create telemetry events for stream replay
        if self._telemetry_logger:
            start_event = create_streaming_llm_start_event(
                prompt=prompt,
                model=model,
                agent_id=agent_id,
                stream_id=stream_id,
                session_id=session_id,
                task_id=task_id,
                recording_session=self._current_run_id,
                replay_mode=self.replay_mode
            )
            self._telemetry_logger.log_event(start_event)
        
        # Create replay iterator
        replay = StreamReplay(tokens)
        
        async def async_stream_generator():
            chunk_count = 0
            async for token in replay.replay_async():
                if not token.is_final:
                    # Log chunk event
                    if self._telemetry_logger:
                        chunk_event = create_streaming_llm_chunk_event(
                            chunk_content=token.content,
                            stream_id=stream_id,
                            chunk_index=token.index,
                            agent_id=agent_id,
                            session_id=session_id,
                            task_id=task_id,
                            recording_session=self._current_run_id,
                            replay_mode=self.replay_mode
                        )
                        self._telemetry_logger.log_event(chunk_event)
                    
                    chunk_count += 1
                    yield token.content
            
            # Log finish event
            if self._telemetry_logger:
                finish_event = create_streaming_llm_finish_event(
                    stream_id=stream_id,
                    total_chunks=chunk_count,
                    total_tokens=len(tokens),
                    agent_id=agent_id,
                    session_id=session_id,
                    task_id=task_id,
                    recording_session=self._current_run_id,
                    replay_mode=self.replay_mode
                )
                self._telemetry_logger.log_event(finish_event)
        
        return async_stream_generator()
    
    def replay_io_edge(self, io_type: str, tool_name: str, input_data: Dict[str, Any],
                      call_index: int, agent_id: str = "") -> Any:
        """
        Replay an IO edge, returning recorded output or raising error on mismatch.
        
        This is the main method adapters should call during replay.
        """
        match_found, output_data = self.get_recorded_output(
            io_type, tool_name, input_data, call_index, agent_id
        )
        
        if not match_found:
            raise ReplayMismatchError(
                f"No matching recorded output found for {io_type} call to {tool_name} "
                f"(call_index={call_index}, agent_id={agent_id})"
            )
        
        return output_data
    
    def _load_events_from_file(self, events_file: Path):
        """Load recorded IO events from compressed JSONL file."""
        try:
            # Handle both compressed and uncompressed files
            if events_file.suffix == '.zst':
                import zstandard as zstd
                with open(events_file, 'rb') as f:
                    dctx = zstd.ZstdDecompressor()
                    content = dctx.decompress(f.read()).decode('utf-8')
            else:
                with open(events_file, 'r') as f:
                    content = f.read()
            
            # Parse JSONL
            for line in content.strip().split('\n'):
                if not line.strip():
                    continue
                
                try:
                    event_data = json.loads(line)
                    
                    # Only process recording notes with IO data
                    if (event_data.get('event_type') == 'recording.note' and 
                        event_data.get('replay_mode') == 'record' and
                        event_data.get('lookup_key')):
                        
                        lookup_key = event_data['lookup_key']
                        self._recorded_ios[lookup_key] = {
                            'input_fingerprint': event_data.get('input_fingerprint'),
                            'input_data': event_data.get('input_data', {}),
                            'output_data': event_data.get('output_data', {}),
                            'io_type': event_data.get('io_type'),
                            'call_index': event_data.get('call_index')
                        }
                        
                except json.JSONDecodeError:
                    continue  # Skip malformed lines
                    
        except Exception as e:
            logger.warning(f"Failed to load events from {events_file}: {e}")
    
    def _load_streaming_chunks(self, chunks_file: Path):
        """Load recorded streaming chunks from file."""
        try:
            # Handle both compressed and uncompressed files
            if chunks_file.suffix == '.zst':
                with open(chunks_file, 'rb') as f:
                    dctx = zstd.ZstdDecompressor()
                    content = dctx.decompress(f.read()).decode('utf-8')
            else:
                with open(chunks_file, 'r') as f:
                    content = f.read()
            
            # Parse JSONL chunks
            for line in content.strip().split('\n'):
                if not line.strip():
                    continue
                
                try:
                    chunk_data = json.loads(line)
                    
                    # Create StreamToken from chunk data
                    token = StreamToken.from_dict(chunk_data)
                    stream_id = token.metadata.get('stream_id', chunk_data.get('stream_id'))
                    
                    if stream_id:
                        if stream_id not in self._recorded_streams:
                            self._recorded_streams[stream_id] = []
                        self._recorded_streams[stream_id].append(token)
                        
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse chunk: {e}")
                    continue
            
            # Sort tokens by index within each stream
            for stream_id in self._recorded_streams:
                self._recorded_streams[stream_id].sort(key=lambda t: t.index)
                    
        except Exception as e:
            logger.warning(f"Failed to load streaming chunks from {chunks_file}: {e}")
    
    def _handle_replay_mismatch(self,
                               mismatch_type: str,
                               io_key: str,
                               message: str,
                               mismatch_details: Optional[Dict[str, Any]] = None,
                               session_id: Optional[str] = None,
                               task_id: Optional[str] = None):
        """Handle replay mismatch with appropriate logging and telemetry."""
        self._mismatch_count += 1
        
        # Create telemetry event for mismatch
        if self._telemetry_logger:
            mismatch_event = create_replay_mismatch_event(
                original_event_id="unknown",  # Would need to be tracked
                mismatch_details=mismatch_details or {"type": mismatch_type, "message": message},
                agent_id="player",
                io_key=io_key,
                session_id=session_id,
                task_id=task_id
            )
            self._telemetry_logger.log_event(mismatch_event)
        
        # Log based on replay mode
        if self.replay_mode == "strict":
            logger.error(f"Replay mismatch ({mismatch_type}): {message}")
        elif self.replay_mode == "warn":
            logger.warning(f"Replay mismatch ({mismatch_type}): {message}")
        elif self.replay_mode == "hybrid":
            logger.info(f"Replay mismatch ({mismatch_type}): {message} - continuing in hybrid mode")
    
    def _log_replay_success(self,
                           io_key: str,
                           session_id: Optional[str] = None,
                           task_id: Optional[str] = None):
        """Log successful replay match."""
        if self._telemetry_logger:
            success_event = ReplayEvent(
                event_type=EventType.REPLAY_START,  # Would need REPLAY_MATCH event type
                source="player",
                agent_id="player",
                session_id=session_id,
                task_id=task_id,
                recording_session=self._current_run_id,
                replay_status="matched",
                io_key=io_key,
                data={"match_successful": True}
            )
            self._telemetry_logger.log_event(success_event)
        
        logger.debug(f"Successfully matched IO for key: {io_key}")
    
    def _compute_input_diff(self, recorded_input: Dict[str, Any], actual_input: Dict[str, Any]) -> Dict[str, Any]:
        """Compute differences between recorded and actual inputs."""
        diff = {
            "added_keys": [],
            "removed_keys": [],
            "changed_values": {}
        }
        
        recorded_keys = set(recorded_input.keys())
        actual_keys = set(actual_input.keys())
        
        diff["added_keys"] = list(actual_keys - recorded_keys)
        diff["removed_keys"] = list(recorded_keys - actual_keys)
        
        for key in recorded_keys & actual_keys:
            if recorded_input[key] != actual_input[key]:
                diff["changed_values"][key] = {
                    "recorded": recorded_input[key],
                    "actual": actual_input[key]
                }
        
        return diff
    
    def get_replay_statistics(self) -> Dict[str, Any]:
        """Get replay statistics and metrics."""
        return {
            "total_replays": self._total_replays,
            "mismatch_count": self._mismatch_count,
            "success_rate": (
                (self._total_replays - self._mismatch_count) / self._total_replays
                if self._total_replays > 0 else 0.0
            ),
            "loaded_ios": len(self._recorded_ios),
            "loaded_streams": len(self._recorded_streams),
            "replay_mode": self.replay_mode,
            "streaming_enabled": self.enable_streaming,
            "current_recording": self._current_run_id,
            "replay_session": self._replay_session_id
        }
    
    def analyze_stream_performance(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Analyze performance characteristics of a recorded stream."""
        tokens = self.get_stream_tokens(stream_id)
        if not tokens:
            return None
        
        return analyze_stream_timing(tokens)
    
    def _create_input_fingerprint(self, input_data: Dict[str, Any]) -> str:
        """Create input fingerprint (same logic as recorder)."""
        import hashlib
        normalized = self._normalize_data(input_data)
        content = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        return hashlib.blake2b(content.encode(), digest_size=16).hexdigest()
    
    def _normalize_data(self, data: Any) -> Any:
        """Normalize data (same logic as recorder)."""
        import os
        import re
        
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                # Skip volatile fields
                if key.lower() in ('timestamp', 'created_at', 'updated_at', 'id', 'uuid', 
                                 'session_id', 'correlation_id', 'trace_id', 'span_id'):
                    continue
                # Normalize paths to relative
                if key.lower().endswith('_path') and isinstance(value, str):
                    value = os.path.relpath(value) if os.path.isabs(value) else value
                normalized[key] = self._normalize_data(value)
            return normalized
        elif isinstance(data, list):
            return [self._normalize_data(item) for item in data]
        elif isinstance(data, str):
            # Replace UUIDs with placeholder
            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            return re.sub(uuid_pattern, '<UUID>', data, flags=re.IGNORECASE)
        else:
            return data
    
    def _log_replay_assert(self, success: bool, message: str):
        """Log replay assertion result."""
        if self._telemetry_logger:
            assert_event = create_event(
                EventType.REPLAY_ASSERT,
                replay_mode="replay",
                replay_match=success,
                replay_error=None if success else message,
                message=message
            )
            self._telemetry_logger.log_event(assert_event)
    
    def get_loaded_recording_id(self) -> Optional[str]:
        """Get the ID of the currently loaded recording."""
        return self._current_run_id
    
    def get_recorded_io_count(self) -> int:
        """Get the number of recorded IO edges loaded."""
        return len(self._recorded_ios)
    
    def list_recorded_io_keys(self) -> List[str]:
        """List all recorded IO lookup keys."""
        return list(self._recorded_ios.keys())


# Backward compatibility alias
Player = EnhancedPlayer


# Global player instance for interception
_global_player: Optional[EnhancedPlayer] = None

def set_global_player(player: Optional[EnhancedPlayer]) -> None:
    """Set the global player instance for IO interception."""
    global _global_player
    _global_player = player

def get_global_player() -> Optional[EnhancedPlayer]:
    """Get the global player instance."""
    return _global_player

def intercept_llm_call(adapter_name: str = "unknown", agent_id: str = "default"):
    """Decorator to intercept LLM calls during replay."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            player = get_global_player()
            if player and player._current_run_id:
                # Generate call index for this LLM call
                call_key = f"llm_call:{adapter_name}:{agent_id}"
                if call_key not in player._call_counters:
                    player._call_counters = getattr(player, '_call_counters', {})
                    player._call_counters[call_key] = 0
                call_index = player._call_counters[call_key]
                player._call_counters[call_key] += 1
                
                # Prepare input data for matching
                input_data = {
                    "function_name": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                
                try:
                    # Try to get recorded output
                    match_found, output_data = player.get_recorded_output(
                        io_type="llm_call",
                        tool_name=func.__name__,
                        input_data=input_data,
                        call_index=call_index,
                        agent_id=agent_id
                    )
                    
                    if match_found:
                        return output_data
                        
                except ReplayMismatchError:
                    # Log the mismatch but continue with normal execution
                    pass
            
            # Execute normally if no replay or mismatch
            return func(*args, **kwargs)
        return wrapper
    return decorator

def intercept_tool_call(adapter_name: str = "unknown", agent_id: str = "default", tool_name: str = None):
    """Decorator to intercept tool calls during replay."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            player = get_global_player()
            if player and player._current_run_id:
                # Use provided tool_name or function name
                actual_tool_name = tool_name or func.__name__
                
                # Generate call index for this tool call
                call_key = f"tool_call:{adapter_name}:{agent_id}:{actual_tool_name}"
                if call_key not in player._call_counters:
                    player._call_counters = getattr(player, '_call_counters', {})
                    player._call_counters[call_key] = 0
                call_index = player._call_counters[call_key]
                player._call_counters[call_key] += 1
                
                # Prepare input data for matching
                input_data = {
                    "function_name": func.__name__,
                    "tool_name": actual_tool_name,
                    "args": args,
                    "kwargs": kwargs
                }
                
                try:
                    # Try to get recorded output
                    match_found, output_data = player.get_recorded_output(
                        io_type="tool_call",
                        tool_name=actual_tool_name,
                        input_data=input_data,
                        call_index=call_index,
                        agent_id=agent_id
                    )
                    
                    if match_found:
                        return output_data
                        
                except ReplayMismatchError:
                    # Log the mismatch but continue with normal execution
                    pass
            
            # Execute normally if no replay or mismatch
            return func(*args, **kwargs)
        return wrapper
    return decorator

def intercept_sandbox_exec(adapter_name: str = "unknown", agent_id: str = "default"):
    """Decorator to intercept sandbox execution during replay."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            player = get_global_player()
            if player and player._current_run_id:
                # Generate call index for this sandbox execution
                call_key = f"sandbox_exec:{adapter_name}:{agent_id}"
                if call_key not in player._call_counters:
                    player._call_counters = getattr(player, '_call_counters', {})
                    player._call_counters[call_key] = 0
                call_index = player._call_counters[call_key]
                player._call_counters[call_key] += 1
                
                # Prepare input data for matching
                input_data = {
                    "function_name": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                
                try:
                    # Try to get recorded output
                    match_found, output_data = player.get_recorded_output(
                        io_type="sandbox_exec",
                        tool_name="execute",
                        input_data=input_data,
                        call_index=call_index,
                        agent_id=agent_id
                    )
                    
                    if match_found:
                        return output_data
                        
                except ReplayMismatchError:
                    # Log the mismatch but continue with normal execution
                    pass
            
            # Execute normally if no replay or mismatch
            return func(*args, **kwargs)
        return wrapper
    return decorator

def intercept_vcs_operation(adapter_name: str = "unknown", agent_id: str = "default", operation: str = None):
    """Decorator to intercept VCS operations during replay."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            player = get_global_player()
            if player and player._current_run_id:
                # Use provided operation or function name
                actual_operation = operation or func.__name__
                
                # Generate call index for this VCS operation
                call_key = f"vcs_operation:{adapter_name}:{agent_id}:{actual_operation}"
                if call_key not in player._call_counters:
                    player._call_counters = getattr(player, '_call_counters', {})
                    player._call_counters[call_key] = 0
                call_index = player._call_counters[call_key]
                player._call_counters[call_key] += 1
                
                # Prepare input data for matching
                input_data = {
                    "function_name": func.__name__,
                    "operation": actual_operation,
                    "args": args,
                    "kwargs": kwargs
                }
                
                try:
                    # Try to get recorded output
                    match_found, output_data = player.get_recorded_output(
                        io_type="vcs_operation",
                        tool_name=actual_operation,
                        input_data=input_data,
                        call_index=call_index,
                        agent_id=agent_id
                    )
                    
                    if match_found:
                        return output_data
                        
                except ReplayMismatchError:
                    # Log the mismatch but continue with normal execution
                    pass
            
            # Execute normally if no replay or mismatch
            return func(*args, **kwargs)
        return wrapper
    return decorator