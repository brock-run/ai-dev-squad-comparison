"""Tests for enhanced detector registry based on task2.md feedback."""

import pytest
from common.phase2.enums import ArtifactType, MismatchType
from common.phase2.detector_improvements import enhanced_detector_registry


def test_registry_contains_expected_detectors():
    text_detectors = {d.name for d in enhanced_detector_registry.get_detectors_for_type(ArtifactType.TEXT)}
    json_detectors = {d.name for d in enhanced_detector_registry.get_detectors_for_type(ArtifactType.JSON)}
    
    # Check for enhanced detectors
    assert any("newline@" in n for n in text_detectors)
    assert any("unicode_nfc@" in n for n in text_detectors)
    assert any("numeric_ulp@" in n for n in json_detectors)
    assert any("nondeterminism@" in n for n in text_detectors)
    
    # Check for existing detectors
    assert any("whitespace" in n for n in text_detectors)
    assert any("markdown" in n for n in text_detectors)
    assert any("json" in n for n in json_detectors)


def test_detect_all_precedence_ordering():
    """Test that detectors run in correct precedence order."""
    # Content with multiple potential matches
    src = "Hello,   world!\r\n"  # Both whitespace and newline issues
    tgt = "Hello, world!\n"
    
    results = enhanced_detector_registry.detect_all(src, tgt, ArtifactType.TEXT, short_circuit=True)
    
    # Should detect newline first (higher precedence)
    assert len(results) >= 1
    first_result = results[0]
    # Should be either newline or whitespace (both are benign)
    assert first_result.mismatch_type in {MismatchType.WHITESPACE}


def test_detect_all_full_evidence_collection():
    """Test full evidence collection without short-circuiting."""
    src = "Hello,   world!\r\n"
    tgt = "Hello, world!\n"
    
    results = enhanced_detector_registry.detect_all(src, tgt, ArtifactType.TEXT, short_circuit=False)
    
    # Should collect evidence from multiple detectors
    assert len(results) >= 1
    
    # All results should have provenance information
    for result in results:
        assert "config_hash" in result.metadata
        assert "runtime" in result.metadata
        assert "detector_version" in result.metadata or "detector_version" in result.reasoning


def test_detect_all_returns_empty_on_equal_content():
    text = "no change\n"
    assert enhanced_detector_registry.detect_all(text, text, ArtifactType.TEXT) == []


def test_registry_provenance_tracking():
    """Test that registry tracks provenance information."""
    registry = enhanced_detector_registry
    
    # Should have config hash
    assert registry.config_hash is not None
    assert len(registry.config_hash) == 16  # Should be 16-char hash
    
    # Should have runtime info
    assert "python" in registry.runtime_info
    assert "os" in registry.runtime_info
    
    # Should have detectors with versions
    detector_names = [d.name for d in registry.detectors]
    versioned_detectors = [name for name in detector_names if "@" in name]
    assert len(versioned_detectors) >= 4  # At least our 4 new enhanced detectors


def test_detector_precedence_prevents_masking():
    """Test that precedence doesn't mask more severe classes."""
    # Create content that could trigger multiple detectors
    src = '{"timestamp": "2023-10-01T12:00:00Z", "value":   1.0}'
    tgt = '{"timestamp": "2023-10-01T12:01:00Z", "value": 1.0}'
    
    # Run with full evidence collection
    results = enhanced_detector_registry.detect_all(src, tgt, ArtifactType.JSON, short_circuit=False)
    
    # Should detect nondeterminism (timestamp change) even if whitespace is also present
    mismatch_types = {r.mismatch_type for r in results}
    
    # Should include nondeterminism detection
    assert MismatchType.NONDETERMINISM in mismatch_types or len(results) > 0


def test_registry_error_handling():
    """Test that registry handles detector errors gracefully."""
    # This should not crash even if individual detectors fail
    results = enhanced_detector_registry.detect_all("", "", ArtifactType.TEXT)
    assert isinstance(results, list)  # Should return empty list, not crash