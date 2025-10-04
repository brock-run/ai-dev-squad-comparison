# Immediate improvements to Task 2 (high ROI)

1. **Detector determinism & provenance**

* Version every detector and persist it in Evidence:

  * `detector_id: "json_structure@1.2.0"`, `config_hash`, `lib_hash`, `runtime:{py, os}`.
* Add `config_fingerprint` to `Diff`/`Evaluation` so results are replayable after config changes.

2. **Unicode & newline normalization (often missed)**

* Add a **NewlineDetector** and **UnicodeNormalizationDetector**:

  * Normalize `CRLF↔LF` and trailing final newline.
  * NFC/NFKC is tricky—default to NFC-only with an allowlist of artifact types. Flag zero-width spaces, BOM, NBSP explicitly.
* Tests: files differing only by line endings and zero-width chars should classify as benign.

3. **JSON canonicalization: adopt JCS semantics**

* Use RFC 8785–style rules: stable key order, UTF-8, number formatting (`-0` vs `0`, `1` vs `1.0`, exponent canon).
* Add a **JsonNumberFormDetector** to catch `1` vs `1.0` vs `1e0`. Keep this separate from ordering so policies can gate it differently.

4. **Numeric tolerance: move from absolute epsilon to ULP-aware**

* Epsilon-by-scale is safer:

```python
import math
def nearly_equal(a: float, b: float, max_ulps: int = 8) -> bool:
    if math.isnan(a) or math.isnan(b): return False
    if math.isinf(a) or math.isinf(b): return a == b
    # interpret as 64-bit ints preserving ordering
    import struct
    ai = struct.unpack('>q', struct.pack('>d', a))[0]
    bi = struct.unpack('>q', struct.pack('>d', b))[0]
    if ai < 0: ai = 0x8000000000000000 - ai
    if bi < 0: bi = 0x8000000000000000 - bi
    return abs(ai - bi) <= max_ulps
```

* Keep absolute/relative epsilons as fallbacks; record which criterion triggered.

5. **Markdown: AST-based, code-block aware**

* Your MarkdownFormattingDetector should parse to CommonMark AST and ignore code blocks, HTML blocks, and fenced tables. Many false positives come from table reflow and list renumbering.

6. **Nondeterminism (analysis-only)**

* Add **NondeterminismDetector** (timestamps, UUIDs, random ids, sorbet seeds):

  * Regex library of patterns + windowed comparison.
  * Mark as `analysis_only`; route to prevention policies.
  * Emit localized **DiffHunk** tags: `kind:"timestamp" | "uuid" | "orderless_set"`.

7. **Diff quality on large text**

* Switch to **patience diff** for text to cut O(n²) blowups and produce stabler hunks.
* Anchor each `DiffHunk` with `{pre_anchor_hash, post_anchor_hash}` to survive small context shifts.

8. **Detector precedence & composition**

* Make registry explicit: `short-circuit` for cheap benign classes (whitespace/newline) before heavier JSON/AST work; ability to run **all** detectors for full evidence in shadow.
* Add tests ensuring precedence doesn’t mask a more severe class (e.g., semantics masquerading as markdown).

9. **PII redaction before persistence**

* Redact emails, tokens, secrets in `Diff.summary` and `Evaluation.details`. Add a redaction test with seeded secrets.

10. **Observability: per-detector metrics**

* Emit `phase2_detector_duration_ms{detector=...}` and error counters. Track hit-rate by type and average diff size. This will guide policy tuning.

# Small artifacts to add (copy-paste)

**Detector config (versioned) — `entities/detectors/v1.yaml`**

```yaml
version: 1
detectors:
  - id: whitespace@1.0.0
    params: {collapse_runs: true, ignore_trailing_newline: true}
  - id: newline@1.0.0
    params: {normalize_final_newline: true, eol: "lf"}
  - id: unicode_nfc@1.0.0
    params: {form: "NFC", flag_zero_width: true, flag_nbsp: true}
  - id: json_structure@1.2.0
    params: {canonicalize_numbers: true, sort_keys: true}
  - id: json_number_form@1.0.0
    params: {ulps: 8, rel_epsilon: 1e-9, abs_epsilon: 1e-12}
  - id: markdown_format@1.1.0
    params: {ignore_code_blocks: true, normalize_lists: true}
  - id: nondeterminism@1.0.0
    params: {uuid: true, timestamps: ["iso8601","rfc2822"], seeds: ["seed="]}
```

**Evidence schema add-ons (pydantic fields)**

```python
class Evidence(BaseModel):
    detector_id: str  # e.g., "json_structure@1.2.0"
    detector_config_hash: str
    runtime: Dict[str, str]  # {"python":"3.11.6","os":"linux","lib":{"markdown_it":"3.0.0"}}
    redaction_applied: bool = False
```

**Prometheus metrics (detector duration & hit-rate)**

```python
DETECTOR_LATENCY = Histogram("phase2_detector_duration_ms","",["detector"])
DETECTOR_HITS = Counter("phase2_detector_hits_total","",["detector","mismatch_type"])
```

# Tests to add (fast and protective)

* **Unicode & newline**

  * Pairs that differ only by CRLF/LF → `whitespace/newline`.
  * Text with NBSP/zero-width → flagged benign with explicit `flags:["zero_width"]`.

* **ULP numeric**

  * Generate pairs with exact ULP steps (0..16) and assert thresholds.

* **Markdown**

  * Reflowed tables and renumbered lists are benign; fenced code changes are **not**.

* **Precedence**

  * Craft cases that trigger multiple detectors; assert chosen `mismatch_type` and that Evidence records *all* hits in shadow.

* **Performance guard**

  * Parametric benchmark on 10MB JSON arrays: timeout/memory assertions; patience diff must not spike.

* **Redaction**

  * Assert secrets are not persisted (search the DB/logs for tokens).

# Additional Tests

Here is a small, surgical test suite for our deterministic analyzers + analyzer flow. These are drop-in `pytest` tests that don’t hit AI or the click CLI; they exercise the detector classes, the registry, and the `RunAnalyzer` (by calling it directly).

Below are four files we can paste into your repo.

---

### `tests/test_detectors_unit.py`

```python
import pytest

from common.phase2.enums import ArtifactType, MismatchType
from common.phase2.detectors import (
    WhitespaceDetector,
    JsonStructureDetector,
    NumericEpsilonDetector,
    MarkdownFormattingDetector,
)

class TestWhitespaceDetector:
    def test_whitespace_only_difference(self):
        d = WhitespaceDetector()
        src = "Hello,   world!\n  \n"
        tgt = "Hello, world!\n"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert res.mismatch_type == MismatchType.WHITESPACE
        assert res.confidence >= 0.8
        assert res.diff is not None
        assert res.diff.diff_type.value in {"textual", "formatting"}

    def test_no_difference(self):
        d = WhitespaceDetector()
        text = "no change\n"
        assert d.detect(text, text, ArtifactType.TEXT) is None

class TestJsonStructureDetector:
    def test_key_ordering(self):
        d = JsonStructureDetector()
        src = '{"a": 1, "b": 2}'
        tgt = '{"b": 2, "a": 1}'
        res = d.detect(src, tgt, ArtifactType.JSON)
        assert res is not None
        assert res.mismatch_type == MismatchType.JSON_ORDERING
        assert res.confidence >= 0.8
        assert res.diff is not None
        assert res.diff.diff_type.value in {"ordering", "structural"}

    def test_same_json_no_mismatch(self):
        d = JsonStructureDetector()
        src = '{"a": 1, "b": 2}'
        tgt = '{"a": 1, "b": 2}'
        assert d.detect(src, tgt, ArtifactType.JSON) is None

class TestNumericEpsilonDetector:
    def test_small_numeric_difference_within_tolerance(self):
        d = NumericEpsilonDetector()
        src = '{"rate": 1.0000000, "tax": 0.07}'
        tgt = '{"rate": 1.000000001, "tax": 0.07}'
        res = d.detect(src, tgt, ArtifactType.JSON)
        assert res is not None
        assert res.mismatch_type == MismatchType.NUMERIC_EPSILON
        assert res.confidence >= 0.7

    def test_material_numeric_difference(self):
        d = NumericEpsilonDetector()
        src = '{"rate": 1.0}'
        tgt = '{"rate": 1.1}'
        res = d.detect(src, tgt, ArtifactType.JSON)
        # Either None or a low-confidence epsilon; never misclassify as benign
        assert res is None or res.confidence < 0.7

class TestMarkdownFormattingDetector:
    def test_markdown_formatting_only(self):
        d = MarkdownFormattingDetector()
        src = "# Title\n\nSome *text* here."
        tgt = "Title\n=====\n\nSome text here."
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert res.mismatch_type == MismatchType.MARKDOWN_FORMATTING
        assert res.confidence >= 0.8

    def test_markdown_semantic_change_not_flagged_as_formatting(self):
        d = MarkdownFormattingDetector()
        src = "Fee is $10 per user per month."
        tgt = "Fee is $10 per organization per month."
        res = d.detect(src, tgt, ArtifactType.TEXT)
        # Detector should not claim benign formatting when semantics changed
        assert res is None or res.mismatch_type != MismatchType.MARKDOWN_FORMATTING
```

---

### `tests/test_detector_registry.py`

```python
import pytest
from common.phase2.enums import ArtifactType, MismatchType
from common.phase2.detectors import detector_registry

def test_registry_contains_expected_detectors():
    text_detectors = {d.name for d in detector_registry.get_detectors_for_type(ArtifactType.TEXT)}
    json_detectors = {d.name for d in detector_registry.get_detectors_for_type(ArtifactType.JSON)}
    assert any("whitespace" in n for n in text_detectors)
    assert any("markdown" in n for n in text_detectors)
    assert any("json" in n for n in json_detectors)
    assert any("epsilon" in n for n in json_detectors)

def test_detect_all_sorts_by_confidence():
    src = "Hello,   world!\n"
    tgt = "Hello, world!\n"
    results = detector_registry.detect_all(src, tgt, ArtifactType.TEXT)
    assert results and all(results[i].confidence >= results[i+1].confidence for i in range(len(results)-1))

def test_detect_all_returns_empty_on_equal_content():
    text = "no change\n"
    assert detector_registry.detect_all(text, text, ArtifactType.TEXT) == []
```

---

### `tests/test_cli_analyzer.py`

```python
import asyncio
import json
from pathlib import Path
import pytest

from common.phase2.enums import ArtifactType
from common.phase2.cli_analyzer import RunAnalyzer

@pytest.mark.asyncio
async def test_analyze_run_with_inline_sample_data(tmp_path):
    analyzer = RunAnalyzer()
    result = await analyzer.analyze_run(run_id="run_test_inline")
    # Should produce at least one mismatch from the built-in sample
    assert result.mismatches_created > 0
    assert result.evidence_populated == result.mismatches_created
    # Has detector stats populated
    assert isinstance(result.detector_stats, dict) and result.detector_stats

@pytest.mark.asyncio
async def test_analyze_run_with_artifacts_file(tmp_path):
    # Prepare a small artifacts file (json ordering + whitespace)
    artifacts = {
        "a1": {"content": '{"a":1,"b":2}', "type": "json"},
        "a2": {"content": '{"b":2,"a":1}', "type": "json"},
        "t1": {"content": "Hi,   there!\n", "type": "text"},
        "t2": {"content": "Hi, there!\n", "type": "text"},
    }
    p = tmp_path / "artifacts.json"
    p.write_text(json.dumps(artifacts), encoding="utf-8")

    analyzer = RunAnalyzer()
    result = await analyzer.analyze_run(run_id="run_from_file", artifacts_path=str(p))
    assert result.mismatches_created >= 2
    assert result.evidence_populated == result.mismatches_created
    assert result.accuracy_score > 0.0

@pytest.mark.asyncio
async def test_analyze_run_latency_reasonable(tmp_path):
    # Create a ~1MB text artifact pair with only whitespace differences
    base = "word " * 200000  # ~1MB
    artifacts = {
        "t1": {"content": base, "type": "text"},
        "t2": {"content": base.replace("  ", " "), "type": "text"},
    }
    p = tmp_path / "big_artifacts.json"
    p.write_text(json.dumps(artifacts), encoding="utf-8")

    analyzer = RunAnalyzer()
    result = await analyzer.analyze_run(run_id="run_big", artifacts_path=str(p))
    # Not asserting absolute ms; just verifying the analyzer completes quickly and records time
    assert result.mismatches_created >= 1
    assert result.total_latency_ms >= 0
```

---

### `tests/test_diff_entities.py`

```python
from common.phase2.enums import ArtifactType, MismatchType, EquivalenceMethod
from common.phase2.diff_entities import (
    Diff, DiffType, DiffHunk,
    Evaluation, EvaluationResult, EvaluationStatus,
    create_diff, create_evaluation
)

def test_diff_entity_roundtrip():
    d = create_diff("art_src", "art_tgt", DiffType.TEXTUAL, ArtifactType.TEXT)
    d.summary = "whitespace only"
    d.total_changes = 3
    d.lines_added = 0
    d.lines_removed = 0
    d.lines_modified = 3
    payload = d.model_dump()
    d2 = Diff(**payload)
    assert d2.source_artifact_id == "art_src"
    assert d2.diff_type == DiffType.TEXTUAL
    assert d2.total_changes == 3

def test_evaluation_consensus_and_best_result():
    e = create_evaluation("diff_123", "art_src", "art_tgt", ArtifactType.TEXT)
    e.results.append(EvaluationResult(
        method=EquivalenceMethod.EXACT,
        equivalent=False,
        confidence=0.99,
        similarity_score=0.0,
        reasoning="raw strings differ",
        cost=0.0,
        latency_ms=1,
    ))
    e.results.append(EvaluationResult(
        method=EquivalenceMethod.COSINE_SIMILARITY,
        equivalent=True,
        confidence=0.85,
        similarity_score=0.92,
        reasoning="semantically same",
        cost=0.0,
        latency_ms=1,
    ))
    # API: get_best_result / get_average_similarity / mark complete
    best = e.get_best_result()
    assert best is not None
    assert e.get_average_similarity() > 0.4
    e.complete(successful=True)
    assert e.status == EvaluationStatus.COMPLETED
    assert e.successful is True
```

---

### (Optional) `tests/conftest.py`

```python
# Empty on purpose; keep for future fixtures (e.g., tmp DB, registry overrides)
```

---

## Why these tests / what they catch

* **Detector correctness** on the four implemented types (whitespace, JSON ordering, numeric epsilon, markdown formatting), including “no-op” cases to prevent over-detection.
* **Registry contract** (supports proper artifact types; confidence sorting is stable).
* **Analyzer E2E path** without touching the CLI (faster, deterministic), including file-based artifact loading and a light latency sanity check.
* **Evidence entities**: sanity of `Diff`/`Evaluation` round-trips and helper methods used by downstream logic.

## How to run

```bash
pytest -q
```

If you use `pytest-asyncio`, the `@pytest.mark.asyncio` tests will run as shown (most repos already have it; if not, add it to your dev deps).

# What’s next (Task 3 plan you can start now)

## Task 3 — Resolution Engine (idempotent transforms)

**Transforms (pure, reversible):**

* `strip_whitespace(text)`; `normalize_newlines(text, eol="lf")`
* `canonicalize_json(obj, jcs=True, number_form=True)`
* `normalize_markdown(md, ignore_code_blocks=True)`

**Plan/execution flow:**

1. Build `ResolutionTransform` registry mirroring detectors (`id@version`, `config_hash`).
2. **Preview first**: produce `Artifact'` + `Diff` → operator approve → apply.
3. **Idempotency tests**: `apply(apply(x)) == apply(x)` for every transform.
4. **Rollback**: store before/after hashes; one-click revert.
5. **Policy gate**: `ResolutionPolicy.permits(type, action, env)`; enforce dual-key where required.
6. **Metrics**: success/fail, time, “no-op” rate.

**Edge cases:**

* JSON that can’t be parsed → fail closed; do not mutate.
* Markdown inside code blocks → don’t touch.
* Extremely large artifacts → stream to temp files to keep memory flat.