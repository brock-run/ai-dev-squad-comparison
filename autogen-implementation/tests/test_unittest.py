"""
Basic tests using unittest to verify that the testing infrastructure is working.

This file contains simple tests that use the unittest module from the Python
standard library to ensure that the testing infrastructure is set up correctly.
"""

import os
import sys
import unittest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def add(a, b):
    """Simple function to add two numbers."""
    return a + b

class TestBasic(unittest.TestCase):
    """Basic test cases."""
    
    def test_add(self):
        """Test the add function."""
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(0, 0), 0)
    
    def test_unittest_working(self):
        """Test that unittest is working."""
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()