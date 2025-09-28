#!/usr/bin/env python3
"""
Context Management System for AI Dev Squad

This module provides intelligent context window management, conversation summarization,
and streaming response handling for optimal performance with large contexts.
"""

import os
import json
import logging
import hashlib
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Iterator, AsyncIterator
from enum import Enum
from pathlib import Path
import asyncio
import time

# Configure logging
logger = logging.getLogger("ai_dev_squad.context_management")


class ContextStrategy(Enum):
    """Strategies for context window management."""
    TRUNCATE_OLDEST = "truncate_oldest"
    TRUNCATE_MIDDLE = "truncate_middle"
    SUMMARIZE_OLDEST = "summarize_oldest"
    SLIDING_WINDOW = "sliding_window"
    IMPORTANCE_BASED = "importance_based"


class MessageImportance(Enum):
    """Importance levels for messages in context."""
    CRITICAL = "critical"  # System messages, key instructions
    HIGH = "high"         # Recent user inputs, important responses
    MEDIUM = "medium"     # Regular conversation flow
    LOW = "low"          # Filler content, less relevant history


@dataclass
class ContextMessage:
    """Represents a message in the context with metadata."""
    role: str
    content: str
    timestamp: datetime
    importance: MessageImportance
    token_count: int
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['importance'] = self.importance.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextMessage':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['importance'] = MessageImportance(data['importance'])
        return cls(**data)
    
    def to_ollama_message(self) -> Dict[str, str]:
        """Convert to Ollama message format."""
        return {
            "role": self.role,
            "content": self.content
        }


@dataclass
class ContextWindow:
    """Represents a managed context window."""
    messages: List[ContextMessage]
    max_tokens: int
    current_tokens: int
    strategy: ContextStrategy
    model_name: str
    conversation_id: Optional[str] = None
    
    def add_message(self, message: ContextMessage) -> None:
        """Add a message to the context window."""
        self.messages.append(message)
        self.current_tokens += message.token_count
        self._manage_context()
    
    def _manage_context(self) -> None:
        """Manage context size according to strategy."""
        if self.current_tokens <= self.max_tokens:
            return
        
        if self.strategy == ContextStrategy.TRUNCATE_OLDEST:
            self._truncate_oldest()
        elif self.strategy == ContextStrategy.TRUNCATE_MIDDLE:
            self._truncate_middle()
        elif self.strategy == ContextStrategy.SUMMARIZE_OLDEST:
            self._summarize_oldest()
        elif self.strategy == ContextStrategy.SLIDING_WINDOW:
            self._sliding_window()
        elif self.strategy == ContextStrategy.IMPORTANCE_BASED:
            self._importance_based_management()
    
    def _truncate_oldest(self) -> None:
        """Remove oldest messages until within token limit."""
        while self.current_tokens > self.max_tokens and len(self.messages) > 1:
            # Keep system messages and recent messages
            if self.messages[0].role == "system":
                if len(self.messages) > 2:
                    removed = self.messages.pop(1)  # Remove second message
                else:
                    break
            else:
                removed = self.messages.pop(0)
            
            self.current_tokens -= removed.token_count
    
    def _truncate_middle(self) -> None:
        """Remove middle messages, keeping system, recent, and important messages."""
        if len(self.messages) <= 3:
            return
        
        # Keep first (system), last few messages, remove middle
        keep_recent = 2
        keep_start = 1 if self.messages[0].role == "system" else 0
        
        while (self.current_tokens > self.max_tokens and 
               len(self.messages) > keep_start + keep_recent):
            
            # Find middle message to remove (avoid system and recent)
            middle_idx = keep_start + (len(self.messages) - keep_start - keep_recent) // 2
            removed = self.messages.pop(middle_idx)
            self.current_tokens -= removed.token_count
    
    def _summarize_oldest(self) -> None:
        """Summarize oldest messages to reduce token count."""
        # This is a placeholder - in practice, you'd use a summarization model
        # For now, we'll use truncation with a summary message
        
        if len(self.messages) <= 2:
            return
        
        # Calculate how many messages to summarize
        target_reduction = self.current_tokens - self.max_tokens + 500  # Buffer
        messages_to_summarize = []
        tokens_to_remove = 0
        
        for i, msg in enumerate(self.messages):
            if msg.role == "system":
                continue
            if tokens_to_remove >= target_reduction:
                break
            
            messages_to_summarize.append(msg)
            tokens_to_remove += msg.token_count
        
        if messages_to_summarize:
            # Create summary message
            summary_content = f"[Previous conversation summary: {len(messages_to_summarize)} messages exchanged about various topics]"
            summary_msg = ContextMessage(
                role="system",
                content=summary_content,
                timestamp=datetime.now(),
                importance=MessageImportance.MEDIUM,
                token_count=len(summary_content.split()) * 1.3,  # Rough estimate
                message_id="summary_" + str(int(time.time()))
            )
            
            # Remove summarized messages and add summary
            for msg in messages_to_summarize:
                if msg in self.messages:
                    self.messages.remove(msg)
                    self.current_tokens -= msg.token_count
            
            # Insert summary after system message
            insert_idx = 1 if self.messages and self.messages[0].role == "system" else 0
            self.messages.insert(insert_idx, summary_msg)
            self.current_tokens += summary_msg.token_count
    
    def _sliding_window(self) -> None:
        """Maintain a sliding window of recent messages."""
        # Keep system message and recent messages within token limit
        if not self.messages:
            return
        
        # Always keep system message
        system_msg = None
        if self.messages[0].role == "system":
            system_msg = self.messages[0]
            remaining_messages = self.messages[1:]
            available_tokens = self.max_tokens - system_msg.token_count
        else:
            remaining_messages = self.messages
            available_tokens = self.max_tokens
        
        # Keep as many recent messages as possible
        kept_messages = []
        used_tokens = 0
        
        for msg in reversed(remaining_messages):
            if used_tokens + msg.token_count <= available_tokens:
                kept_messages.insert(0, msg)
                used_tokens += msg.token_count
            else:
                break
        
        # Update messages list
        if system_msg:
            self.messages = [system_msg] + kept_messages
            self.current_tokens = system_msg.token_count + used_tokens
        else:
            self.messages = kept_messages
            self.current_tokens = used_tokens
    
    def _importance_based_management(self) -> None:
        """Manage context based on message importance."""
        if self.current_tokens <= self.max_tokens:
            return
        
        # Sort messages by importance (keep critical and high importance)
        critical_msgs = [msg for msg in self.messages if msg.importance == MessageImportance.CRITICAL]
        high_msgs = [msg for msg in self.messages if msg.importance == MessageImportance.HIGH]
        medium_msgs = [msg for msg in self.messages if msg.importance == MessageImportance.MEDIUM]
        low_msgs = [msg for msg in self.messages if msg.importance == MessageImportance.LOW]
        
        # Calculate tokens for each importance level
        critical_tokens = sum(msg.token_count for msg in critical_msgs)
        high_tokens = sum(msg.token_count for msg in high_msgs)
        medium_tokens = sum(msg.token_count for msg in medium_msgs)
        
        # Keep messages in order of importance
        kept_messages = critical_msgs.copy()
        used_tokens = critical_tokens
        
        # Add high importance messages if space allows
        for msg in high_msgs:
            if used_tokens + msg.token_count <= self.max_tokens:
                kept_messages.append(msg)
                used_tokens += msg.token_count
        
        # Add medium importance messages if space allows
        for msg in medium_msgs:
            if used_tokens + msg.token_count <= self.max_tokens:
                kept_messages.append(msg)
                used_tokens += msg.token_count
        
        # Sort by timestamp to maintain conversation order
        kept_messages.sort(key=lambda x: x.timestamp)
        
        self.messages = kept_messages
        self.current_tokens = used_tokens
    
    def get_ollama_messages(self) -> List[Dict[str, str]]:
        """Get messages in Ollama format."""
        return [msg.to_ollama_message() for msg in self.messages]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context state."""
        return {
            "message_count": len(self.messages),
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "utilization": self.current_tokens / self.max_tokens,
            "strategy": self.strategy.value,
            "importance_distribution": {
                importance.value: len([msg for msg in self.messages if msg.importance == importance])
                for importance in MessageImportance
            }
        }


class StreamingResponseHandler:
    """Handles streaming responses with real-time processing."""
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        """
        Initialize streaming handler.
        
        Args:
            callback: Optional callback function for each chunk.
        """
        self.callback = callback
        self.buffer = ""
        self.complete_response = ""
        self.start_time = None
        self.chunk_count = 0
        self.total_tokens = 0
        
    def start_streaming(self) -> None:
        """Start streaming session."""
        self.start_time = time.time()
        self.buffer = ""
        self.complete_response = ""
        self.chunk_count = 0
        self.total_tokens = 0
    
    def process_chunk(self, chunk: str) -> str:
        """
        Process a streaming chunk.
        
        Args:
            chunk: Raw chunk from streaming response.
            
        Returns:
            Processed chunk content.
        """
        self.chunk_count += 1
        self.buffer += chunk
        self.complete_response += chunk
        
        # Estimate tokens (rough approximation)
        self.total_tokens = len(self.complete_response.split()) * 1.3
        
        # Call callback if provided
        if self.callback:
            try:
                self.callback(chunk)
            except Exception as e:
                logger.warning(f"Streaming callback error: {e}")
        
        return chunk
    
    def finish_streaming(self) -> Dict[str, Any]:
        """
        Finish streaming and return statistics.
        
        Returns:
            Streaming statistics.
        """
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        return {
            "complete_response": self.complete_response,
            "duration_seconds": duration,
            "chunk_count": self.chunk_count,
            "total_tokens": self.total_tokens,
            "tokens_per_second": self.total_tokens / duration if duration > 0 else 0,
            "chunks_per_second": self.chunk_count / duration if duration > 0 else 0
        }


class ContextManager:
    """Main context management system."""
    
    def __init__(self, 
                 default_strategy: ContextStrategy = ContextStrategy.SLIDING_WINDOW,
                 default_max_tokens: int = 4096,
                 token_estimator: Optional[Callable[[str], int]] = None):
        """
        Initialize context manager.
        
        Args:
            default_strategy: Default context management strategy.
            default_max_tokens: Default maximum tokens for context.
            token_estimator: Optional function to estimate token count.
        """
        self.default_strategy = default_strategy
        self.default_max_tokens = default_max_tokens
        self.token_estimator = token_estimator or self._estimate_tokens
        self.active_contexts: Dict[str, ContextWindow] = {}
        self._lock = threading.RLock()
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate tokens for.
            
        Returns:
            Estimated token count.
        """
        # Simple approximation: ~1.3 tokens per word
        return int(len(text.split()) * 1.3)
    
    def create_context(self, 
                      conversation_id: str,
                      model_name: str,
                      max_tokens: Optional[int] = None,
                      strategy: Optional[ContextStrategy] = None) -> ContextWindow:
        """
        Create a new context window.
        
        Args:
            conversation_id: Unique identifier for the conversation.
            model_name: Name of the model for context sizing.
            max_tokens: Maximum tokens for this context.
            strategy: Context management strategy.
            
        Returns:
            New context window.
        """
        with self._lock:
            context = ContextWindow(
                messages=[],
                max_tokens=max_tokens or self.default_max_tokens,
                current_tokens=0,
                strategy=strategy or self.default_strategy,
                model_name=model_name,
                conversation_id=conversation_id
            )
            
            self.active_contexts[conversation_id] = context
            return context
    
    def get_context(self, conversation_id: str) -> Optional[ContextWindow]:
        """
        Get existing context window.
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            Context window if exists, None otherwise.
        """
        with self._lock:
            return self.active_contexts.get(conversation_id)
    
    def add_message(self, 
                   conversation_id: str,
                   role: str,
                   content: str,
                   importance: MessageImportance = MessageImportance.MEDIUM,
                   metadata: Optional[Dict[str, Any]] = None) -> ContextMessage:
        """
        Add a message to a context.
        
        Args:
            conversation_id: Conversation identifier.
            role: Message role (system, user, assistant).
            content: Message content.
            importance: Message importance level.
            metadata: Optional metadata.
            
        Returns:
            Created context message.
        """
        with self._lock:
            context = self.active_contexts.get(conversation_id)
            if not context:
                raise ValueError(f"No context found for conversation {conversation_id}")
            
            message = ContextMessage(
                role=role,
                content=content,
                timestamp=datetime.now(),
                importance=importance,
                token_count=self.token_estimator(content),
                message_id=f"{conversation_id}_{len(context.messages)}",
                metadata=metadata
            )
            
            context.add_message(message)
            return message
    
    def get_messages_for_model(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get messages formatted for model consumption.
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            List of messages in model format.
        """
        with self._lock:
            context = self.active_contexts.get(conversation_id)
            if not context:
                return []
            
            return context.get_ollama_messages()
    
    def optimize_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Optimize context for better performance.
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            Optimization results.
        """
        with self._lock:
            context = self.active_contexts.get(conversation_id)
            if not context:
                return {"error": "Context not found"}
            
            original_tokens = context.current_tokens
            original_messages = len(context.messages)
            
            # Force context management
            context._manage_context()
            
            return {
                "original_tokens": original_tokens,
                "optimized_tokens": context.current_tokens,
                "tokens_saved": original_tokens - context.current_tokens,
                "original_messages": original_messages,
                "optimized_messages": len(context.messages),
                "messages_removed": original_messages - len(context.messages),
                "strategy_used": context.strategy.value
            }
    
    def get_context_stats(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get statistics for a context.
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            Context statistics.
        """
        with self._lock:
            context = self.active_contexts.get(conversation_id)
            if not context:
                return {"error": "Context not found"}
            
            return context.get_context_summary()
    
    def clear_context(self, conversation_id: str) -> bool:
        """
        Clear a context.
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            True if cleared, False if not found.
        """
        with self._lock:
            if conversation_id in self.active_contexts:
                del self.active_contexts[conversation_id]
                return True
            return False
    
    def get_all_contexts(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of all active contexts.
        
        Returns:
            Dictionary of context summaries.
        """
        with self._lock:
            return {
                conv_id: context.get_context_summary()
                for conv_id, context in self.active_contexts.items()
            }
    
    def cleanup_old_contexts(self, max_age_hours: int = 24) -> int:
        """
        Clean up old contexts.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup.
            
        Returns:
            Number of contexts cleaned up.
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            old_contexts = []
            
            for conv_id, context in self.active_contexts.items():
                if context.messages:
                    last_message_time = max(msg.timestamp for msg in context.messages)
                    if last_message_time < cutoff_time:
                        old_contexts.append(conv_id)
            
            for conv_id in old_contexts:
                del self.active_contexts[conv_id]
            
            return len(old_contexts)


# Global context manager instance
_global_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get the global context manager instance."""
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = ContextManager()
    return _global_context_manager


def configure_context_manager(
    default_strategy: ContextStrategy = ContextStrategy.SLIDING_WINDOW,
    default_max_tokens: int = 4096,
    token_estimator: Optional[Callable[[str], int]] = None
) -> ContextManager:
    """
    Configure the global context manager.
    
    Args:
        default_strategy: Default context management strategy.
        default_max_tokens: Default maximum tokens.
        token_estimator: Optional token estimation function.
        
    Returns:
        Configured context manager.
    """
    global _global_context_manager
    _global_context_manager = ContextManager(
        default_strategy=default_strategy,
        default_max_tokens=default_max_tokens,
        token_estimator=token_estimator
    )
    return _global_context_manager


class AsyncStreamingHandler:
    """Async version of streaming handler for concurrent operations."""
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        self.callback = callback
        self.buffer = ""
        self.complete_response = ""
        self.start_time = None
        self.chunk_count = 0
        self.total_tokens = 0
        self._lock = asyncio.Lock()
    
    async def start_streaming(self) -> None:
        """Start async streaming session."""
        async with self._lock:
            self.start_time = time.time()
            self.buffer = ""
            self.complete_response = ""
            self.chunk_count = 0
            self.total_tokens = 0
    
    async def process_chunk(self, chunk: str) -> str:
        """Process streaming chunk asynchronously."""
        async with self._lock:
            self.chunk_count += 1
            self.buffer += chunk
            self.complete_response += chunk
            self.total_tokens = len(self.complete_response.split()) * 1.3
            
            if self.callback:
                try:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(chunk)
                    else:
                        self.callback(chunk)
                except Exception as e:
                    logger.warning(f"Async streaming callback error: {e}")
            
            return chunk
    
    async def finish_streaming(self) -> Dict[str, Any]:
        """Finish async streaming and return statistics."""
        async with self._lock:
            end_time = time.time()
            duration = end_time - self.start_time if self.start_time else 0
            
            return {
                "complete_response": self.complete_response,
                "duration_seconds": duration,
                "chunk_count": self.chunk_count,
                "total_tokens": self.total_tokens,
                "tokens_per_second": self.total_tokens / duration if duration > 0 else 0,
                "chunks_per_second": self.chunk_count / duration if duration > 0 else 0
            }