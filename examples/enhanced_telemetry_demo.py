#!/usr/bin/env python3
"""
Enhanced Telemetry Integration Demo

Demonstrates the integration between record-replay system and telemetry,
including streaming support and comprehensive event tracking.

Phase 1: Enhanced Telemetry Integration
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import components
from benchmark.replay.recorder import EnhancedRecorder
from benchmark.replay.player import EnhancedPlayer
from common.replay.streaming import (
    StreamingLLMWrapper, capture_stream, analyze_stream_timing,
    split_content_into_chunks
)

# Mock LLM client for demonstration
class MockLLMClient:
    """Mock LLM client that simulates streaming responses."""
    
    def __init__(self, delay_ms: int = 50):
        self.delay_ms = delay_ms
    
    def stream_completion(self, prompt: str, model: str, **kwargs):
        """Simulate streaming completion."""
        # Generate response based on prompt
        if "story" in prompt.lower():
            response = "Once upon a time, in a land far away, there lived a brave knight who embarked on an epic quest to save the kingdom from an ancient dragon."
        elif "code" in prompt.lower():
            response = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        else:
            response = f"This is a response to: {prompt}"
        
        # Split into chunks and yield with delays
        chunks = split_content_into_chunks(response, chunk_size=10, preserve_words=True)
        
        for chunk in chunks:
            time.sleep(self.delay_ms / 1000.0)  # Simulate network delay
            yield chunk
    
    async def stream_completion_async(self, prompt: str, model: str, **kwargs):
        """Simulate async streaming completion."""
        if "story" in prompt.lower():
            response = "Once upon a time, in a land far away, there lived a brave knight who embarked on an epic quest to save the kingdom from an ancient dragon."
        elif "code" in prompt.lower():
            response = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        else:
            response = f"This is an async response to: {prompt}"
        
        chunks = split_content_into_chunks(response, chunk_size=10, preserve_words=True)
        
        for chunk in chunks:
            await asyncio.sleep(self.delay_ms / 1000.0)
            yield chunk


def demonstrate_enhanced_recording():
    """Demonstrate enhanced recording with telemetry integration."""
    print("\\n" + "="*60)
    print("ENHANCED RECORDING DEMONSTRATION")
    print("="*60)
    
    # Create temporary directory for demo
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Demo artifacts will be stored in: {temp_dir}")
    
    # Initialize enhanced recorder
    recorder = EnhancedRecorder(
        output_dir=temp_dir,
        adapter_name="demo_adapter",
        adapter_version="1.0.0",
        compression_enabled=True,
        max_file_size_mb=10
    )
    
    print(f"\\nInitialized recorder: {recorder.adapter_name} v{recorder.adapter_version}")
    print(f"Compression enabled: {recorder.compression_enabled}")
    
    # Start recording session
    session_id = "demo_session_001"
    task_id = "telemetry_demo_task"
    
    recording_id = recorder.start_recording(
        session_id=session_id,
        task_id=task_id,
        config_digest="demo_config_hash_123",
        model_ids=["gpt-4", "claude-3-sonnet"],
        seeds=[42, 123, 456]
    )
    
    print(f"\\nStarted recording session: {session_id}")
    print(f"Recording ID: {recording_id}")
    
    # Record various types of events
    print("\\nRecording events...")
    
    # 1. LLM call event
    llm_event_id = recorder.record_event(
        event_type="llm_call",
        agent_id="demo_agent",
        tool_name="openai_gpt4",
        inputs={
            "prompt": "Explain quantum computing in simple terms",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 150
        },
        outputs={
            "response": "Quantum computing is a revolutionary approach to computation that harnesses quantum mechanics...",
            "tokens_used": 145,
            "finish_reason": "stop"
        },
        duration=2.3,
        metadata={
            "provider": "openai",
            "cost_usd": 0.0023,
            "latency_ms": 2300
        },
        session_id=session_id,
        task_id=task_id
    )
    print(f"  ✓ Recorded LLM call event: {llm_event_id}")
    
    # 2. Tool call event
    tool_event_id = recorder.record_event(
        event_type="tool_call",
        agent_id="demo_agent",
        tool_name="file_writer",
        inputs={
            "filename": "quantum_explanation.txt",
            "content": "Quantum computing explanation...",
            "mode": "write"
        },
        outputs={
            "success": True,
            "bytes_written": 256,
            "file_path": "/tmp/quantum_explanation.txt"
        },
        duration=0.1,
        metadata={
            "file_size": 256,
            "permissions": "644"
        },
        session_id=session_id,
        task_id=task_id
    )
    print(f"  ✓ Recorded tool call event: {tool_event_id}")
    
    # 3. Streaming LLM call
    print("\\nRecording streaming LLM call...")
    
    stream_id = recorder.start_streaming(
        agent_id="demo_agent",
        tool_name="openai_gpt4_stream",
        inputs={
            "prompt": "Tell me a short story about AI",
            "model": "gpt-4",
            "stream": True
        },
        session_id=session_id,
        task_id=task_id
    )
    
    print(f"  Started stream: {stream_id}")
    
    # Simulate streaming chunks
    story_chunks = [
        "Once upon a time, ",
        "there was an AI named ",
        "Claude who loved to help ",
        "humans solve complex problems. ",
        "Every day, Claude would ",
        "learn something new and ",
        "share knowledge with curiosity ",
        "and kindness."
    ]
    
    for i, chunk in enumerate(story_chunks):
        chunk_id = recorder.record_chunk(
            stream_id=stream_id,
            content=chunk,
            metadata={
                "chunk_index": i,
                "token_count": len(chunk.split()),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        print(f"    ✓ Recorded chunk {i+1}: '{chunk.strip()}'")
        time.sleep(0.1)  # Simulate streaming delay
    
    # Final chunk
    final_chunk_id = recorder.record_chunk(
        stream_id=stream_id,
        content="",
        metadata={"final": True},
        is_final=True
    )
    
    total_chunks = recorder.finish_streaming(stream_id, total_tokens=len(story_chunks))
    print(f"  ✓ Finished streaming: {total_chunks} chunks recorded")
    
    # 4. Create checkpoint
    recorder.checkpoint(
        label="after_story_generation",
        metadata={
            "events_recorded": len(recorder.events),
            "streams_active": len(recorder.streaming_chunks),
            "checkpoint_reason": "demo_milestone"
        }
    )
    print("  ✓ Created checkpoint: after_story_generation")
    
    # 5. Record error event
    error_event_id = recorder.record_event(
        event_type="tool_error",
        agent_id="demo_agent",
        tool_name="web_scraper",
        inputs={
            "url": "https://invalid-url-demo.com",
            "timeout": 30
        },
        outputs={
            "error": "Connection timeout",
            "error_code": "TIMEOUT",
            "retry_count": 3
        },
        duration=30.0,
        metadata={
            "error_type": "network",
            "recoverable": True
        },
        session_id=session_id,
        task_id=task_id
    )
    print(f"  ✓ Recorded error event: {error_event_id}")
    
    # Stop recording and generate manifest
    print("\\nStopping recording...")
    manifest = recorder.stop_recording()
    
    print(f"\\nRecording completed!")
    print(f"  Recording ID: {manifest.recording_id}")
    print(f"  Total events: {manifest.total_events}")
    print(f"  Total chunks: {manifest.total_chunks}")
    print(f"  Artifacts size: {manifest.artifacts_size_bytes / 1024:.1f} KB")
    print(f"  Duration: {(manifest.end_time - manifest.start_time).total_seconds():.1f} seconds")
    print(f"  Compression: {manifest.compression_enabled}")
    print(f"  Redaction applied: {manifest.redaction_applied}")
    
    return temp_dir, recording_id


def demonstrate_enhanced_replay(artifacts_dir: Path, recording_id: str):
    """Demonstrate enhanced replay with telemetry integration."""
    print("\\n" + "="*60)
    print("ENHANCED REPLAY DEMONSTRATION")
    print("="*60)
    
    # Initialize enhanced player
    player = EnhancedPlayer(
        storage_path=artifacts_dir,
        replay_mode="strict",
        enable_streaming=True
    )
    
    print(f"Initialized player: mode={player.replay_mode}, streaming={player.enable_streaming}")
    
    # Load recording
    print(f"\\nLoading recording: {recording_id}")
    success = player.load_recording(recording_id)
    
    if not success:
        print("❌ Failed to load recording")
        return
    
    print("✓ Recording loaded successfully")
    
    # Display recording info
    stats = player.get_replay_statistics()
    print(f"  Loaded IOs: {stats['loaded_ios']}")
    print(f"  Loaded streams: {stats['loaded_streams']}")
    
    # Start replay session
    replay_session_id = player.start_replay(
        session_id="demo_replay_session",
        task_id="telemetry_replay_demo"
    )
    
    print(f"\\nStarted replay session: {replay_session_id}")
    
    # Demonstrate IO replay
    print("\\nTesting IO replay...")
    
    # Try to replay an LLM call (this would normally be called by adapter)
    try:
        # This is a simplified example - real adapters would use the interception decorators
        match_found, output = player.get_recorded_output(
            io_type="llm_call",
            tool_name="openai_gpt4",
            input_data={
                "prompt": "Explain quantum computing in simple terms",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 150
            },
            call_index=0,
            agent_id="demo_agent",
            session_id="demo_replay_session"
        )
        
        if match_found:
            print("  ✓ Successfully matched LLM call")
            print(f"    Response preview: {str(output.get('response', ''))[:50]}...")
        else:
            print("  ⚠ No matching LLM call found")
            
    except Exception as e:
        print(f"  ❌ Error during replay: {e}")
    
    # Test streaming replay
    print("\\nTesting streaming replay...")
    
    # List available streams
    stream_keys = [key for key in player._recorded_streams.keys()]
    if stream_keys:
        stream_id = stream_keys[0]
        print(f"  Found stream: {stream_id}")
        
        # Get stream tokens
        tokens = player.get_stream_tokens(stream_id)
        if tokens:
            print(f"  Stream has {len(tokens)} tokens")
            
            # Analyze stream timing
            timing_analysis = player.analyze_stream_performance(stream_id)
            if timing_analysis:
                print(f"  Stream analysis:")
                print(f"    Duration: {timing_analysis['total_duration_seconds']:.2f}s")
                print(f"    Tokens/sec: {timing_analysis['tokens_per_second']:.1f}")
                print(f"    Avg delay: {timing_analysis['average_delay_seconds']*1000:.1f}ms")
            
            # Replay stream
            print("  Replaying stream...")
            replay = player.replay_stream(stream_id, preserve_timing=False)
            if replay:
                content_parts = []
                for token in replay.replay_sync():
                    if not token.is_final:
                        content_parts.append(token.content)
                        print(f"    Chunk: '{token.content}'")
                
                full_content = "".join(content_parts)
                print(f"  ✓ Stream replay complete: '{full_content[:50]}...'")
        else:
            print("  ⚠ No tokens found for stream")
    else:
        print("  ⚠ No streams found in recording")
    
    # Display final statistics
    final_stats = player.get_replay_statistics()
    print(f"\\nReplay Statistics:")
    print(f"  Total replays attempted: {final_stats['total_replays']}")
    print(f"  Mismatches: {final_stats['mismatch_count']}")
    print(f"  Success rate: {final_stats['success_rate']:.1%}")


def demonstrate_streaming_wrapper():
    """Demonstrate streaming LLM wrapper with record/replay."""
    print("\\n" + "="*60)
    print("STREAMING WRAPPER DEMONSTRATION")
    print("="*60)
    
    # Create mock LLM client
    llm_client = MockLLMClient(delay_ms=100)
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    # Initialize recorder
    recorder = EnhancedRecorder(
        output_dir=temp_dir,
        adapter_name="streaming_demo"
    )
    
    # Create streaming wrapper
    wrapper = StreamingLLMWrapper(llm_client, recorder=recorder)
    
    print("Initialized streaming wrapper with mock LLM client")
    
    # Start recording
    recording_id = recorder.start_recording("streaming_demo_session")
    print(f"Started recording: {recording_id}")
    
    # Test streaming completion
    print("\\nTesting streaming completion...")
    
    prompts = [
        "Tell me a short story",
        "Write a simple Python function",
        "Explain machine learning"
    ]
    
    for i, prompt in enumerate(prompts):
        print(f"\\n  Prompt {i+1}: {prompt}")
        print("  Response: ", end="", flush=True)
        
        chunks = []
        for chunk in wrapper.stream_completion(
            prompt=prompt,
            model="gpt-4",
            agent_id=f"demo_agent_{i}",
            temperature=0.7
        ):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        
        print(f"\\n  ✓ Received {len(chunks)} chunks")
    
    # Stop recording
    manifest = recorder.stop_recording()
    print(f"\\nRecording stopped: {manifest.total_events} events, {manifest.total_chunks} chunks")
    
    # Now test replay
    print("\\nTesting replay mode...")
    
    player = EnhancedPlayer(storage_path=temp_dir, enable_streaming=True)
    player.load_recording(recording_id)
    player.start_replay()
    
    # Create wrapper in replay mode
    replay_wrapper = StreamingLLMWrapper(llm_client, player=player)
    
    print("Testing replay of first prompt...")
    print("  Replayed response: ", end="", flush=True)
    
    # This would work if the stream IDs match between recording and replay
    try:
        for chunk in replay_wrapper.stream_completion(
            prompt=prompts[0],
            model="gpt-4",
            agent_id="demo_agent_0"
        ):
            print(chunk, end="", flush=True)
        print("\\n  ✓ Replay successful")
    except Exception as e:
        print(f"\\n  ⚠ Replay failed: {e}")
        print("    (This is expected in demo due to stream ID generation)")


async def demonstrate_async_streaming():
    """Demonstrate async streaming capabilities."""
    print("\\n" + "="*60)
    print("ASYNC STREAMING DEMONSTRATION")
    print("="*60)
    
    # Create mock client and wrapper
    llm_client = MockLLMClient(delay_ms=50)
    
    temp_dir = Path(tempfile.mkdtemp())
    recorder = EnhancedRecorder(temp_dir, "async_demo")
    
    wrapper = StreamingLLMWrapper(llm_client, recorder=recorder)
    
    # Start recording
    recording_id = recorder.start_recording("async_demo_session")
    print(f"Started async recording: {recording_id}")
    
    # Test async streaming
    print("\\nTesting async streaming...")
    
    async def stream_and_collect(prompt: str, agent_id: str):
        chunks = []
        print(f"  Streaming '{prompt}': ", end="", flush=True)
        
        async for chunk in wrapper.stream_completion_async(
            prompt=prompt,
            model="gpt-4",
            agent_id=agent_id
        ):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        
        print(f" ({len(chunks)} chunks)")
        return chunks
    
    # Run multiple async streams concurrently
    tasks = [
        stream_and_collect("Write a haiku", "haiku_agent"),
        stream_and_collect("Count to five", "counter_agent"),
        stream_and_collect("Say hello", "greeter_agent")
    ]
    
    results = await asyncio.gather(*tasks)
    
    print(f"\\n✓ Completed {len(results)} async streams")
    
    # Stop recording
    manifest = recorder.stop_recording()
    print(f"Recording completed: {manifest.total_chunks} total chunks")


def main():
    """Run the enhanced telemetry integration demo."""
    print("Enhanced Telemetry Integration Demo")
    print("Phase 1: Record-Replay with Telemetry and Streaming")
    print("="*60)
    
    try:
        # 1. Demonstrate enhanced recording
        artifacts_dir, recording_id = demonstrate_enhanced_recording()
        
        # 2. Demonstrate enhanced replay
        demonstrate_enhanced_replay(artifacts_dir, recording_id)
        
        # 3. Demonstrate streaming wrapper
        demonstrate_streaming_wrapper()
        
        # 4. Demonstrate async streaming
        asyncio.run(demonstrate_async_streaming())
        
        print("\\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\\nKey features demonstrated:")
        print("  ✓ Enhanced recording with telemetry integration")
        print("  ✓ Streaming data capture and replay")
        print("  ✓ Comprehensive event tracking")
        print("  ✓ Replay with mismatch detection")
        print("  ✓ Stream timing analysis")
        print("  ✓ Async streaming support")
        print("  ✓ Background writing and compression")
        print("  ✓ Manifest generation with provenance")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())