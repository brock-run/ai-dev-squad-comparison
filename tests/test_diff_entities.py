"""Tests for diff entities based on task2.md feedback."""

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
    assert best.confidence == 0.99  # Should be the exact match result
    assert e.get_average_similarity() > 0.4
    e.complete(success=True)
    assert e.status == EvaluationStatus.COMPLETED
    assert e.is_successful() is True


def test_diff_signature_generation():
    """Test diff signature for caching/deduplication."""
    d1 = create_diff("art_1", "art_2", DiffType.TEXTUAL, ArtifactType.TEXT)
    d1.total_changes = 5
    d1.similarity_score = 0.85
    
    d2 = create_diff("art_1", "art_2", DiffType.TEXTUAL, ArtifactType.TEXT)
    d2.total_changes = 5
    d2.similarity_score = 0.85
    
    # Same diffs should have same signature
    assert d1.get_signature() == d2.get_signature()
    
    # Different diffs should have different signatures
    d2.total_changes = 10
    assert d1.get_signature() != d2.get_signature()


def test_diff_significance_detection():
    """Test diff significance detection."""
    # Significant diff
    d1 = create_diff("art_1", "art_2", DiffType.TEXTUAL, ArtifactType.TEXT)
    d1.similarity_score = 0.5  # 50% similarity
    d1.total_changes = 10
    assert d1.is_significant(threshold=0.1) is True
    
    # Insignificant diff
    d2 = create_diff("art_1", "art_2", DiffType.FORMATTING, ArtifactType.TEXT)
    d2.similarity_score = 0.98  # 98% similarity
    d2.total_changes = 1
    assert d2.is_significant(threshold=0.1) is False


def test_evaluation_consensus_calculation():
    """Test evaluation consensus calculation with multiple results."""
    e = create_evaluation("diff_123", "art_src", "art_tgt", ArtifactType.TEXT)
    
    # Add multiple results with different outcomes
    e.add_result(EvaluationResult(
        method=EquivalenceMethod.EXACT,
        equivalent=False,
        confidence=0.95,
        similarity_score=0.0,
        reasoning="exact match failed"
    ))
    
    e.add_result(EvaluationResult(
        method=EquivalenceMethod.COSINE_SIMILARITY,
        equivalent=True,
        confidence=0.8,
        similarity_score=0.9,
        reasoning="high semantic similarity"
    ))
    
    e.add_result(EvaluationResult(
        method=EquivalenceMethod.LLM_RUBRIC_JUDGE,
        equivalent=True,
        confidence=0.7,
        similarity_score=0.85,
        reasoning="LLM judge says equivalent"
    ))
    
    # Consensus should be weighted by confidence
    # False (0.95) vs True (0.8) + True (0.7) = 0.95 vs 1.5
    # So consensus should be True with confidence based on majority
    assert e.consensus_result is True
    assert e.consensus_confidence > 0.5


def test_evaluation_cost_and_latency_tracking():
    """Test that evaluation tracks cost and latency correctly."""
    e = create_evaluation("diff_123", "art_src", "art_tgt", ArtifactType.TEXT)
    
    # Add results with costs and latencies
    e.add_result(EvaluationResult(
        method=EquivalenceMethod.EXACT,
        equivalent=False,
        confidence=0.95,
        similarity_score=0.0,
        reasoning="exact match",
        cost=0.001,
        latency_ms=10
    ))
    
    e.add_result(EvaluationResult(
        method=EquivalenceMethod.COSINE_SIMILARITY,
        equivalent=True,
        confidence=0.8,
        similarity_score=0.9,
        reasoning="embedding similarity",
        cost=0.005,
        latency_ms=50
    ))
    
    # Total cost and latency should be summed
    assert e.total_cost == 0.006
    assert e.total_latency_ms == 60


def test_diff_change_density_calculation():
    """Test diff change density calculation."""
    d = create_diff("art_1", "art_2", DiffType.TEXTUAL, ArtifactType.TEXT)
    
    # Add some hunks
    from common.phase2.diff_entities import create_diff_hunk, DiffOperation
    
    hunk1 = create_diff_hunk(DiffOperation.REPLACE, 0, 1, 0, 1, "old", "new")
    hunk2 = create_diff_hunk(DiffOperation.INSERT, 1, 0, 1, 1, "", "inserted")
    
    d.hunks = [hunk1, hunk2]
    d.total_changes = 5
    
    # Change density should be total_changes / num_hunks
    assert d.get_change_density() == 2.5  # 5 changes / 2 hunks


def test_evaluation_error_handling():
    """Test evaluation error handling and completion."""
    e = create_evaluation("diff_123", "art_src", "art_tgt", ArtifactType.TEXT)
    
    # Test successful completion
    e.complete(success=True)
    assert e.is_complete()
    assert e.is_successful()
    assert e.error_message is None
    
    # Test failed completion
    e2 = create_evaluation("diff_456", "art_src", "art_tgt", ArtifactType.TEXT)
    e2.complete(success=False, error_message="Test error")
    assert e2.is_complete()
    assert not e2.is_successful()
    assert e2.error_message == "Test error"