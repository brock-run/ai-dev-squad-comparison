"""
Demonstration of the record-replay functionality.

This example shows how to use the replay system to record agent executions
and then replay them deterministically.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from benchmark.replay.recorder import Recorder
from benchmark.replay.player import Player, set_global_player
from common.telemetry.schema import EventType, create_event

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_basic_recorder():
    """Demonstrate basic recording functionality."""
    print("=== Basic Recorder Demo ===")
    
    # For now, just demonstrate the recorder initialization
    # The actual recording will be integrated with the telemetry system
    recorder = Recorder(storage_path=Path("demo_artifacts"))
    
    run_id = "demo_run_001"
    print(f"Recorder initialized for run: {run_id}")
    print(f"Storage path: {recorder.storage_path}")
    
    # Create the run directory manually for demo
    run_dir = recorder.storage_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple manifest file
    import yaml
    manifest = {
        "run_id": run_id,
        "timestamp": "2024-01-01T00:00:00Z",
        "framework": "demo",
        "task_type": "demo",
        "io_edges": [
            {
                "lookup_key": "llm_call:demo_agent:chat_model:0",
                "input_fingerprint": "abc123",
                "output_data": {"response": "Hello! How can I help you today?", "tokens": 12}
            },
            {
                "lookup_key": "tool_call:demo_agent:file_writer:1", 
                "input_fingerprint": "def456",
                "output_data": {"success": True, "bytes_written": 13}
            }
        ]
    }
    
    with open(run_dir / "manifest.yaml", "w") as f:
        yaml.dump(manifest, f)
    
    print(f"Demo recording created for run: {run_id}")
    print(f"Artifacts saved to: {recorder.storage_path / run_id}")
    
    return run_id

def demo_basic_player(run_id: str):
    """Demonstrate basic replay functionality."""
    print("\n=== Basic Player Demo ===")
    
    # Create player
    player = Player(storage_path=Path("demo_artifacts"))
    
    # Load recording
    success = player.load_recording(run_id)
    if not success:
        print(f"Failed to load recording: {run_id}")
        return
    
    print(f"Loaded recording: {run_id}")
    print(f"Recorded IO count: {player.get_recorded_io_count()}")
    print(f"Recorded IO keys: {player.list_recorded_io_keys()}")
    
    # Start replay
    replay_run_id = player.start_replay()
    print(f"Started replay with ID: {replay_run_id}")
    
    # Try to replay the recorded operations
    try:
        # Replay LLM call
        match_found, output = player.get_recorded_output(
            io_type="llm_call",
            tool_name="chat_model", 
            input_data={"prompt": "Hello, world!", "temperature": 0.7},
            call_index=0,
            agent_id="demo_agent"
        )
        
        if match_found:
            print(f"✓ LLM call replay successful: {output}")
        else:
            print("✗ LLM call replay failed")
        
        # Replay tool call
        match_found, output = player.get_recorded_output(
            io_type="tool_call",
            tool_name="file_writer",
            input_data={"filename": "demo.txt", "content": "Hello, world!"},
            call_index=1,
            agent_id="demo_agent"
        )
        
        if match_found:
            print(f"✓ Tool call replay successful: {output}")
        else:
            print("✗ Tool call replay failed")
            
    except Exception as e:
        print(f"Replay error: {e}")

def demo_interception_decorators():
    """Demonstrate the interception decorators."""
    print("\n=== Interception Decorators Demo ===")
    
    from benchmark.replay.player import (
        intercept_llm_call, intercept_tool_call, set_global_player
    )
    
    # Create a player and set it globally
    player = Player(storage_path=Path("demo_artifacts"))
    set_global_player(player)
    
    @intercept_llm_call(adapter_name="demo", agent_id="test_agent")
    def mock_llm_call(prompt: str, temperature: float = 0.7):
        """Mock LLM call that can be intercepted."""
        return f"Response to: {prompt} (temp={temperature})"
    
    @intercept_tool_call(adapter_name="demo", agent_id="test_agent", tool_name="calculator")
    def mock_calculator(operation: str, a: int, b: int):
        """Mock calculator tool that can be intercepted."""
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        else:
            return "Unknown operation"
    
    # Test normal execution (no recording loaded)
    print("Normal execution (no replay):")
    result1 = mock_llm_call("What is 2+2?")
    print(f"  LLM result: {result1}")
    
    result2 = mock_calculator("add", 2, 2)
    print(f"  Calculator result: {result2}")
    
    # Clean up
    set_global_player(None)

def main():
    """Run the complete demo."""
    print("Record-Replay System Demo")
    print("=" * 50)
    
    # Demo recording
    run_id = demo_basic_recorder()
    
    # Demo replay
    demo_basic_player(run_id)
    
    # Demo decorators
    demo_interception_decorators()
    
    print("\n=== Demo Complete ===")
    print("Check the 'demo_artifacts' directory for recorded sessions.")

if __name__ == "__main__":
    main()