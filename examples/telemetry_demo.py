#!/usr/bin/env python3
"""
Telemetry System Demo

This script demonstrates the comprehensive structured logging capabilities
of the AI Dev Squad platform, showing various event types and filtering options.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from common.telemetry import (
    configure_logging,
    get_logger,
    EventType,
    LogLevel,
    create_event
)


async def simulate_agent_workflow():
    """Simulate a complete agent workflow with telemetry."""
    
    # Configure logging
    logger = configure_logging(
        log_dir="demo_logs",
        level=LogLevel.INFO,
        enable_console=True
    )
    
    # Set session context
    logger.set_session_context("demo_session_123", "workflow_correlation_456")
    
    print("🚀 Starting AI Dev Squad Telemetry Demo")
    print("=" * 50)
    
    # 1. Agent Lifecycle Events
    print("\n📋 Logging Agent Lifecycle Events...")
    
    logger.log_agent_start(
        agent_id="demo_agent_001",
        agent_type="full_stack_developer",
        framework="langgraph",
        capabilities=["code_generation", "testing", "debugging", "documentation"],
        config={
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "llama3.1:8b"
        }
    )
    
    await asyncio.sleep(0.1)  # Simulate some work
    
    # 2. Task Execution Events
    print("📝 Logging Task Execution Events...")
    
    task_start_time = time.time()
    
    logger.log_task_start(
        task_id="task_generate_api",
        task_name="generate_rest_api",
        agent_id="demo_agent_001",
        framework="langgraph",
        task_input={
            "requirements": "Create a REST API for user management",
            "language": "Python",
            "framework": "FastAPI"
        }
    )
    
    # Simulate task execution time
    await asyncio.sleep(2.0)
    
    task_duration = (time.time() - task_start_time) * 1000
    
    logger.log_task_complete(
        task_id="task_generate_api",
        task_name="generate_rest_api",
        agent_id="demo_agent_001",
        framework="langgraph",
        duration_ms=task_duration,
        task_output={
            "files_created": ["main.py", "models.py", "routes.py", "tests.py"],
            "lines_of_code": 245,
            "test_coverage": 85.5
        }
    )
    
    # 3. Tool Usage Events
    print("🔧 Logging Tool Usage Events...")
    
    tool_start_time = time.time()
    
    logger.log_tool_call(
        tool_name="file_writer",
        agent_id="demo_agent_001",
        framework="langgraph",
        tool_input={
            "filename": "main.py",
            "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}"
        }
    )
    
    await asyncio.sleep(0.5)
    
    tool_duration = (time.time() - tool_start_time) * 1000
    
    # Log tool result using create_event
    tool_result_event = create_event(
        EventType.TOOL_RESULT,
        tool_name="file_writer",
        agent_id="demo_agent_001",
        framework="langgraph",
        tool_output={
            "success": True,
            "bytes_written": 156,
            "file_path": "/workspace/main.py"
        },
        duration_ms=tool_duration,
        success=True,
        message="File written successfully"
    )
    logger.log_event(tool_result_event)
    
    # 4. LLM Interaction Events
    print("🤖 Logging LLM Interaction Events...")
    
    logger.log_llm_interaction(
        model_name="llama3.1:8b",
        provider="ollama",
        prompt_tokens=150,
        completion_tokens=95,
        duration_ms=1800.0,
        cost_usd=0.0,  # Local model
        agent_id="demo_agent_001"
    )
    
    # 5. Safety Events
    print("🛡️ Logging Safety Events...")
    
    logger.log_safety_violation(
        policy_name="file_access_policy",
        violation_type="attempted_system_file_access",
        risk_level="medium",
        action_taken="blocked_and_logged",
        agent_id="demo_agent_001",
        blocked_content="/etc/passwd"
    )
    
    # 6. VCS Events
    print("📚 Logging VCS Events...")
    
    vcs_commit_event = create_event(
        EventType.VCS_COMMIT,
        repository="ai-dev-squad-demo",
        branch="feature/rest-api",
        commit_hash="abc123def456789",
        operation="commit",
        files_changed=["main.py", "models.py", "routes.py"],
        message="Generated REST API with FastAPI"
    )
    logger.log_event(vcs_commit_event)
    
    vcs_pr_event = create_event(
        EventType.VCS_PR_CREATE,
        repository="ai-dev-squad-demo",
        branch="feature/rest-api",
        operation="pull_request_create",
        pr_number=42,
        message="Created PR for REST API implementation"
    )
    logger.log_event(vcs_pr_event)
    
    # 7. Performance Events
    print("📊 Logging Performance Events...")
    
    performance_event = create_event(
        EventType.PERFORMANCE_METRIC,
        metric_name="task_completion_time",
        metric_value=task_duration / 1000,  # Convert to seconds
        metric_unit="seconds",
        cpu_percent=45.2,
        memory_mb=512.0,
        disk_io_mb=15.3,
        network_io_mb=2.1,
        agent_id="demo_agent_001",
        framework="langgraph",
        message="Performance metrics for API generation task"
    )
    logger.log_event(performance_event)
    
    # 8. Framework-Specific Events
    print("⚙️ Logging Framework-Specific Events...")
    
    framework_event = create_event(
        EventType.FRAMEWORK_EVENT,
        framework="langgraph",
        framework_version="0.2.0",
        operation="state_transition",
        component="graph_executor",
        state_data={
            "current_node": "code_generator",
            "next_node": "code_reviewer",
            "transition_reason": "code_generation_complete"
        },
        agent_id="demo_agent_001",
        message="LangGraph state transition"
    )
    logger.log_event(framework_event)
    
    # 9. Error Simulation
    print("❌ Logging Error Events...")
    
    logger.log_task_error(
        task_id="task_broken_feature",
        task_name="generate_broken_code",
        agent_id="demo_agent_001",
        framework="langgraph",
        error="Syntax error in generated Python code: unexpected indent on line 15",
        duration_ms=500.0
    )
    
    # 10. Agent Shutdown
    print("🛑 Logging Agent Shutdown...")
    
    total_duration = (time.time() - task_start_time) * 1000
    
    logger.log_agent_stop(
        agent_id="demo_agent_001",
        framework="langgraph",
        duration_ms=total_duration
    )
    
    # Flush all events
    logger.flush()
    
    print("\n✅ Demo completed! Check the logs in 'demo_logs/' directory")
    print(f"📁 Log file: demo_logs/ai_dev_squad.jsonl")
    
    return logger


def demonstrate_filtering():
    """Demonstrate event filtering capabilities."""
    
    print("\n🔍 Demonstrating Event Filtering")
    print("=" * 40)
    
    # Create logger with filtering
    logger = configure_logging(
        log_dir="filtered_logs",
        level=LogLevel.WARNING,  # Only WARNING and above
        enable_console=True
    )
    
    # Add framework filter
    logger.get_filter().set_framework_filter(["langgraph", "crewai"])
    
    # Add custom filter for important events only
    def important_events_only(event_data):
        message = event_data.get("message", "").lower()
        return any(keyword in message for keyword in ["error", "violation", "critical", "important"])
    
    logger.get_filter().add_custom_filter(important_events_only)
    
    print("🔧 Configured filters:")
    print("  - Level: WARNING and above")
    print("  - Frameworks: langgraph, crewai only")
    print("  - Custom: Important events only")
    
    # Log various events - only some should pass filters
    print("\n📝 Logging test events...")
    
    # This should be filtered out (INFO level)
    logger.log_agent_start(
        agent_id="filtered_agent",
        agent_type="test",
        framework="langgraph"
    )
    
    # This should be filtered out (wrong framework)
    logger.log_safety_violation(
        policy_name="test_policy",
        violation_type="test_violation",
        risk_level="high",
        action_taken="blocked",
        framework="autogen"  # Not in allowed frameworks
    )
    
    # This should pass all filters (WARNING level, correct framework, contains "violation")
    logger.log_safety_violation(
        policy_name="important_policy",
        violation_type="critical_security_violation",
        risk_level="high",
        action_taken="blocked",
        framework="langgraph"
    )
    
    # This should pass (ERROR level, correct framework, contains "error")
    logger.log_task_error(
        task_id="critical_task",
        task_name="important_operation",
        agent_id="filtered_agent",
        framework="crewai",
        error="Critical system error occurred"
    )
    
    logger.flush()
    
    print("✅ Filtering demo completed! Check 'filtered_logs/' directory")
    
    return logger


def analyze_log_output():
    """Analyze and display log output."""
    
    print("\n📊 Analyzing Log Output")
    print("=" * 30)
    
    log_files = [
        Path("demo_logs/ai_dev_squad.jsonl"),
        Path("filtered_logs/ai_dev_squad.jsonl")
    ]
    
    for log_file in log_files:
        if log_file.exists():
            print(f"\n📄 {log_file}")
            print("-" * len(str(log_file)))
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            print(f"Total events: {len(lines)}")
            
            # Count events by type
            event_counts = {}
            for line in lines:
                try:
                    import json
                    event = json.loads(line.strip())
                    event_type = event.get("event_type", "unknown")
                    event_counts[event_type] = event_counts.get(event_type, 0) + 1
                except json.JSONDecodeError:
                    continue
            
            print("Event breakdown:")
            for event_type, count in sorted(event_counts.items()):
                print(f"  {event_type}: {count}")
            
            # Show sample event
            if lines:
                print(f"\nSample event (first):")
                try:
                    import json
                    sample = json.loads(lines[0].strip())
                    print(f"  Type: {sample.get('event_type')}")
                    print(f"  Level: {sample.get('level')}")
                    print(f"  Message: {sample.get('message')}")
                    print(f"  Framework: {sample.get('framework')}")
                except json.JSONDecodeError:
                    print("  Could not parse sample event")
        else:
            print(f"\n❌ {log_file} not found")


async def main():
    """Run the complete telemetry demo."""
    
    print("🎯 AI Dev Squad Telemetry System Demo")
    print("=" * 60)
    
    try:
        # Run main workflow demo
        main_logger = await simulate_agent_workflow()
        
        # Demonstrate filtering
        filter_logger = demonstrate_filtering()
        
        # Analyze output
        analyze_log_output()
        
        print("\n🎉 All demos completed successfully!")
        print("\nNext steps:")
        print("1. Examine the generated log files")
        print("2. Try different filter configurations")
        print("3. Integrate telemetry into your agent implementations")
        
        # Cleanup
        main_logger.close()
        filter_logger.close()
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())