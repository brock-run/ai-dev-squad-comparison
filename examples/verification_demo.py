#!/usr/bin/env python3
"""
Verification System Demo

This script demonstrates the comprehensive verification capabilities
including code testing, static analysis, and semantic verification.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.verifier import (
    IntegratedVerifier, VerificationLevel, BehaviorTest,
    verify_function_complete, verify_code_basic, verify_code_strict
)


def demo_basic_verification():
    """Demonstrate basic code verification."""
    print("\n" + "="*60)
    print("BASIC CODE VERIFICATION DEMO")
    print("="*60)
    
    # Example 1: Simple valid function
    print("\n1. Testing a simple valid function:")
    simple_code = '''
def greet(name):
    """Greet a person by name."""
    return f"Hello, {name}!"
'''
    
    result = verify_code_basic(simple_code)
    print(f"   Overall Score: {result.overall_score:.2f}")
    print(f"   Summary: {result.summary}")
    
    # Example 2: Code with syntax error
    print("\n2. Testing code with syntax error:")
    broken_code = '''
def broken_function(
    # Missing closing parenthesis
    return "This won't work"
'''
    
    result = verify_code_basic(broken_code)
    print(f"   Overall Score: {result.overall_score:.2f}")
    print(f"   Summary: {result.summary}")
    if result.recommendations:
        print(f"   Recommendations: {result.recommendations[0]}")


def demo_function_verification():
    """Demonstrate comprehensive function verification."""
    print("\n" + "="*60)
    print("FUNCTION VERIFICATION DEMO")
    print("="*60)
    
    # Example: Factorial function
    print("\n1. Testing factorial function implementation:")
    factorial_code = '''
def factorial(n):
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
'''
    
    test_cases = [
        (0, 1),
        (1, 1),
        (5, 120),
        (3, 6)
    ]
    
    result = verify_function_complete(factorial_code, "factorial", test_cases, "recursion")
    
    print(f"   Overall Score: {result.overall_score:.2f}")
    print(f"   Test Success Rate: {result.test_success_rate:.1%}")
    print(f"   Total Issues: {result.total_issues}")
    print(f"   Summary: {result.summary}")
    
    if result.code_verification:
        print(f"   Code Tests: {result.code_verification.overall_result.value}")
    
    if result.static_analysis:
        print(f"   Static Analysis Score: {result.static_analysis.overall_score:.1f}/10")
    
    if result.semantic_verification:
        print(f"   Semantic Correctness: {result.semantic_verification.overall_correctness:.2f}")
        print(f"   Algorithm Complexity: {result.semantic_verification.algorithm_complexity}")
    
    if result.recommendations:
        print("   Recommendations:")
        for rec in result.recommendations[:3]:
            print(f"     - {rec}")


def demo_algorithm_verification():
    """Demonstrate algorithm-specific verification."""
    print("\n" + "="*60)
    print("ALGORITHM VERIFICATION DEMO")
    print("="*60)
    
    # Example 1: Correct sorting algorithm
    print("\n1. Testing correct bubble sort implementation:")
    correct_sort = '''
def bubble_sort(arr):
    """Sort array using bubble sort algorithm."""
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr
'''
    
    sort_test_cases = [
        ([3, 1, 4, 1, 5], [1, 1, 3, 4, 5]),
        ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
        ([], []),
        ([1], [1])
    ]
    
    result = verify_function_complete(correct_sort, "bubble_sort", sort_test_cases, "sorting")
    
    print(f"   Overall Score: {result.overall_score:.2f}")
    print(f"   Behavior Tests: {result.semantic_verification.behavior_tests_passed} passed, "
          f"{result.semantic_verification.behavior_tests_failed} failed")
    print(f"   Algorithm Complexity: {result.semantic_verification.algorithm_complexity}")
    
    # Example 2: Incorrect sorting algorithm
    print("\n2. Testing incorrect sorting implementation:")
    incorrect_sort = '''
def fake_sort(arr):
    """This doesn't actually sort - just returns the array."""
    # This is wrong - no sorting logic!
    return arr
'''
    
    result = verify_function_complete(incorrect_sort, "fake_sort", sort_test_cases, "sorting")
    
    print(f"   Overall Score: {result.overall_score:.2f}")
    print(f"   Behavior Tests: {result.semantic_verification.behavior_tests_passed} passed, "
          f"{result.semantic_verification.behavior_tests_failed} failed")
    
    if result.semantic_verification.issues:
        print("   Issues Found:")
        for issue in result.semantic_verification.issues[:3]:
            print(f"     - {issue.severity.value.upper()}: {issue.message}")


def demo_code_quality_analysis():
    """Demonstrate code quality analysis."""
    print("\n" + "="*60)
    print("CODE QUALITY ANALYSIS DEMO")
    print("="*60)
    
    # Example 1: Clean, well-formatted code
    print("\n1. Testing clean, well-formatted code:")
    clean_code = '''
def calculate_circle_area(radius: float) -> float:
    """
    Calculate the area of a circle.
    
    Args:
        radius: The radius of the circle.
        
    Returns:
        The area of the circle.
        
    Raises:
        ValueError: If radius is negative.
    """
    import math
    
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    
    return math.pi * radius * radius


def main() -> None:
    """Main function to demonstrate circle area calculation."""
    try:
        area = calculate_circle_area(5.0)
        print(f"Area of circle with radius 5.0: {area:.2f}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
'''
    
    result = verify_code_strict(clean_code, expected_functions=["calculate_circle_area", "main"])
    
    print(f"   Overall Score: {result.overall_score:.2f}")
    print(f"   Total Issues: {result.total_issues}")
    print(f"   Static Analysis Score: {result.static_analysis.overall_score:.1f}/10")
    
    # Example 2: Messy, problematic code
    print("\n2. Testing messy, problematic code:")
    messy_code = '''
import os,sys,json,re
def badFunction(x,y,z=None):
    global some_var
    some_var=10
    if x>y:
        result=x+y
    else:
        result=x-y
    if z:
        result=result*z
    print(result)
    return result
def unused_function():
    pass
x=badFunction(5,3)
'''
    
    result = verify_code_strict(messy_code)
    
    print(f"   Overall Score: {result.overall_score:.2f}")
    print(f"   Total Issues: {result.total_issues}")
    print(f"   Critical Issues: {result.critical_issues}")
    
    if result.static_analysis and result.static_analysis.recommendations:
        print("   Top Recommendations:")
        for rec in result.static_analysis.recommendations[:3]:
            print(f"     - {rec}")


def demo_security_analysis():
    """Demonstrate security issue detection."""
    print("\n" + "="*60)
    print("SECURITY ANALYSIS DEMO")
    print("="*60)
    
    # Example: Code with potential security issues
    print("\n1. Testing code with potential security issues:")
    risky_code = '''
import subprocess
import os

def execute_command(user_input):
    """Execute a system command - DANGEROUS!"""
    # This is unsafe - shell injection possible
    result = subprocess.run(user_input, shell=True, capture_output=True)
    return result.stdout

def evaluate_expression(expression):
    """Evaluate a mathematical expression - DANGEROUS!"""
    # This is unsafe - code injection possible
    return eval(expression)

def process_file(filename):
    """Process a file without validation."""
    # No path validation - directory traversal possible
    with open(filename, 'r') as f:
        return f.read()
'''
    
    result = verify_code_strict(risky_code)
    
    print(f"   Overall Score: {result.overall_score:.2f}")
    print(f"   Total Issues: {result.total_issues}")
    
    if result.semantic_verification:
        security_issues = [
            issue for issue in result.semantic_verification.issues
            if "security" in issue.issue_type.value or "dangerous" in issue.message.lower()
        ]
        
        if security_issues:
            print("   Security Issues Found:")
            for issue in security_issues:
                print(f"     - {issue.severity.value.upper()}: {issue.message}")
                if issue.suggestion:
                    print(f"       Suggestion: {issue.suggestion}")


def demo_comprehensive_verification():
    """Demonstrate comprehensive verification with all features."""
    print("\n" + "="*60)
    print("COMPREHENSIVE VERIFICATION DEMO")
    print("="*60)
    
    # Example: A complete class implementation
    print("\n1. Testing a complete class implementation:")
    class_code = '''
from typing import List, Optional

class Stack:
    """A simple stack implementation."""
    
    def __init__(self) -> None:
        """Initialize an empty stack."""
        self._items: List[int] = []
    
    def push(self, item: int) -> None:
        """
        Push an item onto the stack.
        
        Args:
            item: The item to push.
        """
        self._items.append(item)
    
    def pop(self) -> int:
        """
        Pop an item from the stack.
        
        Returns:
            The popped item.
            
        Raises:
            IndexError: If the stack is empty.
        """
        if self.is_empty():
            raise IndexError("Cannot pop from empty stack")
        return self._items.pop()
    
    def peek(self) -> int:
        """
        Peek at the top item without removing it.
        
        Returns:
            The top item.
            
        Raises:
            IndexError: If the stack is empty.
        """
        if self.is_empty():
            raise IndexError("Cannot peek at empty stack")
        return self._items[-1]
    
    def is_empty(self) -> bool:
        """Check if the stack is empty."""
        return len(self._items) == 0
    
    def size(self) -> int:
        """Get the size of the stack."""
        return len(self._items)


def test_stack() -> None:
    """Test the stack implementation."""
    stack = Stack()
    
    # Test basic operations
    assert stack.is_empty()
    
    stack.push(1)
    stack.push(2)
    stack.push(3)
    
    assert stack.size() == 3
    assert stack.peek() == 3
    assert stack.pop() == 3
    assert stack.size() == 2
    
    print("All stack tests passed!")


if __name__ == "__main__":
    test_stack()
'''
    
    test_code = '''
import unittest
from main import Stack

class TestStack(unittest.TestCase):
    def setUp(self):
        self.stack = Stack()
    
    def test_empty_stack(self):
        self.assertTrue(self.stack.is_empty())
        self.assertEqual(self.stack.size(), 0)
    
    def test_push_and_pop(self):
        self.stack.push(1)
        self.stack.push(2)
        self.assertEqual(self.stack.size(), 2)
        self.assertEqual(self.stack.pop(), 2)
        self.assertEqual(self.stack.pop(), 1)
        self.assertTrue(self.stack.is_empty())
    
    def test_peek(self):
        self.stack.push(42)
        self.assertEqual(self.stack.peek(), 42)
        self.assertEqual(self.stack.size(), 1)  # Should not remove item
    
    def test_empty_pop_error(self):
        with self.assertRaises(IndexError):
            self.stack.pop()
    
    def test_empty_peek_error(self):
        with self.assertRaises(IndexError):
            self.stack.peek()

if __name__ == '__main__':
    unittest.main()
'''
    
    # Create behavior tests
    behavior_tests = [
        BehaviorTest(
            name="stack_operations",
            input_data=None,
            expected_output=None,
            description="Test basic stack operations"
        )
    ]
    
    verifier = IntegratedVerifier(timeout_seconds=30)
    try:
        result = verifier.verify_code_comprehensive(
            code=class_code,
            test_code=test_code,
            expected_functions=["test_stack"],
            behavior_tests=behavior_tests,
            verification_level=VerificationLevel.COMPREHENSIVE
        )
        
        print(f"   Overall Score: {result.overall_score:.2f}")
        print(f"   Verification Level: {result.verification_level.value}")
        print(f"   Test Success Rate: {result.test_success_rate:.1%}")
        print(f"   Total Issues: {result.total_issues}")
        print(f"   Summary: {result.summary}")
        
        print(f"\n   Detailed Results:")
        if result.code_verification:
            print(f"     Code Tests: {result.code_verification.overall_result.value}")
            for execution in result.code_verification.test_executions:
                print(f"       {execution.framework.value}: {execution.tests_passed}/{execution.tests_run} passed")
        
        if result.static_analysis:
            print(f"     Static Analysis: {result.static_analysis.overall_score:.1f}/10")
            print(f"       Tools used: {len(result.static_analysis.lint_results)}")
        
        if result.semantic_verification:
            print(f"     Semantic Analysis: {result.semantic_verification.overall_correctness:.2f}")
            print(f"       Complexity: {result.semantic_verification.algorithm_complexity}")
            print(f"       Issues found: {len(result.semantic_verification.issues)}")
        
        if result.recommendations:
            print(f"\n   Top Recommendations:")
            for rec in result.recommendations[:5]:
                print(f"     - {rec}")
        
        print(f"\n   Execution Time: {result.metadata.get('total_execution_time', 0):.2f}s")
    
    finally:
        verifier.cleanup()


def main():
    """Run the complete verification system demo."""
    print("AI Dev Squad - Comprehensive Verification System Demo")
    print("=" * 60)
    print("This demo showcases the verification capabilities including:")
    print("- Code testing and functional verification")
    print("- Static analysis (linting, type checking)")
    print("- Semantic verification (logic, algorithms)")
    print("- Security analysis")
    print("- Integrated comprehensive verification")
    
    try:
        # Run all demo sections
        demo_basic_verification()
        demo_function_verification()
        demo_algorithm_verification()
        demo_code_quality_analysis()
        demo_security_analysis()
        demo_comprehensive_verification()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✓ Syntax and import validation")
        print("✓ Functional testing with multiple frameworks")
        print("✓ Static analysis with multiple linting tools")
        print("✓ Type checking and annotation verification")
        print("✓ Semantic correctness and logic analysis")
        print("✓ Algorithm-specific verification")
        print("✓ Security vulnerability detection")
        print("✓ Performance and complexity analysis")
        print("✓ Integrated scoring and recommendations")
        print("✓ Multiple verification levels (basic to strict)")
        
        print("\nNext Steps:")
        print("- Integrate with benchmark task definitions")
        print("- Configure verification criteria for specific tasks")
        print("- Set up automated verification in CI/CD pipelines")
        print("- Customize verification rules for different code types")
        print("- Add domain-specific verification patterns")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())