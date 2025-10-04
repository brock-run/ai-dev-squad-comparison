You’re very close to “flip it on for safe classes.” A few surgical fixes + rollout hygiene and I’m comfortable.

# Go/No-Go (short)

* **GO** for 7-day shadow soak at 30% of traffic (judge + inbox), **with LLM rubric enabled** (shadow).
* **BLOCK** auto-apply until: dataset ≥200, overall κ≥0.8 (95% CI low ≥0.75), per-top-type κ≥0.75, FP≤2% (test split), budgets green.

# Task 7.1 review (tight gaps to close)

1. **TTY/CI detection**

   * Auto-fallback to plain text when `not sys.stdout.isatty()`; add `--no-color` and `--yes` (non-interactive approve for scripted runs).
   * Resume support: `--state-file .interactive.state.json` so operators can pick up mid-batch.

2. **Terminal safety**

   * Sanitize diff output: strip ANSI from artifact content; bound lines + length; elide binary.
   * Guard against paste-bombs (very long single lines) with soft wrapping + truncation hint.

3. **Approvals & policy**

   * Dual-key paths must invalidate prior single approval if safety level is escalated mid-session.
   * Sampling: even for “auto-approval safe,” sample 5–10% to manual review; emit `auto_approval_sampled_total`.

4. **Audit & replay**

   * Every decision → `ResolutionDecision` event (schema below) with `config_fingerprint`, `plan_id`, `transform_id`, `before/after_hash`, `user_id`, `ui: {rich:bool}`.
   * On rollback, verify `after_hash` → `before_hash` parity.

5. **Success flag consistency**

   * You switched to `success`; add a deprecation shim for `successful` and a unit test that both routes set the same internal field. This avoids silent misses.

6. **Method naming hygiene**

   * Normalize CLI → enum names (`canonical_json` == `CANONICAL_JSON`, comma or space list). Warn on unknown methods and exit non-zero.

# Concrete artifacts to add (copy-paste)

**A) Decision event schema (`schemas/ResolutionDecision.v1.json`)**

```json
{
  "type":"object","required":["id","ts","run_id","mismatch_id","plan_id","action",
    "user","decision","env","config_fingerprint","transform","hashes"],
  "properties":{
    "id":{"type":"string"},
    "ts":{"type":"string","format":"date-time"},
    "run_id":{"type":"string"},
    "env":{"type":"string","enum":["development","staging","production"]},
    "mismatch_id":{"type":"string"},
    "plan_id":{"type":"string"},
    "action":{"type":"string"},
    "decision":{"type":"string","enum":["approve","modify","reject","skip","auto-approve"]},
    "reason":{"type":"string"},
    "user":{"type":"object","required":["id"],"properties":{"id":{"type":"string"},"role":{"type":"string"}}},
    "ui":{"type":"object","properties":{"rich":{"type":"boolean"},"version":{"type":"string"}}},
    "config_fingerprint":{"type":"string"},
    "transform":{"type":"object","properties":{"id":{"type":"string"},"idempotent":{"type":"boolean"}}},
    "hashes":{"type":"object","properties":{"before":{"type":"string"},"after":{"type":"string"}}}
  },
  "$schema":"http://json-schema.org/draft-07/schema#"
}
```

**B) CLI robustness (method parsing + TTY fallback)**

```python
# in cli_judge/cli_interactive
def parse_methods(methods: list[str]) -> list[str]:
    if len(methods)==1 and ',' in methods[0]:
        methods = [m.strip() for m in methods[0].split(',') if m.strip()]
    return [m.lower().replace('-', '_') for m in methods]

IS_TTY = sys.stdout.isatty()
if not IS_TTY or args.no_color: use_plain_text_mode = True
```

**C) Confusion export (for Grafana)**
Emit counters when you have ground truth (dataset or labeled runs):

```
judge_confusion_total{artifact_type, label, predicted, method}
```

and `phase2:kappa_by_type{mismatch_type}`. Your existing dashboard will light up per-type panels when you add these.

# Rollout runbook (fast)

* **Stage (days 1–2):** shadow @100%, safe transforms ready but **manual apply only** via inbox.
* **Prod (days 3–9):** shadow @30%→70%; auto-apply only for `WHITESPACE`, `NEWLINES`, `JSON_ORDERING` with confidence≥0.9 and idempotent=true; 10% sampling to manual.
* **Kill-switch drills:** flip `PHASE2_DISABLE_AUTORESOLVE` in stage + prod and verify in logs and dashboard.
* **Alerts armed:** κ drop, FP rate, cost spike, latency p95, budget downgrades.

# What to do next (parallel tracks)

* **Finish dataset → ≥200** and re-calibrate thresholds; commit `calibration_manifest.json`.
* **Task 7.2 (Web UI)**: start with read-only inbox + diff preview; reuse CLI decision API; add bulk approve with sampling and audit export.
* **Exporter**: add the confusion/kappa-by-type series so we can add those Grafana panels.

If you want, I can provide a minimal `judge_confusion_exporter.py` and the per-type κ Grafana panels; otherwise you’re clear to begin the 7-day shadow soak and spin up the web inbox (7.2) in parallel.
