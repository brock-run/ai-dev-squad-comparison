# Replay System Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
# Install the replay system (already included in main installation)
make install
```

### 2. Record a Session

```python
from langgraph_implementation.replay_wrapper import create_replay_adapter
from common.agent_api import TaskSchema

# Create recording adapter
adapter = create_replay_adapter(replay_mode="record")

# Define your task
task = TaskSchema(
    id="test_task_001",
    type="bugfix",
    description="Fix the login bug",
    inputs={"code": "def login(): pass"}
)

# Run and record
result = await adapter.run_task(task)
print(f"Recording completed: {result}")
```

### 3. Replay the Session

```python
# Create replay adapter
replay_adapter = create_replay_adapter(replay_mode="replay")

# Set the recording to replay (if needed)
# task.replay_run_id = "langgraph_test_task_001_1234567890"

# Run with recorded outputs
replay_result = await replay_adapter.run_task(task)
print(f"Replay completed: {replay_result}")
```

### 4. Verify Determinism

```python
# Run multiple replays - should be identical
results = []
for i in range(3):
    adapter = create_replay_adapter(replay_mode="replay")
    result = await adapter.run_task(task)
    results.append(result)

# Check if all results are identical
all_identical = all(r.output == results[0].output for r in results)
print(f"Deterministic replay: {all_identical}")
```

## Common Patterns

### Pattern 1: Test with Replay

```python
import pytest
from your_adapter import create_replay_adapter

@pytest.mark.asyncio
async def test_with_replay():
    # Record once
    record_adapter = create_replay_adapter(replay_mode="record")
    original_result = await record_adapter.run_task(task)
    
    # Replay multiple times
    for i in range(5):
        replay_adapter = create_replay_adapter(replay_mode="replay")
        replay_result = await replay_adapter.run_task(task)
        assert replay_result.output == original_result.output
```

### Pattern 2: Manual Interception

```python
from benchmark.replay.player import intercept_llm_call, Player, set_global_player

# Setup player
player = Player()
player.load_recording("my_recording")
set_global_player(player)

@intercept_llm_call(adapter_name="my_app", agent_id="assistant")
def ask_llm(question: str) -> str:
    # This will use recorded response during replay
    return actual_llm_call(question)

# Use the function normally
answer = ask_llm("What is Python?")
```

### Pattern 3: Debugging with Replay

```python
# Record a failing session
adapter = create_replay_adapter(replay_mode="record")
try:
    result = await adapter.run_task(failing_task)
except Exception as e:
    print(f"Recorded failure: {e}")

# Replay to debug
replay_adapter = create_replay_adapter(replay_mode="replay")
# Add breakpoints or logging here
result = await replay_adapter.run_task(failing_task)
```

## Quick Commands

```bash
# Run smoke tests
make replay-smoke

# Run full replay tests
pytest tests/test_replay_*.py -v

# Run demo
python examples/simple_replay_demo.py

# Clean up recordings
rm -rf artifacts/
```

## Troubleshooting

### "No recording found"
- Check if recording was created successfully
- Verify run_id matches
- Check storage path

### "Replay mismatch"
- Input data changed between record and replay
- Use non-strict mode: `player.strict_mode = False`
- Check input fingerprinting

### "Import errors"
- Ensure dependencies installed: `make install`
- Check Python path includes project root

## Next Steps

1. Read the [full documentation](../replay-system.md)
2. Check out [examples](../../examples/simple_replay_demo.py)
3. Integrate with your CI pipeline
4. Explore consistency evaluation features