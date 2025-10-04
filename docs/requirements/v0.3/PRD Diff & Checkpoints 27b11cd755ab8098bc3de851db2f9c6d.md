# PRD: Diff & Checkpoints

Created by: Brock Butler
Created time: September 27, 2025 7:57 PM
Category: PRD
Last edited by: Brock Butler
Last updated time: September 27, 2025 10:22 PM
Parent item: v1 White Paper: Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization (https://www.notion.so/v1-White-Paper-Code-Diff-Storage-Rewinds-Replays-Bookmarks-and-Visualization-27b11cd755ab809ca950e00144cb5d7a?pvs=21)

## PRD —  Diff, Checkpoints, Merge & Replay

**Doc ID**: PRD-DIFF-CKPT-v1.1

**Owner**: Product (DevEx)

**Status**: Draft → Review → Accepted

**Last Updated**: 2025-09-27

**Related**: ADR‑007, System Spec (§Provenance), Onboarding/DevEx (§Changelog/Bookmarks), *bench‑validate* pack

---

### B1. Problem & Goals

Agentic workflows create high‑velocity, multi‑file changes that must be safe, explainable, and reversible. We need first‑class **diffs**, **bookmarks/checkpoints**, **deterministic replay**, and a practical **merge UX** (including batch operations and binary artifacts) to move fast without breaking trust.

**Goals (measurable)**

- p50 **restore to bookmark** < **2s** on a 5k‑file workspace; p95 < **5s**.
- **Deterministic replay success** ≥ **99%** of recorded runs.
- **AST‑aware diff success** ≥ **95%** on supported langs (Py/YAML) with p95 handler ≤ **100ms/file**.
- **Merge review time** for 10‑file agent refactor ≤ **5 min** p95 using batch operations.

---

### B2. Scope / Non‑Goals

**In scope:** diff visualization (side‑by‑side/unified), bookmarks & rewind, snapshots, deterministic replay (record/replay), merge UX (text 3‑way MVP + gated semantic YAML/JSON), batch merge, binary conflicts, rollups, VCS sync (optional), results overlay.

**Non‑goals (v1):** keystroke‑level CRDT, IDE‑native panels (we ship CLI/TUI + simple web preview), AST merge for all langs (flagged later).

---

### B3. Personas

- **Benchmark Author** – edits tasks/rubrics; needs safe time‑travel.
- **Agent Operator** – runs CrewAI‑style agents; accepts/rewinds proposals.
- **Reviewer** – merges branches; demands auditability and speed.

---

### B4. User Stories

- As an Author, I can view a diff with rationale and **accept** or **reject**.
- As an Operator, I can **bookmark** milestones and **rewind** to any prior point; forward edits create a **branch**.
- As a Reviewer, I can **merge** two branches, use **batch** acceptance to resolve most conflicts fast, and provide rationale for the tricky ones.
- As a QA, I can **replay** any state **without network**, confirm hashes and metrics match, and export a bundle.

---

### B5. Functional Requirements (FRs)

**PRD‑DIFF‑001 (Diff Viewer)**

Side‑by‑side/unified, syntax‑aware; shows adds/removes; filter by file/author/branch/operation; displays `diff_mode` badge (unified/ast/schema/binary); expand/collapse per operation.

**PRD‑CKPT‑001 (Bookmarks & Rewind)**

Create/list/rename/move/share/lock bookmarks; rewind jumps to target; forward edits branch automatically; locked bookmarks protect reachable snapshots from GC and block unsafe FF merges.

**PRD‑SNAP‑001 (Snapshot Policy)**

Auto snapshots at semantic boundaries (merge, approval, branch switch), every **N events** or **T minutes** (defaults provided), and on explicit request. Manifest includes `event_offset`, `ledger_driver`.

**PRD‑REPLAY‑001 (Deterministic Replay + Preflight)**

Record tool/LLM I/O as artifacts; replay denies network; **preflight** required before accepting agent edits (temp restore + hash verify + optional smoke tests). Fail fast on gaps.

**PRD‑MERGE‑001 (Text 3‑Way MVP + Semantic Flag)**

Compute base=LCA; textual 3‑way default. Semantic YAML/JSON merge behind `merge.semantic=true`; code falls back to text.

**PRD‑MERGE‑BATCH‑001 (Batch Acceptance)**

Batch accept/reject per **file**, **semantic block** (if available), or **operation**; deterministic application; **file‑level rationale required** when any conflicts resolved; optional hunk‑level rationale. CLI flags/globs supported.

**PRD‑MERGE‑BLOB‑001 (Binary Conflicts)**

Binary conflicts require explicit choice (ours/theirs/supplied). Show type/size/hashes/bytes changed; record human‑readable summary; allow OS preview where possible.

**PRD‑MERGE‑DRYRUN‑001 (Dry‑Run Merge)**

- `-dry-run` computes merge and runs smoke tests in a temp workspace with **no ledger writes**. Hashes must match final persisted merge when promoted.

**PRD‑MERGE‑UNDO‑001 (Undo Merge)**

`bench merge undo <merge_event_id>` restores **pre‑merge snapshot** onto a new branch (`--to ours|theirs`). Snapshots record `merged_from[]` and `pre_merge_snapshots[]`. Original branches untouched.

**PRD‑ROLLUP‑001 (Event Rollups)**

Non‑destructive rollups when `operation_id` exceeds threshold or on idle; emit composed patch + `rollup_index` artifact; auto‑snapshot after; grouped history default.

**PRD‑BLOB‑001 (Binary Handling General)**

Store whole new blob; set `diff_mode: binary`; require `artifact_impacts[].summary` with hashes and bytes changed.

**PRD‑VCS‑001 (VCS Sync Optional)**

Commit per `operation_id`; tags for bookmarks; repo manifest for integrity; post‑sync replay hash‑match required.

**PRD‑RESULTS‑001 (Results Overlay)**

`ResultEvent` anchors (eval/test/benchmark) shown on timeline; filter by result type; open artifact.

**PRD‑VALIDATE‑001 (Validation Gates)**

`bench‑validate` enforces schemas, preflight on agent edits, binary summaries, rollup equivalence, merge rationale and manifest rules.

---

### B6. Non‑Functional Requirements & SLOs

- p50/p95 **restore_duration_ms**: 2s / 5s (5k files).
- p95 **diff_render_latency_ms**: 150ms per file (cache warm).
- p95 **merge_apply_ms** (10 files): 1000ms text 3‑way; 1500ms with batch ops.
- **Storage**: rollups reduce visible events ≥ 90% on oversized operations.
- **Determinism**: replay/network policy = deny by default; synthetic traces flagged.

---

### B7. CLI/API Surface

```
bench history [--file <p>] [--author <id>] [--branch <b>] [--operation <op>] \
              [--group-by operation|snapshot|author] [--expand]
bench diff <A> <B> [--file <p>] [--side-by-side] [--format unified|ast|schema|binary]
bench bookmark add|list|rm|rename|move|share|lock|unlock <args>
bench snapshot save <name>
bench rewind <bookmark|event> [--branch <name>]
bench replay <A>..<B> [--dry-run] [--no-network]
bench merge <A> <B> [--policy text|semantic] [--auto ours|theirs] [--files <glob>] [--dry-run] [--resume]
bench merge undo <merge_event_id> [--to ours|theirs] [--branch <name>]
bench rollup propose <op-id> | apply <op-id> | revert <rollup_event_id>
bench results list [--between A..B] | show <event_id>
bench blob show <path> | open <path>
bench vcs sync | commit --operation <op-id> | tag <bookmark>
bench ledger convert --to protobuf | index rebuild | verify
bench gc

```

---

### B8. Acceptance Criteria (by FR)

- **DIFF‑001:** Diffs render correctly on golden corpus; `diff_mode` badge shown; AST diffs fallback to unified on parser failure and are labeled.
- **CKPT‑001:** Rewind to any bookmark reproduces file hashes; locked bookmarks block merges without `-force`.
- **SNAP‑001:** Snapshot cadence honored; each manifest contains `event_offset` + `ledger_driver`.
- **REPLAY‑001:** Replays fail on any live network; **preflight.ok=true** required for accepted agent edits; smoke tests run when configured.
- **MERGE‑001:** 3‑way results match Git for identical inputs; semantic flag only affects YAML/JSON; fallback path tested.
- **MERGE‑BATCH‑001:** Batch applies deterministically; file‑level rationale captured; unresolved hunks stop with pointer.
- **MERGE‑BLOB‑001:** Binary changes cannot complete without a recorded decision and `summary`.
- **MERGE‑DRYRUN‑001:** No ledger writes; promoting the plan yields identical hashes.
- **MERGE‑UNDO‑001:** Unmerge branch reproduces exact pre‑merge tree; original merge and branches intact.
- **ROLLUP‑001:** State from (snapshot+rollup) == (snapshot+raw events) on fixtures.
- **BLOB‑001:** `artifact_impacts` present with hashes and bytes changed.
- **VCS‑001:** Post‑sync integrity check passes via replay.
- **RESULTS‑001:** Result markers visible and linked to artifacts.
- **VALIDATE‑001:** Validator flags missing `diff_mode`, missing preflight for agent edits, missing binary summaries, missing post‑merge manifest fields.

---

### B9. Fixtures (for dev & CI)

**Fixture A — Synthetic 10‑File Agent Refactor (batch path)**

- **Setup:** create branch `agent-refactor` diverging from `main` with edits across 10 files:
    - 6 files: whitespace/formatting only (non‑semantic).
    - 3 files: trivial, identical hunks; auto‑resolvable.
    - 1 file: true conflict (2 hunks) requiring human decision.
- **Expectations:**
    - `bench merge main agent-refactor --auto ours --files '**/*.md'` batches MD files, zero conflicts.
    - TUI hotkeys `SHIFT+A` accept all hunks in selected files.
    - For the conflicting file, reviewer provides **file‑level rationale** and optional **hunk‑level** note.
    - Post‑merge **snapshot** and `post-merge-<id>` bookmark created; `merged_from[]` and `pre_merge_snapshots[]` recorded.
    - **Metrics:** `merge_batch_ops_total >= 4`; total resolution time < 5 min on reference machine.

**Fixture B — Binary Conflict (image)**

- **Setup:** both branches modify `docs/diagram.png` (different images). No text conflicts elsewhere.
- **Expectations:**
    - `bench blob show docs/diagram.png` displays type `image/png`, size delta, `sha256` before/after, bytes changed.
    - TUI requires explicit choice: **ours/theirs/supplied**; a **summary** is mandatory.
    - Event records `binary_choices[]` and `artifact_impacts[]`; if **supplied**, verifies new blob exists.
    - Validator passes only when summary present and hashes recorded.

---

### B10. Telemetry / KPIs

- `restore_duration_ms` p50/p95; `replay_success_rate`; `diff_render_latency_ms`; `merge_total`; `merge_conflicts_total`; `merge_human_intervention_ratio`; `merge_time_per_file_ms`; `merge_batch_ops_total`; `merge_undo_total`; `rollup_applied_total`; `blob_changes_total`; `synthetic_traces_used_total`.

---

### B11. Release Plan & Flags

- **MVP (v1.0):** unified diffs; text 3‑way; batch per file/op; binary manual; preflight; rollups; basic VCS sync; results overlay.
- **v1.1:** semantic blocks (Py/YAML); YAML/JSON semantic merge flag; agent assist suggestions recorded; `merge dry‑run`/`merge undo` GA.
- **Flags:** `merge.semantic`, `merge.assist`, `synthetic.traces`, `vcs.sync`.

---

### B12. Risks & Mitigations

- **Batch hides mistakes:** always preview; require rationale; post‑merge preflight/tests.
- **Semantic instability:** keep behind flag; fallback to text; telemetry on handler failure.
- **Binary UX thin:** enforce summaries; allow OS preview; add rich handlers in v1.2.
- **Large ledgers:** rollups, indexed logs, snapshot cadence advisor.

---

### B13. Traceability

- ADR‑007 D1..D7 → FRs above; System Spec (§Provenance) → schemas (`diff_mode`, `operation_id`, `action_scope`, `preflight`, `artifact_impacts`, `event_offset`, `ledger_driver`); Onboarding (§Changelog/Bookmarks) → flow gates.