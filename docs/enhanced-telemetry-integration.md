# Enhanced Telemetry Integration (Phase 1)

## Overview

Phase 1 of the Record-Replay Enhancement Project integrates the foundation components with the existing telemetry system and adds comprehensive streaming capture capabilities. This phase establishes the groundwork for advanced replay features while providing immediate value through enhanced observability and debugging capabilities.

## Key Features

### 1. Enhanced Telemetry Schema

The telemetry schema has been extended with record-replay specific event types:

```python
# New event types for record-replay
RECORDING_START = "recording.start"
RECORDING_STOP = "recording.stop" 
RECORDING_CHECKPOINT = "recording.checkpoint"
REPLAY_START = "replay.start"
REPLAY_STOP = "replay.stop"
REPLAY_MISMATCH = "replay.mismatch"

# Streaming events for LLM calls
LLM_CALL_START = "llm.call.start"
LLM_CALL_CHUNK = "llm.call.chunk"
LLM_CALL_FINISH = "llm.call.finish"

# IO events for record-replay
IO_READ = "io.read"
IO_WRITE = "io.write"
IO_NETWORK = "io.network"
```

### 2. Enhanced Recorder

The `EnhancedRecorder` class provides:

- **Telemetry Integration**: Automatic telemetry event generation for all recording operations
- **Streaming Support**: Capture streaming data like LLM token streams with proper timing
- **Background Writing**: Asynchronous writing for improved performance
- **Compression**: Optional zstd compression for storage efficiency
- **File Rotation**: Automatic file rotation based on size limits
- **Provenance Tracking**: Comprehensive manifest generation with git SHA, config digests, etc.

#### Usage Example

```python
from benchmark.replay.recorder import EnhancedRecorder

# Initialize recorder
recorder = EnhancedRecorder(
    output_dir=Path("recordings"),
    adapter_name="my_adapter",
    adapter_version="1.0.0",
    compression_enabled=True
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
    duration=1.5
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

# Stop recording
manifest = recorder.stop_recording()
```

### 3. Enhanced Player

The `EnhancedPlayer` class provides:

- **Streaming Replay**: Replay streaming data with timing preservation
- **Multiple Replay Modes**: Strict, warn, and hybrid modes for different use cases
- **Mismatch Detection**: Comprehensive mismatch detection with detailed reporting
- **Performance Analysis**: Stream timing analysis and performance metrics
- **Telemetry Integration**: Automatic telemetry events for replay operations

#### Usage Example

```python
from benchmark.replay.player import EnhancedPlayer

# Initialize player
player = EnhancedPlayer(
    storage_path=Path("recordings"),
    replay_mode="strict",
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

### 4. Streaming Support

The streaming support system provides comprehensive tools for capturing and replaying streaming data:

#### StreamCapture

Captures streaming data during recording:

```python
from common.replay.streaming import capture_stream

with capture_stream(recorder, "agent_id", "tool_name", inputs) as capture:
    for chunk in llm_stream:
        capture.add_token(chunk)
```

#### StreamReplay

Replays streaming data with timing preservation:

```python
from common.replay.streaming import StreamReplay

replay = StreamReplay(recorded_tokens)
replay.set_timing_mode(preserve_timing=True)

for token in replay.replay_sync():
    print(token.content, end="")
```

#### StreamingLLMWrapper

Wraps LLM clients to support both recording and replay:

```python
from common.replay.streaming import StreamingLLMWrapper

wrapper = StreamingLLMWrapper(llm_client, recorder=recorder)

# Records streaming automatically
for chunk in wrapper.stream_completion("Hello", "gpt-4", "agent_id"):
    print(chunk, end="")
```

### 5. Telemetry Events

The system generates comprehensive telemetry events:

#### Recording Events

- `RECORDING_START`: When recording begins
- `RECORDING_STOP`: When recording ends
- `RECORDING_CHECKPOINT`: Manual checkpoints during recording

#### Replay Events

- `REPLAY_START`: When replay begins
- `REPLAY_STOP`: When replay ends
- `REPLAY_MISMATCH`: When replay encounters mismatches

#### Streaming Events

- `LLM_CALL_START`: When streaming LLM call begins
- `LLM_CALL_CHUNK`: For each streaming chunk
- `LLM_CALL_FINISH`: When streaming completes

## Architecture

### Component Integration

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

### Data Flow

1. **Recording Phase**:
   - Adapter calls are intercepted
   - Events are processed through foundation components
   - Telemetry events are generated
   - Data is written to storage with compression

2. **Replay Phase**:
   - Recorded data is loaded and validated
   - IO operations are matched using fingerprints
   - Mismatches are detected and handled
   - Telemetry events track replay progress

### Storage Format

Recordings are stored with the following structure:

```
recordings/
├── rec_abc123_1234567890/
│   ├── manifest.json                 # Recording metadata
│   ├── rec_abc123_events_000.jsonl   # Event data (optionally compressed)
│   ├── rec_abc123_chunks.jsonl       # Streaming chunks
│   └── rec_abc123_checkpoints.jsonl  # Manual checkpoints
```

## Configuration

### Recorder Configuration

```python
recorder = EnhancedRecorder(
    output_dir=Path("recordings"),
    adapter_name="my_adapter",
    adapter_version="1.0.0",
    compression_enabled=True,      # Enable zstd compression
    max_file_size_mb=100          # Rotate files at 100MB
)
```

### Player Configuration

```python
player = EnhancedPlayer(
    storage_path=Path("recordings"),
    replay_mode="strict",          # strict, warn, or hybrid
    enable_streaming=True          # Enable streaming replay
)
```

### Replay Modes

- **Strict Mode**: Fails on any mismatch
- **Warn Mode**: Logs warnings but continues
- **Hybrid Mode**: Uses recorded data even with mismatches

## Performance Considerations

### Recording Performance

- **Background Writing**: Events are queued and written asynchronously
- **Compression**: Optional zstd compression reduces storage by ~70%
- **File Rotation**: Prevents individual files from becoming too large
- **Redaction**: Sensitive data is filtered before storage

### Replay Performance

- **Lazy Loading**: Data is loaded on-demand
- **Streaming Optimization**: Streaming data preserves timing characteristics
- **Memory Management**: Large recordings are processed in chunks

## Monitoring and Observability

### Telemetry Dashboard

The enhanced system integrates with the existing telemetry dashboard to provide:

- Recording session metrics
- Replay success rates
- Stream performance analysis
- Mismatch detection reports

### Metrics

Key metrics tracked include:

- **Recording Metrics**:
  - Events per second
  - Storage efficiency
  - Compression ratios
  - Stream capture rates

- **Replay Metrics**:
  - Match success rates
  - Mismatch types and frequencies
  - Replay performance
  - Stream timing accuracy

## Testing

### Unit Tests

Comprehensive unit tests cover:

- Enhanced recorder functionality
- Enhanced player functionality
- Streaming support components
- Telemetry integration

Run tests with:

```bash
python -m pytest tests/test_enhanced_telemetry_integration.py -v
```

### Integration Tests

Integration tests verify:

- End-to-end record/replay cycles
- Streaming data integrity
- Telemetry event generation
- Cross-component compatibility

### Demo Script

Run the demo to see all features in action:

```bash
python examples/enhanced_telemetry_demo.py
```

## Migration Guide

### From Basic Recorder

```python
# Old
from benchmark.replay.recorder import Recorder
recorder = Recorder(output_dir)

# New
from benchmark.replay.recorder import EnhancedRecorder
recorder = EnhancedRecorder(
    output_dir=output_dir,
    adapter_name="my_adapter"
)
```

### From Basic Player

```python
# Old
from benchmark.replay.player import Player
player = Player(storage_path)

# New
from benchmark.replay.player import EnhancedPlayer
player = EnhancedPlayer(
    storage_path=storage_path,
    replay_mode="strict"
)
```

## Troubleshooting

### Common Issues

1. **Recording Not Starting**:
   - Check output directory permissions
   - Verify telemetry system is available
   - Check for sufficient disk space

2. **Replay Mismatches**:
   - Use `warn` or `hybrid` mode for debugging
   - Check input fingerprint generation
   - Verify IO key consistency

3. **Streaming Issues**:
   - Ensure streaming is enabled on player
   - Check stream ID generation consistency
   - Verify chunk ordering

### Debug Logging

Enable debug logging for detailed information:

```python
import logging
logging.getLogger('benchmark.replay').setLevel(logging.DEBUG)
logging.getLogger('common.replay').setLevel(logging.DEBUG)
```

## Future Enhancements

Phase 1 establishes the foundation for future enhancements:

- **Phase 2**: Advanced replay modes with AI-powered mismatch resolution
- **Phase 3**: Distributed recording and replay across multiple agents
- **Phase 4**: Real-time replay monitoring and intervention

## API Reference

### EnhancedRecorder

#### Methods

- `start_recording(session_id, task_id, ...)` - Start recording session
- `record_event(event_type, agent_id, ...)` - Record single event
- `start_streaming(agent_id, tool_name, inputs)` - Start streaming capture
- `record_chunk(stream_id, content, metadata)` - Record streaming chunk
- `finish_streaming(stream_id, total_tokens)` - Finish streaming
- `checkpoint(label, metadata)` - Create checkpoint
- `stop_recording()` - Stop recording and generate manifest

### EnhancedPlayer

#### Methods

- `load_recording(run_id)` - Load recorded session
- `start_replay(new_run_id, session_id, task_id)` - Start replay
- `get_recorded_output(io_type, tool_name, ...)` - Get recorded output
- `replay_streaming_llm_call(prompt, model, ...)` - Replay streaming call
- `get_replay_statistics()` - Get replay metrics
- `analyze_stream_performance(stream_id)` - Analyze stream timing

### Streaming Components

#### StreamCapture

- `add_token(content, metadata, is_final)` - Add streaming token
- `get_full_content()` - Get complete content
- `get_metadata_summary()` - Get stream metadata

#### StreamReplay

- `set_timing_mode(preserve_timing)` - Configure timing preservation
- `replay_sync()` - Synchronous replay iterator
- `replay_async()` - Asynchronous replay iterator

#### StreamingLLMWrapper

- `stream_completion(prompt, model, agent_id, ...)` - Stream with recording
- `stream_completion_async(...)` - Async stream with recording

## Conclusion

Phase 1 provides a solid foundation for enhanced record-replay capabilities with comprehensive telemetry integration and streaming support. The system is designed for production use with proper error handling, performance optimization, and extensive testing.

The enhanced telemetry integration enables better debugging, monitoring, and analysis of AI agent behavior, while the streaming support ensures that real-time interactions are captured and replayed accurately.