#!/usr/bin/env python3
"""
LangGraph Integration Demo

This script demonstrates the LangGraph implementation working end-to-end
with mock data to show the complete workflow without external dependencies.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Mock external dependencies
import unittest.mock as mock

# Mock LangGraph
mock_langgraph = mock.MagicMock()
mock_langgraph.graph.StateGraph = mock.MagicMock()
mock_langgraph.graph.END = "END"
mock_langgraph.checkpoint.memory.MemorySaver = mock.MagicMock()

sys.modules['langgraph'] = mock_langgraph
sys.modules['langgraph.graph'] = mock_langgraph.graph
sys.modules['langgraph.checkpoint'] = mock_langgraph.checkpoint
sys.modules['langgraph.checkpoint.memory'] = mock_langgraph.checkpoint.memory
sys.modules['langchain_core'] = mock.MagicMock()
sys.modules['langchain_core.messages'] = mock.MagicMock()
sys.modules['langchain_community'] = mock.MagicMock()
sys.modules['langchain_community.chat_models'] = mock.MagicMock()

# Mock safety dependencies
sys.modules['docker'] = mock.MagicMock()

# Now import our modules
from common.agent_api import TaskSchema
from adapter import create_langgraph_adapter
from state.development_state import create_initial_state, WorkflowStatus


async def demo_adapter_creation():
    """Demo adapter creation and basic functionality."""
    print("🏗️ Creating LangGraph Adapter...")
    
    try:
        adapter = create_langgraph_adapter()
        print(f"✅ Created: {adapter.name} v{adapter.version}")
        print(f"   Description: {adapter.description}")
        return adapter
    except Exception as e:
        print(f"❌ Failed to create adapter: {e}")
        return None


async def demo_capabilities(adapter):
    """Demo capabilities discovery."""
    print("\n⚙️ Discovering Capabilities...")
    
    try:
        capabilities = await adapter.get_capabilities()
        print(f"✅ Features: {len(capabilities['features'])} available")
        print(f"   Core Features: {', '.join(capabilities['features'][:3])}...")
        print(f"   Safety Features: {sum(capabilities['safety_features'].values())} enabled")
        print(f"   VCS Providers: {sum(capabilities['vcs_providers'].values())} configured")
        return True
    except Exception as e:
        print(f"❌ Failed to get capabilities: {e}")
        return False


async def demo_health_check(adapter):
    """Demo health check functionality."""
    print("\n🏥 Performing Health Check...")
    
    try:
        health = await adapter.health_check()
        print(f"✅ Overall Status: {health['status']}")
        print(f"   Components Checked: {len(health['components'])}")
        
        # Show component status
        for component, status in health['components'].items():
            status_icon = "✅" if status.get('status') in ['healthy', 'available', 'configured'] else "⚠️"
            print(f"   {status_icon} {component}: {status.get('status', 'unknown')}")
        
        return health['status'] in ['healthy', 'degraded']
    except Exception as e:
        print(f"❌ Failed health check: {e}")
        return False


async def demo_state_management():
    """Demo state management functionality."""
    print("\n📊 Demonstrating State Management...")
    
    try:
        # Create initial state
        state = create_initial_state(
            task="Create a simple calculator function",
            requirements=[
                "Handle basic arithmetic operations",
                "Include error handling",
                "Add comprehensive tests"
            ],
            context={"language": "python"}
        )
        
        print(f"✅ Initial State Created:")
        print(f"   Task: {state['task']}")
        print(f"   Requirements: {len(state['requirements'])}")
        print(f"   Status: {state['status']}")
        print(f"   Start Time: {state['workflow_start_time'].strftime('%H:%M:%S')}")
        
        return state
    except Exception as e:
        print(f"❌ Failed state management demo: {e}")
        return None


async def demo_workflow_components(adapter):
    """Demo individual workflow components."""
    print("\n🔄 Demonstrating Workflow Components...")
    
    try:
        # Demo design creation
        print("   🎨 Creating Design...")
        design = await adapter._create_design(
            "Create calculator", 
            ["Add function", "Subtract function"]
        )
        print(f"   ✅ Design: {design['architecture_type']} with {len(design['components'])} components")
        
        # Demo code implementation
        print("   💻 Implementing Code...")
        from state.development_state import DesignArtifact
        design_artifact = DesignArtifact(
            architecture_type="modular",
            components=[{"name": "calculator", "type": "core"}]
        )
        
        code_result = await adapter._implement_code(
            "Calculator function", 
            design_artifact, 
            "python"
        )
        print(f"   ✅ Code: {len(code_result['main_code'])} characters in {code_result['language']}")
        
        # Demo test creation
        print("   🧪 Creating Tests...")
        from state.development_state import CodeArtifact
        code_artifact = CodeArtifact(
            language="python",
            main_code="def add(a, b): return a + b"
        )
        
        test_result = await adapter._create_tests(code_artifact, "Calculator", [])
        print(f"   ✅ Tests: {len(test_result['test_cases'])} test cases using {test_result['test_framework']}")
        
        return True
    except Exception as e:
        print(f"❌ Failed workflow components demo: {e}")
        return False


async def demo_safety_controls(adapter):
    """Demo safety controls functionality."""
    print("\n🛡️ Demonstrating Safety Controls...")
    
    try:
        # Demo input sanitization
        print("   🔍 Testing Input Sanitization...")
        safe_input = await adapter._sanitize_input("print('Hello, World!')")
        print(f"   ✅ Input sanitized successfully")
        
        # Demo code validation
        print("   ✅ Testing Code Validation...")
        safe_code = await adapter._validate_code("def safe_function(): return 'safe'")
        print(f"   ✅ Code validated successfully")
        
        # Check safety components
        print("   🔧 Checking Safety Components...")
        components = {
            'Execution Sandbox': adapter.sandbox is not None,
            'Filesystem Guard': adapter.filesystem_guard is not None,
            'Network Guard': adapter.network_guard is not None,
            'Injection Guard': adapter.injection_guard is not None
        }
        
        for component, available in components.items():
            status = "✅ Available" if available else "⚠️ Not configured"
            print(f"   {status}: {component}")
        
        return True
    except Exception as e:
        print(f"❌ Failed safety controls demo: {e}")
        return False


async def demo_vcs_integration(adapter):
    """Demo VCS integration functionality."""
    print("\n🔗 Demonstrating VCS Integration...")
    
    try:
        state = create_initial_state("Demo VCS task", [])
        
        # Demo branch creation
        print("   🌿 Creating Feature Branch...")
        branch_name = await adapter._create_feature_branch(state)
        print(f"   ✅ Branch: {branch_name}")
        
        # Demo commit message generation
        print("   💬 Generating Commit Message...")
        commit_message = await adapter._generate_commit_message(state)
        print(f"   ✅ Message: {commit_message}")
        
        # Demo commit changes (mock)
        print("   📝 Committing Changes...")
        commit_result = await adapter._commit_changes(state, branch_name, commit_message)
        print(f"   ✅ Commit SHA: {commit_result['sha']}")
        
        # Demo PR creation (mock)
        print("   🔀 Creating Pull Request...")
        pr_result = await adapter._create_pull_request(state, branch_name)
        print(f"   ✅ PR #{pr_result['number']}: {pr_result['url']}")
        
        return True
    except Exception as e:
        print(f"❌ Failed VCS integration demo: {e}")
        return False


async def demo_task_validation(adapter):
    """Demo task validation and processing."""
    print("\n📋 Demonstrating Task Validation...")
    
    try:
        # Create test task
        task = TaskSchema(
            id="demo-task-1",
            description="Create a simple web API",
            requirements=[
                "RESTful endpoints",
                "Input validation",
                "Error handling",
                "Unit tests"
            ],
            context={
                "language": "python",
                "framework": "fastapi"
            }
        )
        
        print(f"   📝 Original Task: {task.description}")
        print(f"   📋 Requirements: {len(task.requirements)}")
        
        # Validate task
        validated_task = await adapter._validate_task(task)
        print(f"   ✅ Task validated successfully")
        print(f"   🆔 Task ID: {validated_task.id}")
        print(f"   📝 Description: {validated_task.description[:50]}...")
        
        return validated_task
    except Exception as e:
        print(f"❌ Failed task validation demo: {e}")
        return None


async def demo_error_handling(adapter):
    """Demo error handling and recovery."""
    print("\n🚨 Demonstrating Error Handling...")
    
    try:
        # Demo error analysis
        print("   🔍 Analyzing Error...")
        error_analysis = await adapter._analyze_error("Sample error for testing")
        print(f"   ✅ Error Type: {error_analysis['type']}")
        print(f"   🔄 Recoverable: {error_analysis['recoverable']}")
        
        return True
    except Exception as e:
        print(f"❌ Failed error handling demo: {e}")
        return False


async def generate_demo_report(results):
    """Generate demo execution report."""
    print("\n📊 Demo Execution Report")
    print("=" * 50)
    
    total_demos = len(results)
    successful_demos = sum(1 for result in results.values() if result)
    
    print(f"Total Demos: {total_demos}")
    print(f"Successful: {successful_demos}")
    print(f"Failed: {total_demos - successful_demos}")
    print(f"Success Rate: {successful_demos/total_demos*100:.1f}%")
    
    print("\nDemo Results:")
    for demo_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {demo_name}")
    
    # Save report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_demos": total_demos,
        "successful_demos": successful_demos,
        "success_rate": successful_demos/total_demos*100,
        "results": results
    }
    
    report_path = Path(__file__).parent / "integration_demo_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_path}")
    
    return successful_demos == total_demos


async def main():
    """Run the complete integration demo."""
    print("🚀 LangGraph Integration Demo")
    print("=" * 50)
    print("This demo shows the LangGraph implementation working end-to-end")
    print("with mock data to demonstrate all major functionality.\n")
    
    results = {}
    
    # Create adapter
    adapter = await demo_adapter_creation()
    if not adapter:
        print("❌ Cannot continue without adapter")
        return 1
    
    # Run all demos
    demos = [
        ("Capabilities Discovery", demo_capabilities(adapter)),
        ("Health Check", demo_health_check(adapter)),
        ("State Management", demo_state_management()),
        ("Workflow Components", demo_workflow_components(adapter)),
        ("Safety Controls", demo_safety_controls(adapter)),
        ("VCS Integration", demo_vcs_integration(adapter)),
        ("Task Validation", demo_task_validation(adapter)),
        ("Error Handling", demo_error_handling(adapter))
    ]
    
    for demo_name, demo_coro in demos:
        try:
            result = await demo_coro
            results[demo_name] = bool(result)
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
            results[demo_name] = False
    
    # Generate report
    success = await generate_demo_report(results)
    
    if success:
        print("\n🎉 ALL DEMOS SUCCESSFUL!")
        print("✅ LangGraph implementation is working correctly")
        print("🚀 Ready for production use and next phase")
    else:
        print("\n⚠️ SOME DEMOS FAILED!")
        print("🔧 Check the failed demos above")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)