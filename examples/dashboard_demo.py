#!/usr/bin/env python3
"""
Enhanced Dashboard Demo

This script demonstrates the comprehensive web-based dashboard with real-time
monitoring, parity matrix visualization, trace analysis, and cost optimization
for the AI Dev Squad platform.
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
    configure_cost_tracking,
    create_dashboard
)


def setup_demo_data():
    """Setup demo data for dashboard visualization."""
    
    print("🔧 Setting up demo data...")
    
    # Configure telemetry systems
    logger = configure_logging(
        log_dir="dashboard_demo_logs",
        enable_console=False
    )
    
    tracer = configure_tracing(
        service_name="dashboard-demo",
        console_export=False
    )
    
    cost_tracker = configure_cost_tracking(
        enable_real_time_tracking=True,
        enable_budget_alerts=True
    )
    
    # Setup budgets for demo
    cost_tracker.budget_manager.set_budget(
        name="daily_demo",
        limit_usd=10.0,
        period="daily",
        alert_thresholds=[0.5, 0.8, 0.9]
    )
    
    cost_tracker.budget_manager.set_budget(
        name="weekly_demo",
        limit_usd=50.0,
        period="weekly",
        alert_thresholds=[0.6, 0.8, 0.95]
    )
    
    # Generate some demo usage data
    print("📊 Generating demo usage data...")
    
    # Simulate various LLM interactions
    demo_scenarios = [
        # LangGraph usage
        {"model": "gpt-4", "provider": "openai", "input": 1500, "output": 800, "duration": 3000, "framework": "langgraph"},
        {"model": "gpt-3.5-turbo", "provider": "openai", "input": 800, "output": 400, "duration": 1500, "framework": "langgraph"},
        {"model": "llama3.1:8b", "provider": "ollama", "input": 2000, "output": 1000, "duration": 4000, "framework": "langgraph"},
        
        # CrewAI usage
        {"model": "claude-3-sonnet", "provider": "anthropic", "input": 1200, "output": 600, "duration": 2500, "framework": "crewai"},
        {"model": "gpt-3.5-turbo", "provider": "openai", "input": 600, "output": 300, "duration": 1200, "framework": "crewai"},
        {"model": "llama3.1:70b", "provider": "ollama", "input": 1800, "output": 900, "duration": 5000, "framework": "crewai"},
        
        # AutoGen usage
        {"model": "gpt-4", "provider": "openai", "input": 1000, "output": 500, "duration": 2000, "framework": "autogen"},
        {"model": "claude-3-haiku", "provider": "anthropic", "input": 400, "output": 200, "duration": 800, "framework": "autogen"},
        
        # LlamaIndex usage
        {"model": "gpt-3.5-turbo", "provider": "openai", "input": 1500, "output": 750, "duration": 2200, "framework": "llamaindex"},
        {"model": "llama3.1:8b", "provider": "ollama", "input": 2500, "output": 1200, "duration": 6000, "framework": "llamaindex"},
        
        # Haystack usage
        {"model": "claude-3-sonnet", "provider": "anthropic", "input": 900, "output": 450, "duration": 1800, "framework": "haystack"},
        {"model": "gpt-4", "provider": "openai", "input": 1200, "output": 600, "duration": 2800, "framework": "haystack"},
    ]
    
    for i, scenario in enumerate(demo_scenarios):
        cost_tracker.track_llm_usage(
            model_name=scenario["model"],
            provider=scenario["provider"],
            input_tokens=scenario["input"],
            output_tokens=scenario["output"],
            duration_ms=scenario["duration"],
            session_id=f"demo_session_{i // 3}",
            agent_id=f"demo_agent_{i % 4}",
            task_id=f"demo_task_{i}",
            framework=scenario["framework"]
        )
    
    print(f"✅ Generated {len(demo_scenarios)} demo interactions")
    
    return logger, tracer, cost_tracker


async def run_dashboard_demo():
    """Run the enhanced dashboard demo."""
    
    print("🚀 AI Dev Squad Enhanced Dashboard Demo")
    print("=" * 60)
    
    try:
        # Setup demo data
        logger, tracer, cost_tracker = setup_demo_data()
        
        # Create and configure dashboard
        print("\n🌐 Starting Enhanced Dashboard...")
        
        dashboard = create_dashboard(
            host="localhost",
            port=8080,
            debug=True
        )
        
        print("\n📊 Dashboard Features:")
        print("  ✅ Real-time metrics and monitoring")
        print("  ✅ Framework parity matrix comparison")
        print("  ✅ Distributed trace visualization")
        print("  ✅ Cost analysis and optimization")
        print("  ✅ Drill-down capabilities")
        print("  ✅ Interactive charts and graphs")
        
        print("\n🔗 Dashboard URLs:")
        print("  📈 Main Dashboard: http://localhost:8080/")
        print("  📊 Parity Matrix: http://localhost:8080/parity-matrix")
        print("  🔍 Trace Analysis: http://localhost:8080/traces")
        print("  💰 Cost Analysis: http://localhost:8080/cost-analysis")
        
        print("\n🎯 API Endpoints:")
        print("  📊 Metrics: http://localhost:8080/api/metrics")
        print("  📋 Parity Matrix: http://localhost:8080/api/parity-matrix")
        print("  🔍 Traces: http://localhost:8080/api/traces")
        print("  💰 Cost Analysis: http://localhost:8080/api/cost-analysis")
        
        print("\n" + "=" * 60)
        print("🚀 Dashboard is starting...")
        print("📱 Open your browser to http://localhost:8080")
        print("⏹️  Press Ctrl+C to stop the dashboard")
        print("=" * 60)
        
        # Start the dashboard (this will block)
        dashboard.run()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Dashboard stopped by user")
        
        # Cleanup
        if 'logger' in locals():
            logger.close()
        if 'tracer' in locals():
            tracer.shutdown()
            
    except ImportError as e:
        print(f"\n❌ Dashboard dependencies missing: {e}")
        print("\n📦 To install dashboard dependencies, run:")
        print("   pip install flask flask-socketio")
        
    except Exception as e:
        print(f"\n❌ Dashboard demo failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    
    # Check if Flask is available
    try:
        import flask
        import flask_socketio
    except ImportError:
        print("❌ Dashboard requires Flask and Flask-SocketIO")
        print("\n📦 Install dependencies with:")
        print("   pip install flask flask-socketio")
        print("\n🔄 Then run the demo again")
        return
    
    # Run the demo
    asyncio.run(run_dashboard_demo())


if __name__ == "__main__":
    main()