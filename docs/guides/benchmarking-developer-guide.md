# Benchmarking System Developer Guide

This guide provides detailed information for developers who want to extend, customize, or contribute to the AI Dev Squad benchmarking system.

## Architecture Overview

The benchmarking system is built with a modular architecture consisting of four main components:

```
common/
├── benchmarking.py           # Core data structures and convenience functions
├── benchmarking_tasks.py     # Task definitions and suite builders
├── benchmarking_runner.py    # Execution engine and result collection
└── benchmarking_analyzer.py  # Analysis and reporting system
```

### Core Components

#### 1. Data Structures (`benchmarking.py`)
- **BenchmarkTask**: Individual benchmark task definition
- **BenchmarkResult**: Results from task execution
- **BenchmarkSuite**: Collection of tasks for comprehensive testing
- **Enums**: BenchmarkType, BenchmarkStatus, MetricType

#### 2. Task Management (`benchmarking_tasks.py`)
- **BenchmarkSuiteBuilder**: Flexible suite construction
- **Predefined task categories**: Coding, Architecture, Testing, Debugging
- **Task factories**: Quick, performance-focused, quality-focused suites

#### 3. Execution Engine (`benchmarking_runner.py`)
- **BenchmarkRunner**: Main execution coordinator
- **QualityEvaluator**: Multi-criteria quality assessment
- **PerformanceProfiler**: Resource usage monitoring

#### 4. Analysis System (`benchmarking_analyzer.py`)
- **BenchmarkAnalyzer**: Result analysis and comparison
- **Report generation**: Comprehensive and CSV formats
- **Outlier detection**: Statistical analysis of performance anomalies

## Extending the System

### Adding New Task Types

#### 1. Define Task Category
```python
# In benchmarking_tasks.py
def add_custom_tasks(self) -> 'BenchmarkSuiteBuilder':
    """Add custom benchmark tasks."""
    custom_tasks = [
        BenchmarkTask(
            task_id="custom_001",
            name="Custom Task Type",
            description="Description of custom task",
            task_type=TaskType.CUSTOM,  # Define new type if needed
            prompt="Custom task prompt...",
            evaluation_criteria={
                'custom_criterion': {
                    'parameter1': 'value1',
                    'parameter2': 'value2'
                }
            }
        )
    ]
    
    self.tasks.extend(custom_tasks)
    if BenchmarkType.CUSTOM not in self.benchmark_types:
        self.benchmark_types.append(BenchmarkType.CUSTOM)
    
    return self
```

#### 2. Implement Custom Evaluation
```python
# In benchmarking_runner.py - QualityEvaluator class
def _evaluate_custom_criterion(self, response: str, config: Dict[str, Any], 
                              task: BenchmarkTask) -> float:
    """Evaluate custom criterion."""
    score = 5.0  # Base score
    
    # Implement custom evaluation logic
    parameter1 = config.get('parameter1', 'default')
    parameter2 = config.get('parameter2', 0)
    
    # Custom scoring logic here
    if parameter1 in response:
        score += 2.0
    
    # Return score between 0.0 and 10.0
    return max(0.0, min(10.0, score))

# Register the new evaluation method
def __init__(self):
    self.evaluation_methods = {
        # ... existing methods ...
        'custom_criterion': self._evaluate_custom_criterion
    }
```

### Adding New Metrics

#### 1. Define Metric Type
```python
# In benchmarking.py
class MetricType(Enum):
    # ... existing metrics ...
    CUSTOM_METRIC = "custom_metric"
```

#### 2. Implement Metric Collection
```python
# In benchmarking_runner.py - BenchmarkRunner class
def _collect_metrics(self, task: BenchmarkTask, agent: Any, 
                    profile_data: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """Collect performance metrics."""
    metrics = {}
    
    # ... existing metric collection ...
    
    # Add custom metric
    if hasattr(agent, 'custom_property'):
        metrics[MetricType.CUSTOM_METRIC.value] = agent.custom_property
    
    return metrics
```

### Creating Custom Analyzers

#### 1. Extend BenchmarkAnalyzer
```python
# Create custom_analyzer.py
from common.benchmarking_analyzer import BenchmarkAnalyzer

class CustomBenchmarkAnalyzer(BenchmarkAnalyzer):
    """Custom analyzer with additional analysis capabilities."""
    
    def analyze_custom_dimension(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform custom analysis on benchmark results."""
        custom_analysis = {}
        
        for framework, framework_results in results_data['results'].items():
            # Implement custom analysis logic
            custom_metrics = self._calculate_custom_metrics(framework_results)
            custom_analysis[framework] = custom_metrics
        
        return custom_analysis
    
    def _calculate_custom_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate custom metrics for a framework."""
        # Implement custom metric calculations
        return {
            'custom_score': 0.0,
            'custom_ratio': 1.0
        }
```

#### 2. Generate Custom Reports
```python
def generate_custom_report(self, results_data: Dict[str, Any]) -> str:
    """Generate custom report format."""
    custom_analysis = self.analyze_custom_dimension(results_data)
    
    report_lines = [
        "# Custom Benchmark Report",
        "",
        "## Custom Analysis Results",
        ""
    ]
    
    for framework, metrics in custom_analysis.items():
        report_lines.extend([
            f"### {framework}",
            f"- Custom Score: {metrics['custom_score']:.2f}",
            f"- Custom Ratio: {metrics['custom_ratio']:.2f}",
            ""
        ])
    
    return "\n".join(report_lines)
```

### Framework Integration

#### 1. Agent Adapter Integration
```python
# In your framework implementation
from common.benchmarking_runner import BenchmarkRunner

class CustomFrameworkAdapter:
    """Custom framework adapter for benchmarking."""
    
    def __init__(self):
        self.benchmark_metadata = {
            'framework_name': 'custom_framework',
            'version': '1.0.0',
            'capabilities': ['coding', 'testing']
        }
    
    def execute_benchmark_task(self, task: BenchmarkTask) -> str:
        """Execute a benchmark task using the custom framework."""
        # Implement framework-specific task execution
        response = self._generate_response(task.prompt, task.task_type)
        
        # Add framework-specific metadata
        self._add_benchmark_metadata(task, response)
        
        return response
    
    def _add_benchmark_metadata(self, task: BenchmarkTask, response: str):
        """Add framework-specific metadata for benchmarking."""
        # Store metadata that can be used in analysis
        pass
```

#### 2. Custom Agent Creation
```python
# In benchmarking_runner.py
def _create_agent_for_framework(self, framework: str, task: BenchmarkTask) -> Any:
    """Create an agent for the specified framework."""
    
    # Add support for custom framework
    if framework == "custom_framework":
        return self._create_custom_framework_agent(task)
    
    # ... existing framework creation logic ...

def _create_custom_framework_agent(self, task: BenchmarkTask) -> Any:
    """Create agent for custom framework."""
    # Implement custom agent creation
    from custom_framework import CustomFrameworkAdapter
    
    agent = CustomFrameworkAdapter()
    agent.configure_for_task(task)
    return agent
```

## Performance Optimization

### Parallel Execution
```python
# Optimize parallel execution
class OptimizedBenchmarkRunner(BenchmarkRunner):
    """Optimized benchmark runner with enhanced parallelization."""
    
    def _run_tasks_parallel(self, tasks: List[BenchmarkTask], 
                           framework: str, max_workers: int) -> List[BenchmarkResult]:
        """Enhanced parallel execution with load balancing."""
        
        # Group tasks by complexity
        simple_tasks = [t for t in tasks if self._estimate_complexity(t) < 5]
        complex_tasks = [t for t in tasks if self._estimate_complexity(t) >= 5]
        
        results = []
        
        # Run simple tasks with higher parallelism
        if simple_tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers * 2) as executor:
                simple_results = self._execute_task_batch(simple_tasks, framework, executor)
                results.extend(simple_results)
        
        # Run complex tasks with lower parallelism
        if complex_tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                complex_results = self._execute_task_batch(complex_tasks, framework, executor)
                results.extend(complex_results)
        
        return results
    
    def _estimate_complexity(self, task: BenchmarkTask) -> int:
        """Estimate task complexity for load balancing."""
        complexity = 1
        
        # Factor in prompt length
        complexity += len(task.prompt) // 1000
        
        # Factor in task type
        if task.task_type in [TaskType.ARCHITECTURE, TaskType.DEBUGGING]:
            complexity += 3
        
        # Factor in evaluation criteria
        complexity += len(task.evaluation_criteria)
        
        return complexity
```

### Caching Integration
```python
# Enhanced caching for benchmark results
class CachedBenchmarkRunner(BenchmarkRunner):
    """Benchmark runner with intelligent caching."""
    
    def __init__(self, results_dir: str = None, enable_caching: bool = True):
        super().__init__(results_dir)
        self.enable_caching = enable_caching
        self.cache = {}
    
    def _run_single_task(self, task: BenchmarkTask, framework: str) -> BenchmarkResult:
        """Run single task with caching support."""
        
        if self.enable_caching:
            cache_key = self._generate_cache_key(task, framework)
            if cache_key in self.cache:
                logger.debug(f"Using cached result for {task.task_id}")
                return self.cache[cache_key]
        
        # Execute task normally
        result = super()._run_single_task(task, framework)
        
        # Cache successful results
        if self.enable_caching and result.status == BenchmarkStatus.COMPLETED:
            cache_key = self._generate_cache_key(task, framework)
            self.cache[cache_key] = result
        
        return result
    
    def _generate_cache_key(self, task: BenchmarkTask, framework: str) -> str:
        """Generate cache key for task and framework combination."""
        import hashlib
        
        key_data = f"{framework}:{task.task_id}:{task.prompt}:{task.task_type.value}"
        return hashlib.md5(key_data.encode()).hexdigest()
```

## Testing and Validation

### Unit Testing Custom Components
```python
# test_custom_benchmarking.py
import unittest
from unittest.mock import Mock, patch
from custom_benchmarking import CustomBenchmarkAnalyzer

class TestCustomBenchmarking(unittest.TestCase):
    """Test custom benchmarking components."""
    
    def setUp(self):
        self.analyzer = CustomBenchmarkAnalyzer()
        self.sample_results = {
            'results': {
                'framework1': [
                    {
                        'task_id': 'test_001',
                        'framework': 'framework1',
                        'status': 'completed',
                        'metrics': {'custom_metric': 0.85}
                    }
                ]
            }
        }
    
    def test_custom_analysis(self):
        """Test custom analysis functionality."""
        analysis = self.analyzer.analyze_custom_dimension(self.sample_results)
        
        self.assertIn('framework1', analysis)
        self.assertIn('custom_score', analysis['framework1'])
    
    def test_custom_report_generation(self):
        """Test custom report generation."""
        report = self.analyzer.generate_custom_report(self.sample_results)
        
        self.assertIn('Custom Benchmark Report', report)
        self.assertIn('framework1', report)
```

### Integration Testing
```python
# test_integration.py
def test_end_to_end_custom_benchmark():
    """Test complete custom benchmarking workflow."""
    
    # Create custom suite
    builder = CustomBenchmarkSuiteBuilder()
    suite = builder.add_custom_tasks().build("test_suite", "Test", "Description")
    
    # Run benchmark
    runner = CustomBenchmarkRunner()
    results = runner.run_benchmark_suite(suite)
    
    # Analyze results
    analyzer = CustomBenchmarkAnalyzer()
    analysis = analyzer.analyze_custom_dimension({'results': results})
    
    # Validate results
    assert len(results) > 0
    assert 'custom_score' in analysis
```

## Configuration and Deployment

### Environment Configuration
```python
# config/benchmarking.yaml
benchmarking:
  default_timeout: 300
  max_workers: 4
  enable_caching: true
  enable_tracing: true
  
  frameworks:
    - name: "langgraph"
      enabled: true
      config:
        model: "llama2"
        temperature: 0.1
    
    - name: "crewai"
      enabled: true
      config:
        model: "llama2"
        max_iterations: 5

  task_categories:
    coding:
      enabled: true
      timeout: 180
    architecture:
      enabled: true
      timeout: 600
    testing:
      enabled: false
```

### Docker Integration
```dockerfile
# Dockerfile.benchmarking
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-benchmarking.txt .
RUN pip install -r requirements-benchmarking.txt

# Copy benchmarking system
COPY common/ /app/common/
COPY benchmark/ /app/benchmark/
COPY examples/ /app/examples/

WORKDIR /app

# Run benchmarking
CMD ["python", "-m", "examples.benchmarking_demo"]
```

### CI/CD Integration
```yaml
# .github/workflows/benchmarking.yml
name: Continuous Benchmarking

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-benchmarking.txt
    
    - name: Run benchmarks
      run: |
        python -m examples.benchmarking_demo
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: benchmark_results/
```

## Monitoring and Observability

### Metrics Collection
```python
# Enhanced metrics collection
class ObservableBenchmarkRunner(BenchmarkRunner):
    """Benchmark runner with enhanced observability."""
    
    def __init__(self, results_dir: str = None):
        super().__init__(results_dir)
        self.metrics_collector = MetricsCollector()
    
    def _run_single_task(self, task: BenchmarkTask, framework: str) -> BenchmarkResult:
        """Run task with enhanced metrics collection."""
        
        # Start metrics collection
        self.metrics_collector.start_task_metrics(task.task_id, framework)
        
        try:
            result = super()._run_single_task(task, framework)
            
            # Collect success metrics
            self.metrics_collector.record_task_success(
                task.task_id, 
                framework, 
                result.duration_seconds,
                result.quality_scores.get('overall', 0.0)
            )
            
            return result
            
        except Exception as e:
            # Collect failure metrics
            self.metrics_collector.record_task_failure(task.task_id, framework, str(e))
            raise
        
        finally:
            self.metrics_collector.end_task_metrics(task.task_id, framework)

class MetricsCollector:
    """Collect and export benchmarking metrics."""
    
    def __init__(self):
        self.active_tasks = {}
        self.completed_tasks = []
    
    def start_task_metrics(self, task_id: str, framework: str):
        """Start collecting metrics for a task."""
        self.active_tasks[task_id] = {
            'framework': framework,
            'start_time': time.time(),
            'memory_start': self._get_memory_usage()
        }
    
    def record_task_success(self, task_id: str, framework: str, 
                           duration: float, quality_score: float):
        """Record successful task completion."""
        # Export to monitoring system (Prometheus, etc.)
        pass
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export collected metrics."""
        return {
            'total_tasks': len(self.completed_tasks),
            'active_tasks': len(self.active_tasks),
            'average_duration': self._calculate_average_duration(),
            'success_rate': self._calculate_success_rate()
        }
```

### Dashboard Integration
```python
# Dashboard data provider
class BenchmarkingDashboard:
    """Provide data for benchmarking dashboard."""
    
    def __init__(self, analyzer: BenchmarkAnalyzer):
        self.analyzer = analyzer
    
    def get_framework_comparison_data(self) -> Dict[str, Any]:
        """Get data for framework comparison charts."""
        # Load recent benchmark results
        recent_results = self._load_recent_results()
        
        comparison_data = {}
        for results_file in recent_results:
            results_data = self.analyzer.load_results(results_file)
            comparison = self.analyzer.compare_frameworks(results_data)
            
            # Format for dashboard
            comparison_data[results_file] = {
                'timestamp': results_data.get('timestamp'),
                'frameworks': comparison['frameworks'],
                'metrics': comparison['metrics'],
                'rankings': comparison['rankings']
            }
        
        return comparison_data
    
    def get_trend_data(self, framework: str, metric: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get trend data for a specific framework and metric."""
        # Implementation for trend analysis
        pass
```

## Best Practices

### Code Organization
- Keep task definitions separate from execution logic
- Use dependency injection for framework adapters
- Implement proper error handling and logging
- Follow the existing naming conventions

### Performance
- Use parallel execution for independent tasks
- Implement intelligent caching strategies
- Monitor resource usage and set appropriate limits
- Profile critical paths for optimization opportunities

### Testing
- Write comprehensive unit tests for all components
- Include integration tests for end-to-end workflows
- Test with various framework configurations
- Validate results against known benchmarks

### Documentation
- Document all public APIs and interfaces
- Provide examples for common use cases
- Keep documentation synchronized with code changes
- Include performance characteristics and limitations

## Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd ai-dev-squad-comparison

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/test_benchmarking.py -v
```

### Submission Guidelines
1. Follow the existing code style and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for API changes
4. Include examples demonstrating new features
5. Ensure all tests pass and code coverage is maintained

### Code Review Process
- All changes require review from a maintainer
- Include performance impact analysis for significant changes
- Validate backward compatibility
- Test with multiple framework configurations

This developer guide provides the foundation for extending and customizing the benchmarking system to meet specific requirements and use cases.