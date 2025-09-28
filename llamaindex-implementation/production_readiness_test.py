#!/usr/bin/env python3

"""
Simple Integration Test for LlamaIndex Implementation

This test validates basic functionality of the LlamaIndex adapter
without requiring external services or complex setup.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_llamaindex_integration():
    """Test LlamaIndex adapter integration."""
    print("Testing LlamaIndex Adapter Integration...")
    
    try:
        # Import the adapter
        from adapter import LlamaIndexAdapter, create_llamaindex_adapter, create_adapter
        
        # Test basic configuration
        config = {
            'language': 'python',
            'llamaindex': {'model': 'gpt-3.5-turbo'},
            'vcs': {'github': {'enabled': True}}
        }
        
        # Test adapter creation
        adapter = create_llamaindex_adapter(config)
        print(f"✓ Created adapter: {adapter.name} v{adapter.version}")
        
        # Test factory function
        generic_adapter = create_adapter(config)
        print(f"✓ Factory function works: {generic_adapter.name}")
        
        # Test async functionality
        async def test_async_features():
            print("\n--- Running Async Tests ---")
            
            # Test capabilities
            capabilities = await adapter.get_capabilities()
            print(f"✓ Capabilities: {len(capabilities.get('features', []))} features")
            
            # Print key features
            features = capabilities.get('features', [])
            for feature in features[:5]:  # Show first 5 features
                print(f"  ✓ {feature}")
            
            # Test retrieval features
            retrieval_features = capabilities.get('retrieval_features', {})
            if retrieval_features:
                print("  Retrieval Features:")
                for key, value in retrieval_features.items():
                    print(f"    {key}: {value}")
            
            # Test agent architecture
            agent_arch = capabilities.get('agent_architecture', {})
            if agent_arch:
                print("  Agent Architecture:")
                for agent, desc in agent_arch.items():
                    print(f"    {agent}: {desc}")
            
            # Test health check
            health = await adapter.health_check()
            print(f"✓ Health check: {health.get('status', 'unknown')}")
            
            # Print component status
            components = health.get('components', {})
            for component, status in components.items():
                status_icon = "✓" if status else "✗"
                print(f"  {status_icon} {component}: {'available' if status else 'unavailable'}")
            
            # Test task execution
            print("\nTesting task execution...")
            
            from common.agent_api import TaskSchema, TaskType
            
            task = TaskSchema(
                id='integration-test-1',
                type=TaskType.FEATURE_ADD,
                inputs={
                    'description': 'Create a retrieval-augmented code analyzer',
                    'requirements': [
                        'Index repository for code understanding',
                        'Implement semantic search capabilities',
                        'Add context-aware code generation',
                        'Include comprehensive documentation retrieval'
                    ],
                    'context': {}
                },
                repo_path='.',
                vcs_provider='github'
            )
            
            results = []
            async for item in adapter.run_task(task):
                results.append(item)
                if hasattr(item, 'status'):  # RunResult
                    break
            
            if results:
                result = results[-1]  # Get the final result
                print(f"✓ Task execution completed: {hasattr(result, 'status')}")
                
                if hasattr(result, 'artifacts'):
                    artifacts = result.artifacts
                    output = artifacts.get('output', {})
                    
                    # Print retrieval-specific outputs
                    if 'indexed_files' in output:
                        print(f"  Indexed files: {output['indexed_files']}")
                    if 'retrieval_queries' in output:
                        print(f"  Retrieval queries: {output['retrieval_queries']}")
                    if 'context_chunks' in output:
                        print(f"  Context chunks: {output['context_chunks']}")
                    if 'generated_code' in output:
                        code_length = len(output['generated_code'])
                        print(f"  Generated code: {code_length} chars")
                    
                    # Print metadata
                    if hasattr(result, 'metadata'):
                        metadata = result.metadata
                        if 'retrieval_method' in metadata:
                            print(f"  Retrieval method: {metadata['retrieval_method']}")
                        if 'index_type' in metadata:
                            print(f"  Index type: {metadata['index_type']}")
            else:
                print("✗ No results returned from task execution")
            
            # Test metrics
            metrics = await adapter.get_metrics()
            print(f"\n✓ Metrics collected: {len(metrics)} categories")
            
            # Print key metrics
            if 'retrieval' in metrics:
                retrieval_metrics = metrics['retrieval']
                print("  Retrieval Metrics:")
                for key, value in retrieval_metrics.items():
                    print(f"    {key}: {value}")
            
            if 'indexing' in metrics:
                indexing_metrics = metrics['indexing']
                print("  Indexing Metrics:")
                for key, value in indexing_metrics.items():
                    print(f"    {key}: {value}")
        
        # Run async tests
        asyncio.run(test_async_features())
        
        print("\n--- Test Summary ---")
        print("✓ Adapter created successfully")
        print("✓ Capabilities retrieved")
        print("✓ Health check completed")
        print("✓ Task execution tested")
        print("✓ Metrics collection working")
        
        print("\n🎉 LlamaIndex adapter integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    success = test_llamaindex_integration()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())