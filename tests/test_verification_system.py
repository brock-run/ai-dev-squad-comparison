#!/usr/bin/env python3
"""
Tests for the Comprehensive Verification System

This module contains tests for all verification components including
code testing, static analysis, semantic verification, and integration.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

# Import verification system components
from benchmark.verifier import (
    IntegratedVerifier, IntegratedVerificationResult, VerificationLevel,
    verify_function_complete, verify_code_basic, verify_code_strict, BehaviorTest
)
from benchmark.verifier.code_tests import (
    CodeTestVerifier, TestFramework, TestResult, verify_function_implementation
)
from benchmark.verifier.lint_type import (
    LintTypeVerifier, LintTool, quick_lint_check, comprehensive_analysis
)
from benchmark.verifier.semantic import (
    SemanticVerifier, SemanticIssueType, verify_algorithm_correctness
)


class TestCodeTestVerifier(unittest.TestCase):
    """Test code testing verification functionality."""
    
    def setUp(self):
        self.verifier = CodeTestVerifier(timeout_seconds=10)
    
    def tearDown(self):
        self.verifier.cleanup()
    
    def test_valid_function_verification(self):
        """Test verification of a valid function."""
        code = '''
def factorial(n):
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
'''
        
        test_code = '''
import unittest
from main import factorial

class TestFactorial(unittest.TestCase):
    def test_factorial_zero(self):
        self.assertEqual(factorial(0), 1)
    
    def test_factorial_one(self):
        self.assertEqual(factorial(1), 1)
    
    def test_factorial_five(self):
        self.assertEqual(factorial(5), 120)

if __name__ == '__main__':
    unittest.main()
'''
        
        result = self.verifier.verify_code(
            code=code,
            test_code=test_code,
            expected_functions=['factorial']
        )
        
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.imports_valid)
        self.assertEqual(result.overall_result, TestResult.PASS)
        self.assertGreater(len(result.test_executions), 0)
        
        # Check that tests passed
        execution = result.test_executions[0]
        self.assertEqual(execution.result, TestResult.PASS)
        self.assertGreater(execution.tests_passed, 0)
    
    def test_syntax_error_detection(self):
        """Test detection of syntax errors."""
        invalid_code = '''
def broken_function(
    # Missing closing parenthesis
    return "broken"
'''
        
        result = self.verifier.verify_code(code=invalid_code)
        
        self.assertFalse(result.syntax_valid)
        self.assertEqual(result.overall_result, TestResult.ERROR)
    
    def test_missing_function_detection(self):
        """Test detection of missing expected functions."""
        code = '''
def wrong_function():
    return "not what we expected"
'''
        
        result = self.verifier.verify_code(
            code=code,
            expected_functions=['expected_function']
        )
        
        self.assertTrue(result.syntax_valid)
        self.assertEqual(result.overall_result, TestResult.FAIL)
        self.assertIn("Missing expected functions", result.error_messages[0])
    
    def test_convenience_function(self):
        """Test convenience function for function verification."""
        code = '''
def reverse_string(s):
    return s[::-1]
'''
        
        test_cases = [
            ("hello", "olleh"),
            ("world", "dlrow"),
            ("", ""),
            ("a", "a")
        ]
        
        result = verify_function_implementation(code, "reverse_string", test_cases)
        
        self.assertTrue(result.syntax_valid)
        self.assertEqual(result.overall_result, TestResult.PASS)


class TestLintTypeVerifier(unittest.TestCase):
    """Test static analysis verification functionality."""
    
    def setUp(self):
        self.verifier = LintTypeVerifier(timeout_seconds=10)
    
    def tearDown(self):
        self.verifier.cleanup()
    
    def test_clean_code_analysis(self):
        """Test analysis of clean, well-formatted code."""
        clean_code = '''
def calculate_area(radius: float) -> float:
    """Calculate the area of a circle."""
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return 3.14159 * radius * radius


def main() -> None:
    """Main function."""
    area = calculate_area(5.0)
    print(f"Area: {area}")


if __name__ == "__main__":
    main()
'''
        
        result = self.verifier.verify_code(
            code=clean_code,
            enable_type_checking=True,
            strict_mode=False
        )
        
        self.assertGreater(result.overall_score, 7.0)  # Should be high quality
        self.assertLess(len([r for r in result.lint_results if not r.success]), 2)
    
    def test_problematic_code_analysis(self):
        """Test analysis of code with various issues."""
        problematic_code = '''
import os,sys,json
def badFunction(x,y):
    z=x+y
    if z>10:
        print("big number")
    return z
def unused_function():
    pass
'''
        
        result = self.verifier.verify_code(
            code=problematic_code,
            enable_type_checking=True,
            strict_mode=True
        )
        
        self.assertLess(result.overall_score, 7.0)  # Should detect issues
        self.assertGreater(len(result.recommendations), 0)
        
        # Should detect style issues
        total_issues = sum(result.issue_summary.values())
        self.assertGreater(total_issues, 0)
    
    def test_convenience_functions(self):
        """Test convenience functions for quick analysis."""
        sample_code = '''
def example_function(x):
    return x * 2
'''
        
        # Test quick lint check
        quick_result = quick_lint_check(sample_code)
        self.assertIsNotNone(quick_result.overall_score)
        
        # Test comprehensive analysis
        comprehensive_result = comprehensive_analysis(sample_code)
        self.assertIsNotNone(comprehensive_result.overall_score)
        
        # Comprehensive should have more checks
        self.assertGreaterEqual(
            len(comprehensive_result.lint_results),
            len(quick_result.lint_results)
        )


class TestSemanticVerifier(unittest.TestCase):
    """Test semantic verification functionality."""
    
    def setUp(self):
        self.verifier = SemanticVerifier()
    
    def tearDown(self):
        self.verifier.cleanup()
    
    def test_correct_algorithm_verification(self):
        """Test verification of a correct algorithm."""
        correct_code = '''
def binary_search(arr, target):
    """Binary search implementation."""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1
'''
        
        behavior_tests = [
            BehaviorTest(
                name="found_element",
                input_data=([1, 2, 3, 4, 5], 3),
                expected_output=2,
                description="Should find element at correct index"
            ),
            BehaviorTest(
                name="not_found",
                input_data=([1, 2, 3, 4, 5], 6),
                expected_output=-1,
                description="Should return -1 for missing element"
            )
        ]
        
        result = self.verifier.verify_semantic_correctness(
            code=correct_code,
            behavior_tests=behavior_tests,
            expected_algorithm="search"
        )
        
        self.assertGreater(result.overall_correctness, 0.7)
        self.assertEqual(result.behavior_tests_passed, 2)
        self.assertEqual(result.behavior_tests_failed, 0)
    
    def test_problematic_algorithm_detection(self):
        """Test detection of algorithmic problems."""
        problematic_code = '''
def infinite_loop_function():
    while True:
        print("This will run forever")
        # No break or return statement

def unsafe_division(a, b):
    return a / b  # No validation for b == 0

def unused_variable_function():
    x = 10
    y = 20
    return 5  # x and y are unused
'''
        
        result = self.verifier.verify_semantic_correctness(code=problematic_code)
        
        # Should detect multiple issues
        self.assertGreater(len(result.issues), 0)
        
        # Check for specific issue types
        issue_types = [issue.issue_type for issue in result.issues]
        self.assertIn(SemanticIssueType.INFINITE_LOOP, issue_types)
        
        # Should have suggestions
        self.assertGreater(len(result.suggestions), 0)
    
    def test_recursive_algorithm_verification(self):
        """Test verification of recursive algorithms."""
        recursive_code = '''
def factorial(n):
    if n <= 1:  # Base case
        return 1
    return n * factorial(n - 1)  # Recursive case

def bad_recursion(n):
    return bad_recursion(n - 1)  # No base case!
'''
        
        result = self.verifier.verify_semantic_correctness(
            code=recursive_code,
            expected_algorithm="recursion"
        )
        
        # Should detect missing base case in bad_recursion
        algorithm_errors = [
            issue for issue in result.issues 
            if issue.issue_type == SemanticIssueType.ALGORITHM_ERROR
        ]
        self.assertGreater(len(algorithm_errors), 0)
    
    def test_convenience_function(self):
        """Test convenience function for algorithm verification."""
        sorting_code = '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        
        test_cases = [
            ([3, 1, 4, 1, 5], [1, 1, 3, 4, 5]),
            ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
            ([], []),
            ([1], [1])
        ]
        
        result = verify_algorithm_correctness(sorting_code, "sorting", test_cases)
        
        self.assertGreater(result.overall_correctness, 0.5)
        self.assertGreater(result.behavior_tests_passed, 0)


class TestIntegratedVerifier(unittest.TestCase):
    """Test integrated verification system."""
    
    def setUp(self):
        self.verifier = IntegratedVerifier(timeout_seconds=15)
    
    def tearDown(self):
        self.verifier.cleanup()
    
    def test_comprehensive_verification(self):
        """Test comprehensive verification of good code."""
        good_code = '''
def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_iterative(n: int) -> int:
    """Calculate the nth Fibonacci number iteratively."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
'''
        
        test_code = '''
import unittest
from main import fibonacci, fibonacci_iterative

class TestFibonacci(unittest.TestCase):
    def test_fibonacci_base_cases(self):
        self.assertEqual(fibonacci(0), 0)
        self.assertEqual(fibonacci(1), 1)
    
    def test_fibonacci_recursive(self):
        self.assertEqual(fibonacci(5), 5)
        self.assertEqual(fibonacci(7), 13)
    
    def test_fibonacci_iterative(self):
        self.assertEqual(fibonacci_iterative(5), 5)
        self.assertEqual(fibonacci_iterative(7), 13)

if __name__ == '__main__':
    unittest.main()
'''
        
        behavior_tests = [
            BehaviorTest(
                name="fib_zero",
                input_data=0,
                expected_output=0,
                description="Fibonacci of 0 should be 0"
            ),
            BehaviorTest(
                name="fib_five",
                input_data=5,
                expected_output=5,
                description="Fibonacci of 5 should be 5"
            )
        ]
        
        result = self.verifier.verify_code_comprehensive(
            code=good_code,
            test_code=test_code,
            expected_functions=['fibonacci', 'fibonacci_iterative'],
            behavior_tests=behavior_tests,
            expected_algorithm="recursion",
            verification_level=VerificationLevel.COMPREHENSIVE
        )
        
        self.assertGreater(result.overall_score, 0.7)
        self.assertIsNotNone(result.code_verification)
        self.assertIsNotNone(result.static_analysis)
        self.assertIsNotNone(result.semantic_verification)
        self.assertGreater(result.test_success_rate, 0.8)
        self.assertIn("Good", result.summary)
    
    def test_basic_verification_level(self):
        """Test basic verification level."""
        simple_code = '''
def add(a, b):
    return a + b
'''
        
        result = self.verifier.verify_code_comprehensive(
            code=simple_code,
            verification_level=VerificationLevel.BASIC
        )
        
        # Basic level should not include static analysis or semantic verification
        self.assertIsNone(result.static_analysis)
        self.assertIsNone(result.semantic_verification)
        self.assertEqual(result.verification_level, VerificationLevel.BASIC)
    
    def test_strict_verification_level(self):
        """Test strict verification level."""
        code_with_issues = '''
def messy_function(x,y):
    z=x+y
    if z>10:
        print("big")
    return z
'''
        
        result = self.verifier.verify_code_comprehensive(
            code=code_with_issues,
            verification_level=VerificationLevel.STRICT
        )
        
        # Strict mode should detect more issues
        self.assertIsNotNone(result.static_analysis)
        self.assertIsNotNone(result.semantic_verification)
        self.assertGreater(result.total_issues, 0)
        self.assertGreater(len(result.recommendations), 0)
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        code = '''
def square(x):
    return x * x
'''
        
        # Test basic verification
        basic_result = verify_code_basic(code)
        self.assertEqual(basic_result.verification_level, VerificationLevel.BASIC)
        
        # Test function verification
        test_cases = [(2, 4), (3, 9), (0, 0)]
        function_result = verify_function_complete(code, "square", test_cases)
        self.assertEqual(function_result.verification_level, VerificationLevel.COMPREHENSIVE)
        self.assertGreater(function_result.test_success_rate, 0.8)
        
        # Test strict verification
        strict_result = verify_code_strict(code, expected_functions=["square"])
        self.assertEqual(strict_result.verification_level, VerificationLevel.STRICT)


class TestVerificationIntegration(unittest.TestCase):
    """Test integration between different verification systems."""
    
    def test_error_propagation(self):
        """Test that errors are properly propagated between systems."""
        broken_code = '''
def broken_function(
    # Syntax error - missing closing parenthesis
    return "broken"
'''
        
        verifier = IntegratedVerifier()
        try:
            result = verifier.verify_code_comprehensive(
                code=broken_code,
                verification_level=VerificationLevel.COMPREHENSIVE
            )
            
            # Should handle syntax errors gracefully
            self.assertEqual(result.overall_score, 0.0)
            self.assertIn("error", result.summary.lower())
            self.assertGreater(len(result.recommendations), 0)
        finally:
            verifier.cleanup()
    
    def test_performance_with_large_code(self):
        """Test verification performance with larger code samples."""
        large_code = '''
class Calculator:
    """A comprehensive calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """Calculate power."""
        result = base ** exponent
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result
    
    def get_history(self) -> list:
        """Get calculation history."""
        return self.history.copy()
    
    def clear_history(self) -> None:
        """Clear calculation history."""
        self.history.clear()


def main():
    """Main function to demonstrate calculator."""
    calc = Calculator()
    
    # Perform some calculations
    print(calc.add(5, 3))
    print(calc.multiply(4, 7))
    print(calc.divide(10, 2))
    
    # Show history
    for entry in calc.get_history():
        print(entry)


if __name__ == "__main__":
    main()
'''
        
        verifier = IntegratedVerifier(timeout_seconds=30)
        try:
            result = verifier.verify_code_comprehensive(
                code=large_code,
                verification_level=VerificationLevel.STANDARD
            )
            
            # Should complete within reasonable time
            self.assertIsNotNone(result)
            self.assertGreater(result.overall_score, 0.0)
            
            # Should detect the class and methods
            if result.semantic_verification:
                self.assertGreater(
                    result.semantic_verification.metadata.get('total_functions', 0), 5
                )
                self.assertGreater(
                    result.semantic_verification.metadata.get('total_classes', 0), 0
                )
        finally:
            verifier.cleanup()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)