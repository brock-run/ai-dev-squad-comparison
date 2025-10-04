# Verification System Developer Guide

This guide provides detailed information for developers who want to extend, customize, or contribute to the AI Dev Squad verification system.

## Architecture Overview

The verification system uses a multi-layered architecture with three main verification components:

```
benchmark/verifier/
├── __init__.py           # Integrated verification interface
├── code_tests.py         # Functional testing and execution
├── lint_type.py          # Static analysis and type checking
└── semantic.py           # Semantic correctness and logic analysis
```

### Core Components

#### 1. Integrated Verification (`__init__.py`)
- **IntegratedVerifier**: Main coordinator for all verification systems
- **VerificationLevel**: Configurable verification thoroughness
- **IntegratedVerificationResult**: Unified result aggregation

#### 2. Code Testing (`code_tests.py`)
- **CodeTestVerifier**: Automated test execution and validation
- **QualityEvaluator**: Multi-criteria response evaluation
- **PerformanceProfiler**: Resource usage monitoring during execution

#### 3. Static Analysis (`lint_type.py`)
- **LintTypeVerifier**: Multi-tool static analysis coordination
- **Tool Integration**: pylint, flake8, mypy, bandit, black, isort
- **Issue Classification**: Severity levels and categorization

#### 4. Semantic Verification (`semantic.py`)
- **SemanticVerifier**: Logic and algorithmic correctness analysis
- **BehaviorTest**: Behavioral testing framework
- **Pattern Detection**: Common issue and vulnerability detection

## Extending Verification Components

### Adding New Test Frameworks

#### 1. Extend CodeTestVerifier
```python
# In code_tests.py
class TestFramework(Enum):
    # ... existing frameworks ...
    CUSTOM_FRAMEWORK = "custom_framework"

class CodeTestVerifier:
    def _run_custom_framework(self, temp_dir: str, test_file: Path) -> TestExecution:
        """Run custom test framework."""
        start_time = time.time()
        
        try:
            # Implement custom framework execution
            cmd = ["custom-test-runner", str(test_file), "--output-format", "json"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=temp_dir
            )
            
            duration = time.time() - start_time
            
            # Parse custom framework output
            tests_run, tests_passed, tests_failed = self._parse_custom_output(result.stdout)
            
            return TestExecution(
                framework=TestFramework.CUSTOM_FRAMEWORK,
                result=TestResult.PASS if result.returncode == 0 else TestResult.FAIL,
                output=result.stdout,
                error_output=result.stderr,
                duration=duration,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed
            )
        
        except subprocess.TimeoutExpired:
            return TestExecution(
                framework=TestFramework.CUSTOM_FRAMEWORK,
                result=TestResult.TIMEOUT,
                output="",
                error_output="Custom framework execution timed out",
                duration=self.timeout_seconds
            )
```

#### 2. Register Framework
```python
def _execute_tests(self, code: str, test_code: str, framework: TestFramework) -> TestExecution:
    """Execute tests based on framework."""
    # ... existing framework handling ...
    elif framework == TestFramework.CUSTOM_FRAMEWORK:
        return self._run_custom_framework(temp_dir, test_file)
```

### Adding New Static Analysis Tools

#### 1. Define Tool Type
```python
# In lint_type.py
class LintTool(Enum):
    # ... existing tools ...
    CUSTOM_LINTER = "custom_linter"
```

#### 2. Implement Tool Integration
```python
def _run_custom_linter(self, code_file: Path, strict_mode: bool, start_time: float) -> LintResult:
    """Run custom linting tool."""
    cmd = ["custom-linter", str(code_file), "--format", "json"]
    
    if strict_mode:
        cmd.append("--strict")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds
        )
        
        duration = time.time() - start_time
        issues = self._parse_custom_linter_output(result.stdout, code_file)
        
        return LintResult(
            tool=LintTool.CUSTOM_LINTER,
            success=result.returncode == 0,
            issues=issues,
            output=result.stdout,
            error_output=result.stderr,
            duration=duration
        )
    
    except subprocess.TimeoutExpired:
        return LintResult(
            tool=LintTool.CUSTOM_LINTER,
            success=False,
            issues=[],
            error_output="Custom linter execution timed out",
            duration=self.timeout_seconds
        )

def _parse_custom_linter_output(self, output: str, code_file: Path) -> List[LintIssue]:
    """Parse custom linter output format."""
    issues = []
    
    try:
        data = json.loads(output)
        for item in data.get('issues', []):
            issues.append(LintIssue(
                tool=LintTool.CUSTOM_LINTER,
                severity=self._map_custom_severity(item.get('severity', 'warning')),
                line=item.get('line', 0),
                column=item.get('column', 0),
                code=item.get('rule_id', ''),
                message=item.get('message', ''),
                rule=item.get('rule_name', ''),
                file_path=str(code_file)
            ))
    except json.JSONDecodeError:
        # Handle parsing errors
        pass
    
    return issues
```

### Adding New Semantic Analysis Patterns

#### 1. Extend Pattern Detection
```python
# In semantic.py
class SemanticIssueType(Enum):
    # ... existing types ...
    CUSTOM_PATTERN = "custom_pattern"

class SemanticVerifier:
    def __init__(self):
        # ... existing initialization ...
        self.pattern_matchers['custom_pattern'] = self._detect_custom_pattern
    
    def _detect_custom_pattern(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
        """Detect custom semantic patterns."""
        issues = []
        
        class CustomPatternAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.pattern_issues = []
            
            def visit_FunctionDef(self, node):
                # Implement custom pattern detection logic
                if self._matches_custom_pattern(node):
                    self.pattern_issues.append((
                        node.lineno,
                        "Custom pattern detected",
                        "Consider alternative implementation"
                    ))
                
                self.generic_visit(node)
            
            def _matches_custom_pattern(self, node) -> bool:
                # Implement pattern matching logic
                return False
        
        analyzer = CustomPatternAnalyzer()
        analyzer.visit(tree)
        
        for line_no, message, suggestion in analyzer.pattern_issues:
            issues.append(SemanticIssue(
                issue_type=SemanticIssueType.CUSTOM_PATTERN,
                severity=SemanticSeverity.MEDIUM,
                message=message,
                line=line_no,
                suggestion=suggestion
            ))
        
        return issues
```

#### 2. Algorithm-Specific Verification
```python
def _analyze_algorithm_correctness(self, tree: ast.AST, code: str, 
                                 expected_algorithm: str) -> List[SemanticIssue]:
    """Analyze algorithm-specific correctness."""
    issues = []
    
    # Add custom algorithm verification
    if expected_algorithm.lower() == "custom_algorithm":
        issues.extend(self._check_custom_algorithm(tree, code))
    
    # ... existing algorithm checks ...
    
    return issues

def _check_custom_algorithm(self, tree: ast.AST, code: str) -> List[SemanticIssue]:
    """Check custom algorithm implementation."""
    issues = []
    
    # Implement algorithm-specific checks
    required_patterns = ['initialization', 'iteration', 'termination']
    found_patterns = []
    
    # Analyze AST for required patterns
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and self._is_initialization(node):
            found_patterns.append('initialization')
        elif isinstance(node, (ast.For, ast.While)) and self._is_iteration(node):
            found_patterns.append('iteration')
        elif isinstance(node, ast.Return) and self._is_termination(node):
            found_patterns.append('termination')
    
    # Check for missing patterns
    missing_patterns = set(required_patterns) - set(found_patterns)
    for pattern in missing_patterns:
        issues.append(SemanticIssue(
            issue_type=SemanticIssueType.ALGORITHM_ERROR,
            severity=SemanticSeverity.HIGH,
            message=f"Custom algorithm missing {pattern} pattern",
            suggestion=f"Add proper {pattern} logic"
        ))
    
    return issues
```

## Custom Verification Levels

### Creating Domain-Specific Verification
```python
# Create custom_verification.py
from benchmark.verifier import IntegratedVerifier, VerificationLevel, IntegratedVerificationResult

class DomainSpecificVerifier(IntegratedVerifier):
    """Domain-specific verification with custom rules."""
    
    def __init__(self, domain: str, timeout_seconds: int = 60):
        super().__init__(timeout_seconds)
        self.domain = domain
        self.domain_rules = self._load_domain_rules(domain)
    
    def verify_domain_code(self, code: str, **kwargs) -> IntegratedVerificationResult:
        """Verify code with domain-specific rules."""
        
        # Apply domain-specific preprocessing
        processed_code = self._preprocess_code(code)
        
        # Use appropriate verification level based on domain
        verification_level = self._get_domain_verification_level()
        
        # Add domain-specific behavior tests
        behavior_tests = self._generate_domain_behavior_tests(code, **kwargs)
        
        # Run verification with domain customizations
        result = self.verify_code_comprehensive(
            code=processed_code,
            behavior_tests=behavior_tests,
            verification_level=verification_level,
            context={'domain': self.domain, 'rules': self.domain_rules}
        )
        
        # Apply domain-specific post-processing
        return self._postprocess_results(result)
    
    def _load_domain_rules(self, domain: str) -> Dict[str, Any]:
        """Load domain-specific verification rules."""
        domain_rules = {
            'web_development': {
                'required_patterns': ['input_validation', 'error_handling'],
                'forbidden_patterns': ['eval', 'exec'],
                'security_focus': True
            },
            'data_science': {
                'required_patterns': ['data_validation', 'null_handling'],
                'performance_focus': True,
                'memory_efficiency': True
            },
            'embedded_systems': {
                'required_patterns': ['resource_management', 'error_codes'],
                'memory_constraints': True,
                'real_time_requirements': True
            }
        }
        
        return domain_rules.get(domain, {})
```

## Performance Optimization

### Parallel Verification
```python
class ParallelVerifier(IntegratedVerifier):
    """Verification system with parallel component execution."""
    
    def verify_code_comprehensive(self, **kwargs) -> IntegratedVerificationResult:
        """Run verification components in parallel."""
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit verification tasks
            futures = {}
            
            if kwargs.get('verification_level') != VerificationLevel.BASIC:
                futures['code'] = executor.submit(self._run_code_verification, **kwargs)
                futures['static'] = executor.submit(self._run_static_analysis, **kwargs)
                
                if kwargs.get('verification_level') == VerificationLevel.COMPREHENSIVE:
                    futures['semantic'] = executor.submit(self._run_semantic_verification, **kwargs)
            
            # Collect results
            results = {}
            for component, future in futures.items():
                try:
                    results[component] = future.result(timeout=self.timeout_seconds)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"{component} verification timed out")
                    results[component] = None
                except Exception as e:
                    logger.error(f"{component} verification failed: {e}")
                    results[component] = None
        
        # Aggregate results
        return self._aggregate_parallel_results(results, **kwargs)
```

### Caching Integration
```python
class CachedVerifier(IntegratedVerifier):
    """Verification system with intelligent caching."""
    
    def __init__(self, timeout_seconds: int = 60, cache_dir: str = None):
        super().__init__(timeout_seconds)
        self.cache_dir = Path(cache_dir or "verification_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def verify_code_comprehensive(self, code: str, **kwargs) -> IntegratedVerificationResult:
        """Verify code with caching support."""
        
        # Generate cache key
        cache_key = self._generate_cache_key(code, **kwargs)
        cached_result = self._load_cached_result(cache_key)
        
        if cached_result:
            logger.debug("Using cached verification result")
            return cached_result
        
        # Run verification
        result = super().verify_code_comprehensive(code=code, **kwargs)
        
        # Cache successful results
        if result.overall_score > 0.0:
            self._save_cached_result(cache_key, result)
        
        return result
    
    def _generate_cache_key(self, code: str, **kwargs) -> str:
        """Generate cache key for verification parameters."""
        import hashlib
        
        key_components = [
            code,
            str(kwargs.get('verification_level', VerificationLevel.STANDARD)),
            str(kwargs.get('expected_functions', [])),
            str(kwargs.get('expected_algorithm', ''))
        ]
        
        key_string = '|'.join(key_components)
        return hashlib.sha256(key_string.encode()).hexdigest()
```

## Testing Custom Components

### Unit Testing Framework Extensions
```python
# test_custom_verification.py
import unittest
from unittest.mock import Mock, patch, MagicMock
from custom_verification import DomainSpecificVerifier

class TestCustomVerification(unittest.TestCase):
    """Test custom verification components."""
    
    def setUp(self):
        self.verifier = DomainSpecificVerifier('web_development')
        self.sample_code = '''
def process_user_input(user_data):
    if not user_data:
        raise ValueError("Input cannot be empty")
    
    # Sanitize input
    sanitized = user_data.strip()
    
    return sanitized.lower()
'''
    
    def test_domain_specific_rules(self):
        """Test domain-specific rule application."""
        result = self.verifier.verify_domain_code(self.sample_code)
        
        # Should detect input validation pattern
        self.assertGreater(result.overall_score, 0.7)
        
        # Should not have security issues
        security_issues = [
            issue for issue in result.semantic_verification.issues
            if 'security' in issue.issue_type.value
        ]
        self.assertEqual(len(security_issues), 0)
    
    @patch('subprocess.run')
    def test_custom_linter_integration(self, mock_run):
        """Test custom linter integration."""
        # Mock custom linter output
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"issues": []}',
            stderr=''
        )
        
        from benchmark.verifier.lint_type import LintTypeVerifier, LintTool
        
        verifier = LintTypeVerifier()
        result = verifier.verify_code(
            code=self.sample_code,
            lint_tools=[LintTool.CUSTOM_LINTER]
        )
        
        # Verify custom linter was called
        mock_run.assert_called()
        self.assertTrue(result.overall_score >= 0.0)
```

### Integration Testing
```python
def test_end_to_end_custom_verification():
    """Test complete custom verification workflow."""
    
    # Test code with known patterns
    test_code = '''
def secure_login(username, password):
    # Input validation
    if not username or not password:
        return {"error": "Missing credentials"}
    
    # Sanitize inputs
    username = username.strip().lower()
    
    # Hash password (simplified)
    import hashlib
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Simulate authentication
    if authenticate_user(username, password_hash):
        return {"success": True, "user": username}
    else:
        return {"error": "Invalid credentials"}

def authenticate_user(username, password_hash):
    # Simulate database lookup
    return True
'''
    
    # Run domain-specific verification
    verifier = DomainSpecificVerifier('web_development')
    result = verifier.verify_domain_code(test_code)
    
    # Validate results
    assert result.overall_score > 0.8
    assert result.total_issues < 5
    assert 'input_validation' in [p for p in result.semantic_verification.detected_patterns]
```

## Configuration and Deployment

### Custom Configuration Schema
```python
# verification_config.py
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class VerificationConfig:
    """Configuration for verification system."""
    
    # Global settings
    timeout_seconds: int = 60
    enable_caching: bool = True
    cache_dir: Optional[str] = None
    
    # Component settings
    code_testing: Dict[str, Any] = None
    static_analysis: Dict[str, Any] = None
    semantic_analysis: Dict[str, Any] = None
    
    # Domain-specific settings
    domain_rules: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.code_testing is None:
            self.code_testing = {
                'frameworks': ['unittest', 'pytest'],
                'enable_coverage': True,
                'timeout_per_test': 30
            }
        
        if self.static_analysis is None:
            self.static_analysis = {
                'tools': ['pylint', 'flake8', 'mypy'],
                'strict_mode': False,
                'ignore_rules': []
            }
        
        if self.semantic_analysis is None:
            self.semantic_analysis = {
                'enable_behavior_tests': True,
                'algorithm_verification': True,
                'security_analysis': True
            }

class ConfigurableVerifier(IntegratedVerifier):
    """Verification system with external configuration."""
    
    def __init__(self, config: VerificationConfig):
        super().__init__(config.timeout_seconds)
        self.config = config
        
        # Configure components based on config
        self._configure_components()
    
    def _configure_components(self):
        """Configure verification components based on configuration."""
        
        # Configure code testing
        if hasattr(self.code_verifier, 'configure'):
            self.code_verifier.configure(self.config.code_testing)
        
        # Configure static analysis
        if hasattr(self.lint_verifier, 'configure'):
            self.lint_verifier.configure(self.config.static_analysis)
        
        # Configure semantic analysis
        if hasattr(self.semantic_verifier, 'configure'):
            self.semantic_verifier.configure(self.config.semantic_analysis)
```

This developer guide provides the foundation for extending and customizing the verification system to meet specific requirements and use cases.