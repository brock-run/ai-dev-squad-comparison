"""
Benchmark Task Definitions for AI Dev Squad Comparison

This module provides comprehensive benchmark tasks for evaluating AI agent frameworks
across different types of software development scenarios.
"""

from .base import BenchmarkTask, TaskCategory, DifficultyLevel, TaskResult
from .bugfix import BugfixTasks
from .feature_add import FeatureAddTasks
from .qa import QATasks
from .optimize import OptimizeTasks
from .edge_case import EdgeCaseTasks

__all__ = [
    'BenchmarkTask',
    'TaskCategory', 
    'DifficultyLevel',
    'TaskResult',
    'BugfixTasks',
    'FeatureAddTasks', 
    'QATasks',
    'OptimizeTasks',
    'EdgeCaseTasks'
]