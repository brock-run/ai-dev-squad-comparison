#!/usr/bin/env python3
"""
Base classes and definitions for benchmark tasks.

This module provides the foundation for all benchmark tasks, including
task definitions, categories, difficulty levels, and result structures.
"""

import os
import json
import time
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from pathlib import Path


class TaskCategory(Enum):
    """Categories of benchmark tasks."""
    BUGFIX = "bugfix"
    FEATURE_ADD = "feature_add"
    QA = "qa"
    OPTIMIZE = "optimize"
    EDGE_CASE = "edge_case"
    INTEGRATION = "integration"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"


class DifficultyLevel(Enum):
    """Difficulty levels for benchmark tasks."""
    TRIVIAL = "trivial"      # Simple, single-step tasks
    EASY = "easy"            # Basic tasks requiring 1-2 steps
    MEDIUM = "medium"        # Moderate complexity, 3-5 steps
    HARD = "hard"            # Complex tasks requiring multiple steps
    EXPERT = "expert"        # Very complex, multi-faceted tasks


class TaskStatus(Enum):
    """Status of task execution."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class TaskMetrics:
    """Metrics for task execution."""
    execution_time_seconds: float
    tokens_used: int
    api_calls_made: int
    memory_usage_mb: float
    success_rate: float
    quality_score: float
    efficiency_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TaskResult:
    """Result of a benchmark task execution."""
    task_id: str
    framework: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime]
    metrics: Optional[TaskMetrics]
    output: Optional[str]
    error_message: Optional[str]
    artifacts: Dict[str, Any]
    validation_results: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Create from dictionary."""
        data['status'] = TaskStatus(data['status'])
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        if data.get('metrics'):
            data['metrics'] = TaskMetrics(**data['metrics'])
        return cls(**data)


@dataclass
class BenchmarkTask:
    """Base class for all benchmark tasks."""
    
    # Task identification
    task_id: str
    name: str
    description: str
    category: TaskCategory
    difficulty: DifficultyLevel
    
    # Task specification
    input_files: Dict[str, str]  # filename -> content
    expected_outputs: Dict[str, str]  # filename -> expected content
    validation_criteria: Dict[str, Any]
    
    # Task configuration
    timeout_seconds: int = 300  # 5 minutes default
    max_iterations: int = 10
    requires_internet: bool = False
    
    # Metadata
    tags: List[str] = None
    author: str = "AI Dev Squad"
    created_at: datetime = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def get_task_hash(self) -> str:
        """Generate a unique hash for this task."""
        task_data = {
            'task_id': self.task_id,
            'input_files': self.input_files,
            'expected_outputs': self.expected_outputs,
            'validation_criteria': self.validation_criteria
        }
        task_json = json.dumps(task_data, sort_keys=True)
        return hashlib.sha256(task_json.encode()).hexdigest()[:16]
    
    def setup_workspace(self, workspace_path: Path) -> None:
        """
        Set up the workspace for task execution.
        
        Args:
            workspace_path: Path to the workspace directory.
        """
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Create input files
        for filename, content in self.input_files.items():
            file_path = workspace_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
    
    def validate_output(self, workspace_path: Path) -> Dict[str, Any]:
        """
        Validate the task output against expected results.
        
        Args:
            workspace_path: Path to the workspace directory.
            
        Returns:
            Validation results dictionary.
        """
        results = {
            'overall_success': True,
            'file_validations': {},
            'criteria_validations': {},
            'score': 0.0
        }
        
        total_checks = 0
        passed_checks = 0
        
        # Validate expected output files
        for filename, expected_content in self.expected_outputs.items():
            total_checks += 1
            file_path = workspace_path / filename
            
            if not file_path.exists():
                results['file_validations'][filename] = {
                    'exists': False,
                    'content_match': False,
                    'error': f"Expected file {filename} not found"
                }
                results['overall_success'] = False
            else:
                actual_content = file_path.read_text()
                content_match = self._compare_content(expected_content, actual_content)
                
                results['file_validations'][filename] = {
                    'exists': True,
                    'content_match': content_match,
                    'similarity_score': self._calculate_similarity(expected_content, actual_content)
                }
                
                if content_match:
                    passed_checks += 1
                else:
                    results['overall_success'] = False
        
        # Validate custom criteria
        for criterion_name, criterion_config in self.validation_criteria.items():
            total_checks += 1
            criterion_result = self._validate_criterion(
                criterion_name, 
                criterion_config, 
                workspace_path
            )
            
            results['criteria_validations'][criterion_name] = criterion_result
            
            if criterion_result.get('passed', False):
                passed_checks += 1
            else:
                results['overall_success'] = False
        
        # Calculate overall score
        results['score'] = passed_checks / total_checks if total_checks > 0 else 0.0
        results['passed_checks'] = passed_checks
        results['total_checks'] = total_checks
        
        return results
    
    def _compare_content(self, expected: str, actual: str) -> bool:
        """
        Compare expected and actual content.
        
        Args:
            expected: Expected content.
            actual: Actual content.
            
        Returns:
            True if content matches sufficiently.
        """
        # Normalize whitespace and line endings
        expected_normalized = ' '.join(expected.split())
        actual_normalized = ' '.join(actual.split())
        
        # For exact matches
        if expected_normalized == actual_normalized:
            return True
        
        # For code, check if key elements are present
        if self.category in [TaskCategory.BUGFIX, TaskCategory.FEATURE_ADD]:
            return self._validate_code_content(expected, actual)
        
        # For other content, use similarity threshold
        similarity = self._calculate_similarity(expected, actual)
        return similarity >= 0.8
    
    def _validate_code_content(self, expected: str, actual: str) -> bool:
        """
        Validate code content with more flexible matching.
        
        Args:
            expected: Expected code.
            actual: Actual code.
            
        Returns:
            True if code is functionally equivalent.
        """
        # Extract key code elements (functions, classes, imports)
        expected_elements = self._extract_code_elements(expected)
        actual_elements = self._extract_code_elements(actual)
        
        # Check if all expected elements are present
        for element in expected_elements:
            if element not in actual_elements:
                return False
        
        return True
    
    def _extract_code_elements(self, code: str) -> List[str]:
        """
        Extract key elements from code for comparison.
        
        Args:
            code: Source code.
            
        Returns:
            List of key code elements.
        """
        elements = []
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            # Extract function definitions
            if line.startswith('def '):
                elements.append(line.split('(')[0])
            # Extract class definitions
            elif line.startswith('class '):
                elements.append(line.split('(')[0].split(':')[0])
            # Extract imports
            elif line.startswith('import ') or line.startswith('from '):
                elements.append(line)
        
        return elements
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text.
            text2: Second text.
            
        Returns:
            Similarity score between 0 and 1.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _validate_criterion(self, name: str, config: Dict[str, Any], 
                          workspace_path: Path) -> Dict[str, Any]:
        """
        Validate a custom criterion.
        
        Args:
            name: Criterion name.
            config: Criterion configuration.
            workspace_path: Workspace path.
            
        Returns:
            Validation result.
        """
        criterion_type = config.get('type', 'file_exists')
        
        if criterion_type == 'file_exists':
            return self._validate_file_exists(config, workspace_path)
        elif criterion_type == 'file_contains':
            return self._validate_file_contains(config, workspace_path)
        elif criterion_type == 'no_syntax_errors':
            return self._validate_no_syntax_errors(config, workspace_path)
        elif criterion_type == 'test_passes':
            return self._validate_test_passes(config, workspace_path)
        else:
            return {
                'passed': False,
                'error': f"Unknown criterion type: {criterion_type}"
            }
    
    def _validate_file_exists(self, config: Dict[str, Any], 
                            workspace_path: Path) -> Dict[str, Any]:
        """Validate that a file exists."""
        filename = config.get('filename')
        if not filename:
            return {'passed': False, 'error': 'No filename specified'}
        
        file_path = workspace_path / filename
        exists = file_path.exists()
        
        return {
            'passed': exists,
            'message': f"File {filename} {'exists' if exists else 'does not exist'}"
        }
    
    def _validate_file_contains(self, config: Dict[str, Any], 
                              workspace_path: Path) -> Dict[str, Any]:
        """Validate that a file contains specific content."""
        filename = config.get('filename')
        content = config.get('content')
        
        if not filename or not content:
            return {'passed': False, 'error': 'Missing filename or content'}
        
        file_path = workspace_path / filename
        if not file_path.exists():
            return {'passed': False, 'error': f"File {filename} does not exist"}
        
        file_content = file_path.read_text()
        contains = content in file_content
        
        return {
            'passed': contains,
            'message': f"File {filename} {'contains' if contains else 'does not contain'} required content"
        }
    
    def _validate_no_syntax_errors(self, config: Dict[str, Any], 
                                 workspace_path: Path) -> Dict[str, Any]:
        """Validate that Python files have no syntax errors."""
        filename = config.get('filename')
        if not filename:
            return {'passed': False, 'error': 'No filename specified'}
        
        file_path = workspace_path / filename
        if not file_path.exists():
            return {'passed': False, 'error': f"File {filename} does not exist"}
        
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), filename, 'exec')
            return {'passed': True, 'message': f"File {filename} has no syntax errors"}
        except SyntaxError as e:
            return {
                'passed': False, 
                'error': f"Syntax error in {filename}: {e}"
            }
    
    def _validate_test_passes(self, config: Dict[str, Any], 
                            workspace_path: Path) -> Dict[str, Any]:
        """Validate that tests pass."""
        test_command = config.get('command', 'python -m pytest')
        
        try:
            import subprocess
            result = subprocess.run(
                test_command.split(),
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            passed = result.returncode == 0
            
            return {
                'passed': passed,
                'message': f"Tests {'passed' if passed else 'failed'}",
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {'passed': False, 'error': 'Test execution timed out'}
        except Exception as e:
            return {'passed': False, 'error': f"Test execution error: {e}"}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        result = asdict(self)
        result['category'] = self.category.value
        result['difficulty'] = self.difficulty.value
        result['created_at'] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkTask':
        """Create task from dictionary."""
        data['category'] = TaskCategory(data['category'])
        data['difficulty'] = DifficultyLevel(data['difficulty'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class TaskRegistry:
    """Registry for managing benchmark tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, BenchmarkTask] = {}
        self.tasks_by_category: Dict[TaskCategory, List[BenchmarkTask]] = {}
        self.tasks_by_difficulty: Dict[DifficultyLevel, List[BenchmarkTask]] = {}
    
    def register_task(self, task: BenchmarkTask) -> None:
        """Register a new task."""
        self.tasks[task.task_id] = task
        
        # Add to category index
        if task.category not in self.tasks_by_category:
            self.tasks_by_category[task.category] = []
        self.tasks_by_category[task.category].append(task)
        
        # Add to difficulty index
        if task.difficulty not in self.tasks_by_difficulty:
            self.tasks_by_difficulty[task.difficulty] = []
        self.tasks_by_difficulty[task.difficulty].append(task)
    
    def get_task(self, task_id: str) -> Optional[BenchmarkTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_tasks_by_category(self, category: TaskCategory) -> List[BenchmarkTask]:
        """Get all tasks in a category."""
        return self.tasks_by_category.get(category, [])
    
    def get_tasks_by_difficulty(self, difficulty: DifficultyLevel) -> List[BenchmarkTask]:
        """Get all tasks at a difficulty level."""
        return self.tasks_by_difficulty.get(difficulty, [])
    
    def get_all_tasks(self) -> List[BenchmarkTask]:
        """Get all registered tasks."""
        return list(self.tasks.values())
    
    def filter_tasks(self, 
                    categories: List[TaskCategory] = None,
                    difficulties: List[DifficultyLevel] = None,
                    tags: List[str] = None) -> List[BenchmarkTask]:
        """Filter tasks by criteria."""
        filtered_tasks = []
        
        for task in self.tasks.values():
            # Filter by category
            if categories and task.category not in categories:
                continue
            
            # Filter by difficulty
            if difficulties and task.difficulty not in difficulties:
                continue
            
            # Filter by tags
            if tags and not any(tag in task.tags for tag in tags):
                continue
            
            filtered_tasks.append(task)
        
        return filtered_tasks


# Global task registry
_task_registry = TaskRegistry()


def get_task_registry() -> TaskRegistry:
    """Get the global task registry."""
    return _task_registry


def register_task(task: BenchmarkTask) -> None:
    """Register a task with the global registry."""
    _task_registry.register_task(task)