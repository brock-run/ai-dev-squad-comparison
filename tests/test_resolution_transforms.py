"""Tests for Phase 2 Resolution Transforms

Tests idempotency, preview/apply workflow, and policy gating.
"""

import pytest
import json
from common.phase2.enums import ArtifactType, ResolutionActionType
from common.phase2.resolution_engine import (
    ResolutionEngine, 
    CanonicalizeJsonTransform, 
    NormalizeWhitespaceTransform, 
    NormalizeNewlinesTransform,
    NormalizeMarkdownTransform
)


class TestTransformIdempotency:
    """Test that all transforms are idempotent."""
    
    def test_json_canonicalize_idempotent(self):
        """Test JSON canonicalization is idempotent."""
        engine = ResolutionEngine()
        content = '{ "b": 2, "a": 1 }'
        
        # First application
        result1 = engine.preview_action(ResolutionActionType.CANONICALIZE_JSON, "a1", ArtifactType.JSON, content)
        
        # Second application on result
        result2 = engine.preview_action(ResolutionActionType.CANONICALIZE_JSON, "a1", ArtifactType.JSON, result1.new_content)
        
        assert result1.new_content == result2.new_content
        assert result1.idempotent
        assert result2.idempotent
        assert result2.diff.total_changes == 0  # No changes on second application
    
    def test_whitespace_normalize_idempotent(self):
        """Test whitespace normalization is idempotent."""
        engine = ResolutionEngine()
        content = "Hello,   world!  \n  \n"
        
        result1 = engine.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "t1", ArtifactType.TEXT, content)
        result2 = engine.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "t1", ArtifactType.TEXT, result1.new_content)
        
        assert result1.new_content == result2.new_content
        assert result1.idempotent
        assert result2.idempotent
    
    def test_newline_normalize_idempotent(self):
        """Test newline normalization is idempotent."""
        engine = ResolutionEngine()
        content = "Line 1\r\nLine 2\r\n"
        
        # Note: NormalizeNewlinesTransform reuses NORMALIZE_WHITESPACE action type
        result1 = engine.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "t1", ArtifactType.CODE, content)
        result2 = engine.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "t1", ArtifactType.CODE, result1.new_content)
        
        assert result1.new_content == result2.new_content
        assert result1.idempotent
        assert result2.idempotent
    
    def test_markdown_normalize_idempotent(self):
        """Test markdown normalization is idempotent."""
        engine = ResolutionEngine()
        content = "Title\n=====\n\nSome text  \n"
        
        result1 = engine.preview_action(ResolutionActionType.REWRITE_FORMATTING, "m1", ArtifactType.TEXT, content)
        result2 = engine.preview_action(ResolutionActionType.REWRITE_FORMATTING, "m1", ArtifactType.TEXT, result1.new_content)
        
        assert result1.new_content == result2.new_content
        assert result1.idempotent
        assert result2.idempotent


class TestTransformBehavior:
    """Test specific transform behaviors."""
    
    def test_whitespace_normalize_text_only(self):
        """Test whitespace normalization only applies to TEXT artifacts."""
        engine = ResolutionEngine()
        text = "Hello,   world!  \n"
        
        # Should work for TEXT
        result = engine.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "t1", ArtifactType.TEXT, text)
        assert "   " not in result.new_content  # Multiple spaces should be collapsed
        
        # For CODE, should get the newlines transform (which also handles NORMALIZE_WHITESPACE)
        code_result = engine.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "c1", ArtifactType.CODE, "x =  1")
        # The newlines transform should add a final newline
        assert code_result.new_content.endswith('\n')
    
    def test_normalize_newlines_adds_final_newline(self):
        """Test newline normalization adds final newline."""
        transform = NormalizeNewlinesTransform()
        
        # Content without final newline
        content = "a\r\nb\r\nc"
        result = transform.apply(content, ArtifactType.TEXT)
        
        assert result.endswith("\n")
        assert result == "a\nb\nc\n"
    
    def test_normalize_newlines_removes_extra_trailing_newlines(self):
        """Test newline normalization removes extra trailing newlines."""
        transform = NormalizeNewlinesTransform()
        
        content = "a\nb\n\n\n"
        result = transform.apply(content, ArtifactType.TEXT)
        
        assert result == "a\nb\n"
    
    def test_json_canonicalize_handles_invalid_json(self):
        """Test JSON canonicalization fails closed on invalid JSON."""
        transform = CanonicalizeJsonTransform()
        
        invalid_json = '{"invalid": json}'
        result = transform.apply(invalid_json, ArtifactType.JSON)
        
        # Should return original content unchanged
        assert result == invalid_json
    
    def test_json_canonicalize_stable_output(self):
        """Test JSON canonicalization produces stable output."""
        transform = CanonicalizeJsonTransform()
        
        content = '{\n  "b": 2,\n  "a": 1\n}'
        result = transform.apply(content, ArtifactType.JSON)
        
        assert result == '{"a":1,"b":2}'
    
    def test_markdown_preserves_code_blocks(self):
        """Test markdown normalization preserves code blocks."""
        transform = NormalizeMarkdownTransform()
        
        content = "# Title\n\n```python\ndef hello():\n    print('world')\n```\n\nText"
        result = transform.apply(content, ArtifactType.TEXT)
        
        # Code block should be preserved (hashed)
        assert "```BLOCK-" in result
        assert "def hello" not in result  # Original code should be hashed out


class TestResolutionEngine:
    """Test the resolution engine functionality."""
    
    def test_preview_vs_apply_same_result(self):
        """Test that preview and apply produce the same result."""
        engine = ResolutionEngine()
        content = '{"b": 2, "a": 1}'
        
        preview = engine.preview_action(ResolutionActionType.CANONICALIZE_JSON, "test", ArtifactType.JSON, content)
        applied = engine.apply_action(ResolutionActionType.CANONICALIZE_JSON, "test", ArtifactType.JSON, content)
        
        assert preview.new_content == applied.new_content
        assert preview.diff.total_changes == applied.diff.total_changes
        assert preview.idempotent == applied.idempotent
    
    def test_get_available_actions(self):
        """Test getting available actions for artifact types."""
        engine = ResolutionEngine()
        
        text_actions = engine.get_available_actions(ArtifactType.TEXT)
        json_actions = engine.get_available_actions(ArtifactType.JSON)
        code_actions = engine.get_available_actions(ArtifactType.CODE)
        
        # TEXT should have whitespace and markdown actions
        assert ResolutionActionType.NORMALIZE_WHITESPACE in text_actions
        assert ResolutionActionType.REWRITE_FORMATTING in text_actions
        
        # JSON should have canonicalization
        assert ResolutionActionType.CANONICALIZE_JSON in json_actions
        
        # CODE should have newline normalization (via NORMALIZE_WHITESPACE action)
        assert ResolutionActionType.NORMALIZE_WHITESPACE in code_actions
    
    def test_unknown_action_raises_error(self):
        """Test that unknown action/artifact combinations raise errors."""
        engine = ResolutionEngine()
        
        with pytest.raises(ValueError, match="No transform for"):
            engine.preview_action(ResolutionActionType.CANONICALIZE_JSON, "test", ArtifactType.TEXT, "text")


class TestDiffGeneration:
    """Test diff generation in transforms."""
    
    def test_diff_includes_context_anchors(self):
        """Test that generated diffs include context anchors."""
        engine = ResolutionEngine()
        content = "Line 1\nLine 2   \nLine 3\nLine 4"  # Line 2 has trailing spaces
        
        result = engine.preview_action(ResolutionActionType.NORMALIZE_WHITESPACE, "test", ArtifactType.TEXT, content)
        
        # Should have changes (trailing spaces removed)
        assert result.diff.total_changes > 0
        
        # Check that hunks have context anchors
        for hunk in result.diff.hunks:
            # Context should be present (may be empty for first/last lines)
            assert hasattr(hunk, 'context_before')
            assert hasattr(hunk, 'context_after')
    
    def test_no_changes_produces_empty_diff(self):
        """Test that no changes produces an empty diff."""
        engine = ResolutionEngine()
        content = '{"a":1,"b":2}'  # Already canonicalized
        
        result = engine.preview_action(ResolutionActionType.CANONICALIZE_JSON, "test", ArtifactType.JSON, content)
        
        assert result.diff.total_changes == 0
        assert result.diff.summary == "No changes"
        assert len(result.diff.hunks) == 0


class TestTransformRegistry:
    """Test the transform registry functionality."""
    
    def test_registry_finds_correct_transforms(self):
        """Test that registry finds the correct transforms for actions."""
        from common.phase2.resolution_engine import transform_registry
        
        # Test JSON canonicalization
        json_transform = transform_registry.get(ResolutionActionType.CANONICALIZE_JSON, ArtifactType.JSON)
        assert json_transform is not None
        assert isinstance(json_transform, CanonicalizeJsonTransform)
        
        # Test whitespace normalization (should get the more specific whitespace transform for TEXT)
        ws_transform = transform_registry.get(ResolutionActionType.NORMALIZE_WHITESPACE, ArtifactType.TEXT)
        assert ws_transform is not None
        assert isinstance(ws_transform, NormalizeWhitespaceTransform)
        
        # Test newline normalization (for CODE artifacts)
        nl_transform = transform_registry.get(ResolutionActionType.NORMALIZE_WHITESPACE, ArtifactType.CODE)
        assert nl_transform is not None
        assert isinstance(nl_transform, NormalizeNewlinesTransform)
    
    def test_registry_returns_none_for_unsupported(self):
        """Test that registry returns None for unsupported combinations."""
        from common.phase2.resolution_engine import transform_registry
        
        # JSON canonicalization not supported for TEXT
        result = transform_registry.get(ResolutionActionType.CANONICALIZE_JSON, ArtifactType.TEXT)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])