#!/usr/bin/env python3
"""
AI Dev Squad Benchmark Suite

This module provides tools for benchmarking different AI agent orchestration frameworks
in a consistent manner. It implements the methodology defined in 
docs/benchmark/benchmark_methodology.md.
"""

import time
import os
import json
import logging
import argparse
import platform
import psutil
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("benchmark")

# Standard benchmark tasks
BENCHMARK_TASKS = {
    "simple_code_generation": {
        "task": "Build a Python function to calculate Fibonacci numbers",
        "requirements": [
            "Must handle negative numbers",
            "Should be optimized for performance using memoization",
            "Should include proper error handling",
            "Should have clear documentation"
        ],
        "language": "python"
    },
    "bug_fixing": {
        "task": "Fix the bugs in the following function that is supposed to find the longest palindromic substring",
        "code": """
def longest_palindrome(s):
    if not s:
        return ""
    
    start = 0
    max_len = 0
    
    for i in range(len(s)):
        # Check odd length palindromes
        left, right = i, i
        while left >= 0 and right < len(s) and s[left] == s[right]:
            if right - left + 1 > max_len:
                max_len = right - left + 1
                start = left
            left -= 1
            right += 1
        
        # Check even length palindromes
        left, right = i, i + 1
        while left >= 0 and right < len(s) and s[left] == s[right]:
            if right - left + 1 > max_len:
                max_len = right - left + 1
                start = left
            left -= 1
            right += 1
    
    return s[start:start+max_len-1]  # Bug: should be start+max_len
""",
        "requirements": [
            "Fix all bugs without changing the overall algorithm",
            "Ensure the function correctly handles all edge cases",
            "Maintain or improve the original time and space complexity"
        ],
        "language": "python"
    },
    "code_review": {
        "task": "Review the following code and provide feedback",
        "code": """
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] % 2 == 0:
            result.append(data[i] * 2)
        else:
            result.append(data[i] * 3)
    return result

def calculate_statistics(numbers):
    total = 0
    for num in numbers:
        total += num
    mean = total / len(numbers)
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    if n % 2 == 0:
        median = (sorted_numbers[n//2] + sorted_numbers[n//2 - 1]) / 2
    else:
        median = sorted_numbers[n//2]
    
    return {'mean': mean, 'median': median}

def main():
    data = [1, 2, 3, 4, 5]
    processed = process_data(data)
    stats = calculate_statistics(processed)
    print(f"Processed data: {processed}")
    print(f"Statistics: {stats}")

if __name__ == "__main__":
    main()
""",
        "requirements": [
            "Identify any performance issues",
            "Suggest improvements for code readability",
            "Identify potential bugs or edge cases",
            "Recommend best practices that should be applied"
        ],
        "language": "python"
    },
    "architecture_design": {
        "task": "Design a system for a real-time collaborative text editor",
        "requirements": [
            "Support multiple users editing the same document simultaneously",
            "Changes should be visible to all users in real-time",
            "System should handle conflict resolution",
            "Should be scalable to thousands of concurrent users",
            "Should maintain document history and support versioning"
        ]
    },
    "test_generation": {
        "task": "Generate comprehensive unit tests for the following code",
        "code": """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1
""",
        "requirements": [
            "Test all edge cases (empty array, single element, etc.)",
            "Test with various input types and sizes",
            "Ensure at least 95% code coverage",
            "Include performance tests for large arrays"
        ],
        "language": "python"
    },
    "documentation_generation": {
        "task": "Generate comprehensive documentation for the following code",
        "code": """
class Cache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.usage = []
    
    def get(self, key):
        if key in self.cache:
            self.usage.remove(key)
            self.usage.append(key)
            return self.cache[key]
        return -1
    
    def put(self, key, value):
        if key in self.cache:
            self.usage.remove(key)
        elif len(self.cache) >= self.capacity:
            oldest = self.usage.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = value
        self.usage.append(key)
""",
        "requirements": [
            "Include class and method descriptions",
            "Document parameters and return values",
            "Explain the algorithm and data structures used",
            "Provide usage examples"
        ],
        "language": "python"
    },
    "multi_agent_collaboration": {
        "task": "Design and implement a RESTful API for a blog platform",
        "requirements": [
            "Support CRUD operations for posts, comments, and users",
            "Implement authentication and authorization",
            "Include input validation and error handling",
            "Design should be scalable and follow best practices",
            "Include comprehensive documentation"
        ],
        "language": "python"
    }
}

class BenchmarkResult:
    """Class to store and process benchmark results."""
    
    def __init__(self, framework: str, task: str):
        self.framework = framework
        self.task = task
        self.timestamp = datetime.now()
        self.metrics = {
            "functional_performance": {},
            "resource_efficiency": {},
            "developer_experience": {},
            "integration_capabilities": {}
        }
        self.raw_data = {}
    
    def add_metric(self, category: str, name: str, value: Any):
        """Add a metric to the results."""
        if category in self.metrics:
            self.metrics[category][name] = value
        else:
            logger.warning(f"Unknown metric category: {category}")
    
    def add_raw_data(self, name: str, data: Any):
        """Add raw data to the results."""
        self.raw_data[name] = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "framework": self.framework,
            "task": self.task,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "raw_data": self.raw_data
        }
    
    def save(self, output_dir: str):
        """Save the result to a JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{self.framework}_{self.task}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        logger.info(f"Results saved to {filepath}")
        return filepath


class PerformanceTracker:
    """Utility to track performance metrics during benchmark execution."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.peak_memory = None
        self.api_calls = 0
        self.tokens_in = 0
        self.tokens_out = 0
    
    def start(self):
        """Start tracking performance."""
        self.start_time = time.time()
        self.start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        return self
    
    def update_memory(self):
        """Update peak memory usage."""
        current_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = max(self.peak_memory, current_memory)
    
    def record_api_call(self, tokens_in: int = 0, tokens_out: int = 0):
        """Record an API call with token counts."""
        self.api_calls += 1
        self.tokens_in += tokens_in
        self.tokens_out += tokens_out
        self.update_memory()
    
    def stop(self):
        """Stop tracking performance."""
        self.end_time = time.time()
        self.update_memory()
        return self
    
    def get_execution_time(self) -> float:
        """Get the execution time in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0
        return self.end_time - self.start_time
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        return {
            "start_memory_mb": self.start_memory,
            "peak_memory_mb": self.peak_memory,
            "memory_increase_mb": self.peak_memory - self.start_memory
        }
    
    def get_api_stats(self) -> Dict[str, int]:
        """Get API call statistics."""
        return {
            "api_calls": self.api_calls,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "total_tokens": self.tokens_in + self.tokens_out
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get all performance statistics."""
        return {
            "execution_time_seconds": self.get_execution_time(),
            **self.get_memory_usage(),
            **self.get_api_stats()
        }


class BenchmarkSuite:
    """Main benchmark suite for AI Dev Squad implementations."""
    
    def __init__(self, framework: str, implementation_dir: str, output_dir: str = "comparison-results"):
        self.framework = framework
        self.implementation_dir = implementation_dir
        self.output_dir = output_dir
        self.results = []
        
        # Ensure output directories exist
        os.makedirs(os.path.join(output_dir, "raw_data"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "analysis"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "visualizations"), exist_ok=True)
    
    def run_task(self, task_name: str, implementation_func: Callable, **kwargs) -> BenchmarkResult:
        """
        Run a benchmark task and collect metrics.
        
        Args:
            task_name: Name of the task from BENCHMARK_TASKS
            implementation_func: Function that implements the task for the framework
            **kwargs: Additional arguments to pass to the implementation function
            
        Returns:
            BenchmarkResult object with collected metrics
        """
        if task_name not in BENCHMARK_TASKS:
            raise ValueError(f"Unknown task: {task_name}")
        
        task_config = BENCHMARK_TASKS[task_name]
        result = BenchmarkResult(self.framework, task_name)
        
        # Record system info
        result.add_raw_data("system_info", {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "total_memory_gb": psutil.virtual_memory().total / (1024**3)
        })
        
        # Record task configuration
        result.add_raw_data("task_config", task_config)
        
        # Track performance
        tracker = PerformanceTracker().start()
        
        try:
            # Run the implementation
            implementation_result = implementation_func(task_config, tracker, **kwargs)
            result.add_raw_data("implementation_result", implementation_result)
            
            # Record success
            result.add_metric("functional_performance", "task_completed", True)
            
            # Evaluate output quality (placeholder - would be done by experts or automated tools)
            # This is a simplified example - real evaluation would be more sophisticated
            if "output_quality" in implementation_result:
                result.add_metric("functional_performance", "output_quality", 
                                 implementation_result["output_quality"])
            else:
                # Placeholder for quality evaluation
                result.add_metric("functional_performance", "output_quality", 7.5)
            
        except Exception as e:
            logger.exception(f"Error running task {task_name}")
            result.add_metric("functional_performance", "task_completed", False)
            result.add_metric("functional_performance", "error", str(e))
            result.add_raw_data("error", str(e))
        
        # Stop performance tracking
        tracker.stop()
        
        # Record resource efficiency metrics
        stats = tracker.get_all_stats()
        for key, value in stats.items():
            result.add_metric("resource_efficiency", key, value)
        
        # Calculate estimated cost (very simplified example)
        token_cost_per_1k = 0.002  # Example cost per 1K tokens
        estimated_cost = (stats["total_tokens"] / 1000) * token_cost_per_1k
        result.add_metric("resource_efficiency", "estimated_cost_usd", estimated_cost)
        
        # Save the result
        result.save(os.path.join(self.output_dir, "raw_data"))
        self.results.append(result)
        
        return result
    
    def run_all_tasks(self, implementation_funcs: Dict[str, Callable], **kwargs) -> List[BenchmarkResult]:
        """
        Run all benchmark tasks.
        
        Args:
            implementation_funcs: Dictionary mapping task names to implementation functions
            **kwargs: Additional arguments to pass to all implementation functions
            
        Returns:
            List of BenchmarkResult objects
        """
        results = []
        
        for task_name in BENCHMARK_TASKS:
            if task_name in implementation_funcs:
                logger.info(f"Running task: {task_name}")
                result = self.run_task(task_name, implementation_funcs[task_name], **kwargs)
                results.append(result)
            else:
                logger.warning(f"No implementation function for task: {task_name}")
        
        return results
    
    def generate_report(self, output_format: str = "markdown") -> str:
        """
        Generate a report of benchmark results.
        
        Args:
            output_format: Format of the report ("markdown", "json", or "html")
            
        Returns:
            Report as a string in the specified format
        """
        if not self.results:
            return "No benchmark results available."
        
        if output_format == "json":
            report = {
                "framework": self.framework,
                "timestamp": datetime.now().isoformat(),
                "results": [result.to_dict() for result in self.results]
            }
            return json.dumps(report, indent=2)
        
        elif output_format == "markdown":
            lines = [
                f"# Benchmark Results: {self.framework}",
                f"Generated: {datetime.now().isoformat()}",
                "",
                "## Summary",
                "",
                "| Task | Completed | Execution Time (s) | Memory (MB) | Tokens | Est. Cost ($) |",
                "|------|-----------|-------------------|-------------|--------|--------------|"
            ]
            
            for result in self.results:
                metrics = result.metrics
                completed = metrics["functional_performance"].get("task_completed", False)
                exec_time = metrics["resource_efficiency"].get("execution_time_seconds", 0)
                memory = metrics["resource_efficiency"].get("peak_memory_mb", 0)
                tokens = metrics["resource_efficiency"].get("total_tokens", 0)
                cost = metrics["resource_efficiency"].get("estimated_cost_usd", 0)
                
                lines.append(f"| {result.task} | {'✅' if completed else '❌'} | {exec_time:.2f} | {memory:.2f} | {tokens} | ${cost:.4f} |")
            
            lines.extend([
                "",
                "## Detailed Results",
                ""
            ])
            
            for result in self.results:
                lines.extend([
                    f"### {result.task}",
                    "",
                    "#### Functional Performance",
                    ""
                ])
                
                for name, value in result.metrics["functional_performance"].items():
                    lines.append(f"- **{name}**: {value}")
                
                lines.extend([
                    "",
                    "#### Resource Efficiency",
                    ""
                ])
                
                for name, value in result.metrics["resource_efficiency"].items():
                    if isinstance(value, float):
                        lines.append(f"- **{name}**: {value:.4f}")
                    else:
                        lines.append(f"- **{name}**: {value}")
                
                lines.append("")
            
            return "\n".join(lines)
        
        elif output_format == "html":
            # Simple HTML report
            html = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                f"<title>Benchmark Results: {self.framework}</title>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                "table { border-collapse: collapse; width: 100%; }",
                "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
                "th { background-color: #f2f2f2; }",
                "tr:nth-child(even) { background-color: #f9f9f9; }",
                "h1, h2, h3 { color: #333; }",
                "</style>",
                "</head>",
                "<body>",
                f"<h1>Benchmark Results: {self.framework}</h1>",
                f"<p>Generated: {datetime.now().isoformat()}</p>",
                "<h2>Summary</h2>",
                "<table>",
                "<tr><th>Task</th><th>Completed</th><th>Execution Time (s)</th><th>Memory (MB)</th><th>Tokens</th><th>Est. Cost ($)</th></tr>"
            ]
            
            for result in self.results:
                metrics = result.metrics
                completed = metrics["functional_performance"].get("task_completed", False)
                exec_time = metrics["resource_efficiency"].get("execution_time_seconds", 0)
                memory = metrics["resource_efficiency"].get("peak_memory_mb", 0)
                tokens = metrics["resource_efficiency"].get("total_tokens", 0)
                cost = metrics["resource_efficiency"].get("estimated_cost_usd", 0)
                
                html.append(f"<tr><td>{result.task}</td><td>{'✅' if completed else '❌'}</td><td>{exec_time:.2f}</td><td>{memory:.2f}</td><td>{tokens}</td><td>${cost:.4f}</td></tr>")
            
            html.append("</table>")
            
            for result in self.results:
                html.extend([
                    f"<h2>{result.task}</h2>",
                    "<h3>Functional Performance</h3>",
                    "<ul>"
                ])
                
                for name, value in result.metrics["functional_performance"].items():
                    html.append(f"<li><strong>{name}</strong>: {value}</li>")
                
                html.extend([
                    "</ul>",
                    "<h3>Resource Efficiency</h3>",
                    "<ul>"
                ])
                
                for name, value in result.metrics["resource_efficiency"].items():
                    if isinstance(value, float):
                        html.append(f"<li><strong>{name}</strong>: {value:.4f}</li>")
                    else:
                        html.append(f"<li><strong>{name}</strong>: {value}</li>")
                
                html.append("</ul>")
            
            html.extend([
                "</body>",
                "</html>"
            ])
            
            return "\n".join(html)
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def save_report(self, output_format: str = "markdown") -> str:
        """
        Generate and save a report of benchmark results.
        
        Args:
            output_format: Format of the report ("markdown", "json", or "html")
            
        Returns:
            Path to the saved report file
        """
        report = self.generate_report(output_format)
        
        os.makedirs(os.path.join(self.output_dir, "reports"), exist_ok=True)
        filename = f"{self.framework}_benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}"
        if output_format == "markdown":
            filename = filename.replace(".markdown", ".md")
        
        filepath = os.path.join(self.output_dir, "reports", filename)
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        logger.info(f"Report saved to {filepath}")
        return filepath
    
    def generate_visualizations(self):
        """Generate visualizations of benchmark results."""
        if not self.results:
            logger.warning("No results to visualize")
            return
        
        os.makedirs(os.path.join(self.output_dir, "visualizations"), exist_ok=True)
        
        # Prepare data for visualization
        tasks = []
        exec_times = []
        memory_usages = []
        token_counts = []
        
        for result in self.results:
            if result.metrics["functional_performance"].get("task_completed", False):
                tasks.append(result.task)
                exec_times.append(result.metrics["resource_efficiency"].get("execution_time_seconds", 0))
                memory_usages.append(result.metrics["resource_efficiency"].get("peak_memory_mb", 0))
                token_counts.append(result.metrics["resource_efficiency"].get("total_tokens", 0))
        
        if not tasks:
            logger.warning("No successful tasks to visualize")
            return
        
        # Create execution time chart
        plt.figure(figsize=(10, 6))
        plt.bar(tasks, exec_times)
        plt.title(f"{self.framework}: Execution Time by Task")
        plt.xlabel("Task")
        plt.ylabel("Execution Time (seconds)")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "visualizations", f"{self.framework}_execution_time.png"))
        plt.close()
        
        # Create memory usage chart
        plt.figure(figsize=(10, 6))
        plt.bar(tasks, memory_usages)
        plt.title(f"{self.framework}: Peak Memory Usage by Task")
        plt.xlabel("Task")
        plt.ylabel("Memory Usage (MB)")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "visualizations", f"{self.framework}_memory_usage.png"))
        plt.close()
        
        # Create token count chart
        plt.figure(figsize=(10, 6))
        plt.bar(tasks, token_counts)
        plt.title(f"{self.framework}: Token Usage by Task")
        plt.xlabel("Task")
        plt.ylabel("Token Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "visualizations", f"{self.framework}_token_usage.png"))
        plt.close()
        
        logger.info(f"Visualizations saved to {os.path.join(self.output_dir, 'visualizations')}")


def main():
    """Main function to run the benchmark suite from the command line."""
    parser = argparse.ArgumentParser(description="AI Dev Squad Benchmark Suite")
    parser.add_argument("framework", help="Name of the framework to benchmark")
    parser.add_argument("implementation_dir", help="Path to the implementation directory")
    parser.add_argument("--output-dir", default="comparison-results", help="Output directory for results")
    parser.add_argument("--task", help="Run a specific task (default: all tasks)")
    parser.add_argument("--format", choices=["markdown", "json", "html"], default="markdown", help="Output format for the report")
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations")
    
    args = parser.parse_args()
    
    logger.info(f"Benchmarking {args.framework} implementation")
    
    # This is a placeholder - in a real implementation, we would dynamically load
    # the framework-specific implementation functions
    logger.warning("This is a placeholder implementation. In a real scenario, you would need to implement framework-specific functions.")
    
    # Example of how this might be used:
    """
    # Import the framework-specific implementation
    sys.path.append(args.implementation_dir)
    from benchmark_impl import get_implementation_functions
    
    # Get the implementation functions
    implementation_funcs = get_implementation_functions()
    
    # Create and run the benchmark suite
    suite = BenchmarkSuite(args.framework, args.implementation_dir, args.output_dir)
    
    if args.task:
        if args.task in implementation_funcs:
            suite.run_task(args.task, implementation_funcs[args.task])
        else:
            logger.error(f"No implementation function for task: {args.task}")
    else:
        suite.run_all_tasks(implementation_funcs)
    
    # Generate and save the report
    suite.save_report(args.format)
    
    # Generate visualizations if requested
    if args.visualize:
        suite.generate_visualizations()
    """


if __name__ == "__main__":
    main()