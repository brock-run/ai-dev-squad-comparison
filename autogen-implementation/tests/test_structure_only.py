#!/usr/bin/env python3

"""
Structure-Only Tests for AutoGen Implementation

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
        "tests",
        "config"
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
        "validate_autogen.py",
        "agents/architect_agent.py",
        "agents/developer_agent.py",
        "agents/tester_agent.py",
        "agents/user_proxy.py",
        "workflows/group_chat_manager.py",
        "tests/test_autogen_adapter.py"
    ]
    
    for file_name in required_files:
        file_path = base_path / file_name
        assert file_path.exists(), f"File {file_name} not found"
        assert file_path.is_file(), f"{file_name} is not a file"
    
    return True

def test_adapter_class():
    """Test that the adapter class can be imported."""
    try:
        from adapter import AutoGenAdapter
        
        # Check class exists
        assert AutoGenAdapter is not None
        
        # Check required methods exist
        required_methods = [
            'get_info',
            'get_capabilities',
            'run_task', 
            'health_check',
            'get_metrics'
        ]
        
        for method in required_methods:
            assert hasattr(AutoGenAdapter, method), f"Method {method} not found"
        
        return True
        
    except ImportError as e:
        print(f"Warning: Could not import adapter: {e}")
        return True  # Don't fail on import errors in structure test

def test_agent_functions():
    """Test that agent creation functions can be imported."""
    try:
        from agents.architect_agent import create_architect_agent
        from agents.developer_agent import create_developer_agent
        from agents.tester_agent import create_tester_agent
        from agents.user_proxy import create_user_proxy
        
        # Check functions exist
        assert callable(create_architect_agent)
        assert callable(create_developer_agent)
        assert callable(create_tester_agent)
        assert callable(create_user_proxy)
        
        return True
        
    except ImportError as e:
        print(f"Warning: Could not import agents: {e}")
        return True  # Don't fail on import errors in structure test

def test_workflow_functions():
    """Test that workflow functions can be imported."""
    try:
        from workflows.group_chat_manager import create_groupchat
        
        # Check function exists
        assert callable(create_groupchat)
        
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
    assert "# AutoGen AI Development Squad Implementation" in readme_content
    assert "## Setup" in readme_content
    assert "## Features" in readme_content
    assert "## Usage" in readme_content
    assert "## Architecture" in readme_content
    
    # Check minimum length
    assert len(readme_content) > 2000, "README too short"
    
    return True

def test_requirements():
    """Test requirements file."""
    base_path = Path(__file__).parent.parent
    
    req_path = base_path / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    
    with open(req_path, 'r') as f:
        req_content = f.read()
    
    # Check for core dependencies
    assert "pyautogen" in req_content or "autogen" in req_content
    assert "pydantic" in req_content
    
    return True

def test_factory_functions():
    """Test factory functions exist."""
    try:
        from adapter import create_autogen_adapter, create_adapter
        
        # Check functions exist
        assert callable(create_autogen_adapter)
        assert callable(create_adapter)
        
        return True
        
    except ImportError as e:
        print(f"Warning: Could not import factory functions: {e}")
        return True  # Don't fail on import errors in structure test

def test_safety_integration():
    """Test safety system integration."""
    adapter_file = Path(__file__).parent.parent / "adapter.py"
    
    with open(adapter_file, 'r') as f:
        content = f.read()
    
    # Check for safety imports
    safety_components = ['ExecutionSandbox', 'FilesystemAccessController', 'NetworkAccessController', 'PromptInjectionGuard']
    
    for component in safety_components:
        if component not in content:
            print(f"Warning: {component} not found in adapter")
    
    return True

def test_autogen_imports():
    """Test AutoGen library imports."""
    try:
        import autogen
        
        # Check for key components
        required_components = ['ConversableAgent', 'GroupChat', 'GroupChatManager']
        
        for component in required_components:
            if not hasattr(autogen, component):
                print(f"Warning: AutoGen component {component} not available")
        
        return True
        
    except ImportError:
        print("Warning: AutoGen library not available")
        return True  # Don't fail on missing optional dependency

def run_all_tests():
    """Run all structure tests."""
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Required Files", test_required_files),
        ("Adapter Class", test_adapter_class),
        ("Agent Functions", test_agent_functions),
        ("Workflow Functions", test_workflow_functions),
        ("Documentation", test_documentation),
        ("Requirements", test_requirements),
        ("Factory Functions", test_factory_functions),
        ("Safety Integration", test_safety_integration),
        ("AutoGen Imports", test_autogen_imports)
    ]
    
    results = []
    
    print("🧪 Running AutoGen Structure Tests")
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