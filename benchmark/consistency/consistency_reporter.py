"""
Consistency Reporter for Self-Consistency Evaluation

Generates consistency.json reports and integrates with dashboard
following ADR-010 specifications.
"""

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from common.benchmarking import BenchmarkResult
from .consensus_analyzer import ConsensusAnalyzer, ConsensusResult
from .variance_calculator import VarianceCalculator, VarianceMetrics


class ConsistencyReporter:
    """Generates consistency reports and integrates with dashboard."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize consistency reporter.
        
        Args:
            output_dir: Directory to write consistency reports
        """
        self.output_dir = output_dir or Path("comparison-results")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_consistency_report(self,
                                  framework: str,
                                  task: str,
                                  results: List[BenchmarkResult],
                                  consensus_result: ConsensusResult,
                                  variance_metrics: VarianceMetrics,
                                  **metadata) -> Dict[str, Any]:
        """
        Generate comprehensive consistency report.
        
        Args:
            framework: Framework name
            task: Task name
            results: List of benchmark results
            consensus_result: Consensus analysis result
            variance_metrics: Variance analysis result
            **metadata: Additional metadata
            
        Returns:
            Dictionary with complete consistency report
        """
        report = {
            # Report metadata
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "framework": framework,
            "task": task,
            
            # Run summary
            "run_summary": {
                "total_runs": len(results),
                "successful_runs": len([r for r in results if r.success]),
                "failed_runs": len([r for r in results if not r.success]),
                "seeds_used": [r.metadata.get('seed') for r in results if hasattr(r, 'metadata') and r.metadata.get('seed') is not None]
            },
            
            # Consensus analysis
            "consensus": {
                "decision": consensus_result.consensus_pass,
                "confidence": consensus_result.confidence,
                "strategy": consensus_result.strategy,
                "vote_breakdown": {
                    "pass_votes": consensus_result.pass_votes,
                    "fail_votes": consensus_result.fail_votes,
                    "total_votes": consensus_result.total_votes
                },
                "weighted_score": consensus_result.weighted_score,
                "quality_weights_used": consensus_result.quality_weights_used,
                "outliers_excluded": consensus_result.outliers_excluded or []
            },
            
            # Variance analysis
            "variance": {
                "success_rate": {
                    "value": variance_metrics.success_rate,
                    "confidence_interval": variance_metrics.success_rate_ci
                },
                "duration": {
                    "mean": variance_metrics.duration_mean,
                    "std": variance_metrics.duration_std,
                    "coefficient_of_variation": variance_metrics.duration_cv,
                    "confidence_interval": variance_metrics.duration_ci
                },
                "tokens": {
                    "mean": variance_metrics.tokens_mean,
                    "std": variance_metrics.tokens_std,
                    "coefficient_of_variation": variance_metrics.tokens_cv,
                    "confidence_interval": variance_metrics.tokens_ci
                } if variance_metrics.tokens_mean is not None else None,
                "quality": {
                    "mean": variance_metrics.quality_mean,
                    "std": variance_metrics.quality_std,
                    "coefficient_of_variation": variance_metrics.quality_cv,
                    "confidence_interval": variance_metrics.quality_ci
                } if variance_metrics.quality_mean is not None else None
            },
            
            # Reliability assessment
            "reliability": {
                "score": variance_metrics.reliability_score,
                "label": variance_metrics.reliability_label,
                "outliers": variance_metrics.outliers or []
            },
            
            # Individual run details
            "individual_runs": [
                self._format_individual_result(i, result)
                for i, result in enumerate(results)
            ],
            
            # Additional metadata
            "metadata": metadata
        }
        
        return report
    
    def write_consistency_report(self,
                               framework: str,
                               task: str,
                               report: Dict[str, Any],
                               filename: Optional[str] = None) -> Path:
        """
        Write consistency report to JSON file.
        
        Args:
            framework: Framework name
            task: Task name
            report: Report dictionary
            filename: Optional custom filename
            
        Returns:
            Path to written file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consistency_{framework}_{task}_{timestamp}.json"
        
        output_file = self.output_dir / filename
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return output_file
    
    def generate_dashboard_data(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate dashboard-compatible data from consistency reports.
        
        Args:
            reports: List of consistency report dictionaries
            
        Returns:
            Dashboard data dictionary
        """
        dashboard_data = {
            "consistency_overview": {
                "total_evaluations": len(reports),
                "frameworks": list(set(r["framework"] for r in reports)),
                "tasks": list(set(r["task"] for r in reports)),
                "generated_at": datetime.now(timezone.utc).isoformat()
            },
            "framework_reliability": {},
            "task_difficulty": {},
            "violin_plot_data": [],
            "confidence_bars": []
        }
        
        # Aggregate by framework
        framework_data = {}
        for report in reports:
            framework = report["framework"]
            if framework not in framework_data:
                framework_data[framework] = []
            framework_data[framework].append(report)
        
        # Calculate framework reliability scores
        for framework, fw_reports in framework_data.items():
            reliability_scores = [r["reliability"]["score"] for r in fw_reports]
            dashboard_data["framework_reliability"][framework] = {
                "mean_reliability": statistics.mean(reliability_scores) if reliability_scores else 0.0,
                "evaluations": len(fw_reports),
                "high_reliability_tasks": len([r for r in fw_reports if r["reliability"]["label"] == "High"]),
                "medium_reliability_tasks": len([r for r in fw_reports if r["reliability"]["label"] == "Medium"]),
                "low_reliability_tasks": len([r for r in fw_reports if r["reliability"]["label"] == "Low"])
            }
        
        # Generate violin plot data for durations
        for report in reports:
            if report["individual_runs"]:
                durations = [
                    run["duration"] for run in report["individual_runs"] 
                    if run["duration"] is not None
                ]
                if durations:
                    dashboard_data["violin_plot_data"].append({
                        "framework": report["framework"],
                        "task": report["task"],
                        "durations": durations,
                        "mean": statistics.mean(durations),
                        "std": statistics.stdev(durations) if len(durations) > 1 else 0.0
                    })
        
        # Generate confidence bars for success rates
        for report in reports:
            success_rate = report["variance"]["success_rate"]["value"]
            ci_lower, ci_upper = report["variance"]["success_rate"]["confidence_interval"]
            
            dashboard_data["confidence_bars"].append({
                "framework": report["framework"],
                "task": report["task"],
                "success_rate": success_rate,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "reliability_label": report["reliability"]["label"]
            })
        
        return dashboard_data
    
    def _format_individual_result(self, index: int, result: BenchmarkResult) -> Dict[str, Any]:
        """Format individual result for report."""
        return {
            "run_index": index,
            "success": result.success,
            "verified_pass": self._extract_verification_result(result),
            "duration": self._extract_duration(result),
            "tokens_used": self._extract_tokens_used(result),
            "quality_score": self._extract_quality_score(result),
            "error": getattr(result, 'error', None),
            "seed": result.metadata.get('seed') if hasattr(result, 'metadata') else None
        }
    
    def _extract_verification_result(self, result: BenchmarkResult) -> bool:
        """Extract verification result from benchmark result."""
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
        
        return getattr(result, 'success', False)
    
    def _extract_duration(self, result: BenchmarkResult) -> Optional[float]:
        """Extract duration from benchmark result."""
        if hasattr(result, 'duration'):
            return result.duration
        elif hasattr(result, 'execution_time'):
            return result.execution_time
        elif hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            return result.metadata.get('duration') or result.metadata.get('execution_time')
        return None
    
    def _extract_tokens_used(self, result: BenchmarkResult) -> Optional[int]:
        """Extract token usage from benchmark result."""
        if hasattr(result, 'tokens_used'):
            return result.tokens_used
        elif hasattr(result, 'total_tokens'):
            return result.total_tokens
        elif hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            return result.metadata.get('tokens_used') or result.metadata.get('total_tokens')
        return None
    
    def _extract_quality_score(self, result: BenchmarkResult) -> Optional[float]:
        """Extract quality score from benchmark result."""
        if hasattr(result, 'quality_score'):
            return result.quality_score
        elif hasattr(result, 'verification') and isinstance(result.verification, dict):
            return result.verification.get('score')
        elif hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            verification = result.metadata.get('verification', {})
            if isinstance(verification, dict):
                return verification.get('score')
        return None