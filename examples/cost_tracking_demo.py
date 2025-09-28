#!/usr/bin/env python3
"""
Cost and Token Tracking Demo

This script demonstrates the comprehensive cost tracking and token counting
capabilities of the AI Dev Squad platform, showing real-time cost monitoring,
budget management, usage analytics, and optimization recommendations.
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from common.telemetry import (
    configure_logging,
    configure_tracing,
    configure_cost_tracking,
    get_cost_tracker,
    ModelProvider,
    ModelPricing
)


def setup_custom_pricing():
    """Setup custom pricing models for the demo."""
    
    cost_tracker = get_cost_tracker()
    
    # Add some custom pricing models
    cost_tracker.add_pricing_model(ModelPricing(
        model_name="custom-gpt-4",
        provider=ModelProvider.OPENAI,
        input_cost_per_1k_tokens=0.025,
        output_cost_per_1k_tokens=0.05,
        context_window=8192,
        max_output_tokens=4096
    ))
    
    cost_tracker.add_pricing_model(ModelPricing(
        model_name="claude-3-haiku",
        provider=ModelProvider.ANTHROPIC,
        input_cost_per_1k_tokens=0.00025,
        output_cost_per_1k_tokens=0.00125,
        context_window=200000,
        max_output_tokens=4096
    ))
    
    print("✅ Custom pricing models added")


def setup_budgets():
    """Setup budget monitoring for the demo."""
    
    cost_tracker = get_cost_tracker()
    
    # Set up different budgets
    cost_tracker.budget_manager.set_budget(
        name="daily_development",
        limit_usd=5.0,
        period="daily",
        alert_thresholds=[0.5, 0.75, 0.9]
    )
    
    cost_tracker.budget_manager.set_budget(
        name="weekly_testing",
        limit_usd=20.0,
        period="weekly",
        alert_thresholds=[0.6, 0.8, 0.95]
    )
    
    cost_tracker.budget_manager.set_budget(
        name="monthly_total",
        limit_usd=100.0,
        period="monthly",
        alert_thresholds=[0.7, 0.85, 0.95]
    )
    
    print("✅ Budget monitoring configured")
    print("  📊 Daily development budget: $5.00")
    print("  📊 Weekly testing budget: $20.00")
    print("  📊 Monthly total budget: $100.00")


def demonstrate_cost_estimation():
    """Demonstrate cost estimation for different scenarios."""
    
    print("\n💰 Cost Estimation Demo")
    print("=" * 40)
    
    cost_tracker = get_cost_tracker()
    
    # Different types of prompts
    prompts = [
        {
            "name": "Simple Question",
            "text": "What is the capital of France?",
            "model": "gpt-3.5-turbo",
            "provider": "openai"
        },
        {
            "name": "Code Generation",
            "text": """
            Create a Python function that implements a binary search algorithm.
            The function should take a sorted list and a target value as parameters,
            and return the index of the target if found, or -1 if not found.
            Include proper error handling and documentation.
            """,
            "model": "gpt-4",
            "provider": "openai"
        },
        {
            "name": "Long Analysis",
            "text": """
            Analyze the following business scenario and provide recommendations:
            
            A mid-sized software company is considering migrating their monolithic
            application to a microservices architecture. They have 50 developers,
            serve 100,000 active users, and process 1 million transactions per day.
            Current system uses Java Spring Boot with PostgreSQL database.
            
            Consider factors like: development complexity, operational overhead,
            scalability benefits, cost implications, team structure changes,
            deployment strategies, monitoring requirements, and timeline.
            
            Provide a detailed analysis with pros/cons and step-by-step migration plan.
            """,
            "model": "claude-3-opus",
            "provider": "anthropic"
        },
        {
            "name": "Local Model Query",
            "text": "Explain the concept of machine learning in simple terms.",
            "model": "llama3.1:8b",
            "provider": "ollama"
        }
    ]
    
    for prompt_info in prompts:
        print(f"\n📝 {prompt_info['name']}")
        print(f"   Model: {prompt_info['model']} ({prompt_info['provider']})")
        
        estimate = cost_tracker.estimate_cost(
            text=prompt_info["text"],
            model_name=prompt_info["model"],
            provider=prompt_info["provider"]
        )
        
        print(f"   Input tokens: {estimate['input_tokens']}")
        print(f"   Estimated output tokens: {estimate['estimated_output_tokens']}")
        print(f"   Total tokens: {estimate['total_tokens']}")
        
        if estimate["pricing_available"]:
            print(f"   💵 Estimated cost: ${estimate['estimated_cost_usd']:.6f}")
            
            model_info = estimate["model_info"]
            print(f"   📊 Input cost: ${model_info['input_cost_per_1k']:.6f}/1k tokens")
            print(f"   📊 Output cost: ${model_info['output_cost_per_1k']:.6f}/1k tokens")
        else:
            print("   💵 Free (local model)")


async def simulate_llm_usage():
    """Simulate various LLM usage scenarios."""
    
    print("\n🤖 Simulating LLM Usage Scenarios")
    print("=" * 45)
    
    cost_tracker = get_cost_tracker()
    
    # Scenario 1: Development workflow
    print("\n📋 Scenario 1: Development Workflow")
    
    scenarios = [
        {
            "description": "Code review request",
            "model": "gpt-3.5-turbo",
            "provider": "openai",
            "input_tokens": 800,
            "output_tokens": 300,
            "duration_ms": 1500,
            "session_id": "dev_session_1",
            "agent_id": "code_reviewer",
            "task_id": "review_001"
        },
        {
            "description": "Bug fix generation",
            "model": "gpt-4",
            "provider": "openai",
            "input_tokens": 1200,
            "output_tokens": 600,
            "duration_ms": 3000,
            "session_id": "dev_session_1",
            "agent_id": "developer",
            "task_id": "bugfix_001"
        },
        {
            "description": "Test case generation",
            "model": "gpt-3.5-turbo",
            "provider": "openai",
            "input_tokens": 600,
            "output_tokens": 400,
            "duration_ms": 1200,
            "session_id": "dev_session_1",
            "agent_id": "tester",
            "task_id": "test_001"
        }
    ]
    
    for scenario in scenarios:
        print(f"  🔧 {scenario['description']}")
        
        cost_entry = cost_tracker.track_llm_usage(
            model_name=scenario["model"],
            provider=scenario["provider"],
            input_tokens=scenario["input_tokens"],
            output_tokens=scenario["output_tokens"],
            duration_ms=scenario["duration_ms"],
            session_id=scenario["session_id"],
            agent_id=scenario["agent_id"],
            task_id=scenario["task_id"],
            framework="langgraph"
        )
        
        print(f"     💵 Cost: ${cost_entry.cost_usd:.6f}")
        print(f"     🕒 Duration: {cost_entry.duration_ms:.0f}ms")
        
        await asyncio.sleep(0.1)  # Small delay for realism
    
    # Scenario 2: High-volume testing
    print("\n📋 Scenario 2: High-Volume Testing")
    
    for i in range(5):
        cost_entry = cost_tracker.track_llm_usage(
            model_name="claude-3-sonnet",
            provider="anthropic",
            input_tokens=500 + (i * 100),
            output_tokens=200 + (i * 50),
            duration_ms=1000 + (i * 200),
            session_id="test_session_2",
            agent_id="qa_agent",
            task_id=f"qa_test_{i+1}",
            framework="crewai"
        )
        
        print(f"  🧪 Test {i+1}: ${cost_entry.cost_usd:.6f} ({cost_entry.tokens.total_tokens} tokens)")
        await asyncio.sleep(0.05)
    
    # Scenario 3: Local model usage (free)
    print("\n📋 Scenario 3: Local Model Usage")
    
    for i in range(3):
        cost_entry = cost_tracker.track_llm_usage(
            model_name="llama3.1:8b",
            provider="ollama",
            input_tokens=1000 + (i * 200),
            output_tokens=500 + (i * 100),
            duration_ms=2000 + (i * 500),
            session_id="local_session_3",
            agent_id="local_agent",
            task_id=f"local_task_{i+1}",
            framework="ollama"
        )
        
        print(f"  🏠 Local query {i+1}: Free ({cost_entry.tokens.total_tokens} tokens)")
        await asyncio.sleep(0.1)


def demonstrate_budget_monitoring():
    """Demonstrate budget monitoring and alerts."""
    
    print("\n📊 Budget Monitoring Demo")
    print("=" * 35)
    
    cost_tracker = get_cost_tracker()
    
    # Check initial budget status
    print("\n💰 Initial Budget Status:")
    for budget_name in ["daily_development", "weekly_testing", "monthly_total"]:
        status = cost_tracker.budget_manager.get_budget_status(budget_name)
        if status:
            print(f"  📈 {status['name']}: ${status['current_spend']:.4f} / ${status['limit_usd']:.2f} "
                  f"({status['spend_ratio']:.1%})")
    
    # Simulate some expensive operations to trigger alerts
    print("\n🚨 Simulating expensive operations...")
    
    # Add expensive GPT-4 usage
    for i in range(3):
        cost_entry = cost_tracker.track_llm_usage(
            model_name="gpt-4",
            provider="openai",
            input_tokens=2000,
            output_tokens=1500,
            duration_ms=4000,
            session_id="expensive_session",
            agent_id="expensive_agent",
            task_id=f"expensive_task_{i+1}"
        )
        
        print(f"  💸 Expensive operation {i+1}: ${cost_entry.cost_usd:.4f}")
        
        # Update budgets manually for demo (normally automatic)
        cost_tracker.budget_manager.add_spend("daily_development", cost_entry.cost_usd)
        cost_tracker.budget_manager.add_spend("weekly_testing", cost_entry.cost_usd)
        cost_tracker.budget_manager.add_spend("monthly_total", cost_entry.cost_usd)
    
    # Check updated budget status
    print("\n💰 Updated Budget Status:")
    for budget_name in ["daily_development", "weekly_testing", "monthly_total"]:
        status = cost_tracker.budget_manager.get_budget_status(budget_name)
        if status:
            print(f"  📈 {status['name']}: ${status['current_spend']:.4f} / ${status['limit_usd']:.2f} "
                  f"({status['spend_ratio']:.1%})")
            if status['alerts_sent']:
                print(f"     🚨 Alerts sent at: {[f'{t:.0%}' for t in status['alerts_sent']]}")


def demonstrate_usage_analytics():
    """Demonstrate usage analytics and reporting."""
    
    print("\n📈 Usage Analytics Demo")
    print("=" * 30)
    
    cost_tracker = get_cost_tracker()
    
    # Overall summary
    print("\n📊 Overall Usage Summary:")
    total_summary = cost_tracker.get_usage_summary(group_by="total")
    
    if total_summary["total_entries"] > 0:
        summary = total_summary["summary"]
        print(f"  📝 Total requests: {summary['total_requests']}")
        print(f"  🎯 Total tokens: {summary['total_tokens']:,}")
        print(f"  📥 Input tokens: {summary['total_input_tokens']:,}")
        print(f"  📤 Output tokens: {summary['total_output_tokens']:,}")
        print(f"  💵 Total cost: ${summary['total_cost_usd']:.6f}")
        print(f"  ⏱️  Total duration: {summary['total_duration_ms']:.0f}ms")
        print(f"  📊 Avg cost/request: ${summary['average_cost_per_request']:.6f}")
        print(f"  📊 Cost per 1k tokens: ${summary['cost_per_1k_tokens']:.6f}")
    
    # By model breakdown
    print("\n📊 Usage by Model:")
    model_summary = cost_tracker.get_usage_summary(group_by="model")
    
    if model_summary["total_entries"] > 0:
        for model, stats in model_summary["summary"].items():
            print(f"  🤖 {model}:")
            print(f"     Requests: {stats['requests']}")
            print(f"     Tokens: {stats['tokens']:,}")
            print(f"     Cost: ${stats['cost_usd']:.6f}")
            print(f"     Avg duration: {stats['duration_ms']/stats['requests']:.0f}ms")
    
    # By provider breakdown
    print("\n📊 Usage by Provider:")
    provider_summary = cost_tracker.get_usage_summary(group_by="provider")
    
    if provider_summary["total_entries"] > 0:
        for provider, stats in provider_summary["summary"].items():
            print(f"  🏢 {provider.upper()}:")
            print(f"     Requests: {stats['requests']}")
            print(f"     Tokens: {stats['tokens']:,}")
            print(f"     Cost: ${stats['cost_usd']:.6f}")
            if stats['cost_usd'] > 0:
                print(f"     Cost per 1k tokens: ${(stats['cost_usd']/stats['tokens'])*1000:.6f}")


def demonstrate_optimization_recommendations():
    """Demonstrate cost optimization recommendations."""
    
    print("\n🎯 Cost Optimization Recommendations")
    print("=" * 45)
    
    cost_tracker = get_cost_tracker()
    recommendations = cost_tracker.get_cost_optimization_recommendations()
    
    if recommendations:
        print(f"\n💡 Found {len(recommendations)} optimization opportunities:")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['type'].replace('_', ' ').title()}")
            print(f"   Priority: {rec['priority'].upper()}")
            print(f"   Description: {rec['description']}")
            
            if rec['type'] == 'model_substitution':
                print(f"   Current model: {rec['current_model']}")
                print(f"   Suggested model: {rec['suggested_model']}")
                print(f"   Potential savings: ${rec['potential_savings_usd']:.2f}")
            elif rec['type'] == 'local_deployment':
                print(f"   Current API cost: ${rec['current_cost']:.2f}")
                print(f"   Suggested solution: {rec['suggested_solution']}")
                print(f"   Potential savings: ${rec['potential_savings_usd']:.2f}")
            elif rec['type'] == 'prompt_optimization':
                print(f"   Current avg input tokens: {rec['current_avg_input_tokens']}")
                print(f"   Suggested reduction: {rec['suggested_reduction']}")
                print(f"   Potential savings: ${rec['potential_savings_usd']:.2f}")
    else:
        print("\n✅ No optimization recommendations at this time.")
        print("   Your usage patterns look efficient!")


def demonstrate_data_export():
    """Demonstrate usage data export capabilities."""
    
    print("\n📁 Data Export Demo")
    print("=" * 25)
    
    cost_tracker = get_cost_tracker()
    
    # Export to JSON
    json_file = "demo_usage_data.json"
    cost_tracker.export_usage_data(json_file, format="json")
    print(f"✅ Exported usage data to {json_file}")
    
    # Show sample of exported data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print(f"   📊 Total entries: {data['total_entries']}")
    print(f"   📅 Export timestamp: {data['export_timestamp']}")
    
    if data['entries']:
        sample_entry = data['entries'][0]
        print(f"   📝 Sample entry:")
        print(f"      Model: {sample_entry['model_name']}")
        print(f"      Provider: {sample_entry['provider']}")
        print(f"      Tokens: {sample_entry['total_tokens']}")
        print(f"      Cost: ${sample_entry['cost_usd']:.6f}")
    
    # Export to CSV
    csv_file = "demo_usage_data.csv"
    cost_tracker.export_usage_data(csv_file, format="csv")
    print(f"✅ Exported usage data to {csv_file}")
    
    # Show CSV structure
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    
    print(f"   📊 CSV rows: {len(lines)} (including header)")
    print(f"   📋 Columns: {lines[0].strip()}")


async def main():
    """Run the complete cost tracking demo."""
    
    print("💰 AI Dev Squad Cost and Token Tracking Demo")
    print("=" * 70)
    
    try:
        # Configure telemetry systems
        logger = configure_logging(
            log_dir="cost_demo_logs",
            enable_console=False  # Reduce noise for demo
        )
        
        tracer = configure_tracing(
            service_name="cost-tracking-demo",
            console_export=False  # Reduce noise for demo
        )
        
        cost_tracker = configure_cost_tracking(
            enable_real_time_tracking=True,
            enable_budget_alerts=True
        )
        
        print("✅ Telemetry systems configured")
        
        # Setup demo environment
        setup_custom_pricing()
        setup_budgets()
        
        # Run demonstrations
        demonstrate_cost_estimation()
        await simulate_llm_usage()
        demonstrate_budget_monitoring()
        demonstrate_usage_analytics()
        demonstrate_optimization_recommendations()
        demonstrate_data_export()
        
        print("\n🎉 Cost Tracking Demo Completed Successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Real-time cost calculation and tracking")
        print("✅ Token counting for multiple model types")
        print("✅ Budget monitoring with threshold alerts")
        print("✅ Comprehensive usage analytics")
        print("✅ Cost optimization recommendations")
        print("✅ Data export in multiple formats")
        print("✅ Integration with structured logging")
        
        print("\nNext Steps:")
        print("1. Integrate cost tracking into your agent implementations")
        print("2. Set up appropriate budgets for your use cases")
        print("3. Monitor usage patterns and optimize costs")
        print("4. Use exported data for detailed analysis")
        
        # Cleanup
        logger.close()
        tracer.shutdown()
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())