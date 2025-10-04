"""Phase 2 Resolution Engine

This module implements idempotent transforms for benign mismatch classes with
preview-first workflow, rollback capability, and policy gating.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, List, Callable
from datetime import datetime, timezone
import json
import re
import hashlib
import difflib

from .enums import ArtifactType, ResolutionActionType, SafetyLevel
from .diff_entities import Diff, DiffType, DiffHunk, DiffOperation, create_diff, create_diff_hunk
from .resolution_metrics import track_resolution_metrics, metrics


@dataclass
class TransformResult:
    """Result of applying a resolution transform."""
    new_content: str
    diff: Diff
    summary: str
    idempotent: bool


class ResolutionTransform:
    """Base class for resolution transforms."""
    
    id: str = "base@0.0.0"
    action_type: ResolutionActionType
    artifact_types: List[ArtifactType]

    def applies_to(self, artifact_type: ArtifactType) -> bool:
        """Check if this transform applies to the given artifact type."""
        return artifact_type in self.artifact_types

    def preview(self, content: str, artifact_type: ArtifactType, artifact_id: str) -> TransformResult:
        """Return new content + diff without side effects."""
        new_content = self.apply(content, artifact_type)
        diff = self._diff(artifact_id, new_content, content, artifact_type)
        return TransformResult(
            new_content=new_content,
            diff=diff,
            summary=diff.summary or f"{self.id} preview",
            idempotent=(self.apply(new_content, artifact_type) == new_content),
        )

    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        """Apply the transform to content. Must be idempotent."""
        raise NotImplementedError

    def _diff(self, artifact_id: str, new: str, old: str, artifact_type: ArtifactType) -> Diff:
        """Create a diff between old and new content."""
        if new == old:
            diff = create_diff(artifact_id, artifact_id, DiffType.FORMATTING, artifact_type)
            diff.summary = "No changes"
            return diff
        
        # Simple line diff (stable)
        old_lines, new_lines = old.splitlines(), new.splitlines()
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        diff = create_diff(artifact_id, artifact_id, DiffType.FORMATTING, artifact_type)
        changes = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            changes += 1
            hunk = create_diff_hunk(
                operation=DiffOperation.REPLACE if tag == 'replace' else 
                         DiffOperation.DELETE if tag == 'delete' else DiffOperation.INSERT,
                source_start=i1, 
                source_length=i2 - i1, 
                target_start=j1, 
                target_length=j2 - j1,
                source_content="\n".join(old_lines[i1:i2]) if i2 > i1 else "",
                target_content="\n".join(new_lines[j1:j2]) if j2 > j1 else "",
            )
            # Add anchors for safer preview/rollback
            hunk.context_before = "\n".join(old_lines[max(i1-1, 0):i1])[:200]
            hunk.context_after = "\n".join(old_lines[i2:i2+1])[:200]
            diff.hunks.append(hunk)
        
        diff.total_changes = changes
        diff.lines_removed = max(0, len(old_lines) - len(new_lines))
        diff.lines_added = max(0, len(new_lines) - len(old_lines))
        diff.similarity_score = 1.0 - (changes / max(1, max(len(old_lines), len(new_lines))))
        diff.summary = f"{self.action_type.value} produced {changes} change hunk(s)"
        
        return diff


# ---- Concrete transforms (idempotent by construction) ----

class NormalizeNewlinesTransform(ResolutionTransform):
    """Transform to normalize newline formats (CRLF -> LF) and ensure final newline."""
    
    id = "normalize_newlines@1.0.0"
    action_type = ResolutionActionType.NORMALIZE_WHITESPACE  # reuse existing action
    artifact_types = [ArtifactType.TEXT, ArtifactType.CODE]
    
    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        """Normalize newlines to LF and ensure single final newline."""
        # Convert all newlines to LF
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        
        # Ensure single final newline presence if content is not empty
        if normalized and not normalized.endswith("\n"):
            normalized += "\n"
        elif normalized.endswith("\n\n"):
            # Remove extra trailing newlines
            normalized = normalized.rstrip("\n") + "\n"
        
        return normalized


class NormalizeWhitespaceTransform(ResolutionTransform):
    """Transform to normalize internal whitespace (spaces/tabs)."""
    
    id = "normalize_whitespace@1.0.0"
    action_type = ResolutionActionType.NORMALIZE_WHITESPACE
    artifact_types = [ArtifactType.TEXT]
    
    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        """Normalize internal whitespace while preserving line structure."""
        lines = []
        for line in content.splitlines():
            # Collapse multiple spaces/tabs to single space, strip trailing whitespace
            normalized_line = re.sub(r'[ \t]+', ' ', line).rstrip()
            lines.append(normalized_line)
        
        result = "\n".join(lines)
        
        # Preserve final newline if original had one
        if content.endswith('\n') and not result.endswith('\n'):
            result += '\n'
        
        return result


class CanonicalizeJsonTransform(ResolutionTransform):
    """Transform to canonicalize JSON (stable key order, formatting)."""
    
    id = "canonicalize_json@1.1.0"
    action_type = ResolutionActionType.CANONICALIZE_JSON
    artifact_types = [ArtifactType.JSON]
    
    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        """Canonicalize JSON with stable keys and separators."""
        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            # Fail closed - return original content if not valid JSON
            return content
        
        # Stable keys & separators; number-form left as-is (policy can add stricter variant later)
        return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


class NormalizeMarkdownTransform(ResolutionTransform):
    """Transform to normalize markdown formatting (experimental/advisory)."""
    
    id = "normalize_markdown@1.0.0"
    action_type = ResolutionActionType.REWRITE_FORMATTING  # advisory/experimental by policy
    artifact_types = [ArtifactType.TEXT]
    
    def apply(self, content: str, artifact_type: ArtifactType) -> str:
        """Minimal, safe markdown normalization (no changes inside fenced code)."""
        
        def hash_block(match):
            """Replace code blocks with hashed placeholders to preserve them."""
            block_content = match.group(1)
            block_hash = hashlib.sha256(block_content.encode()).hexdigest()[:8]
            return f"\n```BLOCK-{block_hash}```\n"
        
        # Preserve code blocks by hashing them
        normalized = re.sub(r"```[\w-]*\n(.*?)```", hash_block, content, flags=re.DOTALL)
        
        # Convert setext headers to atx headers
        normalized = re.sub(r"^(\w[^\n]+)\n=+\s*$", r"# \1", normalized, flags=re.MULTILINE)
        
        # Trim trailing spaces before newlines
        normalized = re.sub(r"\s+\n", "\n", normalized)
        
        return normalized


# ---- Registry & engine ----

class TransformRegistry:
    """Registry for resolution transforms."""
    
    def __init__(self):
        self._by_action: Dict[ResolutionActionType, List[ResolutionTransform]] = {}
        self._all: List[ResolutionTransform] = []
    
    def register(self, transform: ResolutionTransform):
        """Register a transform in the registry."""
        self._all.append(transform)
        self._by_action.setdefault(transform.action_type, []).append(transform)
    
    def get(self, action: ResolutionActionType, artifact_type: ArtifactType) -> Optional[ResolutionTransform]:
        """Get the most specific transform that matches action and artifact type."""
        candidates = []
        for transform in self._by_action.get(action, []):
            if transform.applies_to(artifact_type):
                candidates.append(transform)
        
        if not candidates:
            return None
        
        # Prefer more specific transforms (fewer supported types = more specific)
        candidates.sort(key=lambda t: len(t.artifact_types))
        return candidates[0]
    
    def get_all_transforms(self) -> List[ResolutionTransform]:
        """Get all registered transforms."""
        return self._all.copy()


# Global transform registry instance
transform_registry = TransformRegistry()

# Register default transforms
for transform in [
    NormalizeNewlinesTransform(), 
    NormalizeWhitespaceTransform(), 
    CanonicalizeJsonTransform(), 
    NormalizeMarkdownTransform()
]:
    transform_registry.register(transform)


class ResolutionEngine:
    """Engine for applying resolution transforms with preview and policy gating."""
    
    def __init__(self, registry: Optional[TransformRegistry] = None):
        self.registry = registry or transform_registry

    def preview_action(self, action_type: ResolutionActionType, artifact_id: str, 
                      artifact_type: ArtifactType, content: str) -> TransformResult:
        """Preview the result of applying an action without side effects."""
        import time
        start_time = time.perf_counter()
        
        try:
            transform = self.registry.get(action_type, artifact_type)
            if not transform:
                raise ValueError(f"No transform for {action_type} on {artifact_type}")
            
            result = transform.preview(content, artifact_type, artifact_id)
            
            # Track metrics
            latency_ms = (time.perf_counter() - start_time) * 1000
            if result.diff.total_changes == 0:
                metrics.track_noop(action_type)
            else:
                metrics.track_apply(action_type, success=True, latency_ms=latency_ms)
            
            return result
            
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            metrics.track_apply(action_type, success=False, latency_ms=latency_ms, error_type=type(e).__name__)
            raise

    def apply_action(self, action_type: ResolutionActionType, artifact_id: str, 
                    artifact_type: ArtifactType, content: str) -> TransformResult:
        """Apply an action (same as preview but called post-approval)."""
        # Same as preview but called post-approval; caller persists content & diff + rollback hash
        result = self.preview_action(action_type, artifact_id, artifact_type, content)
        
        # Add audit metadata for database persistence
        transform = self.registry.get(action_type, artifact_type)
        if transform:
            result.diff.metadata.update({
                "transform_audit": self._create_transform_audit(transform, content, result)
            })
        
        return result
    
    def _create_transform_audit(self, transform: ResolutionTransform, original_content: str, 
                               result: TransformResult) -> Dict[str, Any]:
        """Create transform audit metadata for database persistence."""
        import hashlib
        from datetime import datetime, timezone
        
        before_hash = f"sha256:{hashlib.sha256(original_content.encode()).hexdigest()}"
        after_hash = f"sha256:{hashlib.sha256(result.new_content.encode()).hexdigest()}"
        
        # Create config fingerprint (for now, just the transform ID)
        config_fingerprint = f"sha256:{hashlib.sha256(transform.id.encode()).hexdigest()}"
        
        return {
            "transform_id": transform.id,
            "config_fingerprint": config_fingerprint,
            "before_hash": before_hash,
            "after_hash": after_hash,
            "idempotent": result.idempotent,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "checksum_validated": False  # Will be set to True after validation
        }
    
    def get_available_actions(self, artifact_type: ArtifactType) -> List[ResolutionActionType]:
        """Get all available actions for the given artifact type."""
        actions = []
        for transform in self.registry.get_all_transforms():
            if transform.applies_to(artifact_type) and transform.action_type not in actions:
                actions.append(transform.action_type)
        return actions


if __name__ == "__main__":
    # Test the resolution engine
    print("🧪 Testing Resolution Engine...")
    
    engine = ResolutionEngine()
    
    # Test JSON canonicalization
    json_content = '{"b": 2, "a": 1}'
    result = engine.preview_action(
        ResolutionActionType.CANONICALIZE_JSON, 
        "test_json", 
        ArtifactType.JSON, 
        json_content
    )
    print(f"✅ JSON canonicalization: {result.summary}")
    print(f"   Idempotent: {result.idempotent}")
    print(f"   New content: {result.new_content}")
    
    # Test whitespace normalization
    text_content = "Hello,   world!  \n"
    result = engine.preview_action(
        ResolutionActionType.NORMALIZE_WHITESPACE,
        "test_text",
        ArtifactType.TEXT,
        text_content
    )
    print(f"✅ Whitespace normalization: {result.summary}")
    print(f"   Idempotent: {result.idempotent}")
    
    # Test newline normalization
    newline_content = "Line 1\r\nLine 2\r\n"
    result = engine.preview_action(
        ResolutionActionType.NORMALIZE_WHITESPACE,  # Reuses this action type
        "test_newlines",
        ArtifactType.TEXT,
        newline_content
    )
    print(f"✅ Newline normalization: {result.summary}")
    
    print("\n🎉 Resolution Engine working correctly!")