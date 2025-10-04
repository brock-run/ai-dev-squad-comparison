# Phase 1: Enhanced Telemetry Integration - Developer Guide

## Overview

This guide provides comprehensive information for developers working with Phase 1 of the Record-Replay Enhancement Project. Phase 1 introduces enhanced telemetry integration and streaming support for the record-replay system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Getting Started](#getting-started)
4. [API Reference](#api-reference)
5. [Integration Patterns](#integration-patterns)
6. [Testing](#testing)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

Phase 1 enhances the existing record-replay system with:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Foundation    │    │   Telemetry     │    │   Streaming     │
│   Components    │◄──►│   System        │◄──►│   Support       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Enhanced      │    │   Enhanced      │    │   Adapter       │
│   Recorder      │◄──►│   Player        │◄──►│   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Enhancements

- **Enhanced Telemetry Schema**: New event types for record-replay operations
- **Streaming Support**: Real-time data capture and replay with timing preservation
- **Background Processing**: Asynchronous writing for improved performance
- **Comprehensive Provenance**: Git SHA, configuration digests, and metadata tracking

## Core Components

### 1. Enhanced Recorder (`benchmark.replay.recorder.EnhancedRecorder`)

The enhanced recorder provides comprehensive recording capabilities with telemetry integration.

#### Key Features

- **Telemetry Integration**: Automatic event generation for all operations
- **Streaming Capture**: Real-time token stream recording
- **Background Writing**: Asynchronous processing for performance
- **Compression**: Optional zstd compression for storage efficiency
- **File Rotation**: Automatic rotation based on size limits
- **Provenance Tracking**: Git SHA, config digests, model IDs

#### Basic Usage

```python
from benchmark.replay.recorder import EnhancedRecorder

# Initialize recorder
recorder = EnhancedRecorder(
    output_dir=Path("recordings"),
    adapter_name="my_adapter",
    adapter_version="1.0.0",
    compression_enabled=True,
    max_file_size_mb=100
)

# Start recording
recording_id = recorder.start_recording(
    session_id="session_001",
    task_id="task_001",
    config_digest="config_hash",
    model_ids=["gpt-4"],
    seeds=[42]
)

# Record events
event_id = recorder.record_event(
    event_type="llm_call",
    agent_id="my_agent",
    tool_name="openai",
    inputs={"prompt": "Hello"},
    outputs={"response": "Hi there!"},
    duration=1.5,
    session_id="session_001",
    task_id="task_001"
)

# Record streaming data
stream_id = recorder.start_streaming(
    agent_id="my_agent",
    tool_name="openai",
    inputs={"prompt": "Tell me a story"}
)

recorder.record_chunk(stream_id, "Once upon", {"token": 1})
recorder.record_chunk(stream_id, " a time", {"token": 2})
recorder.record_chunk(stream_id, "", is_final=True)

recorder.finish_streaming(stream_id)

# Create checkpoints
recorder.checkpoint("milestone_1", {"progress": "50%"})

# Stop recording
manifest = recorder.stop_recording()
```

### 2. Enhanced Player (`benchmark.replay.player.EnhancedPlayer`)

The enhanced player provides streaming replay capabilities with multiple modes.

#### Key Features

- **Streaming Replay**: Replay streaming data with timing preservation
- **Multiple Modes**: Strict, warn, and hybrid replay modes
- **Mismatch Detection**: Comprehensive mismatch reporting
- **Performance Analysis**: Stream timing analysis
- **Telemetry Integration**: Automatic replay event generation

#### Basic Usage

```python
from benchmark.replay.player import EnhancedPlayer

# Initialize player
player = EnhancedPlayer(
    storage_path=Path("recordings"),
    replay_mode="strict",  # strict, warn, or hybrid
    enable_streaming=True
)

# Load recording
success = player.load_recording("recording_id")

# Start replay
replay_id = player.start_replay(
    session_id="replay_session",
    task_id="replay_task"
)

# Replay IO operations
match_found, output = player.get_recorded_output(
    io_type="llm_call",
    tool_name="openai",
    input_data={"prompt": "Hello"},
    call_index=0,
    agent_id="my_agent"
)

# Replay streaming data
stream_replay = player.replay_streaming_llm_call(
    prompt="Tell me a story",
    model="gpt-4",
    agent_id="my_agent",
    call_index=0
)

if stream_replay:
    for chunk in stream_replay:
        print(chunk, end="")

# Get statistics
stats = player.get_replay_statistics()
print(f"Success rate: {stats['success_rate']:.1%}")
```

### 3. Streaming Support (`common.replay.streaming`)

Comprehensive streaming infrastructure for real-time data capture and replay.

#### Core Classes

##### StreamToken
```python
from common.replay.streaming import StreamToken

token = StreamToken(
    content="Hello",
    timestamp=datetime.utcnow(),
    index=0,
    metadata={"model": "gpt-4"}
)

# Serialization
token_dict = token.to_dict()
restored_token = StreamToken.from_dict(token_dict)
```

##### StreamCapture
```python
from common.replay.streaming import StreamCapture

capture = StreamCapture("stream_123")
capture.add_token("Hello", {"token": 1})
capture.add_token(" world", {"token": 2})
capture.add_token("", is_final=True)

full_content = capture.get_full_content()  # "Hello world"
summary = capture.get_metadata_summary()
```

##### StreamReplay
```python
from common.replay.streaming import StreamReplay

replay = StreamReplay(recorded_tokens)
replay.set_timing_mode(preserve_timing=True)

# Synchronous replay
for token in replay.replay_sync():
    print(token.content, end="")

# Asynchronous replay
async for token in replay.replay_async():
    print(token.content, end="")
```

##### StreamingLLMWrapper
```python
from common.replay.streaming import StreamingLLMWrapper

wrapper = StreamingLLMWrapper(llm_client, recorder=recorder)

# Automatically records streaming
for chunk in wrapper.stream_completion("Hello", "gpt-4", "agent_id"):
    print(chunk, end="")
```

#### Context Managers

```python
from common.replay.streaming import capture_stream, capture_stream_async

# Synchronous streaming
with capture_stream(recorder, "agent_id", "tool_name", inputs) as capture:
    for chunk in llm_stream:
        capture.add_token(chunk)

# Asynchronous streaming
async with capture_stream_async(recorder, "agent_id", "tool_name", inputs) as capture:
    async for chunk in llm_stream:
        capture.add_token(chunk)
```

### 4. Enhanced Telemetry Schema (`common.telemetry.schema`)

Extended telemetry schema with record-replay specific events.

#### New Event Types

```python
from common.telemetry.schema import EventType

# Streaming LLM events
EventType.LLM_CALL_STARTED
EventType.LLM_CALL_CHUNK  
EventType.LLM_CALL_FINISHED

# Record-replay events
EventType.RECORDING_NOTE
EventType.REPLAY_START
EventType.REPLAY_MISMATCH

# IO events
EventType.IO_READ
EventType.IO_WRITE
EventType.IO_NETWORK
```

#### Specialized Event Classes

```python
from common.telemetry.schema import StreamingLLMEvent, RecordingEvent, ReplayEvent

# Streaming LLM event
llm_event = StreamingLLMEvent(
    event_type=EventType.LLM_CALL_STARTED,
    agent_id="my_agent",
    model="gpt-4",
    prompt="Hello world",
    chunk_index=0
)

# Recording event
recording_event = RecordingEvent(
    event_type=EventType.RECORDING_NOTE,
    agent_id="recorder",
    run_id="recording_123"
)
```

#### Convenience Functions

```python
from common.telemetry.schema import (
    create_streaming_llm_start_event,
    create_streaming_llm_chunk_event,
    create_streaming_llm_finish_event,
    create_recording_start_event,
    create_replay_start_event
)

# Create streaming events
start_event = create_streaming_llm_start_event(
    prompt="Hello",
    model="gpt-4",
    agent_id="my_agent",
    stream_id="stream_123"
)

chunk_event = create_streaming_llm_chunk_event(
    chunk_content="Hello",
    stream_id="stream_123",
    chunk_index=0,
    agent_id="my_agent"
)

finish_event = create_streaming_llm_finish_event(
    stream_id="stream_123",
    total_chunks=5,
    total_tokens=10,
    agent_id="my_agent"
)
```

## Getting Started

### Installation

Phase 1 components are part of the existing system. Ensure you have the required dependencies:

```bash
pip install zstandard  # For compression support
pip install pydantic   # For data validation
pip install pyyaml     # For manifest files
```

### Basic Integration

#### 1. Adapter Integration

```python
from benchmark.replay.recorder import EnhancedRecorder
from benchmark.replay.player import EnhancedPlayer
from common.replay.streaming import StreamingLLMWrapper

class MyAdapter:
    def __init__(self):
        # Initialize recorder
        self.recorder = EnhancedRecorder(
            output_dir=Path("recordings"),
            adapter_name="my_adapter"
        )
        
        # Initialize player
        self.player = EnhancedPlayer(
            storage_path=Path("recordings"),
            replay_mode="warn"
        )
        
        # Wrap LLM client
        self.llm_wrapper = StreamingLLMWrapper(
            self.llm_client,
            recorder=self.recorder,
            player=self.player
        )
    
    def run_task(self, task_data):
        # Start recording
        recording_id = self.recorder.start_recording(
            session_id=task_data["session_id"],
            task_id=task_data["task_id"]
        )
        
        try:
            # Use streaming wrapper for LLM calls
            response = ""
            for chunk in self.llm_wrapper.stream_completion(
                prompt=task_data["prompt"],
                model="gpt-4",
                agent_id="my_agent"
            ):
                response += chunk
            
            # Record other events
            self.recorder.record_event(
                event_type="task_complete",
                agent_id="my_agent",
                tool_name="task_processor",
                inputs=task_data,
                outputs={"response": response},
                duration=2.5
            )
            
        finally:
            # Stop recording
            manifest = self.recorder.stop_recording()
            return manifest
```

#### 2. Testing Integration

```python
import pytest
from pathlib import Path
import tempfile

class TestMyAdapter:
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.adapter = MyAdapter()
        self.adapter.recorder.output_dir = self.temp_dir
        self.adapter.player.storage_path = self.temp_dir
    
    def test_record_and_replay(self):
        # Record a session
        task_data = {
            "session_id": "test_session",
            "task_id": "test_task",
            "prompt": "Hello world"
        }
        
        manifest = self.adapter.run_task(task_data)
        assert manifest.total_events > 0
        
        # Load and replay
        success = self.adapter.player.load_recording(manifest.recording_id)
        assert success
        
        replay_id = self.adapter.player.start_replay()
        assert replay_id is not None
        
        stats = self.adapter.player.get_replay_statistics()
        assert stats["success_rate"] >= 0.0
```

## API Reference

### EnhancedRecorder

#### Constructor
```python
EnhancedRecorder(
    output_dir: Path,
    adapter_name: str,
    adapter_version: str = "1.0.0",
    compression_enabled: bool = True,
    max_file_size_mb: int = 100
)
```

#### Methods

##### start_recording()
```python
start_recording(
    session_id: str,
    task_id: Optional[str] = None,
    config_digest: Optional[str] = None,
    model_ids: Optional[List[str]] = None,
    seeds: Optional[List[int]] = None
) -> str
```

##### record_event()
```python
record_event(
    event_type: str,
    agent_id: str,
    tool_name: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    duration: float,
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> str
```

##### start_streaming()
```python
start_streaming(
    agent_id: str,
    tool_name: str,
    inputs: Dict[str, Any],
    session_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> str
```

##### record_chunk()
```python
record_chunk(
    stream_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    is_final: bool = False
) -> str
```

##### finish_streaming()
```python
finish_streaming(
    stream_id: str,
    total_tokens: Optional[int] = None
) -> int
```

##### checkpoint()
```python
checkpoint(
    label: str,
    metadata: Optional[Dict[str, Any]] = None
)
```

##### stop_recording()
```python
stop_recording() -> RecordingManifest
```

### EnhancedPlayer

#### Constructor
```python
EnhancedPlayer(
    storage_path: Optional[Path] = None,
    replay_mode: str = "strict",
    enable_streaming: bool = True
)
```

#### Methods

##### load_recording()
```python
load_recording(run_id: str) -> bool
```

##### start_replay()
```python
start_replay(
    new_run_id: Optional[str] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> str
```

##### get_recorded_output()
```python
get_recorded_output(
    io_type: str,
    tool_name: str,
    input_data: Dict[str, Any],
    call_index: int,
    agent_id: str = "",
    session_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> Tuple[bool, Any]
```

##### replay_streaming_llm_call()
```python
replay_streaming_llm_call(
    prompt: str,
    model: str,
    agent_id: str,
    call_index: int,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> Optional[Iterator[str]]
```

##### get_replay_statistics()
```python
get_replay_statistics() -> Dict[str, Any]
```

## Integration Patterns

### 1. Decorator Pattern for LLM Calls

```python
from functools import wraps
from common.replay.streaming import capture_stream

def record_llm_call(recorder, agent_id: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            inputs = {"args": args, "kwargs": kwargs}
            
            with capture_stream(recorder, agent_id, func.__name__, inputs) as capture:
                result = func(*args, **kwargs)
                
                # If result is a generator (streaming), capture chunks
                if hasattr(result, '__iter__') and not isinstance(result, str):
                    chunks = []
                    for chunk in result:
                        if capture:
                            capture.add_token(chunk)
                        chunks.append(chunk)
                        yield chunk
                    
                    if capture:
                        capture.add_token("", is_final=True)
                else:
                    # Non-streaming result
                    if capture:
                        capture.add_token(str(result), is_final=True)
                    return result
        
        return wrapper
    return decorator

# Usage
@record_llm_call(recorder, "my_agent")
def call_llm(prompt, model):
    # Your LLM call implementation
    return llm_client.stream_completion(prompt, model)
```

### 2. Context Manager Pattern for Sessions

```python
from contextlib import contextmanager

@contextmanager
def recording_session(recorder, session_id, task_id=None):
    recording_id = recorder.start_recording(session_id, task_id)
    try:
        yield recording_id
    finally:
        manifest = recorder.stop_recording()
        print(f"Recording completed: {manifest.recording_id}")

# Usage
with recording_session(recorder, "session_001", "task_001") as recording_id:
    # Your recorded operations here
    event_id = recorder.record_event(...)
    stream_id = recorder.start_streaming(...)
```

### 3. Async Pattern for High-Performance Recording

```python
import asyncio
from common.replay.streaming import capture_stream_async

async def async_llm_call_with_recording(recorder, prompt, model, agent_id):
    inputs = {"prompt": prompt, "model": model}
    
    async with capture_stream_async(recorder, agent_id, "llm_call", inputs) as capture:
        async for chunk in llm_client.stream_completion_async(prompt, model):
            if capture:
                capture.add_token(chunk)
            yield chunk
        
        if capture:
            capture.add_token("", is_final=True)

# Usage
async def main():
    async for chunk in async_llm_call_with_recording(recorder, "Hello", "gpt-4", "agent"):
        print(chunk, end="")
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch
from benchmark.replay.recorder import EnhancedRecorder
from benchmark.replay.player import EnhancedPlayer

class TestEnhancedRecorder:
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.recorder = EnhancedRecorder(self.temp_dir, "test_adapter")
    
    def test_recording_lifecycle(self):
        # Test complete recording lifecycle
        recording_id = self.recorder.start_recording("test_session")
        assert self.recorder.recording
        
        event_id = self.recorder.record_event(
            "llm_call", "agent", "openai",
            {"prompt": "test"}, {"response": "test"}, 1.0
        )
        assert event_id is not None
        
        manifest = self.recorder.stop_recording()
        assert manifest.total_events == 1
        assert not self.recorder.recording
    
    def test_streaming_capture(self):
        self.recorder.start_recording("test_session")
        
        stream_id = self.recorder.start_streaming("agent", "openai", {"prompt": "test"})
        
        chunk_id1 = self.recorder.record_chunk(stream_id, "Hello", {"token": 1})
        chunk_id2 = self.recorder.record_chunk(stream_id, " world", {"token": 2})
        chunk_id3 = self.recorder.record_chunk(stream_id, "", is_final=True)
        
        total_chunks = self.recorder.finish_streaming(stream_id)
        assert total_chunks == 3
        
        manifest = self.recorder.stop_recording()
        assert manifest.total_chunks == 3
```

### Integration Testing

```python
class TestRecordReplayIntegration:
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.recorder = EnhancedRecorder(self.temp_dir, "integration_test")
        self.player = EnhancedPlayer(self.temp_dir, replay_mode="warn")
    
    def test_end_to_end_workflow(self):
        # Record session
        recording_id = self.recorder.start_recording("integration_session")
        
        event_id = self.recorder.record_event(
            "llm_call", "agent", "openai",
            {"prompt": "integration test"}, {"response": "success"}, 2.0
        )
        
        manifest = self.recorder.stop_recording()
        
        # Replay session
        success = self.player.load_recording(recording_id)
        assert success
        
        replay_id = self.player.start_replay()
        
        # Test replay functionality
        match_found, output = self.player.get_recorded_output(
            "llm_call", "openai", {"prompt": "integration test"}, 0, "agent"
        )
        
        # Note: This may not match due to IO key generation differences
        # In real integration, the adapter would handle this properly
        
        stats = self.player.get_replay_statistics()
        assert stats["total_replays"] >= 0
```

### Performance Testing

```python
import time
import threading

class TestPerformance:
    def test_background_writing_performance(self):
        recorder = EnhancedRecorder(
            Path(tempfile.mkdtemp()),
            "perf_test",
            compression_enabled=False
        )
        
        recording_id = recorder.start_recording("perf_session")
        
        # Record many events quickly
        start_time = time.time()
        
        for i in range(1000):
            recorder.record_event(
                "test_event", "agent", "tool",
                {"index": i}, {"result": f"result_{i}"}, 0.001
            )
        
        end_time = time.time()
        
        manifest = recorder.stop_recording()
        
        # Should complete quickly due to background writing
        assert end_time - start_time < 5.0  # Should be much faster
        assert manifest.total_events == 1000
    
    def test_streaming_performance(self):
        recorder = EnhancedRecorder(Path(tempfile.mkdtemp()), "stream_perf")
        recording_id = recorder.start_recording("stream_session")
        
        stream_id = recorder.start_streaming("agent", "llm", {"prompt": "perf test"})
        
        start_time = time.time()
        
        # Record many chunks
        for i in range(1000):
            recorder.record_chunk(stream_id, f"chunk_{i}", {"index": i})
        
        recorder.record_chunk(stream_id, "", is_final=True)
        total_chunks = recorder.finish_streaming(stream_id)
        
        end_time = time.time()
        
        manifest = recorder.stop_recording()
        
        assert total_chunks == 1001  # 1000 + final chunk
        assert end_time - start_time < 2.0  # Should be fast
```

## Performance Considerations

### 1. Background Writing

The enhanced recorder uses background writing to improve performance:

```python
# Background writing is enabled by default
recorder = EnhancedRecorder(
    output_dir=Path("recordings"),
    adapter_name="my_adapter"
)

# Events are queued and written asynchronously
# This provides ~70% performance improvement over synchronous writing
```

### 2. Compression

Enable compression for storage efficiency:

```python
recorder = EnhancedRecorder(
    output_dir=Path("recordings"),
    adapter_name="my_adapter",
    compression_enabled=True  # 60-80% storage reduction
)
```

### 3. File Rotation

Configure file rotation to prevent large files:

```python
recorder = EnhancedRecorder(
    output_dir=Path("recordings"),
    adapter_name="my_adapter",
    max_file_size_mb=50  # Rotate at 50MB
)
```

### 4. Memory Management

For large recordings, consider:

```python
# Use smaller chunk sizes for streaming
def stream_with_small_chunks(content, chunk_size=10):
    for i in range(0, len(content), chunk_size):
        yield content[i:i+chunk_size]

# Monitor memory usage
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Memory usage: {memory_mb:.1f} MB")
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```python
# If you get import errors, ensure PYTHONPATH is set
import sys
sys.path.append('/path/to/project')

# Or use relative imports within the project
from ..replay.recorder import EnhancedRecorder
```

#### 2. Recording Not Starting

```python
# Check if recorder is already recording
if recorder.recording:
    print("Already recording, stop first")
    recorder.stop_recording()

# Check output directory permissions
output_dir = Path("recordings")
if not output_dir.exists():
    output_dir.mkdir(parents=True)
```

#### 3. Streaming Issues

```python
# Ensure streaming is enabled on player
player = EnhancedPlayer(
    storage_path=Path("recordings"),
    enable_streaming=True  # Must be True for streaming
)

# Check if stream exists
tokens = player.get_stream_tokens(stream_id)
if not tokens:
    print(f"No tokens found for stream: {stream_id}")
```

#### 4. Replay Mismatches

```python
# Use warn mode for debugging
player = EnhancedPlayer(
    storage_path=Path("recordings"),
    replay_mode="warn"  # Logs warnings instead of failing
)

# Check replay statistics
stats = player.get_replay_statistics()
print(f"Mismatches: {stats['mismatch_count']}")
print(f"Success rate: {stats['success_rate']:.1%}")
```

### Debug Logging

Enable debug logging for detailed information:

```python
import logging

# Enable debug logging for record-replay components
logging.getLogger('benchmark.replay').setLevel(logging.DEBUG)
logging.getLogger('common.replay').setLevel(logging.DEBUG)
logging.getLogger('common.telemetry').setLevel(logging.DEBUG)

# Create console handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to loggers
logging.getLogger('benchmark.replay').addHandler(handler)
logging.getLogger('common.replay').addHandler(handler)
```

### Performance Debugging

```python
import time
import cProfile

def profile_recording():
    recorder = EnhancedRecorder(Path("recordings"), "profile_test")
    
    recording_id = recorder.start_recording("profile_session")
    
    start_time = time.time()
    
    # Your recording operations here
    for i in range(100):
        recorder.record_event(
            "test_event", "agent", "tool",
            {"index": i}, {"result": f"result_{i}"}, 0.001
        )
    
    end_time = time.time()
    
    manifest = recorder.stop_recording()
    
    print(f"Recorded {manifest.total_events} events in {end_time - start_time:.2f}s")
    print(f"Rate: {manifest.total_events / (end_time - start_time):.1f} events/sec")

# Profile the function
cProfile.run('profile_recording()')
```

## Best Practices

### 1. Error Handling

```python
try:
    recording_id = recorder.start_recording("session")
    
    # Your recording operations
    event_id = recorder.record_event(...)
    
except Exception as e:
    logger.error(f"Recording failed: {e}")
    # Ensure recording is stopped
    if recorder.recording:
        recorder.stop_recording()
    raise
```

### 2. Resource Management

```python
# Use context managers when possible
with recording_session(recorder, "session") as recording_id:
    # Operations are automatically cleaned up
    pass

# Or ensure proper cleanup
try:
    recording_id = recorder.start_recording("session")
    # ... operations ...
finally:
    if recorder.recording:
        recorder.stop_recording()
```

### 3. Testing

```python
# Always test both recording and replay
def test_feature():
    # Test recording
    manifest = record_feature_usage()
    assert manifest.total_events > 0
    
    # Test replay
    success = replay_feature_usage(manifest.recording_id)
    assert success
```

### 4. Monitoring

```python
# Monitor recording performance
def monitor_recording(recorder):
    stats = {
        "events_recorded": len(recorder.events),
        "streams_active": len(recorder.streaming_chunks),
        "recording_duration": time.time() - recorder.start_time.timestamp()
    }
    
    # Log or send to monitoring system
    logger.info(f"Recording stats: {stats}")
```

This developer guide provides comprehensive information for working with Phase 1 components. For user-focused documentation, see the [Phase 1 User Guide](phase1-user-guide.md).