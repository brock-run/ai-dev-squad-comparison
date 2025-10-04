# docs/adr/ADR-015-adapter-conformance-and-contract-tests-gate.md

## ADR-015: Adapter Conformance & Contract Tests as a Gate

**Status:** Proposed
**Date:** 2025-09-28
**Related:** ADR-007 (Agent API), ADR-008 (Telemetry), ADR-013 (Parity)

### Context

Adapters drift over time, breaking parity and replay. Bake conformance into CI.

### Decision

1. **Contract tests:** All adapters must pass the suite under `tests/contract/` covering:

   * Agent API surface (`configure`, `run_task`, `events`)
   * Safety wrapper usage for exec/FS/net
   * Telemetry emission (event counts/types)
   * Advisory-mode VCS behavior (no-net by default)
2. **CI gate:** PRs touching adapters must upload a **conformance report** (JSON summary + logs).
3. **Version discipline:** Each adapter declares `adapter_version`; major bumps require replay compatibility note.

### Consequences

* Faster reviews, fewer regressions, consistent parity.

### Alternatives Considered

* Manual reviews (slow, error‑prone); framework‑specific tests only (incomplete).

### Implementation Notes

* Reuse the previously provided contract tests and extend as needed; GH Actions job `adapter-contract` blocks merge on failure.
