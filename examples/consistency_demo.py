#!/usr/bin/env python3
"""
Consistency Evaluation Demo

This example demonstrates how to use the consistency evaluation system
to assess the reliability and variance of AI agent implementations
across multiple runs.

Week 2, Day 5 - Polish: Examples and documentation
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import consistency evaluation modules
try:
    from benchmark.consistency.multi_run_executor import MultiRunExecutor, ConsistencyRunConfig
    from benchmark.consistency.consensus_analyzer import ConsensusAnalyzer, ConsensusStrategy
    from benchmark.consistency.variance_calculator import VarianceCalculator
    from benchmark.consistency.consistency_reporter import ConsistencyReporter
    from common.config import SeedConfig
    from common.benchmarking import BenchmarkResult
    CONSISTENCY_AVAILABLE = True
except ImportError as e:
    logger.error(f"Consistency evaluation modules not available: {e}")
    CONSISTENCY_AVAILABLE = False


async def run_consistency_demo():
    """Run a complete consistency evaluation demo."""
    
    if not CONSISTENCY_AVAILABLE:
        logger.error("Consistency evaluation modules not available. Please install dependencies.")
        return
    
    logger.info("🚀 Starting Consistency Evaluation Demo")
    logger.info("=" * 60)
    
    # Step 1: Create a demo task configuration
    task_config = {
        "name": "fibonacci_generator",
        "description": "Generate a Python function to calculate Fibonacci numbers",
        "requirements": [
            "Handle negative numbers gracefully",
            "Use memoization for optimization",
            "Include proper error handling",
            "Provide clear documentation"
        ],
        "expected_output": "A working Python function with tests"
    }
    
    logger.info(f"📋 Task: {task_config['name']}")
    logger.info(f"📝 Description: {task_config['description']}")
    
    # Step 2: Configure consistency evaluation
    output_dir = Path("demo_results/consistency")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    seed_config = SeedConfig(base_seed=42, deterministic=True)
    
    config = ConsistencyRunConfig(
        task_config=task_config,
        adapter_name="demo_adapter",
        num_runs=5,
        seed_config=seed_config,
        parallel=True,
        max_workers=3,
        output_dir=output_dir
    )
    
    logger.info(f"⚙️  Configuration:")
    logger.info(f"   • Runs: {config.num_runs}")
    logger.info(f"   • Parallel: {config.parallel}")
    logger.info(f"   • Seeds: {config.seeds}")
    logger.info(f"   • Output: {config.output_dir}")
    
    # Step 3: Execute multiple runs (simulated)
    logger.info("\n🔄 Executing multiple runs...")
    
    executor = MultiRunExecutor(config)
    
    # For demo purposes, we'll create mock results instead of actual execution
    mock_results = create_mock_run_results(config)
    executor.results = mock_results
    
    logger.info(f"✅ Completed {len(mock_results)} runs")
    
    # Step 4: Perform consensus analysis
    logger.info("\n🤝 Analyzing consensus...")
    
    # Test different consensus strategies
    strategies = [
        (ConsensusStrategy.MAJORITY_VOTE, "Simple majority vote"),
        (ConsensusStrategy.WEIGHTED_VOTE, "Weighted by verification score"),
        (ConsensusStrategy.THRESHOLD, "60% threshold requirement"),
    ]
    
    consensus_results = {}
    
    for strategy, description in strategies:
        analyzer = ConsensusAnalyzer(
            strategy=strategy,
            threshold=0.6 if strategy == ConsensusStrategy.THRESHOLD else 0.5
        )
        
        formatted_results = [r.to_dict() for r in mock_results]
        consensus_result = analyzer.analyze_consensus(formatted_results)
        consensus_results[strategy.value] = consensus_result
        
        logger.info(f"   • {description}:")
        logger.info(f"     - Decision: {'PASS' if consensus_result.consensus_decision else 'FAIL'}")
        logger.info(f"     - Confidence: {consensus_result.confidence:.3f}")
        logger.info(f"     - Agreement: {consensus_result.agreement_rate:.3f}")
    
    # Step 5: Calculate variance metrics
    logger.info("\n📊 Calculating variance metrics...")
    
    variance_calculator = VarianceCalculator()
    benchmark_results = [r.benchmark_result for r in mock_results if r.benchmark_result]
    variance_metrics = variance_calculator.calculate_variance_metrics(benchmark_results)
    
    logger.info(f"   • Success Rate: {variance_metrics.success_rate:.3f}")
    logger.info(f"   • Duration Mean: {variance_metrics.duration_mean:.3f}s")
    logger.info(f"   • Duration CV: {variance_metrics.duration_cv:.3f}")
    logger.info(f"   • Reliability Score: {variance_metrics.reliability_score:.3f}")
    logger.info(f"   • Reliability Label: {variance_metrics.reliability_label}")
    
    # Step 6: Calculate reliability score using consensus analyzer
    logger.info("\n🎯 Calculating reliability score...")
    
    reliability_analyzer = ConsensusAnalyzer()
    reliability_data = reliability_analyzer.calculate_reliability_score(formatted_results)
    
    logger.info(f"   • Overall Score: {reliability_data['reliability_score']:.3f}")
    logger.info(f"   • Label: {reliability_data['label']}")
    logger.info(f"   • Components:")
    for component, value in reliability_data['components'].items():
        logger.info(f"     - {component}: {value:.3f}")
    
    # Step 7: Generate comprehensive report
    logger.info("\n📄 Generating consistency report...")
    
    reporter = ConsistencyReporter(output_dir=output_dir)
    
    # Use the majority vote consensus for the report
    main_consensus = consensus_results['majority']
    
    report = reporter.generate_consistency_report(
        framework="demo_adapter",
        task="fibonacci_generator",
        results=benchmark_results,
        consensus_result=main_consensus,
        variance_metrics=variance_metrics,
        configuration={
            'demo_mode': True,
            'strategies_tested': list(consensus_results.keys()),
            'total_runs': len(mock_results),
            'seeds_used': config.seeds
        },
        reliability_data=reliability_data
    )
    
    # Write report to file
    report_file = reporter.write_consistency_report(
        framework="demo_adapter",
        task="fibonacci_generator",
        report=report
    )
    
    logger.info(f"   • Report saved: {report_file}")
    
    # Step 8: Display summary
    logger.info("\n📈 Summary:")
    logger.info("=" * 60)
    logger.info(f"Task: {task_config['name']}")
    logger.info(f"Runs: {len(mock_results)} ({len([r for r in mock_results if r.success])} successful)")
    logger.info(f"Consensus: {'PASS' if main_consensus.consensus_decision else 'FAIL'} (confidence: {main_consensus.confidence:.1%})")
    logger.info(f"Reliability: {variance_metrics.reliability_label} ({variance_metrics.reliability_score:.3f})")
    logger.info(f"Duration Variance: {variance_metrics.duration_cv:.3f} CV")
    logger.info(f"Report: {report_file}")
    
    # Step 9: Show how to use the data for dashboard
    logger.info("\n🖥️  Dashboard Integration:")
    dashboard_data = reporter.generate_dashboard_data([report])
    logger.info(f"   • Total Evaluations: {dashboard_data['consistency_overview']['total_evaluations']}")
    logger.info(f"   • Frameworks: {dashboard_data['consistency_overview']['frameworks']}")
    logger.info(f"   • Violin Plot Data Points: {len(dashboard_data['violin_plot_data'])}")
    logger.info(f"   • Confidence Bars: {len(dashboard_data['confidence_bars'])}")
    
    logger.info("\n✨ Demo completed successfully!")
    logger.info(f"Check the results in: {output_dir}")
    
    return report


def create_mock_run_results(config: ConsistencyRunConfig):
    """Create mock run results for demonstration purposes."""
    from benchmark.consistency.multi_run_executor import RunResult
    
    results = []
    
    for i in range(config.num_runs):
        # Simulate varying success rates and performance
        success = i < 4  # 4 out of 5 succeed
        duration = 1.2 + (i * 0.1) + (config.seeds[i] % 10) * 0.01  # Variable duration
        
        if success:
            # Create mock benchmark result
            benchmark_result = BenchmarkResult(
                task_id=f"fibonacci_generator_run_{i}",
                adapter_name="demo_adapter",
                success=True,
                duration=duration,
                output={
                    "code": f"def fibonacci(n): # Run {i} implementation",
                    "tokens": 150 + i * 10,
                    "lines_of_code": 25 + i * 2
                },
                verification_results={
                    "verified_pass": True,
                    "verification_score": 0.85 + (i * 0.03),  # Slightly increasing scores
                    "test_results": {
                        "passed": 8,
                        "failed": 0,
                        "total": 8
                    }
                },
                metadata={
                    "seed": config.seeds[i],
                    "run_index": i,
                    "model_used": "demo-model-v1",
                    "temperature": 0.1
                }
            )
        else:
            # Create failed benchmark result
            benchmark_result = BenchmarkResult(
                task_id=f"fibonacci_generator_run_{i}",
                adapter_name="demo_adapter",
                success=False,
                duration=duration,
                output={"error": "Timeout during code generation"},
                verification_results={
                    "verified_pass": False,
                    "verification_score": 0.2,
                    "error": "Code did not compile"
                },
                metadata={
                    "seed": config.seeds[i],
                    "run_index": i,
                    "error_type": "timeout"
                }
            )
        
        run_result = RunResult(
            run_index=i,
            seed=config.seeds[i],
            benchmark_result=benchmark_result if success else None,
            error=None if success else Exception("Simulated failure"),
            duration=duration
        )
        
        results.append(run_result)
    
    return results


def demonstrate_cli_usage():
    """Demonstrate CLI usage for consistency evaluation."""
    
    logger.info("\n🖥️  CLI Usage Examples:")
    logger.info("=" * 60)
    
    examples = [
        {
            "description": "Basic consistency evaluation",
            "command": "make consistency F=langgraph T=simple_code_generation"
        },
        {
            "description": "Custom number of runs",
            "command": "make consistency F=crewai T=bug_fixing RUNS=10"
        },
        {
            "description": "Different consensus strategy",
            "command": "make consistency F=autogen T=refactoring STRATEGY=weighted"
        },
        {
            "description": "Sequential execution with custom seeds",
            "command": "make consistency-custom F=haystack T=documentation RUNS=5 PARALLEL=false SEEDS=42,123,456,789,101"
        },
        {
            "description": "Smoke test for CI",
            "command": "make consistency-smoke"
        }
    ]
    
    for example in examples:
        logger.info(f"• {example['description']}:")
        logger.info(f"  {example['command']}")
        logger.info("")
    
    logger.info("📊 View results in the dashboard:")
    logger.info("  make dashboard")
    logger.info("  # Navigate to http://localhost:5000/consistency")


async def main():
    """Main demo function."""
    
    logger.info("🎯 AI Dev Squad - Consistency Evaluation Demo")
    logger.info("This demo shows how to evaluate AI agent consistency across multiple runs")
    logger.info("")
    
    try:
        # Run the main consistency demo
        report = await run_consistency_demo()
        
        # Show CLI usage examples
        demonstrate_cli_usage()
        
        # Show next steps
        logger.info("\n🚀 Next Steps:")
        logger.info("1. Run actual consistency evaluations on your frameworks")
        logger.info("2. View results in the web dashboard")
        logger.info("3. Use reliability scores to compare framework performance")
        logger.info("4. Integrate consistency checks into your CI pipeline")
        
        return report
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())