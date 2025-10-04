#!/usr/bin/env python3
"""
Lint and Type Checking Verification System

This module provides static analysis capabilities including linting,
type checking, and code quality assessment for benchmark verification.
"""

import os
import sys
import subprocess
import tempfile
import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)


class LintSeverity(Enum):
    """Lint issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STYLE = "style"


class LintTool(Enum):
    """Supported linting tools."""
    PYLINT = "pylint"
    FLAKE8 = "flake8"
    PYCODESTYLE = "pycodestyle"
    MYPY = "mypy"
    BANDIT = "bandit"
    BLACK = "black"
    ISORT = "isort"


@dataclass
class LintIssue:
    """Represents a single lint issue."""
    tool: LintTool
    severity: LintSeverity
    line: int
    column: int
    code: str
    message: str
    rule: Optional[str] = None
    file_path: Optional[str] = None


@dataclass
class LintResult:
    """Results from linting analysis."""
    tool: LintTool
    success: bool
    issues: List[LintIssue]
    score: Optional[float] = None
    output: str = ""
    error_output: str = ""
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypeCheckResult:
    """Results from type checking analysis."""
    success: bool
    issues: List[LintIssue]
    coverage_percentage: Optional[float] = None
    output: str = ""
    error_output: str = ""
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StaticAnalysisResult:
    """Complete static analysis results."""
    lint_results: List[LintResult]
    type_check_result: Optional[TypeCheckResult]
    overall_score: float
    issue_summary: Dict[LintSeverity, int]
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LintTypeVerifier:
    """Performs static analysis including linting and type checking."""
    
    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize lint and type verifier.
        
        Args:
            timeout_seconds: Maximum time to allow for each tool execution.
        """
        self.timeout_seconds = timeout_seconds
        self.temp_dirs = []
        
        # Check which tools are available
        self.available_tools = self._check_available_tools()
    
    def verify_code(self, code: str, 
                   enable_type_checking: bool = True,
                   lint_tools: Optional[List[LintTool]] = None,
                   strict_mode: bool = False) -> StaticAnalysisResult:
        """
        Perform comprehensive static analysis on code.
        
        Args:
            code: The code to analyze.
            enable_type_checking: Whether to perform type checking.
            lint_tools: Specific lint tools to use (None for all available).
            strict_mode: Whether to use strict checking rules.
            
        Returns:
            StaticAnalysisResult with comprehensive analysis results.
        """
        if lint_tools is None:
            lint_tools = [tool for tool in LintTool if tool in self.available_tools]
        
        lint_results = []
        type_check_result = None
        
        # Create temporary file for analysis
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        code_file = Path(temp_dir) / "code_to_analyze.py"
        
        try:
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Run lint tools
            for tool in lint_tools:
                if tool in self.available_tools:
                    result = self._run_lint_tool(tool, code_file, strict_mode)
                    lint_results.append(result)
            
            # Run type checking
            if enable_type_checking and LintTool.MYPY in self.available_tools:
                type_check_result = self._run_type_checking(code_file, strict_mode)
            
            # Calculate overall results
            overall_score = self._calculate_overall_score(lint_results, type_check_result)
            issue_summary = self._summarize_issues(lint_results, type_check_result)
            recommendations = self._generate_recommendations(lint_results, type_check_result)
            
            # Add metadata
            metadata = {
                'code_length': len(code),
                'line_count': len(code.split('\n')),
                'tools_used': [result.tool.value for result in lint_results],
                'type_checking_enabled': enable_type_checking,
                'strict_mode': strict_mode
            }
            
            return StaticAnalysisResult(
                lint_results=lint_results,
                type_check_result=type_check_result,
                overall_score=overall_score,
                issue_summary=issue_summary,
                recommendations=recommendations,
                metadata=metadata
            )
        
        except Exception as e:
            logger.error(f"Error during static analysis: {e}")
            return StaticAnalysisResult(
                lint_results=lint_results,
                type_check_result=type_check_result,
                overall_score=0.0,
                issue_summary={severity: 0 for severity in LintSeverity},
                recommendations=[f"Analysis failed: {str(e)}"]
            )
    
    def _check_available_tools(self) -> Set[LintTool]:
        """Check which linting tools are available in the environment."""
        available = set()
        
        tools_to_check = {
            LintTool.PYLINT: "pylint",
            LintTool.FLAKE8: "flake8",
            LintTool.PYCODESTYLE: "pycodestyle",
            LintTool.MYPY: "mypy",
            LintTool.BANDIT: "bandit",
            LintTool.BLACK: "black",
            LintTool.ISORT: "isort"
        }
        
        for tool, command in tools_to_check.items():
            try:
                result = subprocess.run(
                    [command, "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    available.add(tool)
                    logger.debug(f"Found {command}: {result.stdout.decode().strip()}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug(f"Tool {command} not available")
        
        return available
    
    def _run_lint_tool(self, tool: LintTool, code_file: Path, strict_mode: bool) -> LintResult:
        """Run a specific linting tool on the code file."""
        import time
        start_time = time.time()
        
        try:
            if tool == LintTool.PYLINT:
                return self._run_pylint(code_file, strict_mode, start_time)
            elif tool == LintTool.FLAKE8:
                return self._run_flake8(code_file, strict_mode, start_time)
            elif tool == LintTool.PYCODESTYLE:
                return self._run_pycodestyle(code_file, strict_mode, start_time)
            elif tool == LintTool.BANDIT:
                return self._run_bandit(code_file, strict_mode, start_time)
            elif tool == LintTool.BLACK:
                return self._run_black(code_file, strict_mode, start_time)
            elif tool == LintTool.ISORT:
                return self._run_isort(code_file, strict_mode, start_time)
            else:
                return LintResult(
                    tool=tool,
                    success=False,
                    issues=[],
                    error_output=f"Tool {tool.value} not implemented",
                    duration=time.time() - start_time
                )
        
        except Exception as e:
            return LintResult(
                tool=tool,
                success=False,
                issues=[],
                error_output=str(e),
                duration=time.time() - start_time
            )
    
    def _run_pylint(self, code_file: Path, strict_mode: bool, start_time: float) -> LintResult:
        """Run pylint on the code file."""
        cmd = ["pylint", str(code_file), "--output-format=json"]
        
        if not strict_mode:
            # Disable some overly strict checks for benchmark code
            cmd.extend([
                "--disable=missing-docstring,invalid-name,too-few-public-methods",
                "--disable=missing-module-docstring,missing-function-docstring"
            ])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            duration = time.time() - start_time
            issues = []
            score = None
            
            # Parse JSON output
            if result.stdout:
                try:
                    pylint_data = json.loads(result.stdout)
                    for item in pylint_data:
                        if isinstance(item, dict) and 'type' in item:
                            severity = self._map_pylint_severity(item['type'])
                            issues.append(LintIssue(
                                tool=LintTool.PYLINT,
                                severity=severity,
                                line=item.get('line', 0),
                                column=item.get('column', 0),
                                code=item.get('symbol', ''),
                                message=item.get('message', ''),
                                rule=item.get('message-id', ''),
                                file_path=str(code_file)
                            ))
                except json.JSONDecodeError:
                    # Fallback to parsing text output
                    issues = self._parse_pylint_text_output(result.stdout, code_file)
            
            # Extract score from stderr (pylint prints score there)
            if result.stderr:
                score_match = re.search(r'Your code has been rated at ([\d.]+)/10', result.stderr)
                if score_match:
                    score = float(score_match.group(1))
            
            return LintResult(
                tool=LintTool.PYLINT,
                success=result.returncode in [0, 1, 2, 4, 8, 16],  # Pylint exit codes
                issues=issues,
                score=score,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration
            )
        
        except subprocess.TimeoutExpired:
            return LintResult(
                tool=LintTool.PYLINT,
                success=False,
                issues=[],
                error_output="Pylint execution timed out",
                duration=self.timeout_seconds
            )
    
    def _run_flake8(self, code_file: Path, strict_mode: bool, start_time: float) -> LintResult:
        """Run flake8 on the code file."""
        cmd = ["flake8", str(code_file), "--format=json"]
        
        if not strict_mode:
            # Relax some rules for benchmark code
            cmd.extend(["--ignore=E501,W503,E203"])  # Line length, line break before binary operator
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            duration = time.time() - start_time
            issues = []
            
            # Parse output (flake8 doesn't always support JSON, fallback to text parsing)
            if result.stdout:
                issues = self._parse_flake8_output(result.stdout, code_file)
            
            return LintResult(
                tool=LintTool.FLAKE8,
                success=result.returncode == 0,
                issues=issues,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration
            )
        
        except subprocess.TimeoutExpired:
            return LintResult(
                tool=LintTool.FLAKE8,
                success=False,
                issues=[],
                error_output="Flake8 execution timed out",
                duration=self.timeout_seconds
            )
    
    def _run_pycodestyle(self, code_file: Path, strict_mode: bool, start_time: float) -> LintResult:
        """Run pycodestyle on the code file."""
        cmd = ["pycodestyle", str(code_file)]
        
        if not strict_mode:
            cmd.extend(["--ignore=E501,W503,E203"])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            duration = time.time() - start_time
            issues = self._parse_pycodestyle_output(result.stdout, code_file)
            
            return LintResult(
                tool=LintTool.PYCODESTYLE,
                success=result.returncode == 0,
                issues=issues,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration
            )
        
        except subprocess.TimeoutExpired:
            return LintResult(
                tool=LintTool.PYCODESTYLE,
                success=False,
                issues=[],
                error_output="Pycodestyle execution timed out",
                duration=self.timeout_seconds
            )
    
    def _run_bandit(self, code_file: Path, strict_mode: bool, start_time: float) -> LintResult:
        """Run bandit security linter on the code file."""
        cmd = ["bandit", "-f", "json", str(code_file)]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            duration = time.time() - start_time
            issues = []
            
            # Parse JSON output
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    for item in bandit_data.get('results', []):
                        severity = self._map_bandit_severity(item.get('issue_severity', 'LOW'))
                        issues.append(LintIssue(
                            tool=LintTool.BANDIT,
                            severity=severity,
                            line=item.get('line_number', 0),
                            column=item.get('col_offset', 0),
                            code=item.get('test_id', ''),
                            message=item.get('issue_text', ''),
                            rule=item.get('test_name', ''),
                            file_path=str(code_file)
                        ))
                except json.JSONDecodeError:
                    pass
            
            return LintResult(
                tool=LintTool.BANDIT,
                success=result.returncode == 0,
                issues=issues,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration
            )
        
        except subprocess.TimeoutExpired:
            return LintResult(
                tool=LintTool.BANDIT,
                success=False,
                issues=[],
                error_output="Bandit execution timed out",
                duration=self.timeout_seconds
            )
    
    def _run_black(self, code_file: Path, strict_mode: bool, start_time: float) -> LintResult:
        """Run black formatter check on the code file."""
        cmd = ["black", "--check", "--diff", str(code_file)]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            duration = time.time() - start_time
            issues = []
            
            # If black suggests changes, create an issue
            if result.returncode != 0 and result.stdout:
                issues.append(LintIssue(
                    tool=LintTool.BLACK,
                    severity=LintSeverity.STYLE,
                    line=1,
                    column=1,
                    code="format",
                    message="Code formatting could be improved",
                    rule="black-format"
                ))
            
            return LintResult(
                tool=LintTool.BLACK,
                success=result.returncode == 0,
                issues=issues,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration
            )
        
        except subprocess.TimeoutExpired:
            return LintResult(
                tool=LintTool.BLACK,
                success=False,
                issues=[],
                error_output="Black execution timed out",
                duration=self.timeout_seconds
            )
    
    def _run_isort(self, code_file: Path, strict_mode: bool, start_time: float) -> LintResult:
        """Run isort import sorting check on the code file."""
        cmd = ["isort", "--check-only", "--diff", str(code_file)]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            duration = time.time() - start_time
            issues = []
            
            # If isort suggests changes, create an issue
            if result.returncode != 0 and result.stdout:
                issues.append(LintIssue(
                    tool=LintTool.ISORT,
                    severity=LintSeverity.STYLE,
                    line=1,
                    column=1,
                    code="import-order",
                    message="Import order could be improved",
                    rule="isort-order"
                ))
            
            return LintResult(
                tool=LintTool.ISORT,
                success=result.returncode == 0,
                issues=issues,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration
            )
        
        except subprocess.TimeoutExpired:
            return LintResult(
                tool=LintTool.ISORT,
                success=False,
                issues=[],
                error_output="Isort execution timed out",
                duration=self.timeout_seconds
            )
    
    def _run_type_checking(self, code_file: Path, strict_mode: bool) -> TypeCheckResult:
        """Run mypy type checking on the code file."""
        import time
        start_time = time.time()
        
        cmd = ["mypy", str(code_file), "--show-error-codes", "--no-error-summary"]
        
        if not strict_mode:
            cmd.extend([
                "--ignore-missing-imports",
                "--allow-untyped-defs",
                "--allow-incomplete-defs"
            ])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            duration = time.time() - start_time
            issues = self._parse_mypy_output(result.stdout, code_file)
            
            return TypeCheckResult(
                success=result.returncode == 0,
                issues=issues,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration
            )
        
        except subprocess.TimeoutExpired:
            return TypeCheckResult(
                success=False,
                issues=[],
                error_output="Mypy execution timed out",
                duration=self.timeout_seconds
            )
        except Exception as e:
            return TypeCheckResult(
                success=False,
                issues=[],
                error_output=str(e),
                duration=time.time() - start_time
            )
    
    def _map_pylint_severity(self, pylint_type: str) -> LintSeverity:
        """Map pylint message types to our severity levels."""
        mapping = {
            'error': LintSeverity.ERROR,
            'warning': LintSeverity.WARNING,
            'refactor': LintSeverity.INFO,
            'convention': LintSeverity.STYLE,
            'info': LintSeverity.INFO
        }
        return mapping.get(pylint_type.lower(), LintSeverity.WARNING)
    
    def _map_bandit_severity(self, bandit_severity: str) -> LintSeverity:
        """Map bandit severity levels to our severity levels."""
        mapping = {
            'HIGH': LintSeverity.ERROR,
            'MEDIUM': LintSeverity.WARNING,
            'LOW': LintSeverity.INFO
        }
        return mapping.get(bandit_severity.upper(), LintSeverity.WARNING)
    
    def _parse_pylint_text_output(self, output: str, code_file: Path) -> List[LintIssue]:
        """Parse pylint text output when JSON parsing fails."""
        issues = []
        lines = output.split('\n')
        
        for line in lines:
            # Example: "code_to_analyze.py:5:0: C0103: Invalid name "x" (invalid-name)"
            match = re.match(r'([^:]+):(\d+):(\d+):\s*([CRWEF]\d+):\s*(.+)', line)
            if match:
                file_path, line_num, col_num, code, message = match.groups()
                severity = self._map_pylint_code_to_severity(code[0])
                
                issues.append(LintIssue(
                    tool=LintTool.PYLINT,
                    severity=severity,
                    line=int(line_num),
                    column=int(col_num),
                    code=code,
                    message=message,
                    file_path=str(code_file)
                ))
        
        return issues
    
    def _map_pylint_code_to_severity(self, code_prefix: str) -> LintSeverity:
        """Map pylint code prefixes to severity levels."""
        mapping = {
            'E': LintSeverity.ERROR,
            'W': LintSeverity.WARNING,
            'R': LintSeverity.INFO,
            'C': LintSeverity.STYLE,
            'I': LintSeverity.INFO
        }
        return mapping.get(code_prefix, LintSeverity.WARNING)
    
    def _parse_flake8_output(self, output: str, code_file: Path) -> List[LintIssue]:
        """Parse flake8 output."""
        issues = []
        lines = output.split('\n')
        
        for line in lines:
            # Example: "code_to_analyze.py:1:1: E302 expected 2 blank lines, found 1"
            match = re.match(r'([^:]+):(\d+):(\d+):\s*([A-Z]\d+)\s*(.+)', line)
            if match:
                file_path, line_num, col_num, code, message = match.groups()
                severity = self._map_flake8_code_to_severity(code[0])
                
                issues.append(LintIssue(
                    tool=LintTool.FLAKE8,
                    severity=severity,
                    line=int(line_num),
                    column=int(col_num),
                    code=code,
                    message=message,
                    file_path=str(code_file)
                ))
        
        return issues
    
    def _map_flake8_code_to_severity(self, code_prefix: str) -> LintSeverity:
        """Map flake8 code prefixes to severity levels."""
        mapping = {
            'E': LintSeverity.ERROR,
            'W': LintSeverity.WARNING,
            'F': LintSeverity.ERROR,
            'C': LintSeverity.STYLE,
            'N': LintSeverity.STYLE
        }
        return mapping.get(code_prefix, LintSeverity.WARNING)
    
    def _parse_pycodestyle_output(self, output: str, code_file: Path) -> List[LintIssue]:
        """Parse pycodestyle output."""
        issues = []
        lines = output.split('\n')
        
        for line in lines:
            # Example: "code_to_analyze.py:1:1: E302 expected 2 blank lines, found 1"
            match = re.match(r'([^:]+):(\d+):(\d+):\s*([A-Z]\d+)\s*(.+)', line)
            if match:
                file_path, line_num, col_num, code, message = match.groups()
                severity = LintSeverity.STYLE if code.startswith('E') else LintSeverity.WARNING
                
                issues.append(LintIssue(
                    tool=LintTool.PYCODESTYLE,
                    severity=severity,
                    line=int(line_num),
                    column=int(col_num),
                    code=code,
                    message=message,
                    file_path=str(code_file)
                ))
        
        return issues
    
    def _parse_mypy_output(self, output: str, code_file: Path) -> List[LintIssue]:
        """Parse mypy output."""
        issues = []
        lines = output.split('\n')
        
        for line in lines:
            # Example: "code_to_analyze.py:5: error: Function is missing a return type annotation  [return]"
            match = re.match(r'([^:]+):(\d+):\s*(error|warning|note):\s*(.+?)(?:\s*\[([^\]]+)\])?$', line)
            if match:
                file_path, line_num, severity_str, message, code = match.groups()
                
                severity = LintSeverity.ERROR if severity_str == 'error' else LintSeverity.WARNING
                if severity_str == 'note':
                    severity = LintSeverity.INFO
                
                issues.append(LintIssue(
                    tool=LintTool.MYPY,
                    severity=severity,
                    line=int(line_num),
                    column=0,
                    code=code or '',
                    message=message,
                    rule=code,
                    file_path=str(code_file)
                ))
        
        return issues
    
    def _calculate_overall_score(self, lint_results: List[LintResult], 
                                type_check_result: Optional[TypeCheckResult]) -> float:
        """Calculate overall quality score from all results."""
        total_score = 0.0
        weight_sum = 0.0
        
        # Weight lint results
        for result in lint_results:
            if result.success:
                if result.score is not None:
                    # Use tool's own score (like pylint)
                    total_score += result.score * 1.0
                    weight_sum += 1.0
                else:
                    # Calculate score based on issues
                    issue_penalty = sum(
                        4.0 if issue.severity == LintSeverity.ERROR else
                        2.0 if issue.severity == LintSeverity.WARNING else
                        1.0 if issue.severity == LintSeverity.INFO else
                        0.5 for issue in result.issues
                    )
                    score = max(0.0, 10.0 - issue_penalty)
                    total_score += score * 0.5
                    weight_sum += 0.5
        
        # Weight type checking result
        if type_check_result and type_check_result.success:
            type_penalty = sum(
                3.0 if issue.severity == LintSeverity.ERROR else
                1.5 if issue.severity == LintSeverity.WARNING else
                0.5 for issue in type_check_result.issues
            )
            type_score = max(0.0, 10.0 - type_penalty)
            total_score += type_score * 0.8
            weight_sum += 0.8
        
        return total_score / weight_sum if weight_sum > 0 else 0.0
    
    def _summarize_issues(self, lint_results: List[LintResult], 
                         type_check_result: Optional[TypeCheckResult]) -> Dict[LintSeverity, int]:
        """Summarize issues by severity level."""
        summary = {severity: 0 for severity in LintSeverity}
        
        for result in lint_results:
            for issue in result.issues:
                summary[issue.severity] += 1
        
        if type_check_result:
            for issue in type_check_result.issues:
                summary[issue.severity] += 1
        
        return summary
    
    def _generate_recommendations(self, lint_results: List[LintResult], 
                                 type_check_result: Optional[TypeCheckResult]) -> List[str]:
        """Generate improvement recommendations based on analysis results."""
        recommendations = []
        
        # Analyze common issues
        all_issues = []
        for result in lint_results:
            all_issues.extend(result.issues)
        if type_check_result:
            all_issues.extend(type_check_result.issues)
        
        # Count issue types
        issue_counts = {}
        for issue in all_issues:
            key = (issue.tool, issue.code)
            issue_counts[key] = issue_counts.get(key, 0) + 1
        
        # Generate recommendations for common issues
        for (tool, code), count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 3:  # Multiple occurrences
                if tool == LintTool.PYLINT:
                    if code.startswith('C'):
                        recommendations.append("Consider following PEP 8 naming conventions")
                    elif code.startswith('R'):
                        recommendations.append("Consider refactoring for better code organization")
                elif tool == LintTool.FLAKE8:
                    if code.startswith('E'):
                        recommendations.append("Fix PEP 8 style violations for better readability")
                elif tool == LintTool.MYPY:
                    recommendations.append("Add type annotations for better code clarity")
        
        # General recommendations
        error_count = sum(1 for issue in all_issues if issue.severity == LintSeverity.ERROR)
        warning_count = sum(1 for issue in all_issues if issue.severity == LintSeverity.WARNING)
        
        if error_count > 0:
            recommendations.append(f"Fix {error_count} error(s) for code correctness")
        if warning_count > 5:
            recommendations.append(f"Address {warning_count} warning(s) for code quality")
        
        # Tool-specific recommendations
        if not any(result.tool == LintTool.BLACK for result in lint_results):
            recommendations.append("Consider using Black for consistent code formatting")
        
        if not type_check_result:
            recommendations.append("Consider adding type checking with mypy")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
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

def quick_lint_check(code: str) -> StaticAnalysisResult:
    """
    Perform a quick lint check with basic tools.
    
    Args:
        code: The code to analyze.
        
    Returns:
        StaticAnalysisResult with basic analysis.
    """
    verifier = LintTypeVerifier()
    try:
        return verifier.verify_code(
            code=code,
            enable_type_checking=False,
            lint_tools=[LintTool.FLAKE8, LintTool.PYCODESTYLE],
            strict_mode=False
        )
    finally:
        verifier.cleanup()


def comprehensive_analysis(code: str) -> StaticAnalysisResult:
    """
    Perform comprehensive static analysis with all available tools.
    
    Args:
        code: The code to analyze.
        
    Returns:
        StaticAnalysisResult with comprehensive analysis.
    """
    verifier = LintTypeVerifier()
    try:
        return verifier.verify_code(
            code=code,
            enable_type_checking=True,
            lint_tools=None,  # Use all available tools
            strict_mode=True
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

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
    
    result = comprehensive_analysis(sample_code)
    
    print(f"Overall Score: {result.overall_score:.1f}/10")
    print(f"Issue Summary: {result.issue_summary}")
    
    print("\nLint Results:")
    for lint_result in result.lint_results:
        print(f"  {lint_result.tool.value}: {'✓' if lint_result.success else '✗'} "
              f"({len(lint_result.issues)} issues)")
    
    if result.type_check_result:
        print(f"Type Checking: {'✓' if result.type_check_result.success else '✗'} "
              f"({len(result.type_check_result.issues)} issues)")
    
    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")