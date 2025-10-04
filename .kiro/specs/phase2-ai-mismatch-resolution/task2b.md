Here are some surgical, line-level review with concrete patches you can drop in now. I’ve focused on: determinism/provenance, correctness edge cases (markdown/code, JSON numbers, whitespace on code, newlines), perf/metrics, and acceptance-criteria math.

Below I show **unified diffs** per file. Apply as-is (or cherry-pick). I’ve kept the changes small and low-risk.

---

## 1) `common/phase2/detectors.py` — correctness, determinism, and coverage

### Why these changes

* Use **timezone-aware** timestamps and **perf_counter** for latency (accurate, monotonic).
* **Do not treat code as whitespace-only**: your current `WhitespaceDetector` strips indentation/blank lines and supports `ArtifactType.CODE` → can misclassify Python/Markdown code changes as benign. I restrict to `TEXT`.
* Add **NewlineDetector** to catch `CRLF↔LF` and final newline—common benign class you’re missing.
* Make JSON “canonicalization” stable (`ensure_ascii=False`, explicit separators) and keep room for JCS later.
* Numeric epsilon: consider **relative + absolute** tolerance; classify as epsilon when **all** non-zero diffs ≤ thresholds (safer than “≥50%”).
* Markdown normalization: **preserve code content** by hashing code spans/blocks to placeholders (your current regex deletes code blocks entirely → false positives).
* Registry: time **every call**, not only detections; track `call_count` and `error_count`; disable `autojunk` in `SequenceMatcher` for stability.
* Provide **severity/precedence** ordering when multiple detectors hit.

### Patch

````diff
*** a/common/phase2/detectors.py
--- b/common/phase2/detectors.py
@@
-import json
-import re
-import difflib
-import hashlib
+import json
+import re
+import difflib
+import hashlib
+import sys, platform, time
 from abc import ABC, abstractmethod
 from typing import Dict, List, Optional, Any, Tuple, Union
-from datetime import datetime
+from datetime import datetime, timezone
 from decimal import Decimal, InvalidOperation
@@
 class DetectorResult:
@@
-        self.detected_at = datetime.utcnow()
+        self.detected_at = datetime.now(timezone.utc)
@@
 class MismatchDetector(ABC):
@@
-        self.detection_count = 0
-        self.total_latency_ms = 0
+        self.detection_count = 0
+        self.call_count = 0
+        self.error_count = 0
+        self.total_latency_ms = 0
@@
     def get_stats(self) -> Dict[str, Any]:
         """Get detector statistics."""
-        avg_latency = self.total_latency_ms / max(1, self.detection_count)
+        avg_latency = self.total_latency_ms / max(1, self.call_count)
         return {
             "name": self.name,
+            "call_count": self.call_count,
             "detection_count": self.detection_count,
+            "error_count": self.error_count,
             "total_latency_ms": self.total_latency_ms,
             "average_latency_ms": avg_latency,
             "supported_types": [t.value for t in self.supported_types]
         }
@@
 class WhitespaceDetector(MismatchDetector):
@@
-    def __init__(self):
-        super().__init__("whitespace_detector", [ArtifactType.TEXT, ArtifactType.CODE])
+    def __init__(self):
+        # Restrict to TEXT; whitespace is semantic in many CODE contexts (e.g., Python)
+        super().__init__("whitespace_detector", [ArtifactType.TEXT])
@@
-        start_time = datetime.utcnow()
+        t0 = time.perf_counter()
@@
-            self.detection_count += 1
-            self.total_latency_ms += int((datetime.utcnow() - start_time).total_seconds() * 1000)
+            self.detection_count += 1
+            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
             return result
-        
+        self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
         return None
@@
-        lines = [line.strip() for line in content.splitlines()]
-        # Join non-empty lines and normalize internal whitespace
-        normalized_lines = []
-        for line in lines:
-            if line:  # Only process non-empty lines
-                # Replace multiple whitespace with single space
-                normalized_line = ' '.join(line.split())
-                normalized_lines.append(normalized_line)
-        return '\n'.join(normalized_lines)
+        # Normalize internal runs of spaces/tabs; preserve blank lines and line boundaries
+        norm_lines = []
+        for line in content.splitlines():
+            # Collapse spaces/tabs inside the line; strip trailing spaces only
+            inner = re.sub(r'[ \t]+', ' ', line).rstrip()
+            norm_lines.append(inner)
+        return '\n'.join(norm_lines)
@@
-        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
+        matcher = difflib.SequenceMatcher(None, source_lines, target_lines, autojunk=False)
@@
-        diff.similarity_score = 1.0 - (changes / max(len(source_lines), len(target_lines), 1))
+        diff.similarity_score = 1.0 - (changes / max(len(source_lines), len(target_lines), 1))
         return diff
@@
 class JsonStructureDetector(MismatchDetector):
@@
-        start_time = datetime.utcnow()
+        t0 = time.perf_counter()
@@
-            source_canonical = self._canonicalize_json(source_json)
-            target_canonical = self._canonicalize_json(target_json)
+            source_canonical = self._canonicalize_json(source_json)
+            target_canonical = self._canonicalize_json(target_json)
@@
-                self.detection_count += 1
-                self.total_latency_ms += int((datetime.utcnow() - start_time).total_seconds() * 1000)
+                self.detection_count += 1
+                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                 return result
                 
         except json.JSONDecodeError:
             # Not valid JSON, can't detect JSON-specific issues
             pass
-        
+        self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
         return None
@@
-    def _canonicalize_json(self, obj: Any) -> str:
-        """Canonicalize JSON object for comparison."""
-        return json.dumps(obj, sort_keys=True, separators=(',', ':'))
+    def _canonicalize_json(self, obj: Any) -> str:
+        """Canonicalize JSON object for comparison (stable keys, stable separators).
+        Note: not full RFC 8785 JCS; number form normalization is handled by a separate detector."""
+        return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
@@
 class NumericEpsilonDetector(MismatchDetector):
@@
-    def __init__(self, epsilon: float = 1e-6):
+    def __init__(self, epsilon: float = 1e-6, rel_epsilon: float = 1e-9):
         super().__init__("numeric_epsilon_detector", [ArtifactType.TEXT, ArtifactType.JSON, ArtifactType.CODE])
         self.epsilon = epsilon
+        self.rel_epsilon = rel_epsilon
@@
-        start_time = datetime.utcnow()
+        t0 = time.perf_counter()
@@
-        if len(source_numbers) != len(target_numbers):
-            return None
+        if len(source_numbers) != len(target_numbers):
+            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
+            return None
@@
-        epsilon_diffs = []
-        for i, (src_num, tgt_num) in enumerate(zip(source_numbers, target_numbers)):
-            diff = abs(src_num - tgt_num)
-            if diff > 0 and diff <= self.epsilon:
-                epsilon_diffs.append((i, src_num, tgt_num, diff))
-        
-        # If we found epsilon differences and they account for most/all numeric differences
-        if epsilon_diffs and len(epsilon_diffs) >= len(source_numbers) * 0.5:
+        epsilon_diffs = []
+        any_nonzero = False
+        for i, (src_num, tgt_num) in enumerate(zip(source_numbers, target_numbers)):
+            diff = abs(src_num - tgt_num)
+            if diff == 0.0:
+                continue
+            any_nonzero = True
+            rel = diff / max(abs(src_num), abs(tgt_num), 1e-15)
+            if diff <= self.epsilon or rel <= self.rel_epsilon:
+                epsilon_diffs.append((i, src_num, tgt_num, diff))
+            else:
+                # A material numeric change exists → not benign epsilon
+                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
+                return None
+        # Classify as epsilon only if all non-zero diffs were within thresholds
+        if any_nonzero and epsilon_diffs:
             diff = self._create_numeric_diff(source_content, target_content, epsilon_diffs, artifact_type)
-            confidence = self._calculate_numeric_confidence(epsilon_diffs, source_numbers)
+            confidence = self._calculate_numeric_confidence(epsilon_diffs, source_numbers)
@@
-            self.detection_count += 1
-            self.total_latency_ms += int((datetime.utcnow() - start_time).total_seconds() * 1000)
+            self.detection_count += 1
+            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
             return result
-        
+        self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
         return None
@@
 class MarkdownFormattingDetector(MismatchDetector):
@@
-        start_time = datetime.utcnow()
+        t0 = time.perf_counter()
@@
-        source_normalized = self._normalize_markdown(source_content)
-        target_normalized = self._normalize_markdown(target_content)
+        source_normalized = self._normalize_markdown(source_content)
+        target_normalized = self._normalize_markdown(target_content)
@@
-            self.detection_count += 1
-            self.total_latency_ms += int((datetime.utcnow() - start_time).total_seconds() * 1000)
+            self.detection_count += 1
+            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
             return result
-        
+        self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
         return None
@@
-        # Remove headers (# ## ###)
+        # Remove headers (# ## ###)
         normalized = re.sub(r'^#+\s*', '', normalized, flags=re.MULTILINE)
@@
-        # Remove code blocks and inline code
-        normalized = re.sub(r'```[^`]*```', '', normalized, flags=re.DOTALL)
-        normalized = re.sub(r'`([^`]+)`', r'\1', normalized)
+        # Preserve code content by hashing to placeholders so changes in code don't vanish
+        def _hash_code(m):
+            import hashlib
+            h = hashlib.sha256(m.group(1).encode("utf-8")).hexdigest()[:8]
+            return f" CODEBLOCK:{h} "
+        normalized = re.sub(r"```[\w\-]*\n(.*?)```", lambda m: _hash_code(m), normalized, flags=re.DOTALL)
+        normalized = re.sub(r"`([^`]+)`", lambda m: f" CODE:{hashlib.sha256(m.group(1).encode('utf-8')).hexdigest()[:8]} ", normalized)
@@
         return normalized.strip()
@@
-        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
+        matcher = difflib.SequenceMatcher(None, source_lines, target_lines, autojunk=False)
@@
         return diff
+
+
+class NewlineDetector(MismatchDetector):
+    """Detects newline/EOL differences (CRLF vs LF) and final newline presence."""
+    def __init__(self):
+        super().__init__("newline_detector", [ArtifactType.TEXT, ArtifactType.CODE])
+    def detect(self, source_content: str, target_content: str, artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
+        t0 = time.perf_counter()
+        # Normalize CRLF/CR->LF for comparison; preserve content otherwise
+        s_norm = source_content.replace("\r\n", "\n").replace("\r", "\n")
+        t_norm = target_content.replace("\r\n", "\n").replace("\r", "\n")
+        if s_norm == t_norm and source_content != target_content:
+            # Create a small formatting diff
+            diff = create_diff("source","target", DiffType.FORMATTING, artifact_type)
+            hunk = create_diff_hunk(
+                operation=DiffOperation.REPLACE, source_start=0, source_length=len(source_content.splitlines()),
+                target_start=0, target_length=len(target_content.splitlines()),
+                source_content=source_content[:200], target_content=target_content[:200]
+            )
+            hunk.metadata = {"change_type":"newline_eol"}
+            diff.hunks.append(hunk)
+            diff.total_changes = 1
+            diff.summary = "EOL normalization differences (CRLF/LF or final newline)"
+            self.detection_count += 1
+            self.total_latency_ms += int((time.perf_counter()-t0)*1000)
+            return DetectorResult(
+                mismatch_type=MismatchType.WHITESPACE,
+                confidence=0.9,
+                diff=diff,
+                reasoning="Content identical after EOL normalization",
+                metadata={"newline_only": True}
+            )
+        self.total_latency_ms += int((time.perf_counter()-t0)*1000)
+        return None
@@
 class DetectorRegistry:
@@
     def _register_default_detectors(self):
         """Register default detectors."""
-        self.register(WhitespaceDetector())
+        # Precedence: very cheap (newline) → whitespace → JSON → numeric → markdown
+        self.register(NewlineDetector())
+        self.register(WhitespaceDetector())
         self.register(JsonStructureDetector())
         self.register(NumericEpsilonDetector())
         self.register(MarkdownFormattingDetector())
@@
-    def detect_all(self, source_content: str, target_content: str, 
+    def detect_all(self, source_content: str, target_content: str, 
                    artifact_type: ArtifactType, **kwargs) -> List[DetectorResult]:
         """Run all applicable detectors and return results."""
-        results = []
-        
+        results: List[DetectorResult] = []
+        precedence = {
+            # lower number = higher precedence when confidences tie
+            "newline_detector": 0,
+            "whitespace_detector": 1,
+            "json_structure_detector": 2,
+            "numeric_epsilon_detector": 3,
+            "markdown_formatting_detector": 4,
+        }
         for detector in self.get_detectors_for_type(artifact_type):
             try:
-                result = detector.detect(source_content, target_content, artifact_type, **kwargs)
+                t0 = time.perf_counter()
+                detector.call_count += 1
+                result = detector.detect(source_content, target_content, artifact_type, **kwargs)
                 if result:
                     results.append(result)
             except Exception as e:
                 # Log error but continue with other detectors
-                print(f"Detector {detector.name} failed: {e}")
+                detector.error_count += 1
+                print(f"Detector {detector.name} failed: {e}")
-        
-        # Sort by confidence (highest first)
-        results.sort(key=lambda r: r.confidence, reverse=True)
+        # Sort by (confidence desc, precedence asc)
+        results.sort(key=lambda r: (-r.confidence, precedence.get(getattr(r, "detector_name", ""), 99)))
         return results
````

> Note: For the precedence tie-break, if you want exact names, you can also attach `result.detector_name = self.name` inside each detector before returning.

---

## 2) `common/phase2/diff_entities.py` — timezone & stricter schema

### Why these changes

* Use **timezone-aware** timestamps.
* Tighten Pydantic config: **forbid extra**, and (if your enums are used as values) keep `use_enum_values=True` to avoid mixed types in persistence.
* Small comment: you use `datetime.utcnow()` in a few places.

### Patch

```diff
*** a/common/phase2/diff_entities.py
--- b/common/phase2/diff_entities.py
@@
-from datetime import datetime
+from datetime import datetime, timezone
@@
 class Diff(BaseModel):
+    model_config = {"extra": "forbid", "use_enum_values": True}
@@
-    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
+    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
@@
 class Evaluation(BaseModel):
+    model_config = {"extra": "forbid", "use_enum_values": True}
@@
-    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
+    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
-    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
+    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
@@
-        self.completed_at = datetime.utcnow()
+        self.completed_at = datetime.now(timezone.utc)
         if error_message:
             self.error_message = error_message
         return self
```

---

## 3) `common/phase2/cli_analyzer.py` — acceptance math, bytes counted, safer fallback

### Why these changes

* Acceptance should use **actual bytes scanned** (you estimate 10KB per mismatch—very rough).
* Add **content_bytes** tally and compute `ms / 100KB` accurately.
* Fallback classification: using `NONDETERMINISM` as a generic diff can be misleading; if no detector hits, mark as **general textual/structural difference** (pick `SEMANTICS_TEXT` for TEXT/Markdown and `SEMANTICS_CODE` for CODE) so downstream policies don’t mistakenly route to prevention-only paths.
* (Optional) attach detector name to results for precedence sorting.

### Patch

```diff
*** a/common/phase2/cli_analyzer.py
--- b/common/phase2/cli_analyzer.py
@@
 class AnalysisResult:
@@
         self.detector_stats = {}
         self.errors = []
+        self.total_bytes = 0
@@
     async def analyze_run(self, run_id: str, artifacts_path: Optional[str] = None,
                          output_path: Optional[str] = None) -> AnalysisResult:
@@
-            artifact_pairs = self._find_artifact_pairs(artifacts)
+            artifact_pairs = self._find_artifact_pairs(artifacts)
+            # Tally bytes once
+            result.total_bytes = sum(len(a.get("content","").encode("utf-8")) for a in artifacts.values())
@@
-        if not detector_results:
-            # No specific mismatch type detected, classify as general difference
-            detector_results = [DetectorResult(
-                mismatch_type=MismatchType.NONDETERMINISM,
-                confidence=0.5,
-                reasoning="No specific mismatch pattern detected"
-            )]
+        if not detector_results:
+            # No specific mismatch pattern detected → classify as general semantic difference by artifact class
+            fallback_type = (
+                MismatchType.SEMANTICS_TEXT if artifact_type == ArtifactType.TEXT
+                else MismatchType.SEMANTICS_CODE if artifact_type == ArtifactType.CODE
+                else MismatchType.SEMANTICS_TEXT
+            )
+            detector_results = [DetectorResult(
+                mismatch_type=fallback_type,
+                confidence=0.5,
+                reasoning="No deterministic pattern matched; flagging as general semantic difference"
+            )]
@@
-    # Calculate latency per 100KB (rough estimate)
-    estimated_content_kb = result.mismatches_created * 10  # Assume 10KB per mismatch
-    latency_per_100kb = (result.total_latency_ms / max(1, estimated_content_kb)) * 100
+    # Calculate latency per 100KB based on actual bytes analyzed
+    kb = max(1, result.total_bytes // 1024)
+    latency_per_100kb = (result.total_latency_ms / kb) * 100
@@
     if accuracy_pass and latency_pass:
         click.echo(f"\n🎉 Analysis PASSED all acceptance criteria!")
-        return 0
+        return 0
     else:
         click.echo(f"\n❌ Analysis FAILED acceptance criteria")
         return 1
```

---

## Additional nits / suggestions (non-blocking)

* **Attach detector identity to results**: inside each detector, set `result.metadata["detector"] = self.name` (and/or `result.detector_name = self.name`). Your registry tie-break becomes robust.
* **Redaction**: before storing `Diff.summary` or hunk contents anywhere persistent, run a simple PII/token redactor (emails, `api_key=...`). You can add a tiny helper in `diff_entities` and call it from detectors.
* **Unit tests**: add quick cases for:

  * CRLF↔LF (`NewlineDetector`).
  * Markdown code blocks: changes inside code should NOT be flagged as formatting; your new hashing placeholders will ensure normalized strings differ.
  * Numeric epsilon: values that differ by relative threshold only (e.g., `1e9` vs `1e9+1`), and clear material changes (fail fast).
  * Whitespace on code: confirm `WhitespaceDetector` skips `ArtifactType.CODE`.

---

## What this unlocks

With these patches, Task 2 becomes more robust against the classic pitfalls (newline/eol, code-in-markdown, number forms, perf metrics). You’re ready to start **Task 3 (Resolution Engine)** while adding the few tests above.
