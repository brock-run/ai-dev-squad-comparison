"""
Consensus Analyzer for Self-Consistency Evaluation

Implements majority voting and quality-weighted consensus analysis
following ADR-010 specifications.
"""

import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple

from common.benchmarking import BenchmarkResult


@dataclass
class ConsensusResult:
    """Result of consensus analysis."""
    
    # Consensus decision
    consensus_pass: bool
    confidence: float  # 0.0 to 1.0
    
    # Vote breakdown
    total_votes: int
    pass_votes: int
    fail_votes: int
    
    # Quality weighting (if used)
    weighted_score: Optional[float] = None
    quality_weights_used: bool = False
    
    # Individual results
    individual_results: List[Dict[str, Any]] = None
    
    # Metadata
    strategy: str = "majority"  # "majority" | "weighted"
    outliers_excluded: List[int] = None


class ConsensusAnalyzer:
    """Analyzes multiple benchmark results to determine consensus."""
    
    def __init__(self, strategy: str = "majority", exclude_outliers: bool = False):
        """
        Initialize consensus analyzer.
        
        Args:
            strategy: "majority" or "weighted"
            exclude_outliers: Whether to exclude outliers from consensus
        """
        self.strategy = strategy
        self.exclude_outliers = exclude_outliers
    
    def analyze_consensus(self, results: List[BenchmarkResult]) -> ConsensusResult:
        """
        Analyze consensus from multiple benchmark results.
        
        Args:
            results: List of BenchmarkResult objects from multiple runs
            
        Returns:
            ConsensusResult with consensus decision and analysis
        """
        if not results:
            return ConsensusResult(
                consensus_pass=False,
                confidence=0.0,
                total_votes=0,
                pass_votes=0,
                fail_votes=0,
                strategy=self.strategy
            )
        
        # Filter out failed runs (execution failures, not verification failures)
        valid_results = [r for r in results if r.success]
        
        if not valid_results:
            return ConsensusResult(
                consensus_pass=False,
                confidence=0.0,
                total_votes=len(results),
                pass_votes=0,
                fail_votes=len(results),
                strategy=self.strategy
            )
        
        # Extract verification results and quality scores
        individual_data = []
        for i, result in enumerate(valid_results):
            verified_pass = self._extract_verification_result(result)
            quality_score = self._extract_quality_score(result)
            
            individual_data.append({
                'index': i,
                'verified_pass': verified_pass,
                'quality_score': quality_score,
                'result': result
            })
        
        # Exclude outliers if requested
        outliers_excluded = []
        if self.exclude_outliers and len(individual_data) >= 3:
            individual_data, outliers_excluded = self._exclude_outliers(individual_data)
        
        # Perform consensus analysis
        if self.strategy == "weighted" and any(d['quality_score'] is not None for d in individual_data):
            return self._weighted_consensus(individual_data, outliers_excluded)
        else:
            return self._majority_consensus(individual_data, outliers_excluded)
    
    def _extract_verification_result(self, result: BenchmarkResult) -> bool:
        """Extract verification pass/fail from benchmark result."""
        # Check various possible locations for verification result
        if hasattr(result, 'verified_pass'):
            return result.verified_pass
        
        if hasattr(result, 'verification') and isinstance(result.verification, dict):
            return result.verification.get('pass', False)
        
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            verification = result.metadata.get('verification', {})
            if isinstance(verification, dict):
                return verification.get('pass', False)
            elif isinstance(verification, bool):
                return verification
        
        # Fallback to overall success if no specific verification result
        return getattr(result, 'success', False)
    
    def _extract_quality_score(self, result: BenchmarkResult) -> Optional[float]:
        """Extract quality score from benchmark result (0.0 to 1.0)."""
        # Check various possible locations for quality score
        if hasattr(result, 'quality_score'):
            return result.quality_score
        
        if hasattr(result, 'verification') and isinstance(result.verification, dict):
            score = result.verification.get('score')
            if score is not None:
                return float(score)
        
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            verification = result.metadata.get('verification', {})
            if isinstance(verification, dict):
                score = verification.get('score')
                if score is not None:
                    return float(score)
        
        return None
    
    def _majority_consensus(self, individual_data: List[Dict[str, Any]], 
                          outliers_excluded: List[int]) -> ConsensusResult:
        """Perform majority vote consensus analysis."""
        pass_votes = sum(1 for d in individual_data if d['verified_pass'])
        fail_votes = len(individual_data) - pass_votes
        total_votes = len(individual_data)
        
        consensus_pass = pass_votes > fail_votes
        confidence = max(pass_votes, fail_votes) / total_votes if total_votes > 0 else 0.0
        
        return ConsensusResult(
            consensus_pass=consensus_pass,
            confidence=confidence,
            total_votes=total_votes,
            pass_votes=pass_votes,
            fail_votes=fail_votes,
            individual_results=individual_data,
            strategy="majority",
            outliers_excluded=outliers_excluded
        )
    
    def _weighted_consensus(self, individual_data: List[Dict[str, Any]],
                          outliers_excluded: List[int]) -> ConsensusResult:
        """Perform quality-weighted consensus analysis."""
        total_weight = 0.0
        weighted_pass_score = 0.0
        
        pass_votes = 0
        fail_votes = 0
        
        for data in individual_data:
            verified_pass = data['verified_pass']
            quality_score = data['quality_score']
            
            # Use quality score as weight, default to 1.0 if not available
            weight = quality_score if quality_score is not None else 1.0
            total_weight += weight
            
            if verified_pass:
                weighted_pass_score += weight
                pass_votes += 1
            else:
                fail_votes += 1
        
        # Calculate weighted consensus
        weighted_score = weighted_pass_score / total_weight if total_weight > 0 else 0.0
        consensus_pass = weighted_score > 0.5
        confidence = abs(weighted_score - 0.5) * 2  # Convert to 0-1 confidence
        
        return ConsensusResult(
            consensus_pass=consensus_pass,
            confidence=confidence,
            total_votes=len(individual_data),
            pass_votes=pass_votes,
            fail_votes=fail_votes,
            weighted_score=weighted_score,
            quality_weights_used=True,
            individual_results=individual_data,
            strategy="weighted",
            outliers_excluded=outliers_excluded
        )
    
    def _exclude_outliers(self, individual_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Exclude outliers using Tukey fences method (ADR-010).
        
        Returns:
            Tuple of (filtered_data, outlier_indices)
        """
        if len(individual_data) < 3:
            return individual_data, []
        
        # Extract numeric values for outlier detection
        # Use quality scores if available, otherwise use verification results as 0/1
        values = []
        for data in individual_data:
            if data['quality_score'] is not None:
                values.append(data['quality_score'])
            else:
                values.append(1.0 if data['verified_pass'] else 0.0)
        
        # Calculate Tukey fences
        q1 = statistics.quantiles(values, n=4)[0]  # 25th percentile
        q3 = statistics.quantiles(values, n=4)[2]  # 75th percentile
        iqr = q3 - q1
        
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        
        # Identify outliers
        outlier_indices = []
        filtered_data = []
        
        for i, (data, value) in enumerate(zip(individual_data, values)):
            if lower_fence <= value <= upper_fence:
                filtered_data.append(data)
            else:
                outlier_indices.append(data['index'])
        
        return filtered_data, outlier_indices
    
    def calculate_agreement_metrics(self, results: List[BenchmarkResult]) -> Dict[str, float]:
        """
        Calculate inter-run agreement metrics.
        
        Args:
            results: List of BenchmarkResult objects
            
        Returns:
            Dictionary with agreement metrics
        """
        if len(results) < 2:
            return {'agreement_rate': 1.0, 'fleiss_kappa': 1.0}
        
        # Extract verification results
        verification_results = [self._extract_verification_result(r) for r in results if r.success]
        
        if not verification_results:
            return {'agreement_rate': 0.0, 'fleiss_kappa': 0.0}
        
        # Calculate simple agreement rate
        pass_count = sum(verification_results)
        fail_count = len(verification_results) - pass_count
        agreement_rate = max(pass_count, fail_count) / len(verification_results)
        
        # Calculate Fleiss' kappa for inter-rater reliability
        # Simplified version for binary classification
        n = len(verification_results)
        p_pass = pass_count / n
        p_fail = fail_count / n
        
        # Expected agreement by chance
        pe = p_pass ** 2 + p_fail ** 2
        
        # Observed agreement
        po = agreement_rate
        
        # Fleiss' kappa
        kappa = (po - pe) / (1 - pe) if pe != 1 else 1.0
        
        return {
            'agreement_rate': agreement_rate,
            'fleiss_kappa': kappa,
            'pass_rate': p_pass,
            'total_runs': n
        }