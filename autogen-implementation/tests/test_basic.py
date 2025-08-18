"""
Basic tests to verify that the testing infrastructure is working.

This file contains simple tests that don't depend on external modules
to ensure that the testing infrastructure is set up correctly.
"""

import os
import sys
import pytest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def add(a, b):
    """Simple function to add two numbers."""
    return a + b

def test_add():
    """Test the add function."""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_pytest_working():
    """Test that pytest is working."""
    assert True

if __name__ == "__main__":
    pytest.main(["-v", __file__])