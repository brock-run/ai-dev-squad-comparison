#!/usr/bin/env python3

"""
Simple integration test for Claude Code Subagents adapter with real dependencies.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import common modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_claude_subagents_adapter_integration():
    """Test Claude subagents adapter with real dependencies."""
    print("Testing Claude Code Subagents Adapter Integration...")
    
    try:
        # Import the adapter
        from adapter import ClaudeSubagentsAdapter, create_claude_subagents_adapter, CLAUDE_AVAILABLE, SUBAGENTS_AVAILABLE
        
        print(f"✓ Claude API available: {CLAUDE_AVAILABLE}")
        print(f"✓ Subagents available: {SUBAGENTS_AVAILABLE}")
        
        # Test factory function with minimal config
        test_config = {
            'language': 'python',
            'claude': {
                'model': 'claude-3-sonnet-20240229'
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
        adapter = create_claude_subagents_adapter(test_config)
        print(f"✓ Created adapter: {adapter.name} v{adapter.version}")
        
        # Test capabilities
        async def test_capabilities():
            capabilities = await adapter.get_capabilities()
            print(f"✓ Capabilities: {len(capabilities.get('features', []))} features")
            
            required_features = [
                'tool_restricted_subagents',
                'orchestrated_collaboration',
                'claude_api_integration',
                'fine_grained_tool_access'
            ]
            
            for feature in required_features:
                if feature in capabilities.get('features', []):
                    print(f"  ✓ {feature}")
                else:
                    print(f"  ✗ {feature} missing")
            
            # Show subagent architecture
            subagent_arch = capabilities.get('subagent_architecture', {})
            if subagent_arch:
                print(f"  Subagent Architecture:")
                for agent_name, agent_info in subagent_arch.items():
                    print(f"    {agent_name}: {agent_info.get('role', 'Unknown role')}")
                    print(f"      Tools: {', '.join(agent_info.get('allowed_tools', []))}")
            
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
                        'description': 'Create a simple file processing utility',
                        'requirements': [
                            'Function should read and process text files',
                            'Include error handling for file operations',
                            'Add comprehensive logging'
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
                        
                        if output.get('subagents_used'):
                            print(f"  Subagents used: {', '.join(output['subagents_used'])}")
                        
                        if output.get('tools_used'):
                            print(f"  Tools used: {', '.join(output['tools_used'])}")
                        
                        if output.get('fallback'):
                            print(f"  Used fallback workflow: {output['fallback']}")
                    
                    # Show metadata
                    if metadata.get('subagent_interactions'):
                        print(f"  Subagent interactions: {metadata['subagent_interactions']}")
                    
                    if metadata.get('tool_executions'):
                        print(f"  Tool executions: {metadata['tool_executions']}")
                    
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
        
        print("\n🎉 Claude Code Subagents adapter integration test completed!")
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
    success = test_claude_subagents_adapter_integration()
    sys.exit(0 if success else 1)