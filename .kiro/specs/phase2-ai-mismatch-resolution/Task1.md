# High-value fixes to this test file (actionable)

1. Make enum handling consistent (avoid string drift)

* You assert strings in some places (`status == 'analyzing'`), enums elsewhere. Pick one internally (enums), cast only at I/O boundaries.
* Add a test to enforce this contract:

```python
def test_internal_types_are_enums():
    m = create_mismatch(...); assert isinstance(m.type, MismatchType)
    p = create_simple_resolution_plan(...); assert isinstance(p.get_status(), ResolutionStatus)
```

2. ID format tests are brittle

* You check fixed lengths (`len == 12/13`). Use regex instead:

```python
import re
assert re.fullmatch(r"mis_[0-9a-z]{8}", mismatch.id)
assert re.fullmatch(r"plan_[0-9a-z]{9}", plan.id)
```

3. Add negative/FSM tests (missing right now)

* Illegal transitions must fail:

```python
with pytest.raises(ValueError):
    mismatch.update_status(MismatchStatus.APPLIED)  # from DETECTED
```

* Parametrize allowed matrix so future enum edits are guarded.

4. Approval workflow edges

* Prevent duplicate approvers; changing `safety_level` should invalidate prior approvals.

```python
plan.add_approval("user1", "standard")
with pytest.raises(ValueError): plan.add_approval("user1", "standard")
plan.safety_level = SafetyLevel.EXPERIMENTAL
assert not plan.has_required_approvals()  # approvals reset
```

5. Concurrency + double-apply

* Add a DB-backed test that two workers try to apply the same plan; exactly one wins. Assert `rowcount == 1` gate in persistence.

6. Policy gating in envs

* You only test dev. Add stage/prod assertions: destructive actions must be blocked in prod even if policy allows in dev.

7. Config precedence & hot-reload

* Add tests for `env > file > defaults`, and that `Phase2Config.fingerprint()` changes on reload.

8. Evidence/Provenance invariants

* Ensure `config_fingerprint`, `eqc_id@version`, `policy_id@version` are persisted; test round-trip and non-null.

9. Security/PII redaction

* Add a test that `Evidence.summary` is redacted for emails/secrets before persistence.

10. Cleanups

* `AsyncMock` is imported but unused.
* Use `pytest.mark.parametrize` where you repeat similar checks.

# Extra tests (copy-paste candidates)

```python
@pytest.mark.parametrize("from_,to,ok", [
    ("open","proposed",True), ("proposed","approved",True),
    ("approved","applied",True), ("applied","proposed",False),
    ("approved","open",False),
])
def test_state_machine(from_, to, ok):
    m = create_mismatch(...); m.status = from_
    if ok: m.update_status(MismatchStatus[to.upper()])
    else:  with pytest.raises(ValueError): m.update_status(MismatchStatus[to.upper()])

def test_unique_applied_plan_constraint(db):
    m = create_mismatch(...); db.save(m)
    p1 = create_simple_resolution_plan(m.id, ResolutionActionType.CANONICALIZE_JSON, "art_001", SafetyLevel.AUTOMATIC)
    p2 = create_simple_resolution_plan(m.id, ResolutionActionType.CANONICALIZE_JSON, "art_001", SafetyLevel.AUTOMATIC)
    db.approve(p1); db.approve(p2)
    assert db.apply(p1) is True
    assert db.apply(p2) is False  # partial unique index on (mismatch_id) WHERE outcome.status='applied'
```

# What’s good already

* Clear coverage of enum semantics (safety, AI requirements).
* Model JSON round-trip tests exist (extend them to assert timezone-aware `datetime`).
* Policy → plan wiring is exercised (add prod/stage variants).

# Continue implementation: next 3 tasks (thin-slice)

## Task 2 — Evidence substrate & deterministic analyzers

* Build `Diff` + `Evaluation` entities and JSON canonicalizer/whitespace/markdown/numeric-epsilon detectors.
* CLI: `bench analyze <run_id>` populates `Mismatch` + Evidence.
* **Accept**: ≥95% accuracy on goldens for those types; p95 ≤ 400ms/100KB.

## Task 3 — Resolution Engine (idempotent)

* Implement `canonicalize_json`, `normalize_markdown`, `strip_whitespace` transforms.
* Gate by `ResolutionPolicy`; preview diff; rollback via stored artifact hashes.
* **Accept**: idempotency test (`apply` twice == once); 0 destructive changes on goldens.

## Task 4 — Semantic Judge (shadow mode)

* Plug in Equivalence methods (embeddings, AST, tests, LLM rubric) with budgets & circuit breakers.
* Write `Evaluation` only (no mutation); emit cost/latency metrics.
* **Accept**: runs over the growing dataset; κ and cost histograms published; no policy violations in logs.

Parallel: scale the labeled dataset toward ≥200 and keep auto-resolve **shadowed** until the CI κ/FP gates pass.