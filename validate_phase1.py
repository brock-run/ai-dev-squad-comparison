#!/usr/bin/env python3
"""
Phase 1 Validation Script

Tests the core functionality of Phase 1 Enhanced Telemetry Integration
without relying on complex manifest validation.
"""

import tempfile
import json
from pathlib import Path
from datetime import datetime

def test_imports():
    """Test that all Phase 1 components can be imported."""
    print("🔍 Testing imports...")
    
    try:
        # Test foundation components
        from common.replay import (
            StreamToken, StreamCapture, StreamReplay, StreamingLLMWrapper,
            capture_stream, analyze_stream_timing
        )
        print("  ✅ Streaming components")
        
        # Test enhanced recorder
        from benchmark.replay.recorder import EnhancedRecorder, RecordedEvent, StreamingChunk
        print("  ✅ Enhanced recorder")
        
        # Test enhanced player
        from benchmark.replay.player import EnhancedPlayer
        print("  ✅ Enhanced player")
        
        # Test telemetry schema enhancements
        from common.telemetry.schema import (
            EventType, StreamingLLMEvent, RecordingEvent, ReplayEvent,
            create_streaming_llm_start_event, create_recording_start_event
        )
        print("  ✅ Enhanced telemetry schema")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_enhanced_recorder():
    """Test enhanced recorder functionality."""
    print("\n🔍 Testing Enhanced Recorder...")
    
    try:
        from benchmark.replay.recorder import EnhancedRecorder
        
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        
        # Initialize recorder
        recorder = EnhancedRecorder(
            output_dir=temp_dir,
            adapter_name="test_adapter",
            compression_enabled=False  # Disable compression for simplicity
        )
        print("  ✅ Recorder initialization")
        
        # Start recording
        recording_id = recorder.start_recording("test_session")
        assert recording_id is not None
        print("  ✅ Start recording")
        
        # Record events
        event_id = recorder.record_event(
            event_type="llm_call",
            agent_id="test_agent",
            tool_name="openai",
            inputs={"prompt": "Hello world"},
            outputs={"response": "Hi there!"},
            duration=1.5
        )
        assert event_id is not None
        print("  ✅ Record event")
        
        # Test streaming
        stream_id = recorder.start_streaming(
            agent_id="test_agent",
            tool_name="openai",
            inputs={"prompt": "Tell me a story"}
        )
        assert stream_id is not None
        print("  ✅ Start streaming")
        
        # Record chunks
        chunk_id1 = recorder.record_chunk(stream_id, "Once upon", {"token": 1})
        chunk_id2 = recorder.record_chunk(stream_id, " a time", {"token": 2})
        chunk_id3 = recorder.record_chunk(stream_id, "", is_final=True)
        
        assert all([chunk_id1, chunk_id2, chunk_id3])
        print("  ✅ Record streaming chunks")
        
        # Finish streaming
        total_chunks = recorder.finish_streaming(stream_id)
        assert total_chunks == 3
        print("  ✅ Finish streaming")
        
        # Create checkpoint
        recorder.checkpoint("test_checkpoint", {"test": "data"})
        print("  ✅ Create checkpoint")
        
        # Stop recording
        manifest = recorder.stop_recording()
        assert manifest is not None
        assert manifest.total_events == 1
        assert manifest.total_chunks == 3
        print("  ✅ Stop recording and generate manifest")
        
        return True, temp_dir, recording_id
        
    except Exception as e:
        print(f"  ❌ Recorder test failed: {e}")
        return False, None, None


def test_streaming_components():
    """Test streaming support components."""
    print("\n🔍 Testing Streaming Components...")
    
    try:
        from common.replay.streaming import (
            StreamToken, StreamCapture, StreamReplay, 
            analyze_stream_timing, split_content_into_chunks
        )
        
        # Test StreamToken
        token = StreamToken(
            content="Hello",
            timestamp=datetime.utcnow(),
            index=0,
            metadata={"test": "data"}
        )
        token_dict = token.to_dict()
        restored_token = StreamToken.from_dict(token_dict)
        assert restored_token.content == "Hello"
        print("  ✅ StreamToken serialization")
        
        # Test StreamCapture
        capture = StreamCapture("test_stream")
        capture.add_token("Hello", {"token": 1})
        capture.add_token(" world", {"token": 2})
        capture.add_token("", is_final=True)
        
        assert capture.total_tokens == 3
        assert capture.get_full_content() == "Hello world"
        print("  ✅ StreamCapture functionality")
        
        # Test StreamReplay
        tokens = [
            StreamToken("Hello", datetime.utcnow(), 0, {}),
            StreamToken(" world", datetime.utcnow(), 1, {}),
        ]
        replay = StreamReplay(tokens)
        replay.set_timing_mode(False)  # Disable timing for test
        
        replayed_content = []
        for token in replay.replay_sync():
            replayed_content.append(token.content)
        
        assert replayed_content == ["Hello", " world"]
        print("  ✅ StreamReplay functionality")
        
        # Test utility functions
        chunks = split_content_into_chunks("Hello world test", chunk_size=5)
        assert len(chunks) > 1
        print("  ✅ Utility functions")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Streaming test failed: {e}")
        return False


def test_telemetry_integration():
    """Test telemetry integration."""
    print("\n🔍 Testing Telemetry Integration...")
    
    try:
        from common.telemetry.schema import (
            EventType, StreamingLLMEvent, 
            create_streaming_llm_start_event, create_recording_start_event
        )
        
        # Test event creation
        llm_event = create_streaming_llm_start_event(
            prompt="Test prompt",
            model="gpt-4",
            agent_id="test_agent",
            stream_id="test_stream"
        )
        assert llm_event.event_type == EventType.LLM_CALL_STARTED
        print("  ✅ Streaming LLM event creation")
        
        recording_event = create_recording_start_event(
            recording_session="test_recording",
            artifacts_path="/tmp/test",
            agent_id="test_agent"
        )
        assert recording_event.event_type == EventType.RECORDING_NOTE
        print("  ✅ Recording event creation")
        
        # Test event serialization
        event_dict = llm_event.to_dict()
        assert "prompt" in event_dict
        print("  ✅ Event serialization")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Telemetry test failed: {e}")
        return False


def test_basic_integration():
    """Test basic integration between components."""
    print("\n🔍 Testing Basic Integration...")
    
    try:
        from benchmark.replay.recorder import EnhancedRecorder
        from common.replay.streaming import StreamingLLMWrapper
        
        # Mock LLM client
        class MockLLMClient:
            def stream_completion(self, prompt, model, **kwargs):
                return iter(["Hello", " world", "!"])
        
        # Create recorder and wrapper
        temp_dir = Path(tempfile.mkdtemp())
        recorder = EnhancedRecorder(temp_dir, "integration_test", compression_enabled=False)
        llm_client = MockLLMClient()
        wrapper = StreamingLLMWrapper(llm_client, recorder=recorder)
        
        # Start recording
        recording_id = recorder.start_recording("integration_session")
        
        # Test streaming through wrapper
        chunks = list(wrapper.stream_completion(
            prompt="Test prompt",
            model="gpt-4",
            agent_id="test_agent"
        ))
        
        assert chunks == ["Hello", " world", "!"]
        print("  ✅ Streaming wrapper integration")
        
        # Stop recording
        manifest = recorder.stop_recording()
        assert manifest.total_chunks > 0
        print("  ✅ Integration recording")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False


def main():
    """Run all Phase 1 validation tests."""
    print("Phase 1: Enhanced Telemetry Integration - Validation")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Enhanced Recorder", test_enhanced_recorder),
        ("Streaming Components", test_streaming_components),
        ("Telemetry Integration", test_telemetry_integration),
        ("Basic Integration", test_basic_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if test_name == "Enhanced Recorder":
                result = test_func()
                if isinstance(result, tuple):
                    success = result[0]
                else:
                    success = result
            else:
                success = test_func()
            
            results.append((test_name, success))
            
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Phase 1 validation SUCCESSFUL!")
        print("\nKey achievements:")
        print("  ✅ Enhanced telemetry schema with record-replay events")
        print("  ✅ Enhanced recorder with streaming and background writing")
        print("  ✅ Streaming support infrastructure")
        print("  ✅ Telemetry integration with event creation")
        print("  ✅ Basic component integration")
        print("\nPhase 1 is ready for production use!")
        return 0
    else:
        print(f"\n❌ Phase 1 validation FAILED ({total - passed} failures)")
        print("\nSome components need attention before production use.")
        return 1


if __name__ == "__main__":
    exit(main())