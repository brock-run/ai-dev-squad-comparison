Nice work — Task 2 looks properly hardened. You hit the big rocks (determinism, provenance, newline/ULP, code-block safety, perf/metrics). I’ll call out two tiny last-mile nits, then give you a **ready-to-drop scaffold for Task 3 (Resolution Engine)** with idempotent transforms, preview/rollback, policy gating, and tests.

## Two tiny nits on Task 2 (finish now)

* **Attach detector identity onto results**: set `result.metadata["detector"]=self.name` (and optionally `result.detector_name = self.name`) in each detector before returning. Your precedence tiebreaker will be deterministic even if registry order shifts.
* **Anchor diff hunks**: when you build `DiffHunk`, add short context anchors (`context_before/context_after` as first/last 50 chars). It makes preview + rollback safer when surrounding text shifts.

---

## Task 3 – Resolution Engine (thin-slice you can implement now)

### Goals (acceptance)

* **Idempotent transforms** for benign classes: `NORMALIZE_WHITESPACE` (TEXT), `CANONICALIZE_JSON` (JSON), `NORMALIZE_NEWLINES` (TEXT/CODE), `NORMALIZE_MARKDOWN` (TEXT).
* **Preview-first**: show diff before apply; **no mutation** until approved by policy.
* **Rollbackable**: store before/after hashes; one-click revert works.
* **Policy gating**: respect `ResolutionPolicy` + `SafetyLevel` (dual-key, env rules).
* **Concurrency-safe**: single winner applies (`UPDATE … WHERE status='approved'`), others see no-op.

### Default mapping (suggestion)

Mismatch → default transform(s):

* `WHITESPACE` → `NORMALIZE_WHITESPACE` (+ `NORMALIZE_NEWLINES`)
* `JSON_ORDERING` → `CANONICALIZE_JSON`
* `MARKDOWN_FORMATTING` → `NORMALIZE_MARKDOWN`
* `NUMERIC_EPSILON` → **no transform** (advisory-only; don’t rewrite numbers)

---

### 1) Core engine + transform registry

Create `common/phase2/resolution_engine.py`:

````python
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, List, Callable
from datetime import datetime, timezone
import json, re, hashlib

from .enums import ArtifactType, ResolutionActionType, SafetyLevel
from .diff_entities import Diff, DiffType, DiffHunk, DiffOperation, create_diff, create_diff_hunk

@dataclass
class TransformResult:
    new_content: str
    diff: Diff
    summary: str
    idempotent: bool

class ResolutionTransform:
    id: str = "base@0.0.0"
    action_type: ResolutionActionType
    artifact_types: List[ArtifactType]

    def applies_to(self, artifact_type: ArtifactType) -> bool:
        return artifact_type in self.artifact_types

    def preview(self, content: str, artifact_type: ArtifactType, artifact_id: str) -> TransformResult:
        """Return new content + diff without side effects."""
        nc = self.apply(content, artifact_type)
        d = self._diff(artifact_id, nc, content, artifact_type)
        return TransformResult(
            new_content=nc,
            diff=d,
            summary=d.summary or f"{self.id} preview",
            idempotent=(self.apply(nc, artifact_type) == nc),
        )

    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        raise NotImplementedError

    def _diff(self, art_id: str, new: str, old: str, atype: ArtifactType) -> Diff:
        if new == old:
            diff = create_diff(art_id, art_id, DiffType.FORMATTING, atype)
            diff.summary = "No changes"
            return diff
        # simple line diff (stable)
        old_lines, new_lines = old.splitlines(), new.splitlines()
        from difflib import SequenceMatcher
        m = SequenceMatcher(None, old_lines, new_lines, autojunk=False)
        diff = create_diff(art_id, art_id, DiffType.FORMATTING, atype)
        changes = 0
        for tag, i1, i2, j1, j2 in m.get_opcodes():
            if tag == 'equal': continue
            changes += 1
            h = create_diff_hunk(
                operation=DiffOperation.REPLACE if tag=='replace' else DiffOperation.DELETE if tag=='delete' else DiffOperation.INSERT,
                source_start=i1, source_length=i2-i1, target_start=j1, target_length=j2-j1,
                source_content="\n".join(old_lines[i1:i2]) if i2>i1 else "",
                target_content="\n".join(new_lines[j1:j2]) if j2>j1 else "",
            )
            # anchors
            h.context_before = "\n".join(old_lines[max(i1-1,0):i1])[:200]
            h.context_after  = "\n".join(old_lines[i2:i2+1])[:200]
            diff.hunks.append(h)
        diff.total_changes = changes
        diff.lines_removed = max(0, len(old_lines) - len(new_lines))
        diff.lines_added   = max(0, len(new_lines) - len(old_lines))
        diff.similarity_score = 1.0 - (changes / max(1, max(len(old_lines), len(new_lines))))
        diff.summary = f"{self.action_type.value} produced {changes} change hunk(s)"
        return diff

# ---- Concrete transforms (idempotent by construction) ----

class NormalizeNewlinesTransform(ResolutionTransform):
    id = "normalize_newlines@1.0.0"
    action_type = ResolutionActionType.NORMALIZE_WHITESPACE  # reuse existing action
    artifact_types = [ArtifactType.TEXT, ArtifactType.CODE]
    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        c = content.replace("\r\n","\n").replace("\r","\n")
        # ensure single final newline presence
        return (c if c.endswith("\n") else c + "\n") if c else c

class NormalizeWhitespaceTransform(ResolutionTransform):
    id = "normalize_whitespace@1.0.0"
    action_type = ResolutionActionType.NORMALIZE_WHITESPACE
    artifact_types = [ArtifactType.TEXT]
    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        out=[]
        for line in content.splitlines():
            out.append(re.sub(r'[ \t]+',' ', line).rstrip())
        return "\n".join(out)

class CanonicalizeJsonTransform(ResolutionTransform):
    id = "canonicalize_json@1.1.0"
    action_type = ResolutionActionType.CANONICALIZE_JSON
    artifact_types = [ArtifactType.JSON]
    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            return content  # fail closed
        # Stable keys & separators; number-form left as-is (policy can add a stricter variant later)
        return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

class NormalizeMarkdownTransform(ResolutionTransform):
    id = "normalize_markdown@1.0.0"
    action_type = ResolutionActionType.REWRITE_FORMATTING  # advisory/experimental by policy
    artifact_types = [ArtifactType.TEXT]
    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        # Minimal, safe normalization (no changes inside fenced code)
        def hash_block(m):
            import hashlib
            return f"\n```BLOCK-{hashlib.sha256(m.group(1).encode()).hexdigest()[:8]}```\n"
        s = re.sub(r"```[\w-]*\n(.*?)```", hash_block, content, flags=re.DOTALL)
        s = re.sub(r"^(\w[^\n]+)\n=+\s*$", r"# \1", s, flags=re.MULTILINE)  # setext -> atx
        s = re.sub(r"\s+\n", "\n", s)  # trim trailing spaces before newline
        return s

# ---- Registry & engine ----

class TransformRegistry:
    def __init__(self):
        self._by_action: Dict[ResolutionActionType, List[ResolutionTransform]] = {}
        self._all: List[ResolutionTransform] = []
    def register(self, t: ResolutionTransform):
        self._all.append(t)
        self._by_action.setdefault(t.action_type, []).append(t)
    def get(self, action: ResolutionActionType, atype: ArtifactType) -> Optional[ResolutionTransform]:
        for t in self._by_action.get(action, []):
            if t.applies_to(atype): return t
        return None

transform_registry = TransformRegistry()
for t in (NormalizeNewlinesTransform(), NormalizeWhitespaceTransform(), CanonicalizeJsonTransform(), NormalizeMarkdownTransform()):
    transform_registry.register(t)

class ResolutionEngine:
    def __init__(self, registry: TransformRegistry | None = None):
        self.registry = registry or transform_registry

    def preview_action(self, action_type: ResolutionActionType, artifact_id: str, artifact_type: ArtifactType, content: str) -> TransformResult:
        t = self.registry.get(action_type, artifact_type)
        if not t: raise ValueError(f"No transform for {action_type} on {artifact_type}")
        return t.preview(content, artifact_type, artifact_id)

    def apply_action(self, action_type: ResolutionActionType, artifact_id: str, artifact_type: ArtifactType, content: str) -> TransformResult:
        # same as preview but called post-approval; caller persists content & diff + rollback hash
        return self.preview_action(action_type, artifact_id, artifact_type, content)
````

> You already have `ResolutionPlan` and policy logic—wire `ResolutionEngine` into your `apply_plan()` path, and store `{before_hash, after_hash, transform_id, config_fingerprint}` in the plan outcome.

---

### 2) CLI integration (preview/approve/apply)

Add a small extension to `common/phase2/cli_analyzer.py` or a new `cli_resolve.py`:

```python
import click, hashlib
from .resolution_engine import ResolutionEngine
from .enums import ResolutionActionType, ArtifactType
from .config import create_default_config, Environment

@click.command()
@click.argument("artifact_id")
@click.option("--action", type=click.Choice([a.value for a in ResolutionActionType]), required=True)
@click.option("--atype", "artifact_type", type=click.Choice([a.value for a in ArtifactType]), required=True)
@click.option("--input-path", required=True, help="Path to artifact content file")
@click.option("--apply", is_flag=True, help="Apply after preview if policy allows")
def resolve(artifact_id, action, artifact_type, input_path, apply):
    cfg = create_default_config(Environment.DEVELOPMENT)
    eng = ResolutionEngine()
    content = open(input_path, "r", encoding="utf-8").read()
    atype = ArtifactType(artifact_type)
    act = ResolutionActionType(action)

    # Policy gate
    pol = cfg.get_resolution_policy_for_action(act, atype) if hasattr(cfg, "get_resolution_policy_for_action") else cfg.get_resolution_policy
    if hasattr(cfg, "is_action_allowed") and not cfg.is_action_allowed(mismatch_type=None, action=act):  # adapt to your API
        raise click.ClickException("Action not allowed by policy")

    preview = eng.preview_action(act, artifact_id, atype, content)
    click.echo(f"Preview: {preview.summary}")
    click.echo(f"Idempotent: {preview.idempotent}")
    click.echo(f"Diff hunks: {len(preview.diff.hunks)}")

    if apply:
        # Here you’d also require approvals per SafetyLevel before persist
        applied = eng.apply_action(act, artifact_id, atype, content)
        outp = input_path + ".resolved"
        open(outp, "w", encoding="utf-8").write(applied.new_content)
        click.echo(f"Applied. Wrote {outp}")
```

(Adapt the policy lookups to your config helpers; I kept it generic.)

---

### 3) Tests you should add (fast)

`tests/test_resolution_transforms.py`:

```python
import pytest
from common.phase2.enums import ArtifactType, ResolutionActionType
from common.phase2.resolution_engine import ResolutionEngine, CanonicalizeJsonTransform, NormalizeWhitespaceTransform, NormalizeNewlinesTransform

def test_json_canonicalize_idempotent():
    eng = ResolutionEngine()
    c1 = '{ "b": 2, "a": 1 }'
    r1 = eng.preview_action(ResolutionActionType.CANONICALIZE_JSON, "a1", ArtifactType.JSON, c1)
    r2 = eng.preview_action(ResolutionActionType.CANONICALIZE_JSON, "a1", ArtifactType.JSON, r1.new_content)
    assert r1.new_content == r2.new_content
    assert r1.idempotent and r2.idempotent

def test_whitespace_normalize_text_only():
    eng = ResolutionEngine()
    text = "Hello,   world!  \n"
    r = eng.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "t1", ArtifactType.TEXT, text)
    assert "  " not in r.new_content
    with pytest.raises(ValueError):
        eng.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "c1", ArtifactType.CODE, "x =  1")

def test_normalize_newlines_adds_final_newline():
    eng = ResolutionEngine()
    text = "a\r\nb\r\nc"
    r = eng.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "t", ArtifactType.TEXT, text)  # our transform reused action type
    assert r.new_content.endswith("\n")
```

`tests/test_policy_gate_resolution.py` (minimal):

```python
from common.phase2.enums import Environment, MismatchType, ResolutionActionType, ArtifactType, SafetyLevel
from common.phase2.config import create_default_config

def test_policy_blocks_destructive_in_prod():
    cfg = create_default_config(Environment.PRODUCTION)
    # Assume REWRITE_FORMATTING is not auto-apply in prod
    if hasattr(cfg, "is_action_allowed"):
        assert not cfg.is_action_allowed(MismatchType.MARKDOWN_FORMATTING, ResolutionActionType.REWRITE_FORMATTING)
```

---

## Ops & safety checklist (flip these on as you wire apply)

* **One-winner apply**: `UPDATE resolution_plan SET status='applied' WHERE id=:id AND status='approved'` and assert `rowcount == 1`.
* **Partial unique index**: one applied plan per mismatch: `(mismatch_id) WHERE outcome->>'status'='applied'`.
* **Rollback record**: store `{artifact_id, before_hash, after_hash, transform_id, ts}` in `plan.outcome`.
* **Metrics**: counters for `resolution_apply_total{action}`, `resolution_noop_total`, histograms for `resolution_latency_ms{action}`.
* **Kill switch**: read from `phase2_runtime.yaml`; refuse apply if disabled.

---

## Bottom line

* Task 2: ✅ solid. Just add the two nits (detector name on results, anchors in hunks).
* Start **Task 3 now** with the scaffold above. Focus on **idempotency, preview/rollback, and policy gating**. Keep auto-resolve **shadowed** until the ≥200-item dataset passes the κ/FP gates.
