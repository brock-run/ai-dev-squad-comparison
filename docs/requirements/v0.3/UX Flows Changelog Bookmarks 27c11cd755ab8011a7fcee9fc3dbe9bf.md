# UX Flows: Changelog/Bookmarks

Created by: Brock Butler
Created time: September 27, 2025 8:01 PM
Category: User Flows
Last edited by: Brock Butler
Last updated time: September 27, 2025 9:25 PM
Parent item: v1 White Paper: Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization (https://www.notion.so/v1-White-Paper-Code-Diff-Storage-Rewinds-Replays-Bookmarks-and-Visualization-27b11cd755ab809ca950e00144cb5d7a?pvs=21)

## Onboarding & DevEx Flows — §Changelog/Bookmarks (Template)

**Doc ID**: ODX-CLG-BMK-v1.0

**Owner**: DevEx

**Status**: Draft → Review → Accepted

### C1. Objectives

- Make it trivial to see “what changed, when, why, by whom,” approve it, bookmark it, and rewind/replay later.

### C2. Flow Overview (state machine)

States: `idle → propose_change → review_diff → approve|reject → record_event → (optional snapshot) → bookmark_optional → done`

- **Rewind path**: `any_state → rewind(bookmark) → branch(new) → propose_change...`

### C3. CLI/UX Contracts

- `bench history [filters]` — timeline view.
- `bench diff <A> <B> [--file] [--side-by-side]` — visual compare.
- `bench bookmark add|list|rm` — manage anchors.
- `bench snapshot save` — manual snapshot.
- `bench rewind <bookmark|event>` — time‑travel; creates branch.
- `bench replay <A>..<B> [--dry-run] [--no-network]` — deterministic replay.

### C4. Changelog Rules

- **ODX‑CLG‑001**: Only **accepted** proposals append to `events.jsonl` (previews are non‑persistent).
- **ODX‑CLG‑002**: Each event MUST include rationale; agent proposals MUST include tool/LLM trace artifact refs.

### C5. Bookmark Policy

- Names are unique per project; resolving to event or snapshot ids.
- Bookmark ops (`add/rm`) emit `checkpoint` events for audit.

### C6. Error Handling & Escalation

- Replay divergence → present diff of expected vs observed; offer export bundle; allow escalate to human review.
- Snapshot restore failure → attempt previous snapshot; log telemetry; suggest GC or rebuild.

### C7. Examples (ready to copy)

- Example bookmark naming: `pre-optimizer`, `post-dspy-accept`, `candidate-release`.
- Example approval checklist (below).

### C8. Approval Checklist (review gate)

- [ ]  Diff renders and matches intent (green adds, red removes)
- [ ]  Rationale explains *why*
- [ ]  Tests/evals pass
- [ ]  Bookmark created (if milestone)
- [ ]  Snapshot policy evaluated (auto/manual as needed)

### C9. Telemetry

- Emit: `bookmark_created_total`, `diff_view_opens_total`, `rewind_operations_total`, `replay_failures_total`.