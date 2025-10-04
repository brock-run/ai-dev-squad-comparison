"""Phase 2 Deterministic Mismatch Detectors

This module provides deterministic analyzers for detecting and classifying
different types of mismatches between artifacts. These detectors form the
foundation for accurate mismatch classification.
"""

import json
import re
import difflib
import hashlib
import sys
import platform
import time
import struct
import math
import unicodedata
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from .diff_entities import Diff, DiffHunk, DiffType, DiffOperation, create_diff, create_diff_hunk
from .enums import ArtifactType, MismatchType, ConfidenceLevel


class DetectorResult:
    """Result from a mismatch detector."""
    
    def __init__(self, mismatch_type: MismatchType, confidence: float, 
                 diff: Optional[Diff] = None, reasoning: str = "", 
                 metadata: Optional[Dict[str, Any]] = None):
        self.mismatch_type = mismatch_type
        self.confidence = confidence
        self.diff = diff
        self.reasoning = reasoning
        self.metadata = metadata or {}
        self.detected_at = datetime.now(timezone.utc)
    
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence detection."""
        return self.confidence >= 0.8
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """Get confidence level enum."""
        return ConfidenceLevel.from_score(self.confidence)


class MismatchDetector(ABC):
    """Abstract base class for mismatch detectors."""
    
    def __init__(self, name: str, supported_types: List[ArtifactType], version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.supported_types = supported_types
        self.detection_count = 0
        self.call_count = 0
        self.error_count = 0
        self.total_latency_ms = 0
        self.detector_id = f"{name}@{version}"
        self.runtime_info = self._get_runtime_info()
    
    def _get_runtime_info(self) -> Dict[str, str]:
        """Get runtime environment information for provenance."""
        return {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "os": platform.system().lower(),
            "platform": platform.platform(),
        }
    
    @abstractmethod
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect mismatches between source and target content."""
        pass
    
    def supports_type(self, artifact_type: ArtifactType) -> bool:
        """Check if this detector supports the given artifact type."""
        return artifact_type in self.supported_types
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics."""
        avg_latency = self.total_latency_ms / max(1, self.call_count)
        return {
            "name": self.name,
            "detector_id": self.detector_id,
            "call_count": self.call_count,
            "detection_count": self.detection_count,
            "error_count": self.error_count,
            "total_latency_ms": self.total_latency_ms,
            "average_latency_ms": avg_latency,
            "supported_types": [t.value for t in self.supported_types],
            "runtime_info": self.runtime_info
        }


class WhitespaceDetector(MismatchDetector):
    """Detects whitespace-only differences."""
    
    def __init__(self):
        # Restrict to TEXT; whitespace is semantic in many CODE contexts (e.g., Python)
        super().__init__("whitespace_detector", [ArtifactType.TEXT], "1.0.0")
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect whitespace differences."""
        t0 = time.perf_counter()
        self.call_count += 1
        
        try:
            # Normalize whitespace for comparison
            source_normalized = self._normalize_whitespace(source_content)
            target_normalized = self._normalize_whitespace(target_content)
            
            # If normalized versions are identical, it's a whitespace-only difference
            if source_normalized == target_normalized and source_content != target_content:
                diff = self._create_whitespace_diff(source_content, target_content, artifact_type)
                confidence = self._calculate_confidence(source_content, target_content)
                
                reasoning = f"Content identical after whitespace normalization. " \
                           f"Detected {diff.total_changes} whitespace changes."
                
                result = DetectorResult(
                    mismatch_type=MismatchType.WHITESPACE,
                    confidence=confidence,
                    diff=diff,
                    reasoning=reasoning,
                    metadata={
                        "whitespace_changes": diff.total_changes,
                        "normalized_identical": True,
                        "detector_id": self.detector_id,
                        "detector": self.name,
                        "runtime": self.runtime_info
                    }
                )
                result.detector_name = self.name
                
                self.detection_count += 1
                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                return result
            
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            return None
            
        except Exception as e:
            self.error_count += 1
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            raise
    
    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in content."""
        # Normalize internal runs of spaces/tabs; preserve line structure but normalize blank lines
        norm_lines = []
        for line in content.splitlines():
            # Collapse spaces/tabs inside the line; strip trailing spaces only
            inner = re.sub(r'[ \t]+', ' ', line).rstrip()
            norm_lines.append(inner)
        
        # Join and normalize multiple consecutive newlines to single newlines
        result = '\n'.join(norm_lines)
        # Normalize multiple consecutive newlines to single newlines
        result = re.sub(r'\n\s*\n+', '\n', result)
        return result.strip()
    
    def _create_whitespace_diff(self, source: str, target: str, artifact_type: ArtifactType) -> Diff:
        """Create a diff highlighting whitespace changes."""
        diff = create_diff("source", "target", DiffType.FORMATTING, artifact_type)
        
        source_lines = source.splitlines()
        target_lines = target.splitlines()
        
        # Use difflib to find differences
        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
        changes = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                changes += 1
                hunk = create_diff_hunk(
                    operation=DiffOperation.REPLACE if tag == 'replace' else 
                             DiffOperation.DELETE if tag == 'delete' else DiffOperation.INSERT,
                    source_start=i1,
                    source_length=i2 - i1,
                    target_start=j1,
                    target_length=j2 - j1,
                    source_content='\n'.join(source_lines[i1:i2]) if i1 < i2 else "",
                    target_content='\n'.join(target_lines[j1:j2]) if j1 < j2 else ""
                )
                # Add context anchors for safer preview/rollback
                hunk.context_before = '\n'.join(source_lines[max(0, i1-1):i1])[:50]
                hunk.context_after = '\n'.join(source_lines[i2:i2+1])[:50]
                diff.hunks.append(hunk)
        
        diff.total_changes = changes
        diff.lines_added = len(target_lines) - len(source_lines) if len(target_lines) > len(source_lines) else 0
        diff.lines_removed = len(source_lines) - len(target_lines) if len(source_lines) > len(target_lines) else 0
        diff.similarity_score = 1.0 - (changes / max(len(source_lines), len(target_lines), 1))
        
        return diff
    
    def _calculate_confidence(self, source: str, target: str) -> float:
        """Calculate confidence in whitespace detection."""
        # Higher confidence for more obvious whitespace-only changes
        source_chars = len(source)
        target_chars = len(target)
        char_diff = abs(source_chars - target_chars)
        
        # If character difference is small relative to content size, high confidence
        if source_chars > 0:
            char_ratio = char_diff / source_chars
            return max(0.7, 1.0 - char_ratio * 2)
        
        return 0.9


class NewlineDetector(MismatchDetector):
    """Detects newline/EOL differences (CRLF vs LF) and final newline presence."""
    
    def __init__(self):
        super().__init__("newline_detector", [ArtifactType.TEXT, ArtifactType.CODE], "1.0.0")
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect newline format differences."""
        t0 = time.perf_counter()
        self.call_count += 1
        
        try:
            # Normalize CRLF/CR->LF for comparison; preserve content otherwise
            s_norm = source_content.replace("\r\n", "\n").replace("\r", "\n")
            t_norm = target_content.replace("\r\n", "\n").replace("\r", "\n")
            
            if s_norm == t_norm and source_content != target_content:
                # Create a small formatting diff
                diff = create_diff("source", "target", DiffType.FORMATTING, artifact_type)
                hunk = create_diff_hunk(
                    operation=DiffOperation.REPLACE, 
                    source_start=0, 
                    source_length=len(source_content.splitlines()),
                    target_start=0, 
                    target_length=len(target_content.splitlines()),
                    source_content=source_content[:200], 
                    target_content=target_content[:200]
                )
                hunk.metadata = {
                    "change_type": "newline_eol",
                    "source_eol": self._detect_eol(source_content),
                    "target_eol": self._detect_eol(target_content)
                }
                diff.hunks.append(hunk)
                diff.total_changes = 1
                diff.summary = "EOL normalization differences (CRLF/LF or final newline)"
                
                result = DetectorResult(
                    mismatch_type=MismatchType.WHITESPACE,
                    confidence=0.9,
                    diff=diff,
                    reasoning="Content identical after EOL normalization",
                    metadata={
                        "newline_only": True,
                        "detector_id": self.detector_id,
                        "detector": self.name,
                        "runtime": self.runtime_info
                    }
                )
                result.detector_name = self.name
                
                self.detection_count += 1
                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                return result
            
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            return None
            
        except Exception as e:
            self.error_count += 1
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            raise
    
    def _detect_eol(self, content: str) -> str:
        """Detect the primary EOL style in content."""
        crlf_count = content.count('\r\n')
        lf_count = content.count('\n') - crlf_count
        cr_count = content.count('\r') - crlf_count
        
        if crlf_count > max(lf_count, cr_count):
            return "crlf"
        elif cr_count > lf_count:
            return "cr"
        else:
            return "lf"


class JsonStructureDetector(MismatchDetector):
    """Detects JSON ordering and formatting differences."""
    
    def __init__(self):
        super().__init__("json_structure_detector", [ArtifactType.JSON], "1.2.0")
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect JSON structure differences."""
        t0 = time.perf_counter()
        self.call_count += 1
        
        try:
            source_json = json.loads(source_content)
            target_json = json.loads(target_content)
            
            # Canonicalize both JSONs
            source_canonical = self._canonicalize_json(source_json)
            target_canonical = self._canonicalize_json(target_json)
            
            # If canonical versions are identical, it's a structure/ordering difference
            if source_canonical == target_canonical and source_content != target_content:
                diff = self._create_json_diff(source_content, target_content, source_json, target_json)
                confidence = 0.95  # High confidence for JSON structure detection
                
                reasoning = "JSON content identical after canonicalization. " \
                           "Detected ordering or formatting differences."
                
                result = DetectorResult(
                    mismatch_type=MismatchType.JSON_ORDERING,
                    confidence=confidence,
                    diff=diff,
                    reasoning=reasoning,
                    metadata={
                        "canonical_identical": True,
                        "formatting_changes": True,
                        "detector_id": self.detector_id,
                        "detector": self.name,
                        "runtime": self.runtime_info
                    }
                )
                result.detector_name = self.name
                
                self.detection_count += 1
                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                return result
                
        except json.JSONDecodeError:
            # Not valid JSON, can't detect JSON-specific issues
            pass
        
        self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
        return None
    
    def _canonicalize_json(self, obj: Any) -> str:
        """Canonicalize JSON object for comparison (stable keys, stable separators).
        Note: not full RFC 8785 JCS; number form normalization is handled by a separate detector."""
        return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    
    def _create_json_diff(self, source: str, target: str, source_obj: Any, target_obj: Any) -> Diff:
        """Create a diff for JSON structure changes."""
        diff = create_diff("source", "target", DiffType.STRUCTURAL, ArtifactType.JSON)
        
        # Create a single hunk showing the formatting difference
        hunk = create_diff_hunk(
            operation=DiffOperation.REPLACE,
            source_start=0,
            source_length=len(source.splitlines()),
            target_start=0,
            target_length=len(target.splitlines()),
            source_content=source[:200] + "..." if len(source) > 200 else source,
            target_content=target[:200] + "..." if len(target) > 200 else target
        )
        hunk.metadata = {
            "change_type": "json_formatting",
            "canonical_identical": True
        }
        
        diff.hunks.append(hunk)
        diff.total_changes = 1
        diff.similarity_score = 0.95  # High similarity since content is identical
        diff.summary = "JSON formatting or key ordering differences"
        
        return diff


class NumericEpsilonDetector(MismatchDetector):
    """Detects small numerical differences within acceptable tolerance."""
    
    def __init__(self, epsilon: float = 1e-6, rel_epsilon: float = 1e-9):
        super().__init__("numeric_epsilon_detector", [ArtifactType.TEXT, ArtifactType.JSON, ArtifactType.CODE], "1.0.0")
        self.epsilon = epsilon
        self.rel_epsilon = rel_epsilon
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect numeric epsilon differences."""
        t0 = time.perf_counter()
        self.call_count += 1
        
        try:
            # Extract numbers from both contents
            source_numbers = self._extract_numbers(source_content)
            target_numbers = self._extract_numbers(target_content)
        
            if len(source_numbers) != len(target_numbers):
                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                return None
            
            epsilon_diffs = []
            any_nonzero = False
            for i, (src_num, tgt_num) in enumerate(zip(source_numbers, target_numbers)):
                diff = abs(src_num - tgt_num)
                if diff == 0.0:
                    continue
                any_nonzero = True
                rel = diff / max(abs(src_num), abs(tgt_num), 1e-15)
                if diff <= self.epsilon or rel <= self.rel_epsilon:
                    epsilon_diffs.append((i, src_num, tgt_num, diff))
                else:
                    # A material numeric change exists → not benign epsilon
                    self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                    return None
            
            # Classify as epsilon only if all non-zero diffs were within thresholds
            if any_nonzero and epsilon_diffs:
                diff = self._create_numeric_diff(source_content, target_content, epsilon_diffs, artifact_type)
                confidence = self._calculate_numeric_confidence(epsilon_diffs, source_numbers)
                
                reasoning = f"Found {len(epsilon_diffs)} numeric differences within epsilon tolerance " \
                           f"(abs: {self.epsilon}, rel: {self.rel_epsilon}). Max difference: {max(d[3] for d in epsilon_diffs):.2e}"
                
                result = DetectorResult(
                    mismatch_type=MismatchType.NUMERIC_EPSILON,
                    confidence=confidence,
                    diff=diff,
                    reasoning=reasoning,
                    metadata={
                        "epsilon": self.epsilon,
                        "rel_epsilon": self.rel_epsilon,
                        "epsilon_diffs": len(epsilon_diffs),
                        "total_numbers": len(source_numbers),
                        "max_diff": max(d[3] for d in epsilon_diffs) if epsilon_diffs else 0,
                        "detector_id": self.detector_id,
                        "detector": self.name,
                        "runtime": self.runtime_info
                    }
                )
                result.detector_name = self.name
                
                self.detection_count += 1
                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                return result
            
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            return None
            
        except Exception as e:
            self.error_count += 1
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            raise
    
    def _extract_numbers(self, content: str) -> List[float]:
        """Extract all numbers from content."""
        # Regex to find floating point numbers
        number_pattern = r'-?\d+\.?\d*(?:[eE][+-]?\d+)?'
        matches = re.findall(number_pattern, content)
        
        numbers = []
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                continue
        
        return numbers
    
    def _create_numeric_diff(self, source: str, target: str, epsilon_diffs: List[Tuple], 
                           artifact_type: ArtifactType) -> Diff:
        """Create a diff for numeric epsilon changes."""
        diff = create_diff("source", "target", DiffType.NUMERIC, artifact_type)
        
        # Create hunks for each epsilon difference
        for i, src_num, tgt_num, diff_val in epsilon_diffs:
            hunk = create_diff_hunk(
                operation=DiffOperation.REPLACE,
                source_start=i,
                source_length=1,
                target_start=i,
                target_length=1,
                source_content=str(src_num),
                target_content=str(tgt_num)
            )
            hunk.metadata = {
                "numeric_diff": diff_val,
                "within_epsilon": True
            }
            diff.hunks.append(hunk)
        
        diff.total_changes = len(epsilon_diffs)
        diff.similarity_score = 1.0 - (len(epsilon_diffs) * 0.01)  # Small penalty for epsilon diffs
        diff.summary = f"Numeric differences within epsilon tolerance ({len(epsilon_diffs)} changes)"
        
        return diff
    
    def _calculate_numeric_confidence(self, epsilon_diffs: List[Tuple], all_numbers: List[float]) -> float:
        """Calculate confidence in numeric epsilon detection."""
        if not epsilon_diffs or not all_numbers:
            return 0.0
        
        # Higher confidence if more numbers are within epsilon
        ratio = len(epsilon_diffs) / len(all_numbers)
        return min(0.95, 0.7 + ratio * 0.25)


class ULPNumericDetector(MismatchDetector):
    """ULP-aware numeric difference detector for high-precision floating point comparison."""
    
    def __init__(self, max_ulps: int = 8, rel_epsilon: float = 1e-9, abs_epsilon: float = 1e-12):
        super().__init__("numeric_ulp_detector", [ArtifactType.TEXT, ArtifactType.JSON, ArtifactType.CODE], "1.0.0")
        self.max_ulps = max_ulps
        self.rel_epsilon = rel_epsilon
        self.abs_epsilon = abs_epsilon
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect numeric differences using ULP-aware comparison."""
        t0 = time.perf_counter()
        self.call_count += 1
        
        try:
            source_numbers = self._extract_numbers(source_content)
            target_numbers = self._extract_numbers(target_content)
            
            if len(source_numbers) != len(target_numbers):
                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                return None
            
            ulp_diffs = []
            for i, (src_num, tgt_num) in enumerate(zip(source_numbers, target_numbers)):
                if self._nearly_equal_ulp(src_num, tgt_num):
                    ulp_diffs.append((i, src_num, tgt_num, abs(src_num - tgt_num)))
            
            if ulp_diffs and len(ulp_diffs) >= len(source_numbers) * 0.5:
                diff = self._create_ulp_diff(source_content, target_content, ulp_diffs, artifact_type)
                confidence = self._calculate_ulp_confidence(ulp_diffs, source_numbers)
                
                reasoning = f"Found {len(ulp_diffs)} numeric differences within ULP tolerance " \
                           f"(max_ulps={self.max_ulps})"
                
                result = DetectorResult(
                    mismatch_type=MismatchType.NUMERIC_EPSILON,
                    confidence=confidence,
                    diff=diff,
                    reasoning=reasoning,
                    metadata={
                        "ulp_aware": True,
                        "max_ulps": self.max_ulps,
                        "ulp_diffs": len(ulp_diffs),
                        "detector_id": self.detector_id,
                        "detector": self.name,
                        "runtime": self.runtime_info
                    }
                )
                result.detector_name = self.name
                
                self.detection_count += 1
                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                return result
            
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            return None
            
        except Exception as e:
            self.error_count += 1
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            raise
    
    def _nearly_equal_ulp(self, a: float, b: float) -> bool:
        """ULP-aware floating point comparison."""
        if math.isnan(a) or math.isnan(b):
            return False
        if math.isinf(a) or math.isinf(b):
            return a == b
        if a == b:  # Handle exact equality (including 0.0)
            return True
        
        # Fall back to relative/absolute epsilon for very small numbers
        diff = abs(a - b)
        if diff <= self.abs_epsilon:
            return True
        
        if abs(a) > 0:
            rel_diff = diff / abs(a)
            if rel_diff <= self.rel_epsilon:
                return True
        
        # ULP comparison for larger numbers
        try:
            # Convert to 64-bit integers preserving ordering
            ai = struct.unpack('>q', struct.pack('>d', a))[0]
            bi = struct.unpack('>q', struct.pack('>d', b))[0]
            
            # Handle negative numbers
            if ai < 0:
                ai = 0x8000000000000000 - ai
            if bi < 0:
                bi = 0x8000000000000000 - bi
            
            return abs(ai - bi) <= self.max_ulps
        except (struct.error, OverflowError):
            return False
    
    def _extract_numbers(self, content: str) -> List[float]:
        """Extract floating point numbers from content."""
        number_pattern = r'-?\d+\.?\d*(?:[eE][+-]?\d+)?'
        matches = re.findall(number_pattern, content)
        
        numbers = []
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                continue
        
        return numbers
    
    def _create_ulp_diff(self, source: str, target: str, ulp_diffs: List[Tuple], 
                        artifact_type: ArtifactType) -> Diff:
        """Create diff for ULP numeric differences."""
        diff = create_diff("source", "target", DiffType.NUMERIC, artifact_type)
        
        for i, src_num, tgt_num, diff_val in ulp_diffs:
            hunk = create_diff_hunk(
                operation=DiffOperation.REPLACE,
                source_start=i,
                source_length=1,
                target_start=i,
                target_length=1,
                source_content=str(src_num),
                target_content=str(tgt_num)
            )
            hunk.metadata = {
                "numeric_diff": diff_val,
                "ulp_within_tolerance": True
            }
            diff.hunks.append(hunk)
        
        diff.total_changes = len(ulp_diffs)
        diff.similarity_score = 1.0 - (len(ulp_diffs) * 0.005)  # Smaller penalty for ULP diffs
        diff.summary = f"ULP-aware numeric differences ({len(ulp_diffs)} changes)"
        
        return diff
    
    def _calculate_ulp_confidence(self, ulp_diffs: List[Tuple], all_numbers: List[float]) -> float:
        """Calculate confidence in ULP detection."""
        if not ulp_diffs or not all_numbers:
            return 0.0
        
        ratio = len(ulp_diffs) / len(all_numbers)
        return min(0.95, 0.75 + ratio * 0.2)


class MarkdownFormattingDetector(MismatchDetector):
    """Detects markdown formatting differences that don't affect semantic content."""
    
    def __init__(self):
        super().__init__("markdown_formatting_detector", [ArtifactType.TEXT], "1.1.0")
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect markdown formatting differences."""
        t0 = time.perf_counter()
        self.call_count += 1
        
        try:
            # Normalize markdown for semantic comparison
            source_normalized = self._normalize_markdown(source_content)
            target_normalized = self._normalize_markdown(target_content)
            
            # If normalized versions are identical, it's a formatting difference
            if source_normalized == target_normalized and source_content != target_content:
                diff = self._create_markdown_diff(source_content, target_content)
                confidence = self._calculate_markdown_confidence(source_content, target_content)
                
                reasoning = "Markdown content identical after normalization. " \
                           "Detected formatting differences (headers, emphasis, etc.)"
                
                result = DetectorResult(
                    mismatch_type=MismatchType.MARKDOWN_FORMATTING,
                    confidence=confidence,
                    diff=diff,
                    reasoning=reasoning,
                    metadata={
                        "normalized_identical": True,
                        "formatting_only": True,
                        "detector_id": self.detector_id,
                        "detector": self.name,
                        "runtime": self.runtime_info
                    }
                )
                result.detector_name = self.name
                
                self.detection_count += 1
                self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
                return result
            
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            return None
            
        except Exception as e:
            self.error_count += 1
            self.total_latency_ms += int((time.perf_counter() - t0) * 1000)
            raise
    
    def _normalize_markdown(self, content: str) -> str:
        """Normalize markdown content for semantic comparison."""
        # Remove markdown formatting while preserving text content
        normalized = content
        
        # Remove headers (# ## ###)
        normalized = re.sub(r'^#+\s*', '', normalized, flags=re.MULTILINE)
        
        # Remove emphasis (* ** _ __)
        normalized = re.sub(r'\*\*([^*]+)\*\*', r'\1', normalized)
        normalized = re.sub(r'\*([^*]+)\*', r'\1', normalized)
        normalized = re.sub(r'__([^_]+)__', r'\1', normalized)
        normalized = re.sub(r'_([^_]+)_', r'\1', normalized)
        
        # Remove links [text](url) -> text
        normalized = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', normalized)
        
        # Preserve code content by hashing to placeholders so changes in code don't vanish
        def _hash_code(m):
            h = hashlib.sha256(m.group(1).encode("utf-8")).hexdigest()[:8]
            return f" CODEBLOCK:{h} "
        normalized = re.sub(r"```[\w\-]*\n(.*?)```", lambda m: _hash_code(m), normalized, flags=re.DOTALL)
        normalized = re.sub(r"`([^`]+)`", lambda m: f" CODE:{hashlib.sha256(m.group(1).encode('utf-8')).hexdigest()[:8]} ", normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    def _create_markdown_diff(self, source: str, target: str) -> Diff:
        """Create a diff for markdown formatting changes."""
        diff = create_diff("source", "target", DiffType.FORMATTING, ArtifactType.TEXT)
        
        source_lines = source.splitlines()
        target_lines = target.splitlines()
        
        # Find formatting differences
        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
        changes = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                changes += 1
                hunk = create_diff_hunk(
                    operation=DiffOperation.REPLACE if tag == 'replace' else 
                             DiffOperation.DELETE if tag == 'delete' else DiffOperation.INSERT,
                    source_start=i1,
                    source_length=i2 - i1,
                    target_start=j1,
                    target_length=j2 - j1,
                    source_content='\n'.join(source_lines[i1:i2]) if i1 < i2 else "",
                    target_content='\n'.join(target_lines[j1:j2]) if j1 < j2 else ""
                )
                hunk.metadata = {"change_type": "markdown_formatting"}
                diff.hunks.append(hunk)
        
        diff.total_changes = changes
        diff.similarity_score = 0.9  # High similarity for formatting-only changes
        diff.summary = f"Markdown formatting differences ({changes} changes)"
        
        return diff
    
    def _calculate_markdown_confidence(self, source: str, target: str) -> float:
        """Calculate confidence in markdown formatting detection."""
        # Look for markdown-specific patterns
        markdown_patterns = [r'#+\s', r'\*\*.*\*\*', r'_.*_', r'\[.*\]\(.*\)', r'```']
        
        source_markdown_count = sum(len(re.findall(pattern, source)) for pattern in markdown_patterns)
        target_markdown_count = sum(len(re.findall(pattern, target)) for pattern in markdown_patterns)
        
        # Higher confidence if there are markdown patterns
        total_patterns = source_markdown_count + target_markdown_count
        if total_patterns > 0:
            return min(0.95, 0.8 + (total_patterns * 0.02))
        
        return 0.7


class DetectorRegistry:
    """Registry for managing mismatch detectors."""
    
    def __init__(self):
        self.detectors: List[MismatchDetector] = []
        self._register_default_detectors()
    
    def _register_default_detectors(self):
        """Register default detectors."""
        # Precedence: very cheap (newline) → whitespace → JSON → numeric → markdown
        self.register(NewlineDetector())
        self.register(WhitespaceDetector())
        self.register(JsonStructureDetector())
        self.register(NumericEpsilonDetector())
        self.register(ULPNumericDetector())
        self.register(MarkdownFormattingDetector())
    
    def register(self, detector: MismatchDetector):
        """Register a new detector."""
        self.detectors.append(detector)
    
    def get_detectors_for_type(self, artifact_type: ArtifactType) -> List[MismatchDetector]:
        """Get all detectors that support the given artifact type."""
        return [d for d in self.detectors if d.supports_type(artifact_type)]
    
    def detect_all(self, source_content: str, target_content: str, 
                   artifact_type: ArtifactType, **kwargs) -> List[DetectorResult]:
        """Run all applicable detectors and return results."""
        results: List[DetectorResult] = []
        precedence = {
            # lower number = higher precedence when confidences tie
            "newline_detector": 0,
            "whitespace_detector": 1,
            "json_structure_detector": 2,
            "numeric_epsilon_detector": 3,
            "numeric_ulp_detector": 4,
            "markdown_formatting_detector": 5,
        }
        
        for detector in self.get_detectors_for_type(artifact_type):
            try:
                detector.call_count += 1
                result = detector.detect(source_content, target_content, artifact_type, **kwargs)
                if result:
                    results.append(result)
            except Exception as e:
                # Log error but continue with other detectors
                detector.error_count += 1
                print(f"Detector {detector.name} failed: {e}")
        
        # Sort by (confidence desc, precedence asc)
        results.sort(key=lambda r: (-r.confidence, precedence.get(getattr(r, "detector_name", "unknown"), 99)))
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all detectors."""
        return {
            "total_detectors": len(self.detectors),
            "detectors": [d.get_stats() for d in self.detectors]
        }


# Global detector registry instance
detector_registry = DetectorRegistry()


if __name__ == "__main__":
    # Test detectors
    print("🧪 Testing mismatch detectors...")
    
    # Test whitespace detector
    source = "Hello,   world!\n  \n"
    target = "Hello, world!\n"
    
    results = detector_registry.detect_all(source, target, ArtifactType.TEXT)
    if results:
        result = results[0]
        print(f"✅ Detected {result.mismatch_type.value} with confidence {result.confidence:.2f}")
        print(f"   Reasoning: {result.reasoning}")
    
    # Test JSON detector
    json_source = '{"b": 2, "a": 1}'
    json_target = '{\n  "a": 1,\n  "b": 2\n}'
    
    results = detector_registry.detect_all(json_source, json_target, ArtifactType.JSON)
    if results:
        result = results[0]
        print(f"✅ Detected {result.mismatch_type.value} with confidence {result.confidence:.2f}")
    
    print(f"\n📊 Registry stats: {detector_registry.get_stats()['total_detectors']} detectors registered")
    print("\n🎉 All detectors working correctly!")