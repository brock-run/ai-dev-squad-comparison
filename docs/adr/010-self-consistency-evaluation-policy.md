# docs/adr/ADR-010-self-consistency-evaluation-policy.md

## ADR-010: Self‑Consistency Evaluation Policy

**Status:** Proposed
**Date:** 2025-09-28
**Related:** ADR-008, ADR-009, ADR-011, ADR-012

### Context

Single-shot benchmarks amplify randomness. We need a standard, explainable multi-run policy to compare frameworks fairly.

### Decision

1. **Default runs:** `N=5` with **seed variation**. Temperature/prompt variation are opt-in flags.
2. **Consensus:** Majority vote on `verified_pass`. Optional **quality-weighted** vote if verifier yields score ∈ [0,1].
3. **Reliability score:**

   ```
   success_rate = passes / N
   stdev_time   = std(zscore(duration))
   stdev_tokens = std(zscore(tokens))
   reliability  = 0.6*success_rate + 0.2*(1 - clamp(stdev_time,0,1)) + 0.2*(1 - clamp(stdev_tokens,0,1))
   ```

   Labels: High (≥0.8), Medium (0.6–0.8), Low (<0.6).
4. **Outliers:** Tukey fences on duration or verification score. Do not exclude unless `--exclude-outliers` is set.
5. **Reporting:** Emit `consistency.json` per task/framework with CI-friendly schema and 95% CIs for continuous metrics.

### Consequences

* Clear, reproducible comparisons; small overhead to run N>1.
* Avoids conflating randomness sources unless explicitly requested.

### Alternatives Considered

* LLM-as-judge scoring only (opaque); strict seed-only reproducibility (not supported by all frameworks/models).

### Implementation Notes

* Lives under `benchmark/consistency/`; integrates with existing BenchmarkSuite and verifier results.
* CLI flags: `--consistency.runs`, `--consistency.strategy`, `--parallel`.
