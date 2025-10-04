#!/usr/bin/env python3
"""
Benchmark Analysis and Reporting

This module provides analysis capabilities for benchmark results,
including framework comparison, trend analysis, and report generation.
"""

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .benchmarking import BenchmarkResult, BenchmarkStatus


class BenchmarkAnalyzer:
    """Analyzes and compares benchmark results across frameworks."""
    
    def __init__(self, results_dir: str = None):
        self.results_dir = Path(results_dir or "benchmark_results")
    
    def load_results(self, filename: str) -> Dict[str, Any]:
        """Load benchmark results from file."""
        filepath = self.results_dir / filename
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def compare_frameworks(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare frameworks across multiple dimensions.
        
        Args:
            results_data: Loaded benchmark results.
            
        Returns:
            Comparison analysis.
        """
        frameworks = list(results_data['results'].keys())
        comparison = {
            'frameworks': frameworks,
            'metrics': {},
            'rankings': {},
            'recommendations': []
        }
        
        # Performance comparison
        performance_metrics = {}
        for framework in frameworks:
            framework_results = [
                BenchmarkResult.from_dict(result_data)
                for result_data in results_data['results'][framework]
            ]
            completed_results = [r for r in framework_results if r.status == BenchmarkStatus.COMPLETED]
            
            if completed_results:
                avg_response_time = statistics.mean([r.duration_seconds for r in completed_results])
                performance_metrics[framework] = avg_response_time
        
        comparison['metrics']['performance'] = performance_metrics
        
        # Quality comparison
        quality_metrics = {}
        for framework in frameworks:
            framework_results = [
                BenchmarkResult.from_dict(result_data)
                for result_data in results_data['results'][framework]
            ]
            completed_results = [r for r in framework_results if r.status == BenchmarkStatus.COMPLETED]
            
            quality_scores = []
            for result in completed_results:
                if result.quality_scores and 'overall' in result.quality_scores:
                    quality_scores.append(result.quality_scores['overall'])
            
            if quality_scores:
                avg_quality = statistics.mean(quality_scores)
                quality_metrics[framework] = avg_quality
        
        comparison['metrics']['quality'] = quality_metrics
        
        # Reliability comparison
        reliability_metrics = {}
        for framework in frameworks:
            framework_results = [
                BenchmarkResult.from_dict(result_data)
                for result_data in results_data['results'][framework]
            ]
            
            if framework_results:
                success_rate = len([r for r in framework_results if r.status == BenchmarkStatus.COMPLETED]) / len(framework_results)
                reliability_metrics[framework] = success_rate
        
        comparison['metrics']['reliability'] = reliability_metrics
        
        # Cost comparison
        cost_metrics = {}
        for framework in frameworks:
            framework_results = [
                BenchmarkResult.from_dict(result_data)
                for result_data in results_data['results'][framework]
            ]
            completed_results = [r for r in framework_results if r.status == BenchmarkStatus.COMPLETED]
            
            if completed_results:
                total_cost = sum(
                    result.cost_data.get('total_cost_usd', 0.0)
                    for result in completed_results
                )
                avg_cost = total_cost / len(completed_results) if completed_results else 0.0
                cost_metrics[framework] = avg_cost
        
        comparison['metrics']['cost'] = cost_metrics
        
        # Generate rankings
        comparison['rankings'] = self._generate_rankings(comparison['metrics'])
        
        # Generate recommendations
        comparison['recommendations'] = self._generate_recommendations(comparison)
        
        return comparison
    
    def _generate_rankings(self, metrics: Dict[str, Dict[str, float]]) -> Dict[str, List[str]]:
        """Generate framework rankings for each metric."""
        rankings = {}
        
        for metric_name, metric_data in metrics.items():
            if not metric_data:
                continue
            
            # Sort frameworks by metric (higher is better for quality/reliability, lower is better for performance/cost)
            if metric_name in ['performance', 'cost']:
                # Lower values are better
                sorted_frameworks = sorted(metric_data.items(), key=lambda x: x[1])
            else:
                # Higher values are better for quality/reliability
                sorted_frameworks = sorted(metric_data.items(), key=lambda x: x[1], reverse=True)
            
            rankings[metric_name] = [framework for framework, _ in sorted_frameworks]
        
        return rankings
    
    def _generate_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison results."""
        recommendations = []
        
        rankings = comparison.get('rankings', {})
        metrics = comparison.get('metrics', {})
        
        # Performance recommendations
        if 'performance' in rankings and rankings['performance']:
            fastest_framework = rankings['performance'][0]
            recommendations.append(f"For best performance, consider {fastest_framework}")
        
        # Quality recommendations
        if 'quality' in rankings and rankings['quality']:
            highest_quality = rankings['quality'][0]
            recommendations.append(f"For highest quality output, consider {highest_quality}")
        
        # Reliability recommendations
        if 'reliability' in rankings and rankings['reliability']:
            most_reliable = rankings['reliability'][0]
            recommendations.append(f"For highest reliability, consider {most_reliable}")
        
        # Cost recommendations
        if 'cost' in rankings and rankings['cost']:
            most_cost_effective = rankings['cost'][0]
            recommendations.append(f"For best cost efficiency, consider {most_cost_effective}")
        
        # Overall recommendation
        if len(rankings) >= 2:
            # Calculate overall scores (simple average of normalized ranks)
            overall_scores = {}
            for framework in comparison['frameworks']:
                total_rank = 0
                rank_count = 0
                
                for metric_rankings in rankings.values():
                    if framework in metric_rankings:
                        rank = metric_rankings.index(framework) + 1
                        total_rank += rank
                        rank_count += 1
                
                if rank_count > 0:
                    overall_scores[framework] = total_rank / rank_count
            
            if overall_scores:
                best_overall = min(overall_scores.items(), key=lambda x: x[1])[0]
                recommendations.append(f"Overall best framework: {best_overall}")
        
        return recommendations
    
    def analyze_task_performance(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze performance by task type.
        
        Args:
            results_data: Loaded benchmark results.
            
        Returns:
            Task-specific performance analysis.
        """
        task_analysis = {}
        
        # Group results by task type
        for framework, framework_results in results_data['results'].items():
            for result_data in framework_results:
                result = BenchmarkResult.from_dict(result_data)
                task_type = result.metadata.get('task_type', 'unknown')
                
                if task_type not in task_analysis:
                    task_analysis[task_type] = {
                        'frameworks': {},
                        'overall_stats': {
                            'total_runs': 0,
                            'successful_runs': 0,
                            'avg_response_time': 0.0,
                            'avg_quality_score': 0.0
                        }
                    }
                
                if framework not in task_analysis[task_type]['frameworks']:
                    task_analysis[task_type]['frameworks'][framework] = {
                        'runs': 0,
                        'successful_runs': 0,
                        'response_times': [],
                        'quality_scores': []
                    }
                
                framework_stats = task_analysis[task_type]['frameworks'][framework]
                framework_stats['runs'] += 1
                task_analysis[task_type]['overall_stats']['total_runs'] += 1
                
                if result.status == BenchmarkStatus.COMPLETED:
                    framework_stats['successful_runs'] += 1
                    task_analysis[task_type]['overall_stats']['successful_runs'] += 1
                    
                    framework_stats['response_times'].append(result.duration_seconds)
                    
                    if result.quality_scores and 'overall' in result.quality_scores:
                        framework_stats['quality_scores'].append(result.quality_scores['overall'])
        
        # Calculate aggregated statistics
        for task_type, task_data in task_analysis.items():
            all_response_times = []
            all_quality_scores = []
            
            for framework, framework_stats in task_data['frameworks'].items():
                # Calculate framework averages
                if framework_stats['response_times']:
                    framework_stats['avg_response_time'] = statistics.mean(framework_stats['response_times'])
                    all_response_times.extend(framework_stats['response_times'])
                else:
                    framework_stats['avg_response_time'] = 0.0
                
                if framework_stats['quality_scores']:
                    framework_stats['avg_quality_score'] = statistics.mean(framework_stats['quality_scores'])
                    all_quality_scores.extend(framework_stats['quality_scores'])
                else:
                    framework_stats['avg_quality_score'] = 0.0
                
                framework_stats['success_rate'] = (
                    framework_stats['successful_runs'] / framework_stats['runs']
                    if framework_stats['runs'] > 0 else 0.0
                )
            
            # Calculate overall task statistics
            if all_response_times:
                task_data['overall_stats']['avg_response_time'] = statistics.mean(all_response_times)
            if all_quality_scores:
                task_data['overall_stats']['avg_quality_score'] = statistics.mean(all_quality_scores)
            
            task_data['overall_stats']['success_rate'] = (
                task_data['overall_stats']['successful_runs'] / task_data['overall_stats']['total_runs']
                if task_data['overall_stats']['total_runs'] > 0 else 0.0
            )
        
        return task_analysis
    
    def generate_report(self, results_data: Dict[str, Any]) -> str:
        """Generate a comprehensive benchmark report."""
        comparison = self.compare_frameworks(results_data)
        task_analysis = self.analyze_task_performance(results_data)
        
        report_lines = [
            "# Benchmark Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Suite:** {results_data['suite']['name']}",
            f"**Frameworks Tested:** {', '.join(comparison['frameworks'])}",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Add summary statistics
        summary = results_data.get('summary', {})
        if summary:
            report_lines.extend([
                f"- **Total Tasks:** {summary.get('total_tasks', 0)}",
                f"- **Frameworks:** {summary.get('total_frameworks', 0)}",
                ""
            ])
        
        # Add key recommendations
        if comparison['recommendations']:
            report_lines.extend([
                "### Key Recommendations",
                ""
            ])
            for recommendation in comparison['recommendations']:
                report_lines.append(f"- {recommendation}")
            report_lines.append("")
        
        # Add performance metrics
        if 'performance' in comparison['metrics']:
            report_lines.extend([
                "## Performance Metrics (Response Time)",
                ""
            ])
            
            for framework, response_time in comparison['metrics']['performance'].items():
                report_lines.append(f"- **{framework}:** {response_time:.2f} seconds")
            
            report_lines.append("")
        
        # Add quality metrics
        if 'quality' in comparison['metrics']:
            report_lines.extend([
                "## Quality Metrics (Overall Score)",
                ""
            ])
            
            for framework, quality_score in comparison['metrics']['quality'].items():
                report_lines.append(f"- **{framework}:** {quality_score:.1f}/10")
            
            report_lines.append("")
        
        # Add reliability metrics
        if 'reliability' in comparison['metrics']:
            report_lines.extend([
                "## Reliability Metrics (Success Rate)",
                ""
            ])
            
            for framework, success_rate in comparison['metrics']['reliability'].items():
                report_lines.append(f"- **{framework}:** {success_rate:.1%}")
            
            report_lines.append("")
        
        # Add cost metrics
        if 'cost' in comparison['metrics']:
            report_lines.extend([
                "## Cost Metrics (Average Cost per Task)",
                ""
            ])
            
            for framework, avg_cost in comparison['metrics']['cost'].items():
                report_lines.append(f"- **{framework}:** ${avg_cost:.4f}")
            
            report_lines.append("")
        
        # Add rankings
        if comparison['rankings']:
            report_lines.extend([
                "## Framework Rankings",
                ""
            ])
            
            for metric, ranking in comparison['rankings'].items():
                report_lines.append(f"**{metric.title()}:**")
                for i, framework in enumerate(ranking, 1):
                    report_lines.append(f"{i}. {framework}")
                report_lines.append("")
        
        # Add task-specific analysis
        if task_analysis:
            report_lines.extend([
                "## Task Type Analysis",
                ""
            ])
            
            for task_type, task_data in task_analysis.items():
                report_lines.extend([
                    f"### {task_type.title()} Tasks",
                    "",
                    f"- **Total Runs:** {task_data['overall_stats']['total_runs']}",
                    f"- **Success Rate:** {task_data['overall_stats']['success_rate']:.1%}",
                    f"- **Average Response Time:** {task_data['overall_stats']['avg_response_time']:.2f}s",
                    f"- **Average Quality Score:** {task_data['overall_stats']['avg_quality_score']:.1f}/10",
                    ""
                ])
                
                # Framework performance for this task type
                report_lines.append("**Framework Performance:**")
                for framework, framework_stats in task_data['frameworks'].items():
                    report_lines.append(
                        f"- **{framework}:** "
                        f"{framework_stats['success_rate']:.1%} success, "
                        f"{framework_stats['avg_response_time']:.2f}s avg time, "
                        f"{framework_stats['avg_quality_score']:.1f}/10 quality"
                    )
                report_lines.append("")
        
        # Add detailed framework summaries
        if summary and 'frameworks' in summary:
            report_lines.extend([
                "## Detailed Framework Analysis",
                ""
            ])
            
            for framework, framework_summary in summary['frameworks'].items():
                report_lines.extend([
                    f"### {framework}",
                    "",
                    f"- **Tasks Completed:** {framework_summary.get('completed_tasks', 0)}/{framework_summary.get('total_tasks', 0)}",
                    f"- **Success Rate:** {framework_summary.get('success_rate', 0):.1%}",
                    f"- **Average Response Time:** {framework_summary.get('avg_response_time', 0):.2f}s",
                    f"- **Response Time Range:** {framework_summary.get('min_response_time', 0):.2f}s - {framework_summary.get('max_response_time', 0):.2f}s",
                ])
                
                if 'avg_quality_score' in framework_summary:
                    report_lines.extend([
                        f"- **Average Quality Score:** {framework_summary['avg_quality_score']:.1f}/10",
                        f"- **Quality Score Range:** {framework_summary.get('min_quality_score', 0):.1f} - {framework_summary.get('max_quality_score', 0):.1f}",
                    ])
                
                if 'total_cost_usd' in framework_summary:
                    report_lines.append(f"- **Total Cost:** ${framework_summary['total_cost_usd']:.4f}")
                
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def generate_csv_export(self, results_data: Dict[str, Any]) -> str:
        """Generate CSV export of benchmark results."""
        csv_lines = [
            "Framework,Task ID,Task Type,Status,Response Time (s),Quality Score,Cost (USD),Error Message"
        ]
        
        for framework, framework_results in results_data['results'].items():
            for result_data in framework_results:
                result = BenchmarkResult.from_dict(result_data)
                
                csv_lines.append(
                    f"{framework},"
                    f"{result.task_id},"
                    f"{result.metadata.get('task_type', 'unknown')},"
                    f"{result.status.value},"
                    f"{result.duration_seconds:.3f},"
                    f"{result.quality_scores.get('overall', 0.0):.2f},"
                    f"{result.cost_data.get('total_cost_usd', 0.0):.6f},"
                    f"\"{result.error_message or ''}\""
                )
        
        return "\n".join(csv_lines)
    
    def find_performance_outliers(self, results_data: Dict[str, Any], 
                                 threshold_std: float = 2.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find performance outliers in benchmark results.
        
        Args:
            results_data: Loaded benchmark results.
            threshold_std: Number of standard deviations to consider as outlier.
            
        Returns:
            Dictionary of outliers by framework.
        """
        outliers = {}
        
        for framework, framework_results in results_data['results'].items():
            framework_outliers = []
            
            # Get all response times for this framework
            response_times = []
            results_list = []
            
            for result_data in framework_results:
                result = BenchmarkResult.from_dict(result_data)
                if result.status == BenchmarkStatus.COMPLETED:
                    response_times.append(result.duration_seconds)
                    results_list.append(result)
            
            if len(response_times) < 3:  # Need at least 3 data points
                continue
            
            # Calculate statistics
            mean_time = statistics.mean(response_times)
            std_time = statistics.stdev(response_times)
            
            # Find outliers
            for result in results_list:
                z_score = abs(result.duration_seconds - mean_time) / std_time
                if z_score > threshold_std:
                    framework_outliers.append({
                        'task_id': result.task_id,
                        'response_time': result.duration_seconds,
                        'z_score': z_score,
                        'task_type': result.metadata.get('task_type', 'unknown'),
                        'quality_score': result.quality_scores.get('overall', 0.0)
                    })
            
            if framework_outliers:
                outliers[framework] = framework_outliers
        
        return outliers