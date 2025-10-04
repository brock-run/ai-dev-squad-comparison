"""Unit tests for Phase 2 detectors based on task2.md feedback."""

import pytest

from common.phase2.enums import ArtifactType, MismatchType
from common.phase2.detectors import (
    WhitespaceDetector,
    JsonStructureDetector,
    NumericEpsilonDetector,
    MarkdownFormattingDetector,
)
from common.phase2.detector_improvements import (
    NewlineDetector,
    UnicodeNormalizationDetector,
    ULPNumericDetector,
    NondeterminismDetector,
)


class TestWhitespaceDetector:
    def test_whitespace_only_difference(self):
        d = WhitespaceDetector()
        src = "Hello,   world!\n  \n"
        tgt = "Hello, world!\n"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert res.mismatch_type == MismatchType.WHITESPACE
        assert res.confidence >= 0.7
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
        assert res.confidence >= 0.7

    def test_markdown_semantic_change_not_flagged_as_formatting(self):
        d = MarkdownFormattingDetector()
        src = "Fee is $10 per user per month."
        tgt = "Fee is $10 per organization per month."
        res = d.detect(src, tgt, ArtifactType.TEXT)
        # Detector should not claim benign formatting when semantics changed
        assert res is None or res.mismatch_type != MismatchType.MARKDOWN_FORMATTING


class TestNewlineDetector:
    def test_crlf_vs_lf_difference(self):
        d = NewlineDetector()
        src = "Hello, world!\r\n"
        tgt = "Hello, world!\n"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert res.mismatch_type == MismatchType.WHITESPACE
        assert res.confidence >= 0.9
        assert res.metadata["newline_differences"] is True

    def test_no_newline_difference(self):
        d = NewlineDetector()
        text = "Hello, world!\n"
        assert d.detect(text, text, ArtifactType.TEXT) is None


class TestUnicodeNormalizationDetector:
    def test_zero_width_characters(self):
        d = UnicodeNormalizationDetector()
        src = "Hello\u200bworld"  # Zero-width space
        tgt = "Helloworld"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert res.mismatch_type == MismatchType.WHITESPACE
        assert "zero_width" in res.metadata["unicode_flags"]

    def test_nbsp_detection(self):
        d = UnicodeNormalizationDetector()
        src = "Hello\u00a0world"  # Non-breaking space
        tgt = "Hello world"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert "nbsp" in res.metadata["unicode_flags"]


class TestULPNumericDetector:
    def test_ulp_numeric_difference(self):
        d = ULPNumericDetector(max_ulps=8)
        # Numbers that are close in ULP terms
        src = "Value: 1.0000000000000000"
        tgt = "Value: 1.0000000000000002"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert res.mismatch_type == MismatchType.NUMERIC_EPSILON
        assert res.confidence >= 0.7

    def test_large_numeric_difference_not_ulp(self):
        d = ULPNumericDetector()
        src = "Value: 1.0"
        tgt = "Value: 2.0"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is None  # Should not detect large differences as ULP


class TestNondeterminismDetector:
    def test_uuid_differences(self):
        d = NondeterminismDetector()
        src = "Request ID: 550e8400-e29b-41d4-a716-446655440000"
        tgt = "Request ID: 6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert res.mismatch_type == MismatchType.NONDETERMINISM
        assert "uuid" in res.metadata["patterns_detected"]

    def test_timestamp_differences(self):
        d = NondeterminismDetector()
        src = "Created: 2023-10-01T12:00:00Z"
        tgt = "Created: 2023-10-01T12:01:00Z"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert res.mismatch_type == MismatchType.NONDETERMINISM
        assert "iso8601" in res.metadata["patterns_detected"]

    def test_no_nondeterministic_patterns(self):
        d = NondeterminismDetector()
        src = "Static content here"
        tgt = "Static content here"
        assert d.detect(src, tgt, ArtifactType.TEXT) is None


class TestDetectorVersioning:
    def test_detector_has_version_info(self):
        d = NewlineDetector()
        assert "@" in d.name  # Should have version like "newline@1.0.0"
        
        src = "Hello\r\n"
        tgt = "Hello\n"
        res = d.detect(src, tgt, ArtifactType.TEXT)
        assert res is not None
        assert "detector_version" in res.metadata

    def test_ulp_detector_versioning(self):
        d = ULPNumericDetector()
        assert d.name == "numeric_ulp@1.0.0"
        assert hasattr(d, 'config')
        assert 'ulps' in d.config