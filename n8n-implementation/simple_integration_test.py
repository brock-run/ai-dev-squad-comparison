#!/usr/bin/env python3
"""
Simple integration test for n8n adapter with real dependencies.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import common modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_n8n_adapter_integration():
    """Test n8n adapter with real dependencies."""
    print("Testing n8n Adapter Integration...")
    
    try:
        # Import the adapter
        from adapter import N8nAdapter, create_n8n_adapter, N8N_AVAILABLE
        
        print(f"✓ n8n dependencies available: {N8N_AVAILABLE}")
        
        # Test factory function with minimal config
        test_config = {
            'language': 'python',
            'n8n': {
                'base_url': 'http://localhost:5678',
                'workflow_id': 'development-workflow'
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
        adapter = create_n8n_adapter(test_config)
        print(f"✓ Created adapter: {adapter.name} v{adapter.version}")
        
        # Test capabilities
        async def test_capabilities():
            capabilities = await adapter.get_capabilities()
            print(f"✓ Capabilities: {len(capabilities.get('features', []))} features")
            
            required_features = [
                'visual_workflow_design',
                'api_driven_execution',
                'custom_development_nodes',
                'workflow_export_import'
            ]
            
            for feature in required_features:
                if feature in capabilities.get('features', []):
                    print(f"  ✓ {feature}")
                else:
                    print(f"  ✗ {feature} missing")
            
            return capabilities
        
        # Test health check
        async def test_health():
            health = await adapter.health_check()
            print(f"✓ Health check: {health.get('status', 'unknown')}")
            
            components = health.get('components', {})
            for component, status in components.items():
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
                        'description': 'Create a simple data processing function',
                        'requirements': ['Function should process CSV data', 'Include error handling'],
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
                    if isinstance(output, dict):
                        if output.get('implementation'):
                            print(f"  Implementation generated: {len(output['implementation'])} chars")
                        
                        if output.get('tests'):
                            print(f"  Tests generated: {len(output['tests'])} chars")
                        
                        if output.get('nodes_executed'):
                            print(f"  Nodes executed: {len(output['nodes_executed'])}")
                        
                        if output.get('fallback'):
                            print(f"  Used fallback workflow: {output['fallback']}")
                    else:
                        print(f"  Output is not a dict: {type(output)}")
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
        
        print("\n🎉 n8n adapter integration test completed!")
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
    success = test_n8n_adapter_integration()
    sys.exit(0 if success else 1)