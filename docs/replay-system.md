# Record-Replay System Documentation

## Overview

The Record-Replay system provides deterministic execution capabilities for AI agent workflows, enabling reproducible testing, debugging, and consistency evaluation. This system is part of the AI Dev Squad Enhancement platform and follows the architectural decisions outlined in ADR-008 and ADR-009.

## Architecture

### Core Components

1. **Recorder** (`benchmark/replay/recorder.py`)
   - Captures all IO edges during agent execution
   - Stores events in compressed JSONL format with integrity checking
   - Creates manifest files with metadata and hashes

2. **Player** (`benchmark/replay/player.py`)
   - Replays recorded sessions deterministically
   - Intercepts IO operations and substitutes recorded outputs
   - Validates input fingerprints for exact matching

3. **Interception Decorators**
   - `@intercept_llm_call()` - Captures LLM interactions
   - `@intercept_tool_call()` - Captures tool executions
   - `@intercept_sandbox_exec()` - Captures code execution
   - `@intercept_vcs_operation()` - Captures VCS operations

4. **Adapter Wrappers**
   - Framework-specific wrappers that integrate replay capabilities
   - Currently implemented: LangGraph, CrewAI
   - Maintains full compatibility with original adapters

### Storage Format

```
artifacts/<run_id>/
├── events.jsonl.zst         # Compressed telemetry events
├── manifest.yaml            # Metadata and integrity hashes
├── inputs/                  # Task inputs and fixtures
├── outputs/                 # Agent artifacts and files
└── diffs/                   # Git diffs if VCS used
```

### Event Schema

The system uses the existing telemetry schema with three new event types:

- `REPLAY_CHECKPOINT` - IO edge data for replay
- `RECORDING_NOTE` - Metadata and debugging information
- `REPLAY_ASSERT` - Validation results during replay

## Usage

### Basic Recording

```python
from benchmark.replay.recorder import Recorder

# Initialize recorder
recorder = Recorder(storage_path=Path("artifacts"))

# Start recording
run_id = "my_test_run"
recorder.start_recording(run_id, task_type="bugfix", framework="langgraph")

# ... execute agent workflow ...

# Stop recording
recorder.stop_recording()
```

### Basic Replay

```python
from benchmark.replay.player import Player

# Initialize player
player = Player(storage_path=Path("artifacts"))

# Load recording
success = player.load_recording("my_test_run")
if success:
    # Start replay
    replay_run_id = player.start_replay()
    
    # ... execute agent workflow (will use recorded outputs) ...
```

### Using Adapter Wrappers

#### LangGraph with Replay

```python
from langgraph_implementation.replay_wrapper import create_replay_adapter

# Create adapter in record mode
adapter = create_replay_adapter(config=my_config, replay_mode="record")

# Run task (will record all IO)
result = await adapter.run_task(task)

# Create adapter in replay mode
replay_adapter = create_replay_adapter(config=my_config, replay_mode="replay")

# Run same task (will use recorded outputs)
replay_result = await replay_adapter.run_task(task)
```

#### CrewAI with Replay

```python
from crewai_implementation.replay_wrapper import create_replay_adapter

# Similar usage pattern as LangGraph
adapter = create_replay_adapter(replay_mode="record")
result = await adapter.run_task(task)
```

### Manual Interception

```python
from benchmark.replay.player import intercept_llm_call, set_global_player

# Set up global player for interception
player = Player()
player.load_recording("my_recording")
set_global_player(player)

# Decorate functions that should be intercepted
@intercept_llm_call(adapter_name="my_adapter", agent_id="my_agent")
def my_llm_function(prompt: str):
    # This will be intercepted during replay
    return call_actual_llm(prompt)

# Function will use recorded output if available
result = my_llm_function("What is 2+2?")
```

## Deterministic Replay

### Lookup Keys

The system uses stable lookup keys to match recorded IO:

```
{event_type}:{adapter}:{agent_id}:{tool_name}:{call_index}
```

Example: `llm_call:langgraph:architect:chat_model:0`

### Input Fingerprinting

Input data is normalized and hashed using BLAKE3 to ensure exact matching:

1. Remove volatile fields (timestamps, UUIDs, etc.)
2. Normalize paths to relative
3. Sort dictionary keys
4. Generate BLAKE3 hash

### Replay Validation

During replay, the system:

1. Matches lookup keys
2. Validates input fingerprints
3. Returns recorded outputs
4. Logs assertion results
5. Falls back to normal execution on mismatch (non-strict mode)

## Configuration

### Replay Modes

- **normal** - Standard execution, no recording or replay
- **record** - Capture all IO for later replay
- **replay** - Use recorded outputs for deterministic execution

### Strict vs Non-Strict Replay

- **Strict mode** - Raises exceptions on replay mismatches
- **Non-strict mode** - Falls back to normal execution on mismatches

### Storage Configuration

```python
# Custom storage path
recorder = Recorder(storage_path=Path("/custom/path"))

# Compression settings (enabled by default)
session = RecordingSession(run_id, output_dir, compression=True)
```

## Testing

### Smoke Tests

Run the replay smoke tests to verify basic functionality:

```bash
make replay-smoke
```

Or directly with pytest:

```bash
pytest tests/test_replay_smoke.py -v
```

### Integration Tests

```bash
pytest tests/test_replay_wrapper.py -v
```

### Manual Testing

```bash
python examples/simple_replay_demo.py
```

## CI Integration

### Smoke Test in CI

The replay system includes lightweight smoke tests designed for CI:

```yaml
# Example CI configuration
- name: Run Replay Smoke Tests
  run: make replay-smoke
```

### Budget Constraints

Smoke tests are designed to complete within 5 seconds to meet CI budget requirements.

### Deterministic Testing

Uses MockLLM and MockTool classes for deterministic outputs in CI environments.

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration

2. **Recording Not Found**
   - Verify run_id exists in storage path
   - Check manifest.yaml file integrity

3. **Replay Mismatches**
   - Input data may have changed between recording and replay
   - Check input fingerprint validation
   - Use non-strict mode for debugging

4. **Performance Issues**
   - Enable compression for large recordings
   - Use selective recording for specific operations only

### Debug Mode

Enable debug logging for detailed replay information:

```python
import logging
logging.getLogger('benchmark.replay').setLevel(logging.DEBUG)
```

### Integrity Checking

Verify recording integrity:

```python
player = Player()
success = player.load_recording(run_id)
if not success:
    print("Recording failed integrity check")
```

## Best Practices

### Recording

1. Use descriptive run IDs
2. Include relevant metadata
3. Record complete workflows, not partial operations
4. Verify recordings before using for replay

### Replay

1. Use strict mode for critical tests
2. Validate replay results against expected outcomes
3. Handle replay mismatches gracefully
4. Clean up global state after replay

### Performance

1. Use compression for large recordings
2. Limit recording scope to necessary operations
3. Clean up old recordings regularly
4. Monitor storage usage

### Testing

1. Use deterministic mock components in tests
2. Verify replay consistency across multiple runs
3. Test both successful and failure scenarios
4. Include replay tests in CI pipeline

## Future Enhancements

### Planned Features

1. **Consistency Evaluation Integration**
   - Multi-run replay for consistency analysis
   - Variance calculation and reporting
   - Consensus analysis across runs

2. **Enhanced CLI Support**
   - Command-line tools for recording management
   - Replay validation utilities
   - Batch replay operations

3. **Advanced Filtering**
   - Selective replay of specific operations
   - Conditional recording based on criteria
   - Event filtering and transformation

4. **Performance Optimization**
   - Streaming replay for large recordings
   - Parallel replay execution
   - Memory-efficient event processing

### Integration Roadmap

1. **Week 1, Day 5**: Harden integrity checking and failure modes
2. **Week 2**: Integrate with consistency evaluation system
3. **Future**: Add support for remaining adapter frameworks

## API Reference

### Recorder Class

```python
class Recorder:
    def __init__(self, storage_path: Optional[Path] = None)
    def start_recording(self, run_id: str, **metadata) -> str
    def stop_recording(self) -> Optional[str]
    def record_io_edge(self, io_type: str, tool_name: str, 
                      input_data: Dict, output_data: Dict, **context)
    def is_recording(self) -> bool
```

### Player Class

```python
class Player:
    def __init__(self, storage_path: Optional[Path] = None)
    def load_recording(self, run_id: str) -> bool
    def start_replay(self, new_run_id: Optional[str] = None) -> str
    def get_recorded_output(self, io_type: str, tool_name: str, 
                           input_data: Dict, call_index: int, 
                           agent_id: str = "") -> Tuple[bool, Any]
    def replay_io_edge(self, io_type: str, tool_name: str, 
                      input_data: Dict, call_index: int, 
                      agent_id: str = "") -> Any
```

### Interception Decorators

```python
def intercept_llm_call(adapter_name: str, agent_id: str)
def intercept_tool_call(adapter_name: str, agent_id: str, tool_name: str)
def intercept_sandbox_exec(adapter_name: str, agent_id: str)
def intercept_vcs_operation(adapter_name: str, agent_id: str, operation: str)
```

### Wrapper Factories

```python
def create_replay_adapter(config: Optional[Dict] = None, 
                         replay_mode: str = "normal") -> ReplayAdapter
```

## Related Documentation

- [ADR-008: Telemetry Event Schema and OpenTelemetry Strategy](adr/008-telemetry-event-schema-and-otel-strategy.md)
- [ADR-009: Record-Replay Trust Model and Keys](adr/009-record-replay-trust-model-and-keys.md)
- [Adjustment Plan](requirements/v0.3/adjustment-plan.md)
- [Telemetry System Documentation](observability-developer-guide.md)