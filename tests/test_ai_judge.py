"""Tests for AI Judge Components

Tests equivalence evaluation with mock providers.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from common.phase2.ai.clients import LLMClient, EmbeddingClient, OpenAIAdapter, OllamaAdapter
from common.phase2.ai.judge import EquivalenceRunner, BudgetEnforcer
from common.phase2.ai.cache import EmbeddingCache, embed_cosine
from common.phase2.enums import EquivalenceMethod, ArtifactType
from common.phase2.diff_entities import EvaluationStatus


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self, responses=None, fail_after=None):
        super().__init__("mock", "mock-model", 10.0, 30, True)
        self.responses = responses or []
        self.call_count = 0
        self.fail_after = fail_after
    
    def chat(self, messages, max_tokens=256, temperature=0.0, seed=None):
        if self.fail_after and self.call_count >= self.fail_after:
            raise RuntimeError("Mock LLM failure")
        
        response_idx = min(self.call_count, len(self.responses) - 1)
        response = self.responses[response_idx] if self.responses else {
            "equivalent": True,
            "confidence": 0.85,
            "reasoning": "Mock evaluation"
        }
        
        self.call_count += 1
        
        return {
            "text": json.dumps(response),
            "tokens": {"prompt": 100, "completion": 50, "total": 150},
            "latency_ms": 500,
            "cost_usd": 0.001,
            "model": self.model,
            "provider": self.provider_id
        }
    
    def count_tokens(self, messages):
        return {"prompt": len(str(messages)) // 4, "total": len(str(messages)) // 4}


class MockEmbeddingClient(EmbeddingClient):
    """Mock embedding client for testing."""
    
    def __init__(self, dimension=384):
        super().__init__("mock", "mock-embed")
        self.dimension = dimension
        self.call_count = 0
    
    def embed(self, texts):
        import random
        random.seed(42)  # Deterministic for testing
        
        embeddings = []
        for text in texts:
            # Generate deterministic embedding based on text hash
            text_hash = hash(text) % 1000000
            random.seed(text_hash)
            embedding = [random.random() for _ in range(self.dimension)]
            embeddings.append(embedding)
        
        self.call_count += 1
        return embeddings
    
    def get_dimension(self):
        return self.dimension


class TestBudgetEnforcer:
    """Test budget enforcement."""
    
    def test_budget_initialization(self):
        enforcer = BudgetEnforcer(max_cost_usd=0.10, max_latency_ms=5000)
        
        assert enforcer.max_cost_usd == 0.10
        assert enforcer.max_latency_ms == 5000
        assert enforcer.total_cost == 0.0
        assert not enforcer.is_budget_exceeded()
    
    def test_request_budget_check(self):
        enforcer = BudgetEnforcer(max_tokens_per_request=1000)
        
        assert enforcer.check_request_budget(500)
        assert not enforcer.check_request_budget(1500)
    
    def test_cost_budget_enforcement(self):
        enforcer = BudgetEnforcer(max_cost_usd=0.05)
        
        # Within budget
        assert enforcer.record_request(0.02, 1000)
        assert not enforcer.is_budget_exceeded()
        
        # Exceed budget
        assert not enforcer.record_request(0.04, 1000)
        assert enforcer.is_budget_exceeded()
    
    def test_latency_budget_enforcement(self):
        enforcer = BudgetEnforcer(max_latency_ms=2000)
        
        # Within budget
        assert enforcer.record_request(0.01, 1500)
        
        # Exceed latency
        assert not enforcer.record_request(0.01, 3000)
    
    def test_budget_stats(self):
        enforcer = BudgetEnforcer()
        
        enforcer.record_request(0.01, 1000)
        enforcer.record_request(0.02, 1500)
        
        stats = enforcer.get_stats()
        assert stats["total_cost_usd"] == 0.03
        assert stats["total_latency_ms"] == 2500
        assert stats["request_count"] == 2
        assert stats["avg_latency_ms"] == 1250


class TestEmbeddingCache:
    """Test embedding cache functionality."""
    
    def test_cache_operations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = EmbeddingCache(cache_dir=temp_dir, max_memory_items=2)
            
            # Test put and get
            embedding = [0.1, 0.2, 0.3]
            result = cache.put("test", embedding, "model1")
            assert result == embedding
            
            retrieved = cache.get("test", "model1")
            assert retrieved == embedding
            
            # Test cache miss
            missing = cache.get("nonexistent", "model1")
            assert missing is None
    
    def test_memory_lru_eviction(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = EmbeddingCache(cache_dir=temp_dir, max_memory_items=2)
            
            # Fill cache beyond limit
            cache.put("key1", [1.0], "model")
            cache.put("key2", [2.0], "model")
            cache.put("key3", [3.0], "model")  # Should evict key1
            
            # key1 should be evicted from memory but available on disk
            assert len(cache.memory_cache) == 2
            assert "key1" not in cache.memory_cache
            assert "key3" in cache.memory_cache
            
            # Should still be retrievable from disk
            retrieved = cache.get("key1", "model")
            assert retrieved == [1.0]
    
    def test_cache_stats(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = EmbeddingCache(cache_dir=temp_dir)
            
            cache.put("test1", [1.0], "model")
            cache.put("test2", [2.0], "model")
            
            stats = cache.get_stats()
            assert stats["memory_items"] == 2
            assert stats["disk_items"] == 2
            assert stats["disk_size_mb"] > 0


class TestEquivalenceRunner:
    """Test equivalence evaluation runner."""
    
    def create_mock_diff(self, diff_id="test-diff"):
        """Create mock diff object."""
        class MockDiff:
            def __init__(self, diff_id):
                self.id = diff_id
                self.source_artifact_id = f"src_{diff_id}"
                self.target_artifact_id = f"tgt_{diff_id}"
        
        return MockDiff(diff_id)
    
    def test_exact_match_method(self):
        runner = EquivalenceRunner()
        diff = self.create_mock_diff()
        
        # Test exact match
        evaluation = runner.run(
            diff=diff,
            source_text="hello world",
            target_text="hello world",
            artifact_type=ArtifactType.TEXT,
            methods=[EquivalenceMethod.EXACT]
        )
        
        assert evaluation.status == EvaluationStatus.COMPLETED
        assert len(evaluation.results) == 1
        
        result = evaluation.results[0]
        assert result.method == EquivalenceMethod.EXACT
        assert result.equivalent is True
        assert result.confidence == 1.0
        assert result.cost == 0.0
    
    def test_exact_mismatch(self):
        runner = EquivalenceRunner()
        diff = self.create_mock_diff()
        
        # Test exact mismatch
        evaluation = runner.run(
            diff=diff,
            source_text="hello world",
            target_text="hello, world!",
            artifact_type=ArtifactType.TEXT,
            methods=[EquivalenceMethod.EXACT]
        )
        
        result = evaluation.results[0]
        assert result.equivalent is False
        assert result.confidence == 0.0
    
    def test_canonical_json_method(self):
        runner = EquivalenceRunner()
        diff = self.create_mock_diff()
        
        # Test JSON canonicalization
        source_json = '{"b": 2, "a": 1}'
        target_json = '{"a": 1, "b": 2}'
        
        evaluation = runner.run(
            diff=diff,
            source_text=source_json,
            target_text=target_json,
            artifact_type=ArtifactType.JSON,
            methods=[EquivalenceMethod.CANONICAL_JSON]
        )
        
        result = evaluation.results[0]
        assert result.method == EquivalenceMethod.CANONICAL_JSON
        assert result.equivalent is True
        assert result.confidence == 0.95
    
    def test_json_parse_error(self):
        runner = EquivalenceRunner()
        diff = self.create_mock_diff()
        
        # Test invalid JSON
        evaluation = runner.run(
            diff=diff,
            source_text='{"invalid": json}',
            target_text='{"valid": "json"}',
            artifact_type=ArtifactType.JSON,
            methods=[EquivalenceMethod.CANONICAL_JSON]
        )
        
        result = evaluation.results[0]
        assert result.equivalent is False
        assert result.confidence == 0.0
        assert "parse error" in result.reasoning.lower()
    
    def test_ast_normalized_method(self):
        runner = EquivalenceRunner()
        diff = self.create_mock_diff()
        
        # Test AST normalization (equivalent code with different formatting)
        source_code = "def hello():\n    return 'world'"
        target_code = "def hello():\n    return 'world'"
        
        evaluation = runner.run(
            diff=diff,
            source_text=source_code,
            target_text=target_code,
            artifact_type=ArtifactType.CODE,
            methods=[EquivalenceMethod.AST_NORMALIZED]
        )
        
        result = evaluation.results[0]
        assert result.method == EquivalenceMethod.AST_NORMALIZED
        assert result.equivalent is True
        assert result.confidence == 0.90
    
    def test_cosine_similarity_method(self):
        embed_client = MockEmbeddingClient()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = EmbeddingCache(cache_dir=temp_dir)
            runner = EquivalenceRunner(embedding_client=embed_client, embedding_cache=cache)
            diff = self.create_mock_diff()
            
            evaluation = runner.run(
                diff=diff,
                source_text="hello world",
                target_text="hello world",  # Same text should have high similarity
                artifact_type=ArtifactType.TEXT,
                methods=[EquivalenceMethod.COSINE_SIMILARITY]
            )
            
            result = evaluation.results[0]
            assert result.method == EquivalenceMethod.COSINE_SIMILARITY
            assert result.similarity_score == 1.0  # Identical text
            assert result.equivalent is True
    
    def test_llm_rubric_judge_method(self):
        # Mock LLM response indicating equivalence
        llm_client = MockLLMClient(responses=[{
            "equivalent": True,
            "confidence": 0.85,
            "reasoning": "Both texts convey the same meaning",
            "violations": []
        }])
        
        runner = EquivalenceRunner(llm_client=llm_client)
        diff = self.create_mock_diff()
        
        evaluation = runner.run(
            diff=diff,
            source_text="Hello world",
            target_text="Hi there, world!",
            artifact_type=ArtifactType.TEXT,
            methods=[EquivalenceMethod.LLM_RUBRIC_JUDGE]
        )
        
        result = evaluation.results[0]
        assert result.method == EquivalenceMethod.LLM_RUBRIC_JUDGE
        assert result.equivalent is True
        assert result.confidence == 0.85
        assert result.cost > 0.0
        assert "meaning" in result.reasoning
    
    def test_llm_parse_error_handling(self):
        # Mock LLM response with invalid JSON
        llm_client = MockLLMClient(responses=[{
            "invalid": "response format"
        }])
        
        runner = EquivalenceRunner(llm_client=llm_client)
        diff = self.create_mock_diff()
        
        evaluation = runner.run(
            diff=diff,
            source_text="test",
            target_text="test",
            artifact_type=ArtifactType.TEXT,
            methods=[EquivalenceMethod.LLM_RUBRIC_JUDGE]
        )
        
        result = evaluation.results[0]
        assert result.equivalent is False  # Fail-closed on parse error
        assert result.confidence == 0.0
        assert "parse error" in result.reasoning.lower()
    
    def test_budget_enforcement(self):
        # Mock expensive LLM client
        llm_client = MockLLMClient()
        llm_client.chat = Mock(return_value={
            "text": '{"equivalent": true, "confidence": 0.8, "reasoning": "test"}',
            "tokens": {"prompt": 100, "completion": 50, "total": 150},
            "latency_ms": 6000,  # Exceeds budget
            "cost_usd": 0.15,    # Exceeds budget
            "model": "mock",
            "provider": "mock"
        })
        
        runner = EquivalenceRunner(
            llm_client=llm_client,
            budgets={"max_cost_usd": 0.05, "max_latency_ms": 3000}
        )
        diff = self.create_mock_diff()
        
        evaluation = runner.run(
            diff=diff,
            source_text="test",
            target_text="test",
            artifact_type=ArtifactType.TEXT,
            methods=[EquivalenceMethod.LLM_RUBRIC_JUDGE]
        )
        
        # Should complete but mark budget exceeded
        assert evaluation.status == EvaluationStatus.COMPLETED
        assert evaluation.metadata.get("budget_exceeded") is True
    
    def test_multiple_methods(self):
        embed_client = MockEmbeddingClient()
        llm_client = MockLLMClient()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = EmbeddingCache(cache_dir=temp_dir)
            runner = EquivalenceRunner(
                llm_client=llm_client,
                embedding_client=embed_client,
                embedding_cache=cache
            )
            diff = self.create_mock_diff()
            
            evaluation = runner.run(
                diff=diff,
                source_text="hello world",
                target_text="hello world",
                artifact_type=ArtifactType.TEXT,
                methods=[
                    EquivalenceMethod.EXACT,
                    EquivalenceMethod.COSINE_SIMILARITY,
                    EquivalenceMethod.LLM_RUBRIC_JUDGE
                ]
            )
            
            assert len(evaluation.results) == 3
            
            # All methods should agree on identical text
            for result in evaluation.results:
                assert result.equivalent is True
    
    def test_method_failure_isolation(self):
        # Mock embedding client that fails
        embed_client = MockEmbeddingClient()
        embed_client.embed = Mock(side_effect=RuntimeError("Embedding service down"))
        
        llm_client = MockLLMClient()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = EmbeddingCache(cache_dir=temp_dir)
            runner = EquivalenceRunner(
                llm_client=llm_client,
                embedding_client=embed_client,
                embedding_cache=cache
            )
            diff = self.create_mock_diff()
            
            evaluation = runner.run(
                diff=diff,
                source_text="test",
                target_text="test",
                artifact_type=ArtifactType.TEXT,
                methods=[
                    EquivalenceMethod.EXACT,
                    EquivalenceMethod.COSINE_SIMILARITY,  # Will fail
                    EquivalenceMethod.LLM_RUBRIC_JUDGE
                ]
            )
            
            # Should have 3 results, with cosine similarity showing failure
            assert len(evaluation.results) == 3
            
            exact_result = next(r for r in evaluation.results if r.method == EquivalenceMethod.EXACT)
            cosine_result = next(r for r in evaluation.results if r.method == EquivalenceMethod.COSINE_SIMILARITY)
            llm_result = next(r for r in evaluation.results if r.method == EquivalenceMethod.LLM_RUBRIC_JUDGE)
            
            assert exact_result.equivalent is True
            assert cosine_result.equivalent is False  # Failed method
            assert "failed" in cosine_result.reasoning.lower()
            assert llm_result.equivalent is True


class TestCosineEmbedding:
    """Test cosine similarity utility."""
    
    def test_identical_vectors(self):
        embed_client = MockEmbeddingClient()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = EmbeddingCache(cache_dir=temp_dir)
            
            similarity = embed_cosine(embed_client, cache, "hello", "hello")
            assert similarity == 1.0
    
    def test_different_vectors(self):
        embed_client = MockEmbeddingClient()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = EmbeddingCache(cache_dir=temp_dir)
            
            similarity = embed_cosine(embed_client, cache, "hello", "goodbye")
            assert 0.0 <= similarity <= 1.0
            assert similarity < 1.0  # Should be less than identical


if __name__ == "__main__":
    pytest.main([__file__])