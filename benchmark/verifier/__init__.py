#!/usr/bin/env python3
"""
Integrated Verification System

This module provides a unified interface for all verification capabilities
including code testing, static analysis, and semantic verification.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .code_tests import CodeTestVerifier, CodeVerificationResult, TestFramework
from .lint_type import LintTypeVerifier, StaticAnalysisResult
from .semantic import SemanticVerifier, SemanticVerificationResult, BehaviorTest

logger = logging.getLogger(__name__)


class VerificationLevel(Enum):
    """Levels of verification thoroughness."""
    BASIC = "basic"          # Syntax and basic tests only
    STANDARD = "standard"    # Includes linting and type checking
    COMPREHENSIVE = "comprehensive"  # Full semantic analysis
    STRICT = "strict"        # All checks with strict rules


@dataclass
class IntegratedVerificationResult:
    """Complete verification results from all systems."""
    overall_score: float  # 0.0 to 1.0
    verification_level: VerificationLevel
    
    # Individual results
    code_verification: Optional[CodeVerificationResult] = None
    static_analysis: Optional[StaticAnalysisResult] = None
    semantic_verification: Optional[SemanticVerificationResult] = None
    
    # Aggregated metrics
    total_issues: int = 0
    critical_issues: int = 0
    test_success_rate: float = 0.0
    
    # Summary and recommendations
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntegratedVerifier:
    """Unified verification system combining all verification capabilities."""
    
    def __init__(self, timeout_seconds: int = 60):
        """
        Initialize integrated verifier.
        
        Args:
            timeout_seconds: Maximum time for verification operations.
        """
        self.timeout_seconds = timeout_seconds
        self.code_verifier = CodeTestVerifier(timeout_seconds=timeout_seconds)
        self.lint_verifier = LintTypeVerifier(timeout_seconds=timeout_seconds)
        self.semantic_verifier = SemanticVerifier()
    
    def verify_code_comprehensive(self, 
                                code: str,
                                test_code: Optional[str] = None,
                                expected_functions: Optional[List[str]] = None,
                                behavior_tests: Optional[List[BehaviorTest]] = None,
                                expected_algorithm: Optional[str] = None,
                                verification_level: VerificationLevel = VerificationLevel.STANDARD,
                                context: Optional[Dict[str, Any]] = None) -> IntegratedVerificationResult:
        """
        Perform comprehensive code verification using all available systems.
        
        Args:
            code: The code to verify.
            test_code: Optional test code for functional verification.
            expected_functions: List of function names that should be present.
            behavior_tests: Behavioral test cases for semantic verification.
            expected_algorithm: Expected algorithm type for semantic analysis.
            verification_level: Level of verification thoroughness.
            context: Additional context for verification.
            
        Returns:
            IntegratedVerificationResult with comprehensive analysis.
        """
        logger.info(f"Starting {verification_level.value} verification")
        
        code_verification = None
        static_analysis = None
        semantic_verification = None
        
        try:
            # 1. Code Testing (always performed)
            if test_code or expected_functions:
                logger.debug("Running code verification tests")
                code_verification = self.code_verifier.verify_code(
                    code=code,
                    test_code=test_code,
                    expected_functions=expected_functions,
                    test_framework=TestFramework.UNITTEST
                )
            
            # 2. Static Analysis (standard level and above)
            if verification_level in [VerificationLevel.STANDARD, 
                                    VerificationLevel.COMPREHENSIVE, 
                                    VerificationLevel.STRICT]:
                logger.debug("Running static analysis")
                static_analysis = self.lint_verifier.verify_code(
                    code=code,
                    enable_type_checking=True,
                    strict_mode=(verification_level == VerificationLevel.STRICT)
                )
            
            # 3. Semantic Analysis (comprehensive level and above)
            if verification_level in [VerificationLevel.COMPREHENSIVE, 
                                    VerificationLevel.STRICT]:
                logger.debug("Running semantic verification")
                semantic_verification = self.semantic_verifier.verify_semantic_correctness(
                    code=code,
                    behavior_tests=behavior_tests,
                    expected_algorithm=expected_algorithm,
                    context=context
                )
            
            # 4. Aggregate results
            result = self._aggregate_results(
                code_verification=code_verification,
                static_analysis=static_analysis,
                semantic_verification=semantic_verification,
                verification_level=verification_level
            )
            
            logger.info(f"Verification completed with overall score: {result.overall_score:.2f}")
            return result
        
        except Exception as e:
            logger.error(f"Error during integrated verification: {e}")
            return IntegratedVerificationResult(
                overall_score=0.0,
                verification_level=verification_level,
                summary=f"Verification failed: {str(e)}",
                recommendations=["Fix critical errors preventing verification"]
            )
    
    def _aggregate_results(self, 
                          code_verification: Optional[CodeVerificationResult],
                          static_analysis: Optional[StaticAnalysisResult],
                          semantic_verification: Optional[SemanticVerificationResult],
                          verification_level: VerificationLevel) -> IntegratedVerificationResult:
        """Aggregate results from all verification systems."""
        
        # Calculate overall score
        scores = []
        weights = []
        
        # Code verification score
        if code_verification:
            if code_verification.overall_result.value == "pass":
                code_score = 1.0
            elif code_verification.overall_result.value == "fail":
                code_score = 0.3
            else:  # error, timeout
                code_score = 0.0
            
            scores.append(code_score)
            weights.append(0.4)  # 40% weight for functional correctness
        
        # Static analysis score
        if static_analysis:
            static_score = static_analysis.overall_score / 10.0  # Convert to 0-1 scale
            scores.append(static_score)
            weights.append(0.3)  # 30% weight for code quality
        
        # Semantic verification score
        if semantic_verification:
            semantic_score = semantic_verification.overall_correctness
            scores.append(semantic_score)
            weights.append(0.3)  # 30% weight for semantic correctness
        
        # Calculate weighted average
        if scores and weights:
            overall_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            overall_score = 0.0
        
        # Count issues
        total_issues = 0
        critical_issues = 0
        
        if static_analysis:
            total_issues += sum(static_analysis.issue_summary.values())
            critical_issues += static_analysis.issue_summary.get('error', 0)
        
        if semantic_verification:
            total_issues += len(semantic_verification.issues)
            critical_issues += len([
                issue for issue in semantic_verification.issues 
                if issue.severity.value in ['critical', 'high']
            ])
        
        # Calculate test success rate
        test_success_rate = 0.0
        if code_verification and code_verification.test_executions:
            total_tests = sum(exec.tests_run for exec in code_verification.test_executions)
            passed_tests = sum(exec.tests_passed for exec in code_verification.test_executions)
            if total_tests > 0:
                test_success_rate = passed_tests / total_tests
        
        if semantic_verification:
            total_behavior_tests = (semantic_verification.behavior_tests_passed + 
                                  semantic_verification.behavior_tests_failed)
            if total_behavior_tests > 0:
                behavior_success_rate = (semantic_verification.behavior_tests_passed / 
                                       total_behavior_tests)
                if test_success_rate > 0:
                    test_success_rate = (test_success_rate + behavior_success_rate) / 2
                else:
                    test_success_rate = behavior_success_rate
        
        # Generate summary
        summary = self._generate_summary(
            overall_score, total_issues, critical_issues, test_success_rate
        )
        
        # Generate recommendations
        recommendations = self._generate_integrated_recommendations(
            code_verification, static_analysis, semantic_verification
        )
        
        # Collect metadata
        metadata = {
            'verification_level': verification_level.value,
            'systems_used': [],
            'total_execution_time': 0.0
        }
        
        if code_verification:
            metadata['systems_used'].append('code_testing')
            if code_verification.test_executions:
                metadata['total_execution_time'] += sum(
                    exec.duration for exec in code_verification.test_executions
                )
        
        if static_analysis:
            metadata['systems_used'].append('static_analysis')
            if static_analysis.lint_results:
                metadata['total_execution_time'] += sum(
                    result.duration for result in static_analysis.lint_results
                )
        
        if semantic_verification:
            metadata['systems_used'].append('semantic_verification')
        
        return IntegratedVerificationResult(
            overall_score=overall_score,
            verification_level=verification_level,
            code_verification=code_verification,
            static_analysis=static_analysis,
            semantic_verification=semantic_verification,
            total_issues=total_issues,
            critical_issues=critical_issues,
            test_success_rate=test_success_rate,
            summary=summary,
            recommendations=recommendations,
            metadata=metadata
        )
    
    def _generate_summary(self, overall_score: float, total_issues: int, 
                         critical_issues: int, test_success_rate: float) -> str:
        """Generate a human-readable summary of verification results."""
        
        # Score interpretation
        if overall_score >= 0.9:
            score_desc = "Excellent"
        elif overall_score >= 0.8:
            score_desc = "Good"
        elif overall_score >= 0.7:
            score_desc = "Fair"
        elif overall_score >= 0.5:
            score_desc = "Poor"
        else:
            score_desc = "Critical Issues"
        
        # Issue summary
        if critical_issues > 0:
            issue_desc = f"{critical_issues} critical issues require immediate attention"
        elif total_issues > 10:
            issue_desc = f"{total_issues} issues found, consider addressing major ones"
        elif total_issues > 0:
            issue_desc = f"{total_issues} minor issues found"
        else:
            issue_desc = "No significant issues detected"
        
        # Test summary
        if test_success_rate >= 0.9:
            test_desc = "All tests passing"
        elif test_success_rate >= 0.7:
            test_desc = "Most tests passing"
        elif test_success_rate > 0:
            test_desc = f"Only {test_success_rate:.0%} of tests passing"
        else:
            test_desc = "No tests passing"
        
        return f"{score_desc} code quality (score: {overall_score:.2f}). {issue_desc}. {test_desc}."
    
    def _generate_integrated_recommendations(self, 
                                           code_verification: Optional[CodeVerificationResult],
                                           static_analysis: Optional[StaticAnalysisResult],
                                           semantic_verification: Optional[SemanticVerificationResult]) -> List[str]:
        """Generate integrated recommendations from all verification systems."""
        
        recommendations = []
        
        # Priority 1: Critical functional issues
        if code_verification and code_verification.overall_result.value != "pass":
            recommendations.append("Fix functional issues - code tests are failing")
        
        if semantic_verification and semantic_verification.overall_correctness < 0.5:
            recommendations.append("Address semantic correctness issues - logic may be flawed")
        
        # Priority 2: Code quality issues
        if static_analysis and static_analysis.overall_score < 5.0:
            recommendations.append("Improve code quality - multiple style and structure issues")
        
        # Priority 3: Specific improvements
        if static_analysis and static_analysis.recommendations:
            recommendations.extend(static_analysis.recommendations[:2])  # Top 2
        
        if semantic_verification and semantic_verification.suggestions:
            recommendations.extend(semantic_verification.suggestions[:2])  # Top 2
        
        # Priority 4: General improvements
        if code_verification and code_verification.test_executions:
            avg_coverage = sum(
                exec.coverage_percentage or 0 
                for exec in code_verification.test_executions
            ) / len(code_verification.test_executions)
            
            if avg_coverage < 80:
                recommendations.append("Increase test coverage for better reliability")
        
        # Remove duplicates and limit
        unique_recommendations = []
        for rec in recommendations:
            if rec not in unique_recommendations:
                unique_recommendations.append(rec)
        
        return unique_recommendations[:7]  # Limit to top 7 recommendations
    
    def cleanup(self):
        """Clean up all verifier resources."""
        try:
            self.code_verifier.cleanup()
        except Exception as e:
            logger.warning(f"Error cleaning up code verifier: {e}")
        
        try:
            self.lint_verifier.cleanup()
        except Exception as e:
            logger.warning(f"Error cleaning up lint verifier: {e}")
        
        try:
            self.semantic_verifier.cleanup()
        except Exception as e:
            logger.warning(f"Error cleaning up semantic verifier: {e}")
    
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup()


# Convenience functions for common verification scenarios

def verify_function_complete(code: str, function_name: str, 
                           test_cases: List[Tuple[Any, Any]],
                           algorithm_type: Optional[str] = None) -> IntegratedVerificationResult:
    """
    Perform complete verification of a function implementation.
    
    Args:
        code: The code containing the function.
        function_name: Name of the function to verify.
        test_cases: List of (input, expected_output) tuples.
        algorithm_type: Optional algorithm type for semantic analysis.
        
    Returns:
        IntegratedVerificationResult with comprehensive analysis.
    """
    from .code_tests import verify_function_implementation
    
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
    
    # Create behavior tests for semantic verification
    behavior_tests = [
        BehaviorTest(
            name=f"behavior_test_{i+1}",
            input_data=input_val,
            expected_output=expected,
            description=f"Test case {i+1}: {function_name}({input_val}) should return {expected}"
        )
        for i, (input_val, expected) in enumerate(test_cases)
    ]
    
    verifier = IntegratedVerifier()
    try:
        return verifier.verify_code_comprehensive(
            code=code,
            test_code=test_code,
            expected_functions=[function_name],
            behavior_tests=behavior_tests,
            expected_algorithm=algorithm_type,
            verification_level=VerificationLevel.COMPREHENSIVE
        )
    finally:
        verifier.cleanup()


def verify_code_basic(code: str, test_code: Optional[str] = None) -> IntegratedVerificationResult:
    """
    Perform basic verification with minimal checks.
    
    Args:
        code: The code to verify.
        test_code: Optional test code.
        
    Returns:
        IntegratedVerificationResult with basic analysis.
    """
    verifier = IntegratedVerifier()
    try:
        return verifier.verify_code_comprehensive(
            code=code,
            test_code=test_code,
            verification_level=VerificationLevel.BASIC
        )
    finally:
        verifier.cleanup()


def verify_code_strict(code: str, 
                      test_code: Optional[str] = None,
                      expected_functions: Optional[List[str]] = None,
                      behavior_tests: Optional[List[BehaviorTest]] = None,
                      expected_algorithm: Optional[str] = None) -> IntegratedVerificationResult:
    """
    Perform strict verification with all checks enabled.
    
    Args:
        code: The code to verify.
        test_code: Optional test code.
        expected_functions: Expected function names.
        behavior_tests: Behavioral test cases.
        expected_algorithm: Expected algorithm type.
        
    Returns:
        IntegratedVerificationResult with strict analysis.
    """
    verifier = IntegratedVerifier()
    try:
        return verifier.verify_code_comprehensive(
            code=code,
            test_code=test_code,
            expected_functions=expected_functions,
            behavior_tests=behavior_tests,
            expected_algorithm=expected_algorithm,
            verification_level=VerificationLevel.STRICT
        )
    finally:
        verifier.cleanup()


# Export main classes and functions
__all__ = [
    'IntegratedVerifier',
    'IntegratedVerificationResult',
    'VerificationLevel',
    'verify_function_complete',
    'verify_code_basic',
    'verify_code_strict',
    'BehaviorTest'
]