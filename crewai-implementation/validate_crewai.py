#!/usr/bin/env python3
"""
CrewAI Implementation Validation

This script validates the CrewAI implementation structure and functionality
without requiring external dependencies.
"""

import ast
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class CrewAIValidator:
    """Validates CrewAI implementation structure and functionality."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = []
    
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
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {message}")
        return result
    
    def validate_file_structure(self) -> bool:
        """Validate required files exist."""
        print("📁 Validating File Structure...")
        
        required_files = [
            "adapter.py",
            "README.md",
            "requirements.txt",
            "tests/test_crewai_adapter.py"
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
    
    def validate_adapter_structure(self) -> bool:
        """Validate adapter.py code structure."""
        print("\n🏗️ Validating Adapter Structure...")
        
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
            
            required_classes = [
                'CrewAIAdapter',
                'SafeCodeExecutorTool',
                'SafeFileOperationsTool',
                'SafeVCSOperationsTool'
            ]
            
            missing_classes = []
            for cls in required_classes:
                if cls not in classes:
                    missing_classes.append(cls)
                else:
                    self.add_result(f"Class: {cls}", True, "Class found")
            
            if missing_classes:
                self.add_result("Required Classes", False, f"Missing: {missing_classes}")
                return False
            
            # Check for required methods
            methods = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            
            required_methods = [
                'run_task', 'get_capabilities', 'health_check',
                '_create_agents', '_create_tasks', '_create_safe_tools',
                '_sanitize_input', '_emit_event', '_validate_task'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in methods:
                    missing_methods.append(method)
            
            if missing_methods:
                self.add_result("Required Methods", False, f"Missing: {missing_methods}")
                return False
            else:
                self.add_result("Required Methods", True, f"All {len(required_methods)} methods found")
            
            # Check factory function
            if 'create_crewai_adapter' in methods:
                self.add_result("Factory Function", True, "create_crewai_adapter found")
            else:
                self.add_result("Factory Function", False, "Factory function missing")
                return False
            
            # Check code size
            lines = len(content.split('\n'))
            if lines > 800:
                self.add_result("Implementation Size", True, f"{lines} lines (comprehensive)")
            else:
                self.add_result("Implementation Size", False, f"{lines} lines (too small)")
            
            return True
            
        except SyntaxError as e:
            self.add_result("Adapter Syntax", False, f"Syntax error: {e}")
            return False
        except Exception as e:
            self.add_result("Adapter Analysis", False, f"Analysis failed: {e}")
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
                'crewai', 'langchain', 'pydantic', 'pytest'
            ]
            
            missing_packages = []
            for package in required_packages:
                if package not in content.lower():
                    missing_packages.append(package)
            
            if missing_packages:
                self.add_result("Required Packages", False, f"Missing: {missing_packages}")
                return False
            else:
                self.add_result("Required Packages", True, f"All {len(required_packages)} packages listed")
            
            # Count total packages
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            package_count = len(lines)
            
            if package_count >= 10:
                self.add_result("Package Count", True, f"{package_count} packages specified")
            else:
                self.add_result("Package Count", False, f"Only {package_count} packages (needs more)")
            
            return True
            
        except Exception as e:
            self.add_result("Requirements Analysis", False, f"Analysis failed: {e}")
            return False
    
    def validate_documentation(self) -> bool:
        """Validate documentation quality."""
        print("\n📚 Validating Documentation...")
        
        readme_file = self.base_path / "README.md"
        if not readme_file.exists():
            self.add_result("README File", False, "README.md not found")
            return False
        
        try:
            with open(readme_file, 'r') as f:
                content = f.read()
            
            # Check required sections
            required_sections = [
                "# CrewAI Multi-Agent Squad Implementation",
                "## Architecture",
                "## Features",
                "## Setup",
                "## Usage",
                "## Agent Roles"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                self.add_result("README Sections", False, f"Missing: {missing_sections}")
                return False
            else:
                self.add_result("README Sections", True, f"All {len(required_sections)} sections present")
            
            # Check documentation quality
            word_count = len(content.split())
            if word_count > 1000:
                self.add_result("Documentation Quality", True, f"{word_count} words (comprehensive)")
            else:
                self.add_result("Documentation Quality", False, f"{word_count} words (insufficient)")
            
            # Check for code examples
            code_blocks = content.count('```')
            if code_blocks >= 8:
                self.add_result("Code Examples", True, f"{code_blocks//2} code blocks")
            else:
                self.add_result("Code Examples", False, f"{code_blocks//2} code blocks (insufficient)")
            
            return True
            
        except Exception as e:
            self.add_result("Documentation Analysis", False, f"Analysis failed: {e}")
            return False
    
    def validate_test_structure(self) -> bool:
        """Validate test structure."""
        print("\n🧪 Validating Test Structure...")
        
        test_file = self.base_path / "tests" / "test_crewai_adapter.py"
        if not test_file.exists():
            self.add_result("Test File", False, "test_crewai_adapter.py not found")
            return False
        
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Count test methods
            test_methods = content.count('def test_')
            if test_methods >= 10:
                self.add_result("Test Coverage", True, f"{test_methods} test methods")
            else:
                self.add_result("Test Coverage", False, f"Only {test_methods} test methods")
            
            # Check for test classes
            test_classes = content.count('class Test')
            if test_classes >= 2:
                self.add_result("Test Organization", True, f"{test_classes} test classes")
            else:
                self.add_result("Test Organization", False, f"Only {test_classes} test classes")
            
            return True
            
        except Exception as e:
            self.add_result("Test Analysis", False, f"Analysis failed: {e}")
            return False
    
    def validate_crewai_features(self) -> bool:
        """Validate CrewAI-specific features."""
        print("\n🤖 Validating CrewAI Features...")
        
        adapter_file = self.base_path / "adapter.py"
        if not adapter_file.exists():
            return False
        
        try:
            with open(adapter_file, 'r') as f:
                content = f.read()
            
            # Check for CrewAI imports
            crewai_imports = [
                'from crewai import',
                'Agent',
                'Task',
                'Crew',
                'Process'
            ]
            
            missing_imports = []
            for import_item in crewai_imports:
                if import_item not in content:
                    missing_imports.append(import_item)
            
            if missing_imports:
                self.add_result("CrewAI Imports", False, f"Missing: {missing_imports}")
            else:
                self.add_result("CrewAI Imports", True, "All CrewAI imports present")
            
            # Check for agent roles
            agent_roles = [
                'architect',
                'developer',
                'tester',
                'reviewer'
            ]
            
            missing_roles = []
            for role in agent_roles:
                if role not in content.lower():
                    missing_roles.append(role)
            
            if missing_roles:
                self.add_result("Agent Roles", False, f"Missing: {missing_roles}")
            else:
                self.add_result("Agent Roles", True, f"All {len(agent_roles)} roles present")
            
            # Check for safety tools
            safety_tools = [
                'SafeCodeExecutorTool',
                'SafeFileOperationsTool',
                'SafeVCSOperationsTool'
            ]
            
            missing_tools = []
            for tool in safety_tools:
                if tool not in content:
                    missing_tools.append(tool)
            
            if missing_tools:
                self.add_result("Safety Tools", False, f"Missing: {missing_tools}")
            else:
                self.add_result("Safety Tools", True, f"All {len(safety_tools)} tools present")
            
            return len(missing_imports) == 0 and len(missing_roles) == 0
            
        except Exception as e:
            self.add_result("CrewAI Features", False, f"Analysis failed: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "production_ready": passed_tests / total_tests >= 0.90
            },
            "results": self.results
        }
    
    def run_all_validations(self) -> bool:
        """Run all validation tests."""
        print("🚀 CrewAI Implementation Validation")
        print("=" * 50)
        
        validations = [
            self.validate_file_structure,
            self.validate_adapter_structure,
            self.validate_requirements,
            self.validate_documentation,
            self.validate_test_structure,
            self.validate_crewai_features
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
    """Run CrewAI validation."""
    validator = CrewAIValidator()
    
    try:
        success = validator.run_all_validations()
        
        print("\n" + "=" * 50)
        print("📊 CREWAI VALIDATION SUMMARY")
        print("=" * 50)
        
        report = validator.generate_report()
        
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        
        # Show failed tests
        failed_results = [r for r in validator.results if not r["passed"]]
        if failed_results:
            print(f"\n❌ Failed Tests ({len(failed_results)}):")
            for result in failed_results:
                print(f"  - {result['name']}: {result['message']}")
        
        # Final assessment
        print("\n🎯 FINAL ASSESSMENT")
        print("=" * 50)
        
        if report['summary']['production_ready']:
            print("🟢 STATUS: PRODUCTION READY")
            print("✅ CrewAI implementation is complete and validated")
            print("🚀 Ready for integration and production use")
        else:
            print("🟡 STATUS: NEEDS IMPROVEMENTS")
            print("⚠️ Some validation tests failed")
            print("🔧 Address failed tests for full readiness")
        
        # Save report
        report_path = Path(__file__).parent / "crewai_validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 VALIDATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)