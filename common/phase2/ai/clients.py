"""AI Service Clients for Phase 2 Semantic Judge

Provides secure, version-pinned adapters for LLM and embedding services.
"""

import json
import time
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class TokenUsage:
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMResponse:
    """Response from LLM service."""
    text: str
    tokens: TokenUsage
    latency_ms: int
    cost_usd: float
    model: str
    provider: str
    timestamp: str


@dataclass
class EmbeddingResponse:
    """Response from embedding service."""
    embeddings: List[List[float]]
    tokens: int
    latency_ms: int
    cost_usd: float
    model: str
    provider: str
    timestamp: str


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, provider_id: str, model: str, max_tps: float, timeout_s: int, redact: bool = True):
        self.provider_id = provider_id
        self.model = model
        self.max_tps = max_tps
        self.timeout_s = timeout_s
        self.redact = redact
        self.last_request_time = 0.0
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, 
             temperature: float = 0.0, seed: Optional[int] = None) -> LLMResponse:
        """Send chat completion request."""
        pass
    
    @abstractmethod
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in messages."""
        pass
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting based on max_tps."""
        if self.max_tps > 0:
            min_interval = 1.0 / self.max_tps
            elapsed = time.time() - self.last_request_time
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        self.last_request_time = time.time()
    
    def _redact_content(self, content: str) -> str:
        """Redact sensitive information from content."""
        if not self.redact:
            return content
        
        import re
        
        # Redact common patterns
        patterns = [
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),
            (r'(?:api[_-]?key|token)[\\s:=]+[\'"]?([a-zA-Z0-9_-]{20,})[\'"]?', '[API_KEY]'),
            (r'eyJ[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+', '[JWT]'),
            (r'\\b(?:\\d{4}[\\s-]?){3}\\d{4}\\b', '[CREDIT_CARD]'),
            (r'\\b\\d{3}-\\d{2}-\\d{4}\\b', '[SSN]'),
        ]
        
        redacted = content
        for pattern, replacement in patterns:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        
        return redacted


class EmbeddingClient(ABC):
    """Abstract base class for embedding clients."""
    
    def __init__(self, provider_id: str, model: str, timeout_s: int = 30):
        self.provider_id = provider_id
        self.model = model
        self.timeout_s = timeout_s
    
    @abstractmethod
    def embed(self, texts: List[str]) -> EmbeddingResponse:
        """Generate embeddings for texts."""
        pass


class OpenAIAdapter(LLMClient):
    """OpenAI API adapter."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_tps: float = 10.0, 
                 timeout_s: int = 30, redact: bool = True, base_url: Optional[str] = None):
        super().__init__("openai", model, max_tps, timeout_s, redact)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_s
        )
        
        # Token pricing (approximate, per 1K tokens)
        self.pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, 
             temperature: float = 0.0, seed: Optional[int] = None) -> LLMResponse:
        """Send chat completion request to OpenAI."""
        self._enforce_rate_limit()
        
        # Redact sensitive content
        if self.redact:
            messages = [
                {**msg, "content": self._redact_content(msg["content"])}
                for msg in messages
            ]
        
        start_time = time.perf_counter()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed,
                timeout=self.timeout_s
            )
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Extract usage and calculate cost
            usage = response.usage
            tokens = TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )
            
            cost_usd = self._calculate_cost(tokens)
            
            return LLMResponse(
                text=response.choices[0].message.content,
                tokens=tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                model=self.model,
                provider=self.provider_id,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            raise RuntimeError(f"OpenAI API error after {latency_ms}ms: {e}")
    
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count for messages."""
        # Simple estimation: ~4 characters per token
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return max(1, total_chars // 4)
    
    def _calculate_cost(self, tokens: TokenUsage) -> float:
        """Calculate cost based on token usage."""
        pricing = self.pricing.get(self.model, {"input": 0.001, "output": 0.002})
        
        input_cost = (tokens.prompt_tokens / 1000) * pricing["input"]
        output_cost = (tokens.completion_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost


class OllamaAdapter(LLMClient):
    """Ollama local LLM adapter."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b", 
                 max_tps: float = 5.0, timeout_s: int = 60, redact: bool = True):
        super().__init__("ollama", model, max_tps, timeout_s, redact)
        
        if not REQUESTS_AVAILABLE:
            raise ImportError("Requests library not available. Install with: pip install requests")
        
        self.base_url = base_url.rstrip('/')
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, 
             temperature: float = 0.0, seed: Optional[int] = None) -> LLMResponse:
        """Send chat completion request to Ollama."""
        self._enforce_rate_limit()
        
        # Redact sensitive content
        if self.redact:
            messages = [
                {**msg, "content": self._redact_content(msg["content"])}
                for msg in messages
            ]
        
        start_time = time.perf_counter()
        
        try:
            # Convert to Ollama format
            prompt = self._messages_to_prompt(messages)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "seed": seed
                },
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_s
            )
            response.raise_for_status()
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            result = response.json()
            
            # Estimate tokens (Ollama doesn't always provide exact counts)
            prompt_tokens = self.count_tokens(messages)
            completion_tokens = len(result.get("response", "")) // 4
            
            tokens = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
            
            return LLMResponse(
                text=result.get("response", ""),
                tokens=tokens,
                latency_ms=latency_ms,
                cost_usd=0.0,  # Local model, no cost
                model=self.model,
                provider=self.provider_id,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            raise RuntimeError(f"Ollama API error after {latency_ms}ms: {e}")
    
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count for messages."""
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return max(1, total_chars // 4)
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to Ollama prompt."""
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts) + "\n\nAssistant:"


class OpenAIEmbeddingAdapter(EmbeddingClient):
    """OpenAI embedding adapter."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small", timeout_s: int = 30):
        super().__init__("openai", model, timeout_s)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        self.client = openai.OpenAI(api_key=api_key, timeout=timeout_s)
        
        # Embedding pricing (per 1K tokens)
        self.pricing = {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
            "text-embedding-ada-002": 0.0001,
        }
    
    def embed(self, texts: List[str]) -> EmbeddingResponse:
        """Generate embeddings using OpenAI."""
        start_time = time.perf_counter()
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            embeddings = [data.embedding for data in response.data]
            tokens = response.usage.total_tokens
            
            # Calculate cost
            pricing = self.pricing.get(self.model, 0.0001)
            cost_usd = (tokens / 1000) * pricing
            
            return EmbeddingResponse(
                embeddings=embeddings,
                tokens=tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                model=self.model,
                provider=self.provider_id,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            raise RuntimeError(f"OpenAI Embedding API error after {latency_ms}ms: {e}")


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self, model: str = "mock-gpt", deterministic: bool = True):
        super().__init__("mock", model, 0.0, 30, False)
        self.deterministic = deterministic
        self.call_count = 0
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, 
             temperature: float = 0.0, seed: Optional[int] = None) -> LLMResponse:
        """Mock chat completion."""
        self.call_count += 1
        
        # Simulate processing time
        time.sleep(0.01)
        
        # Generate deterministic response based on input
        if self.deterministic:
            content_hash = hashlib.md5(str(messages).encode()).hexdigest()[:8]
            response_text = f'{{"equivalent": true, "confidence": 0.85, "reasoning": "Mock response {content_hash}"}}'
        else:
            response_text = '{"equivalent": false, "confidence": 0.3, "reasoning": "Mock non-deterministic response"}'
        
        tokens = TokenUsage(
            prompt_tokens=self.count_tokens(messages),
            completion_tokens=len(response_text) // 4,
            total_tokens=self.count_tokens(messages) + len(response_text) // 4
        )
        
        return LLMResponse(
            text=response_text,
            tokens=tokens,
            latency_ms=10,
            cost_usd=0.001,
            model=self.model,
            provider=self.provider_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Mock token counting."""
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return max(1, total_chars // 4)


class MockEmbeddingClient(EmbeddingClient):
    """Mock embedding client for testing."""
    
    def __init__(self, model: str = "mock-embedding", dimensions: int = 384):
        super().__init__("mock", model, 30)
        self.dimensions = dimensions
    
    def embed(self, texts: List[str]) -> EmbeddingResponse:
        """Mock embedding generation."""
        import random
        
        # Generate deterministic embeddings based on text hash
        embeddings = []
        for text in texts:
            # Use hash to seed random generator for deterministic results
            text_hash = hashlib.md5(text.encode()).hexdigest()
            random.seed(int(text_hash[:8], 16))
            
            # Generate normalized random vector
            vector = [random.gauss(0, 1) for _ in range(self.dimensions)]
            norm = sum(x*x for x in vector) ** 0.5
            normalized = [x/norm for x in vector] if norm > 0 else vector
            embeddings.append(normalized)
        
        return EmbeddingResponse(
            embeddings=embeddings,
            tokens=sum(len(text) // 4 for text in texts),
            latency_ms=5,
            cost_usd=0.0001,
            model=self.model,
            provider=self.provider_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )


def create_llm_client(provider: str, **kwargs) -> LLMClient:
    """Factory function to create LLM clients."""
    if provider == "openai":
        return OpenAIAdapter(**kwargs)
    elif provider == "ollama":
        return OllamaAdapter(**kwargs)
    elif provider == "mock":
        return MockLLMClient(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def create_embedding_client(provider: str, **kwargs) -> EmbeddingClient:
    """Factory function to create embedding clients."""
    if provider == "openai":
        return OpenAIEmbeddingAdapter(**kwargs)
    elif provider == "mock":
        return MockEmbeddingClient(**kwargs)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


if __name__ == "__main__":
    # Test mock clients
    print("🧪 Testing AI clients...")
    
    # Test mock LLM
    llm = MockLLMClient()
    messages = [{"role": "user", "content": "Test message"}]
    response = llm.chat(messages)
    print(f"✅ Mock LLM: {response.text[:50]}...")
    
    # Test mock embedding
    embed = MockEmbeddingClient()
    embed_response = embed.embed(["test text", "another text"])
    print(f"✅ Mock Embedding: {len(embed_response.embeddings)} vectors of {len(embed_response.embeddings[0])} dimensions")
    
    print("🎉 AI clients working correctly!")