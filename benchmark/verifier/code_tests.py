#!/usr/bin/env python3
"""
Code Test Verification System

This module provides automated test execution and verification capabilities
for benchmark tasks that involve code generation and modification.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)


class TestResult(Enum):
    """Test execution results."""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIP = "skip"


class TestFramework(Enum):
    """Supported test frameworks."""
    UNITTEST = "unittest"
    PYTEST = "pytest"
    DOCTEST = "doctest"
    CUSTOM = "custom"


@dataclass
class TestExecution:
    """Results from test execution."""
    framework: TestFramework
    result: TestResult
    output: str
    error_output: str
    duration: float
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    coverage_percentage: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeVerificationResult:
    """Complete code verification results."""
    syntax_valid: bool
    imports_valid: bool
    test_executions: List[TestExecution]
    overall_result: TestResult
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeTestVerifier:
    """Verifies code by executing tests and checking functionality."""
    
    def __init__(self, timeout_seconds: int = 30, enable_coverage: bool = True):
        """
        Initialize code test verifier.
        
        Args:
            timeout_seconds: Maximum time to allow for test execution.
            enable_coverage: Whether to collect code coverage metrics.
        """
        self.timeout_seconds = timeout_seconds
        self.enable_coverage = enable_coverage
        self.temp_dirs = []
    
    def verify_code(self, code: str, test_code: Optional[str] = None,
                   expected_functions: Optional[List[str]] = None,
                   test_framework: TestFramework = TestFramework.UNITTEST) -> CodeVerificationResult:
        """
        Verify code by running tests and checking functionality.
        
        Args:
            code: The code to verify.
            test_code: Optional test code to run against the main code.
            expected_functions: List of function names that should be present.
            test_framework: Test framework to use for execution.
            
        Returns:
            CodeVerificationResult with detailed verification results.
        """
        result = CodeVerificationResult(
            syntax_valid=False,
            imports_valid=False,
            test_executions=[],
            overall_result=TestResult.ERROR
        )
        
        try:
            # 1. Check syntax validity
            result.syntax_valid = self._check_syntax(code)
            if not result.syntax_valid:
                result.error_messages.append("Code has syntax errors")
                return result
            
            # 2. Check imports validity
            result.imports_valid = self._check_imports(code)
            if not result.imports_valid:
                result.warnings.append("Some imports may not be available")
            
            # 3. Check expected functions are present
            if expected_functions:
                missing_functions = self._check_expected_functions(code, expected_functions)
                if missing_functions:
                    result.error_messages.append(f"Missing expected functions: {missing_functions}")
                    result.overall_result = TestResult.FAIL
                    return result
            
            # 4. Execute tests
            if test_code:
                test_execution = self._execute_tests(code, test_code, test_framework)
                result.test_executions.append(test_execution)
                
                if test_execution.result == TestResult.PASS:
                    result.overall_result = TestResult.PASS
                else:
                    result.overall_result = test_execution.result
            else:
                # If no tests provided, try to run the code to check for runtime errors
                execution_result = self._execute_code_basic(code)
                result.test_executions.append(execution_result)
                result.overall_result = execution_result.result
            
            # 5. Add metadata
            result.metadata = {
                'code_length': len(code),
                'line_count': len(code.split('\n')),
                'has_docstrings': '"""' in code or "'''" in code,
                'has_type_hints': '->' in code or ': str' in code or ': int' in code,
                'complexity_estimate': self._estimate_complexity(code)
            }
            
        except Exception as e:
            logger.error(f"Error during code verification: {e}")
            result.error_messages.append(f"Verification error: {str(e)}")
            result.overall_result = TestResult.ERROR
        
        return result
    
    def _check_syntax(self, code: str) -> bool:
        """Check if code has valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.debug(f"Syntax error in code: {e}")
            return False
    
    def _check_imports(self, code: str) -> bool:
        """Check if all imports in the code are available."""
        try:
            # Parse the AST to find import statements
            tree = ast.parse(code)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Try to import each module
            for module_name in imports:
                try:
                    __import__(module_name.split('.')[0])
                except ImportError:
                    logger.debug(f"Import not available: {module_name}")
                    return False
            
            return True
        except Exception as e:
            logger.debug(f"Error checking imports: {e}")
            return False
    
    def _check_expected_functions(self, code: str, expected_functions: List[str]) -> List[str]:
        """Check if expected functions are present in the code."""
        try:
            tree = ast.parse(code)
            defined_functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    defined_functions.append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    defined_functions.append(node.name)
            
            missing = [func for func in expected_functions if func not in defined_functions]
            return missing
        except Exception as e:
            logger.debug(f"Error checking expected functions: {e}")
            return expected_functions  # Assume all are missing if we can't parse
    
    def _execute_tests(self, code: str, test_code: str, 
                      framework: TestFramework) -> TestExecution:
        """Execute tests against the code."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        try:
            # Write code and test files
            code_file = Path(temp_dir) / "main.py"
            test_file = Path(temp_dir) / "test_main.py"
            
            with open(code_file, 'w') as f:
                f.write(code)
            
            with open(test_file, 'w') as f:
                f.write(test_code)
            
            # Execute tests based on framework
            if framework == TestFramework.UNITTEST:
                return self._run_unittest(temp_dir, test_file)
            elif framework == TestFramework.PYTEST:
                return self._run_pytest(temp_dir, test_file)
            elif framework == TestFramework.DOCTEST:
                return self._run_doctest(temp_dir, code_file)
            else:
                return self._run_custom_test(temp_dir, code_file, test_file)
        
        except Exception as e:
            logger.error(f"Error executing tests: {e}")
            return TestExecution(
                framework=framework,
                result=TestResult.ERROR,
                output="",
                error_output=str(e),
                duration=0.0
            )
    
    def _execute_code_basic(self, code: str) -> TestExecution:
        """Execute code without specific tests to check for runtime errors."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        try:
            code_file = Path(temp_dir) / "main.py"
            
            with open(code_file, 'w') as f:
                f.write(code)
            
            start_time = time.time()
            
            # Try to import and execute the code
            result = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, '{temp_dir}'); import main"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=temp_dir
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return TestExecution(
                    framework=TestFramework.CUSTOM,
                    result=TestResult.PASS,
                    output=result.stdout,
                    error_output=result.stderr,
                    duration=duration,
                    tests_run=1,
                    tests_passed=1
                )
            else:
                return TestExecution(
                    framework=TestFramework.CUSTOM,
                    result=TestResult.FAIL,
                    output=result.stdout,
                    error_output=result.stderr,
                    duration=duration,
                    tests_run=1,
                    tests_failed=1
                )
        
        except subprocess.TimeoutExpired:
            return TestExecution(
                framework=TestFramework.CUSTOM,
                result=TestResult.TIMEOUT,
                output="",
                error_output="Execution timed out",
                duration=self.timeout_seconds
            )
        except Exception as e:
            return TestExecution(
                framework=TestFramework.CUSTOM,
                result=TestResult.ERROR,
                output="",
                error_output=str(e),
                duration=0.0
            )
    
    def _run_unittest(self, temp_dir: str, test_file: Path) -> TestExecution:
        """Run unittest framework tests."""
        start_time = time.time()
        
        try:
            cmd = [sys.executable, "-m", "unittest", "discover", "-s", temp_dir, "-p", "test_*.py", "-v"]
            
            if self.enable_coverage:
                cmd = [sys.executable, "-m", "coverage", "run", "--source", temp_dir, "-m", "unittest", 
                      "discover", "-s", temp_dir, "-p", "test_*.py", "-v"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=temp_dir
            )
            
            duration = time.time() - start_time
            
            # Parse unittest output
            tests_run, tests_passed, tests_failed, tests_skipped = self._parse_unittest_output(result.stderr)
            
            # Get coverage if enabled
            coverage_percentage = None
            if self.enable_coverage and result.returncode == 0:
                coverage_percentage = self._get_coverage_percentage(temp_dir)
            
            test_result = TestResult.PASS if result.returncode == 0 else TestResult.FAIL
            
            return TestExecution(
                framework=TestFramework.UNITTEST,
                result=test_result,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                tests_skipped=tests_skipped,
                coverage_percentage=coverage_percentage
            )
        
        except subprocess.TimeoutExpired:
            return TestExecution(
                framework=TestFramework.UNITTEST,
                result=TestResult.TIMEOUT,
                output="",
                error_output="Test execution timed out",
                duration=self.timeout_seconds
            )
        except Exception as e:
            return TestExecution(
                framework=TestFramework.UNITTEST,
                result=TestResult.ERROR,
                output="",
                error_output=str(e),
                duration=time.time() - start_time
            )
    
    def _run_pytest(self, temp_dir: str, test_file: Path) -> TestExecution:
        """Run pytest framework tests."""
        start_time = time.time()
        
        try:
            cmd = [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"]
            
            if self.enable_coverage:
                cmd.extend(["--cov", temp_dir, "--cov-report", "term-missing"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=temp_dir
            )
            
            duration = time.time() - start_time
            
            # Parse pytest output
            tests_run, tests_passed, tests_failed, tests_skipped = self._parse_pytest_output(result.stdout)
            
            # Extract coverage from output if available
            coverage_percentage = None
            if self.enable_coverage:
                coverage_percentage = self._extract_pytest_coverage(result.stdout)
            
            test_result = TestResult.PASS if result.returncode == 0 else TestResult.FAIL
            
            return TestExecution(
                framework=TestFramework.PYTEST,
                result=test_result,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                tests_skipped=tests_skipped,
                coverage_percentage=coverage_percentage
            )
        
        except subprocess.TimeoutExpired:
            return TestExecution(
                framework=TestFramework.PYTEST,
                result=TestResult.TIMEOUT,
                output="",
                error_output="Test execution timed out",
                duration=self.timeout_seconds
            )
        except Exception as e:
            return TestExecution(
                framework=TestFramework.PYTEST,
                result=TestResult.ERROR,
                output="",
                error_output=str(e),
                duration=time.time() - start_time
            )
    
    def _run_doctest(self, temp_dir: str, code_file: Path) -> TestExecution:
        """Run doctest on the code file."""
        start_time = time.time()
        
        try:
            cmd = [sys.executable, "-m", "doctest", str(code_file), "-v"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=temp_dir
            )
            
            duration = time.time() - start_time
            
            # Parse doctest output
            tests_run, tests_passed, tests_failed = self._parse_doctest_output(result.stdout)
            
            test_result = TestResult.PASS if result.returncode == 0 else TestResult.FAIL
            
            return TestExecution(
                framework=TestFramework.DOCTEST,
                result=test_result,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed
            )
        
        except subprocess.TimeoutExpired:
            return TestExecution(
                framework=TestFramework.DOCTEST,
                result=TestResult.TIMEOUT,
                output="",
                error_output="Test execution timed out",
                duration=self.timeout_seconds
            )
        except Exception as e:
            return TestExecution(
                framework=TestFramework.DOCTEST,
                result=TestResult.ERROR,
                output="",
                error_output=str(e),
                duration=time.time() - start_time
            )
    
    def _run_custom_test(self, temp_dir: str, code_file: Path, test_file: Path) -> TestExecution:
        """Run custom test by executing the test file directly."""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=temp_dir
            )
            
            duration = time.time() - start_time
            
            test_result = TestResult.PASS if result.returncode == 0 else TestResult.FAIL
            
            return TestExecution(
                framework=TestFramework.CUSTOM,
                result=test_result,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration,
                tests_run=1,
                tests_passed=1 if result.returncode == 0 else 0,
                tests_failed=0 if result.returncode == 0 else 1
            )
        
        except subprocess.TimeoutExpired:
            return TestExecution(
                framework=TestFramework.CUSTOM,
                result=TestResult.TIMEOUT,
                output="",
                error_output="Test execution timed out",
                duration=self.timeout_seconds
            )
        except Exception as e:
            return TestExecution(
                framework=TestFramework.CUSTOM,
                result=TestResult.ERROR,
                output="",
                error_output=str(e),
                duration=time.time() - start_time
            )
    
    def _parse_unittest_output(self, output: str) -> Tuple[int, int, int, int]:
        """Parse unittest output to extract test counts."""
        tests_run = tests_passed = tests_failed = tests_skipped = 0
        
        lines = output.split('\n')
        for line in lines:
            if 'Ran' in line and 'test' in line:
                # Example: "Ran 5 tests in 0.001s"
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        tests_run = int(parts[1])
                    except ValueError:
                        pass
            elif 'FAILED' in line:
                # Example: "FAILED (failures=2, errors=1)"
                if 'failures=' in line:
                    try:
                        failures_part = line.split('failures=')[1].split(',')[0].split(')')[0]
                        tests_failed += int(failures_part)
                    except (ValueError, IndexError):
                        pass
                if 'errors=' in line:
                    try:
                        errors_part = line.split('errors=')[1].split(',')[0].split(')')[0]
                        tests_failed += int(errors_part)
                    except (ValueError, IndexError):
                        pass
            elif 'skipped=' in line:
                try:
                    skipped_part = line.split('skipped=')[1].split(',')[0].split(')')[0]
                    tests_skipped = int(skipped_part)
                except (ValueError, IndexError):
                    pass
        
        tests_passed = tests_run - tests_failed - tests_skipped
        return tests_run, tests_passed, tests_failed, tests_skipped
    
    def _parse_pytest_output(self, output: str) -> Tuple[int, int, int, int]:
        """Parse pytest output to extract test counts."""
        tests_run = tests_passed = tests_failed = tests_skipped = 0
        
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line or 'failed' in line or 'skipped' in line:
                # Example: "5 passed, 2 failed, 1 skipped in 0.12s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        try:
                            tests_passed = int(parts[i-1])
                        except ValueError:
                            pass
                    elif part == 'failed' and i > 0:
                        try:
                            tests_failed = int(parts[i-1])
                        except ValueError:
                            pass
                    elif part == 'skipped' and i > 0:
                        try:
                            tests_skipped = int(parts[i-1])
                        except ValueError:
                            pass
        
        tests_run = tests_passed + tests_failed + tests_skipped
        return tests_run, tests_passed, tests_failed, tests_skipped
    
    def _parse_doctest_output(self, output: str) -> Tuple[int, int, int]:
        """Parse doctest output to extract test counts."""
        tests_run = tests_passed = tests_failed = 0
        
        lines = output.split('\n')
        for line in lines:
            if 'items had no tests' in line:
                continue
            elif 'items passed all tests' in line:
                # Example: "1 items passed all tests:"
                parts = line.split()
                if len(parts) >= 1:
                    try:
                        tests_passed = int(parts[0])
                    except ValueError:
                        pass
            elif 'Test passed' in line or 'tests passed' in line:
                tests_passed += 1
            elif 'FAIL' in line or 'Failed' in line:
                tests_failed += 1
        
        tests_run = tests_passed + tests_failed
        return tests_run, tests_passed, tests_failed
    
    def _get_coverage_percentage(self, temp_dir: str) -> Optional[float]:
        """Get coverage percentage from coverage report."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "coverage", "report", "--show-missing"],
                capture_output=True,
                text=True,
                cwd=temp_dir
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'TOTAL' in line:
                        parts = line.split()
                        for part in parts:
                            if part.endswith('%'):
                                try:
                                    return float(part[:-1])
                                except ValueError:
                                    pass
        except Exception as e:
            logger.debug(f"Error getting coverage: {e}")
        
        return None
    
    def _extract_pytest_coverage(self, output: str) -> Optional[float]:
        """Extract coverage percentage from pytest output."""
        lines = output.split('\n')
        for line in lines:
            if 'TOTAL' in line and '%' in line:
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            return float(part[:-1])
                        except ValueError:
                            pass
        return None
    
    def _estimate_complexity(self, code: str) -> int:
        """Estimate code complexity based on AST analysis."""
        try:
            tree = ast.parse(code)
            complexity = 0
            
            for node in ast.walk(tree):
                # Count decision points
                if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                    complexity += 1
                elif isinstance(node, ast.FunctionDef):
                    complexity += 1
                elif isinstance(node, ast.ClassDef):
                    complexity += 1
            
            return complexity
        except Exception:
            return 0
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
        self.temp_dirs.clear()
    
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup()


# Convenience functions for common verification scenarios

def verify_function_implementation(code: str, function_name: str, 
                                 test_cases: List[Tuple[Any, Any]]) -> CodeVerificationResult:
    """
    Verify a function implementation with test cases.
    
    Args:
        code: The code containing the function.
        function_name: Name of the function to test.
        test_cases: List of (input, expected_output) tuples.
        
    Returns:
        CodeVerificationResult with verification results.
    """
    # Generate test code
    test_code = f"""
import unittest
from main import {function_name}

class Test{function_name.title()}(unittest.TestCase):
"""
    
    for i, (input_val, expected) in enumerate(test_cases):
        test_code += f"""
    def test_case_{i+1}(self):
        result = {function_name}({repr(input_val)})
        self.assertEqual(result, {repr(expected)})
"""
    
    test_code += """
if __name__ == '__main__':
    unittest.main()
"""
    
    verifier = CodeTestVerifier()
    try:
        return verifier.verify_code(
            code=code,
            test_code=test_code,
            expected_functions=[function_name],
            test_framework=TestFramework.UNITTEST
        )
    finally:
        verifier.cleanup()


def verify_class_implementation(code: str, class_name: str, 
                               required_methods: List[str]) -> CodeVerificationResult:
    """
    Verify a class implementation has required methods.
    
    Args:
        code: The code containing the class.
        class_name: Name of the class to verify.
        required_methods: List of method names that should be present.
        
    Returns:
        CodeVerificationResult with verification results.
    """
    # Generate test code to check class structure
    test_code = f"""
import unittest
from main import {class_name}

class Test{class_name}(unittest.TestCase):
    def setUp(self):
        self.instance = {class_name}()
    
    def test_class_exists(self):
        self.assertTrue(hasattr(self.instance, '__class__'))
        self.assertEqual(self.instance.__class__.__name__, '{class_name}')
"""
    
    for method in required_methods:
        test_code += f"""
    def test_{method}_exists(self):
        self.assertTrue(hasattr(self.instance, '{method}'))
        self.assertTrue(callable(getattr(self.instance, '{method}')))
"""
    
    test_code += """
if __name__ == '__main__':
    unittest.main()
"""
    
    verifier = CodeTestVerifier()
    try:
        return verifier.verify_code(
            code=code,
            test_code=test_code,
            test_framework=TestFramework.UNITTEST
        )
    finally:
        verifier.cleanup()


if __name__ == "__main__":
    # Example usage
    sample_code = '''
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
    
    result = verify_function_implementation(sample_code, "factorial", test_cases)
    
    print(f"Verification Result: {result.overall_result.value}")
    print(f"Syntax Valid: {result.syntax_valid}")
    print(f"Imports Valid: {result.imports_valid}")
    
    for execution in result.test_executions:
        print(f"\nTest Framework: {execution.framework.value}")
        print(f"Result: {execution.result.value}")
        print(f"Tests Run: {execution.tests_run}")
        print(f"Tests Passed: {execution.tests_passed}")
        print(f"Duration: {execution.duration:.3f}s")
        if execution.coverage_percentage:
            print(f"Coverage: {execution.coverage_percentage:.1f}%")