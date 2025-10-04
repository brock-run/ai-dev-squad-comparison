"""Interactive CLI for Phase 2 Mismatch Resolution

Provides an interactive command-line interface for reviewing, approving, 
and modifying AI-suggested mismatch resolutions.
"""

import json
import sys
import time
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import rich
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.columns import Columns
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from .models import Mismatch, ResolutionPlan, ResolutionAction
    from .enums import MismatchType, ResolutionStatus, ResolutionActionType
    from .resolution_engine import ResolutionEngine
    from .ai.judge import EquivalenceRunner
    from .telemetry_logger import StructuredLogger
except ImportError:
    # Standalone execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from phase2.models import Mismatch, ResolutionPlan, ResolutionAction
    from phase2.enums import MismatchType, ResolutionStatus, ResolutionActionType
    from phase2.resolution_engine import ResolutionEngine
    from phase2.ai.judge import EquivalenceRunner
    from phase2.telemetry_logger import StructuredLogger


@dataclass
class ResolutionChoice:
    """User's choice for a resolution."""
    action: str  # "approve", "modify", "reject", "skip"
    modified_plan: Optional[ResolutionPlan] = None
    feedback: Optional[str] = None
    confidence: float = 1.0


class InteractiveCLI:
    """Interactive CLI for mismatch resolution."""
    
    def __init__(self, resolution_engine: ResolutionEngine, 
                 equivalence_runner: EquivalenceRunner,
                 telemetry_logger: StructuredLogger,
                 auto_approve_safe: bool = False,
                 non_interactive: bool = False,
                 no_color: bool = False,
                 state_file: Optional[str] = None):
        self.resolution_engine = resolution_engine
        self.equivalence_runner = equivalence_runner
        self.telemetry_logger = telemetry_logger
        self.auto_approve_safe = auto_approve_safe
        self.non_interactive = non_interactive
        self.state_file = state_file
        
        # TTY/CI detection
        is_tty = sys.stdout.isatty()
        use_rich = RICH_AVAILABLE and is_tty and not no_color
        
        # Initialize console
        if use_rich:
            self.console = Console()
        else:
            self.console = None
        
        # Statistics
        self.stats = {
            "total_reviewed": 0,
            "approved": 0,
            "modified": 0,
            "rejected": 0,
            "skipped": 0,
            "auto_approved": 0
        }
        
        # Load state if resuming
        self.processed_ids = set()
        if self.state_file and Path(self.state_file).exists():
            self._load_state()
    
    def print(self, *args, **kwargs):
        """Print with rich formatting if available."""
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)
    
    def input(self, prompt: str, choices: List[str] = None, default: str = None) -> str:
        """Get user input with rich formatting if available."""
        if self.console and RICH_AVAILABLE:
            if choices:
                return Prompt.ask(prompt, choices=choices, default=default)
            else:
                return Prompt.ask(prompt, default=default)
        else:
            if choices:
                choice_str = "/".join(choices)
                full_prompt = f"{prompt} [{choice_str}]"
                if default:
                    full_prompt += f" (default: {default})"
                full_prompt += ": "
            else:
                full_prompt = f"{prompt}: "
            
            response = input(full_prompt).strip()
            return response if response else (default or "")
    
    def confirm(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no confirmation."""
        if self.console and RICH_AVAILABLE:
            return Confirm.ask(prompt, default=default)
        else:
            default_str = "Y/n" if default else "y/N"
            response = input(f"{prompt} [{default_str}]: ").strip().lower()
            if not response:
                return default
            return response.startswith('y')
    
    def _sanitize_diff_content(self, content: str) -> str:
        """Sanitize diff content for safe terminal display."""
        if not content:
            return ""
        
        # Remove ANSI escape sequences
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        content = ansi_escape.sub('', content)
        
        # Split into lines and process
        lines = content.split('\n')
        safe_lines = []
        
        for line in lines[:50]:  # Limit to 50 lines
            # Truncate very long lines (paste-bomb protection)
            if len(line) > 200:
                line = line[:200] + " ... [line truncated]"
            
            # Check for binary content
            if any(ord(c) < 32 and c not in '\t\n\r' for c in line):
                line = "[binary content]"
            
            safe_lines.append(line)
        
        if len(lines) > 50:
            safe_lines.append("... [truncated: too many lines]")
        
        return '\n'.join(safe_lines)
    
    def display_mismatch(self, mismatch: Mismatch) -> None:
        """Display mismatch details."""
        if self.console:
            # Rich display
            table = Table(title=f"Mismatch {mismatch.id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Type", mismatch.mismatch_type.value)
            table.add_row("Status", mismatch.status.value)
            table.add_row("Confidence", f"{mismatch.confidence_score:.2f}")
            table.add_row("Created", mismatch.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            
            if mismatch.evidence and mismatch.evidence.get("diff_summary"):
                summary = self._sanitize_diff_content(mismatch.evidence["diff_summary"])
                table.add_row("Diff Summary", summary[:100] + ("..." if len(summary) > 100 else ""))
            
            self.print(table)
            
            # Show diff if available
            if mismatch.evidence and mismatch.evidence.get("diff_content"):
                diff_content = self._sanitize_diff_content(mismatch.evidence["diff_content"])
                
                syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=True)
                self.print(Panel(syntax, title="Diff Content", border_style="blue"))
        else:
            # Plain text display
            print(f"\n=== Mismatch {mismatch.id} ===")
            print(f"Type: {mismatch.mismatch_type.value}")
            print(f"Status: {mismatch.status.value}")
            print(f"Confidence: {mismatch.confidence_score:.2f}")
            print(f"Created: {mismatch.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if mismatch.evidence and mismatch.evidence.get("diff_summary"):
                print(f"Diff Summary: {mismatch.evidence['diff_summary'][:100]}...")
            
            if mismatch.evidence and mismatch.evidence.get("diff_content"):
                print("\nDiff Content:")
                print("-" * 40)
                diff_content = self._sanitize_diff_content(mismatch.evidence["diff_content"])
                print(diff_content)
                print("-" * 40)
    
    def display_resolution_plan(self, plan: ResolutionPlan) -> None:
        """Display resolution plan details."""
        if self.console:
            # Rich display
            table = Table(title="AI-Suggested Resolution Plan")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Strategy", plan.strategy)
            table.add_row("Confidence", f"{plan.confidence:.2f}")
            table.add_row("Safety Level", plan.safety_level.value)
            table.add_row("Actions", str(len(plan.actions)))
            
            if plan.estimated_impact:
                impact = plan.estimated_impact
                table.add_row("Est. Files Changed", str(impact.get("files_changed", "unknown")))
                table.add_row("Est. Lines Changed", str(impact.get("lines_changed", "unknown")))
            
            self.print(table)
            
            # Show actions
            if plan.actions:
                actions_table = Table(title="Resolution Actions")
                actions_table.add_column("#", style="dim")
                actions_table.add_column("Type", style="cyan")
                actions_table.add_column("Description", style="white")
                actions_table.add_column("Safe", style="green")
                
                for i, action in enumerate(plan.actions, 1):
                    safe_str = "✓" if action.is_safe else "⚠"
                    actions_table.add_row(
                        str(i),
                        action.action_type.value,
                        action.description[:60] + ("..." if len(action.description) > 60 else ""),
                        safe_str
                    )
                
                self.print(actions_table)
        else:
            # Plain text display
            print(f"\n=== AI-Suggested Resolution Plan ===")
            print(f"Strategy: {plan.strategy}")
            print(f"Confidence: {plan.confidence:.2f}")
            print(f"Safety Level: {plan.safety_level.value}")
            print(f"Actions: {len(plan.actions)}")
            
            if plan.estimated_impact:
                impact = plan.estimated_impact
                print(f"Est. Files Changed: {impact.get('files_changed', 'unknown')}")
                print(f"Est. Lines Changed: {impact.get('lines_changed', 'unknown')}")
            
            if plan.actions:
                print("\nResolution Actions:")
                for i, action in enumerate(plan.actions, 1):
                    safe_str = "✓" if action.is_safe else "⚠"
                    print(f"  {i}. [{action.action_type.value}] {action.description} ({safe_str})")
    
    def display_impact_analysis(self, plan: ResolutionPlan) -> None:
        """Display impact analysis for the resolution plan."""
        if not plan.estimated_impact:
            self.print("[yellow]No impact analysis available[/yellow]")
            return
        
        impact = plan.estimated_impact
        
        if self.console:
            panel_content = []
            
            # Risk assessment
            risk_level = impact.get("risk_level", "unknown")
            risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(risk_level, "white")
            panel_content.append(f"[{risk_color}]Risk Level: {risk_level.upper()}[/{risk_color}]")
            
            # Changes summary
            files_changed = impact.get("files_changed", 0)
            lines_changed = impact.get("lines_changed", 0)
            panel_content.append(f"Files to change: {files_changed}")
            panel_content.append(f"Lines to change: {lines_changed}")
            
            # Rollback info
            if impact.get("rollback_available"):
                panel_content.append("[green]✓ Rollback available[/green]")
            else:
                panel_content.append("[red]⚠ No rollback available[/red]")
            
            # Warnings
            if impact.get("warnings"):
                panel_content.append("\n[yellow]Warnings:[/yellow]")
                for warning in impact["warnings"]:
                    panel_content.append(f"  • {warning}")
            
            self.print(Panel("\n".join(panel_content), title="Impact Analysis", border_style="yellow"))
        else:
            print("\n=== Impact Analysis ===")
            print(f"Risk Level: {impact.get('risk_level', 'unknown').upper()}")
            print(f"Files to change: {impact.get('files_changed', 0)}")
            print(f"Lines to change: {impact.get('lines_changed', 0)}")
            
            if impact.get("rollback_available"):
                print("✓ Rollback available")
            else:
                print("⚠ No rollback available")
            
            if impact.get("warnings"):
                print("\nWarnings:")
                for warning in impact["warnings"]:
                    print(f"  • {warning}")
    
    def get_user_choice(self, mismatch: Mismatch, plan: ResolutionPlan) -> ResolutionChoice:
        """Get user's choice for the resolution."""
        
        # Check for auto-approval of safe resolutions
        if (self.auto_approve_safe and 
            plan.safety_level.value == "safe" and 
            plan.confidence >= 0.9 and
            mismatch.mismatch_type in [MismatchType.WHITESPACE, MismatchType.JSON_ORDERING]):
            
            self.print("[green]Auto-approving safe resolution[/green]")
            return ResolutionChoice(action="approve", confidence=1.0)
        
        # Non-interactive mode: auto-approve safe, skip others
        if self.non_interactive:
            if (plan.safety_level.value == "safe" and 
                plan.confidence >= 0.8 and
                mismatch.mismatch_type in [MismatchType.WHITESPACE, MismatchType.JSON_ORDERING]):
                self.print("Non-interactive: auto-approving safe resolution")
                return ResolutionChoice(action="approve", confidence=0.9)
            else:
                self.print("Non-interactive: skipping non-safe resolution")
                return ResolutionChoice(action="skip", feedback="Non-interactive mode, not safe for auto-approval")
        
        # Present options
        self.print("\n[bold]Resolution Options:[/bold]")
        self.print("  [green]approve[/green] - Apply the AI suggestion as-is")
        self.print("  [yellow]modify[/yellow]  - Edit the AI suggestion before applying")
        self.print("  [red]reject[/red]   - Reject the AI suggestion")
        self.print("  [blue]skip[/blue]     - Skip this mismatch for now")
        
        choice = self.input(
            "\nWhat would you like to do?",
            choices=["approve", "modify", "reject", "skip"],
            default="approve" if plan.confidence >= 0.8 else "skip"
        )
        
        if choice == "approve":
            # Confirm high-risk approvals
            if plan.safety_level.value in ["risky", "dangerous"]:
                confirmed = self.confirm(
                    f"[red]This is a {plan.safety_level.value} resolution. Are you sure?[/red]",
                    default=False
                )
                if not confirmed:
                    return ResolutionChoice(action="skip", feedback="User cancelled high-risk approval")
            
            return ResolutionChoice(action="approve", confidence=1.0)
        
        elif choice == "modify":
            return self._handle_modification(plan)
        
        elif choice == "reject":
            feedback = self.input("Why are you rejecting this suggestion? (optional)")
            return ResolutionChoice(action="reject", feedback=feedback)
        
        else:  # skip
            return ResolutionChoice(action="skip")
    
    def _handle_modification(self, plan: ResolutionPlan) -> ResolutionChoice:
        """Handle user modification of the resolution plan."""
        self.print("\n[yellow]Modification mode - this is a simplified implementation[/yellow]")
        self.print("In a full implementation, this would provide:")
        self.print("  • Interactive action editing")
        self.print("  • Parameter adjustment")
        self.print("  • Custom action addition")
        
        # For now, just get feedback
        feedback = self.input("Describe your desired modifications")
        
        # Create a modified plan (simplified)
        modified_plan = ResolutionPlan(
            mismatch_id=plan.mismatch_id,
            strategy=f"modified_{plan.strategy}",
            actions=plan.actions,  # In reality, this would be edited
            confidence=plan.confidence * 0.9,  # Reduce confidence for modified plans
            safety_level=plan.safety_level,
            estimated_impact=plan.estimated_impact,
            metadata={**plan.metadata, "user_modified": True, "modification_feedback": feedback}
        )
        
        return ResolutionChoice(
            action="modify",
            modified_plan=modified_plan,
            feedback=feedback,
            confidence=0.8
        )
    
    def apply_resolution(self, mismatch: Mismatch, choice: ResolutionChoice) -> bool:
        """Apply the user's resolution choice."""
        try:
            if choice.action == "approve":
                # Apply the original plan
                plan = self.resolution_engine.generate_resolution_plan(mismatch)
                result = self.resolution_engine.execute_resolution_plan(plan)
                
                if result.status == ResolutionStatus.COMPLETED:
                    self.print("[green]✓ Resolution applied successfully[/green]")
                    return True
                else:
                    self.print(f"[red]✗ Resolution failed: {result.error_message}[/red]")
                    return False
            
            elif choice.action == "modify":
                # Apply the modified plan
                if choice.modified_plan:
                    result = self.resolution_engine.execute_resolution_plan(choice.modified_plan)
                    
                    if result.status == ResolutionStatus.COMPLETED:
                        self.print("[green]✓ Modified resolution applied successfully[/green]")
                        return True
                    else:
                        self.print(f"[red]✗ Modified resolution failed: {result.error_message}[/red]")
                        return False
                else:
                    self.print("[red]✗ No modified plan available[/red]")
                    return False
            
            elif choice.action == "reject":
                self.print("[yellow]Resolution rejected - mismatch remains unresolved[/yellow]")
                return False
            
            else:  # skip
                self.print("[blue]Mismatch skipped[/blue]")
                return False
                
        except Exception as e:
            self.print(f"[red]✗ Error applying resolution: {e}[/red]")
            return False
    
    def log_user_interaction(self, mismatch: Mismatch, choice: ResolutionChoice, success: bool):
        """Log the user interaction for learning purposes."""
        import hashlib
        import uuid
        
        # Generate config fingerprint
        config_str = json.dumps({
            "auto_approve_safe": self.auto_approve_safe,
            "non_interactive": self.non_interactive,
            "rich_ui": self.console is not None
        }, sort_keys=True)
        config_fingerprint = hashlib.sha256(config_str.encode()).hexdigest()[:16]
        
        # Basic interaction event
        event_data = {
            "mismatch_id": mismatch.id,
            "mismatch_type": mismatch.mismatch_type.value,
            "user_action": choice.action,
            "user_confidence": choice.confidence,
            "feedback": choice.feedback,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if choice.modified_plan:
            event_data["plan_modified"] = True
            event_data["original_confidence"] = choice.modified_plan.confidence
        
        self.telemetry_logger.log_event("user_resolution_interaction", event_data)
        
        # Enhanced ResolutionDecision event
        decision_event = {
            "id": f"decision_{uuid.uuid4().hex[:8]}",
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": mismatch.run_id,
            "env": os.getenv("ENVIRONMENT", "development"),
            "mismatch_id": mismatch.id,
            "plan_id": f"plan_{mismatch.id}",
            "action": choice.action,
            "decision": "auto-approve" if (choice.action == "approve" and self.auto_approve_safe) else choice.action,
            "reason": choice.feedback or f"User {choice.action} with confidence {choice.confidence}",
            "user": {
                "id": os.getenv("USER", "unknown"),
                "role": "developer"
            },
            "ui": {
                "rich": self.console is not None,
                "version": "1.0.0"
            },
            "config_fingerprint": config_fingerprint,
            "transform": {
                "id": f"transform_{mismatch.mismatch_type.value}",
                "idempotent": mismatch.mismatch_type in [MismatchType.WHITESPACE, MismatchType.JSON_ORDERING]
            },
            "hashes": {
                "before": hashlib.sha256(str(mismatch.evidence).encode()).hexdigest()[:16],
                "after": hashlib.sha256(f"{mismatch.evidence}_{choice.action}".encode()).hexdigest()[:16]
            }
        }
        
        self.telemetry_logger.log_event("resolution_decision", decision_event)
    
    def process_mismatch(self, mismatch: Mismatch) -> bool:
        """Process a single mismatch interactively."""
        
        # Skip if already processed (resume support)
        if mismatch.id in self.processed_ids:
            self.print(f"[dim]Skipping already processed mismatch {mismatch.id}[/dim]")
            return True
        
        self.stats["total_reviewed"] += 1
        
        # Display mismatch
        self.display_mismatch(mismatch)
        
        # Generate resolution plan
        try:
            plan = self.resolution_engine.generate_resolution_plan(mismatch)
        except Exception as e:
            self.print(f"[red]✗ Failed to generate resolution plan: {e}[/red]")
            return False
        
        # Display plan
        self.display_resolution_plan(plan)
        self.display_impact_analysis(plan)
        
        # Get user choice
        choice = self.get_user_choice(mismatch, plan)
        
        # Update statistics
        self.stats[choice.action] += 1
        if choice.action == "approve" and self.auto_approve_safe:
            self.stats["auto_approved"] += 1
        
        # Apply resolution
        success = self.apply_resolution(mismatch, choice)
        
        # Log interaction
        self.log_user_interaction(mismatch, choice, success)
        
        # Mark as processed and save state
        self.processed_ids.add(mismatch.id)
        self._save_state()
        
        return success
    
    def process_mismatches(self, mismatches: List[Mismatch]) -> Dict[str, Any]:
        """Process multiple mismatches interactively."""
        if not mismatches:
            self.print("[yellow]No mismatches to process[/yellow]")
            return self.get_summary()
        
        self.print(f"\n[bold]Processing {len(mismatches)} mismatches[/bold]")
        
        for i, mismatch in enumerate(mismatches, 1):
            self.print(f"\n[bold cyan]=== Mismatch {i}/{len(mismatches)} ===[/bold cyan]")
            
            try:
                self.process_mismatch(mismatch)
            except KeyboardInterrupt:
                self.print("\n[yellow]Interrupted by user[/yellow]")
                break
            except Exception as e:
                self.print(f"[red]✗ Error processing mismatch {mismatch.id}: {e}[/red]")
                continue
            
            # Ask if user wants to continue
            if i < len(mismatches):
                if not self.confirm("Continue to next mismatch?", default=True):
                    break
        
        return self.get_summary()
    
    def _load_state(self):
        """Load processing state from file."""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.stats.update(state.get("stats", {}))
            self.processed_ids = set(state.get("processed_ids", []))
            
            self.print(f"[blue]Resumed from state file: {len(self.processed_ids)} items already processed[/blue]")
        except Exception as e:
            self.print(f"[yellow]Warning: Could not load state file: {e}[/yellow]")
    
    def _save_state(self):
        """Save processing state to file."""
        if not self.state_file:
            return
        
        try:
            state = {
                "stats": self.stats,
                "processed_ids": list(self.processed_ids),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.print(f"[yellow]Warning: Could not save state file: {e}[/yellow]")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        return {
            "total_reviewed": self.stats["total_reviewed"],
            "approved": self.stats["approved"],
            "modified": self.stats["modified"],
            "rejected": self.stats["rejected"],
            "skipped": self.stats["skipped"],
            "auto_approved": self.stats["auto_approved"],
            "success_rate": (self.stats["approved"] + self.stats["modified"]) / max(1, self.stats["total_reviewed"])
        }
    
    def display_summary(self, summary: Dict[str, Any]):
        """Display processing summary."""
        if self.console:
            table = Table(title="Resolution Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="white")
            table.add_column("Percentage", style="green")
            
            total = summary["total_reviewed"]
            if total > 0:
                table.add_row("Total Reviewed", str(total), "100%")
                table.add_row("Approved", str(summary["approved"]), f"{summary['approved']/total*100:.1f}%")
                table.add_row("Modified", str(summary["modified"]), f"{summary['modified']/total*100:.1f}%")
                table.add_row("Rejected", str(summary["rejected"]), f"{summary['rejected']/total*100:.1f}%")
                table.add_row("Skipped", str(summary["skipped"]), f"{summary['skipped']/total*100:.1f}%")
                table.add_row("Auto-approved", str(summary["auto_approved"]), f"{summary['auto_approved']/total*100:.1f}%")
                table.add_row("Success Rate", f"{summary['success_rate']:.1%}", "")
            
            self.print(table)
        else:
            print("\n=== Resolution Summary ===")
            total = summary["total_reviewed"]
            print(f"Total Reviewed: {total}")
            if total > 0:
                print(f"Approved: {summary['approved']} ({summary['approved']/total*100:.1f}%)")
                print(f"Modified: {summary['modified']} ({summary['modified']/total*100:.1f}%)")
                print(f"Rejected: {summary['rejected']} ({summary['rejected']/total*100:.1f}%)")
                print(f"Skipped: {summary['skipped']} ({summary['skipped']/total*100:.1f}%)")
                print(f"Auto-approved: {summary['auto_approved']} ({summary['auto_approved']/total*100:.1f}%)")
                print(f"Success Rate: {summary['success_rate']:.1%}")


def parse_methods(methods: List[str]) -> List[str]:
    """Parse method list supporting comma or space delimited."""
    if len(methods) == 1 and ',' in methods[0]:
        methods = [m.strip() for m in methods[0].split(',') if m.strip()]
    
    # Normalize method names
    normalized = []
    valid_methods = {
        "exact", "cosine_similarity", "canonical_json", 
        "ast_normalized", "llm_rubric_judge"
    }
    
    for method in methods:
        method = method.lower().replace('-', '_').strip()
        if method in valid_methods:
            normalized.append(method)
        else:
            print(f"❌ Unknown method '{method}'. Valid methods: {', '.join(sorted(valid_methods))}")
            sys.exit(1)
    
    return normalized


def main():
    """CLI entry point for interactive resolution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive Mismatch Resolution CLI")
    parser.add_argument("--mismatches", required=True, help="JSON file containing mismatches")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--auto-approve-safe", action="store_true", 
                       help="Auto-approve safe resolutions")
    parser.add_argument("--output", help="Output summary file")
    parser.add_argument("--no-color", action="store_true",
                       help="Disable colored output")
    parser.add_argument("--yes", action="store_true",
                       help="Non-interactive mode (auto-approve safe resolutions)")
    parser.add_argument("--state-file", 
                       help="State file for resume support (e.g., .interactive.state.json)")
    
    args = parser.parse_args()
    
    # Load mismatches (simplified for demo)
    try:
        with open(args.mismatches, 'r') as f:
            mismatch_data = json.load(f)
        
        # Convert to Mismatch objects (simplified)
        mismatches = []
        for item in mismatch_data.get("mismatches", []):
            from .enums import MismatchStatus
            mismatch = Mismatch(
                id=item["id"],
                run_id=item.get("run_id", "unknown"),
                artifact_ids=item.get("artifact_ids", []),
                mismatch_type=MismatchType(item["mismatch_type"]),
                detectors=item.get("detectors", []),
                evidence=item.get("evidence", {}),
                status=MismatchStatus.DETECTED,
                confidence_score=item.get("confidence_score", 0.5),
                created_at=datetime.now(timezone.utc)
            )
            mismatches.append(mismatch)
        
    except Exception as e:
        print(f"Error loading mismatches: {e}")
        sys.exit(1)
    
    # Initialize components (mock for demo)
    resolution_engine = None  # Would be initialized with real engine
    equivalence_runner = None  # Would be initialized with real runner
    telemetry_logger = None  # Would be initialized with real logger
    
    # Create CLI
    cli = InteractiveCLI(
        resolution_engine=resolution_engine,
        equivalence_runner=equivalence_runner,
        telemetry_logger=telemetry_logger,
        auto_approve_safe=args.auto_approve_safe,
        non_interactive=args.yes,
        no_color=args.no_color,
        state_file=args.state_file
    )
    
    # Process mismatches
    summary = cli.process_mismatches(mismatches)
    
    # Display summary
    cli.display_summary(summary)
    
    # Save summary if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary saved to {args.output}")


if __name__ == "__main__":
    main()