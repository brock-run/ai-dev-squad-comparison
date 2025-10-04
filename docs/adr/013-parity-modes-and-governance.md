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
