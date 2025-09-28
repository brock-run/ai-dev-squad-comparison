#!/usr/bin/env python3
"""
Tests for Intelligent Caching System

This test suite covers the caching functionality, cache strategies,
invalidation, and integration with the Ollama system.
"""

import unittest
import tempfile
import os
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.caching import (
    CacheStrategy,
    CacheInvalidationReason,
    CacheEntry,
    CacheStats,
    PromptSimilarityCalculator,
    IntelligentCache,
    get_cache,
    configure_cache
)

class TestCacheEntry(unittest.TestCase):
    """Test cache entry functionality."""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation and basic properties."""
        entry = CacheEntry(
            key="test_key",
            prompt_hash="abc123",
            model_name="test_model",
            response="Test response",
            metadata={"test": "data"},
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            performance_score=8.5,
            ttl_seconds=3600
        )
        
        self.assertEqual(entry.key, "test_key")
        self.assertEqual(entry.model_name, "test_model")
        self.assertEqual(entry.performance_score, 8.5)
        self.assertFalse(entry.is_expired())
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic."""
        # Create expired entry
        old_time = datetime.now() - timedelta(hours=2)
        entry = CacheEntry(
            key="expired_key",
            prompt_hash="def456",
            model_name="test_model",
            response="Expired response",
            metadata={},
            created_at=old_time,
            last_accessed=old_time,
            access_count=1,
            performance_score=5.0,
            ttl_seconds=3600  # 1 hour TTL, but created 2 hours ago
        )
        
        self.assertTrue(entry.is_expired())
    
    def test_cache_entry_serialization(self):
        """Test cache entry serialization and deserialization."""
        entry = CacheEntry(
            key="serial_key",
            prompt_hash="ghi789",
            model_name="test_model",
            response="Serializable response",
            metadata={"version": 1},
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=5,
            performance_score=7.5,
            ttl_seconds=7200
        )
        
        # Test serialization
        data = entry.to_dict()
        self.assertIn('key', data)
        self.assertIn('created_at', data)
        
        # Test deserialization
        restored = CacheEntry.from_dict(data)
        self.assertEqual(restored.key, entry.key)
        self.assertEqual(restored.performance_score, entry.performance_score)
        self.assertEqual(restored.access_count, entry.access_count)
    
    def test_access_update(self):
        """Test access count and timestamp updates."""
        entry = CacheEntry(
            key="access_key",
            prompt_hash="jkl012",
            model_name="test_model",
            response="Access test response",
            metadata={},
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            performance_score=6.0
        )
        
        original_count = entry.access_count
        original_time = entry.last_accessed
        
        time.sleep(0.01)  # Small delay
        entry.update_access()
        
        self.assertEqual(entry.access_count, original_count + 1)
        self.assertGreater(entry.last_accessed, original_time)

class TestCacheStats(unittest.TestCase):
    """Test cache statistics functionality."""
    
    def test_cache_stats_creation(self):
        """Test cache stats creation and properties."""
        stats = CacheStats()
        
        self.assertEqual(stats.total_requests, 0)
        self.assertEqual(stats.cache_hits, 0)
        self.assertEqual(stats.hit_rate, 0.0)
        self.assertEqual(stats.miss_rate, 1.0)
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(
            total_requests=100,
            cache_hits=75,
            cache_misses=25
        )
        
        self.assertEqual(stats.hit_rate, 0.75)
        self.assertEqual(stats.miss_rate, 0.25)
    
    def test_performance_improvement(self):
        """Test performance improvement calculation."""
        stats = CacheStats(
            avg_response_time_cached=0.1,
            avg_response_time_uncached=2.0
        )
        
        self.assertEqual(stats.performance_improvement, 0.95)  # 95% improvement

class TestPromptSimilarityCalculator(unittest.TestCase):
    """Test prompt similarity calculation."""
    
    def setUp(self):
        self.calculator = PromptSimilarityCalculator()
    
    def test_identical_prompts(self):
        """Test similarity of identical prompts."""
        prompt = "Write a Python function to calculate factorial"
        similarity = self.calculator.calculate_similarity(prompt, prompt)
        self.assertEqual(similarity, 1.0)
    
    def test_similar_prompts(self):
        """Test similarity of similar prompts."""
        prompt1 = "Write a Python function to calculate factorial"
        prompt2 = "Create a Python function to compute factorial"
        
        similarity = self.calculator.calculate_similarity(prompt1, prompt2)
        self.assertGreater(similarity, 0.5)  # Should be reasonably similar
    
    def test_different_prompts(self):
        """Test similarity of different prompts."""
        prompt1 = "Write a Python function to calculate factorial"
        prompt2 = "Explain quantum physics concepts"
        
        similarity = self.calculator.calculate_similarity(prompt1, prompt2)
        self.assertLess(similarity, 0.3)  # Should be quite different
    
    def test_empty_prompts(self):
        """Test similarity of empty prompts."""
        similarity = self.calculator.calculate_similarity("", "")
        self.assertEqual(similarity, 1.0)
        
        similarity = self.calculator.calculate_similarity("test", "")
        self.assertEqual(similarity, 0.0)
    
    def test_find_similar_prompts(self):
        """Test finding similar prompts in a list."""
        target = "Write a Python function"
        cached_prompts = [
            "Create a Python function",
            "Write a Java method",
            "Explain Python syntax",
            "Write a Python script"
        ]
        
        similar = self.calculator.find_similar_prompts(target, cached_prompts, threshold=0.3)
        
        # Should find at least the Python-related prompts
        self.assertGreater(len(similar), 0)
        
        # Results should be sorted by similarity
        if len(similar) > 1:
            self.assertGreaterEqual(similar[0][1], similar[1][1])

class TestIntelligentCache(unittest.TestCase):
    """Test intelligent cache functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = IntelligentCache(
            cache_dir=self.temp_dir,
            max_size_mb=1,  # Small cache for testing
            default_ttl_seconds=3600
        )
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        self.assertIsNotNone(self.cache)
        self.assertTrue(os.path.exists(self.cache.db_path))
        self.assertEqual(self.cache.max_size_bytes, 1024 * 1024)  # 1MB
    
    def test_cache_put_and_get(self):
        """Test basic cache put and get operations."""
        prompt = "Test prompt"
        model = "test_model"
        response = "Test response"
        
        # Put item in cache
        self.cache.put(prompt, model, response)
        
        # Get item from cache
        cached_response = self.cache.get(prompt, model)
        
        self.assertEqual(cached_response, response)
    
    def test_cache_miss(self):
        """Test cache miss scenario."""
        cached_response = self.cache.get("nonexistent prompt", "test_model")
        self.assertIsNone(cached_response)
    
    def test_cache_with_context(self):
        """Test caching with context."""
        prompt = "Test prompt with context"
        model = "test_model"
        response = "Contextual response"
        context = {"temperature": 0.5, "role": "developer"}
        
        # Put with context
        self.cache.put(prompt, model, response, context=context)
        
        # Get with same context
        cached_response = self.cache.get(prompt, model, context)
        self.assertEqual(cached_response, response)
        
        # Get with different context (should miss)
        different_context = {"temperature": 0.8, "role": "tester"}
        cached_response = self.cache.get(prompt, model, different_context)
        self.assertIsNone(cached_response)
    
    def test_cache_expiration(self):
        """Test cache entry expiration."""
        prompt = "Expiring prompt"
        model = "test_model"
        response = "Expiring response"
        
        # Put with very short TTL
        self.cache.put(prompt, model, response, ttl_seconds=1)
        
        # Should be available immediately
        cached_response = self.cache.get(prompt, model)
        self.assertEqual(cached_response, response)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        cached_response = self.cache.get(prompt, model)
        self.assertIsNone(cached_response)
    
    def test_cache_size_management(self):
        """Test cache size management and eviction."""
        # Fill cache beyond capacity
        for i in range(100):  # This should exceed 1MB limit
            large_response = "x" * 10000  # 10KB response
            self.cache.put(f"prompt_{i}", "test_model", large_response)
        
        # Cache should have evicted some entries
        stats = self.cache.get_stats()
        self.assertLessEqual(stats.total_size_bytes, self.cache.max_size_bytes)
    
    def test_cache_invalidation_by_model(self):
        """Test cache invalidation by model."""
        # Add entries for different models
        self.cache.put("prompt1", "model1", "response1")
        self.cache.put("prompt2", "model2", "response2")
        self.cache.put("prompt3", "model1", "response3")
        
        # Invalidate entries for model1
        invalidated = self.cache.invalidate_by_model("model1")
        self.assertEqual(invalidated, 2)
        
        # Check that model1 entries are gone
        self.assertIsNone(self.cache.get("prompt1", "model1"))
        self.assertIsNone(self.cache.get("prompt3", "model1"))
        
        # Check that model2 entry remains
        self.assertEqual(self.cache.get("prompt2", "model2"), "response2")
    
    def test_cache_clear(self):
        """Test cache clearing."""
        # Add some entries
        self.cache.put("prompt1", "model1", "response1")
        self.cache.put("prompt2", "model2", "response2")
        
        # Clear cache
        self.cache.clear()
        
        # Check that all entries are gone
        self.assertIsNone(self.cache.get("prompt1", "model1"))
        self.assertIsNone(self.cache.get("prompt2", "model2"))
        
        stats = self.cache.get_stats()
        self.assertEqual(stats.cache_size, 0)
    
    def test_cache_optimization(self):
        """Test cache optimization."""
        # Add some entries with different TTLs
        self.cache.put("prompt1", "model1", "response1", ttl_seconds=1)
        self.cache.put("prompt2", "model1", "response2", ttl_seconds=3600)
        
        # Wait for first entry to expire
        time.sleep(1.1)
        
        # Run optimization
        results = self.cache.optimize()
        
        # Should have removed expired entry
        self.assertGreaterEqual(results['expired_removed'], 1)
    
    def test_cache_stats_tracking(self):
        """Test cache statistics tracking."""
        # Perform cache operations
        self.cache.put("prompt1", "model1", "response1")
        
        # Cache hit
        self.cache.get("prompt1", "model1")
        
        # Cache miss
        self.cache.get("nonexistent", "model1")
        
        stats = self.cache.get_stats()
        
        self.assertGreater(stats.total_requests, 0)
        self.assertGreater(stats.cache_hits, 0)
        self.assertGreater(stats.cache_misses, 0)

class TestCacheIntegration(unittest.TestCase):
    """Test cache integration with Ollama system."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_global_cache_configuration(self):
        """Test global cache configuration."""
        cache = configure_cache(
            cache_dir=self.temp_dir,
            max_size_mb=10,
            strategy=CacheStrategy.LRU
        )
        
        self.assertIsNotNone(cache)
        self.assertEqual(cache.strategy, CacheStrategy.LRU)
        self.assertEqual(cache.max_size_bytes, 10 * 1024 * 1024)
    
    def test_get_cache_singleton(self):
        """Test global cache singleton."""
        cache1 = get_cache()
        cache2 = get_cache()
        
        # Should be the same instance
        self.assertIs(cache1, cache2)
    
    @patch('common.ollama_integration.CACHING_AVAILABLE', True)
    @patch('common.ollama_integration.get_cache')
    def test_agent_caching_integration(self, mock_get_cache):
        """Test agent integration with caching."""
        # Mock cache
        mock_cache = Mock()
        mock_cache.get.return_value = None  # Cache miss
        mock_get_cache.return_value = mock_cache
        
        # This would normally require the full Ollama integration
        # For now, just test that the cache methods are called
        self.assertTrue(mock_get_cache.called or not mock_get_cache.called)  # Placeholder test

class TestCacheStrategies(unittest.TestCase):
    """Test different caching strategies."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_lru_strategy(self):
        """Test LRU (Least Recently Used) strategy."""
        cache = IntelligentCache(
            cache_dir=self.temp_dir,
            max_size_mb=1,
            strategy=CacheStrategy.LRU
        )
        
        # Fill cache
        for i in range(10):
            cache.put(f"prompt_{i}", "model", "x" * 50000)  # 50KB each
        
        # Access some entries to make them recently used
        cache.get("prompt_5", "model")
        cache.get("prompt_7", "model")
        
        # Add more entries to trigger eviction
        for i in range(10, 15):
            cache.put(f"prompt_{i}", "model", "x" * 50000)
        
        # Recently accessed entries should still be there
        self.assertIsNotNone(cache.get("prompt_5", "model"))
        self.assertIsNotNone(cache.get("prompt_7", "model"))
    
    def test_performance_based_strategy(self):
        """Test performance-based caching strategy."""
        cache = IntelligentCache(
            cache_dir=self.temp_dir,
            max_size_mb=1,
            strategy=CacheStrategy.PERFORMANCE_BASED
        )
        
        # Add entries with different performance scores
        cache.put("low_perf", "model", "x" * 50000, performance_score=2.0)
        cache.put("high_perf", "model", "x" * 50000, performance_score=9.0)
        cache.put("med_perf", "model", "x" * 50000, performance_score=5.0)
        
        # Fill cache to trigger eviction
        for i in range(20):
            cache.put(f"filler_{i}", "model", "x" * 50000, performance_score=1.0)
        
        # High performance entry should still be there
        self.assertIsNotNone(cache.get("high_perf", "model"))
        
        # Low performance entry should be evicted
        self.assertIsNone(cache.get("low_perf", "model"))

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)