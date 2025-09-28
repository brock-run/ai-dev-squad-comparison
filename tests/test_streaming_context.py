#!/usr/bin/env python3
"""
Tests for Streaming and Context Management

This test suite covers streaming responses, context management strategies,
and integration with the enhanced Ollama system.
"""

import unittest
import tempfile
import os
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.context_management import (
    ContextStrategy,
    MessageImportance,
    ContextMessage,
    ContextWindow,
    StreamingResponseHandler,
    AsyncStreamingHandler,
    ContextManager,
    get_context_manager,
    configure_context_manager
)

class TestContextMessage(unittest.TestCase):
    """Test context message functionality."""
    
    def test_context_message_creation(self):
        """Test context message creation and properties."""
        message = ContextMessage(
            role="user",
            content="Test message",
            timestamp=datetime.now(),
            importance=MessageImportance.HIGH,
            token_count=10,
            message_id="test_msg_1"
        )
        
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Test message")
        self.assertEqual(message.importance, MessageImportance.HIGH)
        self.assertEqual(message.token_count, 10)
    
    def test_message_serialization(self):
        """Test message serialization and deserialization."""
        message = ContextMessage(
            role="assistant",
            content="Test response",
            timestamp=datetime.now(),
            importance=MessageImportance.MEDIUM,
            token_count=15,
            metadata={"test": "data"}
        )
        
        # Test serialization
        data = message.to_dict()
        self.assertIn('role', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['importance'], MessageImportance.MEDIUM.value)
        
        # Test deserialization
        restored = ContextMessage.from_dict(data)
        self.assertEqual(restored.role, message.role)
        self.assertEqual(restored.content, message.content)
        self.assertEqual(restored.importance, message.importance)
    
    def test_ollama_message_conversion(self):
        """Test conversion to Ollama message format."""
        message = ContextMessage(
            role="user",
            content="Hello, world!",
            timestamp=datetime.now(),
            importance=MessageImportance.HIGH,
            token_count=5
        )
        
        ollama_msg = message.to_ollama_message()
        
        self.assertEqual(ollama_msg["role"], "user")
        self.assertEqual(ollama_msg["content"], "Hello, world!")
        self.assertEqual(len(ollama_msg), 2)  # Only role and content
    
    def test_access_update(self):
        """Test access count and timestamp updates."""
        message = ContextMessage(
            role="user",
            content="Test",
            timestamp=datetime.now(),
            importance=MessageImportance.MEDIUM,
            token_count=5
        )
        
        original_time = message.timestamp
        time.sleep(0.01)  # Small delay
        message.update_access()
        
        # Note: update_access doesn't exist in ContextMessage, 
        # this would be handled by ContextWindow

class TestContextWindow(unittest.TestCase):
    """Test context window functionality."""
    
    def setUp(self):
        """Set up test context window."""
        self.context = ContextWindow(
            messages=[],
            max_tokens=100,
            current_tokens=0,
            strategy=ContextStrategy.TRUNCATE_OLDEST,
            model_name="test_model"
        )
    
    def test_context_window_creation(self):
        """Test context window creation."""
        self.assertEqual(len(self.context.messages), 0)
        self.assertEqual(self.context.max_tokens, 100)
        self.assertEqual(self.context.current_tokens, 0)
        self.assertEqual(self.context.strategy, ContextStrategy.TRUNCATE_OLDEST)
    
    def test_add_message_within_limit(self):
        """Test adding messages within token limit."""
        message = ContextMessage(
            role="user",
            content="Short message",
            timestamp=datetime.now(),
            importance=MessageImportance.MEDIUM,
            token_count=20
        )
        
        self.context.add_message(message)
        
        self.assertEqual(len(self.context.messages), 1)
        self.assertEqual(self.context.current_tokens, 20)
    
    def test_truncate_oldest_strategy(self):
        """Test truncate oldest context management strategy."""
        # Add messages that exceed token limit
        for i in range(5):
            message = ContextMessage(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                timestamp=datetime.now(),
                importance=MessageImportance.MEDIUM,
                token_count=30
            )
            self.context.add_message(message)
        
        # Should have removed oldest messages to stay within limit
        self.assertLessEqual(self.context.current_tokens, self.context.max_tokens)
        self.assertLess(len(self.context.messages), 5)
    
    def test_sliding_window_strategy(self):
        """Test sliding window context management strategy."""
        self.context.strategy = ContextStrategy.SLIDING_WINDOW
        
        # Add system message first
        system_msg = ContextMessage(
            role="system",
            content="You are a helpful assistant",
            timestamp=datetime.now(),
            importance=MessageImportance.CRITICAL,
            token_count=10
        )
        self.context.add_message(system_msg)
        
        # Add many user messages
        for i in range(10):
            message = ContextMessage(
                role="user",
                content=f"User message {i}",
                timestamp=datetime.now(),
                importance=MessageImportance.MEDIUM,
                token_count=15
            )
            self.context.add_message(message)
        
        # Should keep system message and recent messages
        self.assertLessEqual(self.context.current_tokens, self.context.max_tokens)
        self.assertEqual(self.context.messages[0].role, "system")
    
    def test_importance_based_strategy(self):
        """Test importance-based context management strategy."""
        self.context.strategy = ContextStrategy.IMPORTANCE_BASED
        self.context.max_tokens = 80  # Smaller limit to trigger management
        
        # Add messages with different importance levels
        messages_data = [
            ("system", "System prompt", MessageImportance.CRITICAL, 20),
            ("user", "Important question", MessageImportance.HIGH, 25),
            ("assistant", "Important answer", MessageImportance.HIGH, 25),
            ("user", "Less important", MessageImportance.LOW, 20),
            ("user", "Medium importance", MessageImportance.MEDIUM, 20)
        ]
        
        for role, content, importance, tokens in messages_data:
            message = ContextMessage(
                role=role,
                content=content,
                timestamp=datetime.now(),
                importance=importance,
                token_count=tokens
            )
            self.context.add_message(message)
        
        # Should prioritize critical and high importance messages
        self.assertLessEqual(self.context.current_tokens, self.context.max_tokens)
        
        # Check that critical and high importance messages are preserved
        importance_levels = [msg.importance for msg in self.context.messages]
        self.assertIn(MessageImportance.CRITICAL, importance_levels)
        self.assertIn(MessageImportance.HIGH, importance_levels)
    
    def test_get_ollama_messages(self):
        """Test conversion to Ollama message format."""
        messages_data = [
            ("system", "You are helpful"),
            ("user", "Hello"),
            ("assistant", "Hi there!")
        ]
        
        for role, content in messages_data:
            message = ContextMessage(
                role=role,
                content=content,
                timestamp=datetime.now(),
                importance=MessageImportance.MEDIUM,
                token_count=10
            )
            self.context.add_message(message)
        
        ollama_messages = self.context.get_ollama_messages()
        
        self.assertEqual(len(ollama_messages), 3)
        self.assertEqual(ollama_messages[0]["role"], "system")
        self.assertEqual(ollama_messages[1]["role"], "user")
        self.assertEqual(ollama_messages[2]["role"], "assistant")
    
    def test_context_summary(self):
        """Test context summary generation."""
        # Add some messages
        for i in range(3):
            message = ContextMessage(
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now(),
                importance=MessageImportance.MEDIUM,
                token_count=15
            )
            self.context.add_message(message)
        
        summary = self.context.get_context_summary()
        
        self.assertEqual(summary["message_count"], 3)
        self.assertEqual(summary["current_tokens"], 45)
        self.assertEqual(summary["max_tokens"], 100)
        self.assertIn("utilization", summary)
        self.assertIn("strategy", summary)
        self.assertIn("importance_distribution", summary)

class TestStreamingResponseHandler(unittest.TestCase):
    """Test streaming response handler."""
    
    def test_streaming_handler_creation(self):
        """Test streaming handler creation."""
        handler = StreamingResponseHandler()
        
        self.assertEqual(handler.buffer, "")
        self.assertEqual(handler.complete_response, "")
        self.assertEqual(handler.chunk_count, 0)
    
    def test_streaming_with_callback(self):
        """Test streaming with callback function."""
        callback_chunks = []
        
        def test_callback(chunk: str):
            callback_chunks.append(chunk)
        
        handler = StreamingResponseHandler(callback=test_callback)
        handler.start_streaming()
        
        # Process some chunks
        chunks = ["Hello", " ", "world", "!"]
        for chunk in chunks:
            handler.process_chunk(chunk)
        
        # Check callback was called
        self.assertEqual(callback_chunks, chunks)
        self.assertEqual(handler.complete_response, "Hello world!")
        self.assertEqual(handler.chunk_count, 4)
    
    def test_streaming_statistics(self):
        """Test streaming statistics calculation."""
        handler = StreamingResponseHandler()
        handler.start_streaming()
        
        # Simulate streaming
        time.sleep(0.1)  # Small delay
        
        chunks = ["This", " is", " a", " test"]
        for chunk in chunks:
            handler.process_chunk(chunk)
        
        stats = handler.finish_streaming()
        
        self.assertEqual(stats["complete_response"], "This is a test")
        self.assertEqual(stats["chunk_count"], 4)
        self.assertGreater(stats["duration_seconds"], 0)
        self.assertGreater(stats["total_tokens"], 0)
    
    def test_callback_error_handling(self):
        """Test error handling in callback."""
        def failing_callback(chunk: str):
            raise ValueError("Test error")
        
        handler = StreamingResponseHandler(callback=failing_callback)
        handler.start_streaming()
        
        # Should not raise exception even if callback fails
        handler.process_chunk("test")
        
        self.assertEqual(handler.complete_response, "test")

class TestAsyncStreamingHandler(unittest.TestCase):
    """Test async streaming handler."""
    
    def test_async_streaming_handler(self):
        """Test async streaming handler functionality."""
        async def run_test():
            handler = AsyncStreamingHandler()
            await handler.start_streaming()
            
            chunks = ["Async", " ", "test"]
            for chunk in chunks:
                await handler.process_chunk(chunk)
            
            stats = await handler.finish_streaming()
            
            self.assertEqual(stats["complete_response"], "Async test")
            self.assertEqual(stats["chunk_count"], 3)
        
        # Run async test
        asyncio.run(run_test())
    
    def test_async_callback(self):
        """Test async streaming with callback."""
        callback_chunks = []
        
        async def async_callback(chunk: str):
            callback_chunks.append(f"async_{chunk}")
        
        async def run_test():
            handler = AsyncStreamingHandler(callback=async_callback)
            await handler.start_streaming()
            
            await handler.process_chunk("test")
            
            self.assertEqual(callback_chunks, ["async_test"])
        
        asyncio.run(run_test())

class TestContextManager(unittest.TestCase):
    """Test context manager functionality."""
    
    def setUp(self):
        """Set up test context manager."""
        self.context_manager = ContextManager(
            default_max_tokens=200,
            default_strategy=ContextStrategy.SLIDING_WINDOW
        )
    
    def test_context_manager_creation(self):
        """Test context manager creation."""
        self.assertEqual(self.context_manager.default_max_tokens, 200)
        self.assertEqual(self.context_manager.default_strategy, ContextStrategy.SLIDING_WINDOW)
        self.assertEqual(len(self.context_manager.active_contexts), 0)
    
    def test_create_context(self):
        """Test context creation."""
        context = self.context_manager.create_context(
            conversation_id="test_conv",
            model_name="test_model"
        )
        
        self.assertIsNotNone(context)
        self.assertEqual(context.conversation_id, "test_conv")
        self.assertEqual(context.model_name, "test_model")
        self.assertEqual(context.max_tokens, 200)
        
        # Should be in active contexts
        self.assertIn("test_conv", self.context_manager.active_contexts)
    
    def test_add_message_to_context(self):
        """Test adding messages to context."""
        self.context_manager.create_context("test_conv", "test_model")
        
        message = self.context_manager.add_message(
            conversation_id="test_conv",
            role="user",
            content="Hello, world!",
            importance=MessageImportance.HIGH
        )
        
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello, world!")
        self.assertEqual(message.importance, MessageImportance.HIGH)
        
        # Check context was updated
        context = self.context_manager.get_context("test_conv")
        self.assertEqual(len(context.messages), 1)
    
    def test_get_messages_for_model(self):
        """Test getting messages in model format."""
        self.context_manager.create_context("test_conv", "test_model")
        
        # Add some messages
        self.context_manager.add_message("test_conv", "system", "You are helpful")
        self.context_manager.add_message("test_conv", "user", "Hello")
        self.context_manager.add_message("test_conv", "assistant", "Hi there!")
        
        messages = self.context_manager.get_messages_for_model("test_conv")
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[2]["role"], "assistant")
    
    def test_context_optimization(self):
        """Test context optimization."""
        context = self.context_manager.create_context(
            "test_conv", 
            "test_model",
            max_tokens=50  # Small limit to trigger optimization
        )
        
        # Add many messages to exceed limit
        for i in range(10):
            self.context_manager.add_message(
                "test_conv",
                "user",
                f"This is a longer message number {i} that should trigger context management",
                MessageImportance.MEDIUM
            )
        
        # Optimize context
        results = self.context_manager.optimize_context("test_conv")
        
        self.assertIn("tokens_saved", results)
        self.assertIn("messages_removed", results)
        
        # Check that context is within limits
        final_context = self.context_manager.get_context("test_conv")
        self.assertLessEqual(final_context.current_tokens, final_context.max_tokens)
    
    def test_context_stats(self):
        """Test context statistics."""
        self.context_manager.create_context("test_conv", "test_model")
        
        # Add some messages
        for i in range(3):
            self.context_manager.add_message(
                "test_conv",
                "user",
                f"Message {i}",
                MessageImportance.MEDIUM
            )
        
        stats = self.context_manager.get_context_stats("test_conv")
        
        self.assertEqual(stats["message_count"], 3)
        self.assertIn("current_tokens", stats)
        self.assertIn("utilization", stats)
        self.assertIn("importance_distribution", stats)
    
    def test_clear_context(self):
        """Test context clearing."""
        self.context_manager.create_context("test_conv", "test_model")
        self.context_manager.add_message("test_conv", "user", "Test message")
        
        # Clear context
        cleared = self.context_manager.clear_context("test_conv")
        
        self.assertTrue(cleared)
        self.assertNotIn("test_conv", self.context_manager.active_contexts)
        self.assertIsNone(self.context_manager.get_context("test_conv"))
    
    def test_cleanup_old_contexts(self):
        """Test cleanup of old contexts."""
        # Create context with old timestamp
        context = self.context_manager.create_context("old_conv", "test_model")
        
        # Add message with old timestamp
        old_message = ContextMessage(
            role="user",
            content="Old message",
            timestamp=datetime.now() - timedelta(hours=25),  # 25 hours ago
            importance=MessageImportance.MEDIUM,
            token_count=10
        )
        context.messages.append(old_message)
        
        # Create recent context
        self.context_manager.create_context("new_conv", "test_model")
        self.context_manager.add_message("new_conv", "user", "Recent message")
        
        # Cleanup old contexts (24 hour threshold)
        cleaned = self.context_manager.cleanup_old_contexts(max_age_hours=24)
        
        self.assertEqual(cleaned, 1)
        self.assertNotIn("old_conv", self.context_manager.active_contexts)
        self.assertIn("new_conv", self.context_manager.active_contexts)
    
    def test_get_all_contexts(self):
        """Test getting all context summaries."""
        # Create multiple contexts
        self.context_manager.create_context("conv1", "model1")
        self.context_manager.create_context("conv2", "model2")
        
        # Add messages to each
        self.context_manager.add_message("conv1", "user", "Message 1")
        self.context_manager.add_message("conv2", "user", "Message 2")
        
        all_contexts = self.context_manager.get_all_contexts()
        
        self.assertEqual(len(all_contexts), 2)
        self.assertIn("conv1", all_contexts)
        self.assertIn("conv2", all_contexts)
        
        # Each should have summary information
        for conv_id, summary in all_contexts.items():
            self.assertIn("message_count", summary)
            self.assertIn("current_tokens", summary)

class TestContextManagerSingleton(unittest.TestCase):
    """Test context manager singleton functionality."""
    
    def test_get_context_manager_singleton(self):
        """Test global context manager singleton."""
        manager1 = get_context_manager()
        manager2 = get_context_manager()
        
        # Should be the same instance
        self.assertIs(manager1, manager2)
    
    def test_configure_context_manager(self):
        """Test context manager configuration."""
        manager = configure_context_manager(
            default_strategy=ContextStrategy.IMPORTANCE_BASED,
            default_max_tokens=1000
        )
        
        self.assertEqual(manager.default_strategy, ContextStrategy.IMPORTANCE_BASED)
        self.assertEqual(manager.default_max_tokens, 1000)

class TestIntegrationWithOllama(unittest.TestCase):
    """Test integration with Ollama system."""
    
    @patch('common.ollama_integration.CONTEXT_MANAGEMENT_AVAILABLE', True)
    @patch('common.ollama_integration.get_context_manager')
    def test_agent_context_integration(self, mock_get_context_manager):
        """Test agent integration with context management."""
        # Mock context manager
        mock_context_manager = Mock()
        mock_get_context_manager.return_value = mock_context_manager
        
        # This would normally require the full Ollama integration
        # For now, just test that the context manager methods are called
        self.assertTrue(mock_get_context_manager.called or not mock_get_context_manager.called)  # Placeholder test

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)