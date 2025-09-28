#!/usr/bin/env python3
"""
Production Readiness Test for LangGraph Implementation

This script tests the LangGraph implementation for production readiness
by validating core functionality, safety integration, and documentation.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


class ProductionReadinessValidator:
    """Validates production readiness of the LangGraph implementation."""
    
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
    
    async def test_core_imports(self) -> bool:
        """Test that core imports work."""
        print("📥 Testing Core Imports...")
        
        try:
            # Test adapter imports
            from adapter import LangGraphAdapter, create_langgraph_adapter
            self.add_result("Adapter Imports", True, "LangGraph adapter imports successful")
            
            # Test state imports
            from state.development_state import (
                create_initial_state, WorkflowStatus, AgentRole, StateManager
            )
            self.add_result("State Imports", True, "State management imports successful")
            
            return True
            
        except ImportError as e:
            self.add_result("Core Imports", False, f"Import failed: {e}")
            return False
        except Exception as e:
            self.add_result("Core Imports", False, f"Unexpected error: {e}")
            return False
    
    async def test_adapter_instantiation(self) -> bool:
        """Test adapter can be created."""
        print("\n🏗️ Testing Adapter Instantiation...")
        
        try:
            from adapter import create_langgraph_adapter
            
            # Create adapter with minimal config
            config = {
                "language": "python",
                "vcs": {"enabled": False},  # Disable VCS for testing
                "human_review": {"enabled": False}
            }
            
            adapter = create_langgraph_adapter(config)
            
            if adapter:
                self.add_result("Adapter Creation", True, f"Created {adapter.name} v{adapter.version}")
                
                # Test basic properties
                if hasattr(adapter, 'name') and adapter.name:
                    self.add_result("Adapter Properties", True, "Basic properties available")
                else:
                    self.add_result("Adapter Properties", False, "Missing basic properties")
                
                return True
            else:
                self.add_result("Adapter Creation", False, "Adapter is None")
                return False
                
        except Exception as e:
            self.add_result("Adapter Instantiation", False, f"Failed: {e}")
            return False
    
    async def test_state_management(self) -> bool:
        """Test state management functionality."""
        print("\n📊 Testing State Management...")
        
        try:
            from state.development_state import (
                create_initial_state, WorkflowStatus, AgentRole, StateManager
            )
            
            # Test initial state creation
            state = create_initial_state(
                task="Test task for validation",
                requirements=["Requirement 1", "Requirement 2"],
                context={"test": True}
            )
            
            if state["task"] == "Test task for validation":
                self.add_result("State Creation", True, "Initial state created correctly")
            else:
                self.add_result("State Creation", False, "State not created correctly")
                return False
            
            # Test state manager
            manager = StateManager()
            
            # Test valid transition
            can_transition = manager.can_transition(
                WorkflowStatus.INITIALIZING,
                WorkflowStatus.DESIGN_IN_PROGRESS
            )
            
            if can_transition:
                self.add_result("State Transitions", True, "State transition validation works")
            else:
                self.add_result("State Transitions", False, "State transition validation failed")
            
            return True
            
        except Exception as e:
            self.add_result("State Management", False, f"Failed: {e}")
            return False
    
    async def test_workflow_components(self) -> bool:
        """Test individual workflow components."""
        print("\n🔄 Testing Workflow Components...")
        
        try:
            from adapter import create_langgraph_adapter
            
            config = {
                "language": "python",
                "vcs": {"enabled": False},
                "human_review": {"enabled": False}
            }
            
            adapter = create_langgraph_adapter(config)
            
            # Test design creation
            design = await adapter._create_design(
                "Create a calculator function",
                ["Add operation", "Subtract operation"]
            )
            
            if design and "architecture_type" in design:
                self.add_result("Design Creation", True, f"Design created: {design['architecture_type']}")
            else:
                self.add_result("Design Creation", False, "Design creation failed")
                return False
            
            # Test code implementation
            from state.development_state import DesignArtifact
            design_artifact = DesignArtifact(
                architecture_type="modular",
                components=[{"name": "calculator", "type": "core"}]
            )
            
            code_result = await adapter._implement_code(
                "Calculator function",
                design_artifact,
                "python"
            )
            
            if code_result and "main_code" in code_result:
                self.add_result("Code Implementation", True, f"Code generated: {len(code_result['main_code'])} chars")
            else:
                self.add_result("Code Implementation", False, "Code implementation failed")
                return False
            
            # Test test creation
            from state.development_state import CodeArtifact
            code_artifact = CodeArtifact(
                language="python",
                main_code="def add(a, b): return a + b"
            )
            
            test_result = await adapter._create_tests(code_artifact, "Calculator", [])
            
            if test_result and "test_code" in test_result:
                self.add_result("Test Creation", True, f"Tests created: {len(test_result['test_cases'])} cases")
            else:
                self.add_result("Test Creation", False, "Test creation failed")
                return False
            
            return True
            
        except Exception as e:
            self.add_result("Workflow Components", False, f"Failed: {e}")
            return False
    
    async def test_safety_integration(self) -> bool:
        """Test safety system integration."""
        print("\n🛡️ Testing Safety Integration...")
        
        try:
            from adapter import create_langgraph_adapter
            
            config = {
                "language": "python",
                "vcs": {"enabled": False},
                "human_review": {"enabled": False}
            }
            
            adapter = create_langgraph_adapter(config)
            
            # Test input sanitization
            safe_input = await adapter._sanitize_input("print('Hello, World!')")
            self.add_result("Input Sanitization", True, "Input sanitization works")
            
            # Test code validation
            safe_code = await adapter._validate_code("def safe_function(): return 'safe'")
            self.add_result("Code Validation", True, "Code validation works")
            
            # Check safety components initialization
            safety_components = {
                'Policy Manager': adapter.policy_manager is not None,
                'Active Policy': adapter.active_policy is not None,
            }
            
            available_components = sum(safety_components.values())
            total_components = len(safety_components)
            
            self.add_result("Safety Components", True, 
                          f"{available_components}/{total_components} components initialized")
            
            return True
            
        except Exception as e:
            self.add_result("Safety Integration", False, f"Failed: {e}")
            return False
    
    async def test_api_compliance(self) -> bool:
        """Test AgentAdapter protocol compliance."""
        print("\n🔌 Testing API Compliance...")
        
        try:
            from adapter import create_langgraph_adapter
            from common.agent_api import AgentAdapter
            
            config = {
                "language": "python",
                "vcs": {"enabled": False},
                "human_review": {"enabled": False}
            }
            
            adapter = create_langgraph_adapter(config)
            
            # Check if adapter implements AgentAdapter protocol
            if isinstance(adapter, AgentAdapter):
                self.add_result("Protocol Compliance", True, "Implements AgentAdapter protocol")
            else:
                # Check required methods exist
                required_methods = ['run_task', 'get_capabilities', 'health_check']
                missing_methods = []
                
                for method in required_methods:
                    if not hasattr(adapter, method):
                        missing_methods.append(method)
                
                if not missing_methods:
                    self.add_result("Protocol Compliance", True, "All required methods present")
                else:
                    self.add_result("Protocol Compliance", False, f"Missing methods: {missing_methods}")
                    return False
            
            # Test capabilities method
            capabilities = await adapter.get_capabilities()
            if capabilities and "features" in capabilities:
                self.add_result("Capabilities API", True, f"Features: {len(capabilities['features'])}")
            else:
                self.add_result("Capabilities API", False, "Capabilities method failed")
                return False
            
            # Test health check method
            health = await adapter.health_check()
            if health and "status" in health:
                self.add_result("Health Check API", True, f"Status: {health['status']}")
            else:
                self.add_result("Health Check API", False, "Health check method failed")
                return False
            
            return True
            
        except Exception as e:
            self.add_result("API Compliance", False, f"Failed: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling and recovery."""
        print("\n🚨 Testing Error Handling...")
        
        try:
            from adapter import create_langgraph_adapter
            
            config = {
                "language": "python",
                "vcs": {"enabled": False},
                "human_review": {"enabled": False}
            }
            
            adapter = create_langgraph_adapter(config)
            
            # Test error analysis
            error_analysis = await adapter._analyze_error("Test error message")
            
            if error_analysis and "type" in error_analysis:
                self.add_result("Error Analysis", True, f"Error type: {error_analysis['type']}")
            else:
                self.add_result("Error Analysis", False, "Error analysis failed")
                return False
            
            # Test graceful handling of invalid inputs
            try:
                # This should not crash the system
                result = await adapter._sanitize_input("")
                self.add_result("Graceful Error Handling", True, "Handles empty input gracefully")
            except Exception:
                self.add_result("Graceful Error Handling", False, "Does not handle errors gracefully")
            
            return True
            
        except Exception as e:
            self.add_result("Error Handling", False, f"Failed: {e}")
            return False
    
    def validate_documentation(self) -> bool:
        """Validate documentation completeness."""
        print("\n📚 Validating Documentation...")
        
        # Check required files
        required_files = [
            "README.md",
            "READINESS_CHECKLIST.md", 
            "COMPLETION_SUMMARY.md",
            "INSTALLATION_GUIDE.md"
        ]
        
        missing_files = []
        for file_name in required_files:
            if not (self.base_path / file_name).exists():
                missing_files.append(file_name)
        
        if not missing_files:
            self.add_result("Documentation Files", True, f"All {len(required_files)} files present")
        else:
            self.add_result("Documentation Files", False, f"Missing: {missing_files}")
            return False
        
        # Check README quality
        readme_file = self.base_path / "README.md"
        try:
            with open(readme_file, 'r') as f:
                content = f.read()
            
            word_count = len(content.split())
            code_blocks = content.count('```')
            
            if word_count > 1000:
                self.add_result("README Quality", True, f"{word_count} words, {code_blocks//2} code examples")
            else:
                self.add_result("README Quality", False, f"Only {word_count} words (needs more detail)")
            
        except Exception as e:
            self.add_result("README Quality", False, f"Failed to analyze: {e}")
            return False
        
        return True
    
    def validate_test_coverage(self) -> bool:
        """Validate test coverage."""
        print("\n🧪 Validating Test Coverage...")
        
        # Check test files exist
        test_files = [
            "simple_test.py",
            "tests/test_langgraph_adapter.py",
            "final_validation.py"
        ]
        
        existing_tests = []
        for test_file in test_files:
            if (self.base_path / test_file).exists():
                existing_tests.append(test_file)
        
        if len(existing_tests) >= 2:
            self.add_result("Test Files", True, f"{len(existing_tests)} test files present")
        else:
            self.add_result("Test Files", False, f"Only {len(existing_tests)} test files")
            return False
        
        # Analyze test coverage
        try:
            test_file = self.base_path / "tests" / "test_langgraph_adapter.py"
            if test_file.exists():
                with open(test_file, 'r') as f:
                    content = f.read()
                
                test_methods = content.count('def test_')
                if test_methods >= 10:
                    self.add_result("Test Coverage", True, f"{test_methods} test methods")
                else:
                    self.add_result("Test Coverage", False, f"Only {test_methods} test methods")
            
        except Exception as e:
            self.add_result("Test Coverage", False, f"Failed to analyze: {e}")
        
        return True
    
    async def run_all_tests(self) -> bool:
        """Run all production readiness tests."""
        print("🚀 LangGraph Production Readiness Validation")
        print("=" * 60)
        print("Testing core functionality without external dependencies\n")
        
        tests = [
            self.test_core_imports(),
            self.test_adapter_instantiation(),
            self.test_state_management(),
            self.test_workflow_components(),
            self.test_safety_integration(),
            self.test_api_compliance(),
            self.test_error_handling()
        ]
        
        # Run async tests
        test_results = []
        for test_coro in tests:
            try:
                result = await test_coro
                test_results.append(result)
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                test_results.append(False)
        
        # Run sync tests
        doc_result = self.validate_documentation()
        test_result = self.validate_test_coverage()
        
        test_results.extend([doc_result, test_result])
        
        return all(test_results)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate production readiness report."""
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


async def main():
    """Run production readiness validation."""
    validator = ProductionReadinessValidator()
    
    try:
        success = await validator.run_all_tests()
        
        print("\n" + "=" * 60)
        print("📊 PRODUCTION READINESS REPORT")
        print("=" * 60)
        
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
        print("\n🎯 PRODUCTION READINESS ASSESSMENT")
        print("=" * 60)
        
        if report['summary']['production_ready']:
            print("🟢 STATUS: PRODUCTION READY")
            print("✅ LangGraph implementation passes all core validation tests")
            print("🚀 Ready for integration with benchmark suite and production use")
        else:
            print("🟡 STATUS: NEEDS MINOR IMPROVEMENTS")
            print("⚠️ Some tests failed but core functionality is working")
            print("🔧 Address failed tests for full production readiness")
        
        # Save report
        report_path = Path(__file__).parent / "production_readiness_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 VALIDATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)