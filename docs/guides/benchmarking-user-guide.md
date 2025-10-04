# Benchmarking System User Guide

The AI Dev Squad platform includes a comprehensive benchmarking system that allows you to evaluate and compare AI agent frameworks across multiple dimensions including performance, quality, cost, and reliability.

## Overview

The benchmarking system provides:

- **Framework-agnostic benchmarking** across all supported AI frameworks
- **Multi-dimensional evaluation** including performance, quality, cost, and reliability metrics
- **Flexible task definitions** for different types of development scenarios
- **Comprehensive reporting** with rankings and actionable recommendations
- **Integration with observability systems** for detailed analysis

## Quick Start

### Running a Basic Benchmark

```python
from common.benchmarking import run_quick_benchmark

# Define frameworks to test
frameworks = ["langgraph", "crewai", "haystack"]

# Run quick benchmark
results = run_quick_benchmark(frameworks, results_dir="my_results")

print(f"Benchmark completed for {len(results['results'])} frameworks")
print(f"Summary: {results['summary']}")
```

### Creating a Custom Benchmark Suite

```python
from common.benchmarking_tasks import BenchmarkSuiteBuilder

# Build a custom suite
builder = BenchmarkSuiteBuilder()
suite = (builder
         .add_coding_tasks()
         .add_testing_tasks()
         .add_frameworks(["langgraph", "crewai"])
         .add_configuration({
             'timeout_seconds': 300,
             'parallel_execution': True
         })
         .build(
             suite_id="my_custom_suite",
             name="Custom Development Benchmark",
             description="Focused on coding and testing capabilities"
         ))

# Run the benchmark
from common.benchmarking_runner import BenchmarkRunner
runner = BenchmarkRunner("results")
results = runner.run_benchmark_suite(suite)
```

## Benchmark Types

### Performance Benchmarking
Measures response time, throughput, and resource usage:

```python
from common.benchmarking_tasks import create_performance_focused_suite

frameworks = ["langgraph", "crewai"]
suite = create_performance_focused_suite(frameworks)
```

**Metrics Collected:**
- Response time (seconds)
- Throughput (tokens/operations per second)
- Memory usage (MB)
- CPU usage (percentage)
- Cache hit rates

### Quality Benchmarking
Evaluates output quality across multiple criteria:

```python
from common.benchmarking_tasks import create_quality_focused_suite

frameworks = ["haystack", "llamaindex"]
suite = create_quality_focused_suite(frameworks)
```

**Quality Criteria:**
- Length appropriateness
- Keyword presence/absence
- Structure and formatting
- Code quality (if applicable)
- Completeness against requirements
- Accuracy compared to expected outputs

### Comprehensive Benchmarking
Tests all aspects of framework capabilities:

```python
from common.benchmarking import create_comprehensive_benchmark_suite

frameworks = ["langgraph", "crewai", "haystack", "autogen"]
suite = create_comprehensive_benchmark_suite(frameworks)
```

**Includes:**
- Coding tasks (functions, classes, algorithms)
- Architecture tasks (system design, API design)
- Testing tasks (unit tests, test strategies)
- Debugging tasks (bug analysis, performance optimization)
- Documentation tasks (API docs, technical specs)

## Task Categories

### Coding Tasks
Test code generation and modification capabilities:

- **Simple Functions**: Basic utility functions with error handling
- **Class Design**: Object-oriented programming with methods and validation
- **Algorithm Implementation**: Sorting, searching, and data structure algorithms
- **API Integration**: REST API interaction with authentication and error handling

### Architecture Tasks
Evaluate system design and planning abilities:

- **System Design**: Scalable application architectures
- **API Design**: RESTful endpoint design with proper HTTP methods
- **Microservices**: Service boundaries and communication patterns

### Testing Tasks
Assess testing and quality assurance capabilities:

- **Unit Test Creation**: Comprehensive test suites with edge cases
- **Test Strategy**: Testing approaches and automation plans
- **Performance Testing**: Load and stress testing strategies

### Debugging Tasks
Test problem-solving and optimization skills:

- **Bug Analysis**: Identifying and fixing code issues
- **Performance Issues**: Optimization and complexity improvements

## Configuration Options

### Suite Configuration
```python
configuration = {
    'timeout_seconds': 300,        # Maximum time per task
    'parallel_execution': True,    # Run tasks in parallel
    'max_workers': 4,             # Number of parallel workers
    'enable_caching': True,       # Use caching for performance
    'enable_tracing': True        # Enable distributed tracing
}
```

### Task-Specific Settings
```python
from common.benchmarking_tasks import BenchmarkTask
from common.ollama_integration import TaskType, MessageImportance

task = BenchmarkTask(
    task_id="custom_001",
    name="Custom Task",
    description="A custom benchmark task",
    task_type=TaskType.CODING,
    prompt="Write a function to...",
    timeout_seconds=120,
    importance=MessageImportance.HIGH,
    evaluation_criteria={
        'length_check': {
            'min_length': 100,
            'max_length': 500,
            'optimal_length': 250
        },
        'keyword_presence': {
            'required': ['def', 'return'],
            'forbidden': ['eval', 'exec']
        }
    }
)
```

## Results Analysis

### Loading and Analyzing Results
```python
from common.benchmarking import analyze_benchmark_results

# Analyze saved results
analysis = analyze_benchmark_results("benchmark_results_20241201_143022.json")

print("Framework Comparison:")
for framework, metrics in analysis['comparison']['metrics'].items():
    print(f"  {framework}: {metrics}")

print("\nRecommendations:")
for rec in analysis['comparison']['recommendations']:
    print(f"  - {rec}")
```

### Generating Reports
```python
from common.benchmarking_analyzer import BenchmarkAnalyzer

analyzer = BenchmarkAnalyzer("results")
results_data = analyzer.load_results("my_results.json")

# Generate comprehensive report
report = analyzer.generate_report(results_data)
print(report)

# Export to CSV
csv_data = analyzer.generate_csv_export(results_data)
with open("results.csv", "w") as f:
    f.write(csv_data)
```

### Performance Outlier Detection
```python
# Find performance outliers
outliers = analyzer.find_performance_outliers(results_data, threshold_std=2.0)

for framework, framework_outliers in outliers.items():
    print(f"{framework} outliers:")
    for outlier in framework_outliers:
        print(f"  Task {outlier['task_id']}: {outlier['response_time']:.2f}s")
```

## Integration with Enhanced Features

### Cost Tracking
The benchmarking system automatically integrates with the cost tracking system:

```python
# Cost data is automatically collected in results
for framework, results in benchmark_results.items():
    for result in results:
        cost_info = result.cost_data
        print(f"Task {result.task_id}: ${cost_info.get('total_cost_usd', 0):.4f}")
```

### Telemetry and Tracing
Enable distributed tracing for detailed analysis:

```python
# Tracing is automatically enabled when available
# View traces in Jaeger UI at http://localhost:16686
```

### Caching Integration
Leverage caching for improved performance:

```python
# Caching is automatically used when enabled
# Check cache hit rates in results
for result in results:
    cache_hit_rate = result.metrics.get('cache_hit_rate', 0)
    print(f"Cache hit rate: {cache_hit_rate:.1%}")
```

## Best Practices

### Choosing Frameworks
- Start with 2-3 frameworks for initial comparison
- Include both established and newer frameworks
- Consider your specific use case requirements

### Task Selection
- Use comprehensive suites for thorough evaluation
- Use focused suites for specific capability assessment
- Create custom tasks for domain-specific requirements

### Result Interpretation
- Focus on overall trends rather than individual task results
- Consider multiple metrics (performance, quality, reliability)
- Review recommendations for actionable improvements

### Performance Optimization
- Use parallel execution for faster benchmarking
- Enable caching for repeated operations
- Set appropriate timeouts based on task complexity

## Troubleshooting

### Common Issues

**Benchmark fails to start:**
```bash
# Check framework availability
python -c "from common.benchmarking_runner import BenchmarkRunner; print('OK')"

# Verify enhanced features
python -c "from common.ollama_integration import create_agent; print('Enhanced features available')"
```

**Tasks timeout frequently:**
```python
# Increase timeout in configuration
configuration = {
    'timeout_seconds': 600,  # Increase from default 300
    'max_workers': 2         # Reduce parallelism
}
```

**Memory issues with large suites:**
```python
# Use sequential execution
results = runner.run_benchmark_suite(suite, parallel=False)

# Or reduce task count
builder = BenchmarkSuiteBuilder()
suite = builder.add_coding_tasks().build(...)  # Only coding tasks
```

### Getting Help

- Check the examples in `examples/benchmarking_demo.py`
- Review test cases in `tests/test_benchmarking.py`
- See the developer guide for advanced customization
- Check logs for detailed error information

## Example Workflows

### Framework Evaluation Workflow
```python
# 1. Quick assessment
quick_results = run_quick_benchmark(["framework1", "framework2"])

# 2. Detailed analysis of promising frameworks
detailed_frameworks = ["framework1"]  # Based on quick results
comprehensive_suite = create_comprehensive_benchmark_suite(detailed_frameworks)
detailed_results = runner.run_benchmark_suite(comprehensive_suite)

# 3. Generate final report
analysis = analyze_benchmark_results("detailed_results.json")
print(analysis['report'])
```

### Continuous Benchmarking
```python
import schedule
import time

def run_daily_benchmark():
    frameworks = ["langgraph", "crewai"]
    results = run_quick_benchmark(frameworks, f"daily_{datetime.now().strftime('%Y%m%d')}")
    # Send results to monitoring system
    
schedule.every().day.at("02:00").do(run_daily_benchmark)

while True:
    schedule.run_pending()
    time.sleep(60)
```

This benchmarking system provides comprehensive evaluation capabilities to help you make informed decisions about AI framework selection and optimization.