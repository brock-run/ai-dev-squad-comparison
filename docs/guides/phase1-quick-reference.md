# Phase 1: Enhanced Telemetry Integration - Quick Reference

## Quick Start

### Basic Recording
```python
from benchmark.replay.recorder import EnhancedRecorder

# Initialize
recorder = EnhancedRecorder(Path("recordings"), "my_adapter")

# Record session
recording_id = recorder.start_recording("session_001")
event_id = recorder.record_event("llm_call", "agent", "openai", 
                                 {"prompt": "Hello"}, {"response": "Hi"}, 1.5)
manifest = recorder.stop_recording()
```

### Basic Replay
```python
from benchmark.replay.player import EnhancedPlayer

# Initialize
player = EnhancedPlayer(Path("recordings"), replay_mode="warn")

# Replay session
success = player.load_recording(recording_id)
replay_id = player.start_replay()
match_found, output = player.get_recorded_output("llm_call", "openai", 
                                                 {"prompt": "Hello"}, 0, "agent")
```

### Streaming Capture
```python
from common.replay.streaming import StreamingLLMWrapper

# Wrap LLM client
wrapper = StreamingLLMWrapper(llm_client, recorder=recorder)

# Use normally - streaming is captured automatically
for chunk in wrapper.stream_completion("Hello", "gpt-4", "agent"):
    print(chunk, end="")
```

## API Quick Reference

### EnhancedRecorder

| Method | Purpose | Returns |
|--------|---------|---------|
| `start_recording(session_id, ...)` | Start recording session | `recording_id` |
| `record_event(type, agent, tool, inputs, outputs, duration)` | Record single event | `event_id` |
| `start_streaming(agent, tool, inputs)` | Start streaming capture | `stream_id` |
| `record_chunk(stream_id, content, metadata)` | Record streaming chunk | `chunk_id` |
| `finish_streaming(stream_id, tokens)` | Finish streaming | `total_chunks` |
| `checkpoint(label, metadata)` | Create checkpoint | `None` |
| `stop_recording()` | Stop and generate manifest | `RecordingManifest` |

### EnhancedPlayer

| Method | Purpose | Returns |
|--------|---------|---------|
| `load_recording(run_id)` | Load recorded session | `bool` |
| `start_replay(run_id, session_id, task_id)` | Start replay session | `replay_id` |
| `get_recorded_output(type, tool, inputs, index, agent)` | Get recorded output | `(bool, data)` |
| `replay_streaming_llm_call(prompt, model, agent, index)` | Replay streaming call | `Iterator[str]` |
| `get_replay_statistics()` | Get replay metrics | `Dict[str, Any]` |

### Streaming Components

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `StreamToken` | Single stream token | `to_dict()`, `from_dict()` |
| `StreamCapture` | Capture streaming data | `add_token()`, `get_full_content()` |
| `StreamReplay` | Replay streaming data | `replay_sync()`, `replay_async()` |
| `StreamingLLMWrapper` | Wrap LLM for recording | `stream_completion()` |

## Event Types

### Core Events
- `llm_call` - LLM API calls
- `tool_call` - Tool invocations  
- `task_start` / `task_complete` - Task lifecycle
- `agent_create` / `agent_destroy` - Agent lifecycle

### Streaming Events
- `LLM_CALL_STARTED` - Streaming LLM call begins
- `LLM_CALL_CHUNK` - Individual streaming chunk
- `LLM_CALL_FINISHED` - Streaming LLM call ends

### Record-Replay Events
- `RECORDING_NOTE` - Recording operations
- `REPLAY_START` / `REPLAY_STOP` - Replay lifecycle
- `REPLAY_MISMATCH` - Replay mismatches

## Configuration Options

### Recorder Configuration
```python
recorder = EnhancedRecorder(
    output_dir=Path("recordings"),
    adapter_name="my_adapter",
    adapter_version="1.0.0",
    compression_enabled=True,      # Enable compression
    max_file_size_mb=100          # File rotation size
)
```

### Player Configuration
```python
player = EnhancedPlayer(
    storage_path=Path("recordings"),
    replay_mode="strict",          # strict, warn, hybrid
    enable_streaming=True          # Enable streaming replay
)
```

## Replay Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `strict` | Fail on any mismatch | Exact deterministic testing |
| `warn` | Log warnings, continue | Debugging and development |
| `hybrid` | Use recorded when available, fallback to live | Partial replay scenarios |

## Common Patterns

### Context Manager Pattern
```python
from contextlib import contextmanager

@contextmanager
def recording_session(recorder, session_id):
    recording_id = recorder.start_recording(session_id)
    try:
        yield recording_id
    finally:
        recorder.stop_recording()

# Usage
with recording_session(recorder, "session_001") as recording_id:
    # Your operations here
    pass
```

### Decorator Pattern
```python
from functools import wraps

def record_llm_call(recorder, agent_id):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Record the function call
            result = func(*args, **kwargs)
            recorder.record_event("llm_call", agent_id, func.__name__, 
                                 {"args": args, "kwargs": kwargs}, 
                                 {"result": result}, 0.0)
            return result
        return wrapper
    return decorator
```

### Async Streaming Pattern
```python
from common.replay.streaming import capture_stream_async

async def async_llm_call(recorder, prompt, model, agent_id):
    inputs = {"prompt": prompt, "model": model}
    async with capture_stream_async(recorder, agent_id, "llm", inputs) as capture:
        async for chunk in llm_client.stream_async(prompt, model):
            if capture:
                capture.add_token(chunk)
            yield chunk
```

## Error Handling

### Recording Errors
```python
try:
    recording_id = recorder.start_recording("session")
    # ... operations ...
except Exception as e:
    logger.error(f"Recording failed: {e}")
    if recorder.recording:
        recorder.stop_recording()
    raise
```

### Replay Errors
```python
try:
    success = player.load_recording(recording_id)
    if not success:
        raise ValueError(f"Could not load recording: {recording_id}")
    
    replay_id = player.start_replay()
    # ... replay operations ...
    
except ReplayMismatchError as e:
    logger.warning(f"Replay mismatch: {e}")
    # Handle mismatch appropriately
```

## Debugging

### Enable Debug Logging
```python
import logging
logging.getLogger('benchmark.replay').setLevel(logging.DEBUG)
logging.getLogger('common.replay').setLevel(logging.DEBUG)
```

### Check Recording Status
```python
print(f"Recording active: {recorder.recording}")
print(f"Events recorded: {len(recorder.events)}")
print(f"Active streams: {len(recorder.streaming_chunks)}")
```

### Analyze Replay Issues
```python
stats = player.get_replay_statistics()
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Mismatches: {stats['mismatch_count']}")
print(f"Total replays: {stats['total_replays']}")
```

## Performance Tips

### Recording Performance
- Enable compression: `compression_enabled=True`
- Use appropriate file rotation: `max_file_size_mb=50`
- Background writing is automatic
- Monitor memory usage for large sessions

### Replay Performance
- Use "hybrid" mode for faster replay
- Disable timing preservation for speed: `preserve_timing=False`
- Load recordings once, replay multiple times
- Use appropriate replay mode for your use case

## Common Issues

### Import Errors
```python
# Ensure PYTHONPATH is set
import sys
sys.path.append('/path/to/project')
```

### Recording Not Starting
```python
# Check if already recording
if recorder.recording:
    recorder.stop_recording()

# Check directory permissions
output_dir.mkdir(parents=True, exist_ok=True)
```

### Replay Mismatches
```python
# Use warn mode for debugging
player.replay_mode = "warn"

# Check input fingerprints
stats = player.get_replay_statistics()
if stats['mismatch_count'] > 0:
    # Investigate mismatch details
    pass
```

### Streaming Issues
```python
# Ensure streaming is enabled
player.enable_streaming = True

# Check if streams exist
streams = player.get_recorded_streams(recording_id)
print(f"Available streams: {list(streams.keys())}")
```

## Integration Checklist

- [ ] Import Phase 1 components
- [ ] Initialize recorder with adapter name
- [ ] Configure replay mode appropriately
- [ ] Wrap LLM clients with StreamingLLMWrapper
- [ ] Add error handling for recording/replay
- [ ] Enable debug logging for development
- [ ] Test record/replay cycle
- [ ] Monitor performance and statistics
- [ ] Document adapter-specific patterns

## Links

- [Developer Guide](phase1-developer-guide.md) - Comprehensive technical documentation
- [User Guide](phase1-user-guide.md) - User-focused documentation
- [Enhanced Telemetry Integration](../enhanced-telemetry-integration.md) - Complete technical specification