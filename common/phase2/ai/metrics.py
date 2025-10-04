"""AI Judge Metrics Collection

Provides Prometheus metrics for AI judge operations.
"""

import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback implementations
    class Counter:
        def __init__(self, *args, **kwargs):
            self._value = 0
        def inc(self, amount=1):
            self._value += amount
        def labels(self, **kwargs):
            return self
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            self._observations = []
        def observe(self, value):
            self._observations.append(value)
        def labels(self, **kwargs):
            return self
        def time(self):
            return _HistogramTimer(self)
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            self._value = 0
        def set(self, value):
            self._value = value
        def labels(self, **kwargs):
            return self

from ..enums import EquivalenceMethod


class _HistogramTimer:
    """Timer context manager for histogram observations."""
    
    def __init__(self, histogram):
        self.histogram = histogram
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = (time.perf_counter() - self.start_time) * 1000  # Convert to ms
            self.histogram.observe(duration)


# Judge evaluation metrics
judge_evaluations_total = Counter(
    'phase2_judge_evaluations_total',
    'Total number of judge evaluations',
    ['method', 'artifact_type', 'status']
)

judge_cost_usd_sum = Counter(
    'phase2_judge_cost_usd_sum',
    'Total cost of judge evaluations in USD',
    ['method', 'provider']
)

judge_latency_ms = Histogram(
    'phase2_judge_latency_ms',
    'Judge evaluation latency in milliseconds',
    ['method', 'artifact_type'],
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
)

judge_budget_downgrade_total = Counter(
    'phase2_judge_budget_downgrade_total',
    'Total number of budget-related downgrades',
    ['reason']  # 'cost_exceeded', 'latency_exceeded', 'token_exceeded'
)

judge_confidence_score = Histogram(
    'phase2_judge_confidence_score',
    'Judge confidence scores',
    ['method', 'artifact_type', 'equivalent'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

judge_similarity_score = Histogram(
    'phase2_judge_similarity_score',
    'Judge similarity scores',
    ['method', 'artifact_type'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

judge_kappa_overall = Gauge(
    'phase2_judge_kappa_overall',
    'Overall Cohen\'s kappa for judge agreement'
)

judge_false_positive_rate = Gauge(
    'phase2_judge_false_positive_rate',
    'False positive rate by method',
    ['method', 'artifact_type']
)

judge_cache_hit_rate = Gauge(
    'phase2_judge_cache_hit_rate',
    'Embedding cache hit rate',
    ['cache_type']  # 'memory', 'disk'
)


class JudgeMetrics:
    """Metrics collector for AI judge operations."""
    
    def __init__(self):
        self.enabled = PROMETHEUS_AVAILABLE
    
    @contextmanager
    def time_evaluation(self, method: EquivalenceMethod, artifact_type: str):
        """Time a judge evaluation."""
        if self.enabled:
            with judge_latency_ms.labels(method=method.value, artifact_type=artifact_type).time():
                yield
        else:
            yield
    
    def record_evaluation(self, method: EquivalenceMethod, artifact_type: str, 
                         status: str, equivalent: bool, confidence: float, 
                         similarity_score: Optional[float] = None,
                         cost: float = 0.0, provider: str = "unknown"):
        """Record a judge evaluation result."""
        if self.enabled:
            # Count evaluation
            judge_evaluations_total.labels(
                method=method.value,
                artifact_type=artifact_type,
                status=status
            ).inc()
            
            # Record cost
            if cost > 0:
                judge_cost_usd_sum.labels(
                    method=method.value,
                    provider=provider
                ).inc(cost)
            
            # Record confidence
            judge_confidence_score.labels(
                method=method.value,
                artifact_type=artifact_type,
                equivalent=str(equivalent).lower()
            ).observe(confidence)
            
            # Record similarity if available
            if similarity_score is not None:
                judge_similarity_score.labels(
                    method=method.value,
                    artifact_type=artifact_type
                ).observe(similarity_score)
    
    def record_budget_downgrade(self, reason: str):
        """Record a budget-related downgrade."""
        if self.enabled:
            judge_budget_downgrade_total.labels(reason=reason).inc()
    
    def update_kappa(self, kappa_value: float):
        """Update overall kappa metric."""
        if self.enabled:
            judge_kappa_overall.set(kappa_value)
    
    def update_false_positive_rate(self, method: EquivalenceMethod, 
                                  artifact_type: str, fp_rate: float):
        """Update false positive rate for method."""
        if self.enabled:
            judge_false_positive_rate.labels(
                method=method.value,
                artifact_type=artifact_type
            ).set(fp_rate)
    
    def update_cache_hit_rate(self, cache_type: str, hit_rate: float):
        """Update cache hit rate."""
        if self.enabled:
            judge_cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics stats (for non-Prometheus environments)."""
        if self.enabled:
            return {'prometheus_enabled': True}
        
        # Return basic stats from fallback counters
        return {
            'prometheus_enabled': False,
            'evaluation_count': getattr(judge_evaluations_total, '_value', 0),
            'total_cost': getattr(judge_cost_usd_sum, '_value', 0),
            'downgrade_count': getattr(judge_budget_downgrade_total, '_value', 0)
        }


# Global metrics instance
judge_metrics = JudgeMetrics()


def compute_kappa_from_results(results: list) -> float:
    """Compute Cohen's kappa from evaluation results.
    
    Args:
        results: List of evaluation results with ground truth labels
        
    Returns:
        Cohen's kappa coefficient
    """
    if len(results) < 2:
        return 0.0
    
    # Extract predictions and ground truth
    predictions = []
    ground_truth = []
    
    for result in results:
        if result.get("ground_truth") is None:
            continue  # Skip items without ground truth
        
        # Use consensus of methods or primary method
        evaluation = result.get("evaluation", {})
        method_results = evaluation.get("results", [])
        
        if not method_results:
            continue
        
        # Simple consensus: majority vote or first method
        equivalent_votes = sum(1 for r in method_results if r.get("equivalent", False))
        predicted_equivalent = equivalent_votes > len(method_results) / 2
        
        predictions.append(predicted_equivalent)
        ground_truth.append(result["ground_truth"])
    
    if len(predictions) < 2:
        return 0.0
    
    # Compute Cohen's kappa
    return _compute_cohens_kappa(predictions, ground_truth)


def _compute_cohens_kappa(predictions: list, ground_truth: list) -> float:
    """Compute Cohen's kappa coefficient."""
    if len(predictions) != len(ground_truth):
        return 0.0
    
    n = len(predictions)
    if n == 0:
        return 0.0
    
    # Convert to binary (True/False)
    pred_binary = [bool(p) for p in predictions]
    truth_binary = [bool(t) for t in ground_truth]
    
    # Compute agreement matrix
    tp = sum(1 for p, t in zip(pred_binary, truth_binary) if p and t)
    tn = sum(1 for p, t in zip(pred_binary, truth_binary) if not p and not t)
    fp = sum(1 for p, t in zip(pred_binary, truth_binary) if p and not t)
    fn = sum(1 for p, t in zip(pred_binary, truth_binary) if not p and t)
    
    # Observed agreement
    po = (tp + tn) / n
    
    # Expected agreement by chance
    pred_pos = sum(pred_binary) / n
    pred_neg = 1 - pred_pos
    truth_pos = sum(truth_binary) / n
    truth_neg = 1 - truth_pos
    
    pe = (pred_pos * truth_pos) + (pred_neg * truth_neg)
    
    # Cohen's kappa
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    
    kappa = (po - pe) / (1 - pe)
    return kappa


def compute_false_positive_rate(results: list, method: str) -> float:
    """Compute false positive rate for a specific method."""
    method_results = []
    
    for result in results:
        if result.get("ground_truth") is None:
            continue
        
        evaluation = result.get("evaluation", {})
        for method_result in evaluation.get("results", []):
            if method_result.get("method") == method:
                method_results.append({
                    "predicted": method_result.get("equivalent", False),
                    "actual": result["ground_truth"]
                })
                break
    
    if not method_results:
        return 0.0
    
    # Count false positives and true negatives
    fp = sum(1 for r in method_results if r["predicted"] and not r["actual"])
    tn = sum(1 for r in method_results if not r["predicted"] and not r["actual"])
    
    if fp + tn == 0:
        return 0.0
    
    return fp / (fp + tn)


if __name__ == "__main__":
    # Test metrics collection
    print("🧪 Testing judge metrics...")
    
    metrics = JudgeMetrics()
    
    # Test evaluation recording
    from ..enums import EquivalenceMethod
    
    metrics.record_evaluation(
        method=EquivalenceMethod.LLM_RUBRIC_JUDGE,
        artifact_type="text",
        status="completed",
        equivalent=True,
        confidence=0.85,
        similarity_score=0.92,
        cost=0.001,
        provider="openai"
    )
    
    # Test budget downgrade
    metrics.record_budget_downgrade("cost_exceeded")
    
    # Test kappa computation
    mock_results = [
        {"ground_truth": True, "evaluation": {"results": [{"method": "exact", "equivalent": True}]}},
        {"ground_truth": False, "evaluation": {"results": [{"method": "exact", "equivalent": False}]}},
        {"ground_truth": True, "evaluation": {"results": [{"method": "exact", "equivalent": False}]}},  # FN
    ]
    
    kappa = compute_kappa_from_results(mock_results)
    print(f"✅ Computed kappa: {kappa:.3f}")
    
    # Test FP rate
    fp_rate = compute_false_positive_rate(mock_results, "exact")
    print(f"✅ False positive rate: {fp_rate:.3f}")
    
    stats = metrics.get_stats()
    print(f"✅ Metrics stats: {stats}")
    
    print("\n🎉 Judge metrics working correctly!")