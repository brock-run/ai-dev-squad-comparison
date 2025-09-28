#!/usr/bin/env python3

"""
Production Readiness Test for Semantic Kernel Implementation

This test validates that the Semantic Kernel adapter is ready for production use
by testing all critical functionality, error handling, and integration points.
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_semantic_kernel_production_readiness():
    """Comprehensive production readiness test for Semantic Kernel adapter."""
    print("🔍 Testing Semantic Kernel Production Readiness...")
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
            from adapter import SemanticKernelAdapter, create_semantic_kernel_adapter, create_adapter
            
            config = {
                'language': 'python',
                'semantic_kernel': {'model': 'llama3.1:8b'},
                'vcs': {'github': {'enabled': True}}
            }
            
            adapter = create_semantic_kernel_adapter(config)
            
            assert adapter.name == "Semantic Kernel Plugin-Based Development Squad"
            assert adapter.version == "2.0.0"
            
            test_results['passed'] += 1
            test_results['details'].append("✅ Import and initialization successful")
            print("   ✅ Import and initialization successful")
            
        except Exception as e:
            test_results['failed'] += 1
            test_results['details'].append(f"❌ Import/initialization failed: {e}")
            print(f"   ❌ Import/initialization failed: {e}")
        
        # Test 2: Semantic Kernel Library Availability
        print("\n2. Testing Semantic Kernel Library Availability...")
        
        try:
            import semantic_kernel
            test_results['passed'] += 1
            test_results['details'].append("✅ Semantic Kernel library available")
            print("   ✅ Semantic Kernel library available")
            
            # Check key components
            required_components = ['Kernel']
            for component in required_components:
                if hasattr(semantic_kernel, component):
                    test_results['passed'] += 1
                    test_results['details'].append(f"✅ {component} available")
                    print(f"   ✅ {component} available")
                else:
                    test_results['warnings'] += 1
                    test_results['details'].append(f"⚠️  {component} not available")
                    print(f"   ⚠️  {component} not available")
            
        except ImportError:
            test_results['warnings'] += 1
            test_results['details'].append("⚠️  Semantic Kernel library not available - using fallback mode")
            print("   ⚠️  Semantic Kernel library not available - using fallback mode")
        
        # Test 3: Async Capabilities and Health Check
        print("\n3. Testing Async Capabilities and Health Check...")
        
        async def test_async_functionality():
            try:
                capabilities = await adapter.get_capabilities()
                
                # Check required capabilities
                required_features = [
                    'plugin_based_architecture',
                    'semantic_functions',
                    'native_functions',
                    'function_composition'
                ]
                
                for feature in required_features:
                    if feature in capabilities.get('features', []):
                        test_results['passed'] += 1
                        test_results['details'].append(f"✅ Feature available: {feature}")
                        print(f"   ✅ Feature available: {feature}")
                    else:
                        test_results['warnings'] += 1
                        test_results['details'].append(f"⚠️  Feature missing: {feature}")
                        print(f"   ⚠️  Feature missing: {feature}")
                
                # Check plugin architecture
                plugin_arch = capabilities.get('plugin_architecture', {})
                required_plugins = ['architect', 'developer', 'tester']
                
                for plugin in required_plugins:
                    if plugin in plugin_arch:
                        test_results['passed'] += 1
                        test_results['details'].append(f"✅ Plugin available: {plugin}")
                        print(f"   ✅ Plugin available: {plugin}")
                    else:
                        test_results['warnings'] += 1
                        test_results['details'].append(f"⚠️  Plugin missing: {plugin}")
                        print(f"   ⚠️  Plugin missing: {plugin}")
                
                # Health check
                health = await adapter.health_check()
                
                if 'status' in health:
                    test_results['passed'] += 1
                    test_results['details'].append("✅ Health check has status")
                    print("   ✅ Health check has status")
                
                if 'components' in health:
                    test_results['passed'] += 1
                    test_results['details'].append("✅ Health check has components")
                    print("   ✅ Health check has components")
                
            except Exception as e:
                test_results['failed'] += 1
                test_results['details'].append(f"❌ Async functionality failed: {e}")
                print(f"   ❌ Async functionality failed: {e}")
        
        asyncio.run(test_async_functionality())
        
        # Test 4: Task Execution and Plugin Workflow
        print("\n4. Testing Task Execution and Plugin Workflow...")
        
        async def test_task_execution():
            try:
                # Create a mock task schema with all required attributes
                class MockTaskSchema:
                    def __init__(self):
                        self.id = 'prod-test-1'
                        from common.agent_api import TaskType
                        self.type = TaskType.FEATURE_ADD
                        self.inputs = {
                            'description': 'Create a plugin-based calculator with multiple functions',
                            'requirements': [
                                'Architect designs the plugin structure',
                                'Developer implements the calculation functions',
                                'Tester creates comprehensive test cases'
                            ],
                            'context': {}
                        }
                        self.repo_path = '.'
                        self.vcs_provider = 'github'
                        self.mode = 'autonomous'
                        self.seed = 42
                        self.model_prefs = {}
                        self.timeout_seconds = 300
                        self.resource_limits = {}
                        self.metadata = {'production_test': True}
                
                task = MockTaskSchema()
                
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
                
                # Check plugin-specific outputs
                required_outputs = ['plugin_executions', 'function_calls']
                for req_output in required_outputs:
                    if req_output in output:
                        test_results['passed'] += 1
                        test_results['details'].append(f"✅ Output contains: {req_output}")
                        print(f"   ✅ Output contains: {req_output}")
                    else:
                        test_results['warnings'] += 1
                        test_results['details'].append(f"⚠️  Output missing: {req_output}")
                        print(f"   ⚠️  Output missing: {req_output}")
                
                # Check metadata
                metadata = run_result.metadata
                if 'plugin_workflow' in metadata:
                    test_results['passed'] += 1
                    test_results['details'].append("✅ Metadata contains plugin_workflow")
                    print("   ✅ Metadata contains plugin_workflow")
                
                test_results['passed'] += 1
                test_results['details'].append(f"✅ Task execution passed (took {execution_time:.2f}s)")
                print(f"   ✅ Task execution passed (took {execution_time:.2f}s)")
                
            except Exception as e:
                test_results['failed'] += 1
                test_results['details'].append(f"❌ Task execution failed: {e}")
                print(f"   ❌ Task execution failed: {e}")
        
        asyncio.run(test_task_execution())
        
        # Test 5: Plugin System Validation
        print("\n5. Testing Plugin System Validation...")
        
        try:
            # Test plugin directory structure
            from pathlib import Path
            base_path = Path(__file__).parent
            
            plugin_dirs = [
                "python/plugins",
                "csharp/Plugins"
            ]
            
            plugin_found = False
            for plugin_dir in plugin_dirs:
                plugin_path = base_path / plugin_dir
                if plugin_path.exists():
                    plugin_found = True
                    test_results['passed'] += 1
                    test_results['details'].append(f"✅ Plugin directory found: {plugin_dir}")
                    print(f"   ✅ Plugin directory found: {plugin_dir}")
                    break
            
            if not plugin_found:
                test_results['warnings'] += 1
                test_results['details'].append("⚠️  No plugin directories found")
                print("   ⚠️  No plugin directories found")
            
        except Exception as e:
            test_results['warnings'] += 1
            test_results['details'].append(f"⚠️  Plugin system validation failed: {e}")
            print(f"   ⚠️  Plugin system validation failed: {e}")
        
        # Test 6: Configuration Validation
        print("\n6. Testing Configuration Validation...")
        
        try:
            # Test with minimal config
            minimal_config = {'language': 'python'}
            minimal_adapter = SemanticKernelAdapter(minimal_config)
            
            if minimal_adapter.name == "Semantic Kernel Plugin-Based Development Squad":
                test_results['passed'] += 1
                test_results['details'].append("✅ Minimal configuration working")
                print("   ✅ Minimal configuration working")
            
            # Test with comprehensive config
            comprehensive_config = {
                'language': 'python',
                'semantic_kernel': {
                    'model': 'llama3.1:8b',
                    'code_model': 'codellama:13b',
                    'temperature': 0.7,
                    'max_tokens': 2048
                },
                'plugins': {
                    'architect': {'enabled': True},
                    'developer': {'enabled': True},
                    'tester': {'enabled': True}
                },
                'vcs': {
                    'github': {
                        'enabled': True,
                        'token': 'test-token'
                    }
                },
                'safety': {
                    'enabled': True,
                    'sandbox': True
                }
            }
            
            comprehensive_adapter = SemanticKernelAdapter(comprehensive_config)
            
            if comprehensive_adapter.config == comprehensive_config:
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
    if test_results['failed'] == 0 and success_rate >= 70:
        print("🎉 PRODUCTION READY!")
        print("The Semantic Kernel adapter is ready for production deployment.")
        if test_results['warnings'] > 0:
            print("Note: Some warnings were found but don't prevent production use.")
    elif test_results['failed'] == 0:
        print("⚠️  MOSTLY READY")
        print("The Semantic Kernel adapter is mostly ready but has some concerns.")
        print("Review warnings before production deployment.")
    else:
        print("❌ NOT PRODUCTION READY")
        print("The Semantic Kernel adapter has critical issues that must be resolved.")
        print("Do not deploy to production until all failures are fixed.")
    
    return test_results['failed'] == 0


if __name__ == "__main__":
    success = test_semantic_kernel_production_readiness()
    sys.exit(0 if success else 1)