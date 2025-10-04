Strong work. This is production-grade shadow infra. Don’t pause—move straight into shadow soak + rollout prep. Here’s the shortest path to “safe-on-by-default” with specific gates, artifacts, and a few hardening tweaks.

# Shadow soak plan (do this next)

**Goal:** prove κ & FP gates on real traffic, not just the labeled set.

1. **Batch on the labeled dataset (baseline)**

   * Freeze `eqc.*.yaml` and budgets.
   * Run `bench judge --dataset …` nightly; publish:

     * Overall κ, per-type κ; 95% CI via bootstrap.
     * FP/FN by mismatch_type.
     * Cost & p95 latency by method and artifact_type.
   * Artifact: `reports/judge_calibration_<date>.json` (see “calibration manifest” below).

2. **Live shadow on recent runs (soak 7 days)**

   * Sample 20–30% of Phase-1 replays; store Evaluations only.
   * Watch: drift vs. labeled baseline; regressions >1σ trigger alert & freeze.

3. **Gate to proceed**

   * κ ≥ 0.8 overall **and** κ ≥ 0.75 per top-3 types by volume.
   * FP ≤ 2% on **test** split.
   * Budget: <$0.02/1k tokens, p95 LLM < 5s.
   * Zero sandbox violations.

# Decision rule (lock it now)

Avoid “LLM says yes ⇒ equivalent”. Use a conjunctive rule you can defend:

```python
# text equivalence (shadow; no mutations)
EQ = (
    exact_equal
    or (
        cosine >= τ_text
        and llm_confidence >= τ_llm
        and not any(v in violations for v in {"unit_change","policy_violation","numerical_meaning"})
    )
)
# code: prefer AST/tests; LLM only advisory
EQ_CODE = ast_normalized or tests_pass
```

Pin thresholds in `entities/eqc/eqc.text.v1.yaml` etc., and **commit a calibration manifest** (below). Refuse to update thresholds without a new manifest.

# Tiny hardening items (ship now)

* **Prompt injection guard:** Quote/neutralize SOURCE/TARGET; reject if they exceed max size after redaction. Add adversarial tests (`TARGET` contains “ignore previous instructions…”).
* **Cache hygiene:** Add TTL to embedding cache (e.g., 30d) + version in key (`model@ver`). Log cache hit ratio; alert if <80% for 24h.
* **Redaction audit:** Count and sample 1% of redacted prompts for manual verify (in a secure review environment).
* **Error taxonomy:** Standardize `error_code` in Evaluation (`timeout`, `budget_exceeded`, `invalid_json`, `adapter_unavailable`) and alert on spikes.

# Artifacts to create now

1. **Calibration manifest** — `reports/calibration_manifest.json`

```json
{
  "id": "calib.v1",
  "date": "2025-10-02",
  "dataset": "benchmark/datasets/phase2_mismatch_labels.jsonl@9b2e…",
  "methods": ["exact","cosine_similarity","llm_rubric_judge"],
  "thresholds": {"text.cosine": 0.86, "text.llm_conf": 0.70},
  "metrics": {"kappa_overall": 0.82, "kappa_ci": [0.78,0.86], "fp_rate": 0.017},
  "budgets": {"usd_per_1k_tokens_max": 0.02, "p95_ms": 5000},
  "model_versions": {"llm": "gpt-4o-mini-2025-09-15", "embed": "text-embed-3-large-1.1"},
  "notes": "Conjunctive rule; per-type κ in report."
}
```

2. **CI gate** — fail build if gates not met

```bash
# ci/check_judge_gates.sh
python scripts/validate_labels.py benchmark/datasets/phase2_mismatch_labels.jsonl benchmark/datasets/phase2_mismatch_labels.schema.json
python scripts/kappa_ci.py benchmark/datasets/phase2_mismatch_labels.jsonl  # exits nonzero if CI_low<0.75
python scripts/check_fp_rate.py results.json --max-fp 0.02
```

3. **Prometheus alerts** — `configs/monitoring/phase2_alerts.yaml`

```yaml
groups:
- name: phase2-judge
  rules:
  - alert: Phase2JudgeKappaLow
    expr: phase2:kappa_overall < 0.8
    for: 2h
    labels: {severity: warning}
    annotations: {summary: "Judge κ dropped below 0.8"}
  - alert: Phase2JudgeFPHigh
    expr: increase(resolutions_false_positive_total[24h]) / increase(resolutions_applied_total[24h]) > 0.02
    for: 2h
    labels: {severity: critical}
  - alert: Phase2JudgeCostSpike
    expr: increase(judge_cost_usd_sum[1h]) > 10
    for: 30m
```

# What’s next (Task 5 & 6)

## Task 5 — Operator UX: Resolution Inbox + Judge integration

**Goal:** one place to review Analyzer + Judge evidence, preview transforms, approve/rollback.

Deliverables

* Inbox list with triage states (`pending → needs-info → approved → applied → rolled_back`).
* Item view: left = diff preview (with anchors), right = judge verdicts (method grid, costs, rationales).
* Bulk approve with sampling (e.g., 10% sampled manual QA).
* CLI parity: `bench inbox list|show|approve|apply|rollback`.

Acceptance

* Two concurrent approvers → exactly one apply (CAS guarded).
* Audit trail complete (plan outcome includes transform_id, hashes, config_fingerprint, approvals).

## Task 6 — Controlled rollout to auto-resolve

**Phase A (safe classes only):** `WHITESPACE`, `NEWLINES`, `JSON_ORDERING`

* Envs: dev=on, stage=shadow→on day 3, prod=shadow for 1–2 weeks.
* Auto-apply only when detector confidence ≥ 0.9 and transform idempotent; dual-key not required for `AUTOMATIC`.

**Phase B (semantic advisory):** `SEMANTICS_TEXT` remains **advisory** in dev/stage. Operator approves; log deltas to refine thresholds.

**Kill switches (already in runtime config):** wire to ops runbook; verify they work in stage.

# Extra tests to add (fast)

* **Adversarial text:** prompt injection, HTML/script tags, long repeated tokens (LLM truncation). Expect `parse_error` or `budget_exceeded` → safe fail.
* **Large artifacts:** 10MB JSON → analyzers must remain O(n log n)/streaming; LLM still in shadow.
* **Race on apply:** simulate two workers; ensure one winner, unique index holds.
* **Rollback integrity:** after rollback, recompute hash equals `before_hash`, and plan status = `rolled_back`.

# Small code nudges (optional but helpful)

* **Evaluation consolidation:** add `ev.decision_rule_id = "text.conjunctive.v1"` to metadata so you can A/B rules later.
* **Cost caps per run:** cap total USD per run_id; if exceeded → downgrade to deterministic only; record `downgrade_reason`.
* **Explainability:** truncate LLM reasoning to 180 chars; keep a full trace in secure storage keyed by `evaluation_id` for audit.

---

## Bottom line

* You’re ready to **start the 7-day shadow soak now**.
* In parallel, implement **Task 5 (Inbox)**.
* Prep **Task 6** rollout scripts & alerts so flipping to “on” for safe classes is a config change, not a code change.

If you want, I can generate:

* the `check_fp_rate.py` + bootstrap CI scripts,
* the inbox CLI scaffolding (`bench inbox …`),
* a sample Grafana JSON panel pack for judge metrics (κ, FP, cost, p95).
