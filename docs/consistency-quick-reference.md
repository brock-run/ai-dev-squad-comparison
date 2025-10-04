# Consistency Evaluation Quick Reference

## 🚀 Quick Commands

```bash
# Basic consistency check
make consistency F=langgraph T=simple_code_generation

# Custom configuration
make consistency-custom F=crewai T=bug_fixing RUNS=10 STRATEGY=weighted

# CI smoke test
make consistency-smoke

# View dashboard
make dashboard  # Navigate to /consistency
```

## 📊 Reliability Scores

| Score | Label | Meaning | Action |
|-------|-------|---------|--------|
| ≥0.8 | **High** | Production ready | ✅ Deploy with confidence |
| 0.6-0.8 | **Medium** | Development ready | ⚠️ Monitor closely |
| <0.6 | **Low** | Needs improvement | ❌ Fix before production |

## 🤝 Consensus Strategies

| Strategy | Use Case | Description |
|----------|----------|-------------|
| `majority` | General use | Simple majority vote (default) |
| `weighted` | Quality matters | Weighted by verification scores |
| `unanimous` | Critical systems | All runs must agree |
| `threshold` | Custom strictness | Configurable percentage (e.g., 80%) |
| `best_of_n` | Top performers | Focus on best results only |

## 📈 Variance Indicators

### Duration Coefficient of Variation (CV)
- **<0.1**: Very consistent ✅
- **0.1-0.3**: Moderately consistent ⚠️
- **>0.3**: Highly variable ❌

### Success Rate Confidence Intervals
- **Narrow**: Predictable performance ✅
- **Wide**: Unpredictable performance ❌

## 🛠️ Configuration Options

### Number of Runs
```bash
RUNS=3   # Quick check
RUNS=5   # Standard (default)
RUNS=10+ # Thorough analysis
```

### Execution Mode
```bash
PARALLEL=true   # Faster (default)
PARALLEL=false  # More controlled
```

### Custom Seeds
```bash
SEEDS=42,123,456,789,101  # Reproducible results
```

## 📋 Report Structure

```json
{
  "consensus": {
    "decision": true,        // PASS/FAIL
    "confidence": 0.85,      // 0.0-1.0
    "strategy": "majority"
  },
  "variance": {
    "success_rate": {"value": 0.8, "confidence_interval": [0.6, 0.95]},
    "duration": {"mean": 2.3, "coefficient_of_variation": 0.17}
  },
  "reliability": {
    "score": 0.82,          // 0.0-1.0
    "label": "High"         // High/Medium/Low
  }
}
```

## 🎯 Common Use Cases

### Production Readiness
```bash
make consistency-custom F=your_framework T=critical_task RUNS=10 STRATEGY=weighted
# Look for reliability ≥0.8
```

### Framework Comparison
```bash
make consistency F=langgraph T=same_task
make consistency F=crewai T=same_task
# Compare reliability scores in dashboard
```

### CI Integration
```bash
make consistency-smoke                    # Quick validation
make consistency F=framework T=task RUNS=3  # Critical path check
```

## 🔍 Troubleshooting

| Problem | Symptom | Solution |
|---------|---------|----------|
| Low reliability | Score <0.6 | Fix failing runs, reduce variance |
| High variance | CV >0.3 | Add caching, improve determinism |
| Poor consensus | Low confidence | Increase runs, check for non-determinism |
| No dashboard data | Empty results | Check `comparison-results/consistency/` |

## 📁 File Locations

```
comparison-results/consistency/     # Generated reports
examples/consistency_demo.py        # Complete demo
tests/test_consistency_smoke.py     # Smoke tests
docs/guides/consistency-user-guide.md      # User guide
docs/guides/consistency-developer-guide.md # Developer guide
docs/adr/016-replay-and-consistency-evaluation.md  # Architecture
```

## 🔗 Quick Links

- **User Guide**: [consistency-user-guide.md](guides/consistency-user-guide.md)
- **Developer Guide**: [consistency-developer-guide.md](guides/consistency-developer-guide.md)
- **Architecture**: [ADR-016](adr/016-replay-and-consistency-evaluation.md)
- **Demo**: `examples/consistency_demo.py`

## 💡 Pro Tips

1. **Start small**: Use 3-5 runs for quick feedback
2. **Use weighted strategy**: For tasks with quality scores
3. **Monitor trends**: Track reliability over time
4. **Set thresholds**: Define minimum reliability for production
5. **Combine with other tests**: Use alongside unit/integration tests