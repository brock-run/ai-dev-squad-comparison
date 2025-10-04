"""Embedding Cache for Phase 2 AI Services

Provides LRU cache with disk persistence for embeddings.
"""

import os
import json
import hashlib
import pickle
import time
from typing import List, Optional, Dict, Any
from pathlib import Path
from collections import OrderedDict


class EmbeddingCache:
    """LRU cache for embeddings with disk persistence."""
    
    def __init__(self, cache_dir: str = ".cache/embeddings", max_memory_items: int = 1000, 
                 max_disk_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_items = max_memory_items
        self.max_disk_mb = max_disk_mb
        
        # In-memory LRU cache
        self.memory_cache: OrderedDict[str, List[float]] = OrderedDict()
        
        # Metadata file for disk cache
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "version": "1.0",
            "created_at": time.time(),
            "entries": {},
            "total_size_bytes": 0
        }
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache metadata: {e}")
    
    def _compute_key(self, text: str, model: str = "default") -> str:
        """Compute cache key for text and model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key."""
        # Use first 2 chars for subdirectory to avoid too many files in one dir
        subdir = self.cache_dir / key[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{key}.pkl"
    
    def get(self, text: str, model: str = "default") -> Optional[List[float]]:
        """Get embedding from cache."""
        key = self._compute_key(text, model)
        
        # Check memory cache first
        if key in self.memory_cache:
            # Move to end (most recently used)
            embedding = self.memory_cache.pop(key)
            self.memory_cache[key] = embedding
            return embedding
        
        # Check disk cache
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    embedding = pickle.load(f)
                
                # Add to memory cache
                self._add_to_memory(key, embedding)
                
                # Update access time in metadata
                if key in self.metadata["entries"]:
                    self.metadata["entries"][key]["last_accessed"] = time.time()
                    self._save_metadata()
                
                return embedding
                
            except Exception as e:
                print(f"Warning: Failed to load cached embedding {key}: {e}")
                # Remove corrupted file
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def put(self, text: str, embedding: List[float], model: str = "default") -> List[float]:
        """Store embedding in cache and return it."""
        key = self._compute_key(text, model)
        
        # Add to memory cache
        self._add_to_memory(key, embedding)
        
        # Save to disk cache
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
            
            # Update metadata
            file_size = cache_file.stat().st_size
            self.metadata["entries"][key] = {
                "created_at": time.time(),
                "last_accessed": time.time(),
                "size_bytes": file_size,
                "model": model,
                "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16]
            }
            self.metadata["total_size_bytes"] += file_size
            
            # Clean up if cache is too large
            self._cleanup_disk_cache()
            
            self._save_metadata()
            
        except Exception as e:
            print(f"Warning: Failed to cache embedding {key}: {e}")
        
        return embedding
    
    def _add_to_memory(self, key: str, embedding: List[float]):
        """Add embedding to memory cache with LRU eviction."""
        # Remove if already exists
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Add to end
        self.memory_cache[key] = embedding
        
        # Evict oldest if over limit
        while len(self.memory_cache) > self.max_memory_items:
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
    
    def _cleanup_disk_cache(self):
        """Clean up disk cache if it exceeds size limit."""
        max_bytes = self.max_disk_mb * 1024 * 1024
        
        if self.metadata["total_size_bytes"] <= max_bytes:
            return
        
        # Sort entries by last accessed time (oldest first)
        entries = list(self.metadata["entries"].items())
        entries.sort(key=lambda x: x[1]["last_accessed"])
        
        # Remove oldest entries until under limit
        for key, entry in entries:
            if self.metadata["total_size_bytes"] <= max_bytes:
                break
            
            # Remove file
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
            
            # Update metadata
            self.metadata["total_size_bytes"] -= entry["size_bytes"]
            del self.metadata["entries"][key]
    
    def clear(self):
        """Clear all cached embeddings."""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob('**/*.pkl'):
            cache_file.unlink()
        
        # Reset metadata
        self.metadata = {
            "version": "1.0",
            "created_at": time.time(),
            "entries": {},
            "total_size_bytes": 0
        }
        self._save_metadata()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "memory_items": len(self.memory_cache),
            "disk_items": len(self.metadata["entries"]),
            "disk_size_mb": self.metadata["total_size_bytes"] / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
            "max_memory_items": self.max_memory_items,
            "max_disk_mb": self.max_disk_mb
        }


def embed_cosine(embed_client, cache: EmbeddingCache, text1: str, text2: str, model: str = "default") -> float:
    """Compute cosine similarity between two texts using cached embeddings."""
    import math
    
    # Get or compute embeddings
    v1 = cache.get(text1, model)
    if v1 is None:
        response1 = embed_client.embed([text1])
        # Handle both EmbeddingResponse and direct list returns
        if hasattr(response1, 'embeddings'):
            v1 = cache.put(text1, response1.embeddings[0], model)
        else:
            v1 = cache.put(text1, response1[0], model)
    
    v2 = cache.get(text2, model)
    if v2 is None:
        response2 = embed_client.embed([text2])
        # Handle both EmbeddingResponse and direct list returns
        if hasattr(response2, 'embeddings'):
            v2 = cache.put(text2, response2.embeddings[0], model)
        else:
            v2 = cache.put(text2, response2[0], model)
    
    # Compute cosine similarity
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


if __name__ == "__main__":
    # Test embedding cache
    print("🧪 Testing embedding cache...")
    
    cache = EmbeddingCache(cache_dir=".test_cache", max_memory_items=3, max_disk_mb=1)
    
    # Test storing and retrieving embeddings
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    # Store embedding
    result = cache.put("hello world", test_embedding, "test_model")
    assert result == test_embedding
    
    # Retrieve embedding
    retrieved = cache.get("hello world", "test_model")
    assert retrieved == test_embedding
    
    # Test cache miss
    missing = cache.get("not found", "test_model")
    assert missing is None
    
    # Test stats
    stats = cache.get_stats()
    print(f"✅ Cache stats: {stats}")
    
    # Clean up test cache
    cache.clear()
    
    print("\n🎉 Embedding cache working correctly!")