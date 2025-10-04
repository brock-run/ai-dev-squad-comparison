# UX Flows: Merge Conflict Resolution

Created by: Brock Butler
Created time: September 27, 2025 9:24 PM
Last edited by: Brock Butler
Last updated time: September 27, 2025 9:29 PM
Parent item: v1 White Paper: Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization (https://www.notion.so/v1-White-Paper-Code-Diff-Storage-Rewinds-Replays-Bookmarks-and-Visualization-27b11cd755ab809ca950e00144cb5d7a?pvs=21)

# Merge UX — Text 3‑Way MVP

**Goal:** Provide a clear, deterministic, auditable merge experience when branches/bookmarks rejoin. Ship a solid **textual 3‑way** first; gate semantic YAML/JSON merges behind a flag.

---

## 1) User story

“As a reviewer, when two agent/human branches diverge, I want to preview the combined change, resolve conflicts quickly, and record my rationale — with a snapshot created automatically after merge.”

---

## 2) Flow (happy path)

1. User runs `bench merge <A> <B>`.
2. System finds **LCA** and computes a **textual 3‑way**.
3. If no conflicts → show preview → confirm → create `merge` event + **snapshot**.

### Flow (with conflicts)

1. Same as above, but enter **Conflict TUI**.
2. Resolve per file/hunk: choose **ours**, **theirs**, or **edit**.
3. Enter a **rationale** note per file.
4. Confirm → `merge` event recorded (policy=text; conflicts/resolutions), **snapshot** auto-created, `merge_resolution` artifact saved.

---

## 3) Wireframe (terminal TUI)

```
┌ Merge: A=bookmark/foo  B=bookmark/bar   base=LCA(eid:evt-123) ┐
│ Policy: text (semantic: off)   Files: 2/5 in conflict           │
├─────────────────────────────────────────────────────────────────┤
│ app/service.py  (3 hunks)                                      v│
│                                                                 │
│ @@ Hunk 1 @@                                                    │
│ >>> BASE                                                        │
│   def handle(x):                                                │
│ >>> OURS (A)                                                    │
│ -   return x+1                                                  │
│ +   return normalize(x+1)                                       │
│ >>> THEIRS (B)                                                  │
│ +   return x + 1  # fix spacing                                 │
│                                                                 │
│ [o] ours   [t] theirs   [e] edit   [n] next hunk   [p] prev     │
│ Rationale (file): ____________________________________________  │
├─────────────────────────────────────────────────────────────────┤
│ [S] Save & Continue   [V] View merged preview   [Q] Cancel      │
└─────────────────────────────────────────────────────────────────┘

```

**Keyboard shortcuts**

- `o/t/e` choose resolution per hunk.
- `n/p` navigate hunks; `V` preview merged file; `S` save decisions.
- 

![image.png](UX%20Flows%20Merge%20Conflict%20Resolution%2027c11cd755ab80c7854be0f7e392f70f/image.png)

---

## 4) Preview screen

```
┌ Preview: app/service.py (merged) ┐
│ + def handle(x):                 │
│ +     return normalize(x+1)      │
│                                  │
│ [A] Accept file   [B] Back       │
└──────────────────────────────────┘

```

---

## 5) Event & artifacts recorded

- `merge` event

```json
{
  "action_type": "merge",
  "left": "bookmark/foo",
  "right": "bookmark/bar",
  "base": "evt-123",
  "policy": "text",
  "diff_path": "results/diffs/diff-evt-merge.patch",
  "snapshot_ref": "snap-0021",
  "conflicts": [
    {"path":"app/service.py","resolution":"ours","rationale":"prefer normalized path"}
  ]
}

```

- `merge_resolution` artifact (JSON) with per-file hunks + choices.
- Post-merge **snapshot** created automatically.

---

## 6) Error & edge cases

- **Abort/resume**: if user quits, a temp state is saved under `.user/merge/` → `bench merge --resume` continues.
- **Binary files**: flagged; require manual replace + rationale (no auto-merge).
- **Semantic flag on**: YAML/JSON files attempt path-merge first; unresolved conflicts drop back to text TUI.

---

## 7) Metrics & acceptance

- p95 time to resolve a 10‑file conflict set ≤ 5 min (internal dogfood).
- 100% of merges recorded with rationale and snapshot.
- Replay of pre‑merge states + merge event → produces merged tree bit‑for‑bit.

---

## 8) Next (v1.1+)

- Batch accept/reject hunks per semantic block (Python functions, YAML paths).
- Inline diff minimap & search.
- “Explain this conflict” agent assist (non‑blocking).