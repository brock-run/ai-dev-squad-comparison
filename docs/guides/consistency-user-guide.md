# Consistency Evaluation User Guide

## Overview

The Consistency Evaluation system helps you assess how reliably your AI agents perform across multiple runs of the same task. This is crucial for understanding production readiness and comparing different AI frameworks.

## What is Consistency Evaluation?

Consistency evaluation runs the same task multiple times with different random seeds and analyzes:

- **Success Rate**: How often the agent completes the task successfully
- **Consensus**: Whether multiple runs agree on the results
- **Variance**: How much performance varies between runs
- **Reliability Score**: Overall reliability assessment (0.0 to 1.0)

## Quick Start

### 1. Basic Consistency Check

Run a simple consistency evaluation for any framework:

```bash
make consistency F=langgraph T=simple_code_generation
```

This will:
- Run the task 5 times with different seeds
- Analyze consensus using majority vote
- Generate a detailed report
- Show results in the dashboard

### 2. View Results

Start the dashboard to see visual results:

```bash
make dashboard
```

Then navigate to `http://localhost:5000/consistency` to see:
- Framework reliability scores
- Success rate confidence intervals
- Duration variance analysis
- Individual run details

### 3. Run Smoke Tests

Test that everything is working:

```bash
make consistency-smoke
```

## Understanding the Results

### Reliability Score

The reliability score (0.0 to 1.0) combines three factors:

- **60%** - Success rate across runs
- **20%** - Duration consistency (lower variance = higher score)
- **20%** - Token usage consistency (lower variance = higher score)

**Labels:**
- **High** (≥0.8): Ready for production use
- **Medium** (0.6-0.8): Suitable for development/testing
- **Low** (<0.6): Needs improvement before production

### Consensus Decision

The consensus decision indicates whether multiple runs agree:

- **PASS**: Majority of runs succeeded and agreed
- **FAIL**: Majority failed or disagreed significantly
- **Confidence**: How certain we are about the decision (0-100%)

### Variance Metrics

- **Duration CV**: Coefficient of variation for execution time
  - <0.1: Very consistent
  - 0.1-0.3: Moderately consistent  
  - >0.3: Highly variable

- **Success Rate CI**: Confidence interval for success rate
  - Narrow interval: Consistent performance
  - Wide interval: Unpredictable performance

## Common Use Cases

### 1. Production Readiness Assessment

Before deploying an AI agent to production:

```bash
# Run comprehensive evaluation
make consistency-custom F=your_framework T=your_task RUNS=10 STRATEGY=weighted

# Check reliability score in dashboard
# Look for "High" reliability (≥0.8) before production deployment
```

### 2. Framework Comparison

Compare reliability across different frameworks:

```bash
# Test each framework on the same task
make consistency F=langgraph T=code_generation
make consistency F=crewai T=code_generation  
make consistency F=autogen T=code_generation

# Compare results in dashboard
```

### 3. Performance Optimization

Identify and fix consistency issues:

```bash
# Run with detailed analysis
make consistency-custom F=your_framework T=your_task RUNS=15 STRATEGY=unanimous

# Look for:
# - High duration variance (optimize for speed consistency)
# - Low success rate (fix reliability issues)
# - Poor consensus (improve determinism)
```

### 4. CI/CD Integration

Add consistency checks to your CI pipeline:

```bash
# In your CI script
make consistency-smoke  # Quick smoke test
make consistency F=your_framework T=critical_task RUNS=3  # Critical path check
```

## Advanced Configuration

### Custom Number of Runs

More runs give better statistical confidence but take longer:

```bash
# Quick check (3 runs)
make consistency F=langgraph T=simple_task RUNS=3

# Standard check (5 runs) - default
make consistency F=langgraph T=simple_task

# Thorough check (10+ runs)
make consistency F=langgraph T=simple_task RUNS=15
```

### Consensus Strategies

Choose the right strategy for your use case:

```bash
# Majority vote (default) - most common
make consistency F=langgraph T=task STRATEGY=majority

# Weighted by quality scores - for nuanced decisions
make consistency F=langgraph T=task STRATEGY=weighted

# Unanimous agreement - for critical applications
make consistency F=langgraph T=task STRATEGY=unanimous

# Custom threshold - configurable strictness
make consistency F=langgraph T=task STRATEGY=threshold THRESHOLD=0.8

# Best performers only - focus on top results
make consistency F=langgraph T=task STRATEGY=best_of_n
```

### Deterministic Seeds

Use specific seeds for reproducible results:

```bash
make consistency-custom F=langgraph T=task SEEDS=42,123,456,789,101
```

### Sequential vs Parallel Execution

```bash
# Parallel (default) - faster
make consistency F=langgraph T=task

# Sequential - more controlled
make consistency F=langgraph T=task PARALLEL=false
```

## Interpreting Dashboard Visualizations

### Framework Reliability Chart
- Bar chart showing reliability scores by framework
- Higher bars = more reliable frameworks
- Aim for scores above 0.8 for production

### Reliability Distribution
- Pie chart showing High/Medium/Low reliability tasks
- More green (High) = better overall reliability

### Duration Variance Scatter Plot
- X-axis: Average duration
- Y-axis: Coefficient of variation
- Points closer to bottom = more consistent timing

### Success Rate Confidence Intervals
- Bars show success rates with error bars
- Narrower error bars = more predictable success rates

## Troubleshooting

### Low Reliability Scores

**Problem**: Reliability score below 0.6

**Solutions**:
1. Check success rate - fix failing runs first
2. Reduce duration variance - optimize for consistent performance
3. Improve determinism - ensure reproducible results

### High Variance

**Problem**: High coefficient of variation (>0.3)

**Solutions**:
1. Add caching to reduce execution time variance
2. Use fixed parameters instead of random choices
3. Implement timeout handling for consistent duration

### Poor Consensus

**Problem**: Low confidence in consensus decisions

**Solutions**:
1. Increase number of runs for better statistics
2. Use weighted strategy to account for quality differences
3. Check for non-deterministic behavior in your agent

### No Results in Dashboard

**Problem**: Dashboard shows no consistency reports

**Solutions**:
1. Check that reports are being generated in `comparison-results/consistency/`
2. Verify dashboard is reading from correct directory
3. Run `make consistency-smoke` to test the system

## Best Practices

### 1. Start Small
- Begin with 3-5 runs for quick feedback
- Increase to 10+ runs for production assessment

### 2. Use Appropriate Tasks
- Test on representative real-world tasks
- Include both simple and complex scenarios
- Test edge cases and error conditions

### 3. Monitor Trends
- Run consistency checks regularly
- Track reliability scores over time
- Set up alerts for reliability degradation

### 4. Set Standards
- Define minimum reliability thresholds for your use case
- Document acceptable variance levels
- Create consistency requirements for production deployment

### 5. Combine with Other Testing
- Use consistency evaluation alongside unit tests
- Include in integration testing workflows
- Complement with manual quality assessment

## Getting Help

- **Examples**: See `examples/consistency_demo.py` for complete workflow
- **Architecture**: Read `docs/adr/016-replay-and-consistency-evaluation.md`
- **Developer Guide**: See `docs/guides/consistency-developer-guide.md`
- **Issues**: Check logs in `comparison-results/consistency/` directory

## Next Steps

1. Run your first consistency evaluation
2. Explore the dashboard visualizations
3. Set up regular consistency monitoring
4. Integrate into your CI/CD pipeline
5. Use results to improve agent reliability