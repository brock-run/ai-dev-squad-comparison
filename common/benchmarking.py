#!/usr/bin/env python3
"""
Advanced Benchmarking System for AI Dev Squad

This module provides comprehensive benchmarking capabilities for AI agent frameworks,
including performance testing, quality assessment, cost analysis, and comparative evaluation.
"""

import os
import json
import time
import logging
import asyncio
import statistics
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Iterator
from enum import Enum
from pathlib import Path
import hashlib
import concurrent.futures
from contextlib import contextmanager

# Import our enhanced systems
try:
    from .ollama_integration import create_agent, TaskType, EnhancedAgentInterface
    from .telemetry import get_logger, get_trace_manager, get_cost_tracker
    from .caching import get_cache
    from .context_management import get_context_manager, ContextStrategy, MessageImportance
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False
    logging.warning("Enhanced features not available for benchmarking")

# Configure logging
logger = logging.getLogger("ai_dev_squad.benchmarking")


class BenchmarkType(Enum):
    """Types of benchmarks that can be performed."""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COST = "cost"
    SCALABILITY = "scalability"
    RELIABILITY = "reliability"
    FEATURE_PARITY = "feature_parity"
    USER_EXPERIENCE = "user_experience"
    INTEGRATION = "integration"


class BenchmarkStatus(Enum):
    """Status of benchmark execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MetricType(Enum):
    """Types of metrics that can be collected."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ACCURACY = "accuracy"
    COST_PER_REQUEST = "cost_per_request"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    QUALITY_SCORE = "quality_score"
    TOKEN_EFFICIENCY = "token_efficiency"


@dataclass
class BenchmarkTask:
    """Represents a single benchmark task."""
    task_id: str
    name: str
    description: str
    task_type: TaskType
    prompt: str
    expected_output: Optional[str] = None
    evaluation_criteria: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    importance: MessageImportance = MessageImportance.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['task_type'] = self.task_type.value
        result['importance'] = self.importance.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkTask':
        """Create from dictionary."""
        data['task_type'] = TaskType(data['task_type'])
        data['importance'] = MessageImportance(data['importance'])
        return cls(**data)


@dataclass
class BenchmarkResult:
    """Results from executing a benchmark task."""
    task_id: str
    framework: str
    agent_role: str
    model_name: str
    start_time: datetime
    end_time: datetime
    status: BenchmarkStatus
    response: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    quality_scores: Dict[str, float] = field(default_factory=dict)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    cost_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat()
        result['status'] = self.status.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResult':
        """Create from dictionary."""
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['status'] = BenchmarkStatus(data['status'])
        return cls(**data)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark tasks for comprehensive testing."""
    suite_id: str
    name: str
    description: str
    tasks: List[BenchmarkTask]
    frameworks: List[str]
    benchmark_types: List[BenchmarkType]
    configuration: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['tasks'] = [task.to_dict() for task in self.tasks]
        result['benchmark_types'] = [bt.value for bt in self.benchmark_types]
        result['created_at'] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkSuite':
        """Create from dictionary."""
        data['tasks'] = [BenchmarkTask.from_dict(task) for task in data['tasks']]
        data['benchmark_types'] = [BenchmarkType(bt) for bt in data['benchmark_types']]
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


# Convenience functions for common benchmark operations

def create_comprehensive_benchmark_suite(frameworks: List[str]) -> BenchmarkSuite:
    """Create a comprehensive benchmark suite with all task types."""
    from .benchmarking_tasks import BenchmarkSuiteBuilder
    
    builder = BenchmarkSuiteBuilder()
    
    suite = (builder
             .add_coding_tasks()
             .add_architecture_tasks()
             .add_testing_tasks()
             .add_debugging_tasks()
             .add_documentation_tasks()
             .add_frameworks(frameworks)
             .add_configuration({
                 'timeout_seconds': 300,
                 'parallel_execution': True,
                 'max_workers': 4,
                 'enable_caching': True,
                 'enable_tracing': True
             })
             .build(
                 suite_id="comprehensive_v1",
                 name="Comprehensive Framework Benchmark",
                 description="Complete benchmark suite testing all major capabilities across AI frameworks"
             ))
    
    return suite


def run_quick_benchmark(frameworks: List[str], results_dir: str = None) -> Dict[str, Any]:
    """Run a quick benchmark with essential tasks."""
    from .benchmarking_runner import BenchmarkRunner
    from .benchmarking_tasks import create_quick_suite
    
    # Create a smaller suite for quick testing
    suite = create_quick_suite(frameworks)
    
    # Run the benchmark
    runner = BenchmarkRunner(results_dir)
    results = runner.run_benchmark_suite(suite, parallel=True, max_workers=2)
    
    return {
        'suite': suite,
        'results': results,
        'summary': runner._generate_summary(results)
    }


def analyze_benchmark_results(results_file: str, results_dir: str = None) -> Dict[str, Any]:
    """Analyze benchmark results and generate insights."""
    from .benchmarking_analyzer import BenchmarkAnalyzer
    
    analyzer = BenchmarkAnalyzer(results_dir)
    results_data = analyzer.load_results(results_file)
    
    return {
        'comparison': analyzer.compare_frameworks(results_data),
        'task_analysis': analyzer.analyze_task_performance(results_data),
        'outliers': analyzer.find_performance_outliers(results_data),
        'report': analyzer.generate_report(results_data)
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Available frameworks (would be detected dynamically in real usage)
    available_frameworks = ["langgraph", "crewai", "haystack", "autogen"]
    
    print("Creating comprehensive benchmark suite...")
    suite = create_comprehensive_benchmark_suite(available_frameworks)
    
    print(f"Created suite with {len(suite.tasks)} tasks for {len(suite.frameworks)} frameworks")
    print(f"Benchmark types: {[bt.value for bt in suite.benchmark_types]}")
    
    # Run quick benchmark for demonstration
    print("\nRunning quick benchmark...")
    quick_results = run_quick_benchmark(available_frameworks[:2])  # Test first 2 frameworks
    
    print(f"Quick benchmark completed with {len(quick_results['results'])} framework results")