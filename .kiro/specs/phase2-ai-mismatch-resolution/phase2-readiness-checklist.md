# Phase 2 Readiness Checklist & Answers

## 9 Critical Questions - Answered

### 1. What's the authoritative list of mismatch_type for Phase 2 MVP?

**Answer**: 8 types for MVP, prioritized by safety and frequency:

```python
class MismatchType(Enum):
    # Tier 1: Safe auto-resolution (Day 1)
    WHITESPACE = "whitespace"              # Spaces, tabs, newlines
    JSON_ORDERING = "json_ordering"        # Key ordering, formatting
    
    # Tier 2: Advisory resolution (Week 2)
    MARKDOWN_FORMATTING = "markdown_formatting"  # Headers, lists, emphasis
    
    # Tier 3: Experimental (Week 4+)
    SEMANTICS_TEXT = "semantics_text"      # Meaning-preserving text changes
    SEMANTICS_CODE = "semantics_code"      # Functionally equivalent code
    NONDETERMINISM = "nondeterminism"      # Random/time-dependent outputs
    
    # Tier 4: Analysis only (No auto-resolution)
    POLICY_VIOLATION = "policy_violation"   # Security/compliance issues
    ENV_DRIFT = "env_drift"                # Environment differences
```

### 2. Do we have a labeled dataset with per-type counts and inter-rater agreement?

**Answer**: **NO - BLOCKING ISSUE**. Must create before Task 1.

**Required Dataset**:
- 200+ real mismatches from existing replay runs
- 3 independent labelers per mismatch
- Inter-rater agreement ≥ 0.8 (Cohen's kappa)
- Distribution target:
  - whitespace: 40 examples
  - json_ordering: 35 examples  
  - markdown_formatting: 30 examples
  - semantics_text: 25 examples
  - semantics_code: 20 examples
  - nondeterminism: 25 examples
  - policy_violation: 15 examples
  - env_drift: 10 examples

**Action**: Create `benchmark/datasets/phase2_mismatch_labels.jsonl` before starting implementation.

### 3. Which environments allow auto-apply on day 1 (dev/stage/prod)?

**Answer**: 
- **Dev**: whitespace, json_ordering (automatic)
- **Stage**: whitespace, json_ordering (automatic)  
- **Prod**: json_ordering only (automatic), whitespace (advisory)
- **All others**: shadow mode for 2 weeks minimum

### 4. What's the rollback SLO (time from FP detection → disabled policy)?

**Answer**: 
- **Detection**: ≤ 1 hour (automated monitoring)
- **Disable**: ≤ 5 minutes (automated circuit breaker)
- **Notification**: ≤ 15 minutes (PagerDuty alert)
- **Investigation**: ≤ 4 hours (human response)

### 5. Are code artifacts test-runnable in CI for semantic acceptance?

**Answer**: **PARTIALLY**. 
- Python: Yes (pytest in sandbox)
- JavaScript/TypeScript: Yes (jest/vitest)
- Other languages: No (manual review required)

**Constraint**: Code semantic resolution disabled until test execution is available.

### 6. What are the cost/latency budgets we will enforce in code?

**Answer**:
```yaml
budgets:
  analysis:
    max_latency_ms: 5000  # 5 seconds per mismatch
    max_cost_per_100kb: 0.10  # $0.10 per 100KB analyzed
  
  semantic_judge:
    max_latency_ms: 10000  # 10 seconds for LLM calls
    max_cost_per_1k_tokens: 0.02  # $0.02 per 1K tokens
  
  resolution:
    max_latency_ms: 2000  # 2 seconds to apply resolution
    max_cost_per_resolution: 0.05  # $0.05 per resolution
  
  daily_limits:
    max_total_cost: 100.0  # $100/day total
    max_llm_calls: 10000   # 10K LLM calls/day
```

### 7. Which model(s) and embedding(s) are approved; how are they version-pinned?

**Answer**:
```yaml
approved_models:
  primary:
    llm: "gpt-4-turbo-2024-04-09"  # Version pinned
    embedding: "text-embedding-3-large"
    
  fallback:
    llm: "llama3.1:8b"  # Local Ollama
    embedding: "nomic-embed-text"
    
  version_policy:
    pin_duration: "90d"  # 90 days before upgrade
    upgrade_approval: ["security-team", "platform-team"]
    rollback_sla: "1h"
```

### 8. Where will we visualize resolution metrics (dashboard IDs)?

**Answer**:
- **Primary**: `/dashboard/ai-resolution` (existing telemetry dashboard)
- **Ops**: Grafana dashboard `ai-mismatch-resolution-ops`
- **Business**: Weekly reports to `#ai-platform-metrics` Slack

**Key Metrics**:
- Resolution success rate by type
- False positive rate (7-day rolling)
- Cost per resolution
- Latency p95/p99
- User satisfaction scores

### 9. Do we need per-tenant policies or a global one?

**Answer**: **Global policy for MVP**, per-tenant in Phase 3.

**Rationale**: Complexity vs. value. Global policy with environment-based rules covers 90% of use cases.

## Gate-by-Gate Execution Plan

### Gate 0 (D-7): Foundation Ready
**Deliverables**:
- [ ] Labeled dataset (200+ examples) with ≥0.8 inter-rater agreement
- [ ] Baseline metrics from existing replay system
- [ ] Budget caps encoded in config files
- [ ] Final enums and schemas pass CI validation
- [ ] Provenance fields standardized across Phase 1 integration

**Acceptance Criteria**:
- Dataset reviewed by 3 independent experts
- Baseline metrics show current false positive rate
- All schemas validate against existing Phase 1 data
- Cost monitoring infrastructure deployed

### Gate 1 (D-5): Core Analysis Ready
**Deliverables**:
- [ ] MismatchAnalyzer with deterministic classifiers
- [ ] JSON/whitespace canonicalizers working
- [ ] Provenance tracking end-to-end
- [ ] Semantic judge in shadow mode (no decisions)

**Acceptance Criteria**:
- 95%+ accuracy on Tier 1 mismatch types (whitespace, json_ordering)
- All analysis results include full provenance chain
- Shadow semantic judge running without impacting performance
- Rollback system tested with synthetic failures

### Gate 2 (D-3): Limited Auto-Resolution
**Deliverables**:
- [ ] Auto-resolve enabled for whitespace + json_ordering in dev/stage
- [ ] Production runs in shadow mode for all types
- [ ] Circuit breakers and monitoring active
- [ ] Resolution preview and diff generation working

**Acceptance Criteria**:
- ≤1% false positive rate on enabled types
- All resolutions include preview diffs
- Circuit breakers trigger correctly in test scenarios
- Shadow mode data collection working in production

### Gate 3 (Release): Full Phase 2
**Deliverables**:
- [ ] Semantic text resolution enabled based on shadow results
- [ ] Learning system active with pattern recognition
- [ ] Interactive resolution interface deployed
- [ ] Full monitoring and alerting operational

**Acceptance Criteria**:
- ≥70% auto-resolution rate on benign mismatches
- ≤2% false positive rate with 95% confidence interval
- Learning system shows measurable improvement over 2 weeks
- User satisfaction ≥4.0/5.0 in initial feedback

## "Start Task 1" Readiness Checklist

**FAIL ANY ⇒ DON'T START**

- [ ] **Dataset**: 200+ labeled mismatches with inter-rater agreement ≥0.8
- [ ] **Schemas**: All YAML entities validate in CI
- [ ] **Enums**: Final mismatch_type, status, error_code enums locked
- [ ] **Provenance**: Standardized fields (run_id, artifact_ids, diff_id, costs, seeds)
- [ ] **Budget**: Cost/latency caps encoded and enforced
- [ ] **Baseline**: Current system metrics captured for comparison
- [ ] **Infrastructure**: Monitoring, alerting, and rollback systems ready
- [ ] **Approvals**: Security, QA, and platform teams signed off

## Risk Mitigation Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Judge over-accepts pretty rewrites | Medium | High | Deterministic validators + rubric penalizing content loss; sample reviews on bulk approvals |
| Schema drift breaks integration | Medium | Medium | Versioned entities + CI cross-ref validation; migration docs for enum changes |
| Cost spikes from LLM usage | Medium | Medium | Budget caps + progressive mode; daily cost reports per mismatch type |
| Data leakage in logs | Low | High | Redaction + scoped KMS; secure review environment; PII scanning on artifacts |
| Learning system degrades quality | Low | High | Drift monitors + auto-disable triggers; versioned model rollback capability |
| User rejection of AI suggestions | High | Medium | Transparent explanations + user control; gradual rollout with feedback loops |

## Success Metrics (Measurable)

### Technical Metrics
- **Auto-resolution rate**: ≥70% on held-out test set
- **False positive rate**: ≤2% with 95% confidence interval  
- **Latency**: p95 ≤ 5 seconds analysis, p95 ≤ 2 seconds resolution
- **Cost efficiency**: ≤$0.10 per 100KB analyzed
- **Availability**: ≥99.5% uptime for AI services

### Business Metrics  
- **User productivity**: 70% reduction in manual mismatch investigation time
- **User satisfaction**: ≥4.0/5.0 rating for AI resolution features
- **Adoption rate**: 90% of teams using AI features within 30 days
- **Quality improvement**: 25% reduction in replay failure rate

### Learning Metrics
- **Pattern recognition**: 85% accuracy on similar mismatch classification
- **Improvement rate**: 10% monthly improvement in auto-resolution accuracy
- **Knowledge sharing**: 80% of resolution patterns shared across teams

This readiness checklist ensures we don't ship surprises and have concrete success criteria before starting implementation.