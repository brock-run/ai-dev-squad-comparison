"""Resolution Engine Metrics

Prometheus metrics for resolution transform operations.
"""

import time
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timezone

try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from .enums import ResolutionActionType


class MockMetric:
    """Mock metric for when Prometheus is not available."""
    def inc(self, *args, **kwargs): pass
    def observe(self, *args, **kwargs): pass
    def set(self, *args, **kwargs): pass
    def labels(self, *args, **kwargs): return self


# Resolution metrics
if PROMETHEUS_AVAILABLE:
    resolution_apply_total = Counter(
        'phase2_resolution_apply_total',
        'Total number of resolution transforms applied',
        ['action', 'status']
    )
    
    resolution_noop_total = Counter(
        'phase2_resolution_noop_total', 
        'Total number of no-op resolution attempts',
        ['action']
    )
    
    resolution_latency_ms = Histogram(
        'phase2_resolution_latency_ms',
        'Resolution transform latency in milliseconds',
        ['action'],
        buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
    )
    
    resolution_error_total = Counter(
        'phase2_resolution_error_total',
        'Total number of resolution transform errors',
        ['action', 'error_type']
    )
    
    resolution_idempotency_violations = Counter(
        'phase2_resolution_idempotency_violations_total',
        'Total number of idempotency violations detected',
        ['action']
    )
    
    resolution_rollback_total = Counter(
        'phase2_resolution_rollback_total',
        'Total number of resolution rollbacks performed',
        ['action', 'reason']
    )
    
    resolution_active_transforms = Gauge(
        'phase2_resolution_active_transforms',
        'Number of currently active resolution transforms'
    )

else:
    # Mock metrics when Prometheus is not available
    resolution_apply_total = MockMetric()
    resolution_noop_total = MockMetric()
    resolution_latency_ms = MockMetric()
    resolution_error_total = MockMetric()
    resolution_idempotency_violations = MockMetric()
    resolution_rollback_total = MockMetric()
    resolution_active_transforms = MockMetric()


class ResolutionMetrics:
    """Metrics collector for resolution operations."""
    
    def __init__(self):
        self.active_count = 0
    
    def track_apply(self, action: ResolutionActionType, success: bool = True, 
                   latency_ms: Optional[float] = None, error_type: Optional[str] = None):
        """Track a resolution apply operation."""
        status = "success" if success else "error"
        resolution_apply_total.labels(action=action.value, status=status).inc()
        
        if latency_ms is not None:
            resolution_latency_ms.labels(action=action.value).observe(latency_ms)
        
        if error_type:
            resolution_error_total.labels(action=action.value, error_type=error_type).inc()
    
    def track_noop(self, action: ResolutionActionType):
        """Track a no-op resolution attempt."""
        resolution_noop_total.labels(action=action.value).inc()
    
    def track_idempotency_violation(self, action: ResolutionActionType):
        """Track an idempotency violation."""
        resolution_idempotency_violations.labels(action=action.value).inc()
    
    def track_rollback(self, action: ResolutionActionType, reason: str):
        """Track a rollback operation."""
        resolution_rollback_total.labels(action=action.value, reason=reason).inc()
    
    def start_transform(self):
        """Mark the start of a transform operation."""
        self.active_count += 1
        resolution_active_transforms.set(self.active_count)
    
    def end_transform(self):
        """Mark the end of a transform operation."""
        self.active_count = max(0, self.active_count - 1)
        resolution_active_transforms.set(self.active_count)


# Global metrics instance
metrics = ResolutionMetrics()


def track_resolution_metrics(action: ResolutionActionType):
    """Decorator to track resolution metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            metrics.start_transform()
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate latency
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                # Check if it's a no-op (no changes)
                if hasattr(result, 'diff') and result.diff.total_changes == 0:
                    metrics.track_noop(action)
                else:
                    metrics.track_apply(action, success=True, latency_ms=latency_ms)
                
                # Check idempotency if available
                if hasattr(result, 'idempotent') and not result.idempotent:
                    metrics.track_idempotency_violation(action)
                
                return result
                
            except Exception as e:
                latency_ms = (time.perf_counter() - start_time) * 1000
                error_type = type(e).__name__
                metrics.track_apply(action, success=False, latency_ms=latency_ms, error_type=error_type)
                raise
            
            finally:
                metrics.end_transform()
        
        return wrapper
    return decorator


def get_metrics_summary() -> Dict[str, Any]:
    """Get a summary of current metrics."""
    return {
        "active_transforms": metrics.active_count,
        "prometheus_available": PROMETHEUS_AVAILABLE,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    # Test metrics
    print("🧪 Testing resolution metrics...")
    
    # Test tracking
    metrics.track_apply(ResolutionActionType.CANONICALIZE_JSON, success=True, latency_ms=150.5)
    metrics.track_noop(ResolutionActionType.NORMALIZE_WHITESPACE)
    metrics.track_idempotency_violation(ResolutionActionType.REWRITE_FORMATTING)
    
    summary = get_metrics_summary()
    print(f"✅ Metrics summary: {summary}")
    
    print("🎉 Resolution metrics working correctly!")