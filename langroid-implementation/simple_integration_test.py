#!/usr/bin/env python3

"""
Simple integration test for Langroid adapter with real dependencies.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import common modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_langroid_adapter_integration():
    """Test Langroid adapter with real dependencies."""
    print("Testing Langroid Adapter Integration...")
    
    try:
        # Import the adapter
        from adapter import LangroidAdapter, create_langroid_adapter, LANGROID_AVAILABLE, AGENTS_AVAILABLE
        
        print(f"✓ Langroid available: {LANGROID_AVAILABLE}")
        print(f"✓ Agents available: {AGENTS_AVAILABLE}")
        
        # Test factory function with minimal config
        test_config = {
            'language': 'python',
            'langroid': {
                'model': 'gpt-3.5-turbo'
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
        adapter = create_langroid_adapter(test_config)
        print(f"✓ Created adapter: {adapter.name} v{adapter.version}")
        
        # Test capabilities
        async def test_capabilities():
            capabilities = await adapter.get_capabilities()
            print(f"✓ Capabilities: {len(capabilities.get('features', []))} features")
            
            required_features = [
                'conversation_style_interactions',
                'turn_taking_logic',
                'agent_role_specialization',
                'multi_agent_conversations'
            ]
            
            for feature in required_features:
                if feature in capabilities.get('features', []):
                    print(f"  ✓ {feature}")
                else:
                    print(f"  ✗ {feature} missing")
            
            # Show agent architecture
            agent_arch = capabilities.get('agent_architecture', {})
            if agent_arch:
                print(f"  Agent Architecture:")
                for agent_name, agent_info in agent_arch.items():
                    print(f"    {agent_name}: {agent_info.get('role', 'Unknown role')}")
                    print(f"      Style: {agent_info.get('conversation_style', 'Unknown')}")
            
            # Show conversation features
            conv_features = capabilities.get('conversation_features', {})
            if conv_features:
                print(f"  Conversation Features:")
                for feature, enabled in conv_features.items():
                    print(f"    {feature}: {enabled}")
            
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
                        'description': 'Create a simple data processing pipeline',
                        'requirements': [
                            'Pipeline should process CSV data files',
                            'Include data validation and error handling',
                            'Add logging and monitoring capabilities'
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
                        
                        if output.get('agents_used'):
                            print(f"  Agents used: {', '.join(output['agents_used'])}")
                        
                        if output.get('conversation_log'):
                            print(f"  Conversation log: {len(output['conversation_log'])} chars")
                        
                        if output.get('conversation_turns'):
                            print(f"  Conversation turns: {output['conversation_turns']}")
                        
                        if output.get('fallback'):
                            print(f"  Used fallback workflow: {output['fallback']}")
                    
                    # Show metadata
                    if metadata.get('conversation_turns'):
                        print(f"  Conversation turns: {metadata['conversation_turns']}")
                    
                    if metadata.get('agent_interactions'):
                        print(f"  Agent interactions: {metadata['agent_interactions']}")
                    
                    if metadata.get('turn_taking_events'):
                        print(f"  Turn-taking events: {metadata['turn_taking_events']}")
                    
                    if metadata.get('conversation_style'):
                        print(f"  Conversation style: {metadata['conversation_style']}")
                    
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
        
        print("\n🎉 Langroid adapter integration test completed!")
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
    success = test_langroid_adapter_integration()
    sys.exit(0 if success else 1)