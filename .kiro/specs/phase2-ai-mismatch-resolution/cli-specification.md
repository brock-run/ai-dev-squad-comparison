# Phase 2 CLI Specification

## Command Structure

```bash
# Analysis Commands
ai-replay analyze <recording_file> [options]
ai-replay bench analyze --dataset <path> --output <results.json>

# Resolution Commands  
ai-replay resolve <mismatch_id> [--strategy <strategy>] [--preview] [--apply]
ai-replay resolve batch <mismatch_file> [--parallel <n>] [--dry-run]

# Replay Commands
ai-replay replay <recording_file> [--mode intelligent|adaptive|semantic] [--auto-resolve]
ai-replay replay --from-checkpoint <checkpoint_id> --ai-enhanced

# Learning Commands
ai-replay learn --pattern <pattern_file> --validate
ai-replay learn --export-patterns --since <date> --format json|yaml

# Policy Commands
ai-replay policy validate <policy_file>
ai-replay policy apply <policy_file> [--environment dev|stage|prod]
ai-replay policy rollback --trigger-fp-rate 0.02

# Monitoring Commands
ai-replay monitor --metrics resolution_rate,fp_rate,cost --period 7d
ai-replay monitor --alerts --threshold fp_rate:0.02,cost_daily:100.0
```

## Command Details

### `ai-replay analyze`

Analyze mismatches in a recording file or dataset.

```bash
ai-replay analyze recording.jsonl \
  --output analysis.json \
  --types whitespace,json_ordering \
  --confidence-min 0.8 \
  --budget-max 10.0 \
  --parallel 4
```

**Options**:
- `--output, -o`: Output file for analysis results
- `--types`: Comma-separated list of mismatch types to analyze
- `--confidence-min`: Minimum confidence threshold (0.0-1.0)
- `--budget-max`: Maximum cost budget for analysis ($)
- `--parallel, -p`: Number of parallel analysis workers
- `--model`: AI model to use (gpt-4, llama3.1:8b)
- `--embedding`: Embedding model for semantic analysis
- `--cache`: Enable/disable result caching
- `--verbose, -v`: Verbose output with detailed analysis

**Output**:
```json
{
  "analysis_id": "uuid",
  "recording_file": "recording.jsonl", 
  "total_mismatches": 42,
  "analyzed": 38,
  "skipped": 4,
  "by_type": {
    "whitespace": {"count": 15, "avg_confidence": 0.95},
    "json_ordering": {"count": 12, "avg_confidence": 0.98},
    "semantics_text": {"count": 11, "avg_confidence": 0.73}
  },
  "cost_breakdown": {
    "analysis": 2.45,
    "embedding": 1.20,
    "llm_calls": 3.15,
    "total": 6.80
  },
  "duration_ms": 12450,
  "recommendations": [
    {
      "type": "auto_resolve_candidate",
      "mismatch_ids": ["uuid1", "uuid2"],
      "reason": "High confidence whitespace normalization"
    }
  ]
}
```

### `ai-replay resolve`

Resolve individual or batch mismatches.

```bash
# Single mismatch resolution
ai-replay resolve mismatch_123 \
  --strategy semantic_text \
  --preview \
  --require-approval

# Batch resolution
ai-replay resolve batch mismatches.jsonl \
  --parallel 8 \
  --dry-run \
  --confidence-min 0.9 \
  --safety-level advisory
```

**Options**:
- `--strategy`: Resolution strategy (auto, semantic_text, whitespace_norm, etc.)
- `--preview`: Show resolution preview without applying
- `--apply`: Apply resolution after preview
- `--require-approval`: Require human approval before applying
- `--confidence-min`: Minimum confidence for auto-resolution
- `--safety-level`: Safety level (experimental, advisory, automatic)
- `--rollback-checkpoint`: Create rollback checkpoint before applying
- `--dual-key`: Require dual-key approval for destructive actions

### `ai-replay replay`

Enhanced replay with AI-powered mismatch resolution.

```bash
ai-replay replay recording.jsonl \
  --mode intelligent \
  --auto-resolve \
  --policy policy.yaml \
  --output replay_results.json
```

**Replay Modes**:
- `intelligent`: AI-powered mismatch resolution with learning
- `adaptive`: Learns and adjusts during replay
- `semantic`: Focus on semantic equivalence detection
- `progressive`: Becomes more lenient over time
- `strict`: Traditional exact matching (Phase 1 compatibility)

**Options**:
- `--mode`: Replay mode (see above)
- `--auto-resolve`: Enable automatic resolution for safe mismatches
- `--policy`: Resolution policy file to use
- `--shadow`: Run in shadow mode (analyze but don't resolve)
- `--from-checkpoint`: Resume from specific checkpoint
- `--until-step`: Stop replay at specific step
- `--budget-limit`: Maximum cost budget for AI operations
- `--timeout`: Maximum time for AI analysis per mismatch

### `ai-replay learn`

Manage learning system and patterns.

```bash
# Export learned patterns
ai-replay learn --export-patterns \
  --since 2025-09-01 \
  --format yaml \
  --output patterns.yaml

# Validate pattern file
ai-replay learn --pattern patterns.yaml --validate

# Import patterns from another environment
ai-replay learn --import-patterns prod_patterns.yaml --merge
```

### `ai-replay policy`

Manage resolution policies.

```bash
# Validate policy file
ai-replay policy validate policy.yaml

# Apply policy to environment
ai-replay policy apply policy.yaml --environment prod --dry-run

# Set up automatic rollback triggers
ai-replay policy rollback \
  --trigger-fp-rate 0.02 \
  --trigger-cost-spike 100.0 \
  --action disable_auto_resolve \
  --notification slack,pagerduty
```

### `ai-replay monitor`

Monitor AI resolution system performance.

```bash
# Real-time metrics
ai-replay monitor \
  --metrics resolution_rate,fp_rate,cost,latency \
  --period 24h \
  --refresh 30s

# Set up alerts
ai-replay monitor --alerts \
  --threshold fp_rate:0.02,cost_daily:100.0,latency_p95:5000 \
  --webhook https://alerts.company.com/ai-replay

# Generate reports
ai-replay monitor --report \
  --period 7d \
  --format html \
  --output weekly_report.html \
  --include-charts
```

## Configuration File

```yaml
# ~/.ai-replay/config.yaml
ai_services:
  primary_provider: openai
  models:
    llm: gpt-4-turbo-2024-04-09
    embedding: text-embedding-3-large
  
  openai:
    api_key: ${OPENAI_API_KEY}
    timeout: 30s
    max_retries: 3
  
  fallback:
    provider: ollama
    endpoint: http://localhost:11434
    model: llama3.1:8b

resolution:
  default_policy: policy.phase2.default
  auto_resolve_threshold: 0.9
  safety_level: advisory
  require_preview: true
  
budgets:
  daily_cost_limit: 100.0
  per_analysis_limit: 0.10
  alert_threshold: 80.0

monitoring:
  telemetry_endpoint: http://localhost:4317
  metrics_retention: 30d
  alert_webhook: ${ALERT_WEBHOOK_URL}

cache:
  enabled: true
  ttl: 1h
  max_size: 1GB
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: Configuration error
- `4`: AI service unavailable
- `5`: Budget exceeded
- `6`: Policy violation
- `7`: Rollback triggered
- `8`: Timeout exceeded

## Environment Variables

- `AI_REPLAY_CONFIG`: Path to configuration file
- `AI_REPLAY_LOG_LEVEL`: Logging level (debug, info, warn, error)
- `AI_REPLAY_BUDGET_LIMIT`: Override daily budget limit
- `AI_REPLAY_POLICY`: Override default policy file
- `AI_REPLAY_SHADOW_MODE`: Force shadow mode (true/false)
- `OPENAI_API_KEY`: OpenAI API key
- `OLLAMA_BASE_URL`: Ollama service URL

## Examples

### Basic Workflow

```bash
# 1. Analyze a recording for mismatches
ai-replay analyze recording.jsonl --output analysis.json

# 2. Review analysis results
cat analysis.json | jq '.recommendations'

# 3. Resolve high-confidence mismatches
ai-replay resolve batch analysis.json \
  --confidence-min 0.9 \
  --preview \
  --apply

# 4. Replay with AI enhancement
ai-replay replay recording.jsonl \
  --mode intelligent \
  --auto-resolve \
  --output results.json
```

### Production Deployment

```bash
# 1. Validate policy before deployment
ai-replay policy validate prod_policy.yaml

# 2. Deploy in shadow mode first
ai-replay policy apply prod_policy.yaml \
  --environment prod \
  --shadow-mode \
  --duration 14d

# 3. Monitor shadow mode performance
ai-replay monitor \
  --metrics fp_rate,resolution_rate \
  --period 14d \
  --environment prod

# 4. Enable auto-resolution if metrics are good
ai-replay policy apply prod_policy.yaml \
  --environment prod \
  --enable-auto-resolve
```

This CLI specification provides concrete, actionable commands for all Phase 2 functionality with proper error handling, budgeting, and safety controls.