"""
Streaming Support for Record-Replay

Provides utilities for capturing and replaying streaming data such as
LLM token streams with proper ordering and timing preservation.

Phase 1: Enhanced Telemetry Integration
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager, contextmanager
import uuid

logger = logging.getLogger(__name__)


@dataclass
class StreamToken:
    """A single token in a stream."""
    
    content: str
    timestamp: datetime
    index: int
    metadata: Dict[str, Any]
    is_final: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "index": self.index,
            "metadata": self.metadata,
            "is_final": self.is_final
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamToken':
        """Create from dictionary."""
        return cls(
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            index=data["index"],
            metadata=data["metadata"],
            is_final=data.get("is_final", False)
        )


class StreamCapture:
    """Captures streaming data for recording."""
    
    def __init__(self, stream_id: str, recorder=None):
        """
        Initialize stream capture.
        
        Args:
            stream_id: Unique stream identifier
            recorder: Optional recorder instance
        """
        self.stream_id = stream_id
        self.recorder = recorder
        self.tokens: List[StreamToken] = []
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.total_tokens = 0
        self.is_complete = False
    
    def add_token(self, 
                  content: str, 
                  metadata: Optional[Dict[str, Any]] = None,
                  is_final: bool = False) -> StreamToken:
        """
        Add a token to the stream.
        
        Args:
            content: Token content
            metadata: Additional metadata
            is_final: Whether this is the final token
            
        Returns:
            StreamToken instance
        """
        token = StreamToken(
            content=content,
            timestamp=datetime.utcnow(),
            index=len(self.tokens),
            metadata=metadata or {},
            is_final=is_final
        )
        
        self.tokens.append(token)
        self.total_tokens += 1
        
        # Record with recorder if available
        if self.recorder:
            self.recorder.record_chunk(
                stream_id=self.stream_id,
                content=content,
                metadata=metadata,
                is_final=is_final
            )
        
        if is_final:
            self.end_time = datetime.utcnow()
            self.is_complete = True
        
        return token
    
    def get_full_content(self) -> str:
        """Get the full content from all tokens."""
        return ''.join(token.content for token in self.tokens)
    
    def get_metadata_summary(self) -> Dict[str, Any]:
        """Get summary metadata for the stream."""
        return {
            "stream_id": self.stream_id,
            "total_tokens": self.total_tokens,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (
                (self.end_time - self.start_time).total_seconds() * 1000
                if self.end_time else None
            ),
            "is_complete": self.is_complete
        }


class StreamReplay:
    """Replays streaming data from recorded traces."""
    
    def __init__(self, recorded_tokens: List[StreamToken]):
        """
        Initialize stream replay.
        
        Args:
            recorded_tokens: List of recorded tokens to replay
        """
        self.recorded_tokens = recorded_tokens
        self.current_index = 0
        self.replay_start_time = datetime.utcnow()
        self.preserve_timing = True
    
    def set_timing_mode(self, preserve_timing: bool):
        """
        Set whether to preserve original timing during replay.
        
        Args:
            preserve_timing: If True, replay with original timing delays
        """
        self.preserve_timing = preserve_timing
    
    def replay_sync(self) -> Iterator[StreamToken]:
        """
        Synchronously replay tokens.
        
        Yields:
            StreamToken instances in order
        """
        for token in self.recorded_tokens:
            if self.preserve_timing and self.current_index > 0:
                # Calculate delay based on original timing
                prev_token = self.recorded_tokens[self.current_index - 1]
                delay = (token.timestamp - prev_token.timestamp).total_seconds()
                if delay > 0:
                    time.sleep(min(delay, 1.0))  # Cap at 1 second
            
            self.current_index += 1
            yield token
    
    async def replay_async(self) -> AsyncIterator[StreamToken]:
        """
        Asynchronously replay tokens.
        
        Yields:
            StreamToken instances in order
        """
        for token in self.recorded_tokens:
            if self.preserve_timing and self.current_index > 0:
                # Calculate delay based on original timing
                prev_token = self.recorded_tokens[self.current_index - 1]
                delay = (token.timestamp - prev_token.timestamp).total_seconds()
                if delay > 0:
                    await asyncio.sleep(min(delay, 1.0))  # Cap at 1 second
            
            self.current_index += 1
            yield token


@contextmanager
def capture_stream(recorder, agent_id: str, tool_name: str, inputs: Dict[str, Any]):
    """
    Context manager for capturing streaming operations.
    
    Args:
        recorder: Recorder instance
        agent_id: Agent identifier
        tool_name: Tool name
        inputs: Input parameters
        
    Yields:
        StreamCapture instance
    """
    stream_id = None
    capture = None
    
    try:
        if recorder and recorder.recording:
            stream_id = recorder.start_streaming(agent_id, tool_name, inputs)
            capture = StreamCapture(stream_id, recorder)
        else:
            # Create capture without recorder for testing
            stream_id = f"test_stream_{uuid.uuid4().hex[:8]}"
            capture = StreamCapture(stream_id)
        
        yield capture
        
    finally:
        if recorder and stream_id and recorder.recording:
            recorder.finish_streaming(stream_id, capture.total_tokens if capture else 0)


@asynccontextmanager
async def capture_stream_async(recorder, agent_id: str, tool_name: str, inputs: Dict[str, Any]):
    """
    Async context manager for capturing streaming operations.
    
    Args:
        recorder: Recorder instance
        agent_id: Agent identifier
        tool_name: Tool name
        inputs: Input parameters
        
    Yields:
        StreamCapture instance
    """
    stream_id = None
    capture = None
    
    try:
        if recorder and recorder.recording:
            stream_id = recorder.start_streaming(agent_id, tool_name, inputs)
            capture = StreamCapture(stream_id, recorder)
        else:
            # Create capture without recorder for testing
            stream_id = f"test_stream_{uuid.uuid4().hex[:8]}"
            capture = StreamCapture(stream_id)
        
        yield capture
        
    finally:
        if recorder and stream_id and recorder.recording:
            recorder.finish_streaming(stream_id, capture.total_tokens if capture else 0)


class StreamingLLMWrapper:
    """Wrapper for LLM calls that supports streaming capture and replay."""
    
    def __init__(self, llm_client, recorder=None, player=None):
        """
        Initialize streaming LLM wrapper.
        
        Args:
            llm_client: Underlying LLM client
            recorder: Optional recorder for capturing streams
            player: Optional player for replaying streams
        """
        self.llm_client = llm_client
        self.recorder = recorder
        self.player = player
        self.replay_mode = player is not None
    
    def stream_completion(self, 
                         prompt: str,
                         model: str,
                         agent_id: str,
                         **kwargs) -> Iterator[str]:
        """
        Stream completion with recording/replay support.
        
        Args:
            prompt: Input prompt
            model: Model identifier
            agent_id: Agent identifier
            **kwargs: Additional parameters
            
        Yields:
            Content chunks
        """
        if self.replay_mode and self.player:
            # Replay mode - return recorded stream
            io_key = f"llm_stream_{agent_id}_{hash(prompt) % 10000}"
            recorded_tokens = self.player.get_stream_tokens(io_key)
            
            if recorded_tokens:
                replay = StreamReplay(recorded_tokens)
                for token in replay.replay_sync():
                    yield token.content
                return
            else:
                logger.warning(f"No recorded stream found for key: {io_key}")
                # Fall through to live mode
        
        # Live mode with optional recording
        inputs = {"prompt": prompt, "model": model, **kwargs}
        
        with capture_stream(self.recorder, agent_id, "llm_stream", inputs) as capture:
            try:
                # Call underlying LLM client
                for chunk in self.llm_client.stream_completion(prompt, model, **kwargs):
                    if capture:
                        capture.add_token(chunk)
                    yield chunk
                
                # Mark final token
                if capture:
                    capture.add_token("", is_final=True)
                    
            except Exception as e:
                logger.error(f"Error in streaming completion: {e}")
                if capture:
                    capture.add_token(f"ERROR: {e}", is_final=True)
                raise
    
    async def stream_completion_async(self,
                                    prompt: str,
                                    model: str,
                                    agent_id: str,
                                    **kwargs) -> AsyncIterator[str]:
        """
        Async stream completion with recording/replay support.
        
        Args:
            prompt: Input prompt
            model: Model identifier
            agent_id: Agent identifier
            **kwargs: Additional parameters
            
        Yields:
            Content chunks
        """
        if self.replay_mode and self.player:
            # Replay mode - return recorded stream
            io_key = f"llm_stream_{agent_id}_{hash(prompt) % 10000}"
            recorded_tokens = self.player.get_stream_tokens(io_key)
            
            if recorded_tokens:
                replay = StreamReplay(recorded_tokens)
                async for token in replay.replay_async():
                    yield token.content
                return
            else:
                logger.warning(f"No recorded stream found for key: {io_key}")
                # Fall through to live mode
        
        # Live mode with optional recording
        inputs = {"prompt": prompt, "model": model, **kwargs}
        
        async with capture_stream_async(self.recorder, agent_id, "llm_stream", inputs) as capture:
            try:
                # Call underlying LLM client
                async for chunk in self.llm_client.stream_completion_async(prompt, model, **kwargs):
                    if capture:
                        capture.add_token(chunk)
                    yield chunk
                
                # Mark final token
                if capture:
                    capture.add_token("", is_final=True)
                    
            except Exception as e:
                logger.error(f"Error in async streaming completion: {e}")
                if capture:
                    capture.add_token(f"ERROR: {e}", is_final=True)
                raise


def create_streaming_wrapper(llm_client, recorder=None, player=None) -> StreamingLLMWrapper:
    """
    Create a streaming wrapper for an LLM client.
    
    Args:
        llm_client: LLM client to wrap
        recorder: Optional recorder for capturing
        player: Optional player for replay
        
    Returns:
        StreamingLLMWrapper instance
    """
    return StreamingLLMWrapper(llm_client, recorder, player)


# Utility functions for stream analysis
def analyze_stream_timing(tokens: List[StreamToken]) -> Dict[str, Any]:
    """
    Analyze timing characteristics of a token stream.
    
    Args:
        tokens: List of stream tokens
        
    Returns:
        Timing analysis results
    """
    if not tokens:
        return {"error": "No tokens provided"}
    
    # Calculate inter-token delays
    delays = []
    for i in range(1, len(tokens)):
        delay = (tokens[i].timestamp - tokens[i-1].timestamp).total_seconds()
        delays.append(delay)
    
    # Calculate statistics
    total_duration = (tokens[-1].timestamp - tokens[0].timestamp).total_seconds()
    avg_delay = sum(delays) / len(delays) if delays else 0
    min_delay = min(delays) if delays else 0
    max_delay = max(delays) if delays else 0
    
    return {
        "total_tokens": len(tokens),
        "total_duration_seconds": total_duration,
        "average_delay_seconds": avg_delay,
        "min_delay_seconds": min_delay,
        "max_delay_seconds": max_delay,
        "tokens_per_second": len(tokens) / total_duration if total_duration > 0 else 0,
        "delay_variance": sum((d - avg_delay) ** 2 for d in delays) / len(delays) if delays else 0
    }


def merge_stream_chunks(chunks: List[StreamToken]) -> str:
    """
    Merge stream chunks into a single content string.
    
    Args:
        chunks: List of stream tokens
        
    Returns:
        Merged content string
    """
    return ''.join(chunk.content for chunk in chunks if not chunk.is_final)


def split_content_into_chunks(content: str, 
                            chunk_size: int = 50,
                            preserve_words: bool = True) -> List[str]:
    """
    Split content into chunks for streaming simulation.
    
    Args:
        content: Content to split
        chunk_size: Target chunk size in characters
        preserve_words: Whether to preserve word boundaries
        
    Returns:
        List of content chunks
    """
    if not content:
        return []
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(content):
        end_pos = min(current_pos + chunk_size, len(content))
        
        if preserve_words and end_pos < len(content):
            # Find the last space before the chunk boundary
            space_pos = content.rfind(' ', current_pos, end_pos)
            if space_pos > current_pos:
                end_pos = space_pos + 1
        
        chunk = content[current_pos:end_pos]
        chunks.append(chunk)
        current_pos = end_pos
    
    return chunks