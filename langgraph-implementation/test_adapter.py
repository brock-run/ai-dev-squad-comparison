#!/usr/bin/env python3
"""
Test script for LangGraph Adapter

This script tests the basic functionality of the LangGraph adapter
without requiring external dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from common.agent_api import TaskSchema
from adapter import create_langgraph_adapter


async def test_adapter_creation():
    """Test adapter creation and basic functionality."""
    print("Testing LangGraph Adapter Creation...")
    
    try:
        # Create adapter
        adapter = create_langgraph_adapter()
        print(f"✓ Adapter created: {adapter.name} v{adapter.version}")
        
        # Test capabilities
        capabilities = await adapter.get_capabilities()
        print(f"✓ Capabilities retrieved: {len(capabilities['features'])} features")
        
        # Test health check
        health = await adapter.health_check()
        print(f"✓ Health check: {health['status']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Adapter creation failed: {e}")
        return False


async def test_task_execution():
    """Test task execution (mock)."""
    print("\nTesting Task Execution...")
    
    try:
        # Create adapter
        adapter = create_langgraph_adapter()
        
        # Create test task
        task = TaskSchema(
            id="test-task-1",
            description="Create a simple calculator function",
            requirements=[
                "Function should handle basic arithmetic operations",
                "Include proper error handling",
                "Add comprehensive tests"
            ],
            context={"language": "python"}
        )
        
        print(f"✓ Task created: {task.description}")
        
        # Note: We can't actually run the task without LangGraph installed
        # But we can test the validation
        validated_task = await adapter._validate_task(task)
        print(f"✓ Task validation passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Task execution test failed: {e}")
        return False


async def test_safety_components():
    """Test safety component initialization."""
    print("\nTesting Safety Components...")
    
    try:
        adapter = create_langgraph_adapter()
        
        # Test input sanitization
        safe_input = await adapter._sanitize_input("print('hello world')")
        print(f"✓ Input sanitization works")
        
        # Test code validation
        validated_code = await adapter._validate_code("def add(a, b): return a + b")
        print(f"✓ Code validation works")
        
        return True
        
    except Exception as e:
        print(f"✗ Safety components test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("LangGraph Adapter Test Suite")
    print("=" * 40)
    
    tests = [
        test_adapter_creation,
        test_task_execution,
        test_safety_components
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 40)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)