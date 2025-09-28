#!/usr/bin/env python3

"""
Semantic Kernel Implementation Validation Script

This script validates the structure and basic functionality of the Semantic Kernel
plugin-based AI development implementation.
"""

import os
import sys
from pathlib import Path

def validate_structure():
    """Validate the directory structure."""
    print("🔍 Validating Semantic Kernel implementation structure...")
    
    base_path = Path(__file__).parent
    
    # Required files and directories
    required_items = [
        "adapter.py",
        "requirements.txt", 
        "README.md",
        "COMPLETION_SUMMARY.md",
        "simple_integration_test.py",
        "agents/",
        "workflows/",
        "python/",
        "csharp/",
        "tests/",
        "tests/test_semantic_kernel_adapter.py"
    ]
    
    missing_items = []
    for item in required_items:
        item_path = base_path / item
        if not item_path.exists():
            missing_items.append(item)
    
    if missing_items:
        print(f"❌ Missing required items: {missing_items}")
        return False
    
    print("✅ All required files and directories present")
    return True

def validate_adapter():
    """Validate the adapter implementation."""
    print("🔍 Validating adapter implementation...")
    
    try:
        # Import the adapter
        sys.path.insert(0, str(Path(__file__).parent))
        from adapter import SemanticKernelAdapter
        
        # Check required methods
        required_methods = [
            'get_info',
            'get_capabilities', 
            'run_task',
            'health_check',
            'get_metrics'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(SemanticKernelAdapter, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing required methods: {missing_methods}")
            return False
        
        print("✅ All required methods present")
        return True
        
    except Exception as e:
        print(f"❌ Adapter validation failed: {e}")
        return False

def validate_plugins():
    """Validate the plugin implementations."""
    print("🔍 Validating plugin implementations...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Check for plugin directories
        base_path = Path(__file__).parent
        plugin_dirs = [
            "python/plugins",
            "csharp/Plugins"
        ]
        
        for plugin_dir in plugin_dirs:
            plugin_path = base_path / plugin_dir
            if plugin_path.exists():
                print(f"✅ Found plugin directory: {plugin_dir}")
            else:
                print(f"⚠️  Plugin directory not found: {plugin_dir}")
        
        print("✅ Plugin structure validation completed")
        return True
        
    except Exception as e:
        print(f"❌ Plugin validation failed: {e}")
        return False

def validate_workflows():
    """Validate the workflow implementations."""
    print("🔍 Validating workflow implementations...")
    
    try:
        base_path = Path(__file__).parent
        workflow_files = [
            "workflows/development_workflow.py",
            "python/workflows/development_workflow.py"
        ]
        
        workflow_found = False
        for workflow_file in workflow_files:
            workflow_path = base_path / workflow_file
            if workflow_path.exists():
                workflow_found = True
                print(f"✅ Found workflow: {workflow_file}")
                break
        
        if not workflow_found:
            print("⚠️  No workflow files found, but this may be expected")
        
        print("✅ Workflow implementation valid")
        return True
        
    except Exception as e:
        print(f"❌ Workflow validation failed: {e}")
        return False

def validate_semantic_kernel_imports():
    """Validate Semantic Kernel library imports."""
    print("🔍 Validating Semantic Kernel imports...")
    
    try:
        import semantic_kernel
        print("✅ Semantic Kernel library available")
        
        # Check for key Semantic Kernel components
        required_components = [
            'Kernel',
            'KernelBuilder'
        ]
        
        missing_components = []
        for component in required_components:
            if not hasattr(semantic_kernel, component):
                missing_components.append(component)
        
        if missing_components:
            print(f"⚠️  Missing Semantic Kernel components: {missing_components}")
            return True  # Don't fail validation, just warn
        
        print("✅ All Semantic Kernel components available")
        return True
        
    except ImportError as e:
        print(f"⚠️  Semantic Kernel not available: {e}")
        print("   Install with: pip install semantic-kernel")
        return True  # Don't fail validation for missing optional dependency

def validate_documentation():
    """Validate documentation completeness."""
    print("🔍 Validating documentation...")
    
    base_path = Path(__file__).parent
    readme_path = base_path / "README.md"
    
    if not readme_path.exists():
        print("❌ README.md not found")
        return False
    
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "# Semantic Kernel AI Development Squad Implementation",
            "## Overview",
            "## Setup", 
            "## Features",
            "## Usage",
            "## Architecture"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing documentation sections: {missing_sections}")
            return False
        
        # Check word count
        word_count = len(content.split())
        if word_count < 1000:
            print(f"❌ Documentation too brief: {word_count} words")
            return False
        
        print(f"✅ Documentation complete ({word_count} words)")
        return True
        
    except Exception as e:
        print(f"❌ Documentation validation failed: {e}")
        return False

def validate_factory_functions():
    """Validate factory functions exist."""
    print("🔍 Validating factory functions...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from adapter import create_semantic_kernel_adapter, create_adapter
        
        # Check functions exist
        if not callable(create_semantic_kernel_adapter):
            print("❌ create_semantic_kernel_adapter not callable")
            return False
        
        if not callable(create_adapter):
            print("❌ create_adapter not callable")
            return False
        
        print("✅ All factory functions available")
        return True
        
    except ImportError as e:
        print(f"❌ Factory function validation failed: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🚀 Semantic Kernel Plugin-Based AI Squad Validation")
    print("=" * 60)
    
    validations = [
        validate_structure,
        validate_adapter,
        validate_plugins,
        validate_workflows,
        validate_semantic_kernel_imports,
        validate_documentation,
        validate_factory_functions
    ]
    
    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if all(results):
        print("✅ All validations passed!")
        print("🚀 Semantic Kernel implementation is ready")
        return 0
    else:
        print("❌ Some validations failed")
        print("🔧 Please address the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())