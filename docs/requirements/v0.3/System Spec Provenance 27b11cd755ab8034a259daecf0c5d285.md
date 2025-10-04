# System Spec: Provenance

Created by: Brock Butler
Created time: September 27, 2025 7:54 PM
Category: System Spec
Last edited by: Brock Butler
Last updated time: September 27, 2025 10:33 PM
Parent item: v1 White Paper: Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization (https://www.notion.so/v1-White-Paper-Code-Diff-Storage-Rewinds-Replays-Bookmarks-and-Visualization-27b11cd755ab809ca950e00144cb5d7a?pvs=21)

# System Spec — Provenance (v1.1)

**Doc ID**: SYS-PROV-v1.1

**Owner**: Platform Eng (DevEx)

**Status**: Accepted

**Last Updated**: 2025-09-27

**Related**: ADR‑007, PRD‑DIFF‑CKPT‑v1.1, Onboarding/DevEx Flows, bench‑validate pack

---

### A1. Purpose & Scope

- **Purpose**: Define the *normative* provenance model for agentic changes (events, snapshots, bookmarks, replay/merge), including schemas, guarantees, and conformance tests.
- **In Scope**: Code/text artifacts; tool/LLM I/O traces; environment manifests; deterministic replay rules; merge and rollup provenance.
- **Out of Scope**: Org‑level git branching policy; keystroke‑level CRDT/OT sync (future adapter); IDE‑native UI.

---

### A2. Normative Language & Guarantees

Use RFC2119 terms (MUST/SHOULD/MAY).

- **SYS‑PROV‑001**: Every **accepted** change MUST emit a `ChangeEvent` with `diff_mode ∈ {unified, ast, schema, binary}`, `operation_id`, `action_scope`, and **rationale**.
- **SYS‑PROV‑002**: A **Snapshot** MUST be created at semantic boundaries and per cadence policy; the manifest MUST include `event_offset` and `ledger_driver`.
- **SYS‑PROV‑003**: **Replay(mode=deterministic)** MUST stub network/tool calls with recorded artifacts; any live call MUST fail the run. Synthetic traces are permitted only behind a flag and MUST label runs as **NON‑REPRODUCIBLE**.
- **SYS‑PROV‑004**: Hashes of reconstructed files MUST match the snapshot/event chain; otherwise the system MUST emit a `replay_divergence` error.
- **SYS‑PROV‑005**: **Agent edits** MUST pass **preflight** (temp restore + hash verify; optional smoke tests) and record `preflight.ok=true`.
- **SYS‑PROV‑006**: **Binary diffs** MUST include `artifact_impacts[].summary` with hashes and bytes changed.
- **SYS‑PROV‑007**: **Merge** MUST record left/right/base, policy, batch decisions, binary choices, and rationale; MUST create an automatic post‑merge snapshot and bookmark; **undo** MUST restore a recorded pre‑merge snapshot to a new branch.
- **SYS‑PROV‑008**: **Rollups** MUST be non‑destructive and pass rollup equivalence (state from snapshot+rollup == snapshot+raw events).
- **SYS‑PROV‑009**: **VCS sync** MAY be enabled; if enabled, post‑sync integrity MUST be verified by deterministic replay.
- **SYS‑PROV‑010**: Conformance MUST be enforceable via `bench‑validate` (schemas + semantic rules).

---

### A3. Data Model (Schemas)

Provide machine‑validated schemas (JSON Schema). Below are normative excerpts; full versions live under `schemas/`.

**A3.1 `ChangeEvent.schema.json`**

```json
{
  "$id": "schema/change-event.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": [
    "id","ts","author","action_type","files","diff_path",
    "operation_id","action_scope","rationale","diff_mode"
  ],
  "properties": {
    "id": {"type": "string","minLength":1},
    "ts": {"type": "string","format": "date-time"},
    "author": {"type": "object","required": ["name","kind"],
      "properties": {"name": {"type": "string"}, "version": {"type": "string"}, "kind": {"enum": ["agent","human","system"]}}},
    "action_type": {"enum": [
      "edit_insert","edit_delete","edit_replace",
      "file_create","file_delete","file_move","file_rename",
      "checkpoint","rewind","branch","snapshot_create",
      "eval_run","meta_note","merge","rollup"
    ]},
    "branch": {"type": "string"},
    "run_id": {"type": "string"},
    "parent_event_id": {"type": "string"},
    "files": {"type": "array","items": {"type": "string"},"minItems": 1},
    "diff_path": {"type": "string"},
    "diff_mode": {"enum": ["unified","ast","schema","binary"]},
    "affected_lines": {"type": "array","items": {"type": "integer","minimum":0}},
    "semantic_block": {"type": "object","properties": {"kind": {"type": "string"}, "id": {"type": "string"}},"required": ["kind","id"]},
    "operation_id": {"type": "string"},
    "action_scope": {"enum": ["line","block","file","project"]},
    "artifact_impacts": {"type": "array","items": {"type": "object","properties": {"path": {"type": "string"},"kind": {"type": "string"},"bytes_changed": {"type": "integer"},"hash_before": {"type": "string"},"hash_after": {"type": "string"},"summary": {"type": "string"}},"required": ["path","summary"]}},
    "preflight": {"type": "object","properties": {"ok": {"type": "boolean"},"report_artifact": {"type": "string"}}},
    "rationale": {"type": "string"},
    "artifacts": {"type": "array","items": {"type": "string"}},
    "snapshot_ref": {"type": "string"},
    "bookmark": {"type": "string"}
  },
  "additionalProperties": true
}

```

**A3.2 `Snapshot.schema.json`**

```json
{
  "$id": "schema/snapshot.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": [
    "id","ts","base_event_id","tar_uri","env","seeds",
    "event_offset","ledger_driver"
  ],
  "properties": {
    "id": {"type": "string"},
    "ts": {"type": "string","format":"date-time"},
    "base_event_id": {"type": "string"},
    "tar_uri": {"type": "string"},
    "env": {"type": "object"},
    "seeds": {"type": "object"},
    "tools": {"type": "object"},
    "hashes": {"type": "object"},
    "event_offset": {"type": "integer"},
    "ledger_driver": {"enum": ["jsonl","protobuf"]},
    "merged_from": {"type": "array","items": {"type":"string"}},
    "pre_merge_snapshots": {"type": "array","items": {"type":"string"}}
  },
  "additionalProperties": true
}

```

**A3.3 `MergeEvent` (as `ChangeEvent` with `action_type="merge"`)**

```json
{
  "action_type": "merge",
  "left": "bookmark/ours",
  "right": "bookmark/theirs",
  "base": "evt-ancestor",
  "policy": "text|semantic",
  "auto": "none|ours|theirs",
  "resolutions": [
    {"path": "src/app.py","hunk_id": "h1","resolution": "ours|theirs|manual",
     "batch": {"scope": "file|block|op", "selector": "src/app.py#block:handle()"},
     "rationale_file": "Prefer normalized path",
     "rationale_hunk": "Keep validation order",
     "assist": {"source": "agent|llm|none","agent_name": "crew-merge","version": "0.3.1","suggestion": "Keep ours; normalize() downstream","confidence": 0.82}}
  ],
  "binary_choices": [
    {"path": "docs/diagram.png","decision": "ours|theirs|supplied","summary": "Updated architecture diagram","hash_before": "sha256:…","hash_after": "sha256:…","preview_artifact": "results/artifacts/diagram-after.png"}
  ],
  "diff_path": "results/diffs/diff-evt-merge.patch",
  "snapshot_ref": "snap-####",
  "bookmark": "post-merge-####"
}

```

**A3.4 Snapshot Manifest**

```json
{ "merged_from": ["branch/A","branch/B"], "pre_merge_snapshots": ["snapA","snapB"] }

```

---

### A4. Processes

- **Recording**: Proposed → **preflight** → review (diff) → accept → `ChangeEvent` append → optional `Snapshot` per policy.
- **Replay**: Restore nearest snapshot; apply events; hash‑verify; enforce **no‑network**; compare metrics/artifacts.
- **Rewind**: Append `rewind` marker; create branch; subsequent events land on branch.
- **Merge**: 3‑way compute (semantic if flagged) → batch decisions (file/block/op) → record file‑level rationale (optional hunk notes) → **auto snapshot** + `post‑merge` bookmark; **undo** restores `pre_merge_snapshot` to new branch.
- **Rollup**: Compose first→last patch for an `operation_id`; write `rollup_index` artifact; keep raw events; **auto snapshot** after rollup.

---

### A5. Security & Privacy

- Redaction rules (PII/secrets). At‑rest encryption option for `artifacts/`.
- Access controls: read‑only replay roles.

---

### A6. Observability

- **Metrics**: `events_written_total`, `events_since_snapshot`, `restore_duration_ms`, `replay_success_rate`, `diff_render_latency_ms`, `merge_total`, `merge_conflicts_total`, `merge_human_intervention_ratio`, `merge_time_per_file_ms`, `merge_batch_ops_total`, `merge_undo_total`, `rollup_applied_total`, `blob_changes_total`, `synthetic_traces_used_total`.
- **Logs**: event ids, bookmarks, run ids, tool versions, seeds, merge decisions (policy/auto/batch), binary summaries.

---

### A7. Conformance Tests

List test cases with inputs/expected outputs (enforced via `bench validate provenance` and the *bench‑validate* pack):

- **CT‑PROV‑01**: Rebuild state at event X matches hash H.
- **CT‑PROV‑02**: Replay fails on unexpected network call.
- **CT‑PROV‑03**: Bookmark diff between A and B renders side‑by‑side with expected additions/removals.
- **CT‑PROV‑04**: Agent edit without `preflight.ok=true` is rejected.
- **CT‑PROV‑05**: Binary event missing `artifact_impacts[].summary` fails validation.
- **CT‑PROV‑06**: Rollup equivalence holds on fixture sequence.
- **CT‑PROV‑07**: Merge event records required fields; post‑merge snapshot exists; `merge undo` reproduces pre‑merge tree.
- **CT‑PROV‑08**: `merge --dry-run` produces no ledger writes and the promoted merge yields identical hashes.
- **CT‑PROV‑09**: VCS sync post‑sync replay integrity passes.

---

### A8. Change Control

- Semantic versioning for schemas; migration notes; deprecation policy.
- Backwards compatibility: add‑only fields default‑tolerant; breaking changes require `schema_version` bump and migration tool.

---

### A9. References

- ADR‑007 — Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization
- PRD — Diff, Checkpoints, Merge & Replay (Full Spec, v1.1)
- Onboarding/DevEx Flows — Changelog/Bookmarks
- bench‑validate — Schema + semantic rules