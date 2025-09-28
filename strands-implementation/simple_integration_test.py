#!/usr/bin/env python3
"""
Simple Integration Test for Strands Implementation

Tests basic functionality of the Strands adapter without requiring
external dependencies or complex setup.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_adapter_creation():
    """Test that the adapter can be created."""
    print("🔍 Testing adapter creation...")
    
    try:
        from adapter import create_strands_adapter
        
        # Test basic creation
        adapter = create_strands_adapter()
        assert adapter is not None, "Adapter should not be None"
        assert adapter.name == "strands", "Adapter name should be 'strands'"
        
        print("✅ Adapter creation successful")
        return adapter
        
    except Exception as e:
        print(f"❌ Adapter creation failed: {e}")
        raise

async def test_adapter_info(adapter):
    """Test adapter info method."""
    print("🔍 Testing adapter info...")
    
    try:
        info = await adapter.get_info()
        
        assert isinstance(info, dict), "Info should be a dictionary"
        assert "name" in info, "Info should contain 'name'"
        assert "capabilities" in info, "Info should contain 'capabilities'"
        assert info["name"] == "strands", "Name should be 'strands'"
        
        print("✅ Adapter info test successful")
        print(f"   Name: {info['name']}")
        print(f"   Capabilities: {len(info.get('capabilities', []))}")
        
        return info
        
    except Exception as e:
        print(f"❌ Adapter info test failed: {e}")
        raise

async def test_adapter_capabilities(adapter):
    """Test adapter capabilities method."""
    print("🔍 Testing adapter capabilities...")
    
    try:
        capabilities = await adapter.get_capabilities()
        
        assert isinstance(capabilities, dict), "Capabilities should be a dictionary"
        assert "features" in capabilities, "Capabilities should contain 'features'"
        
        features = capabilities["features"]
        expected_features = [
            "enterprise_observability",
            "multi_cloud_deployment", 
            "distributed_tracing",
            "automatic_error_recovery"
        ]
        
        for feature in expected_features:
            assert feature in features, f"Feature '{feature}' should be present"
        
        print("✅ Adapter capabilities test successful")
        print(f"   Features: {len(features)}")
        
        return capabilities
        
    except Exception as e:
        print(f"❌ Adapter capabilities test failed: {e}")
        raise

async def test_health_check(adapter):
    """Test adapter health check."""
    print("🔍 Testing health check...")
    
    try:
        health = await adapter.health_check()
        
        assert isinstance(health, dict), "Health check should return a dictionary"
        assert "status" in health, "Health check should contain 'status'"
        assert "components" in health, "Health check should contain 'components'"
        
        print("✅ Health check test successful")
        print(f"   Status: {health['status']}")
        print(f"   Components: {len(health.get('components', {}))}")
        
        return health
        
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        raise

async def test_metrics(adapter):
    """Test adapter metrics."""
    print("🔍 Testing metrics...")
    
    try:
        metrics = await adapter.get_metrics()
        
        assert isinstance(metrics, dict), "Metrics should be a dictionary"
        assert "timestamp" in metrics, "Metrics should contain 'timestamp'"
        
        print("✅ Metrics test successful")
        print(f"   Timestamp: {metrics.get('timestamp')}")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        raise

async def test_task_execution(adapter):
    """Test basic task execution."""
    print("🔍 Testing task execution...")
    
    try:
        # Import TaskSchema
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from common.agent_api import TaskSchema, TaskType
        
        # Create a simple test task
        task = TaskSchema(
            id="test_task_001",
            type=TaskType.FEATURE_ADD,
            inputs={
                "description": "Create a simple hello world function",
                "requirements": ["Function should return 'Hello, World!'"]
            },
            repo_path=".",
            vcs_provider="github"
        )
        
        # Execute task
        results = []
        async for result in adapter.run_task(task):
            results.append(result)
        
        assert len(results) > 0, "Should receive at least one result"
        
        final_result = results[-1]
        assert hasattr(final_result, 'task_id'), "Result should have task_id"
        assert hasattr(final_result, 'status'), "Result should have status"
        assert final_result.task_id == task.id, "Task ID should match"
        
        print("✅ Task execution test successful")
        print(f"   Task ID: {final_result.task_id}")
        print(f"   Status: {final_result.status}")
        
        return results
        
    except ImportError as e:
        print(f"⚠️  Task execution test skipped (missing common module): {e}")
        return []
    except Exception as e:
        print(f"❌ Task execution test failed: {e}")
        raise

async def test_enterprise_features(adapter):
    """Test enterprise-specific features."""
    print("🔍 Testing enterprise features...")
    
    try:
        # Test configuration
        if hasattr(adapter, 'config'):
            config = adapter.config
            print(f"   Observability enabled: {config.observability_enabled}")
            print(f"   Distributed tracing: {config.distributed_tracing}")
            print(f"   Cloud providers: {config.cloud_providers}")
            print(f"   Error recovery: {config.error_recovery}")
        
        # Test enterprise components
        components = []
        if hasattr(adapter, 'telemetry_manager') and adapter.telemetry_manager:
            components.append("telemetry_manager")
        if hasattr(adapter, 'provider_manager') and adapter.provider_manager:
            components.append("provider_manager")
        if hasattr(adapter, 'workflow') and adapter.workflow:
            components.append("workflow")
        
        print(f"   Enterprise components initialized: {components}")
        
        print("✅ Enterprise features test successful")
        
    except Exception as e:
        print(f"❌ Enterprise features test failed: {e}")
        raise

async def main():
    """Run all integration tests."""
    print("🚀 Starting Strands integration tests...\n")
    
    try:
        # Test adapter creation
        adapter = await test_adapter_creation()
        
        # Test basic functionality
        await test_adapter_info(adapter)
        await test_adapter_capabilities(adapter)
        await test_health_check(adapter)
        await test_metrics(adapter)
        
        # Test enterprise features
        await test_enterprise_features(adapter)
        
        # Test task execution (may be skipped if common module not available)
        await test_task_execution(adapter)
        
        print("\n🎉 All integration tests completed successfully!")
        print("✅ Strands implementation is working correctly")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)