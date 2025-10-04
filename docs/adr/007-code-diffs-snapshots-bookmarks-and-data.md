# ADR-007: Code Diffs, Snapshots, Bookmarks, and Deterministic Replay

# ADR-007 — Code Diffs, Snapshots, Bookmarks, and Deterministic Replay

**Status**: Accepted

**Date**: 2025-09-27

**Owners**: Agent Platform (DevEx)

**Related**: System Spec (§Provenance), PRD (§Diff & Checkpoints), Onboarding/DevEx Flows (§Changelog/Bookmarks)

---

## 1. Context

Agentic workflows (CrewAI/LangGraph-style) mutate benchmark catalogs, tasks, and rubrics. We need to:

- Capture every accepted change with provenance and rationale.
- Rewind safely to prior states (human/agent checkpoints).
- Deterministically replay a run offline (record → replay) for audit and debugging.
- Create human-friendly bookmarks for fast navigation.
- Visualize side‑by‑side diffs across any two points.

Constraints:

- Minimal infra; must be shippable in days.
- Works locally/offline; cloud optional.
- Plays nicely with Git but is not gated by it.

---

## 2. Decision (summary)

- **Event granularity**: Record **atomic line-level edit events** (OT-style) for fidelity. Every event is **enriched with semantic block/function metadata** (AST/LSP-derived).
- **Snapshots**: Store compressed project snapshots **on semantic boundaries** (branch, approval, PR/merge, run completion, DSPy acceptance) and **periodically** (default **every 80 events** or **every 30 minutes** of active editing, whichever comes first).
- **Bookmarks**: Any event or snapshot may be labeled; bookmarks are first-class anchors used for rewind/replay/diff.
- **Deterministic replay**: Record exact tool/LLM I/O and env manifests during **record mode**; in **replay mode**, stub external calls and verify outputs & digests match prior artifacts.
- **Storage**: Append‑only **events.jsonl** + **snapshots/** (tar.zst) + **diff patch files** (unified) under **.user/ledger/** and **results/**.

Rationale: This balances fidelity (OT) with human ergonomics (semantic grouping) and operational pragmatism (periodic snapshots for fast restore).

---

## 3. Forces & Trade-offs

- **Fidelity vs. complexity**: Keystroke-level OTs are heavy; line-level OTs + semantic enrichment keep replay exact while staying simple.
- **Speed of restore**: Snapshots reduce replay time for long sessions; cadence trades storage for time-to-restore.
- **Git coupling**: Git remains optional. Using git-only would lose agent tool/LLM I/O and non-text artifacts.
- **Determinism**: Requires network stubbing and seed capture; otherwise replay can diverge.

---

## 4. Detailed Rules

### 4.1 Event recording (atomic diffs)

- Record an event for each **accepted** change (agent/human). Proposed changes are preview-only until approved.
- **Action types** (enum):
    - `edit_insert` | `edit_delete` | `edit_replace`
    - `file_create` | `file_delete` | `file_move` | `file_rename`
    - `checkpoint` (bookmark creation) | `rewind` | `branch`
    - `snapshot_create`
    - `eval_run` (benchmark evaluation completed)
    - `meta_note` (free-form annotation/rationale)
- Each event includes: id, timestamp, author (agent/human + version), parent_event_id, run_id, branch, files[], **unified patch path**, **affected_lines[]**, **semantic_block** (function/method/class/module), rationale, and optional links to **artifacts** (tool/LLM traces, eval reports).

### 4.2 Semantic enrichment

- For supported languages, resolve **semantic_block** via AST or LSP (function/method/class). For YAML/JSON, use path-based selectors (e.g., `rubrics.security.criteria[sql_parametrization]`).
- Store `semantic_block_kind` + `semantic_block_id` (e.g., `function:validate_payload`, `yaml_path:/criteria/sql_parametrization`).

### 4.3 Snapshot policy

- **Automatic snapshots** when any of the following triggers occur:
    1. **Semantic boundary**: approval/merge, new branch, PR creation, benchmark run completion, **DSPy optimizer result accepted**.
    2. **Periodic**: every **80** events (configurable `EVENTS_PER_SNAPSHOT`), or every **30m** of active editing (`WALLTIME_SNAPSHOT_INTERVAL`).
    3. **Volume**: if cumulative patch size since last snapshot > **5 MB**.
- **Manual snapshot**: `bench snapshot save <name>` at any time.
- Snapshot content: full workspace (tracked files) + **manifest** (env, seeds, model/tool versions, hashes).

### 4.4 Replay & rewind

- **Rebuild**: restore nearest ≤ target snapshot, then apply events forward to target id; validate file hashes.
- **Replay mode**: external calls are stubbed from recorded artifacts; mismatch → fail with diff of observed vs recorded.
- **Rewind**: creates a `rewind` event; subsequent edits occur on a new branch unless explicitly merged.

### 4.5 Bookmarks

- `bookmark_name -> (event_id | snapshot_id)`; must be unique per project.
- Creating/removing a bookmark writes a `checkpoint` event.

### 4.6 Storage layout (per project)

```
.user/ledger/
  events.jsonl          # append-only event ledger
  bookmarks.json        # name→id map
  snapshots/
    snap-0001.tar.zst
    snap-0002.tar.zst
results/
  diffs/
    diff-evt-*.patch
  artifacts/
    trace-evt-*.json
    eval-*.json

```

### 4.7 Retention & GC

- Keep **all events**; **snapshots**: retain last **K=10** fully, and every Nth older (e.g., every 10th) unless referenced by a bookmark.
- Never GC a snapshot reachable from a bookmark.
- Optionally squash long runs: fold older unbookmarked events into a synthetic patch between surviving snapshots.

### 4.8 Security & privacy

- Tool/LLM traces can include sensitive data; encrypt-at-rest option for `artifacts/`, redact patterns via policy (e.g., secrets, PII) before persist.
- Replay must never leak secrets (use redacted placeholders with deterministic rehydration when authorized).

---

## 5. Data Schemas (normative)

### 5.1 ChangeEvent (JSONL row)

```json
{
  "id": "evt-000123",
  "ts": "2025-09-27T14:05:10Z",
  "author": {"name": "security-agent", "version": "1.2.0", "kind": "agent"},
  "action_type": "edit_replace",
  "branch": "main",
  "run_id": "run-42",
  "parent_event_id": "evt-000122",
  "files": ["rubrics/security.yaml"],
  "diff_path": "results/diffs/diff-evt-000123.patch",
  "affected_lines": [10,11,12],
  "semantic_block": {"kind": "yaml_path", "id": "/criteria/sql_parametrization"},
  "rationale": "Tighten SQL param checks; add stacked query test",
  "artifacts": ["results/artifacts/trace-evt-000123.json"],
  "snapshot_ref": null,
  "bookmark": null
}

```

### 5.2 Snapshot manifest

```json
{
  "id": "snap-0007",
  "ts": "2025-09-27T14:06:00Z",
  "base_event_id": "evt-000120",
  "tar_uri": ".user/ledger/snapshots/snap-0007.tar.zst",
  "env": {"python": "3.11.8", "os": "macOS-14", "llm": "anthropic/claude-3.7"},
  "seeds": {"global": 1337},
  "tools": {"crew": "0.30.1"},
  "hashes": {"rubrics/security.yaml": "sha256:..."}
}

```

### 5.3 Bookmark entry

```json
{"after-new-task": "evt-000101", "candidate-release": "evt-000123"}

```

---

## 6. Interfaces & Commands

- `bench history [--file <path>] [--author <id>] [--branch <name>]` — list events.
- `bench diff <A> <B> [--file <path>] [--side-by-side|--unified]` — render diffs.
- `bench bookmark add <name> [--event <id>|--snapshot <id>]` — create bookmark.
- `bench rewind <bookmark|event_id> [--branch <name>]` — rewind and (default) branch.
- `bench snapshot save <name>` — manual snapshot.
- `bench replay <from>..<to> [--dry-run] [--no-network]` — deterministic replay.
- `bench gc` — apply retention policy.

---

## 7. Alternatives considered

1. **Git-only timeline** (commits/tags as events/bookmarks)
    
    **Pros**: tooling, familiarity. **Cons**: hard to store tool/LLM I/O, coarse granularity, no deterministic replay stubs.
    
2. **Pure OT/CRDT stream** (keystroke-level)
    
    **Pros**: perfect playback & concurrency. **Cons**: heavy infra and storage; harder to ship fast.
    
3. **DB journaling (row-level)**
    
    **Pros**: simple for structured YAML/JSON. **Cons**: loses file-level diffs and editor ergonomics.
    

Chosen design gives us Git-like UX with agent-aware provenance and deterministic replay.

---

## 8. Consequences

**Positive**: High-fidelity audit trail, easy rewind, explainability, offline reproducibility, human-friendly bookmarks.

**Negative**: Additional storage, AST/LSP cost for semantic mapping, engineering for stubbing external calls.

**Neutral/mitigated**: GC policy keeps storage bounded; per-language adapters can degrade gracefully to path-based selectors.

---

## 9. Rollout plan

1. **Phase 1 (v1)**: events.jsonl + unified patches + snapshotting + bookmarks + CLI (`history/diff/rewind/snapshot/replay`).
2. **Phase 2**: semantic enrichment (AST/LSP) for Python/YAML/JSON; side-by-side viewer.
3. **Phase 3**: retention/GC; optional Keystroke OT for hot files; VCDIFF for binaries.

---

## 10. Testing & Acceptance

- **Reconstructability**: Any file state at any event/bookmark matches recorded hash.
- **Determinism**: Replay of a recorded run with `-no-network` reproduces metrics/artifacts byte-for-byte or emits a diff and fails.
- **Snapshot cadence**: Synthetic load confirms restore < **2s** for typical projects.
- **Security**: Redaction rules verified (no secrets in artifacts at rest).

---

## 11. Observability & Metrics

- `events_written_total`, `snapshot_bytes_total`, `events_since_last_snapshot`, `replay_success_rate`, `replay_duration_ms`, `restore_duration_ms`, `gc_bytes_freed_total`.
- Logs include event ids, bookmarks, run ids, tool versions, seeds.

---

## 12. Risks & Mitigations

- **Non-deterministic tools/LLMs** → enforce record/replay; flag live calls in replay mode.
- **AST failures** → fall back to path/line ranges; emit warning; do not block event logging.
- **Large binary changes** → store as artifacts; skip textual diff; consider VCDIFF in Phase 3.

---

## 13. Open questions

- Exact default values per project size? (EVENTS_PER_SNAPSHOT 50/80/100?)
- Per-language semantic adapters prioritized beyond Python/YAML/JSON?
- UI affordances for merging branches produced by rewind?

---

## 14. References

- Internal: System Spec (§Provenance), PRD (§Diff/Checkpoints), DevEx Flows (§Changelog/Bookmarks)
- External inspiration: OT-based editors, snapshot+patch time travel, deterministic record/replay patterns.