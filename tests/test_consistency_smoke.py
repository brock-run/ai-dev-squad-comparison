#!/usr/bin/env python3
"""
Consistency Smoke Test for CI

Quick smoke test to verify consistency evaluation components work
following Week 2, Day 3 of the adjustment plan.
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Import consistency modules
try:
    from benchmark.consistency.multi_run_executor import MultiRunExecutor, ConsistencyRunConfig, RunResult
    from benchmark.consistency.consensus_analyzer import ConsensusAnalyzer, ConsensusStrategy
    from benchmark.consistency.variance_calculator import VarianceCalculator
    from benchmark.consistency.consistency_reporter import ConsistencyReporter
    from common.config import SeedConfig
    from common.benchmarking import BenchmarkResult
    CONSISTENCY_AVAILABLE = True
except ImportError as e:
    CONSISTENCY_AVAILABLE = False
    pytest.skip(f"Consistency modules not available: {e}", allow_module_level=True)


class TestConsistencySmoke:
    """Smoke tests for consistency evaluation components."""
    
    def test_consistency_modules_importable(self):
        """Test that all consistency modules can be imported."""
        assert CONSISTENCY_AVAILABLE, "Consistency modules should be importable"
    
    def test_consensus_analyzer_basic(self):
        """Test basic consensus analyzer functionality."""
        analyzer = ConsensusAnalyzer(strategy=ConsensusStrategy.MAJORITY_VOTE)
        
        # Create mock run results
        mock_results = [
            {
                'success': True,
                'benchmark_result': {
                    'verification_results': {
                        'verified_pass': True,
                        'verification_score': 0.9
                    }
                }
            },
            {
                'success': True,
                'benchmark_result': {
                    'verification_results': {
                        'verified_pass': True,
                        'verification_score': 0.8
                    }
                }
            },
            {
                'success': True,
                'benchmark_result': {
                    'verification_results': {
                        'verified_pass': False,
                        'verification_score': 0.3
                    }
                }
            }
        ]
        
        result = analyzer.analyze_consensus(mock_results)
        
        assert result is not None
        assert hasattr(result, 'consensus_decision')
        assert hasattr(result, 'confidence')
        assert result.total_runs == 3
        assert result.successful_runs == 3
    
    def test_variance_calculator_basic(self):
        """Test basic variance calculator functionality."""
        calculator = VarianceCalculator()
        
        # Create mock benchmark results
        mock_results = []
        for i in range(3):
            result = BenchmarkResult(
                task_id=f"test_task_{i}",
                adapter_name="test_adapter",
                success=True,
                duration=1.0 + i * 0.1,  # Variable durations
                output={"result": f"output_{i}"},
                verification_results={"verified_pass": True, "score": 0.8 + i * 0.05},
                metadata={"seed": 42 + i}
            )
            mock_results.append(result)
        
        metrics = calculator.calculate_variance_metrics(mock_results)
        
        assert metrics is not None
        assert metrics.success_rate == 1.0  # All successful
        assert metrics.duration_mean > 0
        assert metrics.reliability_score >= 0
        assert metrics.reliability_label in ["High", "Medium", "Low"]
    
    def test_consistency_reporter_basic(self):
        """Test basic consistency reporter functionality."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = ConsistencyReporter(output_dir=Path(temp_dir))
            
            # Create mock data
            mock_results = [
                BenchmarkResult(
                    task_id="test_task",
                    adapter_name="test_adapter",
                    success=True,
                    duration=1.0,
                    output={"result": "output"},
                    verification_results={"verified_pass": True, "score": 0.9},
                    metadata={"seed": 42}
                )
            ]
            
            # Mock consensus result
            class MockConsensusResult:
                def __init__(self):
                    self.consensus_pass = True
                    self.confidence = 0.9
                    self.strategy = "majority"
                    self.pass_votes = 1
                    self.fail_votes = 0
                    self.total_votes = 1
                    self.weighted_score = 0.9
                    self.quality_weights_used = True
                    self.outliers_excluded = []
            
            # Mock variance metrics
            class MockVarianceMetrics:
                def __init__(self):
                    self.success_rate = 1.0
                    self.success_rate_ci = (0.8, 1.0)
                    self.duration_mean = 1.0
                    self.duration_std = 0.1
                    self.duration_cv = 0.1
                    self.duration_ci = (0.9, 1.1)
                    self.tokens_mean = None
                    self.tokens_std = None
                    self.tokens_cv = None
                    self.tokens_ci = None
                    self.quality_mean = 0.9
                    self.quality_std = 0.0
                    self.quality_cv = 0.0
                    self.quality_ci = (0.9, 0.9)
                    self.reliability_score = 0.95
                    self.reliability_label = "High"
                    self.outliers = []
            
            consensus_result = MockConsensusResult()
            variance_metrics = MockVarianceMetrics()
            
            # Generate report
            report = reporter.generate_consistency_report(
                framework="test_framework",
                task="test_task",
                results=mock_results,
                consensus_result=consensus_result,
                variance_metrics=variance_metrics
            )
            
            assert report is not None
            assert "schema_version" in report
            assert "framework" in report
            assert "task" in report
            assert "consensus" in report
            assert "variance" in report
            assert "reliability" in report
            
            # Test writing report
            report_file = reporter.write_consistency_report(
                framework="test_framework",
                task="test_task",
                report=report
            )
            
            assert report_file.exists()
            assert report_file.suffix == ".json"
    
    @pytest.mark.asyncio
    async def test_multi_run_executor_basic(self):
        """Test basic multi-run executor functionality."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create basic configuration
            task_config = {
                "name": "test_task",
                "description": "Test task for smoke test"
            }
            
            config = ConsistencyRunConfig(
                task_config=task_config,
                adapter_name="test_adapter",
                num_runs=2,  # Small number for smoke test
                parallel=False,  # Sequential for simplicity
                output_dir=Path(temp_dir)
            )
            
            executor = MultiRunExecutor(config)
            
            # The executor should be created successfully
            assert executor is not None
            assert executor.config.num_runs == 2
            assert executor.config.adapter_name == "test_adapter"
            
            # Test execution summary before runs
            summary = executor.get_execution_summary()
            assert summary["status"] == "not_executed"
    
    def test_consensus_strategies(self):
        """Test different consensus strategies."""
        strategies = [
            ConsensusStrategy.MAJORITY_VOTE,
            ConsensusStrategy.WEIGHTED_VOTE,
            ConsensusStrategy.UNANIMOUS,
            ConsensusStrategy.THRESHOLD,
            ConsensusStrategy.BEST_OF_N
        ]
        
        for strategy in strategies:
            analyzer = ConsensusAnalyzer(strategy=strategy)
            assert analyzer.strategy == strategy
    
    def test_reliability_score_calculation(self):
        """Test reliability score calculation."""
        analyzer = ConsensusAnalyzer()
        
        # Mock run results with varying success rates
        mock_results = [
            {
                'success': True,
                'duration': 1.0,
                'benchmark_result': {
                    'output': {'tokens': 100},
                    'verification_results': {'verified_pass': True, 'verification_score': 0.9}
                }
            },
            {
                'success': True,
                'duration': 1.1,
                'benchmark_result': {
                    'output': {'tokens': 110},
                    'verification_results': {'verified_pass': True, 'verification_score': 0.8}
                }
            },
            {
                'success': False,
                'duration': 0.5,
                'benchmark_result': None
            }
        ]
        
        reliability = analyzer.calculate_reliability_score(mock_results)
        
        assert reliability is not None
        assert 'reliability_score' in reliability
        assert 'label' in reliability
        assert 'components' in reliability
        assert reliability['reliability_score'] >= 0.0
        assert reliability['reliability_score'] <= 1.0
        assert reliability['label'] in ['High', 'Medium', 'Low']


class TestConsistencyIntegration:
    """Integration tests for consistency evaluation workflow."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_mock(self):
        """Test end-to-end consistency evaluation workflow with mocked data."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Create configuration
            task_config = {"name": "integration_test", "description": "End-to-end test"}
            
            config = ConsistencyRunConfig(
                task_config=task_config,
                adapter_name="test_adapter",
                num_runs=3,
                parallel=False,
                output_dir=Path(temp_dir)
            )
            
            # Step 2: Create mock run results (simulating executor output)
            mock_run_results = []
            for i in range(3):
                benchmark_result = BenchmarkResult(
                    task_id=f"test_task_{i}",
                    adapter_name="test_adapter",
                    success=True,
                    duration=1.0 + i * 0.1,
                    output={"result": f"output_{i}", "tokens": 100 + i * 10},
                    verification_results={"verified_pass": True, "verification_score": 0.8 + i * 0.05},
                    metadata={"seed": 42 + i}
                )
                
                run_result = RunResult(
                    run_index=i,
                    seed=42 + i,
                    benchmark_result=benchmark_result,
                    duration=1.0 + i * 0.1
                )
                mock_run_results.append(run_result)
            
            # Step 3: Consensus analysis
            formatted_results = [r.to_dict() for r in mock_run_results]
            consensus_analyzer = ConsensusAnalyzer(strategy=ConsensusStrategy.MAJORITY_VOTE)
            consensus_result = consensus_analyzer.analyze_consensus(formatted_results)
            
            assert consensus_result.consensus_decision is True  # All passed
            assert consensus_result.confidence > 0.5
            
            # Step 4: Variance analysis
            variance_calculator = VarianceCalculator()
            benchmark_results = [r.benchmark_result for r in mock_run_results]
            variance_metrics = variance_calculator.calculate_variance_metrics(benchmark_results)
            
            assert variance_metrics.success_rate == 1.0
            assert variance_metrics.reliability_score > 0.5
            
            # Step 5: Generate report
            reporter = ConsistencyReporter(output_dir=Path(temp_dir))
            report = reporter.generate_consistency_report(
                framework="test_adapter",
                task="integration_test",
                results=benchmark_results,
                consensus_result=consensus_result,
                variance_metrics=variance_metrics
            )
            
            # Verify report structure
            assert "consensus" in report
            assert "variance" in report
            assert "reliability" in report
            assert "individual_runs" in report
            assert len(report["individual_runs"]) == 3
            
            # Step 6: Write report
            report_file = reporter.write_consistency_report(
                framework="test_adapter",
                task="integration_test",
                report=report
            )
            
            assert report_file.exists()
            
            # Verify file contents
            import json
            with open(report_file) as f:
                loaded_report = json.load(f)
            
            assert loaded_report["framework"] == "test_adapter"
            assert loaded_report["task"] == "integration_test"
            assert loaded_report["consensus"]["decision"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])