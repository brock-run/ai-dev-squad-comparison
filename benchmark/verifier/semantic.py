#!/usr/bin/env python3
"""
Semantic Verification System

This module provides semantic correctness checking for benchmark tasks,
including logical consistency, algorithmic correctness, and behavioral verification.
"""

import ast
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import inspect
import importlib.util
import tempfile
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class SemanticIssueType(Enum):
    """Types of semantic issues that can be detected."""
    LOGIC_ERROR = "logic_error"
    ALGORITHM_ERROR = "algorithm_error"
    EDGE_CASE_MISSING = "edge_case_missing"
    INFINITE_LOOP = "infinite_loop"
    UNREACHABLE_CODE = "unreachable_code"
    INCORRECT_BEHAVIOR = "incorrect_behavior"
    MISSING_VALIDATION = "missing_validation"
    PERFORMANCE_ISSUE = "performance_issue"
    RESOURCE_LEAK = "resource_leak"
    SECURITY_ISSUE = "security_issue"


class SemanticSeverity(Enum):
    """Severity levels for semantic issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SemanticIssue:
    """Represents a semantic issue in the code."""
    issue_type: SemanticIssueType
    severity: SemanticSeverity
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    function_name: Optional[str] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class BehaviorTest:
    """Represents a behavioral test case."""
    name: str
    input_data: Any
    expected_output: Any
    description: str
    test_function: Optional[Callable] = None


@dataclass
class SemanticVerificationResult:
    """Results from semantic verification."""
    overall_correctness: float  # 0.0 to 1.0
    issues: List[SemanticIssue]
    behavior_tests_passed: int
    behavior_tests_failed: int
    algorithm_complexity: Optional[str] = None
    detected_patterns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticVerifier:
    """Performs semantic analysis and correctness checking."""
    
    def __init__(self):
        """Initialize semantic verifier."""
        self.temp_dirs = []
        
        # Pattern matchers for common issues
        self.pattern_matchers = {
            'infinite_loop': self._detect_infinite_loops,
            'unreachable_code': self._detect_unreachable_code,
            'missing_validation': self._detect_missing_validation,
            'performance_issues': self._detect_performance_issues,
            'security_issues': self._detect_security_issues
        }
    
    def verify_semantic_correctness(self, code: str, 
                                  behavior_tests: Optional[List[BehaviorTest]] = None,
                                  expected_algorithm: Optional[str] = None,
                                  context: Optional[Dict[str, Any]] = None) -> SemanticVerificationResult:
        """
        Perform comprehensive semantic verification of code.
        
        Args:
            code: The code to verify.
            behavior_tests: Optional behavioral test cases.
            expected_algorithm: Expected algorithm type (e.g., "sorting", "search").
            context: Additional context about the expected behavior.
            
        Returns:
            SemanticVerificationResult with detailed analysis.
        """
        issues = []
        behavior_tests_passed = 0
        behavior_tests_failed = 0
        detected_patterns = []
        suggestions = []
        
        try:
            # Parse the code into AST
            tree = ast.parse(code)
            
            # 1. Static semantic analysis
            static_issues = self._perform_static_analysis(tree, code)
            issues.extend(static_issues)
            
            # 2. Pattern-based analysis
            for pattern_name, matcher in self.pattern_matchers.items():
                pattern_issues = matcher(tree, code)
                issues.extend(pattern_issues)
                if pattern_issues:
                    detected_patterns.append(pattern_name)
            
            # 3. Algorithm-specific analysis
            if expected_algorithm:
                algo_issues = self._analyze_algorithm_correctness(tree, code, expected_algorithm)
                issues.extend(algo_issues)
            
            # 4. Behavioral testing
            if behavior_tests:
                behavior_results = self._run_behavior_tests(code, behavior_tests)
                behavior_tests_passed = behavior_results['passed']
                behavior_tests_failed = behavior_results['failed']
                issues.extend(behavior_results['issues'])
            
            # 5. Complexity analysis
            complexity = self._analyze_complexity(tree)
            
            # 6. Generate suggestions
            suggestions = self._generate_suggestions(issues, detected_patterns, complexity)
            
            # Calculate overall correctness score
            correctness = self._calculate_correctness_score(
                issues, behavior_tests_passed, behavior_tests_failed
            )
            
            return SemanticVerificationResult(
                overall_correctness=correctness,
                issues=issues,
                behavior_tests_passed=behavior_tests_passed,
                behavior_tests_failed=behavior_tests_failed,
                algorithm_complexity=complexity,
                detected_patterns=detected_patterns,
                suggestions=suggestions,
                metadata={
                    'total_functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                    'total_classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                    'lines_of_code': len(code.split('\n')),
                    'cyclomatic_complexity': self._calculate_cyclomatic_complexity(tree)
                }
            )
        
        except SyntaxError as e:
            return SemanticVerificationResult(
                overall_correctness=0.0,
                issues=[SemanticIssue(
                    issue_type=SemanticIssueType.LOGIC_ERROR,
                    severity=SemanticSeverity.CRITICAL,
                    message=f"Syntax error prevents semantic analysis: {e}",
                    line=getattr(e, 'lineno', None)
                )],
                behavior_tests_passed=0,
                behavior_tests_failed=len(behavior_tests) if behavior_tests else 0
            )
        except Exception as e:
            logger.error(f"Error during semantic verification: {e}")
            return SemanticVerificationResult(
                overall_correctness=0.0,
                issues=[SemanticIssue(
                    issue_type=SemanticIssueType.LOGIC_ERROR,
                    severity=SemanticSeverity.HIGH,
                    message=f"Verification error: {str(e)}"
                )],
                behavior_tests_passed=0,
                behavior_tests_failed=len(behavior_tests) if behavior_tests else 0
            )
    
    def _perform_static_analysis(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Perform static semantic analysis on the AST."""
        issues = []
        
        # Check for common logical issues
        issues.extend(self._check_variable_usage(tree))
        issues.extend(self._check_function_returns(tree))
        issues.extend(self._check_exception_handling(tree))
        issues.extend(self._check_resource_management(tree))
        
        return issues
    
    def _check_variable_usage(self, tree: ast.AST) -> List[SemanticIssue]:
        """Check for variable usage issues."""
        issues = []
        
        class VariableAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.defined_vars = set()
                self.used_vars = set()
                self.unused_vars = set()
                self.undefined_usage = []
            
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    self.defined_vars.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    self.used_vars.add(node.id)
                    if node.id not in self.defined_vars and node.id not in dir(__builtins__):
                        self.undefined_usage.append((node.id, node.lineno))
                self.generic_visit(node)
        
        analyzer = VariableAnalyzer()
        analyzer.visit(tree)
        
        # Check for undefined variables
        for var_name, line_no in analyzer.undefined_usage:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.LOGIC_ERROR,
                severity=SemanticSeverity.HIGH,
                message=f"Variable '{var_name}' used before definition",
                line=line_no,
                suggestion=f"Define '{var_name}' before using it"
            ))
        
        # Check for unused variables
        unused = analyzer.defined_vars - analyzer.used_vars
        for var_name in unused:
            if not var_name.startswith('_'):  # Ignore private variables
                issues.append(SemanticIssue(
                    issue_type=SemanticIssueType.LOGIC_ERROR,
                    severity=SemanticSeverity.LOW,
                    message=f"Variable '{var_name}' defined but never used",
                    suggestion=f"Remove unused variable '{var_name}' or use it"
                ))
        
        return issues
    
    def _check_function_returns(self, tree: ast.AST) -> List[SemanticIssue]:
        """Check for function return issues."""
        issues = []
        
        class ReturnAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.current_function = None
                self.return_issues = []
            
            def visit_FunctionDef(self, node):
                old_function = self.current_function
                self.current_function = node.name
                
                # Check if function has return statements
                has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
                has_explicit_return = any(
                    isinstance(n, ast.Return) and n.value is not None 
                    for n in ast.walk(node)
                )
                
                # Check for missing return statements
                if not has_return and not node.name.startswith('_'):
                    # Check if function seems to compute something
                    has_computation = any(
                        isinstance(n, (ast.BinOp, ast.Call, ast.Compare))
                        for n in ast.walk(node)
                    )
                    if has_computation:
                        self.return_issues.append((
                            node.name, node.lineno,
                            "Function appears to compute a value but has no return statement"
                        ))
                
                # Check for inconsistent returns
                returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                if len(returns) > 1:
                    explicit_returns = [r for r in returns if r.value is not None]
                    implicit_returns = [r for r in returns if r.value is None]
                    
                    if explicit_returns and implicit_returns:
                        self.return_issues.append((
                            node.name, node.lineno,
                            "Function has inconsistent return statements (some with values, some without)"
                        ))
                
                self.generic_visit(node)
                self.current_function = old_function
        
        analyzer = ReturnAnalyzer()
        analyzer.visit(tree)
        
        for func_name, line_no, message in analyzer.return_issues:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.LOGIC_ERROR,
                severity=SemanticSeverity.MEDIUM,
                message=message,
                line=line_no,
                function_name=func_name,
                suggestion="Add appropriate return statements"
            ))
        
        return issues
    
    def _check_exception_handling(self, tree: ast.AST) -> List[SemanticIssue]:
        """Check for exception handling issues."""
        issues = []
        
        class ExceptionAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.exception_issues = []
            
            def visit_Try(self, node):
                # Check for bare except clauses
                for handler in node.handlers:
                    if handler.type is None:
                        self.exception_issues.append((
                            handler.lineno,
                            "Bare except clause catches all exceptions, including system exits"
                        ))
                
                # Check for empty except blocks
                for handler in node.handlers:
                    if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                        self.exception_issues.append((
                            handler.lineno,
                            "Empty except block silently ignores exceptions"
                        ))
                
                self.generic_visit(node)
            
            def visit_Raise(self, node):
                # Check for re-raising without context
                if node.exc is None and node.cause is None:
                    # This is actually good practice, but check context
                    pass
                self.generic_visit(node)
        
        analyzer = ExceptionAnalyzer()
        analyzer.visit(tree)
        
        for line_no, message in analyzer.exception_issues:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.LOGIC_ERROR,
                severity=SemanticSeverity.MEDIUM,
                message=message,
                line=line_no,
                suggestion="Use specific exception types and handle appropriately"
            ))
        
        return issues
    
    def _check_resource_management(self, tree: ast.AST) -> List[SemanticIssue]:
        """Check for resource management issues."""
        issues = []
        
        class ResourceAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.resource_issues = []
                self.open_calls = []
            
            def visit_Call(self, node):
                # Check for file operations without context managers
                if (isinstance(node.func, ast.Name) and node.func.id == 'open'):
                    self.open_calls.append(node.lineno)
                
                self.generic_visit(node)
            
            def visit_With(self, node):
                # Remove open calls that are properly managed
                for item in node.items:
                    if (isinstance(item.context_expr, ast.Call) and
                        isinstance(item.context_expr.func, ast.Name) and
                        item.context_expr.func.id == 'open'):
                        if item.context_expr.lineno in self.open_calls:
                            self.open_calls.remove(item.context_expr.lineno)
                
                self.generic_visit(node)
        
        analyzer = ResourceAnalyzer()
        analyzer.visit(tree)
        
        for line_no in analyzer.open_calls:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.RESOURCE_LEAK,
                severity=SemanticSeverity.MEDIUM,
                message="File opened without proper resource management",
                line=line_no,
                suggestion="Use 'with open(...)' context manager for file operations"
            ))
        
        return issues
    
    def _detect_infinite_loops(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Detect potential infinite loops."""
        issues = []
        
        class LoopAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.loop_issues = []
            
            def visit_While(self, node):
                # Check for while True without break
                if (isinstance(node.test, ast.Constant) and node.test.value is True):
                    has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                    has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
                    
                    if not has_break and not has_return:
                        self.loop_issues.append((
                            node.lineno,
                            "Potential infinite loop: 'while True' without break or return"
                        ))
                
                self.generic_visit(node)
            
            def visit_For(self, node):
                # Check for nested loops that might be inefficient
                nested_loops = [n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While))]
                if len(nested_loops) > 3:  # Including the current loop
                    self.loop_issues.append((
                        node.lineno,
                        f"Deeply nested loops ({len(nested_loops)} levels) may cause performance issues"
                    ))
                
                self.generic_visit(node)
        
        analyzer = LoopAnalyzer()
        analyzer.visit(tree)
        
        for line_no, message in analyzer.loop_issues:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.INFINITE_LOOP,
                severity=SemanticSeverity.HIGH,
                message=message,
                line=line_no,
                suggestion="Add appropriate loop termination conditions"
            ))
        
        return issues
    
    def _detect_unreachable_code(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Detect unreachable code."""
        issues = []
        
        class UnreachableAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.unreachable_issues = []
            
            def visit_FunctionDef(self, node):
                # Check for code after return statements
                for i, stmt in enumerate(node.body):
                    if isinstance(stmt, ast.Return):
                        if i < len(node.body) - 1:
                            next_stmt = node.body[i + 1]
                            self.unreachable_issues.append((
                                next_stmt.lineno,
                                "Code after return statement is unreachable"
                            ))
                
                self.generic_visit(node)
        
        analyzer = UnreachableAnalyzer()
        analyzer.visit(tree)
        
        for line_no, message in analyzer.unreachable_issues:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.UNREACHABLE_CODE,
                severity=SemanticSeverity.MEDIUM,
                message=message,
                line=line_no,
                suggestion="Remove unreachable code or restructure logic"
            ))
        
        return issues
    
    def _detect_missing_validation(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Detect missing input validation."""
        issues = []
        
        class ValidationAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.validation_issues = []
                self.current_function = None
            
            def visit_FunctionDef(self, node):
                old_function = self.current_function
                self.current_function = node.name
                
                # Check if function has parameters but no validation
                if node.args.args:
                    has_validation = any(
                        isinstance(n, (ast.If, ast.Try, ast.Assert))
                        for n in ast.walk(node)
                    )
                    
                    # Look for operations that might need validation
                    risky_operations = []
                    for n in ast.walk(node):
                        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
                            risky_operations.append("division")
                        elif isinstance(n, ast.Subscript):
                            risky_operations.append("indexing")
                        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                            if n.func.attr in ['index', 'remove']:
                                risky_operations.append("list operations")
                    
                    if risky_operations and not has_validation:
                        self.validation_issues.append((
                            node.lineno,
                            f"Function performs {', '.join(set(risky_operations))} without input validation"
                        ))
                
                self.generic_visit(node)
                self.current_function = old_function
        
        analyzer = ValidationAnalyzer()
        analyzer.visit(tree)
        
        for line_no, message in analyzer.validation_issues:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.MISSING_VALIDATION,
                severity=SemanticSeverity.MEDIUM,
                message=message,
                line=line_no,
                suggestion="Add input validation and error handling"
            ))
        
        return issues
    
    def _detect_performance_issues(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Detect potential performance issues."""
        issues = []
        
        class PerformanceAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.performance_issues = []
            
            def visit_ListComp(self, node):
                # Check for nested list comprehensions
                nested_comps = [n for n in ast.walk(node) if isinstance(n, ast.ListComp)]
                if len(nested_comps) > 1:
                    self.performance_issues.append((
                        node.lineno,
                        "Nested list comprehensions can be inefficient for large datasets"
                    ))
                
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # Check for inefficient string operations
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr == 'join' and
                    isinstance(node.func.value, ast.Str)):
                    # This is actually good, but check the argument
                    pass
                
                # Check for repeated expensive operations in loops
                parent = getattr(node, 'parent', None)
                if isinstance(parent, (ast.For, ast.While)):
                    if (isinstance(node.func, ast.Name) and 
                        node.func.id in ['sorted', 'max', 'min', 'sum']):
                        self.performance_issues.append((
                            node.lineno,
                            f"Expensive operation '{node.func.id}' inside loop"
                        ))
                
                self.generic_visit(node)
        
        # Add parent references
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        
        analyzer = PerformanceAnalyzer()
        analyzer.visit(tree)
        
        for line_no, message in analyzer.performance_issues:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.PERFORMANCE_ISSUE,
                severity=SemanticSeverity.LOW,
                message=message,
                line=line_no,
                suggestion="Consider optimizing for better performance"
            ))
        
        return issues
    
    def _detect_security_issues(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Detect potential security issues."""
        issues = []
        
        class SecurityAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.security_issues = []
            
            def visit_Call(self, node):
                # Check for dangerous function calls
                dangerous_functions = ['eval', 'exec', 'compile']
                
                if isinstance(node.func, ast.Name) and node.func.id in dangerous_functions:
                    self.security_issues.append((
                        node.lineno,
                        f"Use of '{node.func.id}' can be dangerous with untrusted input"
                    ))
                
                # Check for subprocess without shell=False
                if (isinstance(node.func, ast.Attribute) and
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'subprocess'):
                    
                    # Look for shell=True in arguments
                    for keyword in node.keywords:
                        if (keyword.arg == 'shell' and
                            isinstance(keyword.value, ast.Constant) and
                            keyword.value.value is True):
                            self.security_issues.append((
                                node.lineno,
                                "subprocess with shell=True can be vulnerable to injection"
                            ))
                
                self.generic_visit(node)
        
        analyzer = SecurityAnalyzer()
        analyzer.visit(tree)
        
        for line_no, message in analyzer.security_issues:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.SECURITY_ISSUE,
                severity=SemanticSeverity.HIGH,
                message=message,
                line=line_no,
                suggestion="Use safer alternatives or validate input carefully"
            ))
        
        return issues
    
    def _analyze_algorithm_correctness(self, tree: ast.AST, code: str, 
                                     expected_algorithm: str) -> List[SemanticIssue]:
        """Analyze algorithm-specific correctness."""
        issues = []
        
        if expected_algorithm.lower() == "sorting":
            issues.extend(self._check_sorting_algorithm(tree, code))
        elif expected_algorithm.lower() == "search":
            issues.extend(self._check_search_algorithm(tree, code))
        elif expected_algorithm.lower() == "recursion":
            issues.extend(self._check_recursive_algorithm(tree, code))
        
        return issues
    
    def _check_sorting_algorithm(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Check sorting algorithm correctness."""
        issues = []
        
        # Check for comparison operations
        has_comparisons = any(isinstance(n, ast.Compare) for n in ast.walk(tree))
        if not has_comparisons:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.ALGORITHM_ERROR,
                severity=SemanticSeverity.HIGH,
                message="Sorting algorithm should include comparison operations",
                suggestion="Add comparison logic to sort elements"
            ))
        
        # Check for element swapping or rearrangement
        has_assignment = any(isinstance(n, ast.Assign) for n in ast.walk(tree))
        if not has_assignment:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.ALGORITHM_ERROR,
                severity=SemanticSeverity.HIGH,
                message="Sorting algorithm should rearrange elements",
                suggestion="Add logic to swap or rearrange elements"
            ))
        
        return issues
    
    def _check_search_algorithm(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Check search algorithm correctness."""
        issues = []
        
        # Check for comparison with target
        has_comparisons = any(isinstance(n, ast.Compare) for n in ast.walk(tree))
        if not has_comparisons:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.ALGORITHM_ERROR,
                severity=SemanticSeverity.HIGH,
                message="Search algorithm should compare elements with target",
                suggestion="Add comparison logic to find target element"
            ))
        
        return issues
    
    def _check_recursive_algorithm(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Check recursive algorithm correctness."""
        issues = []
        
        class RecursionAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.functions = {}
                self.recursive_calls = {}
            
            def visit_FunctionDef(self, node):
                self.functions[node.name] = node
                self.recursive_calls[node.name] = []
                
                # Look for recursive calls
                for n in ast.walk(node):
                    if (isinstance(n, ast.Call) and
                        isinstance(n.func, ast.Name) and
                        n.func.id == node.name):
                        self.recursive_calls[node.name].append(n.lineno)
                
                self.generic_visit(node)
        
        analyzer = RecursionAnalyzer()
        analyzer.visit(tree)
        
        for func_name, calls in analyzer.recursive_calls.items():
            if calls:
                # Check for base case
                func_node = analyzer.functions[func_name]
                has_base_case = any(
                    isinstance(n, ast.Return) and n.value is not None
                    for n in ast.walk(func_node)
                    if not any(isinstance(parent, ast.Call) for parent in ast.walk(func_node))
                )
                
                if not has_base_case:
                    issues.append(SemanticIssue(
                        issue_type=SemanticIssueType.ALGORITHM_ERROR,
                        severity=SemanticSeverity.CRITICAL,
                        message=f"Recursive function '{func_name}' may lack proper base case",
                        function_name=func_name,
                        suggestion="Add base case to prevent infinite recursion"
                    ))
        
        return issues
    
    def _run_behavior_tests(self, code: str, behavior_tests: List[BehaviorTest]) -> Dict[str, Any]:
        """Run behavioral tests against the code."""
        passed = 0
        failed = 0
        issues = []
        
        # Create temporary module
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        try:
            module_file = Path(temp_dir) / "test_module.py"
            with open(module_file, 'w') as f:
                f.write(code)
            
            # Import the module
            spec = importlib.util.spec_from_file_location("test_module", module_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules["test_module"] = module
            spec.loader.exec_module(module)
            
            # Run each behavior test
            for test in behavior_tests:
                try:
                    if test.test_function:
                        # Custom test function
                        result = test.test_function(module, test.input_data)
                        if result == test.expected_output:
                            passed += 1
                        else:
                            failed += 1
                            issues.append(SemanticIssue(
                                issue_type=SemanticIssueType.INCORRECT_BEHAVIOR,
                                severity=SemanticSeverity.HIGH,
                                message=f"Behavior test '{test.name}' failed: expected {test.expected_output}, got {result}",
                                suggestion=f"Fix logic to handle case: {test.description}"
                            ))
                    else:
                        # Try to find and call a function with the input
                        functions = [getattr(module, name) for name in dir(module) 
                                   if callable(getattr(module, name)) and not name.startswith('_')]
                        
                        if functions:
                            func = functions[0]  # Use first function found
                            result = func(test.input_data)
                            if result == test.expected_output:
                                passed += 1
                            else:
                                failed += 1
                                issues.append(SemanticIssue(
                                    issue_type=SemanticIssueType.INCORRECT_BEHAVIOR,
                                    severity=SemanticSeverity.HIGH,
                                    message=f"Behavior test '{test.name}' failed: expected {test.expected_output}, got {result}",
                                    suggestion=f"Fix logic to handle case: {test.description}"
                                ))
                        else:
                            failed += 1
                            issues.append(SemanticIssue(
                                issue_type=SemanticIssueType.ALGORITHM_ERROR,
                                severity=SemanticSeverity.CRITICAL,
                                message=f"No callable functions found for behavior test '{test.name}'",
                                suggestion="Ensure code defines callable functions"
                            ))
                
                except Exception as e:
                    failed += 1
                    issues.append(SemanticIssue(
                        issue_type=SemanticIssueType.LOGIC_ERROR,
                        severity=SemanticSeverity.HIGH,
                        message=f"Behavior test '{test.name}' raised exception: {str(e)}",
                        suggestion="Fix runtime errors in the code"
                    ))
        
        except Exception as e:
            # Failed to import/execute code
            failed = len(behavior_tests)
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.LOGIC_ERROR,
                severity=SemanticSeverity.CRITICAL,
                message=f"Failed to execute code for behavior testing: {str(e)}",
                suggestion="Fix syntax and runtime errors"
            ))
        
        finally:
            # Cleanup
            if "test_module" in sys.modules:
                del sys.modules["test_module"]
        
        return {
            'passed': passed,
            'failed': failed,
            'issues': issues
        }
    
    def _analyze_complexity(self, tree: ast.AST) -> str:
        """Analyze algorithmic complexity."""
        # Simple heuristic-based complexity analysis
        loop_depth = 0
        max_loop_depth = 0
        
        class ComplexityAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
                self.max_depth = 0
            
            def visit_For(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
            
            def visit_While(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
        
        analyzer = ComplexityAnalyzer()
        analyzer.visit(tree)
        
        if analyzer.max_depth == 0:
            return "O(1) - Constant"
        elif analyzer.max_depth == 1:
            return "O(n) - Linear"
        elif analyzer.max_depth == 2:
            return "O(n²) - Quadratic"
        elif analyzer.max_depth == 3:
            return "O(n³) - Cubic"
        else:
            return f"O(n^{analyzer.max_depth}) - Polynomial"
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_correctness_score(self, issues: List[SemanticIssue], 
                                   tests_passed: int, tests_failed: int) -> float:
        """Calculate overall correctness score."""
        # Start with perfect score
        score = 1.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == SemanticSeverity.CRITICAL:
                score -= 0.3
            elif issue.severity == SemanticSeverity.HIGH:
                score -= 0.2
            elif issue.severity == SemanticSeverity.MEDIUM:
                score -= 0.1
            elif issue.severity == SemanticSeverity.LOW:
                score -= 0.05
        
        # Factor in behavior test results
        total_tests = tests_passed + tests_failed
        if total_tests > 0:
            test_score = tests_passed / total_tests
            score = (score + test_score) / 2  # Average with test results
        
        return max(0.0, min(1.0, score))
    
    def _generate_suggestions(self, issues: List[SemanticIssue], 
                            patterns: List[str], complexity: str) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        # Issue-based suggestions
        critical_issues = [i for i in issues if i.severity == SemanticSeverity.CRITICAL]
        if critical_issues:
            suggestions.append("Address critical issues first to ensure code functionality")
        
        high_issues = [i for i in issues if i.severity == SemanticSeverity.HIGH]
        if len(high_issues) > 3:
            suggestions.append("Multiple high-severity issues detected - consider code review")
        
        # Pattern-based suggestions
        if 'infinite_loop' in patterns:
            suggestions.append("Review loop termination conditions carefully")
        
        if 'performance_issues' in patterns:
            suggestions.append("Consider optimizing for better performance")
        
        if 'security_issues' in patterns:
            suggestions.append("Review code for security vulnerabilities")
        
        # Complexity-based suggestions
        if "Cubic" in complexity or "Polynomial" in complexity:
            suggestions.append("Consider optimizing algorithm complexity for better scalability")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
        self.temp_dirs.clear()
    
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup()


# Convenience functions

def verify_algorithm_correctness(code: str, algorithm_type: str, 
                               test_cases: List[Tuple[Any, Any]]) -> SemanticVerificationResult:
    """
    Verify algorithm correctness with test cases.
    
    Args:
        code: The algorithm code to verify.
        algorithm_type: Type of algorithm (e.g., "sorting", "search").
        test_cases: List of (input, expected_output) tuples.
        
    Returns:
        SemanticVerificationResult with verification results.
    """
    behavior_tests = [
        BehaviorTest(
            name=f"test_case_{i+1}",
            input_data=input_val,
            expected_output=expected,
            description=f"Test case {i+1}: input={input_val}, expected={expected}"
        )
        for i, (input_val, expected) in enumerate(test_cases)
    ]
    
    verifier = SemanticVerifier()
    try:
        return verifier.verify_semantic_correctness(
            code=code,
            behavior_tests=behavior_tests,
            expected_algorithm=algorithm_type
        )
    finally:
        verifier.cleanup()


if __name__ == "__main__":
    # Example usage
    sample_code = '''
def factorial(n):
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

def buggy_sort(arr):
    # This has issues - no actual sorting logic
    for i in range(len(arr)):
        pass
    return arr
'''
    
    test_cases = [
        (0, 1),
        (1, 1),
        (5, 120)
    ]
    
    result = verify_algorithm_correctness(sample_code, "recursion", test_cases)
    
    print(f"Overall Correctness: {result.overall_correctness:.2f}")
    print(f"Behavior Tests: {result.behavior_tests_passed} passed, {result.behavior_tests_failed} failed")
    print(f"Algorithm Complexity: {result.algorithm_complexity}")
    
    print(f"\nIssues Found ({len(result.issues)}):")
    for issue in result.issues:
        print(f"  {issue.severity.value.upper()}: {issue.message}")
        if issue.suggestion:
            print(f"    Suggestion: {issue.suggestion}")
    
    if result.suggestions:
        print(f"\nRecommendations:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")