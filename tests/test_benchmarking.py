#!/usr/bin/env python3
"""
Tests for the Advanced Benchmarking System

This module contains comprehensive tests for the benchmarking framework,
including task creation, execution, analysis, and reporting.
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import benchmarking modules
from common.benchmarking import (
    BenchmarkTask, BenchmarkResult, BenchmarkSuite, BenchmarkType, BenchmarkStatus,
    MetricType, TaskType, MessageImportance, create_comprehensive_benchmark_suite,
    run_quick_benchmark, analyze_benchmark_results
)
from common.benchmarking_tasks import BenchmarkSuiteBuilder, create_quick_suite
from common.benchmarking_runner import BenchmarkRunner, QualityEvaluator, PerformanceProfiler
from common.benchmarking_analyzer import BenchmarkAnalyzer


class TestBenchmarkDataStructures(unittest.TestCase):
    """Test benchmark data structures and serialization."""
    
    def test_benchmark_task_creation(self):
        """Test BenchmarkTask creation and serialization."""
        task = BenchmarkTask(
            task_id="test_001",
            name="Test Task",
            description="A test task",
            task_type=TaskType.CODING,
            prompt="Write a hello world function",
            expected_output="def hello_world():",
            evaluation_criteria={
                'length_check': {'min_length': 50, 'max_length': 200},
                'keyword_presence': {'required': ['def', 'hello']}
            },
            timeout_seconds=120,
            importance=MessageImportance.HIGH
        )
        
        # Test basic properties
        self.assertEqual(task.task_id, "test_001")
        self.assertEqual(task.task_type, TaskType.CODING)
        self.assertEqual(task.importance, MessageImportance.HIGH)
        
        # Test serialization
        task_dict = task.to_dict()
        self.assertIsInstance(task_dict, dict)
        self.assertEqual(task_dict['task_type'], 'coding')
        self.assertEqual(task_dict['importance'], 'high')
        
        # Test deserialization
        restored_task = BenchmarkTask.from_dict(task_dict)
        self.assertEqual(restored_task.task_id, task.task_id)
        self.assertEqual(restored_task.task_type, task.task_type)
        self.assertEqual(restored_task.importance, task.importance)
    
    def test_benchmark_result_creation(self):
        """Test BenchmarkResult creation and serialization."""
        start_time = datetime.now()
        end_time = datetime.now()
        
        result = BenchmarkResult(
            task_id="test_001",
            framework="test_framework",
            agent_role="developer",
            model_name="test_model",
            start_time=start_time,
            end_time=end_time,
            status=BenchmarkStatus.COMPLETED,
            response="def hello_world(): return 'Hello, World!'",
            metrics={'response_time': 1.5, 'quality_score': 8.5},
            quality_scores={'overall': 8.5, 'code_quality': 9.0},
            performance_data={'memory_usage': 10.5},
            cost_data={'total_cost_usd': 0.001}
        )
        
        # Test basic properties
        self.assertEqual(result.task_id, "test_001")
        self.assertEqual(result.status, BenchmarkStatus.COMPLETED)
        self.assertGreater(result.duration_seconds, 0)
        
        # Test serialization
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['status'], 'completed')
        
        # Test deserialization
        restored_result = BenchmarkResult.from_dict(result_dict)
        self.assertEqual(restored_result.task_id, result.task_id)
        self.assertEqual(restored_result.status, result.status)
    
    def test_benchmark_suite_creation(self):
        """Test BenchmarkSuite creation and serialization."""
        tasks = [
            BenchmarkTask(
                task_id="task_001",
                name="Task 1",
                description="First task",
                task_type=TaskType.CODING,
                prompt="Write a function"
            ),
            BenchmarkTask(
                task_id="task_002",
                name="Task 2",
                description="Second task",
                task_type=TaskType.TESTING,
                prompt="Write a test"
            )
        ]
        
        suite = BenchmarkSuite(
            suite_id="test_suite",
            name="Test Suite",
            description="A test benchmark suite",
            tasks=tasks,
            frameworks=["framework1", "framework2"],
            benchmark_types=[BenchmarkType.PERFORMANCE, BenchmarkType.QUALITY],
            configuration={'timeout': 300}
        )
        
        # Test basic properties
        self.assertEqual(suite.suite_id, "test_suite")
        self.assertEqual(len(suite.tasks), 2)
        self.assertEqual(len(suite.frameworks), 2)
        
        # Test serialization
        suite_dict = suite.to_dict()
        self.assertIsInstance(suite_dict, dict)
        self.assertEqual(len(suite_dict['tasks']), 2)
        
        # Test deserialization
        restored_suite = BenchmarkSuite.from_dict(suite_dict)
        self.assertEqual(restored_suite.suite_id, suite.suite_id)
        self.assertEqual(len(restored_suite.tasks), len(suite.tasks))


class TestBenchmarkSuiteBuilder(unittest.TestCase):
    """Test benchmark suite builder functionality."""
    
    def test_suite_builder_basic(self):
        """Test basic suite builder functionality."""
        builder = BenchmarkSuiteBuilder()
        
        suite = (builder
                .add_coding_tasks()
                .add_frameworks(["test_framework"])
                .build("test_suite", "Test Suite", "A test suite"))
        
        self.assertEqual(suite.suite_id, "test_suite")
        self.assertGreater(len(suite.tasks), 0)
        self.assertIn("test_framework", suite.frameworks)
        self.assertIn(BenchmarkType.PERFORMANCE, suite.benchmark_types)
    
    def test_suite_builder_all_tasks(self):
        """Test suite builder with all task types."""
        builder = BenchmarkSuiteBuilder()
        
        suite = (builder
                .add_coding_tasks()
                .add_architecture_tasks()
                .add_testing_tasks()
                .add_debugging_tasks()
                .add_documentation_tasks()
                .add_frameworks(["framework1", "framework2"])
                .add_configuration({'timeout': 600})
                .build("comprehensive_suite", "Comprehensive Suite", "All task types"))
        
        # Should have tasks from all categories
        task_types = {task.task_type for task in suite.tasks}
        self.assertIn(TaskType.CODING, task_types)
        self.assertIn(TaskType.ARCHITECTURE, task_types)
        self.assertIn(TaskType.TESTING, task_types)
        self.assertIn(TaskType.DEBUGGING, task_types)
        self.assertIn(TaskType.DOCUMENTATION, task_types)
        
        # Should have multiple benchmark types
        self.assertGreater(len(suite.benchmark_types), 1)
        
        # Should have configuration
        self.assertEqual(suite.configuration['timeout'], 600)
    
    def test_create_quick_suite(self):
        """Test quick suite creation."""
        frameworks = ["framework1", "framework2"]
        suite = create_quick_suite(frameworks)
        
        self.assertEqual(suite.suite_id, "quick_v1")
        self.assertEqual(suite.frameworks, frameworks)
        self.assertGreater(len(suite.tasks), 0)
        self.assertLess(len(suite.tasks), 10)  # Should be a small suite


class TestQualityEvaluator(unittest.TestCase):
    """Test quality evaluation functionality."""
    
    def setUp(self):
        self.evaluator = QualityEvaluator()
        self.sample_task = BenchmarkTask(
            task_id="eval_test",
            name="Evaluation Test",
            description="Test task for evaluation",
            task_type=TaskType.CODING,
            prompt="Write a function",
            evaluation_criteria={
                'length_check': {'min_length': 50, 'max_length': 200, 'optimal_length': 100},
                'keyword_presence': {'required': ['def', 'return'], 'forbidden': ['import']},
                'structure_check': {'expect_code': True},
                'code_quality': {},
                'completeness': {'expected_elements': ['function definition', 'return statement']}
            }
        )
    
    def test_length_evaluation(self):
        """Test length-based evaluation."""
        # Test optimal length
        response = "def test_function():\n    return 'Hello, World!'\n\n# This is a simple test function"
        scores = self.evaluator.evaluate_response(self.sample_task, response)
        self.assertIn('length_check', scores)
        self.assertGreater(scores['length_check'], 5.0)
        
        # Test too short
        short_response = "def test(): return 1"
        scores = self.evaluator.evaluate_response(self.sample_task, short_response)
        self.assertEqual(scores['length_check'], 2.0)
        
        # Test too long
        long_response = "def test():\n" + "    # comment\n" * 100 + "    return 1"
        scores = self.evaluator.evaluate_response(self.sample_task, long_response)
        self.assertEqual(scores['length_check'], 3.0)
    
    def test_keyword_evaluation(self):
        """Test keyword presence evaluation."""
        # Test with required keywords
        good_response = "def test_function():\n    return 'Hello'"
        scores = self.evaluator.evaluate_response(self.sample_task, good_response)
        self.assertIn('keyword_presence', scores)
        self.assertGreater(scores['keyword_presence'], 7.0)
        
        # Test with forbidden keywords
        bad_response = "import os\ndef test_function():\n    return 'Hello'"
        scores = self.evaluator.evaluate_response(self.sample_task, bad_response)
        self.assertLess(scores['keyword_presence'], 7.0)
        
        # Test missing required keywords
        missing_response = "print('Hello, World!')"
        scores = self.evaluator.evaluate_response(self.sample_task, missing_response)
        self.assertLess(scores['keyword_presence'], 6.0)
    
    def test_structure_evaluation(self):
        """Test structure-based evaluation."""
        # Test with expected code structure
        code_response = "def test_function():\n    return 'Hello'"
        scores = self.evaluator.evaluate_response(self.sample_task, code_response)
        self.assertIn('structure_check', scores)
        self.assertGreater(scores['structure_check'], 6.0)
        
        # Test without expected code structure
        text_response = "This is just text without code"
        scores = self.evaluator.evaluate_response(self.sample_task, text_response)
        self.assertLess(scores['structure_check'], 4.0)
    
    def test_overall_score_calculation(self):
        """Test overall score calculation."""
        response = "def test_function():\n    return 'Hello, World!'"
        scores = self.evaluator.evaluate_response(self.sample_task, response)
        
        self.assertIn('overall', scores)
        self.assertGreater(scores['overall'], 0.0)
        self.assertLessEqual(scores['overall'], 10.0)
        
        # Overall should be average of individual scores
        individual_scores = [v for k, v in scores.items() if k != 'overall']
        expected_overall = sum(individual_scores) / len(individual_scores)
        self.assertAlmostEqual(scores['overall'], expected_overall, places=1)


class TestPerformanceProfiler(unittest.TestCase):
    """Test performance profiling functionality."""
    
    def setUp(self):
        self.profiler = PerformanceProfiler()
    
    def test_profile_execution(self):
        """Test execution profiling context manager."""
        task_id = "profile_test"
        
        with self.profiler.profile_execution(task_id) as profile_data:
            # Simulate some work
            import time
            time.sleep(0.1)
            
            # Check that profile data is being collected
            self.assertIn('start_time', profile_data)
            self.assertIn('start_memory', profile_data)
            self.assertIn('start_cpu', profile_data)
        
        # Check that final profile data is available
        final_data = self.profiler.get_profile_data(task_id)
        self.assertIsNotNone(final_data)
        self.assertIn('duration', final_data)
        self.assertGreater(final_data['duration'], 0.05)  # Should be at least 0.05 seconds
    
    def test_memory_and_cpu_tracking(self):
        """Test memory and CPU usage tracking."""
        memory_usage = self.profiler._get_memory_usage()
        cpu_usage = self.profiler._get_cpu_usage()
        
        # Should return numeric values (or 0.0 if psutil not available)
        self.assertIsInstance(memory_usage, float)
        self.assertIsInstance(cpu_usage, float)
        self.assertGreaterEqual(memory_usage, 0.0)
        self.assertGreaterEqual(cpu_usage, 0.0)


class TestBenchmarkRunner(unittest.TestCase):
    """Test benchmark runner functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.runner = BenchmarkRunner(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('common.benchmarking_runner.ENHANCED_FEATURES_AVAILABLE', False)
    def test_runner_initialization(self):
        """Test runner initialization without enhanced features."""
        runner = BenchmarkRunner(self.temp_dir)
        
        self.assertIsNotNone(runner.quality_evaluator)
        self.assertIsNotNone(runner.performance_profiler)
        self.assertIsNone(runner.logger)
        self.assertIsNone(runner.tracer)
    
    def test_create_agent_for_framework_without_enhanced_features(self):
        """Test agent creation when enhanced features are not available."""
        task = BenchmarkTask(
            task_id="test",
            name="Test",
            description="Test task",
            task_type=TaskType.CODING,
            prompt="Test prompt"
        )
        
        with patch('common.benchmarking_runner.ENHANCED_FEATURES_AVAILABLE', False):
            runner = BenchmarkRunner(self.temp_dir)
            
            with self.assertRaises(RuntimeError):
                runner._create_agent_for_framework("test_framework", task)
    
    def test_collect_metrics(self):
        """Test metrics collection."""
        task = BenchmarkTask(
            task_id="test",
            name="Test",
            description="Test task",
            task_type=TaskType.CODING,
            prompt="Test prompt"
        )
        
        # Mock agent
        mock_agent = Mock()
        
        # Mock profile data
        profile_data = {
            'duration': 1.5,
            'memory_delta': 10.0,
            'cpu_delta': 5.0
        }
        
        metrics = self.runner._collect_metrics(task, mock_agent, profile_data)
        
        self.assertIn('response_time', metrics)
        self.assertIn('memory_usage', metrics)
        self.assertIn('cpu_usage', metrics)
        self.assertIn('throughput', metrics)
        
        self.assertEqual(metrics['response_time'], 1.5)
        self.assertEqual(metrics['memory_usage'], 10.0)
        self.assertEqual(metrics['cpu_usage'], 5.0)
    
    def test_generate_summary(self):
        """Test summary generation."""
        # Create mock results
        results = {
            'framework1': [
                BenchmarkResult(
                    task_id="task1",
                    framework="framework1",
                    agent_role="developer",
                    model_name="model1",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    status=BenchmarkStatus.COMPLETED,
                    metrics={'response_time': 1.0},
                    quality_scores={'overall': 8.0}
                ),
                BenchmarkResult(
                    task_id="task2",
                    framework="framework1",
                    agent_role="developer",
                    model_name="model1",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    status=BenchmarkStatus.FAILED,
                    error_message="Test error"
                )
            ]
        }
        
        summary = self.runner._generate_summary(results)
        
        self.assertEqual(summary['total_frameworks'], 1)
        self.assertEqual(summary['total_tasks'], 2)
        self.assertIn('framework1', summary['frameworks'])
        
        framework_summary = summary['frameworks']['framework1']
        self.assertEqual(framework_summary['total_tasks'], 2)
        self.assertEqual(framework_summary['completed_tasks'], 1)
        self.assertEqual(framework_summary['failed_tasks'], 1)
        self.assertEqual(framework_summary['success_rate'], 0.5)


class TestBenchmarkAnalyzer(unittest.TestCase):
    """Test benchmark analysis functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = BenchmarkAnalyzer(self.temp_dir)
        
        # Create sample results data
        self.sample_results = {
            'suite': {
                'suite_id': 'test_suite',
                'name': 'Test Suite',
                'description': 'Test benchmark suite'
            },
            'results': {
                'framework1': [
                    {
                        'task_id': 'task1',
                        'framework': 'framework1',
                        'agent_role': 'developer',
                        'model_name': 'model1',
                        'start_time': '2024-01-01T10:00:00',
                        'end_time': '2024-01-01T10:00:02',
                        'status': 'completed',
                        'response': 'def hello(): return "Hello"',
                        'metrics': {'response_time': 2.0},
                        'quality_scores': {'overall': 8.5},
                        'performance_data': {},
                        'cost_data': {'total_cost_usd': 0.001},
                        'metadata': {'task_type': 'coding'}
                    }
                ],
                'framework2': [
                    {
                        'task_id': 'task1',
                        'framework': 'framework2',
                        'agent_role': 'developer',
                        'model_name': 'model2',
                        'start_time': '2024-01-01T10:00:00',
                        'end_time': '2024-01-01T10:00:01',
                        'status': 'completed',
                        'response': 'def hello(): return "Hi"',
                        'metrics': {'response_time': 1.0},
                        'quality_scores': {'overall': 7.5},
                        'performance_data': {},
                        'cost_data': {'total_cost_usd': 0.002},
                        'metadata': {'task_type': 'coding'}
                    }
                ]
            },
            'summary': {
                'total_frameworks': 2,
                'total_tasks': 2
            }
        }
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_compare_frameworks(self):
        """Test framework comparison functionality."""
        comparison = self.analyzer.compare_frameworks(self.sample_results)
        
        self.assertIn('frameworks', comparison)
        self.assertIn('metrics', comparison)
        self.assertIn('rankings', comparison)
        self.assertIn('recommendations', comparison)
        
        # Check frameworks
        self.assertEqual(set(comparison['frameworks']), {'framework1', 'framework2'})
        
        # Check metrics
        self.assertIn('performance', comparison['metrics'])
        self.assertIn('quality', comparison['metrics'])
        self.assertIn('reliability', comparison['metrics'])
        
        # Framework2 should be faster (1.0s vs 2.0s)
        self.assertLess(
            comparison['metrics']['performance']['framework2'],
            comparison['metrics']['performance']['framework1']
        )
        
        # Framework1 should have higher quality (8.5 vs 7.5)
        self.assertGreater(
            comparison['metrics']['quality']['framework1'],
            comparison['metrics']['quality']['framework2']
        )
    
    def test_analyze_task_performance(self):
        """Test task performance analysis."""
        task_analysis = self.analyzer.analyze_task_performance(self.sample_results)
        
        self.assertIn('coding', task_analysis)
        
        coding_analysis = task_analysis['coding']
        self.assertIn('frameworks', coding_analysis)
        self.assertIn('overall_stats', coding_analysis)
        
        # Should have data for both frameworks
        self.assertIn('framework1', coding_analysis['frameworks'])
        self.assertIn('framework2', coding_analysis['frameworks'])
        
        # Check overall stats
        overall_stats = coding_analysis['overall_stats']
        self.assertEqual(overall_stats['total_runs'], 2)
        self.assertEqual(overall_stats['successful_runs'], 2)
        self.assertEqual(overall_stats['success_rate'], 1.0)
    
    def test_generate_report(self):
        """Test report generation."""
        report = self.analyzer.generate_report(self.sample_results)
        
        self.assertIsInstance(report, str)
        self.assertIn('Benchmark Report', report)
        self.assertIn('Test Suite', report)
        self.assertIn('framework1', report)
        self.assertIn('framework2', report)
        self.assertIn('Performance Metrics', report)
        self.assertIn('Quality Metrics', report)
    
    def test_generate_csv_export(self):
        """Test CSV export generation."""
        csv_data = self.analyzer.generate_csv_export(self.sample_results)
        
        self.assertIsInstance(csv_data, str)
        lines = csv_data.split('\n')
        
        # Should have header + 2 data rows
        self.assertEqual(len(lines), 3)
        
        # Check header
        self.assertIn('Framework', lines[0])
        self.assertIn('Task ID', lines[0])
        self.assertIn('Status', lines[0])
        
        # Check data rows
        self.assertIn('framework1', lines[1])
        self.assertIn('framework2', lines[2])
    
    def test_find_performance_outliers(self):
        """Test performance outlier detection."""
        # Add more data points to enable outlier detection
        extended_results = self.sample_results.copy()
        extended_results['results']['framework1'].extend([
            {
                'task_id': 'task2',
                'framework': 'framework1',
                'agent_role': 'developer',
                'model_name': 'model1',
                'start_time': '2024-01-01T10:00:00',
                'end_time': '2024-01-01T10:00:01.5',
                'status': 'completed',
                'response': 'def test(): return 1',
                'metrics': {'response_time': 1.5},
                'quality_scores': {'overall': 8.0},
                'performance_data': {},
                'cost_data': {},
                'metadata': {'task_type': 'coding'}
            },
            {
                'task_id': 'task3',
                'framework': 'framework1',
                'agent_role': 'developer',
                'model_name': 'model1',
                'start_time': '2024-01-01T10:00:00',
                'end_time': '2024-01-01T10:00:10',  # Very slow - 10 seconds
                'status': 'completed',
                'response': 'def slow(): return 1',
                'metrics': {'response_time': 10.0},
                'quality_scores': {'overall': 8.0},
                'performance_data': {},
                'cost_data': {},
                'metadata': {'task_type': 'coding'}
            }
        ])
        
        outliers = self.analyzer.find_performance_outliers(extended_results, threshold_std=1.5)
        
        # Should detect the 10-second task as an outlier
        self.assertIn('framework1', outliers)
        framework1_outliers = outliers['framework1']
        self.assertGreater(len(framework1_outliers), 0)
        
        # The slow task should be in the outliers
        outlier_task_ids = [outlier['task_id'] for outlier in framework1_outliers]
        self.assertIn('task3', outlier_task_ids)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete benchmarking system."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_create_comprehensive_suite(self):
        """Test creating a comprehensive benchmark suite."""
        frameworks = ["framework1", "framework2"]
        suite = create_comprehensive_benchmark_suite(frameworks)
        
        self.assertEqual(suite.frameworks, frameworks)
        self.assertGreater(len(suite.tasks), 10)  # Should have many tasks
        self.assertGreater(len(suite.benchmark_types), 1)  # Multiple benchmark types
        
        # Should have tasks of different types
        task_types = {task.task_type for task in suite.tasks}
        self.assertGreater(len(task_types), 3)
    
    @patch('common.benchmarking_runner.ENHANCED_FEATURES_AVAILABLE', False)
    def test_quick_benchmark_without_enhanced_features(self):
        """Test quick benchmark when enhanced features are not available."""
        frameworks = ["test_framework"]
        
        # Should raise an error when trying to run without enhanced features
        with self.assertRaises(Exception):
            run_quick_benchmark(frameworks, self.temp_dir)
    
    def test_analyze_benchmark_results_function(self):
        """Test the analyze_benchmark_results convenience function."""
        # Create a sample results file
        sample_data = {
            'suite': {'name': 'Test Suite'},
            'results': {
                'framework1': [
                    {
                        'task_id': 'task1',
                        'framework': 'framework1',
                        'agent_role': 'developer',
                        'model_name': 'model1',
                        'start_time': '2024-01-01T10:00:00',
                        'end_time': '2024-01-01T10:00:02',
                        'status': 'completed',
                        'response': 'test response',
                        'metrics': {},
                        'quality_scores': {'overall': 8.0},
                        'performance_data': {},
                        'cost_data': {},
                        'metadata': {'task_type': 'coding'}
                    }
                ]
            }
        }
        
        # Save sample data to file
        results_file = Path(self.temp_dir) / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(sample_data, f)
        
        # Analyze results
        analysis = analyze_benchmark_results("test_results.json", self.temp_dir)
        
        self.assertIn('comparison', analysis)
        self.assertIn('task_analysis', analysis)
        self.assertIn('outliers', analysis)
        self.assertIn('report', analysis)
        
        # Check that report is a string
        self.assertIsInstance(analysis['report'], str)
        self.assertIn('Benchmark Report', analysis['report'])


if __name__ == '__main__':
    unittest.main()