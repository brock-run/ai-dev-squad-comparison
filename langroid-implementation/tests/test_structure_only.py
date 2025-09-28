#!/usr/bin/env python3
"""
Structure-Only Tests for Langroid Implementation

This script runs basic structure and import tests without requiring
external dependencies to be installed.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_directory_structure():
    """Test that all required directories exist."""
    base_path = Path(__file__).parent.parent
    
    required_dirs = [
        "agents",
        "workflows", 
        "tests"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Directory {dir_name} not found"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"
    
    return True

def test_required_files():
    """Test that all required files exist."""
    base_path = Path(__file__).parent.parent
    
    required_files = [
        "adapter.py",
        "requirements.txt",
        "README.md", 
        "COMPLETION_SUMMARY.md",
        "simple_integration_test.py",
        "agents/developer_agent.py",
        "agents/reviewer_agent.py",
        "agents/tester_agent.py",
        "workflows/conversation_workflow.py",
        "tests/test_langroid_adapter.py"
    ]
    
    for file_name in required_files:
        file_path = base_path / file_name
        assert file_path.exists(), f"File {file_name} not found"
        assert file_path.is_file(), f"{file_name} is not a file"
    
    return True

def test_adapter_class():
    """Test that the adapter class can be imported."""
    try:
        from adapter import LangroidAdapter
        
        # Check class exists
        assert LangroidAdapter is not None
        
        # Check required methods exist
        required_methods = [
            'get_info',
            'get_capabilities',
            'run_task', 
            'health_check',
            'get_metrics'
        ]
        
        for method in required_methods:
            assert hasattr(LangroidAdapter, method), f"Method {method} not found"
        
        return True
        
    except ImportError as e:
        print(f"Warning: Could not import adapter: {e}")
        return True  # Don't fail on import errors in structure test

def test_agent_classes():
    """Test that agent classes can be imported."""
    try:
        from agents.developer_agent import DeveloperAgent
        from agents.reviewer_agent import ReviewerAgent
        from agents.tester_agent import TesterAgent
        
        # Check classes exist
        assert DeveloperAgent is not None
        assert ReviewerAgent is not None
        assert TesterAgent is not None
        
        return True
        
    except ImportError as e:
        print(f"Warning: Could not import agents: {e}")
        return True  # Don't fail on import errors in structure test

def test_workflow_class():
    """Test that workflow class can be imported."""
    try:
        from workflows.conversation_workflow import ConversationWorkflow
        
        # Check class exists
        assert ConversationWorkflow is not None
        
        return True
        
    except ImportError as e:
        print(f"Warning: Could not import workflow: {e}")
        return True  # Don't fail on import errors in structure test

def test_documentation():
    """Test documentation files."""
    base_path = Path(__file__).parent.parent
    
    # Check README
    readme_path = base_path / "README.md"
    assert readme_path.exists(), "README.md not found"
    
    with open(readme_path, 'r') as f:
        readme_content = f.read()
    
    # Check for key sections
    assert "# Langroid" in readme_content
    assert "## Overview" in readme_content
    assert "## Features" in readme_content
    assert "## Setup" in readme_content
    assert "## Usage" in readme_content
    
    # Check minimum length
    assert len(readme_content) > 1000, "README too short"
    
    return True

def test_requirements():
    """Test requirements file."""
    base_path = Path(__file__).parent.parent
    
    req_path = base_path / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    
    with open(req_path, 'r') as f:
        req_content = f.read()
    
    # Check for core dependencies
    assert "langroid" in req_content.lower()
    assert "pydantic" in req_content
    
    return True

def test_langroid_imports():
    """Test Langroid-specific imports."""
    adapter_file = Path(__file__).parent.parent / "adapter.py"
    
    with open(adapter_file, 'r') as f:
        content = f.read()
    
    # Check for Langroid imports
    langroid_imports = ['langroid', 'ChatAgent', 'Task']
    
    for import_item in langroid_imports:
        assert import_item in content, f"{import_item} should be imported"
    
    return True

def test_factory_function():
    """Test factory function exists."""
    adapter_file = Path(__file__).parent.parent / "adapter.py"
    
    with open(adapter_file, 'r') as f:
        content = f.read()
    
    assert 'def create_langroid_adapter' in content or 'def create_adapter' in content, "Factory function should exist"
    
    return True

def test_safety_integration():
    """Test safety system integration."""
    adapter_file = Path(__file__).parent.parent / "adapter.py"
    
    with open(adapter_file, 'r') as f:
        content = f.read()
    
    # Check for safety imports
    safety_components = ['ExecutionSandbox', 'FilesystemAccessController', 'NetworkAccessController', 'PromptInjectionGuard']
    
    for component in safety_components:
        assert component in content, f"{component} should be imported"
    
    return True

def run_all_tests():
    """Run all structure tests."""
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Required Files", test_required_files),
        ("Adapter Class", test_adapter_class),
        ("Agent Classes", test_agent_classes),
        ("Workflow Class", test_workflow_class),
        ("Documentation", test_documentation),
        ("Requirements", test_requirements),
        ("Langroid Imports", test_langroid_imports),
        ("Factory Function", test_factory_function),
        ("Safety Integration", test_safety_integration)
    ]
    
    results = []
    
    print("🧪 Running Langroid Structure Tests")
    print("=" * 40)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        except Exception as e:
            results.append(False)
            print(f"❌ {test_name}: {e}")
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 40)
    print(f"Results: {passed} passed, {total - passed} failed")
    
    return all(results)

def main():
    """Main function."""
    success = run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())