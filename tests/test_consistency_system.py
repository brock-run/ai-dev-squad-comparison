"""
Test the self-consistency evaluation system.

These tests verify the multi-run executor, consensus analyzer, and variance calculator
implemented for Week 2, Day 1-2 of the adjustment plan.
"""

import pytest
import sys
import statistics
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from benchmark.consistency.multi_run_executor import MultiRunExecutor, MultiRunConfig
from benchmark.consistency.consensus_analyzer import ConsensusAnalyzer, ConsensusResult
from benchmark.consistency.variance_calculator import VarianceCalculator, VarianceMetrics
from benchmark.consistency.consistency_reporter import ConsistencyReporter
from common.benchmarking import BenchmarkResult


def create_mock_benchmark_result(success: bool = True, verified_pass: bool = True, 
                               duration: float = 10.0, tokens: int = 100,
                               quality_score: float = 0.8, seed: int = 42) -> BenchmarkResult:
    """Create a mock benchmark result for testing."""
    result = BenchmarkResult(
        framework="test_framework",
        task="test_task",
        success=success,
        duration=duration,
        metadata={
            'seed': seed,
            'tokens_used': tokens,
            'verification': {
                'pass': verified_pass,
                'score': quality_score
            }
        }
    )
    return result


class TestMultiRunExecutor:
    """Test the multi-run executor."""
    
    def test_multi_run_config_defaults(self):
        """Test MultiRunConfig default values."""
        config = MultiRunConfig()
        assert config.runs == 5
        assert config.parallel is True
        assert config.seed_strategy == "sequential"
        assert config.base_seed == 42
        assert config.timeout_per_run == 300
    
    def test_seed_generation_sequential(self):
        """Test sequential seed generation."""
        config = MultiRunConfig(runs=3, seed_strategy="sequential", base_seed=100)
        executor = MultiRunExecutor(config)
        
        # Mock the config system to avoid import issues
        with patch('benchmark.consistency.multi_run_executor.get_config_manager') as mock_config:
            mock_config.side_effect = ImportError("Config not available")
            
            seeds = executor._generate_seeds()
            assert seeds == [100, 101, 102]
    
    def test_seed_generation_random(self):
        """Test random seed generation."""
        config = MultiRunConfig(runs=3, seed_strategy="random", base_seed=42)
        executor = MultiRunExecutor(config)
        
        with patch('benchmark.consistency.multi_run_executor.get_config_manager') as mock_config:
            mock_config.side_effect = ImportError("Config not available")
            
            seeds1 = executor._generate_seeds()
            seeds2 = executor._generate_seeds()
            
            # Should be deterministic (same base seed)
            assert seeds1 == seeds2
            assert len(seeds1) == 3
    
    def test_seed_generation_user(self):
        """Test user-provided seed generation."""
        config = MultiRunConfig(runs=3, seed_strategy="user", base_seed=999)
        executor = MultiRunExecutor(config)
        
        with patch('benchmark.consistency.multi_run_executor.get_config_manager') as mock_config:
            mock_config.side_effect = ImportError("Config not available")
            
            seeds = executor._generate_seeds()
            assert seeds == [999, 999, 999]
    
    def test_execute_runs_sequential(self):
        """Test sequential execution of runs."""
        config = MultiRunConfig(runs=3, parallel=False, seed_strategy="sequential", base_seed=10)
        executor = MultiRunExecutor(config)
        
        # Mock benchmark function
        def mock_benchmark(**kwargs):
            seed = kwargs.get('seed', 0)
            return create_mock_benchmark_result(
                duration=seed * 0.1,  # Vary duration by seed
                seed=seed
            )
        
        with patch('benchmark.consistency.multi_run_executor.get_config_manager') as mock_config:
            mock_config.side_effect = ImportError("Config not available")
            
            results = executor.execute_runs(mock_benchmark, "test_framework", "test_task")
            
            assert len(results) == 3
            assert all(r.success for r in results)
            assert [r.metadata['seed'] for r in results] == [10, 11, 12]
    
    def test_execution_summary(self):
        """Test execution summary generation."""
        config = MultiRunConfig(runs=3)
        executor = MultiRunExecutor(config)
        
        # Create mock results
        results = [
            create_mock_benchmark_result(success=True, duration=10.0, seed=1),
            create_mock_benchmark_result(success=True, duration=12.0, seed=2),
            create_mock_benchmark_result(success=False, duration=0.0, seed=3)
        ]
        
        # Add execution time metadata
        for i, result in enumerate(results):
            result.metadata['execution_time'] = 10.0 + i
        
        executor._results = results
        summary = executor.get_execution_summary()
        
        assert summary['total_runs'] == 3
        assert summary['successful_runs'] == 2
        assert summary['failed_runs'] == 1
        assert summary['success_rate'] == 2/3
        assert summary['seeds_used'] == [1, 2, 3]


class TestConsensusAnalyzer:
    """Test the consensus analyzer."""
    
    def test_majority_consensus_pass(self):
        """Test majority consensus with passing result."""
        analyzer = ConsensusAnalyzer(strategy="majority")
        
        results = [
            create_mock_benchmark_result(verified_pass=True),
            create_mock_benchmark_result(verified_pass=True),
            create_mock_benchmark_result(verified_pass=False)
        ]
        
        consensus = analyzer.analyze_consensus(results)
        
        assert consensus.consensus_pass is True
        assert consensus.pass_votes == 2
        assert consensus.fail_votes == 1
        assert consensus.confidence == 2/3
        assert consensus.strategy == "majority"
    
    def test_majority_consensus_fail(self):
        """Test majority consensus with failing result."""
        analyzer = ConsensusAnalyzer(strategy="majority")
        
        results = [
            create_mock_benchmark_result(verified_pass=False),
            create_mock_benchmark_result(verified_pass=False),
            create_mock_benchmark_result(verified_pass=True)
        ]
        
        consensus = analyzer.analyze_consensus(results)
        
        assert consensus.consensus_pass is False
        assert consensus.pass_votes == 1
        assert consensus.fail_votes == 2
        assert consensus.confidence == 2/3
    
    def test_weighted_consensus(self):
        """Test weighted consensus analysis."""
        analyzer = ConsensusAnalyzer(strategy="weighted")
        
        results = [
            create_mock_benchmark_result(verified_pass=True, quality_score=0.9),   # High quality pass
            create_mock_benchmark_result(verified_pass=False, quality_score=0.3),  # Low quality fail
            create_mock_benchmark_result(verified_pass=False, quality_score=0.4)   # Low quality fail
        ]
        
        consensus = analyzer.analyze_consensus(results)
        
        # High quality pass should outweigh low quality fails
        assert consensus.consensus_pass is True
        assert consensus.quality_weights_used is True
        assert consensus.weighted_score > 0.5
    
    def test_empty_results(self):
        """Test consensus analysis with empty results."""
        analyzer = ConsensusAnalyzer()
        consensus = analyzer.analyze_consensus([])
        
        assert consensus.consensus_pass is False
        assert consensus.confidence == 0.0
        assert consensus.total_votes == 0
    
    def test_all_failed_runs(self):
        """Test consensus analysis when all runs failed."""
        analyzer = ConsensusAnalyzer()
        
        results = [
            BenchmarkResult(framework="test", task="test", success=False, error="Failed"),
            BenchmarkResult(framework="test", task="test", success=False, error="Failed")
        ]
        
        consensus = analyzer.analyze_consensus(results)
        
        assert consensus.consensus_pass is False
        assert consensus.total_votes == 2
        assert consensus.pass_votes == 0
        assert consensus.fail_votes == 2


class TestVarianceCalculator:
    """Test the variance calculator."""
    
    def test_variance_metrics_calculation(self):
        """Test comprehensive variance metrics calculation."""
        calculator = VarianceCalculator()
        
        results = [
            create_mock_benchmark_result(success=True, duration=10.0, tokens=100, quality_score=0.8),
            create_mock_benchmark_result(success=True, duration=12.0, tokens=110, quality_score=0.9),
            create_mock_benchmark_result(success=True, duration=11.0, tokens=105, quality_score=0.85),
            create_mock_benchmark_result(success=False, duration=0.0, tokens=0, quality_score=0.0)
        ]
        
        metrics = calculator.calculate_variance_metrics(results)
        
        assert metrics.success_rate == 0.75  # 3/4 successful
        assert metrics.duration_mean == 11.0  # Mean of [10, 12, 11]
        assert metrics.tokens_mean == 105.0   # Mean of [100, 110, 105]
        assert metrics.quality_mean == 0.85   # Mean of [0.8, 0.9, 0.85]
        assert metrics.reliability_label in ["High", "Medium", "Low"]
    
    def test_reliability_score_calculation(self):
        """Test reliability score calculation using ADR-010 formula."""
        calculator = VarianceCalculator()
        
        # Create results with known variance
        results = [
            create_mock_benchmark_result(success=True, duration=10.0, tokens=100),
            create_mock_benchmark_result(success=True, duration=10.1, tokens=101),
            create_mock_benchmark_result(success=True, duration=10.2, tokens=102),
            create_mock_benchmark_result(success=True, duration=10.0, tokens=100),
            create_mock_benchmark_result(success=True, duration=10.1, tokens=101)
        ]
        
        metrics = calculator.calculate_variance_metrics(results)
        
        # High success rate (100%) + low variance should give high reliability
        assert metrics.success_rate == 1.0
        assert metrics.reliability_score > 0.8
        assert metrics.reliability_label == "High"
    
    def test_empty_results(self):
        """Test variance calculation with empty results."""
        calculator = VarianceCalculator()
        metrics = calculator.calculate_variance_metrics([])
        
        assert metrics.success_rate == 0.0
        assert metrics.reliability_score == 0.0
        assert metrics.reliability_label == "Low"
    
    def test_outlier_detection(self):
        """Test outlier detection using Tukey fences."""
        calculator = VarianceCalculator()
        
        # Create results with one clear outlier
        results = [
            create_mock_benchmark_result(duration=10.0, quality_score=0.8),
            create_mock_benchmark_result(duration=11.0, quality_score=0.85),
            create_mock_benchmark_result(duration=10.5, quality_score=0.82),
            create_mock_benchmark_result(duration=50.0, quality_score=0.1)  # Outlier
        ]
        
        metrics = calculator.calculate_variance_metrics(results)
        
        # Should detect the outlier
        assert metrics.outliers is not None
        assert len(metrics.outliers) > 0


class TestConsistencyReporter:
    """Test the consistency reporter."""
    
    def test_consistency_report_generation(self):
        """Test comprehensive consistency report generation."""
        reporter = ConsistencyReporter()
        
        # Create mock results
        results = [
            create_mock_benchmark_result(verified_pass=True, duration=10.0, seed=1),
            create_mock_benchmark_result(verified_pass=True, duration=11.0, seed=2),
            create_mock_benchmark_result(verified_pass=False, duration=12.0, seed=3)
        ]
        
        # Create mock consensus and variance results
        consensus = ConsensusResult(
            consensus_pass=True,
            confidence=0.67,
            total_votes=3,
            pass_votes=2,
            fail_votes=1,
            strategy="majority"
        )
        
        variance = VarianceMetrics(
            success_rate=1.0,
            success_rate_ci=(0.8, 1.0),
            duration_mean=11.0,
            duration_std=1.0,
            duration_cv=0.09,
            duration_ci=(10.0, 12.0),
            reliability_score=0.85,
            reliability_label="High"
        )
        
        report = reporter.generate_consistency_report(
            framework="test_framework",
            task="test_task",
            results=results,
            consensus_result=consensus,
            variance_metrics=variance
        )
        
        # Verify report structure
        assert report["framework"] == "test_framework"
        assert report["task"] == "test_task"
        assert report["schema_version"] == "1.0"
        assert "generated_at" in report
        
        # Verify run summary
        assert report["run_summary"]["total_runs"] == 3
        assert report["run_summary"]["successful_runs"] == 3
        assert report["run_summary"]["seeds_used"] == [1, 2, 3]
        
        # Verify consensus section
        assert report["consensus"]["decision"] is True
        assert report["consensus"]["confidence"] == 0.67
        assert report["consensus"]["vote_breakdown"]["pass_votes"] == 2
        
        # Verify variance section
        assert report["variance"]["success_rate"]["value"] == 1.0
        assert report["variance"]["duration"]["mean"] == 11.0
        
        # Verify reliability section
        assert report["reliability"]["score"] == 0.85
        assert report["reliability"]["label"] == "High"
        
        # Verify individual runs
        assert len(report["individual_runs"]) == 3
    
    def test_dashboard_data_generation(self):
        """Test dashboard data generation from consistency reports."""
        reporter = ConsistencyReporter()
        
        # Create mock reports
        reports = [
            {
                "framework": "langgraph",
                "task": "bugfix",
                "reliability": {"score": 0.85, "label": "High"},
                "variance": {
                    "success_rate": {"value": 0.8, "confidence_interval": (0.6, 0.95)}
                },
                "individual_runs": [
                    {"duration": 10.0}, {"duration": 11.0}, {"duration": 12.0}
                ]
            },
            {
                "framework": "crewai", 
                "task": "bugfix",
                "reliability": {"score": 0.75, "label": "Medium"},
                "variance": {
                    "success_rate": {"value": 0.6, "confidence_interval": (0.4, 0.8)}
                },
                "individual_runs": [
                    {"duration": 15.0}, {"duration": 16.0}, {"duration": 14.0}
                ]
            }
        ]
        
        dashboard_data = reporter.generate_dashboard_data(reports)
        
        # Verify structure
        assert "consistency_overview" in dashboard_data
        assert "framework_reliability" in dashboard_data
        assert "violin_plot_data" in dashboard_data
        assert "confidence_bars" in dashboard_data
        
        # Verify content
        assert dashboard_data["consistency_overview"]["total_evaluations"] == 2
        assert "langgraph" in dashboard_data["framework_reliability"]
        assert "crewai" in dashboard_data["framework_reliability"]
        assert len(dashboard_data["violin_plot_data"]) == 2
        assert len(dashboard_data["confidence_bars"]) == 2


def test_end_to_end_consistency_evaluation():
    """Test complete end-to-end consistency evaluation workflow."""
    
    # Step 1: Create multi-run executor
    config = MultiRunConfig(runs=5, parallel=False, seed_strategy="sequential", base_seed=42)
    executor = MultiRunExecutor(config)
    
    # Step 2: Mock benchmark function that varies by seed
    def mock_benchmark(**kwargs):
        seed = kwargs.get('seed', 42)
        # Simulate some variance based on seed
        success_prob = 0.8 + (seed % 3) * 0.1  # 0.8, 0.9, 1.0, 0.8, 0.9
        verified_pass = (seed % 5) != 0  # Fail on seed 0, 5, 10, etc.
        duration = 10.0 + (seed % 3)     # 10, 11, 12, 10, 11
        tokens = 100 + (seed % 10)       # Some token variation
        quality = 0.7 + (seed % 4) * 0.05  # Quality variation
        
        return create_mock_benchmark_result(
            success=True,  # Execution success
            verified_pass=verified_pass,
            duration=duration,
            tokens=tokens,
            quality_score=quality,
            seed=seed
        )
    
    # Step 3: Execute runs
    with patch('benchmark.consistency.multi_run_executor.get_config_manager') as mock_config:
        mock_config.side_effect = ImportError("Config not available")
        
        results = executor.execute_runs(mock_benchmark, "test_framework", "test_task")
    
    # Step 4: Analyze consensus
    consensus_analyzer = ConsensusAnalyzer(strategy="majority")
    consensus_result = consensus_analyzer.analyze_consensus(results)
    
    # Step 5: Calculate variance
    variance_calculator = VarianceCalculator()
    variance_metrics = variance_calculator.calculate_variance_metrics(results)
    
    # Step 6: Generate report
    reporter = ConsistencyReporter()
    report = reporter.generate_consistency_report(
        framework="test_framework",
        task="test_task",
        results=results,
        consensus_result=consensus_result,
        variance_metrics=variance_metrics
    )
    
    # Verify end-to-end results
    assert len(results) == 5
    assert report["framework"] == "test_framework"
    assert report["task"] == "test_task"
    assert report["run_summary"]["total_runs"] == 5
    assert "consensus" in report
    assert "variance" in report
    assert "reliability" in report
    assert len(report["individual_runs"]) == 5
    
    print(f"✓ End-to-end test completed:")
    print(f"  - Consensus: {'PASS' if consensus_result.consensus_pass else 'FAIL'} (confidence: {consensus_result.confidence:.2f})")
    print(f"  - Reliability: {variance_metrics.reliability_label} ({variance_metrics.reliability_score:.2f})")
    print(f"  - Success rate: {variance_metrics.success_rate:.2%}")
    print(f"  - Duration: {variance_metrics.duration_mean:.1f}s ± {variance_metrics.duration_std:.1f}s")


if __name__ == "__main__":
    # Run tests directly
    print("Running consistency system tests...")
    
    # Test multi-run executor
    test_executor = TestMultiRunExecutor()
    test_executor.test_multi_run_config_defaults()
    print("✓ Multi-run config defaults test passed")
    
    test_executor.test_seed_generation_sequential()
    print("✓ Sequential seed generation test passed")
    
    test_executor.test_seed_generation_random()
    print("✓ Random seed generation test passed")
    
    test_executor.test_seed_generation_user()
    print("✓ User seed generation test passed")
    
    test_executor.test_execute_runs_sequential()
    print("✓ Sequential execution test passed")
    
    test_executor.test_execution_summary()
    print("✓ Execution summary test passed")
    
    # Test consensus analyzer
    test_consensus = TestConsensusAnalyzer()
    test_consensus.test_majority_consensus_pass()
    print("✓ Majority consensus pass test passed")
    
    test_consensus.test_majority_consensus_fail()
    print("✓ Majority consensus fail test passed")
    
    test_consensus.test_weighted_consensus()
    print("✓ Weighted consensus test passed")
    
    test_consensus.test_empty_results()
    print("✓ Empty results test passed")
    
    test_consensus.test_all_failed_runs()
    print("✓ All failed runs test passed")
    
    # Test variance calculator
    test_variance = TestVarianceCalculator()
    test_variance.test_variance_metrics_calculation()
    print("✓ Variance metrics calculation test passed")
    
    test_variance.test_reliability_score_calculation()
    print("✓ Reliability score calculation test passed")
    
    test_variance.test_empty_results()
    print("✓ Variance empty results test passed")
    
    test_variance.test_outlier_detection()
    print("✓ Outlier detection test passed")
    
    # Test consistency reporter
    test_reporter = TestConsistencyReporter()
    test_reporter.test_consistency_report_generation()
    print("✓ Consistency report generation test passed")
    
    test_reporter.test_dashboard_data_generation()
    print("✓ Dashboard data generation test passed")
    
    # Test end-to-end workflow
    test_end_to_end_consistency_evaluation()
    print("✓ End-to-end consistency evaluation test passed")
    
    print("\n🎉 All consistency system tests passed!")
    print("The self-consistency evaluation system is working correctly.")