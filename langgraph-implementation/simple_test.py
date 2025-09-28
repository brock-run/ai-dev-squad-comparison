#!/usr/bin/env python3
"""
Simple test for LangGraph Adapter structure

This test checks the basic structure without importing dependencies.
"""

import ast
import sys
from pathlib import Path


def test_adapter_structure():
    """Test that the adapter file has the correct structure."""
    print("Testing LangGraph Adapter Structure...")
    
    adapter_file = Path(__file__).parent / "adapter.py"
    
    if not adapter_file.exists():
        print("✗ adapter.py file not found")
        return False
    
    try:
        with open(adapter_file, 'r') as f:
            content = f.read()
        
        # Parse the AST to check structure
        tree = ast.parse(content)
        
        # Check for required classes and methods
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        required_classes = ['LangGraphAdapter']
        required_methods = [
            'run_task', 'get_capabilities', 'health_check',
            '_architect_node', '_developer_node', '_tester_node',
            '_reviewer_node', '_vcs_node', '_error_handler_node'
        ]
        
        # Check classes
        for cls in required_classes:
            if cls in classes:
                print(f"✓ Class {cls} found")
            else:
                print(f"✗ Class {cls} missing")
                return False
        
        # Check methods
        for method in required_methods:
            if method in functions:
                print(f"✓ Method {method} found")
            else:
                print(f"✗ Method {method} missing")
                return False
        
        print(f"✓ File structure is valid ({len(content)} characters)")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in adapter.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading adapter.py: {e}")
        return False


def test_state_structure():
    """Test that the state file has the correct structure."""
    print("\nTesting Development State Structure...")
    
    state_file = Path(__file__).parent / "state" / "development_state.py"
    
    if not state_file.exists():
        print("✗ development_state.py file not found")
        return False
    
    try:
        with open(state_file, 'r') as f:
            content = f.read()
        
        # Parse the AST to check structure
        tree = ast.parse(content)
        
        # Check for required classes
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        required_classes = [
            'WorkflowStatus', 'AgentRole', 'AgentExecution',
            'DesignArtifact', 'CodeArtifact', 'TestArtifact',
            'ReviewArtifact', 'VCSArtifact', 'StateManager'
        ]
        
        for cls in required_classes:
            if cls in classes:
                print(f"✓ Class {cls} found")
            else:
                print(f"✗ Class {cls} missing")
                return False
        
        print(f"✓ State structure is valid")
        return True
        
    except Exception as e:
        print(f"✗ Error reading development_state.py: {e}")
        return False


def main():
    """Run all tests."""
    print("LangGraph Adapter Structure Test")
    print("=" * 40)
    
    tests = [
        test_adapter_structure,
        test_state_structure
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 40)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("✓ All structure tests passed!")
        return 0
    else:
        print("✗ Some structure tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)