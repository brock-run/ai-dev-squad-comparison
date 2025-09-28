#!/usr/bin/env python3
"""
Intelligent Caching System for AI Dev Squad

This module provides smart caching for LLM interactions with cache invalidation
strategies, performance-based optimization, and context-aware cache management.
"""

import os
import json
import hashlib
import time
import logging
import pickle
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from enum import Enum
from pathlib import Path
import sqlite3
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger("ai_dev_squad.caching")


class CacheStrategy(Enum):
    """Cache strategies for different types of content."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    PERFORMANCE_BASED = "performance_based"  # Based on model performance
    SIMILARITY_BASED = "similarity_based"  # Based on content similarity


class CacheInvalidationReason(Enum):
    """Reasons for cache invalidation."""
    EXPIRED = "expired"
    SIZE_LIMIT = "size_limit"
    MANUAL = "manual"
    MODEL_HEALTH_CHANGE = "model_health_change"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CONTEXT_CHANGE = "context_change"


@dataclass
class CacheEntry:
    """Represents a cached LLM response."""
    key: str
    prompt_hash: str
    model_name: str
    response: str
    metadata: Dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    access_count: int
    performance_score: float
    context_hash: Optional[str] = None
    ttl_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def update_access(self) -> None:
        """Update access statistics."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['last_accessed'] = self.last_accessed.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)


@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_size: int = 0
    total_size_bytes: int = 0
    avg_response_time_cached: float = 0.0
    avg_response_time_uncached: float = 0.0
    invalidations: Dict[str, int] = None
    
    def __post_init__(self):
        if self.invalidations is None:
            self.invalidations = {reason.value: 0 for reason in CacheInvalidationReason}
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    @property
    def performance_improvement(self) -> float:
        """Calculate performance improvement from caching."""
        if self.avg_response_time_uncached == 0:
            return 0.0
        return (self.avg_response_time_uncached - self.avg_response_time_cached) / self.avg_response_time_uncached


class PromptSimilarityCalculator:
    """Calculate similarity between prompts for intelligent caching."""
    
    def __init__(self):
        self.word_cache = {}
    
    def calculate_similarity(self, prompt1: str, prompt2: str) -> float:
        """
        Calculate similarity between two prompts using simple word overlap.
        
        Args:
            prompt1: First prompt.
            prompt2: Second prompt.
            
        Returns:
            Similarity score between 0 and 1.
        """
        words1 = set(self._tokenize(prompt1.lower()))
        words2 = set(self._tokenize(prompt2.lower()))
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        import re
        return re.findall(r'\b\w+\b', text)
    
    def find_similar_prompts(self, target_prompt: str, cached_prompts: List[str], 
                           threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Find similar prompts in cache.
        
        Args:
            target_prompt: The prompt to find similarities for.
            cached_prompts: List of cached prompts.
            threshold: Minimum similarity threshold.
            
        Returns:
            List of (prompt, similarity_score) tuples above threshold.
        """
        similar = []
        
        for cached_prompt in cached_prompts:
            similarity = self.calculate_similarity(target_prompt, cached_prompt)
            if similarity >= threshold:
                similar.append((cached_prompt, similarity))
        
        # Sort by similarity descending
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar


class IntelligentCache:
    """Intelligent caching system with multiple strategies and optimization."""
    
    def __init__(self, 
                 cache_dir: str = None,
                 max_size_mb: int = 500,
                 default_ttl_seconds: int = 3600,
                 strategy: CacheStrategy = CacheStrategy.PERFORMANCE_BASED,
                 similarity_threshold: float = 0.8):
        """
        Initialize the intelligent cache.
        
        Args:
            cache_dir: Directory for cache storage.
            max_size_mb: Maximum cache size in MB.
            default_ttl_seconds: Default TTL for cache entries.
            strategy: Default caching strategy.
            similarity_threshold: Threshold for prompt similarity matching.
        """
        self.cache_dir = Path(cache_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "cache"
        ))
        self.cache_dir.mkdir(exist_ok=True)
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds
        self.strategy = strategy
        self.similarity_threshold = similarity_threshold
        
        # Initialize database
        self.db_path = self.cache_dir / "cache.db"
        self._init_database()
        
        # Initialize components
        self.similarity_calculator = PromptSimilarityCalculator()
        self.stats = CacheStats()
        self._lock = threading.RLock()
        
        # Load existing stats
        self._load_stats()
        
        logger.info(f"Initialized intelligent cache at {self.cache_dir}")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for cache storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    prompt_hash TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    response TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER NOT NULL,
                    performance_score REAL NOT NULL,
                    context_hash TEXT,
                    ttl_seconds INTEGER,
                    size_bytes INTEGER NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompt_hash ON cache_entries(prompt_hash)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_name ON cache_entries(model_name)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _generate_cache_key(self, prompt: str, model_name: str, 
                          context: Dict[str, Any] = None) -> str:
        """
        Generate a unique cache key for a prompt and model combination.
        
        Args:
            prompt: The input prompt.
            model_name: Name of the model.
            context: Additional context that affects the response.
            
        Returns:
            Unique cache key.
        """
        # Create a hash of the prompt
        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]
        
        # Include context in the key if provided
        context_str = ""
        if context:
            context_str = json.dumps(context, sort_keys=True)
            context_hash = hashlib.sha256(context_str.encode('utf-8')).hexdigest()[:8]
            context_str = f"_ctx_{context_hash}"
        
        return f"{model_name}_{prompt_hash}{context_str}"
    
    def _calculate_entry_size(self, entry: CacheEntry) -> int:
        """Calculate the size of a cache entry in bytes."""
        # Rough estimation of memory usage
        size = len(entry.response.encode('utf-8'))
        size += len(entry.key.encode('utf-8'))
        size += len(entry.prompt_hash.encode('utf-8'))
        size += len(entry.model_name.encode('utf-8'))
        size += len(json.dumps(entry.metadata).encode('utf-8'))
        return size
    
    def get(self, prompt: str, model_name: str, 
            context: Dict[str, Any] = None) -> Optional[str]:
        """
        Get cached response for a prompt and model.
        
        Args:
            prompt: The input prompt.
            model_name: Name of the model.
            context: Additional context.
            
        Returns:
            Cached response if found, None otherwise.
        """
        with self._lock:
            self.stats.total_requests += 1
            
            # Try exact match first
            cache_key = self._generate_cache_key(prompt, model_name, context)
            
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM cache_entries WHERE key = ?",
                    (cache_key,)
                )
                row = cursor.fetchone()
                
                if row:
                    entry = self._row_to_cache_entry(row)
                    
                    # Check if expired
                    if entry.is_expired():
                        self._invalidate_entry(cache_key, CacheInvalidationReason.EXPIRED)
                        self.stats.cache_misses += 1
                        return None
                    
                    # Update access statistics
                    entry.update_access()
                    self._update_entry_access(cache_key, entry)
                    
                    self.stats.cache_hits += 1
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return entry.response
            
            # Try similarity-based matching if enabled
            if self.strategy == CacheStrategy.SIMILARITY_BASED:
                similar_response = self._find_similar_cached_response(
                    prompt, model_name, context
                )
                if similar_response:
                    self.stats.cache_hits += 1
                    return similar_response
            
            self.stats.cache_misses += 1
            return None
    
    def put(self, prompt: str, model_name: str, response: str,
            metadata: Dict[str, Any] = None, context: Dict[str, Any] = None,
            performance_score: float = 5.0, ttl_seconds: int = None) -> None:
        """
        Cache a response for a prompt and model.
        
        Args:
            prompt: The input prompt.
            model_name: Name of the model.
            response: The model's response.
            metadata: Additional metadata.
            context: Additional context.
            performance_score: Performance score for this response (0-10).
            ttl_seconds: Time to live in seconds.
        """
        with self._lock:
            cache_key = self._generate_cache_key(prompt, model_name, context)
            prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
            context_hash = None
            
            if context:
                context_hash = hashlib.sha256(
                    json.dumps(context, sort_keys=True).encode('utf-8')
                ).hexdigest()
            
            entry = CacheEntry(
                key=cache_key,
                prompt_hash=prompt_hash,
                model_name=model_name,
                response=response,
                metadata=metadata or {},
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                performance_score=performance_score,
                context_hash=context_hash,
                ttl_seconds=ttl_seconds or self.default_ttl_seconds
            )
            
            entry_size = self._calculate_entry_size(entry)
            
            # Check if we need to make space
            self._ensure_cache_space(entry_size)
            
            # Store in database
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, prompt_hash, model_name, response, metadata, created_at, 
                     last_accessed, access_count, performance_score, context_hash, 
                     ttl_seconds, size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.key, entry.prompt_hash, entry.model_name, entry.response,
                    json.dumps(entry.metadata), entry.created_at.isoformat(),
                    entry.last_accessed.isoformat(), entry.access_count,
                    entry.performance_score, entry.context_hash,
                    entry.ttl_seconds, entry_size
                ))
                conn.commit()
            
            self.stats.cache_size += 1
            self.stats.total_size_bytes += entry_size
            
            logger.debug(f"Cached response for key: {cache_key}")
    
    def _find_similar_cached_response(self, prompt: str, model_name: str,
                                    context: Dict[str, Any] = None) -> Optional[str]:
        """
        Find similar cached responses using prompt similarity.
        
        Args:
            prompt: The input prompt.
            model_name: Name of the model.
            context: Additional context.
            
        Returns:
            Similar cached response if found, None otherwise.
        """
        with self._get_db_connection() as conn:
            # Get all cached prompts for the same model
            cursor = conn.execute(
                "SELECT prompt_hash, response, performance_score FROM cache_entries WHERE model_name = ?",
                (model_name,)
            )
            
            cached_entries = cursor.fetchall()
            
            if not cached_entries:
                return None
            
            # Find similar prompts (this is a simplified approach)
            # In a production system, you might want to use more sophisticated
            # similarity measures or vector embeddings
            
            best_similarity = 0.0
            best_response = None
            
            for entry in cached_entries:
                # For now, we'll use a simple heuristic based on prompt length
                # and common words. In practice, you'd want to store the original
                # prompts or use embeddings for better similarity matching.
                
                # This is a placeholder - in reality you'd need to store
                # the original prompts or use embeddings
                if entry['performance_score'] > 7.0:  # Only use high-quality responses
                    # Simple heuristic: if prompts are similar length, they might be similar
                    # This is very basic and should be improved with proper similarity
                    similarity = min(len(prompt), 100) / 100.0  # Placeholder
                    
                    if similarity > best_similarity and similarity >= self.similarity_threshold:
                        best_similarity = similarity
                        best_response = entry['response']
            
            if best_response:
                logger.debug(f"Found similar cached response with similarity: {best_similarity}")
            
            return best_response
    
    def _ensure_cache_space(self, required_bytes: int) -> None:
        """
        Ensure there's enough space in the cache for a new entry.
        
        Args:
            required_bytes: Bytes required for the new entry.
        """
        if self.stats.total_size_bytes + required_bytes <= self.max_size_bytes:
            return
        
        # Need to free up space based on strategy
        if self.strategy == CacheStrategy.LRU:
            self._evict_lru_entries(required_bytes)
        elif self.strategy == CacheStrategy.LFU:
            self._evict_lfu_entries(required_bytes)
        elif self.strategy == CacheStrategy.PERFORMANCE_BASED:
            self._evict_low_performance_entries(required_bytes)
        else:
            self._evict_lru_entries(required_bytes)  # Default to LRU
    
    def _evict_lru_entries(self, required_bytes: int) -> None:
        """Evict least recently used entries."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT key, size_bytes FROM cache_entries 
                ORDER BY last_accessed ASC
            """)
            
            freed_bytes = 0
            keys_to_delete = []
            
            for row in cursor:
                keys_to_delete.append(row['key'])
                freed_bytes += row['size_bytes']
                
                if freed_bytes >= required_bytes:
                    break
            
            # Delete the entries
            for key in keys_to_delete:
                self._invalidate_entry(key, CacheInvalidationReason.SIZE_LIMIT)
    
    def _evict_lfu_entries(self, required_bytes: int) -> None:
        """Evict least frequently used entries."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT key, size_bytes FROM cache_entries 
                ORDER BY access_count ASC, last_accessed ASC
            """)
            
            freed_bytes = 0
            keys_to_delete = []
            
            for row in cursor:
                keys_to_delete.append(row['key'])
                freed_bytes += row['size_bytes']
                
                if freed_bytes >= required_bytes:
                    break
            
            # Delete the entries
            for key in keys_to_delete:
                self._invalidate_entry(key, CacheInvalidationReason.SIZE_LIMIT)
    
    def _evict_low_performance_entries(self, required_bytes: int) -> None:
        """Evict entries with low performance scores."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT key, size_bytes FROM cache_entries 
                ORDER BY performance_score ASC, access_count ASC
            """)
            
            freed_bytes = 0
            keys_to_delete = []
            
            for row in cursor:
                keys_to_delete.append(row['key'])
                freed_bytes += row['size_bytes']
                
                if freed_bytes >= required_bytes:
                    break
            
            # Delete the entries
            for key in keys_to_delete:
                self._invalidate_entry(key, CacheInvalidationReason.SIZE_LIMIT)
    
    def _invalidate_entry(self, key: str, reason: CacheInvalidationReason) -> None:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate.
            reason: Reason for invalidation.
        """
        with self._get_db_connection() as conn:
            # Get entry size before deletion
            cursor = conn.execute("SELECT size_bytes FROM cache_entries WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                size_bytes = row['size_bytes']
                
                # Delete the entry
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                
                # Update stats
                self.stats.cache_size -= 1
                self.stats.total_size_bytes -= size_bytes
                self.stats.invalidations[reason.value] += 1
                
                logger.debug(f"Invalidated cache entry {key} due to {reason.value}")
    
    def _update_entry_access(self, key: str, entry: CacheEntry) -> None:
        """Update access statistics for an entry."""
        with self._get_db_connection() as conn:
            conn.execute("""
                UPDATE cache_entries 
                SET last_accessed = ?, access_count = ?
                WHERE key = ?
            """, (entry.last_accessed.isoformat(), entry.access_count, key))
            conn.commit()
    
    def _row_to_cache_entry(self, row: sqlite3.Row) -> CacheEntry:
        """Convert database row to CacheEntry object."""
        return CacheEntry(
            key=row['key'],
            prompt_hash=row['prompt_hash'],
            model_name=row['model_name'],
            response=row['response'],
            metadata=json.loads(row['metadata']),
            created_at=datetime.fromisoformat(row['created_at']),
            last_accessed=datetime.fromisoformat(row['last_accessed']),
            access_count=row['access_count'],
            performance_score=row['performance_score'],
            context_hash=row['context_hash'],
            ttl_seconds=row['ttl_seconds']
        )
    
    def invalidate_by_model(self, model_name: str) -> int:
        """
        Invalidate all cache entries for a specific model.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            Number of entries invalidated.
        """
        with self._lock:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT key FROM cache_entries WHERE model_name = ?",
                    (model_name,)
                )
                
                keys = [row['key'] for row in cursor.fetchall()]
                
                for key in keys:
                    self._invalidate_entry(key, CacheInvalidationReason.MODEL_HEALTH_CHANGE)
                
                return len(keys)
    
    def invalidate_expired(self) -> int:
        """
        Invalidate all expired cache entries.
        
        Returns:
            Number of entries invalidated.
        """
        with self._lock:
            with self._get_db_connection() as conn:
                current_time = datetime.now()
                
                cursor = conn.execute("""
                    SELECT key, created_at, ttl_seconds FROM cache_entries 
                    WHERE ttl_seconds IS NOT NULL
                """)
                
                expired_keys = []
                
                for row in cursor:
                    created_at = datetime.fromisoformat(row['created_at'])
                    ttl_seconds = row['ttl_seconds']
                    
                    if (current_time - created_at).total_seconds() > ttl_seconds:
                        expired_keys.append(row['key'])
                
                for key in expired_keys:
                    self._invalidate_entry(key, CacheInvalidationReason.EXPIRED)
                
                return len(expired_keys)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            with self._get_db_connection() as conn:
                conn.execute("DELETE FROM cache_entries")
                conn.commit()
            
            self.stats = CacheStats()
            logger.info("Cache cleared")
    
    def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        with self._lock:
            # Update current cache size from database
            with self._get_db_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM cache_entries")
                row = cursor.fetchone()
                
                if row and row[0]:
                    self.stats.cache_size = row[0]
                    self.stats.total_size_bytes = row[1] or 0
                else:
                    self.stats.cache_size = 0
                    self.stats.total_size_bytes = 0
            
            return self.stats
    
    def _load_stats(self) -> None:
        """Load statistics from persistent storage."""
        stats_file = self.cache_dir / "cache_stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                
                self.stats.total_requests = data.get('total_requests', 0)
                self.stats.cache_hits = data.get('cache_hits', 0)
                self.stats.cache_misses = data.get('cache_misses', 0)
                self.stats.avg_response_time_cached = data.get('avg_response_time_cached', 0.0)
                self.stats.avg_response_time_uncached = data.get('avg_response_time_uncached', 0.0)
                self.stats.invalidations = data.get('invalidations', 
                    {reason.value: 0 for reason in CacheInvalidationReason})
                
                logger.debug("Loaded cache statistics from file")
            except Exception as e:
                logger.warning(f"Failed to load cache statistics: {e}")
    
    def _save_stats(self) -> None:
        """Save statistics to persistent storage."""
        stats_file = self.cache_dir / "cache_stats.json"
        
        try:
            data = {
                'total_requests': self.stats.total_requests,
                'cache_hits': self.stats.cache_hits,
                'cache_misses': self.stats.cache_misses,
                'avg_response_time_cached': self.stats.avg_response_time_cached,
                'avg_response_time_uncached': self.stats.avg_response_time_uncached,
                'invalidations': self.stats.invalidations
            }
            
            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Saved cache statistics to file")
        except Exception as e:
            logger.warning(f"Failed to save cache statistics: {e}")
    
    def optimize(self) -> Dict[str, Any]:
        """
        Optimize cache performance based on usage patterns.
        
        Returns:
            Dictionary with optimization results.
        """
        with self._lock:
            optimization_results = {
                'expired_removed': self.invalidate_expired(),
                'recommendations': []
            }
            
            stats = self.get_stats()
            
            # Analyze cache performance and provide recommendations
            if stats.hit_rate < 0.3:
                optimization_results['recommendations'].append(
                    "Low hit rate detected. Consider increasing cache size or TTL."
                )
            
            if stats.total_size_bytes > self.max_size_bytes * 0.9:
                optimization_results['recommendations'].append(
                    "Cache is nearly full. Consider increasing max size or adjusting eviction strategy."
                )
            
            if stats.performance_improvement < 0.2:
                optimization_results['recommendations'].append(
                    "Low performance improvement from caching. Review caching strategy."
                )
            
            # Save updated stats
            self._save_stats()
            
            return optimization_results
    
    def __del__(self):
        """Cleanup when cache is destroyed."""
        try:
            self._save_stats()
        except:
            pass


# Global cache instance
_global_cache: Optional[IntelligentCache] = None


def get_cache() -> IntelligentCache:
    """Get the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = IntelligentCache()
    return _global_cache


def configure_cache(cache_dir: str = None, max_size_mb: int = 500,
                   default_ttl_seconds: int = 3600,
                   strategy: CacheStrategy = CacheStrategy.PERFORMANCE_BASED) -> IntelligentCache:
    """
    Configure the global cache instance.
    
    Args:
        cache_dir: Directory for cache storage.
        max_size_mb: Maximum cache size in MB.
        default_ttl_seconds: Default TTL for cache entries.
        strategy: Caching strategy to use.
        
    Returns:
        Configured cache instance.
    """
    global _global_cache
    _global_cache = IntelligentCache(
        cache_dir=cache_dir,
        max_size_mb=max_size_mb,
        default_ttl_seconds=default_ttl_seconds,
        strategy=strategy
    )
    return _global_cache