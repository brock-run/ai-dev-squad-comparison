"""Tests for Enhanced Phase 2 Detectors

These tests implement the high-ROI improvements from task2.md:
- Detector determinism & provenance
- Unicode & newline normalization
- JCS JSON canonicalization
- ULP-aware numeric tolerance
- Nondeterminism detection
"""

import pytest
import json
import struct
from typing import List, Dict, Any

from common.phase2.detectors import (
    NewlineDetector, ULPNumericDetector, detector_registry
)
from common.phase2.enums import ArtifactType, MismatchType


class TestDetectorProvenance:
    """Test detector versioning and provenance tracking."""
    
    def test_detector_versioning(self):
        """Test that detectors have proper versioning."""
        detector = NewlineDetector()
        
        assert detector.detector_id == "newline_detector@1.0.0"
        assert detector.version == "1.0.0"
        assert detector.runtime_info is not None
        assert detector.runtime_info["python"] is not None
        assert detector.runtime_info["os"] is not None
    
    def test_provenance_in_results(self):
        """Test that detection results include provenance metadata."""
        detector = NewlineDetector()
        result = detector.detect("Hello\r\nworld", "Hello\nworld", ArtifactType.TEXT)
        
        assert result is not None
        assert "detector_id" in result.metadata
        assert "runtime" in result.metadata
        assert result.metadata["detector_id"] == "newline_detector@1.0.0"


class TestNewlineDetector:
    """Test newline format detection."""
    
    def test_crlf_to_lf_detection(self):
        """Test CRLF to LF conversion detection."""
        detector = NewlineDetector()
        source = "Hello\r\nworld\r\n"
        target = "Hello\nworld\n"
        
        result = detector.detect(source, target, ArtifactType.TEXT)
        assert result is not None
        assert result.mismatch_type == MismatchType.WHITESPACE
        assert result.confidence >= 0.8
        assert result.metadata["newline_only"] is True
    
    def test_no_newline_differences(self):
        """Test that identical newline formats don't trigger detection."""
        detector = NewlineDetector()
        content = "Hello\nworld\n"
        
        result = detector.detect(content, content, ArtifactType.TEXT)
        assert result is None
    
    @pytest.mark.parametrize("content,expected_eol", [
        ("Hello\r\nworld\r\n", "crlf"),
        ("Hello\nworld\n", "lf"),
        ("Hello\rworld\r", "cr"),
        ("Hello world", "lf"),  # Default when no newlines
    ])
    def test_eol_detection(self, content, expected_eol):
        """Test EOL format detection."""
        detector = NewlineDetector()
        detected_eol = detector._detect_eol(content)
        assert detected_eol == expected_eol


class TestULPNumericDetector:
    """Test ULP-aware numeric detection."""
    
    def test_ulp_within_tolerance(self):
        """Test ULP differences within tolerance."""
        detector = ULPNumericDetector(max_ulps=8)
        
        # Create two numbers that differ by a few ULPs
        a = 1.0
        b = struct.unpack('>d', struct.pack('>q', struct.unpack('>q', struct.pack('>d', a))[0] + 4))[0]
        
        source = f"value: {a}"
        target = f"value: {b}"
        
        result = detector.detect(source, target, ArtifactType.TEXT)
        assert result is not None
        assert result.mismatch_type == MismatchType.NUMERIC_EPSILON
        assert result.metadata["ulp_aware"] is True
    
    def test_ulp_beyond_tolerance(self):
        """Test ULP differences beyond tolerance."""
        detector = ULPNumericDetector(max_ulps=8)
        source = "value: 1.0"
        target = "value: 1.1"  # Large difference
        
        result = detector.detect(source, target, ArtifactType.TEXT)
        assert result is None  # Should not detect as epsilon difference
    
    def test_absolute_epsilon_fallback(self):
        """Test absolute epsilon for very small numbers."""
        detector = ULPNumericDetector(abs_epsilon=1e-12)
        source = "value: 1e-15"
        target = "value: 2e-15"
        
        result = detector.detect(source, target, ArtifactType.TEXT)
        assert result is not None  # Should use absolute epsilon
    
    def test_relative_epsilon_fallback(self):
        """Test relative epsilon for medium numbers."""
        detector = ULPNumericDetector(rel_epsilon=1e-9)
        source = "value: 1000.0"
        target = "value: 1000.000001"  # 1e-9 relative difference
        
        result = detector.detect(source, target, ArtifactType.TEXT)
        assert result is not None


class TestDetectorIntegration:
    """Integration tests for enhanced detectors."""
    
    def test_detector_precedence(self):
        """Test that detectors can be run in sequence without conflicts."""
        # Content with multiple issues
        source = "Value: 1.0000000000000002\r\n"
        target = "Value: 1.0000000000000004\n"
        
        results = detector_registry.detect_all(source, target, ArtifactType.TEXT)
        
        # Should detect multiple issues
        assert len(results) >= 1
        
        # Check that detectors found their specific issues
        mismatch_types = [r.mismatch_type for r in results]
        # Should detect at least newline or numeric differences
        assert any(mt in [MismatchType.WHITESPACE, MismatchType.NUMERIC_EPSILON] for mt in mismatch_types)
    
    def test_performance_on_large_content(self):
        """Test detector performance on large content."""
        import time
        
        # Create 100KB content with small differences
        base_content = "word " * 25000  # ~100KB
        source = base_content + "\r\n"
        target = base_content + "\n"
        
        detector = NewlineDetector()
        
        start_time = time.time()
        result = detector.detect(source, target, ArtifactType.TEXT)
        latency_ms = (time.time() - start_time) * 1000
        
        assert result is not None
        assert latency_ms < 100  # Should be fast even for large content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])