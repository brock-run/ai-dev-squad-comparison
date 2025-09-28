"""
Structure-only tests for LangGraph implementation

These tests validate the code structure without requiring external dependencies.
"""

import ast
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))


def test_adapter_file_exists():
    """Test that adapter.py exists."""
    adapter_file = Path(__file__).parent.parent / "adapter.py"
    assert adapter_file.exists(), "adapter.py file should exist"


def test_adapter_structure():
    """Test adapter.py structure."""
    adapter_file = Path(__file__).parent.parent / "adapter.py"
    
    with open(adapter_file, 'r') as f:
        content = f.read()
    
    # Parse AST
    tree = ast.parse(content)
    
    # Check for required classes
    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    assert 'LangGraphAdapter' in classes, "LangGraphAdapter class should exist"
    
    # Check for required methods
    methods = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    required_methods = ['run_task', 'get_capabilities', 'health_check']
    
    for method in required_methods:
        assert method in methods, f"{method} method should exist"


def test_state_file_exists():
    """Test that development_state.py exists."""
    state_file = Path(__file__).parent.parent / "state" / "development_state.py"
    assert state_file.exists(), "development_state.py file should exist"


def test_state_structure():
    """Test state file structure."""
    state_file = Path(__file__).parent.parent / "state" / "development_state.py"
    
    with open(state_file, 'r') as f:
        content = f.read()
    
    # Parse AST
    tree = ast.parse(content)
    
    # Check for required classes
    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    required_classes = ['WorkflowStatus', 'AgentRole', 'StateManager']
    
    for cls in required_classes:
        assert cls in classes, f"{cls} class should exist"


def test_factory_function():
    """Test factory function exists."""
    adapter_file = Path(__file__).parent.parent / "adapter.py"
    
    with open(adapter_file, 'r') as f:
        content = f.read()
    
    assert 'def create_langgraph_adapter' in content, "Factory function should exist"


def test_requirements_file():
    """Test requirements.txt exists and has content."""
    req_file = Path(__file__).parent.parent / "requirements.txt"
    assert req_file.exists(), "requirements.txt should exist"
    
    with open(req_file, 'r') as f:
        content = f.read()
    
    assert 'langgraph' in content.lower(), "Should include langgraph dependency"
    assert 'langchain' in content.lower(), "Should include langchain dependency"


def test_readme_exists():
    """Test README.md exists."""
    readme_file = Path(__file__).parent.parent / "README.md"
    assert readme_file.exists(), "README.md should exist"


def test_readme_content():
    """Test README.md has required content."""
    readme_file = Path(__file__).parent.parent / "README.md"
    
    with open(readme_file, 'r') as f:
        content = f.read()
    
    assert "# LangGraph" in content, "README should have LangGraph title"
    assert "## Setup" in content, "README should have Setup section"
    assert "## Usage" in content, "README should have Usage section"


if __name__ == "__main__":
    # Run tests manually if pytest not available
    import traceback
    
    test_functions = [
        test_adapter_file_exists,
        test_adapter_structure,
        test_state_file_exists,
        test_state_structure,
        test_factory_function,
        test_requirements_file,
        test_readme_exists,
        test_readme_content
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✅ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)