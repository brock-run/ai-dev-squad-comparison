"""
Enhanced Recorder with Telemetry Integration and Streaming Support

Captures execution traces for deterministic replay, including LLM calls,
tool invocations, and other IO operations. Integrates with telemetry system
for comprehensive event tracking and streaming support.

Phase 1: Enhanced Telemetry Integration
"""

import json
import logging
import time
import zstandard as zstd
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from queue import Queue, Empty
import threading
import uuid

# Import foundation components
from common.replay import (
    get_ordering_manager,
    create_ordered_event,
    get_determinism_manager,
    get_redaction_filter,
    redact_dict,
    create_io_key
)

# Import telemetry components
try:
    from common.telemetry.schema import (
        TelemetryEvent,
        EventType,
        RecordingEvent,
        StreamingLLMEvent,
        IOEvent,
        create_recording_start_event,
        create_streaming_llm_start_event,
        create_streaming_llm_chunk_event,
        create_streaming_llm_finish_event
    )
    from common.telemetry.logger import get_telemetry_logger
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    logging.warning("Telemetry modules not available - using basic logging")

logger = logging.getLogger(__name__)


@dataclass
class RecordedEvent:
    """A recorded event that can be replayed."""
    
    event_id: str
    timestamp: datetime
    event_type: str
    agent_id: str
    tool_name: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    duration: float
    metadata: Dict[str, Any]
    
    # Enhanced fields for Phase 1
    step: Optional[int] = None
    parent_step: Optional[int] = None
    call_index: Optional[int] = None
    io_key: Optional[str] = None
    input_fingerprint: Optional[str] = None
    stream_id: Optional[str] = None
    chunk_index: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "duration": self.duration,
            "metadata": self.metadata
        }
        
        # Add enhanced fields if present
        if self.step is not None:
            data["step"] = self.step
        if self.parent_step is not None:
            data["parent_step"] = self.parent_step
        if self.call_index is not None:
            data["call_index"] = self.call_index
        if self.io_key:
            data["io_key"] = self.io_key
        if self.input_fingerprint:
            data["input_fingerprint"] = self.input_fingerprint
        if self.stream_id:
            data["stream_id"] = self.stream_id
        if self.chunk_index is not None:
            data["chunk_index"] = self.chunk_index
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecordedEvent':
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            agent_id=data["agent_id"],
            tool_name=data["tool_name"],
            inputs=data["inputs"],
            outputs=data["outputs"],
            duration=data["duration"],
            metadata=data["metadata"],
            step=data.get("step"),
            parent_step=data.get("parent_step"),
            call_index=data.get("call_index"),
            io_key=data.get("io_key"),
            input_fingerprint=data.get("input_fingerprint"),
            stream_id=data.get("stream_id"),
            chunk_index=data.get("chunk_index")
        )


@dataclass
class StreamingChunk:
    """A chunk of streaming data (e.g., LLM token stream)."""
    
    chunk_id: str
    stream_id: str
    chunk_index: int
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    is_final: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "chunk_id": self.chunk_id,
            "stream_id": self.stream_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "is_final": self.is_final
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamingChunk':
        """Create from dictionary."""
        return cls(
            chunk_id=data["chunk_id"],
            stream_id=data["stream_id"],
            chunk_index=data["chunk_index"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data["metadata"],
            is_final=data.get("is_final", False)
        )


@dataclass
class RecordingManifest:
    """Manifest for a recording session with provenance information."""
    
    recording_id: str
    start_time: datetime
    end_time: Optional[datetime]
    adapter_name: str
    adapter_version: str
    git_sha: Optional[str]
    config_digest: str
    model_ids: List[str]
    seeds: List[int]
    redaction_applied: bool
    compression_enabled: bool
    total_events: int
    total_chunks: int
    artifacts_size_bytes: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "recording_id": self.recording_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "adapter_name": self.adapter_name,
            "adapter_version": self.adapter_version,
            "git_sha": self.git_sha,
            "config_digest": self.config_digest,
            "model_ids": self.model_ids,
            "seeds": self.seeds,
            "redaction_applied": self.redaction_applied,
            "compression_enabled": self.compression_enabled,
            "total_events": self.total_events,
            "total_chunks": self.total_chunks,
            "artifacts_size_bytes": self.artifacts_size_bytes
        }


class EnhancedRecorder:
    """Enhanced recorder with telemetry integration and streaming support."""
    
    def __init__(self, 
                 output_dir: Path,
                 adapter_name: str,
                 adapter_version: str = "1.0.0",
                 compression_enabled: bool = True,
                 max_file_size_mb: int = 100):
        """
        Initialize enhanced recorder.
        
        Args:
            output_dir: Directory to store recorded traces
            adapter_name: Name of the adapter being recorded
            adapter_version: Version of the adapter
            compression_enabled: Enable zstd compression
            max_file_size_mb: Maximum file size before rotation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.adapter_name = adapter_name
        self.adapter_version = adapter_version
        self.compression_enabled = compression_enabled
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        # Recording state
        self.recording = False
        self.recording_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.current_file_index = 0
        self.current_file_size = 0
        
        # Event storage
        self.events: List[RecordedEvent] = []
        self.streaming_chunks: Dict[str, List[StreamingChunk]] = {}
        
        # File handles
        self.events_file: Optional[TextIO] = None
        self.chunks_file: Optional[TextIO] = None
        
        # Telemetry integration
        self.telemetry_logger = get_telemetry_logger() if TELEMETRY_AVAILABLE else None
        self.ordering_manager = get_ordering_manager()
        self.redaction_filter = get_redaction_filter()
        
        # Background writer for performance
        self.write_queue: Queue = Queue()
        self.writer_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
        logger.info(f"Initialized enhanced recorder: {adapter_name} v{adapter_version}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Compression: {compression_enabled}, Max file size: {max_file_size_mb}MB")
    
    def start_recording(self, 
                       session_id: str,
                       task_id: Optional[str] = None,
                       config_digest: Optional[str] = None,
                       model_ids: Optional[List[str]] = None,
                       seeds: Optional[List[int]] = None) -> str:
        """
        Start recording session with enhanced metadata.
        
        Args:
            session_id: Unique session identifier
            task_id: Task identifier
            config_digest: Hash of configuration
            model_ids: List of model identifiers used
            seeds: List of seeds used for determinism
            
        Returns:
            Recording ID
        """
        if self.recording:
            logger.warning("Recording already in progress")
            return self.recording_id
        
        # Generate recording ID
        self.recording_id = f"rec_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        self.recording = True
        self.start_time = datetime.utcnow()
        self.current_file_index = 0
        self.current_file_size = 0
        
        # Clear previous data
        self.events.clear()
        self.streaming_chunks.clear()
        
        # Start background writer
        self._start_writer_thread()
        
        # Open output files
        self._open_output_files()
        
        # Create telemetry event
        if self.telemetry_logger:
            recording_event = create_recording_start_event(
                recording_session=self.recording_id,
                artifacts_path=str(self.output_dir),
                agent_id="recorder",
                session_id=session_id,
                task_id=task_id,
                adapter_name=self.adapter_name,
                adapter_version=self.adapter_version,
                config_digest=config_digest,
                model_ids=model_ids or [],
                seeds=seeds or []
            )
            self.telemetry_logger.log_event(recording_event)
        
        logger.info(f"Started recording session: {session_id}")
        logger.info(f"Recording ID: {self.recording_id}")
        
        return self.recording_id
    
    def record_event(self, 
                    event_type: str,
                    agent_id: str,
                    tool_name: str,
                    inputs: Dict[str, Any],
                    outputs: Dict[str, Any],
                    duration: float,
                    metadata: Optional[Dict[str, Any]] = None,
                    session_id: Optional[str] = None,
                    task_id: Optional[str] = None) -> str:
        """
        Record an event with enhanced metadata and ordering.
        
        Args:
            event_type: Type of event (e.g., 'llm_call', 'tool_call')
            agent_id: ID of the agent performing the action
            tool_name: Name of the tool being used
            inputs: Input parameters
            outputs: Output results
            duration: Duration in seconds
            metadata: Additional metadata
            session_id: Session ID for telemetry
            task_id: Task ID for telemetry
            
        Returns:
            Event ID
        """
        if not self.recording:
            logger.warning("Not recording - event ignored")
            return None
        
        # Create ordered event for step tracking
        ordered_event = self.ordering_manager.create_ordered_event(
            event_type=event_type,
            agent_id=agent_id,
            tool_name=tool_name,
            data={"inputs": inputs, "outputs": outputs}
        )
        
        # Create IO key for replay lookup
        io_key = create_io_key(
            event_type=event_type,
            adapter=self.adapter_name,
            agent_id=agent_id,
            tool_name=tool_name,
            call_index=ordered_event.call_index,
            input_data=inputs
        )
        
        # Apply redaction to sensitive data
        redacted_inputs = self.redaction_filter.redact_dict(inputs)
        redacted_outputs = self.redaction_filter.redact_dict(outputs)
        redacted_metadata = self.redaction_filter.redact_dict(metadata or {})
        
        # Create recorded event
        event = RecordedEvent(
            event_id=ordered_event.event_id,
            timestamp=ordered_event.timestamp,
            event_type=event_type,
            agent_id=agent_id,
            tool_name=tool_name,
            inputs=redacted_inputs,
            outputs=redacted_outputs,
            duration=duration,
            metadata=redacted_metadata,
            step=ordered_event.step,
            parent_step=ordered_event.parent_step,
            call_index=ordered_event.call_index,
            io_key=io_key.to_string(),
            input_fingerprint=io_key.input_fingerprint
        )
        
        # Queue for background writing
        self.write_queue.put(('event', event))
        
        # Create telemetry event
        if self.telemetry_logger:
            telemetry_event = TelemetryEvent(
                event_type=EventType(event_type) if hasattr(EventType, event_type.upper()) else EventType.CUSTOM,
                source="recorder",
                agent_id=agent_id,
                session_id=session_id,
                task_id=task_id,
                recording_session=self.recording_id,
                step=ordered_event.step,
                parent_step=ordered_event.parent_step,
                call_index=ordered_event.call_index,
                io_key=io_key.to_string(),
                input_fingerprint=io_key.input_fingerprint,
                duration_ms=duration * 1000,
                data={
                    "tool_name": tool_name,
                    "input_size": len(str(inputs)),
                    "output_size": len(str(outputs))
                }
            )
            self.telemetry_logger.log_event(telemetry_event)
        
        self.events.append(event)
        logger.debug(f"Recorded event: {event.event_id} ({event_type})")
        
        return event.event_id
    
    def start_streaming(self, 
                       agent_id: str,
                       tool_name: str,
                       inputs: Dict[str, Any],
                       session_id: Optional[str] = None,
                       task_id: Optional[str] = None) -> str:
        """
        Start recording a streaming operation (e.g., LLM token stream).
        
        Args:
            agent_id: ID of the agent
            tool_name: Name of the tool (e.g., 'openai')
            inputs: Input parameters
            session_id: Session ID for telemetry
            task_id: Task ID for telemetry
            
        Returns:
            Stream ID
        """
        if not self.recording:
            logger.warning("Not recording - streaming ignored")
            return None
        
        stream_id = f"stream_{uuid.uuid4().hex[:8]}"
        self.streaming_chunks[stream_id] = []
        
        # Create telemetry event for stream start
        if self.telemetry_logger:
            stream_start_event = create_streaming_llm_start_event(
                prompt=inputs.get('prompt', ''),
                model=inputs.get('model', ''),
                agent_id=agent_id,
                stream_id=stream_id,
                session_id=session_id,
                task_id=task_id,
                recording_session=self.recording_id
            )
            self.telemetry_logger.log_event(stream_start_event)
        
        logger.debug(f"Started streaming: {stream_id} for {agent_id}/{tool_name}")
        return stream_id
    
    def record_chunk(self, 
                    stream_id: str,
                    content: str,
                    metadata: Optional[Dict[str, Any]] = None,
                    is_final: bool = False) -> str:
        """
        Record a streaming chunk.
        
        Args:
            stream_id: Stream identifier
            content: Chunk content
            metadata: Additional metadata
            is_final: Whether this is the final chunk
            
        Returns:
            Chunk ID
        """
        if not self.recording or stream_id not in self.streaming_chunks:
            logger.warning(f"Not recording or invalid stream: {stream_id}")
            return None
        
        chunk_index = len(self.streaming_chunks[stream_id])
        chunk_id = f"{stream_id}_chunk_{chunk_index:04d}"
        
        # Apply redaction to chunk content
        redacted_content = self.redaction_filter.redact_text(content)
        redacted_metadata = self.redaction_filter.redact_dict(metadata or {})
        
        chunk = StreamingChunk(
            chunk_id=chunk_id,
            stream_id=stream_id,
            chunk_index=chunk_index,
            content=redacted_content,
            timestamp=datetime.utcnow(),
            metadata=redacted_metadata,
            is_final=is_final
        )
        
        self.streaming_chunks[stream_id].append(chunk)
        
        # Queue for background writing
        self.write_queue.put(('chunk', chunk))
        
        # Create telemetry event for chunk
        if self.telemetry_logger:
            chunk_event = create_streaming_llm_chunk_event(
                chunk_content=redacted_content,
                stream_id=stream_id,
                chunk_index=chunk_index,
                agent_id="recorder",  # Would be passed from caller
                recording_session=self.recording_id
            )
            self.telemetry_logger.log_event(chunk_event)
        
        logger.debug(f"Recorded chunk: {chunk_id} (final: {is_final})")
        return chunk_id
    
    def finish_streaming(self, 
                        stream_id: str,
                        total_tokens: Optional[int] = None) -> int:
        """
        Finish a streaming operation.
        
        Args:
            stream_id: Stream identifier
            total_tokens: Total token count
            
        Returns:
            Total number of chunks recorded
        """
        if stream_id not in self.streaming_chunks:
            logger.warning(f"Unknown stream: {stream_id}")
            return 0
        
        chunks = self.streaming_chunks[stream_id]
        total_chunks = len(chunks)
        
        # Create telemetry event for stream finish
        if self.telemetry_logger:
            finish_event = create_streaming_llm_finish_event(
                stream_id=stream_id,
                total_chunks=total_chunks,
                total_tokens=total_tokens or 0,
                agent_id="recorder",  # Would be passed from caller
                recording_session=self.recording_id
            )
            self.telemetry_logger.log_event(finish_event)
        
        logger.debug(f"Finished streaming: {stream_id} ({total_chunks} chunks)")
        return total_chunks
    
    def checkpoint(self, label: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a checkpoint for partial replay.
        
        Args:
            label: Checkpoint label
            metadata: Additional metadata
        """
        if not self.recording:
            return
        
        checkpoint_data = {
            "label": label,
            "timestamp": datetime.utcnow().isoformat(),
            "event_count": len(self.events),
            "metadata": metadata or {}
        }
        
        # Queue checkpoint for writing
        self.write_queue.put(('checkpoint', checkpoint_data))
        
        logger.info(f"Created checkpoint: {label}")
    
    def stop_recording(self) -> RecordingManifest:
        """
        Stop recording and generate manifest.
        
        Returns:
            Recording manifest with metadata
        """
        if not self.recording:
            logger.warning("No recording in progress")
            return None
        
        self.recording = False
        end_time = datetime.utcnow()
        
        # Stop background writer
        self._stop_writer_thread()
        
        # Close output files
        self._close_output_files()
        
        # Calculate total chunks
        total_chunks = sum(len(chunks) for chunks in self.streaming_chunks.values())
        
        # Get git SHA if available
        git_sha = self._get_git_sha()
        
        # Calculate artifacts size
        artifacts_size = sum(
            f.stat().st_size for f in self.output_dir.glob(f"{self.recording_id}*")
            if f.is_file()
        )
        
        # Create manifest
        manifest = RecordingManifest(
            recording_id=self.recording_id,
            start_time=self.start_time,
            end_time=end_time,
            adapter_name=self.adapter_name,
            adapter_version=self.adapter_version,
            git_sha=git_sha,
            config_digest="",  # Would be provided by caller
            model_ids=[],  # Would be collected during recording
            seeds=[],  # Would be provided by caller
            redaction_applied=True,
            compression_enabled=self.compression_enabled,
            total_events=len(self.events),
            total_chunks=total_chunks,
            artifacts_size_bytes=artifacts_size
        )
        
        # Save manifest
        manifest_path = self.output_dir / f"{self.recording_id}_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
        
        logger.info(f"Recording stopped: {self.recording_id}")
        logger.info(f"Total events: {len(self.events)}, Total chunks: {total_chunks}")
        logger.info(f"Artifacts size: {artifacts_size / 1024 / 1024:.1f} MB")
        logger.info(f"Manifest saved: {manifest_path}")
        
        return manifest
    
    def _start_writer_thread(self):
        """Start background writer thread."""
        self.shutdown_event.clear()
        self.writer_thread = threading.Thread(
            target=self._writer_loop,
            name="RecorderWriter",
            daemon=True
        )
        self.writer_thread.start()
    
    def _stop_writer_thread(self):
        """Stop background writer thread."""
        self.shutdown_event.set()
        if self.writer_thread and self.writer_thread.is_alive():
            self.writer_thread.join(timeout=5.0)
    
    def _writer_loop(self):
        """Background writer loop."""
        while not self.shutdown_event.is_set():
            try:
                item = self.write_queue.get(timeout=1.0)
                if item is None:
                    break
                
                item_type, data = item
                
                if item_type == 'event':
                    self._write_event(data)
                elif item_type == 'chunk':
                    self._write_chunk(data)
                elif item_type == 'checkpoint':
                    self._write_checkpoint(data)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in writer thread: {e}")
    
    def _write_event(self, event: RecordedEvent):
        """Write event to file."""
        if self.events_file:
            line = json.dumps(event.to_dict()) + '\n'
            
            if self.compression_enabled:
                # Write compressed
                compressed = zstd.compress(line.encode('utf-8'))
                self.events_file.write(compressed)
            else:
                self.events_file.write(line)
            
            self.current_file_size += len(line)
            
            # Check for rotation
            if self.current_file_size > self.max_file_size_bytes:
                self._rotate_files()
    
    def _write_chunk(self, chunk: StreamingChunk):
        """Write streaming chunk to file."""
        if self.chunks_file:
            line = json.dumps(chunk.to_dict()) + '\n'
            
            if self.compression_enabled:
                compressed = zstd.compress(line.encode('utf-8'))
                self.chunks_file.write(compressed)
            else:
                self.chunks_file.write(line)
    
    def _write_checkpoint(self, checkpoint_data: Dict[str, Any]):
        """Write checkpoint to file."""
        checkpoint_path = self.output_dir / f"{self.recording_id}_checkpoints.jsonl"
        with open(checkpoint_path, 'a') as f:
            f.write(json.dumps(checkpoint_data) + '\n')
    
    def _open_output_files(self):
        """Open output files for writing."""
        events_path = self.output_dir / f"{self.recording_id}_events_{self.current_file_index:03d}.jsonl"
        chunks_path = self.output_dir / f"{self.recording_id}_chunks.jsonl"
        
        mode = 'wb' if self.compression_enabled else 'w'
        self.events_file = open(events_path, mode)
        self.chunks_file = open(chunks_path, mode)
    
    def _close_output_files(self):
        """Close output files."""
        if self.events_file:
            self.events_file.close()
            self.events_file = None
        
        if self.chunks_file:
            self.chunks_file.close()
            self.chunks_file = None
    
    def _rotate_files(self):
        """Rotate output files when they get too large."""
        self._close_output_files()
        self.current_file_index += 1
        self.current_file_size = 0
        self._open_output_files()
        
        logger.info(f"Rotated to file index: {self.current_file_index}")
    
    def _get_git_sha(self) -> Optional[str]:
        """Get current git SHA if available."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=self.output_dir.parent
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None


# Backward compatibility alias
Recorder = EnhancedRecorder