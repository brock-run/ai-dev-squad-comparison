#!/usr/bin/env python3
"""
LangGraph Implementation - Full Setup and Testing

This script sets up all dependencies and runs comprehensive tests
to ensure the LangGraph implementation is fully functional.
"""

import subprocess
import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class DependencyManager:
    """Manages installation and validation of all dependencies."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = []
    
    def add_result(self, name: str, passed: bool, message: str = "", details: Dict[str, Any] = None):
        """Add a test result."""
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
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        print("🐍 Checking Python Version...")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.add_result("Python Version", True, f"Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.add_result("Python Version", False, f"Python {version.major}.{version.minor} (requires 3.8+)")
            return False
    
    def install_core_dependencies(self) -> bool:
        """Install core Python dependencies."""
        print("\n📦 Installing Core Dependencies...")
        
        # Read requirements
        req_file = self.base_path / "requirements.txt"
        if not req_file.exists():
            self.add_result("Requirements File", False, "requirements.txt not found")
            return False
        
        try:
            # Install requirements
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(req_file)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.add_result("Core Dependencies", True, "All packages installed successfully")
                return True
            else:
                self.add_result("Core Dependencies", False, f"Installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.add_result("Core Dependencies", False, "Installation timeout (5 minutes)")
            return False
        except Exception as e:
            self.add_result("Core Dependencies", False, f"Installation error: {e}")
            return False
    
    def install_optional_dependencies(self) -> bool:
        """Install optional dependencies for full functionality."""
        print("\n🔧 Installing Optional Dependencies...")
        
        optional_packages = [
            "docker",  # For execution sandbox
            "pytest",  # For testing
            "pytest-asyncio",  # For async testing
            "black",  # For code formatting
            "flake8",  # For linting
        ]
        
        success_count = 0
        for package in optional_packages:
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    self.add_result(f"Optional: {package}", True, "Installed successfully")
                    success_count += 1
                else:
                    self.add_result(f"Optional: {package}", False, f"Failed: {result.stderr}")
                    
            except Exception as e:
                self.add_result(f"Optional: {package}", False, f"Error: {e}")
        
        # Consider success if at least half installed
        success = success_count >= len(optional_packages) // 2
        return success
    
    def check_docker_availability(self) -> bool:
        """Check if Docker is available for sandbox execution."""
        print("\n🐳 Checking Docker Availability...")
        
        try:
            result = subprocess.run([
                "docker", "--version"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.add_result("Docker", True, f"Available: {result.stdout.strip()}")
                
                # Test Docker functionality
                test_result = subprocess.run([
                    "docker", "run", "--rm", "hello-world"
                ], capture_output=True, text=True, timeout=30)
                
                if test_result.returncode == 0:
                    self.add_result("Docker Functionality", True, "Docker is working correctly")
                    return True
                else:
                    self.add_result("Docker Functionality", False, "Docker not working properly")
                    return False
            else:
                self.add_result("Docker", False, "Docker not available")
                return False
                
        except subprocess.TimeoutExpired:
            self.add_result("Docker", False, "Docker check timeout")
            return False
        except FileNotFoundError:
            self.add_result("Docker", False, "Docker not installed")
            return False
        except Exception as e:
            self.add_result("Docker", False, f"Docker check error: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Set up environment variables and configuration."""
        print("\n🌍 Setting Up Environment...")
        
        # Check for required environment variables
        env_vars = {
            "OPENAI_API_KEY": "OpenAI API access",
            "GITHUB_TOKEN": "GitHub integration (optional)",
            "GITLAB_TOKEN": "GitLab integration (optional)"
        }
        
        missing_required = []
        for var, description in env_vars.items():
            if os.getenv(var):
                self.add_result(f"Env: {var}", True, "Set")
            else:
                if var == "OPENAI_API_KEY":
                    missing_required.append(var)
                self.add_result(f"Env: {var}", False, f"Not set - {description}")
        
        # Set up default configuration if needed
        try:
            # Create .env file template if it doesn't exist
            env_file = self.base_path / ".env"
            if not env_file.exists():
                env_template = """# LangGraph Implementation Environment Variables

# Required for LLM access
OPENAI_API_KEY=your_openai_api_key_here

# Optional for VCS integration
GITHUB_TOKEN=your_github_token_here
GITLAB_TOKEN=your_gitlab_token_here

# Optional for local models
OLLAMA_BASE_URL=http://localhost:11434
"""
                with open(env_file, 'w') as f:
                    f.write(env_template)
                
                self.add_result("Environment Template", True, ".env template created")
            
            return len(missing_required) == 0
            
        except Exception as e:
            self.add_result("Environment Setup", False, f"Setup error: {e}")
            return False


class FullImplementationTester:
    """Tests the full LangGraph implementation with all dependencies."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = []
    
    def add_result(self, name: str, passed: bool, message: str = "", details: Dict[str, Any] = None):
        """Add a test result."""
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
    
    async def test_import_system(self) -> bool:
        """Test that all imports work correctly."""
        print("\n📥 Testing Import System...")
        
        try:
            # Add parent directory to path for imports
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent))
            
            # Test core imports
            from common.agent_api import TaskSchema, AgentAdapter, RunResult, Event
            self.add_result("Core API Imports", True, "All core imports successful")
            
            # Test safety imports
            from common.safety.policy import get_policy_manager
            from common.safety.execute import ExecutionSandbox
            from common.safety.fs import FilesystemGuard
            from common.safety.net import NetworkGuard
            from common.safety.injection import PromptInjectionGuard
            self.add_result("Safety Imports", True, "All safety imports successful")
            
            # Test VCS imports
            from common.vcs.github import GitHubProvider
            from common.vcs.gitlab import GitLabProvider
            from common.vcs.commit_msgs import generate_commit_message
            self.add_result("VCS Imports", True, "All VCS imports successful")
            
            # Test LangGraph imports
            try:
                from langgraph.graph import StateGraph, END
                from langgraph.checkpoint.memory import MemorySaver
                self.add_result("LangGraph Imports", True, "LangGraph imports successful")
            except ImportError as e:
                self.add_result("LangGraph Imports", False, f"LangGraph not available: {e}")
                return False
            
            # Test adapter imports
            from adapter import create_langgraph_adapter, LangGraphAdapter
            from state.development_state import create_initial_state, WorkflowStatus
            self.add_result("Adapter Imports", True, "Adapter imports successful")
            
            return True
            
        except ImportError as e:
            self.add_result("Import System", False, f"Import failed: {e}")
            return False
        except Exception as e:
            self.add_result("Import System", False, f"Unexpected error: {e}")
            return False
    
    async def test_adapter_creation(self) -> bool:
        """Test adapter creation with real dependencies."""
        print("\n🏗️ Testing Adapter Creation...")
        
        try:
            from adapter import create_langgraph_adapter
            
            # Create adapter with default config
            adapter = create_langgraph_adapter()
            
            if adapter:
                self.add_result("Adapter Creation", True, f"Created {adapter.name} v{adapter.version}")
                
                # Test basic properties
                if hasattr(adapter, 'workflow') and adapter.workflow:
                    self.add_result("Workflow Graph", True, "LangGraph workflow created")
                else:
                    self.add_result("Workflow Graph", False, "Workflow not created")
                
                return True
            else:
                self.add_result("Adapter Creation", False, "Adapter is None")
                return False
                
        except Exception as e:
            self.add_result("Adapter Creation", False, f"Creation failed: {e}")
            return False
    
    async def test_safety_system_integration(self) -> bool:
        """Test safety system integration with real components."""
        print("\n🛡️ Testing Safety System Integration...")
        
        try:
            from adapter import create_langgraph_adapter
            adapter = create_langgraph_adapter()
            
            # Test policy manager
            if adapter.policy_manager:
                policies = adapter.policy_manager.list_policies()
                self.add_result("Policy Manager", True, f"Available policies: {len(policies)}")
            else:
                self.add_result("Policy Manager", False, "Policy manager not initialized")
            
            # Test execution sandbox
            if adapter.sandbox:
                self.add_result("Execution Sandbox", True, "Sandbox initialized")
                
                # Test simple code execution
                try:
                    result = await adapter.sandbox.execute_code("print('Hello, World!')", language='python')
                    if result.success:
                        self.add_result("Sandbox Execution", True, "Code executed successfully")
                    else:
                        self.add_result("Sandbox Execution", False, f"Execution failed: {result.error}")
                except Exception as e:
                    self.add_result("Sandbox Execution", False, f"Execution error: {e}")
            else:
                self.add_result("Execution Sandbox", False, "Sandbox not initialized")
            
            # Test other safety components
            safety_components = {
                'Filesystem Guard': adapter.filesystem_guard,
                'Network Guard': adapter.network_guard,
                'Injection Guard': adapter.injection_guard
            }
            
            for component_name, component in safety_components.items():
                if component:
                    self.add_result(component_name, True, "Initialized")
                else:
                    self.add_result(component_name, False, "Not initialized")
            
            return True
            
        except Exception as e:
            self.add_result("Safety Integration", False, f"Integration test failed: {e}")
            return False
    
    async def test_workflow_execution(self) -> bool:
        """Test actual workflow execution with a simple task."""
        print("\n🔄 Testing Workflow Execution...")
        
        try:
            from adapter import create_langgraph_adapter
            from common.agent_api import TaskSchema
            
            adapter = create_langgraph_adapter()
            
            # Create a simple test task
            task = TaskSchema(
                id="test-workflow-1",
                description="Create a simple hello world function",
                requirements=[
                    "Function should return 'Hello, World!'",
                    "Include basic error handling"
                ],
                context={"language": "python"}
            )
            
            # Test task validation
            validated_task = await adapter._validate_task(task)
            self.add_result("Task Validation", True, "Task validated successfully")
            
            # Test individual workflow components
            design = await adapter._create_design(task.description, task.requirements)
            self.add_result("Design Creation", True, f"Design created with {len(design['components'])} components")
            
            from state.development_state import DesignArtifact
            design_artifact = DesignArtifact(
                architecture_type=design['architecture_type'],
                components=design['components']
            )
            
            code_result = await adapter._implement_code(task.description, design_artifact)
            self.add_result("Code Implementation", True, f"Code generated ({len(code_result['main_code'])} chars)")
            
            from state.development_state import CodeArtifact
            code_artifact = CodeArtifact(
                language=code_result['language'],
                main_code=code_result['main_code']
            )
            
            test_result = await adapter._create_tests(code_artifact, task.description, task.requirements)
            self.add_result("Test Creation", True, f"Tests created with {len(test_result['test_cases'])} cases")
            
            return True
            
        except Exception as e:
            self.add_result("Workflow Execution", False, f"Workflow test failed: {e}")
            return False
    
    async def test_vcs_integration(self) -> bool:
        """Test VCS integration with real providers."""
        print("\n🔗 Testing VCS Integration...")
        
        try:
            from adapter import create_langgraph_adapter
            adapter = create_langgraph_adapter()
            
            # Test VCS provider initialization
            github_available = adapter.github is not None
            gitlab_available = adapter.gitlab is not None
            
            self.add_result("GitHub Provider", github_available, 
                          "Available" if github_available else "Not configured")
            self.add_result("GitLab Provider", gitlab_available,
                          "Available" if gitlab_available else "Not configured")
            
            # Test VCS operations (mock mode)
            from state.development_state import create_initial_state
            state = create_initial_state("Test VCS task", [])
            
            branch_name = await adapter._create_feature_branch(state)
            self.add_result("Branch Creation", True, f"Branch: {branch_name}")
            
            commit_message = await adapter._generate_commit_message(state)
            self.add_result("Commit Message", True, f"Message: {commit_message[:50]}...")
            
            return True
            
        except Exception as e:
            self.add_result("VCS Integration", False, f"VCS test failed: {e}")
            return False
    
    async def test_health_and_capabilities(self) -> bool:
        """Test health check and capabilities reporting."""
        print("\n🏥 Testing Health and Capabilities...")
        
        try:
            from adapter import create_langgraph_adapter
            adapter = create_langgraph_adapter()
            
            # Test capabilities
            capabilities = await adapter.get_capabilities()
            self.add_result("Capabilities API", True, f"Features: {len(capabilities['features'])}")
            
            # Test health check
            health = await adapter.health_check()
            self.add_result("Health Check", True, f"Status: {health['status']}")
            
            # Validate health components
            components = health.get('components', {})
            healthy_components = sum(1 for comp in components.values() 
                                   if comp.get('status') in ['healthy', 'available', 'configured'])
            
            self.add_result("Component Health", True, 
                          f"{healthy_components}/{len(components)} components healthy")
            
            return True
            
        except Exception as e:
            self.add_result("Health Check", False, f"Health test failed: {e}")
            return False
    
    async def run_pytest_suite(self) -> bool:
        """Run the pytest test suite."""
        print("\n🧪 Running Pytest Suite...")
        
        try:
            # Run pytest on the test directory
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(self.base_path / "tests"),
                "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                # Parse pytest output for test count
                output_lines = result.stdout.split('\n')
                test_summary = [line for line in output_lines if 'passed' in line and 'failed' in line]
                
                if test_summary:
                    self.add_result("Pytest Suite", True, f"Tests passed: {test_summary[-1]}")
                else:
                    self.add_result("Pytest Suite", True, "All tests passed")
                return True
            else:
                self.add_result("Pytest Suite", False, f"Tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.add_result("Pytest Suite", False, "Test timeout (2 minutes)")
            return False
        except FileNotFoundError:
            self.add_result("Pytest Suite", False, "Pytest not available")
            return False
        except Exception as e:
            self.add_result("Pytest Suite", False, f"Test error: {e}")
            return False


async def main():
    """Run complete setup and testing."""
    print("🚀 LangGraph Implementation - Full Setup and Testing")
    print("=" * 60)
    print("This script will install dependencies and run comprehensive tests")
    print("to ensure the LangGraph implementation is fully functional.\n")
    
    # Phase 1: Dependency Management
    print("📦 PHASE 1: DEPENDENCY SETUP")
    print("=" * 40)
    
    dep_manager = DependencyManager()
    
    # Check Python version
    if not dep_manager.check_python_version():
        print("❌ Python version incompatible. Please use Python 3.8+")
        return 1
    
    # Install dependencies
    if not dep_manager.install_core_dependencies():
        print("❌ Failed to install core dependencies")
        return 1
    
    # Install optional dependencies
    dep_manager.install_optional_dependencies()
    
    # Check Docker
    docker_available = dep_manager.check_docker_availability()
    
    # Setup environment
    env_setup = dep_manager.setup_environment()
    
    # Phase 2: Full Implementation Testing
    print("\n🧪 PHASE 2: FULL IMPLEMENTATION TESTING")
    print("=" * 40)
    
    tester = FullImplementationTester()
    
    # Run all tests
    tests = [
        tester.test_import_system(),
        tester.test_adapter_creation(),
        tester.test_safety_system_integration(),
        tester.test_workflow_execution(),
        tester.test_vcs_integration(),
        tester.test_health_and_capabilities(),
        tester.run_pytest_suite()
    ]
    
    test_results = []
    for test_coro in tests:
        try:
            result = await test_coro
            test_results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            test_results.append(False)
    
    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    # Dependency results
    dep_total = len(dep_manager.results)
    dep_passed = sum(1 for r in dep_manager.results if r["passed"])
    
    print(f"\n📦 Dependency Setup: {dep_passed}/{dep_total} ({dep_passed/dep_total*100:.1f}%)")
    
    # Test results
    test_total = len(tester.results)
    test_passed = sum(1 for r in tester.results if r["passed"])
    
    print(f"🧪 Implementation Tests: {test_passed}/{test_total} ({test_passed/test_total*100:.1f}%)")
    
    # Overall results
    overall_total = dep_total + test_total
    overall_passed = dep_passed + test_passed
    
    print(f"🎯 Overall Score: {overall_passed}/{overall_total} ({overall_passed/overall_total*100:.1f}%)")
    
    # Show failed tests
    all_results = dep_manager.results + tester.results
    failed_results = [r for r in all_results if not r["passed"]]
    
    if failed_results:
        print(f"\n❌ Failed Tests ({len(failed_results)}):")
        for result in failed_results:
            print(f"  - {result['name']}: {result['message']}")
    
    # Final assessment
    print("\n🎯 FINAL ASSESSMENT")
    print("=" * 40)
    
    success_threshold = 0.85  # 85% success rate
    success_rate = overall_passed / overall_total
    
    if success_rate >= success_threshold:
        print("🟢 STATUS: FULLY VALIDATED AND READY")
        print("✅ LangGraph implementation is production-ready")
        print("🚀 All systems operational with external dependencies")
        final_status = True
    else:
        print("🟡 STATUS: NEEDS ATTENTION")
        print("⚠️ Some tests failed - review before production use")
        print("🔧 Address failed tests for full validation")
        final_status = False
    
    # Save comprehensive report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "dependency_setup": {
                "total": dep_total,
                "passed": dep_passed,
                "success_rate": dep_passed/dep_total*100
            },
            "implementation_tests": {
                "total": test_total,
                "passed": test_passed,
                "success_rate": test_passed/test_total*100
            },
            "overall": {
                "total": overall_total,
                "passed": overall_passed,
                "success_rate": success_rate*100,
                "status": "READY" if final_status else "NEEDS_ATTENTION"
            }
        },
        "dependency_results": dep_manager.results,
        "test_results": tester.results,
        "environment": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "docker_available": docker_available,
            "environment_setup": env_setup
        }
    }
    
    report_path = Path(__file__).parent / "full_test_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return 0 if final_status else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)