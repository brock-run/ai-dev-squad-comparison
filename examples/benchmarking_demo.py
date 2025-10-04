#!/usr/bin/env python3
"""
Advanced Benchmarking System Demo

This script demonstrates the comprehensive benchmarking capabilities
of the AI Dev Squad platform, including suite creation, execution,
analysis, and reporting.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.benchmarking import (
    create_comprehensive_benchmark_suite,
    run_quick_benchmark,
    analyze_benchmark_results
)
from common.benchmarking_tasks import (
    BenchmarkSuiteBuilder,
    create_quick_suite,
    create_performance_focused_suite,
    create_quality_focused_suite
)
from common.benchmarking_runner import BenchmarkRunner
from common.benchmarking_analyzer import BenchmarkAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_suite_creation():
    """Demonstrate different ways to create benchmark suites."""
    print("\n" + "="*60)
    print("BENCHMARK SUITE CREATION DEMO")
    print("="*60)
    
    # Available frameworks for testing
    frameworks = ["langgraph", "crewai", "haystack", "autogen"]
    
    print(f"\nAvailable frameworks: {', '.join(frameworks)}")
    
    # 1. Create a comprehensive benchmark suite
    print("\n1. Creating comprehensive benchmark suite...")
    comprehensive_suite = create_comprehensive_benchmark_suite(frameworks)
    
    print(f"   - Suite ID: {comprehensive_suite.suite_id}")
    print(f"   - Name: {comprehensive_suite.name}")
    print(f"   - Total tasks: {len(comprehensive_suite.tasks)}")
    print(f"   - Frameworks: {len(comprehensive_suite.frameworks)}")
    print(f"   - Benchmark types: {[bt.value for bt in comprehensive_suite.benchmark_types]}")
    
    # Show task breakdown by type
    task_types = {}
    for task in comprehensive_suite.tasks:
        task_type = task.task_type.value
        task_types[task_type] = task_types.get(task_type, 0) + 1
    
    print(f"   - Task breakdown: {task_types}")
    
    # 2. Create a quick benchmark suite
    print("\n2. Creating quick benchmark suite...")
    quick_suite = create_quick_suite(frameworks[:2])  # Use first 2 frameworks
    
    print(f"   - Suite ID: {quick_suite.suite_id}")
    print(f"   - Total tasks: {len(quick_suite.tasks)}")
    print(f"   - Frameworks: {quick_suite.frameworks}")
    
    # 3. Create performance-focused suite
    print("\n3. Creating performance-focused suite...")
    perf_suite = create_performance_focused_suite(frameworks[:2])
    
    print(f"   - Suite ID: {perf_suite.suite_id}")
    print(f"   - Total tasks: {len(perf_suite.tasks)}")
    print(f"   - Benchmark types: {[bt.value for bt in perf_suite.benchmark_types]}")
    
    # 4. Create quality-focused suite
    print("\n4. Creating quality-focused suite...")
    quality_suite = create_quality_focused_suite(frameworks[:2])
    
    print(f"   - Suite ID: {quality_suite.suite_id}")
    print(f"   - Total tasks: {len(quality_suite.tasks)}")
    print(f"   - Configuration: {quality_suite.configuration}")
    
    # 5. Custom suite with builder
    print("\n5. Creating custom suite with builder...")
    builder = BenchmarkSuiteBuilder()
    
    custom_suite = (builder
                   .add_coding_tasks()
                   .add_testing_tasks()
                   .add_frameworks(["custom_framework"])
                   .add_configuration({
                       'timeout_seconds': 180,
                       'parallel_execution': False,
                       'custom_setting': 'demo_value'
                   })
                   .build(
                       suite_id="custom_demo",
                       name="Custom Demo Suite",
                       description="A custom suite for demonstration"
                   ))
    
    print(f"   - Suite ID: {custom_suite.suite_id}")
    print(f"   - Total tasks: {len(custom_suite.tasks)}")
    print(f"   - Custom configuration: {custom_suite.configuration}")
    
    return comprehensive_suite, quick_suite


def demo_task_details(suite):
    """Demonstrate detailed task information."""
    print("\n" + "="*60)
    print("BENCHMARK TASK DETAILS DEMO")
    print("="*60)
    
    print(f"\nAnalyzing suite: {suite.name}")
    print(f"Total tasks: {len(suite.tasks)}")
    
    # Show details for first few tasks
    for i, task in enumerate(suite.tasks[:3]):
        print(f"\n--- Task {i+1}: {task.name} ---")
        print(f"ID: {task.task_id}")
        print(f"Type: {task.task_type.value}")
        print(f"Description: {task.description}")
        print(f"Timeout: {task.timeout_seconds}s")
        print(f"Importance: {task.importance.value}")
        
        # Show prompt (truncated)
        prompt_preview = task.prompt[:100] + "..." if len(task.prompt) > 100 else task.prompt
        print(f"Prompt: {prompt_preview}")
        
        # Show evaluation criteria
        if task.evaluation_criteria:
            print("Evaluation criteria:")
            for criterion, config in task.evaluation_criteria.items():
                print(f"  - {criterion}: {config}")
        
        # Show expected output if available
        if task.expected_output:
            expected_preview = task.expected_output[:50] + "..." if len(task.expected_output) > 50 else task.expected_output
            print(f"Expected output: {expected_preview}")


def demo_mock_benchmark_execution():
    """Demonstrate benchmark execution with mock data."""
    print("\n" + "="*60)
    print("MOCK BENCHMARK EXECUTION DEMO")
    print("="*60)
    
    # Note: This creates mock results since we don't have actual AI agents running
    print("\nNote: This demo creates mock benchmark results for demonstration.")
    print("In a real scenario, this would execute actual AI agents.")
    
    # Create a simple suite for demo
    frameworks = ["mock_framework_1", "mock_framework_2"]
    suite = create_quick_suite(frameworks)
    
    print(f"\nCreated suite with {len(suite.tasks)} tasks for {len(frameworks)} frameworks")
    
    # Create mock results
    from datetime import datetime
    from common.benchmarking import BenchmarkResult, BenchmarkStatus
    
    mock_results = {}
    
    for framework in frameworks:
        framework_results = []
        
        for i, task in enumerate(suite.tasks):
            # Create mock result with varying performance
            base_time = 1.0 + (i * 0.5)  # Increasing response times
            framework_multiplier = 1.2 if framework == "mock_framework_2" else 1.0
            response_time = base_time * framework_multiplier
            
            # Mock quality scores
            base_quality = 8.0 - (i * 0.5)  # Decreasing quality
            framework_quality_bonus = 0.5 if framework == "mock_framework_1" else 0.0
            quality_score = max(5.0, base_quality + framework_quality_bonus)
            
            start_time = datetime.now()
            end_time = datetime.now()
            
            result = BenchmarkResult(
                task_id=task.task_id,
                framework=framework,
                agent_role="mock_agent",
                model_name="mock_model",
                start_time=start_time,
                end_time=end_time,
                status=BenchmarkStatus.COMPLETED if i < len(suite.tasks) - 1 else BenchmarkStatus.FAILED,
                response=f"Mock response for {task.task_id}" if i < len(suite.tasks) - 1 else None,
                error_message="Mock error" if i == len(suite.tasks) - 1 else None,
                metrics={
                    'response_time': response_time,
                    'memory_usage': 10.0 + i,
                    'cpu_usage': 5.0 + i,
                    'throughput': 100.0 / response_time
                },
                quality_scores={
                    'overall': quality_score,
                    'length_check': quality_score + 0.2,
                    'keyword_presence': quality_score - 0.1,
                    'structure_check': quality_score + 0.1
                },
                performance_data={
                    'duration': response_time,
                    'memory_delta': 5.0 + i,
                    'cpu_delta': 2.0 + i
                },
                cost_data={
                    'total_cost_usd': 0.001 * (i + 1),
                    'total_tokens': 100 * (i + 1),
                    'avg_cost_per_token': 0.00001
                },
                metadata={
                    'task_type': task.task_type.value,
                    'importance': task.importance.value,
                    'prompt_length': len(task.prompt),
                    'response_length': len(f"Mock response for {task.task_id}") if i < len(suite.tasks) - 1 else 0
                }
            )
            
            framework_results.append(result)
        
        mock_results[framework] = framework_results
    
    print(f"\nGenerated mock results for {len(mock_results)} frameworks")
    
    # Show summary of results
    for framework, results in mock_results.items():
        completed = len([r for r in results if r.status == BenchmarkStatus.COMPLETED])
        failed = len([r for r in results if r.status == BenchmarkStatus.FAILED])
        avg_time = sum(r.duration_seconds for r in results if r.status == BenchmarkStatus.COMPLETED) / max(completed, 1)
        avg_quality = sum(r.quality_scores.get('overall', 0) for r in results if r.status == BenchmarkStatus.COMPLETED) / max(completed, 1)
        
        print(f"\n{framework}:")
        print(f"  - Completed: {completed}/{len(results)} tasks")
        print(f"  - Success rate: {completed/len(results):.1%}")
        print(f"  - Average response time: {avg_time:.2f}s")
        print(f"  - Average quality score: {avg_quality:.1f}/10")
    
    return suite, mock_results


def demo_benchmark_analysis(suite, results):
    """Demonstrate benchmark analysis and reporting."""
    print("\n" + "="*60)
    print("BENCHMARK ANALYSIS DEMO")
    print("="*60)
    
    # Create analyzer
    analyzer = BenchmarkAnalyzer()
    
    # Prepare results data in the expected format
    results_data = {
        'suite': suite.to_dict(),
        'results': {
            framework: [result.to_dict() for result in framework_results]
            for framework, framework_results in results.items()
        },
        'summary': {},
        'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    
    # 1. Framework comparison
    print("\n1. Framework Comparison Analysis")
    comparison = analyzer.compare_frameworks(results_data)
    
    print(f"   Frameworks analyzed: {', '.join(comparison['frameworks'])}")
    
    # Performance metrics
    if 'performance' in comparison['metrics']:
        print("\n   Performance (Response Time):")
        for framework, time in comparison['metrics']['performance'].items():
            print(f"     - {framework}: {time:.2f}s")
    
    # Quality metrics
    if 'quality' in comparison['metrics']:
        print("\n   Quality (Overall Score):")
        for framework, quality in comparison['metrics']['quality'].items():
            print(f"     - {framework}: {quality:.1f}/10")
    
    # Reliability metrics
    if 'reliability' in comparison['metrics']:
        print("\n   Reliability (Success Rate):")
        for framework, reliability in comparison['metrics']['reliability'].items():
            print(f"     - {framework}: {reliability:.1%}")
    
    # Rankings
    if comparison['rankings']:
        print("\n   Rankings:")
        for metric, ranking in comparison['rankings'].items():
            print(f"     {metric.title()}: {' > '.join(ranking)}")
    
    # Recommendations
    if comparison['recommendations']:
        print("\n   Recommendations:")
        for rec in comparison['recommendations']:
            print(f"     - {rec}")
    
    # 2. Task performance analysis
    print("\n2. Task Performance Analysis")
    task_analysis = analyzer.analyze_task_performance(results_data)
    
    for task_type, task_data in task_analysis.items():
        print(f"\n   {task_type.title()} Tasks:")
        stats = task_data['overall_stats']
        print(f"     - Total runs: {stats['total_runs']}")
        print(f"     - Success rate: {stats['success_rate']:.1%}")
        print(f"     - Avg response time: {stats['avg_response_time']:.2f}s")
        print(f"     - Avg quality score: {stats['avg_quality_score']:.1f}/10")
        
        print("     Framework performance:")
        for framework, framework_stats in task_data['frameworks'].items():
            print(f"       - {framework}: {framework_stats['success_rate']:.1%} success, "
                  f"{framework_stats['avg_response_time']:.2f}s, "
                  f"{framework_stats['avg_quality_score']:.1f}/10 quality")
    
    # 3. Performance outliers
    print("\n3. Performance Outlier Detection")
    outliers = analyzer.find_performance_outliers(results_data, threshold_std=1.5)
    
    if outliers:
        for framework, framework_outliers in outliers.items():
            print(f"\n   {framework} outliers:")
            for outlier in framework_outliers:
                print(f"     - Task {outlier['task_id']}: {outlier['response_time']:.2f}s "
                      f"(z-score: {outlier['z_score']:.2f})")
    else:
        print("   No significant outliers detected")
    
    # 4. Generate comprehensive report
    print("\n4. Comprehensive Report Generation")
    report = analyzer.generate_report(results_data)
    
    print("   Generated comprehensive report (first 500 characters):")
    print("   " + "─" * 50)
    print("   " + report[:500].replace('\n', '\n   '))
    if len(report) > 500:
        print("   ... (truncated)")
    print("   " + "─" * 50)
    
    # 5. CSV export
    print("\n5. CSV Export Generation")
    csv_data = analyzer.generate_csv_export(results_data)
    csv_lines = csv_data.split('\n')
    
    print(f"   Generated CSV with {len(csv_lines)} lines")
    print("   Sample CSV data:")
    print("   " + "─" * 50)
    for line in csv_lines[:4]:  # Show header + first 3 data rows
        print("   " + line)
    if len(csv_lines) > 4:
        print("   ... (additional rows)")
    print("   " + "─" * 50)
    
    return comparison, task_analysis, report


def demo_file_operations():
    """Demonstrate file save/load operations."""
    print("\n" + "="*60)
    print("FILE OPERATIONS DEMO")
    print("="*60)
    
    # Create a temporary directory for demo
    import tempfile
    temp_dir = tempfile.mkdtemp()
    print(f"\nUsing temporary directory: {temp_dir}")
    
    try:
        # Create a runner with the temp directory
        runner = BenchmarkRunner(temp_dir)
        
        # Create mock suite and results
        suite = create_quick_suite(["demo_framework"])
        
        # Create minimal mock results
        from datetime import datetime
        from common.benchmarking import BenchmarkResult, BenchmarkStatus
        
        mock_results = {
            "demo_framework": [
                BenchmarkResult(
                    task_id=suite.tasks[0].task_id,
                    framework="demo_framework",
                    agent_role="demo_agent",
                    model_name="demo_model",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    status=BenchmarkStatus.COMPLETED,
                    response="Demo response",
                    metrics={'response_time': 1.5},
                    quality_scores={'overall': 8.0},
                    performance_data={},
                    cost_data={},
                    metadata={'task_type': 'coding'}
                )
            ]
        }
        
        # Save results
        print("\n1. Saving benchmark results...")
        runner._save_suite_results(suite, mock_results)
        
        # List saved files
        results_dir = Path(temp_dir)
        saved_files = list(results_dir.glob("*.json"))
        print(f"   Saved {len(saved_files)} result files:")
        for file in saved_files:
            print(f"     - {file.name}")
        
        # Load and analyze results
        if saved_files:
            print("\n2. Loading and analyzing saved results...")
            analyzer = BenchmarkAnalyzer(temp_dir)
            
            results_data = analyzer.load_results(saved_files[0].name)
            print(f"   Loaded results for suite: {results_data['suite']['name']}")
            print(f"   Frameworks: {list(results_data['results'].keys())}")
            print(f"   Total tasks: {sum(len(fr) for fr in results_data['results'].values())}")
            
            # Generate report from loaded data
            report = analyzer.generate_report(results_data)
            print(f"   Generated report ({len(report)} characters)")
    
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory: {temp_dir}")


def demo_convenience_functions():
    """Demonstrate high-level convenience functions."""
    print("\n" + "="*60)
    print("CONVENIENCE FUNCTIONS DEMO")
    print("="*60)
    
    frameworks = ["demo_framework_1", "demo_framework_2"]
    
    # Note: These would normally execute real benchmarks
    print("\nNote: In a real environment, these functions would execute actual AI agents.")
    print("This demo shows the function interfaces and expected behavior.")
    
    # 1. Create comprehensive suite
    print("\n1. create_comprehensive_benchmark_suite()")
    try:
        suite = create_comprehensive_benchmark_suite(frameworks)
        print(f"   ✓ Created suite with {len(suite.tasks)} tasks")
        print(f"   ✓ Supports {len(suite.frameworks)} frameworks")
        print(f"   ✓ Includes {len(suite.benchmark_types)} benchmark types")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 2. Quick benchmark (would fail without enhanced features)
    print("\n2. run_quick_benchmark()")
    try:
        # This will fail because enhanced features aren't available in demo
        result = run_quick_benchmark(frameworks)
        print(f"   ✓ Completed quick benchmark")
        print(f"   ✓ Results for {len(result['results'])} frameworks")
    except Exception as e:
        print(f"   ✗ Expected error (enhanced features not available): {type(e).__name__}")
        print("   ℹ In a real environment with AI agents, this would execute successfully")
    
    # 3. Analysis function (using mock data)
    print("\n3. analyze_benchmark_results()")
    
    # Create mock results file
    import tempfile
    import json
    
    temp_dir = tempfile.mkdtemp()
    try:
        mock_data = {
            'suite': {'name': 'Demo Suite'},
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
                        'response': 'demo response',
                        'metrics': {'response_time': 2.0},
                        'quality_scores': {'overall': 8.0},
                        'performance_data': {},
                        'cost_data': {},
                        'metadata': {'task_type': 'coding'}
                    }
                ]
            }
        }
        
        results_file = Path(temp_dir) / "demo_results.json"
        with open(results_file, 'w') as f:
            json.dump(mock_data, f)
        
        analysis = analyze_benchmark_results("demo_results.json", temp_dir)
        print(f"   ✓ Analyzed results successfully")
        print(f"   ✓ Generated comparison for {len(analysis['comparison']['frameworks'])} frameworks")
        print(f"   ✓ Created {len(analysis['report'])} character report")
        print(f"   ✓ Found {len(analysis['task_analysis'])} task types")
    
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """Run the complete benchmarking system demo."""
    print("AI Dev Squad - Advanced Benchmarking System Demo")
    print("=" * 60)
    print("This demo showcases the comprehensive benchmarking capabilities")
    print("for comparing AI agent frameworks across multiple dimensions.")
    
    try:
        # 1. Suite creation demo
        comprehensive_suite, quick_suite = demo_suite_creation()
        
        # 2. Task details demo
        demo_task_details(quick_suite)
        
        # 3. Mock execution demo
        suite, results = demo_mock_benchmark_execution()
        
        # 4. Analysis demo
        comparison, task_analysis, report = demo_benchmark_analysis(suite, results)
        
        # 5. File operations demo
        demo_file_operations()
        
        # 6. Convenience functions demo
        demo_convenience_functions()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✓ Flexible benchmark suite creation")
        print("✓ Comprehensive task definitions")
        print("✓ Performance profiling and metrics collection")
        print("✓ Quality evaluation with multiple criteria")
        print("✓ Framework comparison and ranking")
        print("✓ Task-specific performance analysis")
        print("✓ Outlier detection")
        print("✓ Comprehensive reporting")
        print("✓ CSV export capabilities")
        print("✓ File save/load operations")
        print("✓ High-level convenience functions")
        
        print("\nNext Steps:")
        print("- Integrate with actual AI agent frameworks")
        print("- Configure enhanced features (caching, telemetry, etc.)")
        print("- Set up automated benchmark execution")
        print("- Create custom benchmark suites for specific use cases")
        print("- Implement continuous benchmarking in CI/CD pipelines")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())