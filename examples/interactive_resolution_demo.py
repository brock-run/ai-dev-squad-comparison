#!/usr/bin/env python3
"""Demo of Interactive Resolution CLI

Shows how the interactive CLI works with sample mismatches.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Sample mismatches for demo
SAMPLE_MISMATCHES = {
    "mismatches": [
        {
            "id": "mismatch_001",
            "run_id": "run_12345",
            "artifact_ids": ["artifact_001", "artifact_002"],
            "mismatch_type": "whitespace",
            "detectors": ["whitespace_detector"],
            "evidence": {
                "diff_summary": "Extra whitespace in line 42",
                "diff_content": "- def hello():\n+ def hello(): \n",
                "cost_estimate": 0.001,
                "latency_ms": 50
            },
            "confidence_score": 0.95,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "mismatch_002", 
            "run_id": "run_12345",
            "artifact_ids": ["artifact_003"],
            "mismatch_type": "json_ordering",
            "detectors": ["json_structure_detector"],
            "evidence": {
                "diff_summary": "JSON key ordering difference",
                "diff_content": '- {"a": 1, "b": 2}\n+ {"b": 2, "a": 1}',
                "cost_estimate": 0.002,
                "latency_ms": 75
            },
            "confidence_score": 0.88,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "mismatch_003",
            "run_id": "run_12345", 
            "artifact_ids": ["artifact_004"],
            "mismatch_type": "semantics_text",
            "detectors": ["semantic_detector"],
            "evidence": {
                "diff_summary": "Potential semantic difference in text",
                "diff_content": "- Hello world\n+ Hello there",
                "cost_estimate": 0.05,
                "latency_ms": 2000
            },
            "confidence_score": 0.65,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
}


def create_demo_files():
    """Create demo files for the interactive CLI."""
    
    # Create temporary directory
    demo_dir = Path("demo_interactive_resolution")
    demo_dir.mkdir(exist_ok=True)
    
    # Create mismatches file
    mismatches_file = demo_dir / "sample_mismatches.json"
    with open(mismatches_file, 'w') as f:
        json.dump(SAMPLE_MISMATCHES, f, indent=2)
    
    # Create config file
    config_file = demo_dir / "config.yaml"
    config_content = """
# Interactive Resolution Configuration
resolution:
  auto_approve_safe: true
  safety_threshold: 0.9
  
ai:
  llm:
    provider: mock
    model: mock-llm
  
telemetry:
  enabled: true
  log_level: INFO
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    return mismatches_file, config_file, demo_dir


def main():
    """Run the interactive resolution demo."""
    
    print("🎯 Interactive Resolution CLI Demo")
    print("=" * 50)
    
    # Create demo files
    mismatches_file, config_file, demo_dir = create_demo_files()
    
    print(f"📁 Demo files created in: {demo_dir}")
    print(f"   Mismatches: {mismatches_file}")
    print(f"   Config: {config_file}")
    
    print("\n📋 Sample Mismatches:")
    for i, mismatch in enumerate(SAMPLE_MISMATCHES["mismatches"], 1):
        print(f"   {i}. {mismatch['id']} - {mismatch['mismatch_type']} (confidence: {mismatch['confidence_score']:.2f})")
    
    print("\n🚀 To run the interactive CLI:")
    print(f"   python common/phase2/cli_interactive.py \\")
    print(f"     --mismatches {mismatches_file} \\")
    print(f"     --config {config_file} \\")
    print(f"     --auto-approve-safe \\")
    print(f"     --output {demo_dir}/summary.json")
    
    print("\n💡 Features demonstrated:")
    print("   • Rich terminal UI with colors and tables")
    print("   • Interactive mismatch review")
    print("   • AI resolution plan display")
    print("   • Impact analysis")
    print("   • User choice handling (approve/modify/reject/skip)")
    print("   • Auto-approval of safe resolutions")
    print("   • Processing summary and statistics")
    
    print("\n🎮 Interactive Options:")
    print("   • approve - Apply AI suggestion as-is")
    print("   • modify  - Edit AI suggestion before applying")
    print("   • reject  - Reject AI suggestion")
    print("   • skip    - Skip mismatch for now")
    
    print("\n🔒 Safety Features:")
    print("   • Risk level assessment")
    print("   • Confirmation for high-risk operations")
    print("   • Rollback availability checking")
    print("   • User feedback collection for learning")
    
    print(f"\n📊 Results will be saved to: {demo_dir}/summary.json")
    
    # Show sample mismatch details
    print("\n📄 Sample Mismatch Details:")
    sample = SAMPLE_MISMATCHES["mismatches"][0]
    print(f"   ID: {sample['id']}")
    print(f"   Type: {sample['mismatch_type']}")
    print(f"   Confidence: {sample['confidence_score']}")
    print(f"   Evidence: {sample['evidence']['diff_summary']}")
    print(f"   Diff: {sample['evidence']['diff_content']}")
    
    print("\n✨ The CLI provides a rich, interactive experience for:")
    print("   • Reviewing AI-detected mismatches")
    print("   • Understanding resolution impact")
    print("   • Making informed decisions")
    print("   • Learning from user feedback")
    
    return demo_dir


if __name__ == "__main__":
    demo_dir = main()
    print(f"\n🎉 Demo setup complete! Files are in: {demo_dir}")