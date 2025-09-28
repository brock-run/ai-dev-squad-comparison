#!/usr/bin/env python3

"""
Simple integration test for Semantic Kernel adapter with real dependencies.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import common modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_semantic_kernel_adapter_integration():
    """Test Semantic Kernel adapter with real dependencies."""
    print("Testing Semantic Kernel Adapter Integration...")
    
    try:
        # Import the adapter
        from adapter import SemanticKernelAdapter, create_semantic_kernel_adapter, SEMANTIC_KERNEL_AVAILABLE, PLUGINS_AVAILABLE
        
        print(f"✓ Semantic Kernel available: {SEMANTIC_KERNEL_AVAILABLE}")
        print(f"✓ Plugins available: {PLUGINS_AVAILABLE}")
        
        # Test factory function with minimal config
        test_config = {
            'language': 'python',
            'ollama': {
                'host': 'http://localhost:11434',
                'model': 'llama3.1:8b'
            },
            'vcs': {
                'github': {
                    'enabled': True,
                    'token': 'test-token',
                    'owner': 'test-owner',
                    'repo': 'test-repo'
                }
            }
        }
        adapter = create_semantic_kernel_adapter(test_config)
        print(f"✓ Created adapter: {adapter.name} v{adapter.version}")
        
        # Test capabilities
        async def test_capabilities():
            capabilities = await adapter.get_capabilities()
            print(f"✓ Capabilities: {len(capabilities.get('features', []))} features")
            
            required_features = [
                'skill_based_architecture',
                'planner_integration',
                'safety_controls',
                'vcs_integration'
            ]
            
            for feature in required_features:
                if feature in capabilities.get('features', []):
                    print(f"  ✓ {feature}")
                else:
                    print(f"  ✗ {feature} missing")
            
            # Show skill architecture
            skill_arch = capabilities.get('skill_architecture', {})
            if skill_arch:
                print(f"  Skill Architecture:")
                for skill_name, skill_info in skill_arch.items():
                    print(f"    {skill_name}: {skill_info.get('role', 'Unknown role')}")
                    print(f"      Safety: {', '.join(skill_info.get('safety_controls', []))}")
            
            # Show planner features
            planner_features = capabilities.get('planner_features', {})
            if planner_features:
                print(f"  Planner: {planner_features.get('type', 'Unknown')}")
                print(f"    Capabilities: {', '.join(planner_features.get('capabilities', []))}")
            
            return capabilities
        
        # Test health check
        async def test_health():
            health = await adapter.health_check()
            print(f"✓ Health check: {health.get('status', 'unknown')}")
            
            components = health.get('components', {})
            for component, status in components.items():
                if isinstance(status, dict):
                    print(f"  {component}: {status.get('status', 'unknown')}")
                else:
                    print(f"  {component}: {status}")
            
            return health
        
        # Test basic task execution
        async def test_task_execution():
            print("Testing task execution...")
            
            try:
                # Convert task_data to TaskSchema
                from common.agent_api import TaskSchema, TaskType
                task_schema = TaskSchema(
                    id='test-task-1',
                    type=TaskType.FEATURE_ADD,
                    inputs={
                        'description': 'Create a simple calculator utility',
                        'requirements': [
                            'Function should support basic arithmetic operations',
                            'Include error handling for division by zero',
                            'Add comprehensive unit tests'
                        ],
                        'context': {}
                    },
                    repo_path='.',
                    vcs_provider='github'
                )
                
                # Iterate over the async generator
                result = None
                async for item in adapter.run_task(task_schema):
                    if hasattr(item, 'status'):  # This is a RunResult
                        result = {
                            'success': item.status.value in ['completed', 'success'],
                            'output': item.artifacts.get('output', {}),
                            'error': item.error_message,
                            'metadata': item.metadata
                        }
                        break
                
                if result:
                    print(f"✓ Task execution completed: {result.get('success', False)}")
                    
                    output = result.get('output', {})
                    metadata = result.get('metadata', {})
                    
                    if isinstance(output, dict):
                        if output.get('implementation'):
                            print(f"  Implementation generated: {len(output['implementation'])} chars")
                        
                        if output.get('tests'):
                            print(f"  Tests generated: {len(output['tests'])} chars")
                        
                        if output.get('skills_used'):
                            print(f"  Skills used: {', '.join(output['skills_used'])}")
                        
                        if output.get('plan_result'):
                            print(f"  Plan executed: {len(output['plan_result'])} chars")
                        
                        if output.get('fallback'):
                            print(f"  Used fallback workflow: {output['fallback']}")
                    
                    # Show metadata
                    if metadata.get('plans_created'):
                        print(f"  Plans created: {metadata['plans_created']}")
                    
                    if metadata.get('skills_executed'):
                        print(f"  Skills executed: {metadata['skills_executed']}")
                    
                    if metadata.get('planner_type'):
                        print(f"  Planner type: {metadata['planner_type']}")
                    
                else:
                    print("✗ No result received from task execution")
                
                return result
                
            except Exception as e:
                print(f"✗ Task execution failed: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Run async tests
        async def run_tests():
            print("\n--- Running Async Tests ---")
            
            capabilities = await test_capabilities()
            print()
            
            health = await test_health()
            print()
            
            task_result = await test_task_execution()
            print()
            
            return {
                'capabilities': capabilities,
                'health': health,
                'task_result': task_result
            }
        
        # Execute tests
        results = asyncio.run(run_tests())
        
        # Summary
        print("--- Test Summary ---")
        print(f"✓ Adapter created successfully")
        print(f"✓ Capabilities retrieved: {len(results['capabilities'].get('features', []))} features")
        print(f"✓ Health check: {results['health'].get('status', 'unknown')}")
        
        if results['task_result']:
            print(f"✓ Task execution: {'success' if results['task_result'].get('success') else 'failed'}")
        else:
            print(f"✗ Task execution failed")
        
        print("\n🎉 Semantic Kernel adapter integration test completed!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_semantic_kernel_adapter_integration()
    sys.exit(0 if success else 1)