#!/usr/bin/env python3
"""
Strands Implementation Validation Script

Validates the Strands implementation structure, imports, and basic functionality.
"""

import sys
import os
from pathlib import Path
import importlib.util

def validate_structure():
    """Validate directory and file structure."""
    print("🔍 Validating Strands implementation structure...")
    
    base_dir = Path(__file__).parent
    
    # Required directories
    required_dirs = [
        "agents",
        "workflows",
        "observability", 
        "cloud",
        "tests"
    ]
    
    # Required files
    required_files = [
        "adapter.py",
        "requirements.txt",
        "README.md",
        "agents/__init__.py",
        "agents/enterprise_architect.py",
        "agents/senior_developer.py", 
        "agents/qa_engineer.py",
        "workflows/__init__.py",
        "workflows/enterprise_workflow.py",
        "observability/__init__.py",
        "observability/telemetry_manager.py",
        "cloud/__init__.py",
        "cloud/provider_manager.py",
        "tests/__init__.py",
        "tests/test_structure_only.py"
    ]
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            print(f"❌ Missing directory: {dir_name}")
            return False
        print(f"✅ Directory exists: {dir_name}")
    
    # Check files
    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            print(f"❌ Missing file: {file_path}")
            return False
        print(f"✅ File exists: {file_path}")
    
    return True

def validate_imports():
    """Validate that key modules can be imported."""
    print("\n🔍 Validating imports...")
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    imports_to_test = [
        ("adapter", "StrandsAdapter"),
        ("adapter", "create_strands_adapter"),
        ("agents.enterprise_architect", "EnterpriseArchitectAgent"),
        ("agents.senior_developer", "SeniorDeveloperAgent"),
        ("agents.qa_engineer", "QAEngineerAgent"),
        ("workflows.enterprise_workflow", "EnterpriseWorkflow"),
        ("observability.telemetry_manager", "TelemetryManager"),
        ("cloud.provider_manager", "ProviderManager")
    ]
    
    for module_name, class_name in imports_to_test:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                print(f"✅ Successfully imported {class_name} from {module_name}")
            else:
                print(f"❌ Class {class_name} not found in {module_name}")
                return False
        except ImportError as e:
            print(f"❌ Failed to import {module_name}: {e}")
            return False
    
    return True

def validate_adapter_interface():
    """Validate that the adapter implements the required interface."""
    print("\n🔍 Validating adapter interface...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from adapter import StrandsAdapter
        
        # Required methods
        required_methods = [
            'get_info',
            'get_capabilities',
            'health_check', 
            'get_metrics',
            'run_task'
        ]
        
        adapter = StrandsAdapter()
        
        for method_name in required_methods:
            if hasattr(adapter, method_name):
                method = getattr(adapter, method_name)
                if callable(method):
                    print(f"✅ Method {method_name} exists and is callable")
                else:
                    print(f"❌ Method {method_name} exists but is not callable")
                    return False
            else:
                print(f"❌ Method {method_name} not found")
                return False
        
        # Test adapter name
        if hasattr(adapter, 'name') and adapter.name == "strands":
            print("✅ Adapter name is correctly set to 'strands'")
        else:
            print("❌ Adapter name is not set correctly")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate adapter interface: {e}")
        return False

def validate_factory_function():
    """Validate the factory function."""
    print("\n🔍 Validating factory function...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from adapter import create_strands_adapter
        
        # Test factory function
        adapter = create_strands_adapter()
        
        if adapter is not None:
            print("✅ Factory function creates adapter instance")
            
            # Test with config
            config = {"model_config": {"primary": "test"}}
            adapter_with_config = create_strands_adapter(config)
            
            if adapter_with_config is not None:
                print("✅ Factory function works with configuration")
                return True
            else:
                print("❌ Factory function failed with configuration")
                return False
        else:
            print("❌ Factory function returned None")
            return False
            
    except Exception as e:
        print(f"❌ Failed to validate factory function: {e}")
        return False

def validate_enterprise_features():
    """Validate enterprise-specific features."""
    print("\n🔍 Validating enterprise features...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from adapter import StrandsAdapter
        
        adapter = StrandsAdapter()
        
        # Check enterprise configuration
        if hasattr(adapter, 'config'):
            config = adapter.config
            enterprise_features = [
                'observability_enabled',
                'distributed_tracing',
                'cloud_providers',
                'error_recovery'
            ]
            
            for feature in enterprise_features:
                if hasattr(config, feature):
                    print(f"✅ Enterprise feature configured: {feature}")
                else:
                    print(f"❌ Enterprise feature missing: {feature}")
                    return False
        
        # Check enterprise components
        enterprise_components = [
            'telemetry_manager',
            'provider_manager', 
            'workflow'
        ]
        
        for component in enterprise_components:
            if hasattr(adapter, component):
                print(f"✅ Enterprise component available: {component}")
            else:
                print(f"⚠️  Enterprise component not initialized: {component} (may be due to missing dependencies)")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate enterprise features: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🚀 Starting Strands implementation validation...\n")
    
    checks = [
        ("Structure", validate_structure),
        ("Imports", validate_imports),
        ("Adapter Interface", validate_adapter_interface),
        ("Factory Function", validate_factory_function),
        ("Enterprise Features", validate_enterprise_features)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{'='*50}")
        print(f"Running {check_name} validation")
        print('='*50)
        
        try:
            result = check_func()
            results.append((check_name, result))
            
            if result:
                print(f"✅ {check_name} validation PASSED")
            else:
                print(f"❌ {check_name} validation FAILED")
                
        except Exception as e:
            print(f"❌ {check_name} validation ERROR: {e}")
            results.append((check_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("VALIDATION SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All validations passed! Strands implementation is ready.")
        return 0
    else:
        print("❌ Some validations failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())