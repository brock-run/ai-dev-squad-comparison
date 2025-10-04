# v1 White Paper: Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization

Created by: Brock Butler
Created time: September 27, 2025 5:58 PM
Category: White Paper
Last edited by: Brock Butler
Last updated time: September 28, 2025 1:58 PM
Parent item: v1 (https://www.notion.so/v1-27a11cd755ab80efa99cfad4cd59780d?pvs=21)
Sub-item: Research: Realtime Code Playback and Rewind Tools: A Comparison (https://www.notion.so/Research-Realtime-Code-Playback-and-Rewind-Tools-A-Comparison-27b11cd755ab80a8b66dc597ce95408f?pvs=21), Example: CrewAI CLI session (https://www.notion.so/Example-CrewAI-CLI-session-27b11cd755ab805b8626eae89a7d9296?pvs=21), Research: VCS, AI, Diff Capture Workflows (https://www.notion.so/Research-VCS-AI-Diff-Capture-Workflows-27b11cd755ab8076b424edc627899e86?pvs=21), System Spec: Provenance (https://www.notion.so/System-Spec-Provenance-27b11cd755ab8034a259daecf0c5d285?pvs=21), PRD: Diff & Checkpoints (https://www.notion.so/PRD-Diff-Checkpoints-27b11cd755ab8098bc3de851db2f9c6d?pvs=21), UX Flows: Changelog/Bookmarks (https://www.notion.so/UX-Flows-Changelog-Bookmarks-27c11cd755ab8011a7fcee9fc3dbe9bf?pvs=21), Design Spec: CI Integration (https://www.notion.so/Design-Spec-CI-Integration-27c11cd755ab80bf9906f79236b2e99c?pvs=21), System Spec: bench validate (https://www.notion.so/System-Spec-bench-validate-27c11cd755ab80cca7cbe8d9b56c42fb?pvs=21), UX Flows: Merge Conflict Resolution (https://www.notion.so/UX-Flows-Merge-Conflict-Resolution-27c11cd755ab80c7854be0f7e392f70f?pvs=21), ADR-007: Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization (https://www.notion.so/ADR-007-Code-Diff-Storage-Rewinds-Replays-Bookmarks-and-Visualization-27c11cd755ab8024bdf5d0b129b314cd?pvs=21), Risk Mitigation: Code Diff (https://www.notion.so/Risk-Mitigation-Code-Diff-27c11cd755ab806a894ece1e1e660b11?pvs=21)

# Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization

**Primary Spec / White Paper**

**Version**: v2 (Draft for Review)

**Date**: 2025‑09‑27

**Owners**: Agent Platform (DevEx) · Benchmark Tooling · AI Systems

**Related**: ADR‑007; PRD — Diff & Checkpoints; System Spec — Provenance; Onboarding/DevEx Flows — Changelog/Bookmarks; *bench‑validate* Starter Pack

---

## 0) Release Notes — Why this matters (outcomes)

**Today we ship time‑travel for agentic work.** Teams can now:

- **See exactly what changed and why**: Every accepted change—by human or agent—has a diff, rationale, and provenance.
- **Rewind and branch safely**: Jump to any bookmark or snapshot; continue on a new branch without risk.
- **Deterministically replay**: Reconstruct runs offline, with external calls stubbed from recorded traces for exact reproduction.
- **Compare, review, export**: Side‑by‑side diffs between any two points; export an auditable bundle for PRs, audits, or incident analysis.
- **Operate at human and semantic scales**: From a single line tweak to multi‑file agent refactors, we preserve both atomic fidelity and semantic intent for clear review and fast navigation.

**Outcomes**

- **Reliability**: Fewer “mystery diffs.” Any state can be reconstructed and explained.
- **Velocity**: Safer experimentation; quick branch/merge of agent proposals; faster incident rollback.
- **Governance**: Audit‑ready provenance and replayability reduces compliance and review burden.

---

## 1) Scope & Goals

### In scope

- Change logging, snapshots, deterministic replay, bookmarks, visualization.
- Concurrency/branching model for multi‑agent edits.
- Binary/non‑code artifact handling.
- Retention/GC policy.

### Out of scope (v2 may consider)

- Realtime CRDT sync across editors; large‑scale multi‑repo merges.
- Integrated code review UI beyond our diff/timeline viewer (we link out to GitHub/PRs as needed).

---

## 2) Core Concepts

- **Atomic Event**: Minimal accepted change (line‑level OT or unified patch) with rationale and provenance.
- **Semantic Operation**: A higher‑level action (often agent‑initiated) that may span many files/events. **Groups events via `operation_id` and `action_scope`.**
- **Snapshot**: Compressed workspace state + manifest (env, seeds, versions, hashes).
- **Bookmark**: Named pointer to an event or snapshot; used for rewind/diff/replay.
- **Branch**: Named lineage from an event; merges recorded as events.

---

## 3) Improvements Addressed in v2

### 3.1 Diff granularity for semantic agent changes

- New metadata: `operation_id` (UUID) and `action_scope: line|block|file|project`.
- Proposal/accept flow: agent proposes a **Semantic Operation**; on acceptance we emit N atomic events with the same `operation_id`. Reviewers can expand/collapse by operation.
- For code, we also attach `semantic_block` info per event (function/class/json‑path) for jump‑to‑context UX.

### 3.2 OT/patch ordering & concurrent flows

- Ledger is append‑only, but multiple operations can branch from the same parent.
- Event fields: `branch`, `parent_event_id`. Rewind creates a new `branch` unless fast‑forward.
- Merges are explicit `merge` events: `{left, right, base, policy, conflicts[]}` with a synthetic merge patch and mandatory snapshot.

### 3.3 Binary and non‑code artifacts

- Introduce `BlobArtifact` types with content hashes and size metadata.
- Diffs for binaries are **handler‑based** (optional): VCDIFF for generic binaries; perceptual hash for images; otherwise store **hash delta** and `bytes_changed`.
- Diff events may include `artifact_impacts[]` with human‑readable explanations (e.g., "Replaced diagram.png; bytes_changed=1204").

### 3.4 Retention/GC/scale

- Policy config (per project): targets restore SLO and storage budget.
- Snapshot cadence auto‑tuning based on measured `t_snapshot_ms` and `t_patch_ms`.
- Bookmark‑protected snapshots are never GC’d. Older segments can be squashed into roll‑up patches.

### 3.5 Deterministic replay for LLM/APIs

- **Record mode required** for onboarding/critical tasks; records tool/LLM request+response as `Artifact(type: trace)`.
- **Replay mode** denies network calls; any unrecorded external call causes a hard error with a pointed diff of expected vs observed.

### 3.7 Preflight acceptance (before any proposal is accepted)

1. Apply the proposed patch in a **temp workspace** (no network). 2) Rebuild via nearest snapshot + events + proposal. 3) Hash‑verify resulting files; optionally run smoke tests. 4) On mismatch → **reject** with a divergence report artifact; record `preflight.ok=false`.

### 3.6 Visual timeline

- Filters by **author kind**: `human|agent|llm` and by `operation_id`, `branch`, `file`, `semantic_block`.
- Overlays: approvals, merges, test/eval passes, DSPy optimizations, snapshots and bookmarks.
- Jump controls: expand/collapse operations; "play head" scrubber; quick compare between bookmarks.

### 3.A Model‑aware / AST diffs (normative, pluggable handlers)

- **diff_mode** added to events: `unified|ast|schema|binary` (default `unified`).
- **Handler API** (pure, deterministic; must fallback on error):
    - **Input**: `(path, before_text, after_text, unified_patch)`
    - **Output**: `{diff_mode, semantic_blocks[], summary, fallback_reason?}`
- **Priority languages** (Phase 2): Python (libcst), TS/JS (tsserver), YAML/JSON (schema/path). Go to follow.
- **Telemetry / SLOs**: ≥95% handler success on corpus; p95 ≤100ms/file after warm index.

**Schema delta** (see §5.1): `ChangeEvent.diff_mode` required enum; `semantic_block` stays per‑event.

---

## 4) Architecture

### 4.1 Storage layout

```
.user/ledger/
  events.jsonl           # append-only ledger (ordered)
  bookmarks.json         # name -> (event|snapshot id)
  snapshots/
    snap-*.tar.zst       # each contains manifest.json
results/
  diffs/                 # unified patches
  artifacts/             # traces, logs, blobs

```

### 4.2 Entity overview

- **ChangeEvent**: atomic diff + provenance. Includes `operation_id`, `action_scope`, `diff_mode`, `semantic_block`.
- **SemanticOperation** (virtual): group of events sharing `operation_id`.
- **Snapshot**: tarball + `manifest.json` (env/seeds/versions/hashes, `base_event_id`, `event_offset`, `ledger_driver`).
- **MergeEvent**: special ChangeEvent with `{left,right,base,policy}` and an aggregate patch.
- **RollupEvent**: synthetic, compact patch summarizing an oversized operation; non‑destructive index of raw events.
- **ResultEvent**: eval/test/benchmark outputs anchored to specific events.

### 4.3 Deterministic replay engine

1. Restore nearest snapshot ≤ target. 2) Apply events forward; verify file hashes. 3) Stub external calls from traces. 4) Validate metrics/artifacts match. 5) If any external call lacks a recorded trace → **FAIL** (see §3.5 Preflight & Replay).

### 4.4 VCS Sync (optional)

- **Source of truth remains the ledger**; Git is a synchronization target.
- Mapping: default commit granularity = **one commit per `operation_id`**; bookmarks → Git tags; branches → `bench/<name>`.
- Commit messages embed ledger refs (first/last event ids, operation_id, bookmark names); a `.bench/manifest.json` is written with current `event_id`, `snapshot_id`.
- CLI: `bench vcs sync`, `bench vcs tag <bookmark>`, `bench vcs commit --operation <op-id>`.
- Integrity: post-sync `bench replay` against the synced commit must hash‑match workspace.
1. Restore nearest snapshot ≤ target. 2) Apply events forward; verify file hashes. 3) Stub external calls from traces. 4) Validate metrics/artifacts match.

---

## 5) Data Contracts (normative excerpts)

### 5.1 `ChangeEvent` (JSON Schema excerpt)

```json
{
  "required": ["id","ts","author","action_type","files","diff_path","operation_id","action_scope","rationale"],
  "properties": {
    "operation_id": {"type": "string"},
    "action_scope": {"enum": ["line","block","file","project"]},
    "diff_mode": {"enum": ["unified","ast","schema","binary"]},
    "semantic_block": {"type": "object", "properties": {"kind": {"type":"string"}, "id": {"type":"string"}}},
    "preflight": {"type":"object","properties": {"ok": {"type":"boolean"}, "report_artifact": {"type":"string"}}}
  }
}

```

### 5.2 `Snapshot.manifest.json` (excerpt)

```json
{
  "id":"snap-0007","base_event_id":"evt-0123",
  "env": {"python":"3.11.8","llm":"anthropic/claude-3.7"},
  "seeds":{"global":1337},
  "tools":{"crew":"0.30.1"},
  "hashes": {"rubrics/security.yaml":"sha256:..."},
  "event_offset": 123456,
  "ledger_driver": "jsonl"
}

```

### 5.3 Merge event

```json
{"id":"evt-0456","action_type":"merge","left":"bmk-A","right":"bmk-B","base":"evt-0333","policy":"text|semantic","diff_path":"results/diffs/diff-evt-0456.patch","snapshot_ref":"snap-0021","rationale":"Combine branches"}

```

### 5.4 Blob artifact impact (attached to event)

```json
{"artifact_impacts":[{"path":"docs/diagram.png","kind":"image","bytes_changed":1204,"hash_before":"sha256:..a","hash_after":"sha256:..b","summary":"Replaced architecture diagram"}]}

```

### 5.5 Rollup event (synthetic)

```json
{
  "id":"evt-roll-op9",
  "action_type":"rollup",
  "operation_id":"op-9b2d",
  "diff_path":"results/diffs/diff-roll-op9.patch",
  "rollup": {"of_operation_id":"op-9b2d","event_count": 432, "rollup_index_artifact":"results/artifacts/rollup-op9.json"},
  "snapshot_ref":"snap-0012"
}

```

### 5.6 Result event (eval/test/benchmark)

```json
{
  "id":"evt-r123","action_type":"eval_run","run_id":"run-42",
  "inputs":{"benchmark":"security","seed":1337},
  "outputs":{"pass@1":0.76,"sql_parametrization":0.81},
  "artifacts":["results/artifacts/eval-run-42.json"],
  "anchors":["evt-0004"]
}

```

---

## 6) Concurrency & Branching Model

- **Append‑only ledger** ensures linear history per branch, with explicit forks on rewind.
- **Branch semantics**: `rewind` → new branch unless FF possible. **Merge** uses three‑way at LCA; semantic policy for YAML/JSON behind a feature flag; code falls back to text.
- **Locking**: admission control serializes accepted changes per branch; concurrent proposals queue; merges require review.

### 6.1 Conflict review UX (MVP + flagged semantic)

- MVP = textual three‑way with interactive hunk selection (`ours|theirs|edit`). Require **file‑level rationale**; emit `merge_resolution` artifact; auto‑snapshot on success.
- `merge.semantic=true`: YAML/JSON path‑level merges with conflict list by JSON Pointer; AST merges attempted only where handlers exist; otherwise fallback to text.

---

## 7) Retention & GC Policy

- Target **restore SLO** and **storage budget**; compute `N_events_per_snapshot` from observed timings.
- Default tiers (small/medium/large/XL) with suggested cadence and keep rules.
- Never GC snapshots reachable from bookmarks. Optional **roll‑up** squashing for old, unbookmarked segments.

### 7.1 Rollups & grouped history

- Trigger when an `operation_id` exceeds `N_events_per_op` (default 200) or on idle ≥10 min.
- Emit a **RollupEvent** with composed patch and a `rollup_index` artifact (list of original event ids, sizes, hashes). **Non‑destructive**.
- Auto‑snapshot after rollup; default **history view groups by operation** with expand/collapse.

---

## 8) Visualization & UX

### 8.1 Timeline

- Filters: `author.kind`, `operation_id`, `branch`, `file`, `semantic_block`, `action_type`.
- Overlays: approvals, merges, eval/test results, DSPy optimizer runs, snapshots/bookmarks.
- Controls: play/pause, step, jump to bookmark, expand/collapse operation.

### 8.2 Diff viewer

- Side‑by‑side and unified; syntax‑aware; inline rationale and provenance badges.
- Binary artifacts show hash deltas and preview if handler exists.

### 8.3 CLI essentials

```
bench history [--file <p>] [--author <id>] [--branch <b>] [--operation <op>] [--group-by operation|snapshot|author] [--expand]
bench diff <A> <B> [--file <p>] [--side-by-side] [--format unified|ast|schema|binary]
bench rewind <bookmark|event> [--branch <name>]
bench merge <A> <B> [--policy text|semantic] [--no-ff] [--resume]
bench snapshot save <name>
bench replay <A>..<B> [--no-network] [--dry-run]
bench rollup propose <operation_id> | apply <operation_id> | revert <rollup_event_id>
bench bookmark add|rename|move|share|lock|unlock <args>
bench results list [--between A..B] | show <event_id>
bench blob diff <path> [--open]
bench vcs sync | commit --operation <op-id> | tag <bookmark>
bench ledger convert --to protobuf | index rebuild | verify
bench gc

```

---

## 9) Security, Privacy, and Compliance

- Redaction filters for traces; optional encryption‑at‑rest for `artifacts/`.
- Replay mode **denies** outbound network by default; any attempt fails the run.
- Audit bundle export contains events, patches, snapshots manifests, traces, and a replay script.

---

## 10) Observability & SLIs

- Metrics: `events_written_total`, `events_since_last_snapshot`, `restore_duration_ms`, `replay_success_rate`, `diff_render_latency_ms`, `gc_bytes_freed_total`.
- Logs: all ids (event/operation/branch/bookmark), seeds, tool versions.

---

## 11) Testing & Validation

- **bench‑validate** schema checks for `ChangeEvent` and `Snapshot`.
- Golden replays over fixtures (byte‑for‑byte files + metrics).
- Adapter tests: semantic block resolution per language; YAML/JSON path mapping.
- Merge tests: three‑way + semantic resolution with known conflict sets.

---

## 12) Roadmap (Adapters & Merges)

- **M0**: YAML/JSON (path selectors), Markdown (headings), Python (libcst). Baseline for others = line ranges.
- **M1**: TS/JS (tsserver), Go (go/parser + go/types). Semantic merge for YAML/JSON.
- **M2**: Java/Kotlin, Rust with Tree‑sitter; optional AST diffs for large refactors.

---

## 13) Governance & Change Control

- RFC2119 language in System Spec — Provenance.
- Schema versions with migrations; deprecation window per minor release.
- Feature flags for semantic merges and binary diff handlers.

---

## 14) Cross‑Doc Traceability

| Requirement | ADR‑007 | PRD (Diff/Checkpoints) | System Spec (Provenance) | Onboarding/DevEx | Tests |
| --- | --- | --- | --- | --- | --- |
| Record accepted changes | ✓ | ✓ | SYS‑PROV‑001 | ODX‑CLG‑001 | CT‑PROV‑01 |
| Snapshot cadence | ✓ | PRD‑SNAP‑001 | SYS‑PROV‑002 | — | CT‑PROV‑05 |
| Deterministic replay | ✓ | PRD‑REPLAY‑001 | SYS‑PROV‑003/004 | C6 | CT‑PROV‑02 |
| Semantic ops/action_scope | ✓ | PRD‑DIFF‑001 | SYS‑PROV‑001b | ODX UI | CT‑PROV‑07 |
| Concurrency/branching/merge | ✓ | PRD‑MERGE‑001 | SYS‑PROV‑005 | ODX‑FLOW‑MERGE | CT‑MERGE‑* |
| Binary artifacts | ✓ | PRD‑BLOB‑001 | SYS‑PROV‑006 | ODX‑REVIEW | CT‑BLOB‑* |

---

## 15) Appendices

### A. Example Event (semantic operation)

```json
{
  "id":"evt-00ab",
  "ts":"2025-09-27T15:03:12Z",
  "author":{"name":"refactor-agent","version":"1.3.0","kind":"agent"},
  "operation_id":"op-9b2d",
  "action_scope":"project",
  "action_type":"edit_replace",
  "branch":"security-alt",
  "files":["tasks/sql_injection.yaml","rubrics/security.yaml","README.md"],
  "diff_path":"results/diffs/diff-evt-00ab.patch",
  "semantic_block":{"kind":"yaml_path","id":"/criteria/sql_parametrization"},
  "rationale":"Agent refactor + README and tests updated to reflect new rubric",
  "artifacts":["results/artifacts/trace-evt-00ab.json"],
  "snapshot_ref":"snap-0010"
}

```

### B. Snapshot manifest

```json
{
  "id":"snap-0010","ts":"2025-09-27T15:05:00Z","base_event_id":"evt-00aa",
  "tar_uri":".user/ledger/snapshots/snap-0010.tar.zst",
  "env":{"python":"3.11.8","os":"macOS-14","llm":"anthropic/claude-3.7"},
  "seeds":{"global":1337},
  "tools":{"crew":"0.30.1"},
  "hashes":{"tasks/sql_injection.yaml":"sha256:..."}
}

```

### C. Merge event

```json
{"id":"evt-00b1","action_type":"merge","left":"candidate-A","right":"candidate-B","base":"evt-0090","policy":"semantic","diff_path":"results/diffs/diff-evt-00b1.patch","snapshot_ref":"snap-0011","rationale":"Combine agent A’s task tightening with agent B’s rubric weights"}

```

---

## 16) Open Questions

- Default snapshot cadence by tier vs. auto‑tuning thresholds—what should we ship as defaults?
- How far to push AST/IR diffs in v2 (Python only vs. TS/Go as well)?
- UI design for conflict resolution on semantic merges (what’s the MVP?).

---

## 17) Next Steps

- Ratify schemas and CLI surface.
- Implement `operation_id` & `action_scope` in ledger writes.
- Ship `bench merge` (three‑way + semantic for YAML/JSON) with auto‑snapshot.
- Integrate *bench‑validate* into CI and publish golden replay fixtures.

---

## v1.1 Addenda — Patches Applied from Whitepaper

This addendum updates the templates with new fields, flows, and gates. Fold these into the main sections during drafting.

### H1. System Spec — Provenance (insertions)

- **New MUSTs**: `operation_id`, `action_scope`, and `diff_mode` on every `ChangeEvent`; preflight required before accepting agent proposals; rollups non‑destructive with `rollup_index` artifact; binary events require `artifact_impacts[].summary`.
- **Snapshot manifest** adds `event_offset` and `ledger_driver`.
- **Merge** recorded with `{left,right,base,policy}` and conflict rationale; semantic merge gated.
- **Synthetic traces** only via explicit flag; runs labeled **NON‑REPRODUCIBLE**.

**Schema deltas (snippets)**

- *ChangeEvent.schema.json* (+):

```json
{
  "properties": {
    "operation_id": {"type": "string"},
    "action_scope": {"enum": ["line","block","file","project"]},
    "diff_mode": {"enum": ["unified","ast","schema","binary"]},
    "preflight": {"type": "object", "properties": {"ok": {"type": "boolean"}, "report_artifact": {"type": "string"}}},
    "artifact_impacts": {"type": "array", "items": {"type": "object", "properties": {"path": {"type": "string"}, "summary": {"type": "string"}}, "required": ["path","summary"]}}
  }
}

```

- *Snapshot.schema.json* (+):

```json
{
  "required": ["event_offset","ledger_driver"],
  "properties": {"event_offset": {"type": "integer"}, "ledger_driver": {"enum": ["jsonl","protobuf"]}}
}

```

### H2. PRD — Diff & Checkpoints (insertions)

- **FRs**: PRD‑MERGE‑001 (text 3‑way MVP + semantic YAML/JSON behind flag), PRD‑ROLLUP‑001 (grouped history, non‑destructive rollups), PRD‑BLOB‑001 (binary summary), PRD‑VCS‑001 (Git sync), PRD‑REPLAY‑001 (preflight required).
- **KPIs**: `ast_diff_success_rate`, `restore_duration_ms`, `rollup_applied_total`.
- **ACs**: rollup equivalence vs raw events; merge reproducibility; Git sync integrity.

### H3. Onboarding/DevEx (insertions)

- **Flow**: `… → preflight → review_diff → accept → record_event → (rollup?) → (snapshot?)`.
- **CLI**: extend with `bookmark rename|move|share|lock|unlock`, `rollup propose|apply|revert`, `merge --policy text|semantic --resume`, `results list|show`, `vcs sync|commit|tag`.
- **Policies**: locked bookmarks protect snapshots; divergence surfaces immediately with a report artifact; semantic merge gated.

### H4. New Event Types (reference)

- `merge`, `rollup`, `eval_run` (`ResultEvent`).

### H5. Traceability matrix (delta)

Add rows for *semantic ops & diff_mode*, *rollups*, *VCS sync*, and *preflight & determinism* linking to new FRs and MUSTs.

## Other Additions in v1.1

### F1. Semantic / AST-aware diffs

**Why include:** Big lift in explainability and safer merges for agent refactors. It should be a **pluggable diff handler**, not the only path.

**Spec adds**

- **ChangeEvent**: add `diff_mode: unified|ast|schema|binary` (default `unified`).
- **Adapter contract** (new “Diff Handler” section):
    - Input: `(path, before, after, unified_patch)`
    - Output: `{diff_mode, semantic_blocks[], summary, fallback_reason?}`
    - Must be pure, deterministic; MUST fall back to unified on parser errors.
- **Priority languages (Phase 2)**: Python (libcst), TS/JS (tsserver), YAML/JSON (schema/path), Go (go/parser).
- **Acceptance metrics**: ≥95% handler success rate on corpus; p95 handler latency ≤ 100ms/file (warm cache).

**Docs to update**

- Whitepaper §3.A “Model-aware diffs” → make **normative** with handler API + `diff_mode`.
- System Spec — §Provenance → add `diff_mode` to schema.
- PRD → add KPI “AST diff success rate” and latency SLO.

**Risks & mitigations**

- Parser fragility → strict fallback + telemetry.
- Latency → background indexing + per-file caching.

### F2. Integration with native VCS (Git)

**Why include:** Teams will want PRs that mirror the ledger. Keep **JSONL ledger as source of truth**; Git is a synchronization target.

**Spec adds**

- New module: **VCS Sync** (optional).
- **Mapping rules**:
    - Commit granularity: default = one **commit per `operation_id`** (semantic op). Option: one per snapshot.
    - Commit message template includes: `operation_id`, first/last event ids, bookmark names, run id, hashes.
    - Bookmarks → lightweight Git **tags**; branches map 1:1 by name with prefix `bench/`.
    - Drop a `.bench/manifest.json` at repo root containing current event id, snapshot, branch.
- **Commands**:
    - `bench vcs sync` (idempotent, dry-run preview).
    - `bench vcs tag <bookmark>`; `bench vcs commit --operation <op-id>`.
- **Integrity check**: after sync, `bench replay …` against the synced commit must hash-match workspace.

**Docs to update**

- Whitepaper §4 Storage & §8 CLI → add VCS Sync subsection.
- ADR-007 → “Git is integration, not source of truth.”

**Risks**

- Divergence between Git and ledger → block sync if workspace dirty; always embed ledger refs in commit message + manifest and verify on next sync.

### F3. Preemptive replay validation (before accept)

**Why include:** Catches “looks fine but reapply diverges” issues (common with generated content/tools).

**Spec adds**

- **Acceptance gate** (normative): Before an agent proposal is accepted:
    1. Apply patch into a **temp workspace** (no network).
    2. Rebuild state from **nearest snapshot + events + the proposed patch**.
    3. Hash files; optionally run **fast checks** (lint/unit smoke).
    4. If mismatch → **reject** with a divergence diff.
- **Flags**: `-strict-apply` (default ON for onboarding/critical), `-smoke-tests` (runs configured quick tests).
- **Events**: log `preflight_ok: true|false`, and attach `divergence_report` artifact on failure.

**Docs to update**

- Whitepaper §3.5 Deterministic replay → add **Preflight** subsection.
- PRD Acceptance Criteria → add AC: “preflight must pass” for all accepted agent changes.
- bench-validate → add a test that synthetic divergence is blocked.

**Risks**

- Time cost → cache temp workspace; run only quick checks (configurable).

### F4. Time/space-optimized event log

**Why include:** Scale path. Don’t block v1; design the **storage driver** interface now.

**Spec adds**

- **Ledger storage driver** abstraction:
    - Drivers: `jsonl` (default), `protobuf+lz4`, (optional `sqlite`/`parquet` later).
    - Required APIs: `append(event)`, `scan(range|predicate)`, `seek(id|timestamp)`, `index(build|verify)`.
- **Indexing**: sidecar `.idx` with offsets by `event_id`, `timestamp`, `operation_id`, `branch`.
- **Snapshot index**: manifest contains the **event offset** so restore = O(1) seek + streaming apply.
- **CLI**: `bench ledger convert --to protobuf`, `bench ledger index rebuild`, `bench ledger verify`.

**Docs to update**

- Whitepaper §4.1 Storage layout → “storage drivers & indexes”.
- System Spec — schema unchanged; storage is an implementation detail with a normative API.

**Risks**

- Complexity → keep JSONL primary for now; introduce protobuf behind a feature flag until we have stable tooling.

### Where each lands (quick map)

| Item | Whitepaper | System Spec (Provenance) | PRD (Diff/Checkpoints) | Onboarding/DevEx | ADR-007 |
| --- | --- | --- | --- | --- | --- |
| AST-aware diffs | §3.A → normative, +handler API | Add `diff_mode`; handler contract | KPI: success rate & p95 | Flow note: show “AST diff” badge | Note as future-proofing |
| Git sync | §4 (VCS Sync) + CLI | Source-of-truth statement + manifest fields | Story: “Commit + Tag from bookmarks” | Flow: “Export to PR” | Explicit non-primary SoT |
| Preemptive replay | §3.5 (Preflight) | MUST gate before accept; event flags | AC: “preflight must pass” | Add to approval checklist | Called out in Decision & Risks |
| Ledger perf | §4 (Storage drivers & indexes) | API contract for drivers | Non-functional: p50/p95 restore | Ops runbook (index rebuild) | Mentioned as evolvability |

### Suggested schema tweaks (minimal)

**ChangeEvent (+)**

```json
{
  "diff_mode": { "enum": ["unified","ast","schema","binary"] },
  "operation_id": { "type": "string" },
  "action_scope": { "enum": ["line","block","file","project"] },
  "preflight": {
    "type":"object",
    "properties": {
      "ok": {"type":"boolean"},
      "report_artifact": {"type":"string"}
    }
  }
}

```

**Snapshot.manifest (+)**

```json
{
  "event_offset": { "type":"integer" },   // for O(1) seek in indexed logs
  "ledger_driver": { "enum":["jsonl","protobuf"] }
}

```

### MVP vs Phase

- **MVP (ships now):** keep unified diffs; add schema fields (`diff_mode`, `operation_id`, `action_scope`), implement **preflight**, and stub **VCS sync** (commit/tag). JSONL + sidecar index.
- **Phase 2:** AST diffs for Python/YAML/JSON, semantic YAML/JSON merges, basic Git PR export, protobuf driver behind flag.
- **Phase 3:** TS/Go adapters, conflict UI with semantic assists, full protobuf pipeline + faster snapshot seek.

If you want, I can patch the whitepaper and spec templates to add these exact sections and schema fields, and extend the `bench-validate` pack with:

- a `diff_mode` rule,
- preflight-required checks,
- and a storage-driver conformance test stub.

[ADR-007: Code Diffs, Snapshots, Bookmarks, and Deterministic Replay](v1%20White%20Paper%20Code%20Diff%20Storage,%20Rewinds,%20Replays%2027b11cd755ab809ca950e00144cb5d7a/ADR-007%20Code%20Diffs,%20Snapshots,%20Bookmarks,%20and%20Dete%2027b11cd755ab804c806df95c6f58b1a0.md)