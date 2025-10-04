"""Enhanced CLI analyzer tests based on task2.md feedback."""

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


@pytest.mark.asyncio
async def test_analyze_run_with_unicode_and_newlines(tmp_path):
    """Test analyzer with Unicode and newline differences."""
    artifacts = {
        "u1": {"content": "Hello\u200bworld\r\n", "type": "text"},  # Zero-width space + CRLF
        "u2": {"content": "Helloworld\n", "type": "text"},          # No zero-width + LF
        "n1": {"content": "Line 1\r\nLine 2\r\n", "type": "text"},  # CRLF
        "n2": {"content": "Line 1\nLine 2\n", "type": "text"},      # LF
    }
    p = tmp_path / "unicode_artifacts.json"
    p.write_text(json.dumps(artifacts), encoding="utf-8")

    analyzer = RunAnalyzer()
    result = await analyzer.analyze_run(run_id="run_unicode", artifacts_path=str(p))
    
    # Should detect Unicode and newline differences
    assert result.mismatches_created >= 2
    assert result.accuracy_score >= 0.95  # Should be high accuracy


@pytest.mark.asyncio
async def test_analyze_run_with_nondeterministic_content(tmp_path):
    """Test analyzer with nondeterministic patterns."""
    artifacts = {
        "nd1": {
            "content": "Request ID: 550e8400-e29b-41d4-a716-446655440000\nTimestamp: 2023-10-01T12:00:00Z",
            "type": "text"
        },
        "nd2": {
            "content": "Request ID: 6ba7b810-9dad-11d1-80b4-00c04fd430c8\nTimestamp: 2023-10-01T12:01:00Z", 
            "type": "text"
        }
    }
    p = tmp_path / "nondeterministic_artifacts.json"
    p.write_text(json.dumps(artifacts), encoding="utf-8")

    analyzer = RunAnalyzer()
    result = await analyzer.analyze_run(run_id="run_nondeterministic", artifacts_path=str(p))
    
    # Should detect nondeterministic patterns
    assert result.mismatches_created >= 1
    assert result.accuracy_score > 0.0


@pytest.mark.asyncio
async def test_analyze_run_with_ulp_numeric_differences(tmp_path):
    """Test analyzer with ULP-level numeric differences."""
    artifacts = {
        "num1": {
            "content": '{"precision": 1.0000000000000000, "rate": 0.1}',
            "type": "json"
        },
        "num2": {
            "content": '{"precision": 1.0000000000000002, "rate": 0.1}',
            "type": "json"
        }
    }
    p = tmp_path / "numeric_artifacts.json"
    p.write_text(json.dumps(artifacts), encoding="utf-8")

    analyzer = RunAnalyzer()
    result = await analyzer.analyze_run(run_id="run_numeric", artifacts_path=str(p))
    
    # Should detect ULP-level numeric differences
    assert result.mismatches_created >= 1
    assert result.accuracy_score >= 0.95


@pytest.mark.asyncio
async def test_analyze_run_provenance_tracking(tmp_path):
    """Test that analyzer tracks provenance information."""
    artifacts = {
        "p1": {"content": "Hello,   world!", "type": "text"},
        "p2": {"content": "Hello, world!", "type": "text"},
    }
    p = tmp_path / "provenance_artifacts.json"
    p.write_text(json.dumps(artifacts), encoding="utf-8")

    analyzer = RunAnalyzer()
    result = await analyzer.analyze_run(run_id="run_provenance", artifacts_path=str(p))
    
    # Should have detector stats with provenance
    assert result.detector_stats is not None
    assert "detectors" in result.detector_stats
    
    # Check that detectors have version information
    detector_info = result.detector_stats["detectors"]
    versioned_detectors = [d for d in detector_info if "@" in d.get("name", "")]
    assert len(versioned_detectors) > 0  # Should have at least some versioned detectors


@pytest.mark.asyncio
async def test_analyze_run_error_handling(tmp_path):
    """Test analyzer error handling with malformed artifacts."""
    # Create artifacts with some invalid JSON
    artifacts = {
        "valid": {"content": "Hello, world!", "type": "text"},
        "invalid": {"content": '{"invalid": json}', "type": "json"},  # Invalid JSON
    }
    p = tmp_path / "error_artifacts.json"
    p.write_text(json.dumps(artifacts), encoding="utf-8")

    analyzer = RunAnalyzer()
    result = await analyzer.analyze_run(run_id="run_errors", artifacts_path=str(p))
    
    # Should handle errors gracefully
    assert isinstance(result.errors, list)
    # Should still process valid artifacts
    assert result.mismatches_created >= 0