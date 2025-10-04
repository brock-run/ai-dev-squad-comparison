"""
Variance Calculator for Self-Consistency Evaluation

Calculates variance and reliability metrics for multi-run results
following ADR-010 specifications.
"""

import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple

from common.benchmarking import BenchmarkResult


@dataclass
class VarianceMetrics:
    """Variance and reliability metrics for multi-run results."""
    
    # Success rate metrics
    success_rate: float
    success_rate_ci: Tuple[float, float]  # 95% confidence interval
    
    # Timing metrics
    duration_mean: float
    duration_std: float
    duration_cv: float  # coefficient of variation
    duration_ci: Tuple[float, float]
    
    # Token usage metrics
    tokens_mean: Optional[float] = None
    tokens_std: Optional[float] = None
    tokens_cv: Optional[float] = None
    tokens_ci: Optional[Tuple[float, float]] = None
    
    # Quality metrics (if available)
    quality_mean: Optional[float] = None
    quality_std: Optional[float] = None
    quality_cv: Optional[float] = None
    quality_ci: Optional[Tuple[float, float]] = None
    
    # Reliability score (ADR-010 formula)
    reliability_score: float
    reliability_label: str  # "High", "Medium", "Low"
    
    # Outlier information
    outliers: List[int] = None
    outlier_method: str = "tukey"


class VarianceCalculator:
    """Calculates variance and reliability metrics for benchmark results."""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize variance calculator.
        
        Args:
            confidence_level: Confidence level for intervals (default 0.95)
        """
        self.confidence_level = confidence_level
    
    def calculate_variance_metrics(self, results: List[BenchmarkResult]) -> VarianceMetrics:
        """
        Calculate comprehensive variance metrics for multi-run results.
        
        Args:
            results: List of BenchmarkResult objects from multiple runs
            
        Returns:
            VarianceMetrics with all calculated metrics
        """
        if not results:
            return self._empty_metrics()
        
        # Filter successful runs for most metrics
        successful_results = [r for r in results if r.success]
        
        # Calculate success rate
        success_rate = len(successful_results) / len(results)
        success_rate_ci = self._calculate_proportion_ci(len(successful_results), len(results))
        
        if not successful_results:
            return VarianceMetrics(
                success_rate=success_rate,
                success_rate_ci=success_rate_ci,
                duration_mean=0.0,
                duration_std=0.0,
                duration_cv=0.0,
                duration_ci=(0.0, 0.0),
                reliability_score=0.0,
                reliability_label="Low"
            )
        
        # Extract timing data
        durations = self._extract_durations(successful_results)
        duration_stats = self._calculate_stats_with_ci(durations)
        
        # Extract token data
        tokens = self._extract_tokens(successful_results)
        token_stats = self._calculate_stats_with_ci(tokens) if tokens else None
        
        # Extract quality scores
        quality_scores = self._extract_quality_scores(successful_results)
        quality_stats = self._calculate_stats_with_ci(quality_scores) if quality_scores else None
        
        # Detect outliers
        outliers = self._detect_outliers(durations, quality_scores or [])
        
        # Calculate reliability score (ADR-010 formula)
        reliability_score = self._calculate_reliability_score(
            success_rate, duration_stats, token_stats
        )
        reliability_label = self._get_reliability_label(reliability_score)
        
        return VarianceMetrics(
            success_rate=success_rate,
            success_rate_ci=success_rate_ci,
            duration_mean=duration_stats['mean'],
            duration_std=duration_stats['std'],
            duration_cv=duration_stats['cv'],
            duration_ci=duration_stats['ci'],
            tokens_mean=token_stats['mean'] if token_stats else None,
            tokens_std=token_stats['std'] if token_stats else None,
            tokens_cv=token_stats['cv'] if token_stats else None,
            tokens_ci=token_stats['ci'] if token_stats else None,
            quality_mean=quality_stats['mean'] if quality_stats else None,
            quality_std=quality_stats['std'] if quality_stats else None,
            quality_cv=quality_stats['cv'] if quality_stats else None,
            quality_ci=quality_stats['ci'] if quality_stats else None,
            reliability_score=reliability_score,
            reliability_label=reliability_label,
            outliers=outliers
        )
    
    def _extract_durations(self, results: List[BenchmarkResult]) -> List[float]:
        """Extract duration values from results."""
        durations = []
        for result in results:
            # Try multiple possible locations for duration
            duration = None
            
            if hasattr(result, 'duration'):
                duration = result.duration
            elif hasattr(result, 'execution_time'):
                duration = result.execution_time
            elif hasattr(result, 'metadata') and isinstance(result.metadata, dict):
                duration = result.metadata.get('duration') or result.metadata.get('execution_time')
            
            if duration is not None and duration > 0:
                durations.append(float(duration))
        
        return durations
    
    def _extract_tokens(self, results: List[BenchmarkResult]) -> List[float]:
        """Extract token usage values from results."""
        tokens = []
        for result in results:
            # Try multiple possible locations for token count
            token_count = None
            
            if hasattr(result, 'tokens_used'):
                token_count = result.tokens_used
            elif hasattr(result, 'total_tokens'):
                token_count = result.total_tokens
            elif hasattr(result, 'metadata') and isinstance(result.metadata, dict):
                token_count = (result.metadata.get('tokens_used') or 
                             result.metadata.get('total_tokens'))
            
            if token_count is not None and token_count > 0:
                tokens.append(float(token_count))
        
        return tokens
    
    def _extract_quality_scores(self, results: List[BenchmarkResult]) -> List[float]:
        """Extract quality scores from results."""
        scores = []
        for result in results:
            # Try multiple possible locations for quality score
            score = None
            
            if hasattr(result, 'quality_score'):
                score = result.quality_score
            elif hasattr(result, 'verification') and isinstance(result.verification, dict):
                score = result.verification.get('score')
            elif hasattr(result, 'metadata') and isinstance(result.metadata, dict):
                verification = result.metadata.get('verification', {})
                if isinstance(verification, dict):
                    score = verification.get('score')
            
            if score is not None:
                scores.append(float(score))
        
        return scores
    
    def _calculate_stats_with_ci(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistics with confidence interval for a list of values."""
        if not values:
            return {'mean': 0.0, 'std': 0.0, 'cv': 0.0, 'ci': (0.0, 0.0)}
        
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        cv = std / mean if mean > 0 else 0.0
        
        # Calculate confidence interval
        if len(values) > 1:
            ci = self._calculate_mean_ci(values)
        else:
            ci = (mean, mean)
        
        return {
            'mean': mean,
            'std': std,
            'cv': cv,
            'ci': ci
        }
    
    def _calculate_mean_ci(self, values: List[float]) -> Tuple[float, float]:
        """Calculate confidence interval for mean using t-distribution."""
        if len(values) <= 1:
            return (values[0], values[0]) if values else (0.0, 0.0)
        
        import math
        
        try:
            from scipy import stats
            use_scipy = True
        except ImportError:
            # Fallback to normal approximation if scipy not available
            use_scipy = False
        
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        n = len(values)
        
        if use_scipy:
            # t-critical value for given confidence level
            alpha = 1 - self.confidence_level
            t_critical = stats.t.ppf(1 - alpha/2, n - 1)
        else:
            # Normal approximation (z-score) as fallback
            # For 95% confidence level, z ≈ 1.96
            alpha = 1 - self.confidence_level
            if alpha == 0.05:  # 95% confidence
                t_critical = 1.96
            elif alpha == 0.01:  # 99% confidence
                t_critical = 2.58
            else:
                t_critical = 1.96  # Default to 95%
        
        # Margin of error
        margin = t_critical * (std / math.sqrt(n))
        
        return (mean - margin, mean + margin)
    
    def _calculate_proportion_ci(self, successes: int, total: int) -> Tuple[float, float]:
        """Calculate confidence interval for proportion using Wilson score interval."""
        if total == 0:
            return (0.0, 0.0)
        
        import math
        
        try:
            from scipy import stats
            use_scipy = True
        except ImportError:
            use_scipy = False
        
        p = successes / total
        n = total
        
        if use_scipy:
            # Z-critical value for given confidence level
            alpha = 1 - self.confidence_level
            z = stats.norm.ppf(1 - alpha/2)
        else:
            # Normal approximation as fallback
            alpha = 1 - self.confidence_level
            if alpha == 0.05:  # 95% confidence
                z = 1.96
            elif alpha == 0.01:  # 99% confidence
                z = 2.58
            else:
                z = 1.96  # Default to 95%
        
        # Wilson score interval
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2*n)) / denominator
        margin = z * math.sqrt((p*(1-p) + z**2/(4*n)) / n) / denominator
        
        return (max(0.0, center - margin), min(1.0, center + margin))
    
    def _detect_outliers(self, durations: List[float], quality_scores: List[float]) -> List[int]:
        """Detect outliers using Tukey fences method."""
        outliers = []
        
        # Check duration outliers
        if len(durations) >= 3:
            duration_outliers = self._tukey_outliers(durations)
            outliers.extend(duration_outliers)
        
        # Check quality score outliers
        if len(quality_scores) >= 3:
            quality_outliers = self._tukey_outliers(quality_scores)
            outliers.extend(quality_outliers)
        
        return list(set(outliers))  # Remove duplicates
    
    def _tukey_outliers(self, values: List[float]) -> List[int]:
        """Find outliers using Tukey fences method."""
        if len(values) < 3:
            return []
        
        # Calculate quartiles
        q1 = statistics.quantiles(values, n=4)[0]
        q3 = statistics.quantiles(values, n=4)[2]
        iqr = q3 - q1
        
        # Calculate fences
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        
        # Find outlier indices
        outliers = []
        for i, value in enumerate(values):
            if value < lower_fence or value > upper_fence:
                outliers.append(i)
        
        return outliers
    
    def _calculate_reliability_score(self, 
                                   success_rate: float,
                                   duration_stats: Dict[str, float],
                                   token_stats: Optional[Dict[str, float]]) -> float:
        """
        Calculate reliability score using ADR-010 formula.
        
        Formula: 0.6*success_rate + 0.2*(1 - clamp(stdev_time,0,1)) + 0.2*(1 - clamp(stdev_tokens,0,1))
        """
        # Normalize standard deviations using z-score approach
        stdev_time_norm = self._clamp(duration_stats['cv'], 0.0, 1.0) if duration_stats['mean'] > 0 else 0.0
        
        if token_stats and token_stats['mean'] > 0:
            stdev_tokens_norm = self._clamp(token_stats['cv'], 0.0, 1.0)
        else:
            stdev_tokens_norm = 0.0  # No token variance penalty if no token data
        
        # Apply ADR-010 formula
        reliability_score = (
            0.6 * success_rate +
            0.2 * (1 - stdev_time_norm) +
            0.2 * (1 - stdev_tokens_norm)
        )
        
        return self._clamp(reliability_score, 0.0, 1.0)
    
    def _get_reliability_label(self, score: float) -> str:
        """Get reliability label based on score (ADR-010)."""
        if score >= 0.8:
            return "High"
        elif score >= 0.6:
            return "Medium"
        else:
            return "Low"
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max."""
        return max(min_val, min(max_val, value))
    
    def _empty_metrics(self) -> VarianceMetrics:
        """Return empty metrics for edge cases."""
        return VarianceMetrics(
            success_rate=0.0,
            success_rate_ci=(0.0, 0.0),
            duration_mean=0.0,
            duration_std=0.0,
            duration_cv=0.0,
            duration_ci=(0.0, 0.0),
            reliability_score=0.0,
            reliability_label="Low"
        )