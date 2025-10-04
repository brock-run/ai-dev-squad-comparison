# Code Verification System User Guide

The AI Dev Squad platform includes a comprehensive code verification system that ensures the quality, correctness, and security of generated code through multi-layered analysis.

## Overview

The verification system provides:

- **Multi-layer verification**: Functional testing, static analysis, and semantic verification
- **Automated quality assessment** with industry-standard tools
- **Security vulnerability detection** for safe code generation
- **Algorithm correctness verification** for specific problem types
- **Comprehensive scoring and reporting** with actionable recommendations

## Quick Start

### Basic Code Verification

```python
from benchmark.verifier import verify_code_basic

code = '''
def calculate_area(radius):
    """Calculate the area of a circle."""
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return 3.14159 * radius * radius
'''

result = verify_code_basic(code)
print(f"Overall Score: {result.overall_score:.2f}")
print(f"Summary: {result.summary}")
```

### Function Verification with Test Cases

```python
from benchmark.verifier import verify_function_complete

code = '''
def factorial(n):
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''

test_cases = [
    (0, 1),
    (1, 1),
    (5, 120),
    (3, 6)
]

result = verify_function_complete(code, "factorial", test_cases, "recursion")
print(f"Overall Score: {result.overall_score:.2f}")
print(f"Test Success Rate: {result.test_success_rate:.1%}")
```

## Verification Levels

### Basic Verification
Performs syntax checking and basic functional testing:

```python
from benchmark.verifier import verify_code_basic

result = verify_code_basic(code, test_code)
```

**Includes:**
- Syntax validation
- Import checking
- Basic test execution (if provided)

### Standard Verification
Adds static analysis and type checking:

```python
from benchmark.verifier import IntegratedVerifier, VerificationLevel

verifier = IntegratedVerifier()
result = verifier.verify_code_comprehensive(
    code=code,
    verification_level=VerificationLevel.STANDARD
)
```

**Includes:**
- All basic verification features
- Linting with multiple tools (pylint, flake8, pycodestyle)
- Type checking with mypy
- Code formatting analysis

### Comprehensive Verification
Adds semantic analysis and behavioral testing:

```python
result = verifier.verify_code_comprehensive(
    code=code,
    verification_level=VerificationLevel.COMPREHENSIVE,
    behavior_tests=behavior_tests,
    expected_algorithm="sorting"
)
```

**Includes:**
- All standard verification features
- Semantic correctness analysis
- Algorithm-specific verification
- Behavioral testing
- Security vulnerability detection

### Strict Verification
Uses the most rigorous checking rules:

```python
from benchmark.verifier import verify_code_strict

result = verify_code_strict(
    code=code,
    test_code=test_code,
    expected_functions=["main_function"],
    behavior_tests=behavior_tests
)
```

**Includes:**
- All comprehensive verification features
- Strict linting rules
- Enhanced type checking
- Rigorous security analysis

## Verification Components

### 1. Code Testing

Tests functional correctness through automated test execution:

```python
from benchmark.verifier.code_tests import CodeTestVerifier, TestFramework

verifier = CodeTestVerifier()
result = verifier.verify_code(
    code=code,
    test_code=test_code,
    expected_functions=["my_function"],
    test_framework=TestFramework.UNITTEST
)
```

**Supported Test Frameworks:**
- unittest (Python standard library)
- pytest (third-party testing framework)
- doctest (documentation testing)
- Custom test execution

**Features:**
- Syntax and import validation
- Test execution with timeout protection
- Coverage tracking (when available)
- Performance profiling

### 2. Static Analysis

Analyzes code quality without execution:

```python
from benchmark.verifier.lint_type import LintTypeVerifier

verifier = LintTypeVerifier()
result = verifier.verify_code(
    code=code,
    enable_type_checking=True,
    strict_mode=False
)
```

**Supported Tools:**
- **pylint**: Comprehensive Python linting
- **flake8**: Style guide enforcement
- **pycodestyle**: PEP 8 compliance
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **black**: Code formatting analysis
- **isort**: Import sorting analysis

**Analysis Categories:**
- Code style and formatting
- Potential bugs and errors
- Code complexity
- Type annotations
- Security vulnerabilities
- Import organization

### 3. Semantic Verification

Analyzes logical correctness and algorithmic properties:

```python
from benchmark.verifier.semantic import SemanticVerifier, BehaviorTest

behavior_tests = [
    BehaviorTest(
        name="test_sorting",
        input_data=[3, 1, 4, 1, 5],
        expected_output=[1, 1, 3, 4, 5],
        description="Should sort array in ascending order"
    )
]

verifier = SemanticVerifier()
result = verifier.verify_semantic_correctness(
    code=code,
    behavior_tests=behavior_tests,
    expected_algorithm="sorting"
)
```

**Analysis Types:**
- Logic correctness
- Algorithm-specific verification
- Behavioral testing
- Security issue detection
- Performance pattern analysis
- Resource management

**Supported Algorithms:**
- Sorting algorithms
- Search algorithms
- Recursive algorithms
- Custom algorithm patterns

## Creating Test Cases

### Unit Test Code
```python
test_code = '''
import unittest
from main import my_function

class TestMyFunction(unittest.TestCase):
    def test_basic_case(self):
        result = my_function(5)
        self.assertEqual(result, 25)
    
    def test_edge_case(self):
        result = my_function(0)
        self.assertEqual(result, 0)
    
    def test_error_case(self):
        with self.assertRaises(ValueError):
            my_function(-1)

if __name__ == '__main__':
    unittest.main()
'''
```

### Behavior Tests
```python
from benchmark.verifier import BehaviorTest

behavior_tests = [
    BehaviorTest(
        name="normal_case",
        input_data=5,
        expected_output=25,
        description="Normal positive input"
    ),
    BehaviorTest(
        name="zero_case",
        input_data=0,
        expected_output=0,
        description="Zero input edge case"
    ),
    BehaviorTest(
        name="large_input",
        input_data=100,
        expected_output=10000,
        description="Large input handling"
    )
]
```

## Understanding Results

### Overall Score
The overall score (0.0 to 1.0) combines:
- **Functional correctness** (40% weight): Test results
- **Code quality** (30% weight): Static analysis score
- **Semantic correctness** (30% weight): Logic and behavior analysis

### Result Components

```python
result = verify_code_comprehensive(...)

# Overall metrics
print(f"Overall Score: {result.overall_score:.2f}")
print(f"Test Success Rate: {result.test_success_rate:.1%}")
print(f"Total Issues: {result.total_issues}")
print(f"Critical Issues: {result.critical_issues}")

# Individual component results
if result.code_verification:
    print(f"Code Tests: {result.code_verification.overall_result.value}")

if result.static_analysis:
    print(f"Static Analysis: {result.static_analysis.overall_score:.1f}/10")
    print(f"Issue Summary: {result.static_analysis.issue_summary}")

if result.semantic_verification:
    print(f"Semantic Correctness: {result.semantic_verification.overall_correctness:.2f}")
    print(f"Behavior Tests: {result.semantic_verification.behavior_tests_passed} passed")
```

### Recommendations
```python
if result.recommendations:
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

## Common Use Cases

### Algorithm Verification
```python
def verify_sorting_algorithm(code, algorithm_name):
    test_cases = [
        ([3, 1, 4, 1, 5], [1, 1, 3, 4, 5]),
        ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
        ([], []),
        ([1], [1])
    ]
    
    return verify_function_complete(
        code=code,
        function_name=algorithm_name,
        test_cases=test_cases,
        algorithm_type="sorting"
    )

# Usage
bubble_sort_code = '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''

result = verify_sorting_algorithm(bubble_sort_code, "bubble_sort")
```

### Class Verification
```python
from benchmark.verifier.code_tests import verify_class_implementation

class_code = '''
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def get_history(self):
        return self.history.copy()
'''

result = verify_class_implementation(
    code=class_code,
    class_name="Calculator",
    required_methods=["add", "get_history"]
)
```

### Security Analysis
```python
# Code with potential security issues
risky_code = '''
def execute_user_command(command):
    import subprocess
    return subprocess.run(command, shell=True)  # Security risk!

def evaluate_expression(expr):
    return eval(expr)  # Security risk!
'''

result = verify_code_strict(risky_code)

# Check for security issues
if result.semantic_verification:
    security_issues = [
        issue for issue in result.semantic_verification.issues
        if "security" in issue.issue_type.value
    ]
    
    for issue in security_issues:
        print(f"Security Issue: {issue.message}")
        print(f"Suggestion: {issue.suggestion}")
```

## Configuration and Customization

### Timeout Configuration
```python
from benchmark.verifier import IntegratedVerifier

verifier = IntegratedVerifier(timeout_seconds=120)  # 2 minutes
```

### Tool Selection
```python
from benchmark.verifier.lint_type import LintTool

# Use specific linting tools
result = verifier.verify_code(
    code=code,
    lint_tools=[LintTool.PYLINT, LintTool.FLAKE8],
    enable_type_checking=True
)
```

### Custom Evaluation Criteria
```python
from benchmark.verifier.code_tests import BenchmarkTask

task = BenchmarkTask(
    task_id="custom_verification",
    name="Custom Verification Task",
    description="Custom verification with specific criteria",
    task_type=TaskType.CODING,
    prompt="Write a function...",
    evaluation_criteria={
        'length_check': {
            'min_length': 50,
            'max_length': 300,
            'optimal_length': 150
        },
        'keyword_presence': {
            'required': ['def', 'return'],
            'forbidden': ['eval', 'exec', 'import os']
        },
        'structure_check': {
            'expect_code': True,
            'expect_docstring': True
        }
    }
)
```

## Best Practices

### Code Quality
- Use comprehensive verification for production code
- Address critical and high-severity issues first
- Follow recommendations for code improvement
- Use type annotations for better analysis

### Performance
- Use basic verification for quick checks
- Enable parallel execution when possible
- Set appropriate timeouts for complex code
- Cache results for repeated verification

### Security
- Always use strict mode for security-sensitive code
- Review security recommendations carefully
- Avoid dangerous functions (eval, exec, shell=True)
- Validate all inputs and handle errors properly

### Testing
- Provide comprehensive test cases
- Include edge cases and error conditions
- Test both positive and negative scenarios
- Use behavior tests for algorithm verification

## Troubleshooting

### Common Issues

**Verification fails with import errors:**
```python
# Check if required packages are installed
pip install pylint flake8 mypy bandit black isort

# Or use basic verification without static analysis
result = verify_code_basic(code)
```

**Tests timeout frequently:**
```python
# Increase timeout
verifier = IntegratedVerifier(timeout_seconds=300)

# Or use sequential execution
result = verifier.verify_code_comprehensive(
    code=code,
    verification_level=VerificationLevel.BASIC
)
```

**Memory issues with large code:**
```python
# Use basic verification level
result = verify_code_basic(code)

# Or verify in smaller chunks
```

### Getting Help

- Check examples in `examples/verification_demo.py`
- Review test cases in `tests/test_verification_system.py`
- See the developer guide for advanced customization
- Enable debug logging for detailed information

## Integration with Benchmarking

The verification system integrates seamlessly with the benchmarking system:

```python
from common.benchmarking_tasks import BenchmarkTask

# Verification criteria are automatically used in benchmarks
task = BenchmarkTask(
    task_id="verified_task",
    name="Verified Coding Task",
    description="Task with comprehensive verification",
    task_type=TaskType.CODING,
    prompt="Implement a binary search function",
    evaluation_criteria={
        'verification_level': 'comprehensive',
        'expected_algorithm': 'search',
        'required_functions': ['binary_search']
    }
)
```

This verification system ensures that all generated code meets high standards for quality, correctness, and security.