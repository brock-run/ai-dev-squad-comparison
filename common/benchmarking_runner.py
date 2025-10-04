#!/usr/bin/env python3
"""
Benchmark Runner and Execution Engine

This module handles the execution of benchmark suites, performance profiling,
quality evaluation, and result collection.
"""

import time
import logging
import threading
import statistics
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

from .benchmarking import (
    BenchmarkSuite, BenchmarkTask, BenchmarkResult, BenchmarkStatus,
    MetricType, TaskType, MessageImportance
)

# Import enhanced features
try:
    from .ollama_integration import create_agent
    from .telemetry import get_logger, get_trace_manager, get_cost_tracker
    from .caching import get_cache
    from .context_management import get_context_manager, ContextStrategy
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False
    logging.warning("Enhanced features not available for benchmarking")

logger = logging.getLogger("ai_dev_squad.benchmarking.runner")


class QualityEvaluator:
    """Evaluates the quality of benchmark responses."""
    
    def __init__(self):
        self.evaluation_methods = {
            'length_check': self._evaluate_length,
            'keyword_presence': self._evaluate_keywords,
            'structure_check': self._evaluate_structure,
            'code_quality': self._evaluate_code_quality,
            'completeness': self._evaluate_completeness,
            'accuracy': self._evaluate_accuracy
        }
    
    def evaluate_response(self, task: BenchmarkTask, response: str) -> Dict[str, float]:
        """
        Evaluate response quality based on task criteria.
        
        Args:
            task: The benchmark task.
            response: The response to evaluate.
            
        Returns:
            Dictionary of quality scores (0-10 scale).
        """
        scores = {}
        criteria = task.evaluation_criteria
        
        for criterion, config in criteria.items():
            if criterion in self.evaluation_methods:
                try:
                    score = self.evaluation_methods[criterion](response, config, task)
                    scores[criterion] = max(0.0, min(10.0, score))
                except Exception as e:
                    logger.warning(f"Error evaluating {criterion}: {e}")
                    scores[criterion] = 0.0
        
        # Calculate overall quality score
        if scores:
            scores['overall'] = sum(scores.values()) / len(scores)
        else:
            scores['overall'] = 5.0  # Default neutral score
        
        return scores
    
    def _evaluate_length(self, response: str, config: Dict[str, Any], task: BenchmarkTask) -> float:
        """Evaluate response length appropriateness."""
        min_length = config.get('min_length', 50)
        max_length = config.get('max_length', 2000)
        optimal_length = config.get('optimal_length', 500)
        
        length = len(response)
        
        if length < min_length:
            return 2.0  # Too short
        elif length > max_length:
            return 3.0  # Too long
        else:
            # Score based on proximity to optimal length
            distance = abs(length - optimal_length)
            max_distance = max(optimal_length - min_length, max_length - optimal_length)
            score = 10.0 - (distance / max_distance) * 5.0
            return max(5.0, score)
    
    def _evaluate_keywords(self, response: str, config: Dict[str, Any], task: BenchmarkTask) -> float:
        """Evaluate presence of required keywords."""
        required_keywords = config.get('required', [])
        optional_keywords = config.get('optional', [])
        forbidden_keywords = config.get('forbidden', [])
        
        response_lower = response.lower()
        score = 5.0  # Base score
        
        # Check required keywords
        required_found = sum(1 for kw in required_keywords if kw.lower() in response_lower)
        if required_keywords:
            score += (required_found / len(required_keywords)) * 3.0
        
        # Check optional keywords (bonus points)
        optional_found = sum(1 for kw in optional_keywords if kw.lower() in response_lower)
        if optional_keywords:
            score += (optional_found / len(optional_keywords)) * 2.0
        
        # Penalize forbidden keywords
        forbidden_found = sum(1 for kw in forbidden_keywords if kw.lower() in response_lower)
        if forbidden_found > 0:
            score -= forbidden_found * 2.0
        
        return score
    
    def _evaluate_structure(self, response: str, config: Dict[str, Any], task: BenchmarkTask) -> float:
        """Evaluate response structure and formatting."""
        score = 5.0
        
        # Check for code blocks if expected
        if config.get('expect_code', False):
            if '```' in response or 'def ' in response or 'class ' in response:
                score += 2.0
            else:
                score -= 2.0
        
        # Check for lists/bullets if expected
        if config.get('expect_list', False):
            if any(marker in response for marker in ['1.', '2.', '-', '*', '•']):
                score += 1.0
            else:
                score -= 1.0
        
        # Check for sections/headers if expected
        if config.get('expect_sections', False):
            if any(marker in response for marker in ['#', '##', '###', '**', '__']):
                score += 1.0
        
        return score
    
    def _evaluate_code_quality(self, response: str, config: Dict[str, Any], task: BenchmarkTask) -> float:
        """Evaluate code quality if response contains code."""
        score = 5.0
        
        # Simple heuristics for code quality
        if 'def ' in response or 'class ' in response:
            # Check for docstrings
            if '"""' in response or "'''" in response:
                score += 1.0
            
            # Check for proper indentation (Python)
            lines = response.split('\n')
            indented_lines = [line for line in lines if line.startswith('    ')]
            if len(indented_lines) > 0:
                score += 1.0
            
            # Check for error handling
            if 'try:' in response or 'except' in response:
                score += 1.0
            
            # Check for type hints
            if '->' in response or ': str' in response or ': int' in response:
                score += 1.0
        
        return score
    
    def _evaluate_completeness(self, response: str, config: Dict[str, Any], task: BenchmarkTask) -> float:
        """Evaluate response completeness."""
        expected_elements = config.get('expected_elements', [])
        
        if not expected_elements:
            return 7.0  # Default good score if no specific expectations
        
        found_elements = 0
        for element in expected_elements:
            if element.lower() in response.lower():
                found_elements += 1
        
        completeness_ratio = found_elements / len(expected_elements)
        return 3.0 + (completeness_ratio * 7.0)  # Scale from 3-10
    
    def _evaluate_accuracy(self, response: str, config: Dict[str, Any], task: BenchmarkTask) -> float:
        """Evaluate response accuracy against expected output."""
        if not task.expected_output:
            return 7.0  # Default score if no expected output
        
        # Simple similarity check
        response_words = set(response.lower().split())
        expected_words = set(task.expected_output.lower().split())
        
        if not expected_words:
            return 7.0
        
        intersection = response_words & expected_words
        similarity = len(intersection) / len(expected_words)
        
        return 2.0 + (similarity * 8.0)  # Scale from 2-10


class PerformanceProfiler:
    """Profiles performance characteristics of benchmark runs."""
    
    def __init__(self):
        self.active_profiles = {}
        self._lock = threading.RLock()
    
    @contextmanager
    def profile_execution(self, task_id: str):
        """Context manager for profiling task execution."""
        profile_data = {
            'start_time': time.time(),
            'start_memory': self._get_memory_usage(),
            'start_cpu': self._get_cpu_usage()
        }
        
        with self._lock:
            self.active_profiles[task_id] = profile_data
        
        try:
            yield profile_data
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            end_cpu = self._get_cpu_usage()
            
            with self._lock:
                if task_id in self.active_profiles:
                    profile_data.update({
                        'end_time': end_time,
                        'duration': end_time - profile_data['start_time'],
                        'end_memory': end_memory,
                        'memory_delta': end_memory - profile_data['start_memory'],
                        'end_cpu': end_cpu,
                        'cpu_delta': end_cpu - profile_data['start_cpu']
                    })
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
    
    def get_profile_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get profile data for a task."""
        with self._lock:
            return self.active_profiles.get(task_id)


class BenchmarkRunner:
    """Executes benchmark suites and collects results."""
    
    def __init__(self, results_dir: str = None):
        """
        Initialize benchmark runner.
        
        Args:
            results_dir: Directory to store benchmark results.
        """
        self.results_dir = Path(results_dir or "benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
        
        self.quality_evaluator = QualityEvaluator()
        self.performance_profiler = PerformanceProfiler()
        
        # Initialize enhanced features if available
        if ENHANCED_FEATURES_AVAILABLE:
            self.logger = get_logger()
            self.tracer = get_trace_manager()
            self.cost_tracker = get_cost_tracker()
            self.cache = get_cache()
            self.context_manager = get_context_manager()
        else:
            self.logger = None
            self.tracer = None
            self.cost_tracker = None
            self.cache = None
            self.context_manager = None
        
        self.active_runs = {}
        self._lock = threading.RLock()
    
    def run_benchmark_suite(self, suite: BenchmarkSuite, 
                           parallel: bool = True,
                           max_workers: int = 4) -> Dict[str, List[BenchmarkResult]]:
        """
        Run a complete benchmark suite.
        
        Args:
            suite: The benchmark suite to run.
            parallel: Whether to run tasks in parallel.
            max_workers: Maximum number of parallel workers.
            
        Returns:
            Dictionary mapping framework names to lists of results.
        """
        logger.info(f"Starting benchmark suite: {suite.name}")
        
        all_results = {}
        
        for framework in suite.frameworks:
            logger.info(f"Running benchmarks for framework: {framework}")
            
            if parallel:
                results = self._run_tasks_parallel(suite.tasks, framework, max_workers)
            else:
                results = self._run_tasks_sequential(suite.tasks, framework)
            
            all_results[framework] = results
        
        # Save results
        self._save_suite_results(suite, all_results)
        
        logger.info(f"Completed benchmark suite: {suite.name}")
        return all_results
    
    def _run_tasks_parallel(self, tasks: List[BenchmarkTask], 
                           framework: str, max_workers: int) -> List[BenchmarkResult]:
        """Run tasks in parallel using thread pool."""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._run_single_task, task, framework): task
                for task in tasks
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    # Create failed result
                    result = BenchmarkResult(
                        task_id=task.task_id,
                        framework=framework,
                        agent_role="unknown",
                        model_name="unknown",
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        status=BenchmarkStatus.FAILED,
                        error_message=str(e)
                    )
                    results.append(result)
        
        return results
    
    def _run_tasks_sequential(self, tasks: List[BenchmarkTask], 
                             framework: str) -> List[BenchmarkResult]:
        """Run tasks sequentially."""
        results = []
        
        for task in tasks:
            try:
                result = self._run_single_task(task, framework)
                results.append(result)
            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {e}")
                result = BenchmarkResult(
                    task_id=task.task_id,
                    framework=framework,
                    agent_role="unknown",
                    model_name="unknown",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    status=BenchmarkStatus.FAILED,
                    error_message=str(e)
                )
                results.append(result)
        
        return results
    
    def _run_single_task(self, task: BenchmarkTask, framework: str) -> BenchmarkResult:
        """
        Run a single benchmark task.
        
        Args:
            task: The task to run.
            framework: The framework to test.
            
        Returns:
            Benchmark result.
        """
        start_time = datetime.now()
        
        # Create agent for the framework
        try:
            agent = self._create_agent_for_framework(framework, task)
            agent_role = getattr(agent, 'role', 'unknown')
            model_name = getattr(agent, 'model', 'unknown')
        except Exception as e:
            return BenchmarkResult(
                task_id=task.task_id,
                framework=framework,
                agent_role="unknown",
                model_name="unknown",
                start_time=start_time,
                end_time=datetime.now(),
                status=BenchmarkStatus.FAILED,
                error_message=f"Failed to create agent: {e}"
            )
        
        # Profile the execution
        with self.performance_profiler.profile_execution(task.task_id):
            try:
                # Execute the task with tracing if available
                if self.tracer:
                    with self.tracer.trace_operation(f"benchmark_{task.task_id}"):
                        response = self._execute_task_with_agent(agent, task)
                else:
                    response = self._execute_task_with_agent(agent, task)
                
                end_time = datetime.now()
                status = BenchmarkStatus.COMPLETED
                error_message = None
                
            except Exception as e:
                end_time = datetime.now()
                response = None
                status = BenchmarkStatus.FAILED
                error_message = str(e)
                logger.error(f"Task execution failed: {e}")
        
        # Get performance data
        profile_data = self.performance_profiler.get_profile_data(task.task_id)
        
        # Evaluate quality if response was generated
        quality_scores = {}
        if response and status == BenchmarkStatus.COMPLETED:
            quality_scores = self.quality_evaluator.evaluate_response(task, response)
        
        # Collect metrics
        metrics = self._collect_metrics(task, agent, profile_data)
        
        # Collect cost data if available
        cost_data = self._collect_cost_data(task, agent)
        
        # Create result
        result = BenchmarkResult(
            task_id=task.task_id,
            framework=framework,
            agent_role=agent_role,
            model_name=model_name,
            start_time=start_time,
            end_time=end_time,
            status=status,
            response=response,
            error_message=error_message,
            metrics=metrics,
            quality_scores=quality_scores,
            performance_data=profile_data or {},
            cost_data=cost_data,
            metadata={
                'task_type': task.task_type.value,
                'importance': task.importance.value,
                'prompt_length': len(task.prompt),
                'response_length': len(response) if response else 0
            }
        )
        
        return result
    
    def _create_agent_for_framework(self, framework: str, task: BenchmarkTask) -> Any:
        """
        Create an agent for the specified framework.
        
        Args:
            framework: Framework name.
            task: Benchmark task.
            
        Returns:
            Agent instance.
        """
        if not ENHANCED_FEATURES_AVAILABLE:
            raise RuntimeError("Enhanced features not available")
        
        # Map task types to agent roles
        role_mapping = {
            TaskType.CODING: "developer",
            TaskType.ARCHITECTURE: "architect",
            TaskType.TESTING: "tester",
            TaskType.DOCUMENTATION: "general",
            TaskType.DEBUGGING: "developer",
            TaskType.ANALYSIS: "general",
            TaskType.PLANNING: "architect",
            TaskType.GENERAL: "general"
        }
        
        role = role_mapping.get(task.task_type, "general")
        
        # Create agent with all enhanced features enabled
        agent = create_agent(
            role=role,
            enable_caching=True,
            enable_context_management=True,
            max_context_tokens=4096
        )
        
        return agent
    
    def _execute_task_with_agent(self, agent: Any, task: BenchmarkTask) -> str:
        """
        Execute a task with the given agent.
        
        Args:
            agent: The agent to use.
            task: The task to execute.
            
        Returns:
            Response from the agent.
        """
        # Use context management if available
        if hasattr(agent, 'enable_context_management') and agent.enable_context_management:
            conversation_id = agent.start_conversation(
                context_strategy=ContextStrategy.SLIDING_WINDOW
            )
            
            try:
                response = agent.chat_with_context(
                    conversation_id=conversation_id,
                    message=task.prompt,
                    task_type=task.task_type,
                    importance=task.importance
                )
            finally:
                agent.end_conversation(conversation_id)
        else:
            # Fallback to basic generation
            response = agent.generate(
                prompt=task.prompt,
                task_type=task.task_type
            )
        
        return response
    
    def _collect_metrics(self, task: BenchmarkTask, agent: Any, 
                        profile_data: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """
        Collect performance metrics.
        
        Args:
            task: The benchmark task.
            agent: The agent used.
            profile_data: Performance profile data.
            
        Returns:
            Dictionary of metrics.
        """
        metrics = {}
        
        if profile_data:
            metrics[MetricType.RESPONSE_TIME.value] = profile_data.get('duration', 0.0)
            metrics[MetricType.MEMORY_USAGE.value] = profile_data.get('memory_delta', 0.0)
            metrics[MetricType.CPU_USAGE.value] = profile_data.get('cpu_delta', 0.0)
        
        # Get cache metrics if available
        if hasattr(agent, 'cache') and agent.cache:
            cache_stats = agent.cache.get_stats()
            metrics[MetricType.CACHE_HIT_RATE.value] = cache_stats.hit_rate
        
        # Calculate throughput (tokens per second)
        if profile_data and 'duration' in profile_data and profile_data['duration'] > 0:
            # Estimate tokens (rough approximation)
            estimated_tokens = len(task.prompt.split()) * 1.3
            metrics[MetricType.THROUGHPUT.value] = estimated_tokens / profile_data['duration']
        
        return metrics
    
    def _collect_cost_data(self, task: BenchmarkTask, agent: Any) -> Dict[str, Any]:
        """
        Collect cost-related data.
        
        Args:
            task: The benchmark task.
            agent: The agent used.
            
        Returns:
            Cost data dictionary.
        """
        cost_data = {}
        
        if self.cost_tracker:
            # Get recent cost entries for this agent
            summary = self.cost_tracker.get_usage_summary()
            if summary.get('total_entries', 0) > 0:
                cost_data = {
                    'total_cost_usd': summary.get('summary', {}).get('total_cost_usd', 0.0),
                    'total_tokens': summary.get('summary', {}).get('total_tokens', 0),
                    'avg_cost_per_token': summary.get('summary', {}).get('total_cost_usd', 0.0) / max(summary.get('summary', {}).get('total_tokens', 1), 1)
                }
        
        return cost_data
    
    def _save_suite_results(self, suite: BenchmarkSuite, 
                           results: Dict[str, List[BenchmarkResult]]) -> None:
        """
        Save benchmark suite results to file.
        
        Args:
            suite: The benchmark suite.
            results: The results to save.
        """
        import json
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_suite_{suite.suite_id}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        # Prepare data for serialization
        data = {
            'suite': suite.to_dict(),
            'results': {
                framework: [result.to_dict() for result in framework_results]
                for framework, framework_results in results.items()
            },
            'summary': self._generate_summary(results),
            'timestamp': timestamp
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved benchmark results to: {filepath}")
    
    def _generate_summary(self, results: Dict[str, List[BenchmarkResult]]) -> Dict[str, Any]:
        """
        Generate summary statistics from benchmark results.
        
        Args:
            results: Benchmark results by framework.
            
        Returns:
            Summary statistics.
        """
        summary = {
            'total_frameworks': len(results),
            'total_tasks': sum(len(framework_results) for framework_results in results.values()),
            'frameworks': {}
        }
        
        for framework, framework_results in results.items():
            if not framework_results:
                continue
            
            # Calculate framework-specific metrics
            completed_results = [r for r in framework_results if r.status == BenchmarkStatus.COMPLETED]
            failed_results = [r for r in framework_results if r.status == BenchmarkStatus.FAILED]
            
            framework_summary = {
                'total_tasks': len(framework_results),
                'completed_tasks': len(completed_results),
                'failed_tasks': len(failed_results),
                'success_rate': len(completed_results) / len(framework_results) if framework_results else 0.0
            }
            
            if completed_results:
                # Performance metrics
                response_times = [r.duration_seconds for r in completed_results]
                framework_summary.update({
                    'avg_response_time': statistics.mean(response_times),
                    'median_response_time': statistics.median(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times)
                })
                
                # Quality metrics
                quality_scores = []
                for result in completed_results:
                    if result.quality_scores and 'overall' in result.quality_scores:
                        quality_scores.append(result.quality_scores['overall'])
                
                if quality_scores:
                    framework_summary.update({
                        'avg_quality_score': statistics.mean(quality_scores),
                        'median_quality_score': statistics.median(quality_scores),
                        'min_quality_score': min(quality_scores),
                        'max_quality_score': max(quality_scores)
                    })
                
                # Cost metrics
                total_cost = sum(
                    result.cost_data.get('total_cost_usd', 0.0)
                    for result in completed_results
                )
                framework_summary['total_cost_usd'] = total_cost
            
            summary['frameworks'][framework] = framework_summary
        
        return summary