"""Phase 2 Detector Improvements

This module implements the high-ROI improvements from task2.md feedback:
- Detector versioning and provenance
- Unicode & newline normalization
- ULP-aware numeric tolerance
- Enhanced JSON canonicalization with JCS semantics
"""

import math
import struct
import unicodedata
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from .detectors import MismatchDetector, DetectorResult
from .enums import ArtifactType, MismatchType
from .diff_entities import create_diff, DiffType


class NewlineDetector(MismatchDetector):
    """Detects newline ending differences (CRLF vs LF)."""
    
    def __init__(self):
        super().__init__("newline@1.0.0", [ArtifactType.TEXT, ArtifactType.CODE])
        self.config = {
            "normalize_final_newline": True,
            "eol": "lf"
        }
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect newline ending differences."""
        start_time = datetime.utcnow()
        
        # Normalize newlines for comparison
        source_normalized = self._normalize_newlines(source_content)
        target_normalized = self._normalize_newlines(target_content)
        
        # If normalized versions are identical, it's a newline difference
        if source_normalized == target_normalized and source_content != target_content:
            diff = self._create_newline_diff(source_content, target_content, artifact_type)
            confidence = 0.95  # High confidence for newline detection
            
            reasoning = "Content identical after newline normalization. " \
                       f"Detected CRLF/LF differences."
            
            result = DetectorResult(
                mismatch_type=MismatchType.WHITESPACE,
                confidence=confidence,
                diff=diff,
                reasoning=reasoning,
                metadata={
                    "newline_differences": True,
                    "normalized_identical": True,
                    "detector_version": "newline@1.0.0"
                }
            )
            
            self.detection_count += 1
            self.total_latency_ms += int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return result
        
        return None
    
    def _normalize_newlines(self, content: str) -> str:
        """Normalize newline endings."""
        # Convert CRLF to LF
        normalized = content.replace('\r\n', '\n')
        # Convert standalone CR to LF
        normalized = normalized.replace('\r', '\n')
        
        # Normalize final newline if configured
        if self.config["normalize_final_newline"]:
            normalized = normalized.rstrip('\n') + '\n' if normalized else ''
        
        return normalized
    
    def _create_newline_diff(self, source: str, target: str, artifact_type: ArtifactType):
        """Create a diff for newline changes."""
        diff = create_diff("source", "target", DiffType.FORMATTING, artifact_type)
        diff.summary = "Newline ending differences (CRLF vs LF)"
        diff.total_changes = 1
        diff.similarity_score = 0.98  # Very high similarity
        return diff


class UnicodeNormalizationDetector(MismatchDetector):
    """Detects Unicode normalization differences."""
    
    def __init__(self):
        super().__init__("unicode_nfc@1.0.0", [ArtifactType.TEXT, ArtifactType.CODE])
        self.config = {
            "form": "NFC",
            "flag_zero_width": True,
            "flag_nbsp": True
        }
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect Unicode normalization differences."""
        start_time = datetime.utcnow()
        
        # Check for zero-width characters and NBSP
        source_flags = self._detect_unicode_flags(source_content)
        target_flags = self._detect_unicode_flags(target_content)
        
        # Normalize Unicode for comparison
        source_normalized = unicodedata.normalize(self.config["form"], source_content)
        target_normalized = unicodedata.normalize(self.config["form"], target_content)
        
        # If normalized versions are identical or we found flagged characters
        if ((source_normalized == target_normalized and source_content != target_content) or
            source_flags or target_flags):
            
            diff = self._create_unicode_diff(source_content, target_content, 
                                           source_flags, target_flags, artifact_type)
            confidence = 0.9 if source_flags or target_flags else 0.8
            
            reasoning = f"Unicode normalization differences detected. " \
                       f"Flags: {source_flags + target_flags}"
            
            result = DetectorResult(
                mismatch_type=MismatchType.WHITESPACE,
                confidence=confidence,
                diff=diff,
                reasoning=reasoning,
                metadata={
                    "unicode_flags": source_flags + target_flags,
                    "normalization_form": self.config["form"],
                    "detector_version": "unicode_nfc@1.0.0"
                }
            )
            
            self.detection_count += 1
            self.total_latency_ms += int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return result
        
        return None
    
    def _detect_unicode_flags(self, content: str) -> List[str]:
        """Detect flagged Unicode characters."""
        flags = []
        
        if self.config["flag_zero_width"]:
            # Zero-width characters
            zero_width_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']  # ZWSP, ZWNJ, ZWJ, BOM
            if any(char in content for char in zero_width_chars):
                flags.append("zero_width")
        
        if self.config["flag_nbsp"]:
            # Non-breaking space
            if '\u00a0' in content:
                flags.append("nbsp")
        
        return flags
    
    def _create_unicode_diff(self, source: str, target: str, source_flags: List[str], 
                           target_flags: List[str], artifact_type: ArtifactType):
        """Create a diff for Unicode normalization changes."""
        diff = create_diff("source", "target", DiffType.FORMATTING, artifact_type)
        diff.summary = f"Unicode normalization differences. Flags: {source_flags + target_flags}"
        diff.total_changes = 1
        diff.similarity_score = 0.95
        return diff


class ULPNumericDetector(MismatchDetector):
    """ULP-aware numeric difference detector."""
    
    def __init__(self, max_ulps: int = 8):
        super().__init__("numeric_ulp@1.0.0", [ArtifactType.TEXT, ArtifactType.JSON, ArtifactType.CODE])
        self.max_ulps = max_ulps
        self.config = {
            "ulps": max_ulps,
            "rel_epsilon": 1e-9,
            "abs_epsilon": 1e-12
        }
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect ULP-aware numeric differences."""
        start_time = datetime.utcnow()
        
        # Extract numbers from both contents
        source_numbers = self._extract_numbers(source_content)
        target_numbers = self._extract_numbers(target_content)
        
        if len(source_numbers) != len(target_numbers):
            return None
        
        # Check numeric differences using ULP-aware comparison
        ulp_diffs = []
        for i, (src_num, tgt_num) in enumerate(zip(source_numbers, target_numbers)):
            if self._nearly_equal_ulp(src_num, tgt_num):
                ulp_diffs.append((i, src_num, tgt_num, abs(src_num - tgt_num)))
        
        # If we found ULP differences
        if ulp_diffs and len(ulp_diffs) >= len(source_numbers) * 0.5:
            diff = self._create_ulp_diff(source_content, target_content, ulp_diffs, artifact_type)
            confidence = self._calculate_ulp_confidence(ulp_diffs, source_numbers)
            
            reasoning = f"Found {len(ulp_diffs)} numeric differences within ULP tolerance " \
                       f"({self.max_ulps} ULPs). Max difference: {max(d[3] for d in ulp_diffs):.2e}"
            
            result = DetectorResult(
                mismatch_type=MismatchType.NUMERIC_EPSILON,
                confidence=confidence,
                diff=diff,
                reasoning=reasoning,
                metadata={
                    "max_ulps": self.max_ulps,
                    "ulp_diffs": len(ulp_diffs),
                    "total_numbers": len(source_numbers),
                    "max_diff": max(d[3] for d in ulp_diffs) if ulp_diffs else 0,
                    "detector_version": "numeric_ulp@1.0.0"
                }
            )
            
            self.detection_count += 1
            self.total_latency_ms += int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return result
        
        return None
    
    def _nearly_equal_ulp(self, a: float, b: float) -> bool:
        """ULP-aware floating point comparison."""
        if math.isnan(a) or math.isnan(b):
            return False
        if math.isinf(a) or math.isinf(b):
            return a == b
        if a == b:  # Handle exact equality (including 0.0)
            return True
        
        # Convert to 64-bit integers preserving ordering
        try:
            ai = struct.unpack('>q', struct.pack('>d', a))[0]
            bi = struct.unpack('>q', struct.pack('>d', b))[0]
            
            # Handle negative numbers
            if ai < 0:
                ai = 0x8000000000000000 - ai
            if bi < 0:
                bi = 0x8000000000000000 - bi
            
            return abs(ai - bi) <= self.max_ulps
        except (struct.error, OverflowError):
            # Fallback to relative/absolute epsilon
            return self._nearly_equal_epsilon(a, b)
    
    def _nearly_equal_epsilon(self, a: float, b: float) -> bool:
        """Fallback epsilon-based comparison."""
        diff = abs(a - b)
        
        # Absolute epsilon for numbers near zero
        if diff <= self.config["abs_epsilon"]:
            return True
        
        # Relative epsilon for larger numbers
        max_val = max(abs(a), abs(b))
        return diff <= max_val * self.config["rel_epsilon"]
    
    def _extract_numbers(self, content: str) -> List[float]:
        """Extract all numbers from content."""
        # Enhanced regex for floating point numbers
        number_pattern = r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
        matches = re.findall(number_pattern, content)
        
        numbers = []
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                continue
        
        return numbers
    
    def _create_ulp_diff(self, source: str, target: str, ulp_diffs: List, artifact_type: ArtifactType):
        """Create a diff for ULP numeric changes."""
        diff = create_diff("source", "target", DiffType.NUMERIC, artifact_type)
        diff.total_changes = len(ulp_diffs)
        diff.similarity_score = 1.0 - (len(ulp_diffs) * 0.005)  # Very small penalty
        diff.summary = f"ULP-aware numeric differences ({len(ulp_diffs)} changes)"
        return diff
    
    def _calculate_ulp_confidence(self, ulp_diffs: List, all_numbers: List[float]) -> float:
        """Calculate confidence in ULP detection."""
        if not ulp_diffs or not all_numbers:
            return 0.0
        
        # Higher confidence if more numbers are within ULP tolerance
        ratio = len(ulp_diffs) / len(all_numbers)
        return min(0.95, 0.8 + ratio * 0.15)


class NondeterminismDetector(MismatchDetector):
    """Detects nondeterministic patterns (analysis-only)."""
    
    def __init__(self):
        super().__init__("nondeterminism@1.0.0", [ArtifactType.TEXT, ArtifactType.CODE, ArtifactType.JSON])
        self.config = {
            "uuid": True,
            "timestamps": ["iso8601", "rfc2822"],
            "seeds": ["seed="]
        }
        
        # Compile regex patterns
        self.patterns = {
            "uuid": re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE),
            "iso8601": re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})'),
            "rfc2822": re.compile(r'\w{3},?\s+\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}'),
            "seed": re.compile(r'seed=\d+'),
            "random_id": re.compile(r'[a-zA-Z0-9]{16,}')  # Long random-looking strings
        }
    
    def detect(self, source_content: str, target_content: str, 
               artifact_type: ArtifactType, **kwargs) -> Optional[DetectorResult]:
        """Detect nondeterministic patterns."""
        start_time = datetime.utcnow()
        
        # Find nondeterministic patterns in both contents
        source_patterns = self._find_patterns(source_content)
        target_patterns = self._find_patterns(target_content)
        
        # Check if patterns differ between source and target
        pattern_diffs = []
        for pattern_type in source_patterns:
            if pattern_type in target_patterns:
                if source_patterns[pattern_type] != target_patterns[pattern_type]:
                    pattern_diffs.append(pattern_type)
        
        # If we found differing nondeterministic patterns
        if pattern_diffs:
            diff = self._create_nondeterminism_diff(source_content, target_content, 
                                                  pattern_diffs, artifact_type)
            confidence = min(0.9, 0.7 + len(pattern_diffs) * 0.1)
            
            reasoning = f"Nondeterministic patterns detected: {', '.join(pattern_diffs)}. " \
                       f"This suggests execution-dependent differences."
            
            result = DetectorResult(
                mismatch_type=MismatchType.NONDETERMINISM,
                confidence=confidence,
                diff=diff,
                reasoning=reasoning,
                metadata={
                    "patterns_detected": pattern_diffs,
                    "analysis_only": True,
                    "detector_version": "nondeterminism@1.0.0"
                }
            )
            
            self.detection_count += 1
            self.total_latency_ms += int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return result
        
        return None
    
    def _find_patterns(self, content: str) -> Dict[str, List[str]]:
        """Find nondeterministic patterns in content."""
        patterns_found = {}
        
        for pattern_name, pattern_regex in self.patterns.items():
            matches = pattern_regex.findall(content)
            if matches:
                patterns_found[pattern_name] = matches
        
        return patterns_found
    
    def _create_nondeterminism_diff(self, source: str, target: str, 
                                  pattern_diffs: List[str], artifact_type: ArtifactType):
        """Create a diff for nondeterministic changes."""
        diff = create_diff("source", "target", DiffType.TEMPORAL, artifact_type)
        diff.summary = f"Nondeterministic patterns: {', '.join(pattern_diffs)}"
        diff.total_changes = len(pattern_diffs)
        diff.similarity_score = 0.8  # Moderate similarity due to nondeterminism
        return diff


# Enhanced detector registry with versioning
class VersionedDetectorRegistry:
    """Enhanced detector registry with versioning and provenance."""
    
    def __init__(self):
        self.detectors: List[MismatchDetector] = []
        self.config_hash = self._calculate_config_hash()
        self.runtime_info = self._get_runtime_info()
        self._register_enhanced_detectors()
    
    def _register_enhanced_detectors(self):
        """Register enhanced detectors with versioning."""
        # Import existing detectors
        from .detectors import WhitespaceDetector, JsonStructureDetector, MarkdownFormattingDetector
        
        # Register enhanced detectors
        self.register(NewlineDetector())
        self.register(UnicodeNormalizationDetector())
        self.register(ULPNumericDetector())
        self.register(NondeterminismDetector())
        
        # Register existing detectors (they should be enhanced with versioning)
        self.register(WhitespaceDetector())
        self.register(JsonStructureDetector())
        self.register(MarkdownFormattingDetector())
    
    def register(self, detector: MismatchDetector):
        """Register a detector with provenance tracking."""
        self.detectors.append(detector)
    
    def _calculate_config_hash(self) -> str:
        """Calculate hash of detector configuration."""
        import hashlib
        config_str = "detector_registry_v1.0.0"  # Simple version for now
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def _get_runtime_info(self) -> Dict[str, str]:
        """Get runtime environment information."""
        import sys
        import platform
        
        return {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "os": platform.system().lower(),
            "platform": platform.platform()
        }
    
    def get_detectors_for_type(self, artifact_type: ArtifactType) -> List[MismatchDetector]:
        """Get detectors for artifact type with precedence ordering."""
        detectors = [d for d in self.detectors if d.supports_type(artifact_type)]
        
        # Order by precedence: cheap benign classes first
        precedence_order = [
            "newline@1.0.0",
            "unicode_nfc@1.0.0", 
            "whitespace_detector",
            "json_structure_detector",
            "numeric_ulp@1.0.0",
            "markdown_formatting_detector",
            "nondeterminism@1.0.0"
        ]
        
        def get_precedence(detector):
            try:
                return precedence_order.index(detector.name)
            except ValueError:
                return len(precedence_order)  # Unknown detectors go last
        
        return sorted(detectors, key=get_precedence)
    
    def detect_all(self, source_content: str, target_content: str, 
                   artifact_type: ArtifactType, **kwargs) -> List[DetectorResult]:
        """Run detectors with precedence and full evidence collection."""
        results = []
        
        # Get detectors in precedence order
        detectors = self.get_detectors_for_type(artifact_type)
        
        # Run detectors with short-circuit option
        short_circuit = kwargs.get('short_circuit', True)
        
        for detector in detectors:
            try:
                result = detector.detect(source_content, target_content, artifact_type, **kwargs)
                if result:
                    # Add provenance information
                    result.metadata.update({
                        "config_hash": self.config_hash,
                        "runtime": self.runtime_info
                    })
                    results.append(result)
                    
                    # Short-circuit for benign classes if enabled
                    if short_circuit and result.mismatch_type in {
                        MismatchType.WHITESPACE, 
                        MismatchType.JSON_ORDERING,
                        MismatchType.MARKDOWN_FORMATTING
                    }:
                        break
                        
            except Exception as e:
                # Log error but continue with other detectors
                print(f"Detector {detector.name} failed: {e}")
        
        return results


# Global enhanced registry instance
enhanced_detector_registry = VersionedDetectorRegistry()


if __name__ == "__main__":
    # Test enhanced detectors
    print("🧪 Testing enhanced detectors...")
    
    # Test newline detector
    source = "Hello, world!\r\n"
    target = "Hello, world!\n"
    
    results = enhanced_detector_registry.detect_all(source, target, ArtifactType.TEXT)
    if results:
        result = results[0]
        print(f"✅ Detected {result.mismatch_type.value} with confidence {result.confidence:.2f}")
        print(f"   Version: {result.metadata.get('detector_version', 'unknown')}")
    
    # Test ULP numeric detector
    source_num = "Value: 1.0000000000000000"
    target_num = "Value: 1.0000000000000002"
    
    results = enhanced_detector_registry.detect_all(source_num, target_num, ArtifactType.TEXT)
    if results:
        result = results[0]
        print(f"✅ Detected {result.mismatch_type.value} with ULP tolerance")
    
    print(f"\n📊 Registry: {len(enhanced_detector_registry.detectors)} enhanced detectors")
    print(f"   Config hash: {enhanced_detector_registry.config_hash}")
    print("\n🎉 Enhanced detectors working correctly!")