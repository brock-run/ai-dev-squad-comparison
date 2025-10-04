# docs/adr/ADR-012-model-routing-and-deterministic-sampling-ollama-first.md

## ADR-012: Model Routing & Deterministic Sampling (Ollama‑first)

**Status:** Proposed
**Date:** 2025-09-28
**Related:** ADR-011 (Seeds), ADR-010 (Consistency)

### Context

Benchmarks should be repeatable on developer hardware. We need routing rules and sampling clamps.

### Decision

1. **Routing by task type:**

   * Code gen/review → code-specialized models (e.g., `codellama`, `deepseek-coder`, `qwen2.5-coder`).
   * Commit/PR text → small instruct (e.g., `gemma:2b/7b`, `llama2-7b-chat`).
   * Repo QA → general instruct ≥13B with retrieval when applicable.
2. **Determinism clamps:** `temperature ≤ 0.2`, fixed `top_p`, **seed required** when supported.
3. **Caching:** Enable local caching; surface cache hits in telemetry.
4. **Fallback chain:** primary local → smaller local → cloud (opt‑in, explicitly flagged in results).

### Consequences

* More stable metrics on modest machines; visible when cloud fallbacks occur.

### Alternatives Considered

* One-size-fits-all model (biases results); cloud-only (costs & privacy).

### Implementation Notes

* Routing table lives in `common/ollama_integration.py` and config under `ollama.model_routing`.

---

# docs/adr/ADR-013-parity-modes-and-governance.md

## ADR-013: Parity Modes & Governance (Autonomous vs Advisory)

**Status:** Proposed
**Date:** 2025-09-28
**Related:** ADR-006 (VCS), ADR-007 (Agent API)

### Context

Frameworks vary in ability to perform VCS writes. We need consistent definitions and CI expectations.

### Decision

1. **Modes:**

   * **Autonomous:** Agent performs VCS actions itself.
   * **Advisory:** Agent outputs diffs/plans; harness applies changes.
2. **Parity policy:** Benchmarks prefer Autonomous; if unsupported, run Advisory and mark the parity matrix with ⚠️ and notes.
3. **CI gate:** New adapters must pass Advisory mode contract tests before merge; Autonomous can follow.

### Consequences

* Enables apples-to-apples comparisons without blocking weaker frameworks.

### Alternatives Considered

* Mandate Autonomous only (blocks several adapters); ignore parity (misleading results).

### Implementation Notes

* Parity matrix lives in `docs/parity_matrix.md`; test toggles via `--mode` flag.
