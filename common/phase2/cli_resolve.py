"""CLI interface for Phase 2 Resolution Engine

Provides preview/approve/apply workflow for resolution transforms.
"""

import click
import hashlib
from pathlib import Path

from .resolution_engine import ResolutionEngine
from .enums import ResolutionActionType, ArtifactType
from .config import create_default_config, Environment


@click.command()
@click.argument("artifact_id")
@click.option("--action", type=click.Choice([a.value for a in ResolutionActionType]), required=True)
@click.option("--atype", "artifact_type", type=click.Choice([a.value for a in ArtifactType]), required=True)
@click.option("--input-path", required=True, help="Path to artifact content file")
@click.option("--apply", is_flag=True, help="Apply after preview if policy allows")
@click.option("--output-path", help="Output path for resolved content (default: input-path.resolved)")
def resolve(artifact_id, action, artifact_type, input_path, apply, output_path):
    """Preview or apply resolution transforms to artifacts."""
    
    # Load configuration
    cfg = create_default_config(Environment.DEVELOPMENT)
    engine = ResolutionEngine()
    
    # Read input content
    input_file = Path(input_path)
    if not input_file.exists():
        raise click.ClickException(f"Input file not found: {input_path}")
    
    content = input_file.read_text(encoding="utf-8")
    atype = ArtifactType(artifact_type)
    act = ResolutionActionType(action)
    
    # Policy gate (basic check - adapt to your policy API)
    # TODO: Integrate with actual policy system when available
    # For now, allow all actions in development environment
    if hasattr(cfg, "is_action_allowed") and cfg.environment != Environment.DEVELOPMENT:
        if not cfg.is_action_allowed(mismatch_type=None, action=act):
            raise click.ClickException(f"Action {act.value} not allowed by policy")
    
    try:
        # Preview the transformation
        preview = engine.preview_action(act, artifact_id, atype, content)
        
        click.echo(f"🔍 Preview: {preview.summary}")
        click.echo(f"📊 Idempotent: {preview.idempotent}")
        click.echo(f"📝 Diff hunks: {len(preview.diff.hunks)}")
        click.echo(f"📈 Similarity score: {preview.diff.similarity_score:.3f}")
        
        if preview.diff.hunks:
            click.echo("\n📋 Changes:")
            for i, hunk in enumerate(preview.diff.hunks[:3]):  # Show first 3 hunks
                click.echo(f"  Hunk {i+1}: {hunk.operation.value} at lines {hunk.source_start}-{hunk.source_start + hunk.source_length}")
                if hunk.source_content and len(hunk.source_content) < 100:
                    click.echo(f"    - {repr(hunk.source_content)}")
                if hunk.target_content and len(hunk.target_content) < 100:
                    click.echo(f"    + {repr(hunk.target_content)}")
            
            if len(preview.diff.hunks) > 3:
                click.echo(f"  ... and {len(preview.diff.hunks) - 3} more hunks")
        
        if apply:
            # Apply the transformation
            click.echo("\n🔧 Applying transformation...")
            
            # Here you'd also require approvals per SafetyLevel before persist
            applied = engine.apply_action(act, artifact_id, atype, content)
            
            # Determine output path
            if not output_path:
                output_path = str(input_file.with_suffix(input_file.suffix + ".resolved"))
            
            # Write resolved content
            output_file = Path(output_path)
            output_file.write_text(applied.new_content, encoding="utf-8")
            
            # Calculate hashes for rollback
            before_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            after_hash = hashlib.sha256(applied.new_content.encode()).hexdigest()[:16]
            
            click.echo(f"✅ Applied. Wrote {output_path}")
            click.echo(f"📋 Before hash: {before_hash}")
            click.echo(f"📋 After hash: {after_hash}")
            click.echo(f"🔄 Transform: {act.value} ({applied.summary})")
            
            # Store rollback info (in real implementation, this would go to database)
            from datetime import datetime, timezone
            rollback_info = {
                "artifact_id": artifact_id,
                "transform_id": f"{act.value}@1.0.0",
                "before_hash": before_hash,
                "after_hash": after_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "input_path": str(input_path),
                "output_path": str(output_path)
            }
            
            rollback_file = output_file.with_suffix(".rollback.json")
            import json
            rollback_file.write_text(json.dumps(rollback_info, indent=2), encoding="utf-8")
            click.echo(f"💾 Rollback info saved to {rollback_file}")
        
        else:
            click.echo("\n💡 Use --apply to execute the transformation")
    
    except ValueError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Unexpected error: {e}")


@click.command()
@click.argument("artifact_type", type=click.Choice([a.value for a in ArtifactType]))
def list_actions(artifact_type):
    """List available resolution actions for an artifact type."""
    
    engine = ResolutionEngine()
    atype = ArtifactType(artifact_type)
    actions = engine.get_available_actions(atype)
    
    click.echo(f"📋 Available actions for {artifact_type}:")
    for action in actions:
        click.echo(f"  • {action.value}")
    
    if not actions:
        click.echo("  (no actions available)")


@click.group()
def cli():
    """Phase 2 Resolution CLI - Preview and apply resolution transforms."""
    pass


cli.add_command(resolve)
cli.add_command(list_actions)


if __name__ == "__main__":
    cli()