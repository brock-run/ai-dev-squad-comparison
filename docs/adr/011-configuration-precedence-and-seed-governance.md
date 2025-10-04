# docs/adr/ADR-011-configuration-precedence-and-seed-governance.md

## ADR-011: Configuration Precedence & Seed Governance

**Status:** Proposed
**Date:** 2025-09-28
**Related:** ADR-007 (Agent API), ADR-008, ADR-010, Configuration Management System

### Context

Configs are split across env and YAML; seeds are inconsistent, hurting reproducibility.

### Decision

1. **Precedence:** **ENV > CLI > YAML > Defaults**.
2. **Seed bus:** A single `base_seed` produces per-run and per-agent seeds deterministically (e.g., `hash(base_seed, run_index, agent_id)`), exposed via `context.seed`.
3. **Propagation:** Adapters must pass seeds to underlying frameworks/models where supported; otherwise record the inability in telemetry.
4. **Provenance:** Every run writes a `manifest.yaml` with config digest, seeds, model ids, adapter versions, git SHA. CI gate rejects missing provenance.

### Consequences

* Reproducible runs; simpler debugging and comparisons.
* Requires modest adapter changes to plumb seeds.

### Alternatives Considered

* YAML-only or ENV-only; both insufficient for CI and local dev ergonomics.

### Implementation Notes

* Implemented in `common/config.py`; add `--seed` and `--seed.strategy` flags to CLI.
