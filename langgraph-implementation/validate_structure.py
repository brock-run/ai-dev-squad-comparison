#!/usr/bin/env python3
"""
LangGraph Structure and Code Quality Validation

This script validates the structure, code quality, and completeness
of the LangGraph implementation without requiring external dependencies.
"""

import ast
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set


class StructureValidator:
    """Validates LangGraph implementation structure and code quality."""
    
    def __init__(self):
        self.results = []
        self.base_path = Path(__file__).parent
    
    def add_result(self, name: str, passed: bool, message: str = "", details: Dict[str, Any] = None):
        """Add a validation result."""
        result = {
            "name": name,
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}: {message}")
        return result
    
    def validate_file_structure(self) -> bool:
        """Validate required files exist."""
        print("\n📁 Validating File Structure...")
        
        required_files = [
            "adapter.py",
            "state/development_state.py",
            "README.md",
            "simple_test.py",
            "tests/test_langgraph_adapter.py",
            "requirements.txt"
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                self.add_result(f"File: {file_path}", True, "File exists")
            else:
                self.add_result(f"File: {file_path}", False, "File missing")
                all_exist = False
        
        return all_exist
    
    def validate_adapter_code_structure(self) -> bool:
        """Validate adapter.py code structure."""
        print("\n🏗️ Validating Adapter Code Structure...")
        
        adapter_file = self.base_path / "adapter.py"
        if not adapter_file.exists():
            self.add_result("Adapter File", False, "adapter.py not found")
            return False
        
        try:
            with open(adapter_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for required classes
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if 'LangGraphAdapter' not in classes:
                self.add_result("LangGraphAdapter Class", False, "Class not found")
                return False
            
            self.add_result("LangGraphAdapter Class", True, "Class found")
            
            # Check for required methods
            methods = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            
            required_methods = [
                'run_task', 'get_capabilities', 'health_check',
                '_architect_node', '_developer_node', '_tester_node',
                '_reviewer_node', '_vcs_node', '_error_handler_node',
                '_create_design', '_implement_code', '_create_tests',
                '_sanitize_input', '_validate_code'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in methods:
                    missing_methods.append(method)
            
            if missing_methods:
                self.add_result("Required Methods", False, f"Missing: {missing_methods}")
                return False
            
            self.add_result("Required Methods", True, f"All {len(required_methods)} methods found")
            
            # Check for proper imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            required_import_patterns = [
                'asyncio', 'logging', 'datetime', 'typing', 'pathlib'
            ]
            
            missing_imports = []
            for pattern in required_import_patterns:
                if not any(pattern in imp for imp in imports):
                    missing_imports.append(pattern)
            
            if missing_imports:
                self.add_result("Core Imports", False, f"Missing patterns: {missing_imports}")
            else:
                self.add_result("Core Imports", True, "All core import patterns found")
            
            # Check code metrics
            total_lines = len(content.split('\n'))
            self.add_result("Code Size", True, f"{total_lines} lines of code")
            
            return len(missing_methods) == 0
            
        except SyntaxError as e:
            self.add_result("Adapter Syntax", False, f"Syntax error: {e}")
            return False
        except Exception as e:
            self.add_result("Adapter Analysis", False, f"Analysis failed: {e}")
            return False
    
    def validate_state_code_structure(self) -> bool:
        """Validate state/development_state.py code structure."""
        print("\n📊 Validating State Code Structure...")
        
        state_file = self.base_path / "state" / "development_state.py"
        if not state_file.exists():
            self.add_result("State File", False, "development_state.py not found")
            return False
        
        try:
            with open(state_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for required classes
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            required_classes = [
                'WorkflowStatus', 'AgentRole', 'AgentExecution',
                'DesignArtifact', 'CodeArtifact', 'TestArtifact',
                'ReviewArtifact', 'VCSArtifact', 'StateManager'
            ]
            
            missing_classes = []
            for cls in required_classes:
                if cls not in classes:
                    missing_classes.append(cls)
            
            if missing_classes:
                self.add_result("State Classes", False, f"Missing: {missing_classes}")
                return False
            
            self.add_result("State Classes", True, f"All {len(required_classes)} classes found")
            
            # Check for required functions
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            required_functions = ['create_initial_state', 'validate_state']
            missing_functions = []
            for func in required_functions:
                if func not in functions:
                    missing_functions.append(func)
            
            if missing_functions:
                self.add_result("State Functions", False, f"Missing: {missing_functions}")
            else:
                self.add_result("State Functions", True, f"All {len(required_functions)} functions found")
            
            return len(missing_classes) == 0
            
        except Exception as e:
            self.add_result("State Analysis", False, f"Analysis failed: {e}")
            return False
    
    def validate_documentation_quality(self) -> bool:
        """Validate documentation quality and completeness."""
        print("\n📚 Validating Documentation Quality...")
        
        readme_file = self.base_path / "README.md"
        if not readme_file.exists():
            self.add_result("README File", False, "README.md not found")
            return False
        
        try:
            with open(readme_file, 'r') as f:
                content = f.read()
            
            # Check required sections
            required_sections = [
                "# LangGraph Multi-Agent Squad Implementation",
                "## Architecture",
                "## Features",
                "## Setup",
                "## Usage",
                "## Workflow States",
                "## State Artifacts",
                "## Testing",
                "## Safety Controls",
                "## VCS Integration",
                "## Troubleshooting"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                self.add_result("README Sections", False, f"Missing: {missing_sections}")
                return False
            
            self.add_result("README Sections", True, f"All {len(required_sections)} sections found")
            
            # Check documentation length and quality
            word_count = len(content.split())
            if word_count < 1000:
                self.add_result("Documentation Length", False, f"Too short: {word_count} words")
            else:
                self.add_result("Documentation Length", True, f"Comprehensive: {word_count} words")
            
            # Check for code examples
            code_blocks = content.count('```')
            if code_blocks < 10:
                self.add_result("Code Examples", False, f"Too few: {code_blocks // 2} code blocks")
            else:
                self.add_result("Code Examples", True, f"Good coverage: {code_blocks // 2} code blocks")
            
            return len(missing_sections) == 0
            
        except Exception as e:
            self.add_result("Documentation Analysis", False, f"Analysis failed: {e}")
            return False
    
    def validate_test_structure(self) -> bool:
        """Validate test file structure and completeness."""
        print("\n🧪 Validating Test Structure...")
        
        # Check simple test
        simple_test = self.base_path / "simple_test.py"
        if simple_test.exists():
            self.add_result("Simple Test", True, "Structure test exists")
        else:
            self.add_result("Simple Test", False, "Structure test missing")
        
        # Check comprehensive test
        comprehensive_test = self.base_path / "tests" / "test_langgraph_adapter.py"
        if comprehensive_test.exists():
            try:
                with open(comprehensive_test, 'r') as f:
                    content = f.read()
                
                # Count test methods
                test_methods = content.count('def test_')
                if test_methods < 5:
                    self.add_result("Test Coverage", False, f"Too few tests: {test_methods}")
                else:
                    self.add_result("Test Coverage", True, f"Good coverage: {test_methods} test methods")
                
            except Exception as e:
                self.add_result("Test Analysis", False, f"Analysis failed: {e}")
                return False
        else:
            self.add_result("Comprehensive Test", False, "Comprehensive test missing")
            return False
        
        return True
    
    def validate_code_quality(self) -> bool:
        """Validate code quality metrics."""
        print("\n🔍 Validating Code Quality...")
        
        adapter_file = self.base_path / "adapter.py"
        if not adapter_file.exists():
            return False
        
        try:
            with open(adapter_file, 'r') as f:
                content = f.read()
            
            # Check for docstrings
            docstring_count = content.count('"""')
            if docstring_count < 20:
                self.add_result("Documentation Strings", False, f"Too few: {docstring_count // 2} docstrings")
            else:
                self.add_result("Documentation Strings", True, f"Well documented: {docstring_count // 2} docstrings")
            
            # Check for error handling
            try_count = content.count('try:')
            except_count = content.count('except')
            
            if try_count < 10:
                self.add_result("Error Handling", False, f"Insufficient: {try_count} try blocks")
            else:
                self.add_result("Error Handling", True, f"Good coverage: {try_count} try blocks")
            
            # Check for logging
            logging_count = content.count('logger.')
            if logging_count < 10:
                self.add_result("Logging Coverage", False, f"Insufficient: {logging_count} log statements")
            else:
                self.add_result("Logging Coverage", True, f"Good coverage: {logging_count} log statements")
            
            # Check for type hints
            lines = content.split('\n')
            typed_functions = 0
            total_functions = 0
            
            for line in lines:
                if 'def ' in line or 'async def ' in line:
                    total_functions += 1
                    if '->' in line:
                        typed_functions += 1
            
            if total_functions > 0:
                type_coverage = (typed_functions / total_functions) * 100
                if type_coverage < 80:
                    self.add_result("Type Hints", False, f"Low coverage: {type_coverage:.1f}%")
                else:
                    self.add_result("Type Hints", True, f"Good coverage: {type_coverage:.1f}%")
            
            return True
            
        except Exception as e:
            self.add_result("Code Quality Analysis", False, f"Analysis failed: {e}")
            return False
    
    def validate_requirements(self) -> bool:
        """Validate requirements.txt completeness."""
        print("\n📦 Validating Requirements...")
        
        req_file = self.base_path / "requirements.txt"
        if not req_file.exists():
            self.add_result("Requirements File", False, "requirements.txt not found")
            return False
        
        try:
            with open(req_file, 'r') as f:
                content = f.read()
            
            required_packages = [
                'langgraph', 'langchain', 'pydantic', 'pytest'
            ]
            
            missing_packages = []
            for package in required_packages:
                if package not in content.lower():
                    missing_packages.append(package)
            
            if missing_packages:
                self.add_result("Required Packages", False, f"Missing: {missing_packages}")
            else:
                self.add_result("Required Packages", True, f"All {len(required_packages)} packages listed")
            
            # Count total packages
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            package_count = len(lines)
            
            self.add_result("Package Count", True, f"{package_count} packages specified")
            
            return len(missing_packages) == 0
            
        except Exception as e:
            self.add_result("Requirements Analysis", False, f"Analysis failed: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "categories": {
                "structure": [r for r in self.results if "File:" in r["name"] or "Structure" in r["name"]],
                "code_quality": [r for r in self.results if any(x in r["name"] for x in ["Code", "Methods", "Classes", "Quality"])],
                "documentation": [r for r in self.results if any(x in r["name"] for x in ["README", "Documentation", "Examples"])],
                "testing": [r for r in self.results if "Test" in r["name"]],
                "requirements": [r for r in self.results if "Requirements" in r["name"] or "Package" in r["name"]]
            },
            "results": self.results
        }
        
        return report
    
    def run_all_validations(self) -> bool:
        """Run all structure validations."""
        print("🚀 Starting LangGraph Structure and Quality Validation")
        print("=" * 60)
        
        validations = [
            self.validate_file_structure,
            self.validate_adapter_code_structure,
            self.validate_state_code_structure,
            self.validate_documentation_quality,
            self.validate_test_structure,
            self.validate_code_quality,
            self.validate_requirements
        ]
        
        all_passed = True
        
        for validation in validations:
            try:
                result = validation()
                if not result:
                    all_passed = False
            except Exception as e:
                self.add_result(validation.__name__, False, f"Validation failed: {e}")
                all_passed = False
        
        return all_passed


def main():
    """Run the structure validation suite."""
    validator = StructureValidator()
    
    try:
        success = validator.run_all_validations()
        
        print("\n" + "=" * 60)
        print("📊 STRUCTURE VALIDATION SUMMARY")
        print("=" * 60)
        
        report = validator.generate_report()
        
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        
        # Show category breakdown
        print("\n📋 Category Breakdown:")
        for category, results in report['categories'].items():
            if results:
                passed = sum(1 for r in results if r["passed"])
                total = len(results)
                print(f"  {category.title()}: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if success:
            print("\n🎉 ALL STRUCTURE VALIDATIONS PASSED!")
            print("✅ LangGraph implementation structure is complete and high-quality")
        else:
            print("\n❌ SOME STRUCTURE VALIDATIONS FAILED!")
            print("🔧 Please address the failed tests")
            
            # Show failed tests
            failed_tests = [r for r in validator.results if not r["passed"]]
            if failed_tests:
                print("\nFailed Tests:")
                for test in failed_tests:
                    print(f"  - {test['name']}: {test['message']}")
        
        # Save detailed report
        report_path = Path(__file__).parent / "structure_validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 STRUCTURE VALIDATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)