# ADR-016: Replay & Consistency Evaluation Architecture

## Status
Accepted

## Context

The AI Dev Squad Enhancement Platform requires robust mechanisms to evaluate the consistency and reliability of AI agent implementations across multiple runs. This is critical for:

1. **Production Readiness Assessment**: Understanding how consistently an AI agent performs the same task
2. **Framework Comparison**: Comparing reliability across different AI orchestration frameworks
3. **Quality Assurance**: Detecting non-deterministic behavior and performance variance
4. **Continuous Integration**: Automated consistency checks in CI/CD pipelines

The system needs to support both replay capabilities (deterministic re-execution) and consistency evaluation (multi-run analysis with variance assessment).

## Decision

We implement a comprehensive **Replay & Consistency Evaluation** system with the following architecture:

### 1. Multi-Run Execution Engine

**Component**: `MultiRunExecutor`
- Executes multiple runs of the same task with different seeds
- Supports both parallel and sequential execution
- Provides configurable timeout and resource limits
- Generates deterministic seeds for reproducible results

**Key Features**:
- Parallel execution using ProcessPoolExecutor to avoid GIL limitations
- Seed-based deterministic execution for reproducibility
- Comprehensive error handling and result collection
- Progress tracking and execution summaries

### 2. Consensus Analysis Framework

**Component**: `ConsensusAnalyzer`
- Analyzes agreement across multiple run results
- Supports multiple consensus strategies:
  - **Majority Vote**: Simple majority decision on verification results
  - **Weighted Vote**: Weighted by verification scores
  - **Unanimous**: Requires all runs to agree
  - **Threshold**: Configurable percentage threshold
  - **Best-of-N**: Consensus among top-performing runs

**Key Features**:
- Pluggable consensus strategies
- Confidence scoring for consensus decisions
- Outlier detection and exclusion options
- Quality-weighted voting mechanisms

### 3. Variance Analysis System

**Component**: `VarianceCalculator`
- Calculates comprehensive variance metrics across runs
- Analyzes multiple dimensions:
  - **Duration Variance**: Execution time consistency
  - **Token Usage Variance**: Resource consumption consistency
  - **Quality Score Variance**: Output quality consistency
  - **Success Rate Analysis**: Reliability assessment

**Key Features**:
- Statistical analysis with confidence intervals
- Outlier detection using multiple methods (Tukey fences, Z-score, Modified Z-score)
- Normality testing for distribution analysis
- Reliability scoring using ADR-010 formula

### 4. Reliability Scoring Algorithm

**Formula** (from ADR-010):
```
reliability_score = 0.6 * success_rate + 0.2 * (1 - clamp(stdev_time, 0, 1)) + 0.2 * (1 - clamp(stdev_tokens, 0, 1))
```

**Labels**:
- **High**: Score ≥ 0.8
- **Medium**: 0.6 ≤ Score < 0.8  
- **Low**: Score < 0.6

### 5. Comprehensive Reporting System

**Component**: `ConsistencyReporter`
- Generates structured JSON reports with full analysis
- Provides dashboard-compatible data formats
- Supports multiple output formats and visualizations
- Integrates with existing telemetry and observability systems

**Report Structure**:
```json
{
  "schema_version": "1.0",
  "framework": "langgraph",
  "task": "simple_code_generation",
  "consensus": {
    "decision": true,
    "confidence": 0.85,
    "strategy": "majority"
  },
  "variance": {
    "success_rate": {"value": 0.8, "confidence_interval": [0.6, 0.95]},
    "duration": {"mean": 2.3, "std": 0.4, "coefficient_of_variation": 0.17}
  },
  "reliability": {
    "score": 0.82,
    "label": "High"
  },
  "individual_runs": [...]
}
```

### 6. Dashboard Integration

**Features**:
- Real-time consistency monitoring
- Framework reliability comparison
- Variance visualization with violin plots
- Success rate confidence intervals
- Drill-down capabilities for detailed analysis

### 7. CLI Integration

**Commands**:
```bash
# Basic consistency evaluation
make consistency F=langgraph T=simple_code_generation

# Custom parameters
make consistency-custom F=crewai T=bug_fixing RUNS=10 STRATEGY=weighted SEEDS=42,123,456

# CI smoke tests
make consistency-smoke
```

### 8. Configuration Management

**Seed Management**:
- Deterministic seed generation from base seed
- Custom seed specification for reproducibility
- Seed governance following ADR-011

**Execution Configuration**:
- Parallel vs sequential execution
- Resource limits and timeouts
- Output directory management
- Strategy selection and parameters

## Implementation Details

### Multi-Run Execution Flow

1. **Configuration**: Create `ConsistencyRunConfig` with task parameters
2. **Seed Generation**: Generate deterministic seeds for all runs
3. **Parallel Execution**: Use ProcessPoolExecutor for isolated runs
4. **Result Collection**: Aggregate results with error handling
5. **Summary Generation**: Create execution summary with metrics

### Consensus Analysis Process

1. **Data Extraction**: Extract verification results from run outputs
2. **Strategy Application**: Apply selected consensus strategy
3. **Confidence Calculation**: Compute confidence based on agreement
4. **Outlier Handling**: Detect and optionally exclude outliers
5. **Decision Generation**: Make final consensus decision with metadata

### Variance Calculation Workflow

1. **Metric Extraction**: Extract timing, token, and quality metrics
2. **Statistical Analysis**: Calculate means, standard deviations, confidence intervals
3. **Outlier Detection**: Identify statistical outliers using multiple methods
4. **Normality Testing**: Test for normal distribution using Shapiro-Wilk
5. **Reliability Scoring**: Apply ADR-010 formula for overall reliability

### Dashboard Data Flow

1. **Report Scanning**: Scan consistency report directory
2. **Data Aggregation**: Aggregate reports by framework and task
3. **Visualization Preparation**: Generate chart-ready data structures
4. **Real-time Updates**: Provide WebSocket updates for new reports

## Rationale

### Why Multi-Strategy Consensus?

Different use cases require different consensus approaches:
- **Majority Vote**: Simple, interpretable for most cases
- **Weighted Vote**: Accounts for quality differences
- **Unanimous**: Critical applications requiring perfect agreement
- **Threshold**: Configurable strictness levels
- **Best-of-N**: Focus on top-performing runs

### Why Comprehensive Variance Analysis?

Understanding variance across multiple dimensions provides insights into:
- **Performance Consistency**: Duration variance indicates execution stability
- **Resource Predictability**: Token variance affects cost predictability
- **Quality Reliability**: Score variance indicates output consistency
- **Overall Reliability**: Combined metric for production readiness

### Why Parallel Execution?

- **Efficiency**: Significantly faster than sequential execution
- **Isolation**: ProcessPoolExecutor provides process isolation
- **Scalability**: Configurable worker count for different environments
- **Resource Management**: Better resource utilization

### Why Dashboard Integration?

- **Visibility**: Real-time monitoring of consistency trends
- **Comparison**: Side-by-side framework reliability comparison
- **Analysis**: Interactive drill-down for detailed investigation
- **Reporting**: Executive-level reliability dashboards

## Consequences

### Positive

1. **Reliability Assessment**: Quantitative reliability scoring for all frameworks
2. **Production Readiness**: Clear criteria for production deployment decisions
3. **Framework Comparison**: Objective comparison of framework consistency
4. **Quality Assurance**: Automated detection of consistency issues
5. **CI Integration**: Automated consistency checks in development workflow
6. **Observability**: Comprehensive visibility into agent behavior variance

### Negative

1. **Execution Time**: Multiple runs increase total execution time
2. **Resource Usage**: Higher computational and storage requirements
3. **Complexity**: Additional configuration and analysis complexity
4. **Storage Requirements**: Detailed reports require significant storage

### Neutral

1. **Learning Curve**: Teams need to understand consistency metrics
2. **Configuration Management**: Additional configuration parameters to manage
3. **Report Management**: Need processes for report retention and cleanup

## Compliance

This ADR complies with:
- **ADR-010**: Self-Consistency Evaluation Policy (reliability scoring formula)
- **ADR-011**: Configuration Precedence and Seed Governance (seed management)
- **ADR-012**: Model Routing and Deterministic Sampling (deterministic execution)
- **ADR-008**: Telemetry Event Schema and OpenTelemetry Strategy (observability integration)

## Implementation Status

### Week 2 Implementation (Completed)

- ✅ **Day 1-2**: Multi-run executor, consensus analyzer, variance calculator
- ✅ **Day 3**: Reporter, CLI flags, consistency smoke tests for CI
- ✅ **Day 4**: Dashboard minimal integration (consistency tab)
- ✅ **Day 5**: Polish with examples, Make targets, ADR documentation

### Future Enhancements

- **Advanced Outlier Detection**: Machine learning-based outlier detection
- **Trend Analysis**: Historical consistency trend analysis
- **Alerting**: Automated alerts for consistency degradation
- **A/B Testing**: Framework A/B testing with consistency metrics
- **Cost-Consistency Tradeoffs**: Analysis of cost vs consistency relationships

## References

- [ADR-010: Self-Consistency Evaluation Policy](./010-self-consistency-evaluation-policy.md)
- [ADR-011: Configuration Precedence and Seed Governance](./011-configuration-precedence-and-seed-governance.md)
- [ADR-012: Model Routing and Deterministic Sampling](./012-model-routing-and-deterministic-sampling-ollama-first.md)
- [Adjustment Plan v0.3](../requirements/v0.3/adjustment-plan.md)
- [Benchmarking Developer Guide](../guides/benchmarking-developer-guide.md)

## Examples

See `examples/consistency_demo.py` for a complete demonstration of the consistency evaluation system.

## Testing

Run consistency smoke tests:
```bash
make consistency-smoke
```

Run full consistency evaluation:
```bash
make consistency F=langgraph T=simple_code_generation
```

View results in dashboard:
```bash
make dashboard
# Navigate to http://localhost:5000/consistency
```