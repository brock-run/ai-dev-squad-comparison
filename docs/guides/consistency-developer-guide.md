# Consistency Evaluation Developer Guide

## Architecture Overview

The Consistency Evaluation system is built with a modular architecture that supports multiple consensus strategies, comprehensive variance analysis, and extensible reporting capabilities.

## Core Components

### 1. Multi-Run Executor (`benchmark/consistency/multi_run_executor.py`)

The executor manages parallel execution of multiple benchmark runs with deterministic seeding.

```python
from benchmark.consistency.multi_run_executor import MultiRunExecutor, ConsistencyRunConfig
from common.config import SeedConfig

# Configure execution
config = ConsistencyRunConfig(
    task_config={"name": "test_task", "description": "Test task"},
    adapter_name="test_adapter",
    num_runs=5,
    seed_config=SeedConfig(base_seed=42, deterministic=True),
    parallel=True,
    max_workers=3
)

# Execute runs
executor = MultiRunExecutor(config)
results = await executor.execute_runs()
```

**Key Features**:
- ProcessPoolExecutor for true parallelism
- Deterministic seed generation
- Comprehensive error handling
- Progress tracking and summaries

### 2. Consensus Analyzer (`benchmark/consistency/consensus_analyzer.py`)

Analyzes agreement across multiple runs using various strategies.

```python
from benchmark.consistency.consensus_analyzer import ConsensusAnalyzer, ConsensusStrategy

# Create analyzer with strategy
analyzer = ConsensusAnalyzer(
    strategy=ConsensusStrategy.WEIGHTED_VOTE,
    threshold=0.6,
    weight_by_score=True
)

# Analyze consensus
formatted_results = [r.to_dict() for r in run_results]
consensus_result = analyzer.analyze_consensus(formatted_results)

print(f"Decision: {consensus_result.consensus_decision}")
print(f"Confidence: {consensus_result.confidence}")
```

**Available Strategies**:
- `MAJORITY_VOTE`: Simple majority on verified_pass
- `WEIGHTED_VOTE`: Weighted by verification scores
- `UNANIMOUS`: All runs must agree
- `THRESHOLD`: Configurable percentage threshold
- `BEST_OF_N`: Consensus among top performers

### 3. Variance Calculator (`benchmark/consistency/variance_calculator.py`)

Calculates comprehensive statistical metrics across runs.

```python
from benchmark.consistency.variance_calculator import VarianceCalculator

calculator = VarianceCalculator(confidence_level=0.95)
variance_metrics = calculator.calculate_variance_metrics(benchmark_results)

print(f"Success Rate: {variance_metrics.success_rate}")
print(f"Duration CV: {variance_metrics.duration_cv}")
print(f"Reliability: {variance_metrics.reliability_label}")
```

**Metrics Calculated**:
- Success rates with confidence intervals
- Duration statistics (mean, std, CV, CI)
- Token usage statistics (if available)
- Quality score statistics (if available)
- Outlier detection using multiple methods
- Reliability scoring using ADR-010 formula

### 4. Consistency Reporter (`benchmark/consistency/consistency_reporter.py`)

Generates structured reports and dashboard data.

```python
from benchmark.consistency.consistency_reporter import ConsistencyReporter

reporter = ConsistencyReporter(output_dir=Path("results"))

# Generate comprehensive report
report = reporter.generate_consistency_report(
    framework="test_framework",
    task="test_task",
    results=benchmark_results,
    consensus_result=consensus_result,
    variance_metrics=variance_metrics
)

# Write to file
report_file = reporter.write_consistency_report(
    framework="test_framework",
    task="test_task",
    report=report
)
```

## Extending the System

### Adding New Consensus Strategies

1. Add strategy to `ConsensusStrategy` enum:

```python
class ConsensusStrategy(Enum):
    # Existing strategies...
    CUSTOM_STRATEGY = "custom"
```

2. Implement analysis method in `ConsensusAnalyzer`:

```python
def _analyze_custom_strategy(self, all_runs: List[Dict[str, Any]], 
                           successful_runs: List[Dict[str, Any]]) -> ConsensusResult:
    # Your custom logic here
    pass
```

3. Add to strategy dispatch in `analyze_consensus`:

```python
elif self.strategy == ConsensusStrategy.CUSTOM_STRATEGY:
    return self._analyze_custom_strategy(run_results, successful_runs)
```

### Adding New Variance Metrics

1. Extend `VarianceMetrics` dataclass:

```python
@dataclass
class VarianceMetrics:
    # Existing fields...
    custom_metric_mean: Optional[float] = None
    custom_metric_std: Optional[float] = None
```

2. Add extraction method in `VarianceCalculator`:

```python
def _extract_custom_metric(self, results: List[BenchmarkResult]) -> List[float]:
    values = []
    for result in results:
        # Extract your custom metric
        value = result.metadata.get('custom_metric')
        if value is not None:
            values.append(float(value))
    return values
```

3. Include in `calculate_variance_metrics`:

```python
# Extract custom metric data
custom_values = self._extract_custom_metric(successful_results)
custom_stats = self._calculate_stats_with_ci(custom_values) if custom_values else None
```

### Adding New Outlier Detection Methods

1. Add method to `OutlierDetectionMethod`:

```python
class OutlierDetectionMethod:
    # Existing methods...
    CUSTOM_METHOD = "custom_method"
```

2. Implement detection logic:

```python
def _detect_outliers_custom(self, values: List[float]) -> List[Tuple[int, float]]:
    # Your custom outlier detection logic
    outliers = []
    # ... implementation
    return outliers
```

3. Add to detection dispatch:

```python
elif self.outlier_method == OutlierDetectionMethod.CUSTOM_METHOD:
    return self._detect_outliers_custom(values)
```

## Integration Patterns

### Custom Benchmark Integration

To integrate with your own benchmarking system:

```python
import asyncio
from benchmark.consistency.multi_run_executor import ConsistencyRunConfig
from benchmark.consistency.consensus_analyzer import ConsensusAnalyzer
from benchmark.consistency.variance_calculator import VarianceCalculator
from benchmark.consistency.consistency_reporter import ConsistencyReporter

async def run_custom_consistency_evaluation(task_config, adapter_name):
    # 1. Configure execution
    config = ConsistencyRunConfig(
        task_config=task_config,
        adapter_name=adapter_name,
        num_runs=5
    )
    
    # 2. Execute runs (implement your own executor or use MultiRunExecutor)
    run_results = await execute_your_custom_runs(config)
    
    # 3. Analyze consensus
    analyzer = ConsensusAnalyzer()
    consensus_result = analyzer.analyze_consensus([r.to_dict() for r in run_results])
    
    # 4. Calculate variance
    calculator = VarianceCalculator()
    benchmark_results = [r.benchmark_result for r in run_results if r.benchmark_result]
    variance_metrics = calculator.calculate_variance_metrics(benchmark_results)
    
    # 5. Generate report
    reporter = ConsistencyReporter()
    report = reporter.generate_consistency_report(
        framework=adapter_name,
        task=task_config["name"],
        results=benchmark_results,
        consensus_result=consensus_result,
        variance_metrics=variance_metrics
    )
    
    return report
```

### Dashboard Integration

To add consistency data to your own dashboard:

```python
from benchmark.consistency.consistency_reporter import ConsistencyReporter
from pathlib import Path
import json

def get_consistency_dashboard_data():
    # Load reports
    consistency_dir = Path("comparison-results/consistency")
    reports = []
    
    for report_file in consistency_dir.glob("consistency_*.json"):
        with open(report_file) as f:
            reports.append(json.load(f))
    
    # Generate dashboard data
    reporter = ConsistencyReporter()
    dashboard_data = reporter.generate_dashboard_data(reports)
    
    return dashboard_data
```

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Consistency Check
on: [push, pull_request]

jobs:
  consistency:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          make install-benchmark
          make install-framework F=your_framework
      
      - name: Run consistency smoke tests
        run: make consistency-smoke
      
      - name: Run consistency evaluation
        run: make consistency F=your_framework T=critical_task RUNS=3
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: consistency-reports
          path: comparison-results/consistency/
```

## Configuration Reference

### ConsistencyRunConfig

```python
@dataclass
class ConsistencyRunConfig:
    task_config: Dict[str, Any]          # Task configuration
    adapter_name: str                    # Framework adapter name
    num_runs: int = 5                    # Number of runs to execute
    seed_config: Optional[SeedConfig] = None  # Seed configuration
    parallel: bool = True                # Enable parallel execution
    max_workers: Optional[int] = None    # Max parallel workers
    timeout_per_run: Optional[float] = None  # Timeout per run (seconds)
    output_dir: Optional[Path] = None    # Output directory
    seeds: List[int] = None              # Custom seeds (auto-generated if None)
```

### ConsensusAnalyzer Parameters

```python
def __init__(self, 
             strategy: ConsensusStrategy = ConsensusStrategy.MAJORITY_VOTE,
             threshold: float = 0.6,      # For THRESHOLD strategy
             min_runs: int = 3,           # Minimum runs required
             weight_by_score: bool = True # Weight votes by quality scores
):
```

### VarianceCalculator Parameters

```python
def __init__(self, 
             outlier_method: str = OutlierDetectionMethod.TUKEY_FENCES,
             confidence_level: float = 0.95,  # For confidence intervals
             exclude_outliers: bool = False   # Exclude outliers from calculations
):
```

## Testing

### Unit Tests

Run the consistency smoke tests:

```bash
make consistency-smoke
```

Or run specific test files:

```bash
python -m pytest tests/test_consistency_smoke.py -v
python -m pytest tests/test_consistency_system.py -v
```

### Integration Tests

Test with actual framework implementations:

```bash
# Test with LangGraph
make consistency F=langgraph T=simple_code_generation RUNS=3

# Test with CrewAI
make consistency F=crewai T=bug_fixing RUNS=3
```

### Mock Testing

For development and testing, use the mock results generator:

```python
from examples.consistency_demo import create_mock_run_results

# Create mock results for testing
config = ConsistencyRunConfig(
    task_config={"name": "test"},
    adapter_name="test_adapter",
    num_runs=5
)
mock_results = create_mock_run_results(config)
```

## Performance Considerations

### Parallel Execution

- Uses ProcessPoolExecutor to avoid Python GIL limitations
- Default max_workers = min(num_runs, cpu_count())
- Each run executes in isolated process
- Memory usage scales with number of parallel workers

### Memory Management

- Results are collected incrementally to avoid memory spikes
- Large outputs should be summarized rather than stored in full
- Consider using streaming for very large result sets

### Storage Optimization

- Reports are stored as compressed JSON
- Old reports can be archived or deleted
- Consider implementing report retention policies

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

1. **Import Errors**: Ensure all consistency modules are installed
2. **Seed Issues**: Check that seeds are properly generated and used
3. **Timeout Issues**: Increase `timeout_per_run` for slow tasks
4. **Memory Issues**: Reduce `max_workers` or `num_runs`
5. **Report Issues**: Check file permissions in output directory

### Debugging Tools

```python
# Check execution summary
summary = executor.get_execution_summary()
print(json.dumps(summary, indent=2))

# Examine individual run results
for i, result in enumerate(run_results):
    print(f"Run {i}: success={result.success}, duration={result.duration}")
    if result.error:
        print(f"  Error: {result.error}")
```

## Best Practices

### 1. Error Handling

Always handle potential failures gracefully:

```python
try:
    results = await executor.execute_runs()
except Exception as e:
    logger.error(f"Consistency evaluation failed: {e}")
    # Implement fallback or retry logic
```

### 2. Resource Management

Monitor resource usage during execution:

```python
import psutil

# Monitor memory usage
process = psutil.Process()
memory_before = process.memory_info().rss
# ... run consistency evaluation
memory_after = process.memory_info().rss
print(f"Memory used: {(memory_after - memory_before) / 1024 / 1024:.1f} MB")
```

### 3. Configuration Validation

Validate configuration before execution:

```python
def validate_consistency_config(config: ConsistencyRunConfig):
    assert config.num_runs >= 3, "Need at least 3 runs for meaningful analysis"
    assert config.num_runs <= 50, "Too many runs may cause resource issues"
    if config.seeds:
        assert len(config.seeds) == config.num_runs, "Seed count must match run count"
```

### 4. Result Validation

Validate results before analysis:

```python
def validate_run_results(results: List[RunResult]):
    successful_results = [r for r in results if r.success]
    if len(successful_results) < 2:
        raise ValueError("Need at least 2 successful runs for analysis")
```

## Contributing

### Adding New Features

1. Follow the existing code patterns and architecture
2. Add comprehensive tests for new functionality
3. Update documentation and examples
4. Ensure backward compatibility

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Add docstrings for all public methods
- Include examples in docstrings where helpful

### Testing Requirements

- Unit tests for all new functionality
- Integration tests with mock data
- Performance tests for resource-intensive operations
- Documentation tests for all examples

## References

- [ADR-016: Replay & Consistency Evaluation](../adr/016-replay-and-consistency-evaluation.md)
- [ADR-010: Self-Consistency Evaluation Policy](../adr/010-self-consistency-evaluation-policy.md)
- [Consistency User Guide](./consistency-user-guide.md)
- [Benchmarking Developer Guide](./benchmarking-developer-guide.md)