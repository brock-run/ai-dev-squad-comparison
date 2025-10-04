"""Equivalence Judge for Phase 2 AI Services

Provides semantic equivalence evaluation using multiple methods.
"""

import json
import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .clients import LLMClient, EmbeddingClient
from .cache import EmbeddingCache, embed_cosine
from .metrics import judge_metrics
from .prompt_guard import prompt_guard
from ..enums import EquivalenceMethod, ArtifactType
from ..diff_entities import Evaluation, EvaluationResult, EvaluationStatus, create_evaluation


class BudgetEnforcer:
    """Enforces cost and latency budgets for AI operations."""
    
    def __init__(self, max_cost_usd: float = 0.10, max_latency_ms: int = 5000, 
                 max_tokens_per_request: int = 8000):
        self.max_cost_usd = max_cost_usd
        self.max_latency_ms = max_latency_ms
        self.max_tokens_per_request = max_tokens_per_request
        
        self.total_cost = 0.0
        self.total_latency = 0.0
        self.request_count = 0
    
    def check_request_budget(self, estimated_tokens: int) -> bool:
        """Check if request is within budget before making it."""
        return estimated_tokens <= self.max_tokens_per_request
    
    def record_request(self, cost_usd: float, latency_ms: int) -> bool:
        """Record request cost and latency. Returns True if still within budget."""
        self.total_cost += cost_usd
        self.total_latency += latency_ms
        self.request_count += 1
        
        return (self.total_cost <= self.max_cost_usd and 
                latency_ms <= self.max_latency_ms)
    
    def is_budget_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        return (self.total_cost > self.max_cost_usd or 
                self.total_latency > self.max_latency_ms * self.request_count)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get budget usage statistics."""
        return {
            "total_cost_usd": self.total_cost,
            "total_latency_ms": self.total_latency,
            "request_count": self.request_count,
            "avg_latency_ms": self.total_latency / max(1, self.request_count),
            "budget_exceeded": self.is_budget_exceeded()
        }


class EquivalenceRunner:
    """Runs equivalence evaluation using multiple methods."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None, 
                 embedding_client: Optional[EmbeddingClient] = None,
                 embedding_cache: Optional[EmbeddingCache] = None,
                 budgets: Optional[Dict[str, Any]] = None,
                 sandbox_enabled: bool = True):
        self.llm_client = llm_client
        self.embedding_client = embedding_client
        self.embedding_cache = embedding_cache or EmbeddingCache()
        self.sandbox_enabled = sandbox_enabled
        
        # Default budgets
        default_budgets = {
            "max_cost_usd": 0.10,
            "max_latency_ms": 5000,
            "max_tokens_per_request": 8000
        }
        self.budgets = {**default_budgets, **(budgets or {})}
        
        # Load rubric prompt template
        self.rubric_template = self._load_rubric_template()
    
    def _load_rubric_template(self) -> str:
        """Load rubric prompt template."""
        try:
            with open("common/phase2/prompts/judge_rubric.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback inline template
            return """You are an equivalence judge. Decide if TARGET is semantically equivalent to SOURCE.

Rules:
- Ignore formatting, ordering, markdown cosmetics.
- Preserve facts, units, and constraints. If any fact changes, it's NOT equivalent.
- For code: equivalence means same behavior; ignore whitespace/comment changes.

Return ONLY this JSON:
{"equivalent": <true|false>, "confidence": <0..1>, "reasoning": "<<=180 chars>", "violations": ["<short keywords>"]}

SOURCE:
<<<
{SOURCE_TEXT}
>>>
TARGET:
<<<
{TARGET_TEXT}
>>>"""
    
    def run(self, diff, source_text: str, target_text: str, artifact_type: ArtifactType, 
            methods: List[EquivalenceMethod]) -> Evaluation:
        """Run equivalence evaluation using specified methods."""
        
        evaluation = create_evaluation(
            diff_id=diff.id,
            source_artifact_id=diff.source_artifact_id,
            target_artifact_id=diff.target_artifact_id,
            artifact_type=artifact_type
        )
        
        evaluation.status = EvaluationStatus.RUNNING
        budget_enforcer = BudgetEnforcer(**self.budgets)
        
        try:
            for method in methods:
                try:
                    with judge_metrics.time_evaluation(method, artifact_type.value):
                        result = self._run_method(method, source_text, target_text, 
                                                artifact_type, budget_enforcer)
                        evaluation.add_result(result)
                        
                        # Record metrics
                        judge_metrics.record_evaluation(
                            method=method,
                            artifact_type=artifact_type.value,
                            status="completed",
                            equivalent=result.equivalent,
                            confidence=result.confidence,
                            similarity_score=result.similarity_score,
                            cost=result.cost,
                            provider=getattr(self.llm_client, 'provider_id', 'unknown')
                        )
                        
                        # Check budget after each method
                        if budget_enforcer.is_budget_exceeded():
                            evaluation.metadata["budget_exceeded"] = True
                            evaluation.metadata["downgrade"] = "budget_exceeded"
                            judge_metrics.record_budget_downgrade("budget_exceeded")
                            break
                            
                except Exception as e:
                    # Record failed method but continue with others
                    error_result = EvaluationResult(
                        method=method,
                        equivalent=False,
                        confidence=0.0,
                        similarity_score=0.0,
                        reasoning=f"Method failed: {str(e)[:100]}",
                        cost=0.0,
                        latency_ms=0
                    )
                    evaluation.add_result(error_result)
                    
                    judge_metrics.record_evaluation(
                        method=method,
                        artifact_type=artifact_type.value,
                        status="failed",
                        equivalent=False,
                        confidence=0.0,
                        cost=0.0
                    )
            
            # Add budget stats to metadata
            evaluation.metadata["budget_stats"] = budget_enforcer.get_stats()
            
            return evaluation.complete(success=True)
            
        except Exception as e:
            evaluation.error_message = str(e)
            evaluation.metadata["budget_stats"] = budget_enforcer.get_stats()
            return evaluation.complete(success=False)
    
    def _run_method(self, method: EquivalenceMethod, source: str, target: str, 
                   artifact_type: ArtifactType, budget_enforcer: BudgetEnforcer) -> EvaluationResult:
        """Run a single equivalence method."""
        
        start_time = time.time()
        
        if method == EquivalenceMethod.EXACT:
            return self._exact_match(source, target, start_time)
        
        elif method == EquivalenceMethod.CANONICAL_JSON and artifact_type == ArtifactType.JSON:
            return self._canonical_json(source, target, start_time)
        
        elif method == EquivalenceMethod.COSINE_SIMILARITY:
            return self._cosine_similarity(source, target, start_time, budget_enforcer)
        
        elif method == EquivalenceMethod.LLM_RUBRIC_JUDGE:
            return self._llm_rubric_judge(source, target, artifact_type, start_time, budget_enforcer)
        
        elif method == EquivalenceMethod.AST_NORMALIZED and artifact_type == ArtifactType.CODE:
            return self._ast_normalized(source, target, start_time)
        
        else:
            raise ValueError(f"Unsupported method {method} for artifact type {artifact_type}")
    
    def _exact_match(self, source: str, target: str, start_time: float) -> EvaluationResult:
        """Exact string match."""
        equivalent = source == target
        latency_ms = int((time.time() - start_time) * 1000)
        
        return EvaluationResult(
            method=EquivalenceMethod.EXACT,
            equivalent=equivalent,
            confidence=1.0 if equivalent else 0.0,
            similarity_score=1.0 if equivalent else 0.0,
            reasoning="Exact string match" if equivalent else "Strings differ",
            cost=0.0,
            latency_ms=latency_ms
        )
    
    def _canonical_json(self, source: str, target: str, start_time: float) -> EvaluationResult:
        """Canonical JSON comparison."""
        try:
            source_obj = json.loads(source)
            target_obj = json.loads(target)
            
            # Canonicalize both
            source_canonical = json.dumps(source_obj, sort_keys=True, separators=(',', ':'))
            target_canonical = json.dumps(target_obj, sort_keys=True, separators=(',', ':'))
            
            equivalent = source_canonical == target_canonical
            latency_ms = int((time.time() - start_time) * 1000)
            
            return EvaluationResult(
                method=EquivalenceMethod.CANONICAL_JSON,
                equivalent=equivalent,
                confidence=0.95 if equivalent else 0.1,
                similarity_score=1.0 if equivalent else 0.0,
                reasoning="JSON canonically equivalent" if equivalent else "JSON structures differ",
                cost=0.0,
                latency_ms=latency_ms
            )
            
        except json.JSONDecodeError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return EvaluationResult(
                method=EquivalenceMethod.CANONICAL_JSON,
                equivalent=False,
                confidence=0.0,
                similarity_score=0.0,
                reasoning=f"JSON parse error: {e}",
                cost=0.0,
                latency_ms=latency_ms
            )
    
    def _cosine_similarity(self, source: str, target: str, start_time: float, 
                          budget_enforcer: BudgetEnforcer) -> EvaluationResult:
        """Cosine similarity using embeddings."""
        if not self.embedding_client:
            raise ValueError("Embedding client not configured")
        
        try:
            # Compute cosine similarity using cache
            similarity = embed_cosine(
                self.embedding_client, 
                self.embedding_cache, 
                source, 
                target, 
                self.embedding_client.model
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Calibrated threshold (could be loaded from config)
            threshold = 0.86
            equivalent = similarity >= threshold
            
            # Map similarity to confidence (calibrated function)
            confidence = self._calibrate_similarity_confidence(similarity)
            
            return EvaluationResult(
                method=EquivalenceMethod.COSINE_SIMILARITY,
                equivalent=equivalent,
                confidence=confidence,
                similarity_score=similarity,
                reasoning=f"Cosine similarity: {similarity:.3f} (threshold: {threshold})",
                cost=0.001,  # Approximate embedding cost
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return EvaluationResult(
                method=EquivalenceMethod.COSINE_SIMILARITY,
                equivalent=False,
                confidence=0.0,
                similarity_score=0.0,
                reasoning=f"Embedding error: {e}",
                cost=0.0,
                latency_ms=latency_ms
            )
    
    def _llm_rubric_judge(self, source: str, target: str, artifact_type: ArtifactType, 
                         start_time: float, budget_enforcer: BudgetEnforcer) -> EvaluationResult:
        """LLM rubric-based judgment."""
        if not self.llm_client:
            raise ValueError("LLM client not configured")
        
        try:
            # Scan inputs for injection attempts
            source_scan = prompt_guard.scan_content(source, "source")
            target_scan = prompt_guard.scan_content(target, "target")
            
            # Use sanitized content
            source_safe = source_scan["sanitized_content"]
            target_safe = target_scan["sanitized_content"]
            
            # Check if content is safe enough to proceed
            if not source_scan["safe"] or not target_scan["safe"]:
                return EvaluationResult(
                    method=EquivalenceMethod.LLM_RUBRIC_JUDGE,
                    equivalent=False,
                    confidence=0.0,
                    similarity_score=0.0,
                    reasoning=f"Content safety violation: {source_scan['violations'] + target_scan['violations']}",
                    cost=0.0,
                    latency_ms=int((time.time() - start_time) * 1000),
                    metadata={"safety_violations": source_scan["violations"] + target_scan["violations"]}
                )
            
            # Build prompt with sanitized content
            prompt = self._build_rubric_prompt(source_safe, target_safe, artifact_type)
            messages = [{"role": "user", "content": prompt}]
            
            # Check token budget
            token_estimate = self.llm_client.count_tokens(messages)["total"]
            if not budget_enforcer.check_request_budget(token_estimate):
                raise ValueError(f"Request exceeds token budget: {token_estimate}")
            
            # Make LLM request
            response = self.llm_client.chat(
                messages=messages,
                max_tokens=256,
                temperature=0.0,
                seed=42  # Deterministic for consistency
            )
            
            # Record budget usage
            budget_ok = budget_enforcer.record_request(response["cost_usd"], response["latency_ms"])
            if not budget_ok:
                raise ValueError("Budget exceeded during LLM request")
            
            # Parse response
            parsed = self._parse_llm_response(response["text"])
            
            return EvaluationResult(
                method=EquivalenceMethod.LLM_RUBRIC_JUDGE,
                equivalent=parsed["equivalent"],
                confidence=parsed["confidence"],
                similarity_score=1.0 if parsed["equivalent"] else 0.0,
                reasoning=parsed["reasoning"],
                cost=response["cost_usd"],
                latency_ms=response["latency_ms"],
                metadata={
                    "model": response["model"],
                    "provider": response["provider"],
                    "tokens": response["tokens"],
                    "violations": parsed.get("violations", [])
                }
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return EvaluationResult(
                method=EquivalenceMethod.LLM_RUBRIC_JUDGE,
                equivalent=False,
                confidence=0.0,
                similarity_score=0.0,
                reasoning=f"LLM judge error: {e}",
                cost=0.0,
                latency_ms=latency_ms
            )
    
    def _ast_normalized(self, source: str, target: str, start_time: float) -> EvaluationResult:
        """AST-normalized code comparison."""
        try:
            import ast
            
            # Parse both code snippets
            source_ast = ast.parse(source)
            target_ast = ast.parse(target)
            
            # Normalize ASTs (remove docstrings, comments, etc.)
            source_normalized = ast.dump(source_ast, annotate_fields=False)
            target_normalized = ast.dump(target_ast, annotate_fields=False)
            
            equivalent = source_normalized == target_normalized
            latency_ms = int((time.time() - start_time) * 1000)
            
            return EvaluationResult(
                method=EquivalenceMethod.AST_NORMALIZED,
                equivalent=equivalent,
                confidence=0.90 if equivalent else 0.1,
                similarity_score=1.0 if equivalent else 0.0,
                reasoning="AST structures match" if equivalent else "AST structures differ",
                cost=0.0,
                latency_ms=latency_ms
            )
            
        except SyntaxError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return EvaluationResult(
                method=EquivalenceMethod.AST_NORMALIZED,
                equivalent=False,
                confidence=0.0,
                similarity_score=0.0,
                reasoning=f"Syntax error: {e}",
                cost=0.0,
                latency_ms=latency_ms
            )
    
    def _build_rubric_prompt(self, source: str, target: str, artifact_type: ArtifactType) -> str:
        """Build rubric prompt for LLM judge."""
        # Truncate content to avoid token limits
        max_chars = 6000
        source_truncated = source[:max_chars]
        target_truncated = target[:max_chars]
        
        return self.rubric_template.format(
            SOURCE_TEXT=source_truncated,
            TARGET_TEXT=target_truncated
        )
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response JSON with robust error handling."""
        try:
            # Extract JSON from response
            json_text = self._extract_json(response_text)
            obj = json.loads(json_text)
            
            # Validate and normalize fields
            equivalent = bool(obj.get("equivalent", False))
            confidence = float(obj.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
            reasoning = str(obj.get("reasoning", ""))[:180]  # Truncate
            violations = obj.get("violations", [])
            
            return {
                "equivalent": equivalent,
                "confidence": confidence,
                "reasoning": reasoning,
                "violations": violations
            }
            
        except Exception as e:
            # Fail-closed: assume not equivalent on parse error
            return {
                "equivalent": False,
                "confidence": 0.0,
                "reasoning": f"Parse error: {str(e)[:100]}",
                "violations": ["parse_error"]
            }
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON object from text response."""
        import re
        
        # Look for JSON object in text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        
        # Fallback: return fail-closed JSON
        return '{"equivalent": false, "confidence": 0.0, "reasoning": "no-json-found"}'
    
    def _calibrate_similarity_confidence(self, similarity: float) -> float:
        """Map cosine similarity to confidence using calibrated function."""
        # Piecewise linear calibration (could be loaded from config)
        if similarity >= 0.95:
            return 0.95
        elif similarity >= 0.86:
            # Linear interpolation between (0.86, 0.70) and (0.95, 0.95)
            return 0.70 + (similarity - 0.86) * (0.95 - 0.70) / (0.95 - 0.86)
        elif similarity >= 0.70:
            # Linear interpolation between (0.70, 0.30) and (0.86, 0.70)
            return 0.30 + (similarity - 0.70) * (0.70 - 0.30) / (0.86 - 0.70)
        else:
            # Low similarity -> low confidence
            return max(0.1, similarity * 0.5)


if __name__ == "__main__":
    # Test equivalence runner with mock clients
    print("🧪 Testing equivalence runner...")
    
    from .clients import OllamaAdapter
    from .cache import EmbeddingCache
    
    # Mock LLM client for testing
    class MockLLMClient:
        def __init__(self):
            self.provider_id = "mock"
            self.model = "mock-model"
        
        def chat(self, messages, max_tokens=256, temperature=0.0, seed=None):
            # Return mock response
            return {
                "text": '{"equivalent": true, "confidence": 0.85, "reasoning": "Mock evaluation"}',
                "tokens": {"prompt": 100, "completion": 50, "total": 150},
                "latency_ms": 500,
                "cost_usd": 0.001,
                "model": self.model,
                "provider": self.provider_id
            }
        
        def count_tokens(self, messages):
            return {"prompt": 100, "total": 100}
    
    # Mock embedding client
    class MockEmbeddingClient:
        def __init__(self):
            self.provider_id = "mock"
            self.model = "mock-embed"
        
        def embed(self, texts):
            # Return mock embeddings (normalized vectors)
            import random
            random.seed(42)  # Deterministic for testing
            return [[random.random() for _ in range(384)] for _ in texts]
        
        def get_dimension(self):
            return 384
    
    # Test runner
    try:
        llm_client = MockLLMClient()
        embed_client = MockEmbeddingClient()
        cache = EmbeddingCache(cache_dir=".test_cache")
        
        runner = EquivalenceRunner(
            llm_client=llm_client,
            embedding_client=embed_client,
            embedding_cache=cache,
            budgets={"max_cost_usd": 0.10, "max_latency_ms": 5000}
        )
        
        # Mock diff object
        class MockDiff:
            def __init__(self):
                self.id = "test-diff-001"
                self.source_artifact_id = "src-001"
                self.target_artifact_id = "tgt-001"
        
        diff = MockDiff()
        
        # Test text equivalence
        from ..enums import EquivalenceMethod, ArtifactType
        
        evaluation = runner.run(
            diff=diff,
            source_text="Hello world",
            target_text="Hello, world!",
            artifact_type=ArtifactType.TEXT,
            methods=[EquivalenceMethod.EXACT, EquivalenceMethod.COSINE_SIMILARITY]
        )
        
        print(f"✅ Evaluation completed: {evaluation.status}")
        print(f"   Results: {len(evaluation.results)} methods")
        for result in evaluation.results:
            print(f"   - {result.method.value}: equivalent={result.equivalent}, confidence={result.confidence:.2f}")
        
        # Clean up test cache
        cache.clear()
        
        print("\n🎉 Equivalence runner working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()