#!/usr/bin/env python3
"""
OpenTelemetry Integration Demo

This script demonstrates the comprehensive distributed tracing capabilities
of the AI Dev Squad platform, showing how OpenTelemetry integrates with
structured logging for complete observability.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from common.telemetry import (
    configure_logging,
    configure_tracing,
    get_logger,
    get_trace_manager,
    EventType,
    LogLevel,
    create_event,
    trace_function
)


@trace_function(operation_name="demo.calculate_fibonacci")
def calculate_fibonacci(n: int) -> int:
    """Calculate fibonacci number with tracing."""
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


@trace_function(operation_name="demo.process_data", attributes={"data.type": "user_input"})
def process_user_data(data: dict) -> dict:
    """Process user data with automatic tracing."""
    
    # Simulate data processing
    time.sleep(0.1)
    
    processed = {
        "original": data,
        "processed_at": time.time(),
        "status": "completed"
    }
    
    return processed


async def simulate_agent_workflow_with_tracing():
    """Simulate a complete agent workflow with both logging and tracing."""
    
    # Configure both logging and tracing
    logger = configure_logging(
        log_dir="otel_demo_logs",
        level=LogLevel.INFO,
        enable_console=True
    )
    
    trace_manager = configure_tracing(
        service_name="ai-dev-squad-demo",
        service_version="1.0.0",
        environment="demo",
        console_export=True  # This will show traces in console
    )
    
    # Set session context
    logger.set_session_context("otel_demo_session", "workflow_trace_123")
    
    print("🚀 Starting AI Dev Squad OpenTelemetry Demo")
    print("=" * 60)
    
    # 1. Agent Lifecycle with Tracing
    print("\n📋 Agent Lifecycle with Distributed Tracing...")
    
    with trace_manager.trace_agent_operation(
        agent_id="demo_agent_otel",
        framework="langgraph",
        operation="startup",
        attributes={
            "agent.type": "full_stack_developer",
            "agent.capabilities": ["coding", "testing", "debugging"]
        }
    ) as agent_span:
        
        # Log the agent start event
        logger.log_agent_start(
            agent_id="demo_agent_otel",
            agent_type="full_stack_developer",
            framework="langgraph",
            capabilities=["coding", "testing", "debugging"],
            config={"temperature": 0.7, "model": "llama3.1:8b"}
        )
        
        # Add trace ID to log context for correlation
        trace_id = trace_manager.get_current_trace_id()
        span_id = trace_manager.get_current_span_id()
        
        print(f"🔗 Trace ID: {trace_id}")
        print(f"🔗 Span ID: {span_id}")
        
        # 2. Task Execution with Nested Tracing
        print("\n📝 Task Execution with Nested Spans...")
        
        with trace_manager.trace_task_execution(
            task_id="otel_task_001",
            task_name="generate_api_with_tracing",
            agent_id="demo_agent_otel",
            framework="langgraph",
            attributes={
                "task.complexity": "medium",
                "task.estimated_duration": "5s"
            }
        ) as task_span:
            
            task_start_time = time.time()
            
            # Log task start
            logger.log_task_start(
                task_id="otel_task_001",
                task_name="generate_api_with_tracing",
                agent_id="demo_agent_otel",
                framework="langgraph",
                task_input={
                    "requirements": "Create FastAPI with tracing",
                    "language": "Python"
                }
            )
            
            # 3. Tool Calls with Tracing
            print("🔧 Tool Calls with Distributed Tracing...")
            
            with trace_manager.trace_tool_call(
                tool_name="code_generator",
                agent_id="demo_agent_otel",
                framework="langgraph",
                attributes={
                    "tool.version": "2.0",
                    "tool.language": "python"
                }
            ) as tool_span:
                
                # Simulate code generation
                await asyncio.sleep(1.0)
                
                # Log tool call
                logger.log_tool_call(
                    tool_name="code_generator",
                    agent_id="demo_agent_otel",
                    framework="langgraph",
                    tool_input={
                        "prompt": "Generate FastAPI code",
                        "style": "clean"
                    }
                )
                
                # Add custom event to span
                tool_event = create_event(
                    EventType.TOOL_RESULT,
                    tool_name="code_generator",
                    agent_id="demo_agent_otel",
                    framework="langgraph",
                    tool_output={
                        "files_generated": ["main.py", "models.py"],
                        "lines_of_code": 150
                    },
                    success=True,
                    message="Code generation completed"
                )
                
                trace_manager.add_event_to_current_span(tool_event, "tool.completion")
            
            # 4. LLM Interaction with Tracing
            print("🤖 LLM Interaction with Performance Tracking...")
            
            with trace_manager.trace_llm_interaction(
                model_name="llama3.1:8b",
                provider="ollama",
                agent_id="demo_agent_otel",
                attributes={
                    "llm.temperature": 0.7,
                    "llm.max_tokens": 1000,
                    "llm.prompt_type": "code_generation"
                }
            ) as llm_span:
                
                llm_start_time = time.time()
                
                # Simulate LLM call
                await asyncio.sleep(1.5)
                
                llm_duration = (time.time() - llm_start_time) * 1000
                
                # Log LLM interaction
                logger.log_llm_interaction(
                    model_name="llama3.1:8b",
                    provider="ollama",
                    prompt_tokens=200,
                    completion_tokens=150,
                    duration_ms=llm_duration,
                    cost_usd=0.0,
                    agent_id="demo_agent_otel"
                )
                
                # Add performance attributes to span
                llm_span.set_attribute("llm.prompt_tokens", 200)
                llm_span.set_attribute("llm.completion_tokens", 150)
                llm_span.set_attribute("llm.total_tokens", 350)
                llm_span.set_attribute("llm.cost_usd", 0.0)
            
            # 5. Safety Check with Tracing
            print("🛡️ Safety Checks with Security Tracing...")
            
            with trace_manager.trace_safety_check(
                policy_name="code_safety_policy",
                check_type="generated_code_scan",
                attributes={
                    "safety.scanner_version": "3.1",
                    "safety.rules_count": 150
                }
            ) as safety_span:
                
                # Simulate safety check
                await asyncio.sleep(0.3)
                
                # Log safety check (no violation)
                safety_event = create_event(
                    EventType.POLICY_CHECK,
                    policy_name="code_safety_policy",
                    message="Code safety check passed",
                    metadata={
                        "scan_duration_ms": 300,
                        "issues_found": 0,
                        "confidence_score": 0.95
                    }
                )
                
                trace_manager.add_event_to_current_span(safety_event, "safety.check_complete")
            
            # 6. VCS Operation with Tracing
            print("📚 VCS Operations with Repository Tracing...")
            
            with trace_manager.trace_vcs_operation(
                repository="ai-dev-squad-demo",
                operation="commit_and_push",
                branch="feature/otel-integration",
                attributes={
                    "vcs.provider": "github",
                    "vcs.files_count": 3
                }
            ) as vcs_span:
                
                # Simulate VCS operations
                await asyncio.sleep(0.5)
                
                # Log VCS commit
                vcs_event = create_event(
                    EventType.VCS_COMMIT,
                    repository="ai-dev-squad-demo",
                    branch="feature/otel-integration",
                    commit_hash="otel123abc456def",
                    operation="commit",
                    files_changed=["main.py", "models.py", "tests.py"],
                    message="Added OpenTelemetry integration"
                )
                
                logger.log_event(vcs_event)
                trace_manager.add_event_to_current_span(vcs_event, "vcs.commit_complete")
            
            # Complete task
            task_duration = (time.time() - task_start_time) * 1000
            
            logger.log_task_complete(
                task_id="otel_task_001",
                task_name="generate_api_with_tracing",
                agent_id="demo_agent_otel",
                framework="langgraph",
                duration_ms=task_duration,
                task_output={
                    "files_created": ["main.py", "models.py", "tests.py"],
                    "total_lines": 245,
                    "test_coverage": 92.5
                }
            )
        
        # 7. Function Tracing Demo
        print("\n🔄 Function-Level Tracing Demo...")
        
        # Use traced functions
        fib_result = calculate_fibonacci(8)
        print(f"Fibonacci(8) = {fib_result}")
        
        user_data = {"name": "demo_user", "action": "generate_code"}
        processed_data = process_user_data(user_data)
        print(f"Processed data: {processed_data['status']}")
        
        # Stop agent
        logger.log_agent_stop(
            agent_id="demo_agent_otel",
            framework="langgraph",
            duration_ms=(time.time() - task_start_time) * 1000
        )
    
    print("\n✅ OpenTelemetry Demo completed!")
    print(f"📁 Logs: otel_demo_logs/ai_dev_squad.jsonl")
    print(f"🔍 Traces: Check console output above")
    
    return logger, trace_manager


def demonstrate_trace_correlation():
    """Demonstrate trace correlation across multiple operations."""
    
    print("\n🔗 Demonstrating Trace Correlation")
    print("=" * 40)
    
    trace_manager = get_trace_manager()
    if not trace_manager:
        print("❌ No trace manager configured")
        return
    
    # Parent operation
    with trace_manager.trace_operation(
        operation_name="correlation_demo",
        attributes={"demo.type": "correlation"}
    ) as parent_span:
        
        parent_trace_id = trace_manager.get_current_trace_id()
        parent_span_id = trace_manager.get_current_span_id()
        
        print(f"🔗 Parent Trace ID: {parent_trace_id}")
        print(f"🔗 Parent Span ID: {parent_span_id}")
        
        # Child operations
        for i in range(3):
            with trace_manager.trace_operation(
                operation_name=f"child_operation_{i}",
                attributes={"child.index": i}
            ) as child_span:
                
                child_trace_id = trace_manager.get_current_trace_id()
                child_span_id = trace_manager.get_current_span_id()
                
                print(f"  🔗 Child {i} Trace ID: {child_trace_id}")
                print(f"  🔗 Child {i} Span ID: {child_span_id}")
                
                # Verify same trace ID
                assert parent_trace_id == child_trace_id, "Trace IDs should match"
                assert parent_span_id != child_span_id, "Span IDs should be different"
                
                # Simulate work
                time.sleep(0.1)
    
    print("✅ Trace correlation verified!")


def analyze_trace_output():
    """Analyze and display trace correlation information."""
    
    print("\n📊 Trace Analysis")
    print("=" * 25)
    
    trace_manager = get_trace_manager()
    if not trace_manager:
        print("❌ No trace manager configured")
        return
    
    print("🔍 Trace Context Information:")
    
    # Get current context (should be empty outside of spans)
    context = trace_manager.get_trace_context()
    print(f"  Current context: {context}")
    
    # Demonstrate context propagation
    with trace_manager.trace_operation("context_demo") as span:
        
        # Get context within span
        context = trace_manager.get_trace_context()
        trace_id = trace_manager.get_current_trace_id()
        span_id = trace_manager.get_current_span_id()
        
        print(f"  Active trace ID: {trace_id}")
        print(f"  Active span ID: {span_id}")
        print(f"  Propagation context: {len(context)} headers")
        
        # This context could be passed to other services
        if context:
            print("  📤 Context headers for propagation:")
            for key, value in context.items():
                print(f"    {key}: {value[:50]}...")


async def main():
    """Run the complete OpenTelemetry demo."""
    
    print("🎯 AI Dev Squad OpenTelemetry Integration Demo")
    print("=" * 70)
    
    try:
        # Run main workflow demo
        logger, trace_manager = await simulate_agent_workflow_with_tracing()
        
        # Demonstrate trace correlation
        demonstrate_trace_correlation()
        
        # Analyze trace output
        analyze_trace_output()
        
        print("\n🎉 All OpenTelemetry demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Distributed tracing with nested spans")
        print("✅ Trace correlation across operations")
        print("✅ Integration with structured logging")
        print("✅ Automatic function tracing")
        print("✅ Custom span attributes and events")
        print("✅ Performance tracking")
        print("✅ Context propagation")
        
        print("\nNext Steps:")
        print("1. Set up Jaeger or OTLP collector for trace visualization")
        print("2. Configure trace sampling for production")
        print("3. Add custom instrumentation to your agents")
        print("4. Use trace correlation for debugging")
        
        # Cleanup
        logger.close()
        trace_manager.shutdown()
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())