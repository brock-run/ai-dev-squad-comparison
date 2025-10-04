"""Mock AI Clients for Testing

Provides deterministic mock clients for CI/testing environments.
"""

import time
import json
import hashlib
from typing import List, Dict, Any

from .clients import LLMClient, EmbeddingClient


class MockLLMClient(LLMClient):
    """Mock LLM client with deterministic responses."""
    
    def __init__(self, model: str = "mock-llm", deterministic: bool = True):
        super().__init__("mock", model, 10.0, 30, True)
        self.deterministic = deterministic
        self.call_count = 0
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, 
             temperature: float = 0.0, seed: int = None) -> Dict[str, Any]:
        """Generate deterministic mock LLM response."""
        self.call_count += 1
        
        # Extract content for analysis
        content = " ".join([msg.get("content", "") for msg in messages])
        
        # Simple heuristic-based response
        if self.deterministic:
            # Use content hash for deterministic responses
            content_hash = hashlib.md5(content.encode()).hexdigest()
            hash_int = int(content_hash[:8], 16)
            
            # Deterministic equivalence decision based on content
            equivalent = self._analyze_content_similarity(content)
            confidence = 0.7 + (hash_int % 30) / 100.0  # 0.70-0.99
            
            reasoning = self._generate_reasoning(content, equivalent)
            
        else:
            # Random responses for stress testing
            import random
            equivalent = random.choice([True, False])
            confidence = random.uniform(0.5, 0.95)
            reasoning = "Random mock response"
        
        response_json = {
            "equivalent": equivalent,
            "confidence": confidence,
            "reasoning": reasoning,
            "violations": []
        }
        
        return {
            "text": json.dumps(response_json),
            "tokens": {"prompt": len(content) // 4, "completion": 50, "total": len(content) // 4 + 50},
            "latency_ms": 500 + (self.call_count * 10),  # Simulate increasing latency
            "cost_usd": 0.001,
            "model": self.model,
            "provider": self.provider_id
        }
    
    def count_tokens(self, messages: List[Dict[str, str]]) -> Dict[str, int]:
        """Mock token counting."""
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        tokens = total_chars // 4  # Rough approximation
        return {"prompt": tokens, "total": tokens}
    
    def _analyze_content_similarity(self, content: str) -> bool:
        """Simple heuristic to determine equivalence."""
        content_lower = content.lower()
        
        # Look for obvious differences
        if "different" in content_lower or "not equivalent" in content_lower:
            return False
        
        # Look for similarity indicators
        if "same" in content_lower or "equivalent" in content_lower or "similar" in content_lower:
            return True
        
        # Check for JSON structure similarity
        if "json" in content_lower and "{" in content and "}" in content:
            # Simple JSON equivalence check
            try:
                # Extract potential JSON objects
                import re
                json_matches = re.findall(r'\{[^{}]*\}', content)
                if len(json_matches) >= 2:
                    # Compare first two JSON-like structures
                    try:
                        obj1 = json.loads(json_matches[0])
                        obj2 = json.loads(json_matches[1])
                        return obj1 == obj2
                    except:
                        pass
            except:
                pass
        
        # For testing: make it more realistic by checking actual content similarity
        # Extract the two text snippets being compared
        lines = content.split('\n')
        text_snippets = []
        for line in lines:
            if 'excerpt' in line or 'content' in line:
                # Try to extract quoted text
                import re
                quotes = re.findall(r'"([^"]*)"', line)
                text_snippets.extend(quotes)
        
        if len(text_snippets) >= 2:
            # Simple similarity check
            text1, text2 = text_snippets[0], text_snippets[1]
            
            # Exact match
            if text1 == text2:
                return True
            
            # JSON reordering check
            if text1.startswith('{') and text2.startswith('{'):
                try:
                    obj1 = json.loads(text1)
                    obj2 = json.loads(text2)
                    return obj1 == obj2
                except:
                    pass
            
            # Whitespace differences (for code)
            if text1.replace(' ', '').replace('\n', '').replace('\t', '') == \
               text2.replace(' ', '').replace('\n', '').replace('\t', ''):
                return True
            
            # Different content
            return False
        
        # Default: be conservative for unknown content (prefer false negatives over false positives)
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return int(content_hash[:2], 16) % 4 == 0  # 25% equivalent for unknown content
    
    def _generate_reasoning(self, content: str, equivalent: bool) -> str:
        """Generate plausible reasoning."""
        if equivalent:
            reasons = [
                "Content appears semantically equivalent despite formatting differences",
                "Core meaning and structure are preserved",
                "Differences are cosmetic and don't affect semantic content",
                "Both versions convey the same information"
            ]
        else:
            reasons = [
                "Semantic differences detected in content structure",
                "Key information differs between versions",
                "Structural changes affect meaning",
                "Content modifications change semantic intent"
            ]
        
        # Select reason based on content hash for consistency
        content_hash = hashlib.md5(content.encode()).hexdigest()
        reason_idx = int(content_hash[-1], 16) % len(reasons)
        return reasons[reason_idx]


class MockEmbeddingClient(EmbeddingClient):
    """Mock embedding client with deterministic vectors."""
    
    def __init__(self, model: str = "mock-embed", dimension: int = 384):
        super().__init__("mock", model)
        self.dimension = dimension
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings based on text content."""
        embeddings = []
        
        for text in texts:
            # Generate deterministic embedding from text hash
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            # Convert hash to embedding vector
            embedding = []
            for i in range(self.dimension):
                # Use different parts of hash for each dimension
                hash_part = text_hash[(i * 2) % len(text_hash):(i * 2 + 8) % len(text_hash)]
                if len(hash_part) < 8:
                    hash_part = (text_hash + text_hash)[:8]
                
                # Convert to float in [-1, 1] range
                hash_int = int(hash_part, 16) if hash_part else 0
                value = (hash_int % 2000 - 1000) / 1000.0
                embedding.append(value)
            
            # Normalize to unit vector
            norm = sum(x * x for x in embedding) ** 0.5
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            embeddings.append(embedding)
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


def create_mock_clients(config: Dict[str, Any] = None) -> tuple:
    """Create mock LLM and embedding clients for testing."""
    config = config or {}
    
    llm_client = MockLLMClient(
        model=config.get("llm_model", "mock-llm"),
        deterministic=config.get("deterministic", True)
    )
    
    embedding_client = MockEmbeddingClient(
        model=config.get("embedding_model", "mock-embed"),
        dimension=config.get("embedding_dimension", 384)
    )
    
    return llm_client, embedding_client


if __name__ == "__main__":
    # Test mock clients
    print("🧪 Testing mock AI clients...")
    
    llm, embed = create_mock_clients()
    
    # Test LLM
    messages = [{"role": "user", "content": "Compare these two texts for equivalence"}]
    response = llm.chat(messages)
    print(f"✅ LLM response: {response['text'][:100]}...")
    
    # Test embeddings
    texts = ["hello world", "hello world", "goodbye world"]
    embeddings = embed.embed(texts)
    print(f"✅ Embeddings: {len(embeddings)} vectors of dimension {len(embeddings[0])}")
    
    # Test similarity
    from .cache import embed_cosine, EmbeddingCache
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = EmbeddingCache(cache_dir=temp_dir)
        
        # Same text should have high similarity
        sim1 = embed_cosine(embed, cache, "hello world", "hello world")
        print(f"✅ Same text similarity: {sim1:.3f}")
        
        # Different text should have lower similarity
        sim2 = embed_cosine(embed, cache, "hello world", "goodbye world")
        print(f"✅ Different text similarity: {sim2:.3f}")
    
    print("\n🎉 Mock AI clients working correctly!")