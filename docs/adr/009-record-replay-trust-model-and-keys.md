# docs/adr/ADR-009-record-replay-trust-model-and-keys.md

## ADR-009: Record–Replay Trust Model & Lookup Keys

**Status:** Proposed
**Date:** 2025-09-28
**Related:** ADR-008 (Telemetry), ADR-011 (Config/Seeds), ADR-012 (Deterministic Sampling)

### Context

Deterministic debugging depends on recording IO edges and faithfully substituting them during replay. We need stable keys and normalization rules.

### Decision

1. **What we record:** All **IO edges** (LLM/tool/sandbox/VCS), normalized inputs/outputs, config snapshot, seeds, env digest, and git SHA.
2. **Artifacts layout:**

   ```
   artifacts/<run_id>/
     events.jsonl.zst
     manifest.yaml      # schema_version, hashes, seeds, model ids, git sha
     inputs/            # task config, fixtures
     outputs/           # agent artifacts
     diffs/             # VCS diffs (if any)
   ```
3. **Lookup key (per IO event):** `{event_type, adapter, agent_id, tool_name, call_index, input_fingerprint}` where `input_fingerprint = BLAKE3(prompt+params_normalized)`.
4. **Normalization:** Strip/replace volatile fields (timestamps, UUIDs, absolute paths) before hashing and storage.
5. **Replay policy:** Substitute recorded outputs on key match; **fail-fast** on mismatch and emit `replay_assert`.
6. **Integrity:** `manifest.yaml` contains content hashes; CI verifies integrity and detects tampering.

### Consequences

* High-fidelity replay; detectable drift when code or config changes.
* Small overhead to compute fingerprints and write compressed events.

### Alternatives Considered

* Recompute using seeds only (insufficient across frameworks); full VM snapshots (heavy, non-portable).

### Implementation Notes

* `benchmark/replay/recorder.py` and `player.py`; helpers in `common/telemetry`.
* Input sanitizers pluggable per adapter (e.g., AutoGen group chat indices).
* Compatibility: major adapter version changes invalidate replays; tool checks emit advisory.
