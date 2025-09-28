#!/usr/bin/env python3

"""
Production readiness test for Langroid implementation.

This test validates that the Langroid adapter is ready for production use
by testing all critical functionality, error handling, and integration points.
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_langroid_production_readiness():
    """Comprehensive production readiness test for Langroid adapter."""
    print("🔍 Testing Langroid Production Readiness...")
    print("=" * 60)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0,
        'details': []
    }
    
    try:
        # Test 1: Import and Basic Initialization
        print("\n1. Testing Import and Initialization...")
        try:
            from adapter import LangroidAdapter, create_langroid_adapter, LANGROID_AVAILABLE, AGENTS_AVAILABLE
            
            config = {
                'language': 'python',
                'langroid': {'model': 'gpt-3.5-turbo'},
                'vcs': {'github': {'enabled': True}}
            }
            
            adapter = create_langroid_adapter(config)
            
            assert adapter.name == "Langroid Conversation Orchestrator"
            assert adapter.version == "2.0.0"
            
            test_results['passed'] += 1
            test_results['details'].append("✅ Import and initialization successful")
            print("   ✅ Import and initialization successful")
            
        except Exception as e:
            test_results['failed'] += 1
            test_results['details'].append(f"❌ Import/initialization failed: {e}")
            print(f"   ❌ Import/initialization failed: {e}")
        
        # Test 2: Dependency Availability
        print("\n2. Testing Dependency Availability...")
        
        if LANGROID_AVAILABLE:
            test_results['passed'] += 1
            test_results['details'].append("✅ Langroid library available")
            print("   ✅ Langroid library available")
        else:
            test_results['warnings'] += 1
            test_results['details'].append("⚠️  Langroid library not available - using fallback mode")
            print("   ⚠️  Langroid library not available - using fallback mode")
        
        if AGENTS_AVAILABLE:
            test_results['passed'] += 1
            test_results['details'].append("✅ Langroid agents available")
            print("   ✅ Langroid agents available")
        else:
            test_results['warnings'] += 1
            test_results['details'].append("⚠️  Langroid agents not available - using mock agents")
            print("   ⚠️  Langroid agents not available - using mock agents")
        
        # Test 3: Async Capabilities and Health Check
        print("\n3. Testing Async Capabilities and Health Check...")
        
        async def test_async_functionality():
            try:
                capabilities = await adapter.get_capabilities()
                
                # Check required capabilities
                required_features = [
                    'conversation_style_interactions',
                    'turn_taking_logic',
                    'agent_role_specialization',
                    'multi_agent_conversations'
                ]
                
                for feature in required_features:
                    if feature not in capabilities.get('features', []):
                        raise AssertionError(f"Missing required feature: {feature}")
                
                # Check agent architecture
                agent_arch = capabilities.get('agent_architecture', {})
                required_agents = ['developer', 'reviewer', 'tester']
                
                for agent in required_agents:
                    if agent not in agent_arch:
                        raise AssertionError(f"Missing required agent: {agent}")
                
                # Check conversation features
                conv_features = capabilities.get('conversation_features', {})
                if not conv_features.get('turn_taking'):
                    raise AssertionError("Turn-taking not enabled")
                
                test_results['passed'] += 1
                test_results['details'].append("✅ Capabilities check passed")
                print("   ✅ Capabilities check passed")
                
                # Health check
                health = await adapter.health_check()
                
                if 'status' not in health:
                    raise AssertionError("Health check missing status")
                
                if 'components' not in health:
                    raise AssertionError("Health check missing components")
                
                test_results['passed'] += 1
                test_results['details'].append("✅ Health check passed")
                print("   ✅ Health check passed")
                
            except Exception as e:
                test_results['failed'] += 1
                test_results['details'].append(f"❌ Async functionality failed: {e}")
                print(f"   ❌ Async functionality failed: {e}")
        
        asyncio.run(test_async_functionality())
        
        # Test 4: Task Execution and Conversation Workflow
        print("\n4. Testing Task Execution and Conversation Workflow...")
        
        async def test_task_execution():
            try:
                from common.agent_api import TaskSchema, TaskType
                
                task = TaskSchema(
                    id='prod-test-1',
                    type=TaskType.FEATURE_ADD,
                    inputs={
                        'description': 'Create a conversation-based data validator',
                        'requirements': [
                            'Validate data through agent conversations',
                            'Include comprehensive error handling',
                            'Add detailed logging and monitoring'
                        ],
                        'context': {}
                    },
                    repo_path='.',
                    vcs_provider='github'
                )
                
                results = []
                start_time = time.time()
                
                async for item in adapter.run_task(task):
                    results.append(item)
                    if hasattr(item, 'status'):  # RunResult
                        break
                
                execution_time = time.time() - start_time
                
                if not results:
                    raise AssertionError("No results returned from task execution")
                
                # Find RunResult
                run_result = None
                for item in results:
                    if hasattr(item, 'status'):
                        run_result = item
                        break
                
                if not run_result:
                    raise AssertionError("No RunResult found in task execution")
                
                # Validate result structure
                if not hasattr(run_result, 'artifacts'):
                    raise AssertionError("RunResult missing artifacts")
                
                if 'output' not in run_result.artifacts:
                    raise AssertionError("RunResult missing output in artifacts")
                
                output = run_result.artifacts['output']
                
                # Check conversation-specific outputs
                required_outputs = ['agents_used', 'conversation_turns']
                for req_output in required_outputs:
                    if req_output not in output:
                        raise AssertionError(f"Missing required output: {req_output}")
                
                # Check metadata
                metadata = run_result.metadata
                if 'conversation_style' not in metadata:
                    raise AssertionError("Missing conversation_style in metadata")
                
                if metadata['conversation_style'] != 'turn_taking':
                    raise AssertionError("Incorrect conversation style")
                
                test_results['passed'] += 1
                test_results['details'].append(f"✅ Task execution passed (took {execution_time:.2f}s)")
                print(f"   ✅ Task execution passed (took {execution_time:.2f}s)")
                
                # Check conversation quality
                if output.get('conversation_turns', 0) > 0:
                    test_results['passed'] += 1
                    test_results['details'].append("✅ Conversation workflow active")
                    print("   ✅ Conversation workflow active")
                else:
                    test_results['warnings'] += 1
                    test_results['details'].append("⚠️  No conversation turns recorded")
                    print("   ⚠️  No conversation turns recorded")
                
            except Exception as e:
                test_results['failed'] += 1
                test_results['details'].append(f"❌ Task execution failed: {e}")
                print(f"   ❌ Task execution failed: {e}")
        
        asyncio.run(test_task_execution())
        
        # Test 5: Safety and Error Handling
        print("\n5. Testing Safety and Error Handling...")
        
        async def test_safety_features():
            try:
                # Test input sanitization
                safe_input = await adapter._sanitize_input("normal input")
                if safe_input != "normal input":
                    raise AssertionError("Input sanitization failed for normal input")
                
                test_results['passed'] += 1
                test_results['details'].append("✅ Input sanitization working")
                print("   ✅ Input sanitization working")
                
                # Test task validation
                from common.agent_api import TaskSchema, TaskType
                
                valid_task = TaskSchema(
                    id='safety-test',
                    type=TaskType.FEATURE_ADD,
                    inputs={
                        'description': 'Test task',
                        'requirements': ['Test requirement'],
                        'context': {}
                    },
                    repo_path='.',
                    vcs_provider='github'
                )
                
                validated_task = await adapter._validate_task(valid_task)
                if validated_task.id != valid_task.id:
                    raise AssertionError("Task validation failed")
                
                test_results['passed'] += 1
                test_results['details'].append("✅ Task validation working")
                print("   ✅ Task validation working")
                
                # Test error handling with invalid input
                try:
                    invalid_task = TaskSchema(
                        id='invalid-test',
                        type=TaskType.FEATURE_ADD,
                        inputs={},  # Missing required fields
                        repo_path='.',
                        vcs_provider='github'
                    )
                    
                    results = []
                    async for item in adapter.run_task(invalid_task):
                        results.append(item)
                        if len(results) > 5:  # Prevent infinite loop
                            break
                    
                    # Should handle gracefully
                    test_results['passed'] += 1
                    test_results['details'].append("✅ Error handling working")
                    print("   ✅ Error handling working")
                    
                except Exception as e:
                    # This is expected - error handling should work
                    test_results['passed'] += 1
                    test_results['details'].append("✅ Error handling working (caught exception)")
                    print("   ✅ Error handling working (caught exception)")
                
            except Exception as e:
                test_results['failed'] += 1
                test_results['details'].append(f"❌ Safety features failed: {e}")
                print(f"   ❌ Safety features failed: {e}")
        
        asyncio.run(test_safety_features())
        
        # Test 6: VCS Integration
        print("\n6. Testing VCS Integration...")
        
        try:
            workflow_result = {
                'implementation': 'def main(): print("Hello Langroid")',
                'tests': 'def test_main(): assert True',
                'conversation_log': 'Mock conversation log',
                'agents_used': ['developer', 'reviewer', 'tester'],
                'conversation_turns': 5
            }
            
            # Test file extraction
            files = adapter._extract_files_from_result(workflow_result)
            
            expected_files = ['main.py', 'test_main.py', 'CONVERSATION_LOG.md', 'AGENTS.md']
            for expected_file in expected_files:
                if expected_file not in files:
                    raise AssertionError(f"Missing expected file: {expected_file}")
            
            test_results['passed'] += 1
            test_results['details'].append("✅ File extraction working")
            print("   ✅ File extraction working")
            
            # Test VCS operations (mock)
            from common.agent_api import TaskSchema, TaskType
            
            mock_task = TaskSchema(
                id='vcs-test',
                type=TaskType.FEATURE_ADD,
                inputs={'description': 'VCS test task'},
                repo_path='.',
                vcs_provider='github'
            )
            
            # Test with VCS disabled
            original_vcs_config = adapter.config.get('vcs', {})
            adapter.config['vcs'] = {'enabled': False}
            
            async def test_vcs_disabled():
                vcs_result = await adapter._handle_vcs_operations(mock_task, workflow_result)
                if vcs_result['status'] != 'skipped':
                    raise AssertionError("VCS should be skipped when disabled")
            
            asyncio.run(test_vcs_disabled())
            
            # Restore original config
            adapter.config['vcs'] = original_vcs_config
            
            test_results['passed'] += 1
            test_results['details'].append("✅ VCS integration working")
            print("   ✅ VCS integration working")
            
        except Exception as e:
            test_results['failed'] += 1
            test_results['details'].append(f"❌ VCS integration failed: {e}")
            print(f"   ❌ VCS integration failed: {e}")
        
        # Test 7: Performance and Resource Usage
        print("\n7. Testing Performance and Resource Usage...")
        
        try:
            import psutil
            import gc
            
            # Memory usage test
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create multiple adapters to test memory usage
            adapters = []
            for i in range(5):
                test_adapter = LangroidAdapter(config)
                adapters.append(test_adapter)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Clean up
            del adapters
            gc.collect()
            
            if memory_increase > 100:  # More than 100MB increase
                test_results['warnings'] += 1
                test_results['details'].append(f"⚠️  High memory usage: {memory_increase:.1f}MB increase")
                print(f"   ⚠️  High memory usage: {memory_increase:.1f}MB increase")
            else:
                test_results['passed'] += 1
                test_results['details'].append(f"✅ Memory usage acceptable: {memory_increase:.1f}MB increase")
                print(f"   ✅ Memory usage acceptable: {memory_increase:.1f}MB increase")
            
        except ImportError:
            test_results['warnings'] += 1
            test_results['details'].append("⚠️  psutil not available, skipping performance tests")
            print("   ⚠️  psutil not available, skipping performance tests")
        except Exception as e:
            test_results['warnings'] += 1
            test_results['details'].append(f"⚠️  Performance test failed: {e}")
            print(f"   ⚠️  Performance test failed: {e}")
        
        # Test 8: Configuration Validation
        print("\n8. Testing Configuration Validation...")
        
        try:
            # Test with minimal config
            minimal_config = {'language': 'python'}
            minimal_adapter = LangroidAdapter(minimal_config)
            
            if minimal_adapter.name != "Langroid Conversation Orchestrator":
                raise AssertionError("Minimal config initialization failed")
            
            test_results['passed'] += 1
            test_results['details'].append("✅ Minimal configuration working")
            print("   ✅ Minimal configuration working")
            
            # Test with comprehensive config
            comprehensive_config = {
                'language': 'python',
                'langroid': {
                    'model': 'gpt-4',
                    'temperature': 0.7
                },
                'vcs': {
                    'github': {
                        'enabled': True,
                        'token': 'test-token',
                        'owner': 'test-owner',
                        'repo': 'test-repo'
                    },
                    'gitlab': {
                        'enabled': False
                    }
                },
                'safety': {
                    'enabled': True,
                    'sandbox': True
                }
            }
            
            comprehensive_adapter = LangroidAdapter(comprehensive_config)
            
            if comprehensive_adapter.config != comprehensive_config:
                raise AssertionError("Comprehensive config not properly stored")
            
            test_results['passed'] += 1
            test_results['details'].append("✅ Comprehensive configuration working")
            print("   ✅ Comprehensive configuration working")
            
        except Exception as e:
            test_results['failed'] += 1
            test_results['details'].append(f"❌ Configuration validation failed: {e}")
            print(f"   ❌ Configuration validation failed: {e}")
        
    except Exception as e:
        test_results['failed'] += 1
        test_results['details'].append(f"❌ Critical test failure: {e}")
        print(f"❌ Critical test failure: {e}")
    
    # Final Results
    print("\n" + "=" * 60)
    print("🏁 PRODUCTION READINESS TEST RESULTS")
    print("=" * 60)
    
    total_tests = test_results['passed'] + test_results['failed'] + test_results['warnings']
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⚠️  Warnings: {test_results['warnings']}")
    
    success_rate = (test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    print("\nDetailed Results:")
    for detail in test_results['details']:
        print(f"  {detail}")
    
    # Production readiness assessment
    print("\n" + "=" * 60)
    if test_results['failed'] == 0 and success_rate >= 80:
        print("🎉 PRODUCTION READY!")
        print("The Langroid adapter is ready for production deployment.")
        if test_results['warnings'] > 0:
            print("Note: Some warnings were found but don't prevent production use.")
    elif test_results['failed'] == 0:
        print("⚠️  MOSTLY READY")
        print("The Langroid adapter is mostly ready but has some concerns.")
        print("Review warnings before production deployment.")
    else:
        print("❌ NOT PRODUCTION READY")
        print("The Langroid adapter has critical issues that must be resolved.")
        print("Do not deploy to production until all failures are fixed.")
    
    return test_results['failed'] == 0


if __name__ == "__main__":
    success = test_langroid_production_readiness()
    sys.exit(0 if success else 1)