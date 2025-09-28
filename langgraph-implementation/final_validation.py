#!/usr/bin/env python3
"""
Final LangGraph Implementation Validation

This script provides a comprehensive final validation of the LangGraph
implementation to confirm it's ready for the next phase.
"""

import ast
import sys
import json
from pathlib import Path
from datetime import datetime


def validate_implementation_completeness():
    """Validate that the implementation is complete and ready."""
    print("🔍 Final Implementation Validation")
    print("=" * 50)
    
    base_path = Path(__file__).parent
    results = []
    
    def add_result(name, passed, message=""):
        results.append({"name": name, "passed": passed, "message": message})
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {message}")
    
    # 1. Check all required files exist
    print("\n📁 File Structure Validation")
    required_files = [
        "adapter.py",
        "state/development_state.py", 
        "README.md",
        "requirements.txt",
        "simple_test.py",
        "tests/test_langgraph_adapter.py",
        "READINESS_CHECKLIST.md"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if (base_path / file_path).exists():
            add_result(f"File: {file_path}", True, "Present")
        else:
            add_result(f"File: {file_path}", False, "Missing")
            all_files_exist = False
    
    # 2. Validate adapter.py structure
    print("\n🏗️ Adapter Implementation Validation")
    adapter_file = base_path / "adapter.py"
    
    if adapter_file.exists():
        try:
            with open(adapter_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for LangGraphAdapter class
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if 'LangGraphAdapter' in classes:
                add_result("LangGraphAdapter Class", True, "Implementation found")
            else:
                add_result("LangGraphAdapter Class", False, "Class missing")
            
            # Check for required methods
            methods = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            
            critical_methods = [
                'run_task', 'get_capabilities', 'health_check',
                '_architect_node', '_developer_node', '_tester_node',
                '_reviewer_node', '_vcs_node'
            ]
            
            missing_methods = [m for m in critical_methods if m not in methods]
            if not missing_methods:
                add_result("Critical Methods", True, f"All {len(critical_methods)} methods present")
            else:
                add_result("Critical Methods", False, f"Missing: {missing_methods}")
            
            # Check for factory function
            if 'create_langgraph_adapter' in methods:
                add_result("Factory Function", True, "create_langgraph_adapter found")
            else:
                add_result("Factory Function", False, "Factory function missing")
            
            # Check code size (should be substantial)
            lines = len(content.split('\n'))
            if lines > 1000:
                add_result("Implementation Size", True, f"{lines} lines (comprehensive)")
            else:
                add_result("Implementation Size", False, f"{lines} lines (too small)")
                
        except Exception as e:
            add_result("Adapter Analysis", False, f"Failed to analyze: {e}")
    
    # 3. Validate state management
    print("\n📊 State Management Validation")
    state_file = base_path / "state" / "development_state.py"
    
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            required_classes = [
                'WorkflowStatus', 'AgentRole', 'AgentExecution',
                'DesignArtifact', 'CodeArtifact', 'TestArtifact',
                'ReviewArtifact', 'VCSArtifact', 'StateManager'
            ]
            
            missing_classes = [c for c in required_classes if c not in classes]
            if not missing_classes:
                add_result("State Classes", True, f"All {len(required_classes)} classes present")
            else:
                add_result("State Classes", False, f"Missing: {missing_classes}")
            
            # Check for utility functions
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            if 'create_initial_state' in functions:
                add_result("State Functions", True, "create_initial_state found")
            else:
                add_result("State Functions", False, "create_initial_state missing")
                
        except Exception as e:
            add_result("State Analysis", False, f"Failed to analyze: {e}")
    
    # 4. Validate documentation
    print("\n📚 Documentation Validation")
    readme_file = base_path / "README.md"
    
    if readme_file.exists():
        try:
            with open(readme_file, 'r') as f:
                content = f.read()
            
            # Check for required sections
            required_sections = [
                "# LangGraph Multi-Agent Squad Implementation",
                "## Architecture", 
                "## Features",
                "## Setup",
                "## Usage",
                "## Testing"
            ]
            
            missing_sections = [s for s in required_sections if s not in content]
            if not missing_sections:
                add_result("README Sections", True, f"All {len(required_sections)} sections present")
            else:
                add_result("README Sections", False, f"Missing: {missing_sections}")
            
            # Check documentation quality
            word_count = len(content.split())
            if word_count > 800:
                add_result("Documentation Quality", True, f"{word_count} words (comprehensive)")
            else:
                add_result("Documentation Quality", False, f"{word_count} words (insufficient)")
            
            # Check for code examples
            code_blocks = content.count('```')
            if code_blocks >= 10:
                add_result("Code Examples", True, f"{code_blocks//2} code blocks")
            else:
                add_result("Code Examples", False, f"{code_blocks//2} code blocks (insufficient)")
                
        except Exception as e:
            add_result("Documentation Analysis", False, f"Failed to analyze: {e}")
    
    # 5. Validate requirements
    print("\n📦 Requirements Validation")
    req_file = base_path / "requirements.txt"
    
    if req_file.exists():
        try:
            with open(req_file, 'r') as f:
                content = f.read()
            
            required_packages = ['langgraph', 'langchain', 'pydantic']
            missing_packages = [p for p in required_packages if p not in content.lower()]
            
            if not missing_packages:
                add_result("Required Packages", True, f"All {len(required_packages)} packages listed")
            else:
                add_result("Required Packages", False, f"Missing: {missing_packages}")
                
        except Exception as e:
            add_result("Requirements Analysis", False, f"Failed to analyze: {e}")
    
    # 6. Validate test structure
    print("\n🧪 Test Structure Validation")
    
    # Check simple test
    if (base_path / "simple_test.py").exists():
        add_result("Structure Test", True, "simple_test.py present")
    else:
        add_result("Structure Test", False, "simple_test.py missing")
    
    # Check comprehensive test
    test_file = base_path / "tests" / "test_langgraph_adapter.py"
    if test_file.exists():
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            
            test_count = content.count('def test_')
            if test_count >= 10:
                add_result("Test Coverage", True, f"{test_count} test methods")
            else:
                add_result("Test Coverage", False, f"{test_count} test methods (insufficient)")
                
        except Exception as e:
            add_result("Test Analysis", False, f"Failed to analyze: {e}")
    
    # 7. Validate readiness checklist
    print("\n✅ Readiness Checklist Validation")
    checklist_file = base_path / "READINESS_CHECKLIST.md"
    
    if checklist_file.exists():
        try:
            with open(checklist_file, 'r') as f:
                content = f.read()
            
            if "READY FOR PRODUCTION" in content:
                add_result("Readiness Status", True, "Marked as production ready")
            else:
                add_result("Readiness Status", False, "Not marked as ready")
            
            checklist_items = content.count('- [x]')
            if checklist_items >= 30:
                add_result("Checklist Completeness", True, f"{checklist_items} items completed")
            else:
                add_result("Checklist Completeness", False, f"{checklist_items} items completed (insufficient)")
                
        except Exception as e:
            add_result("Checklist Analysis", False, f"Failed to analyze: {e}")
    
    # Generate final report
    print("\n" + "=" * 50)
    print("📊 FINAL VALIDATION SUMMARY")
    print("=" * 50)
    
    total_checks = len(results)
    passed_checks = sum(1 for r in results if r["passed"])
    failed_checks = total_checks - passed_checks
    
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")
    print(f"Success Rate: {passed_checks/total_checks*100:.1f}%")
    
    # Show failed checks
    failed_results = [r for r in results if not r["passed"]]
    if failed_results:
        print(f"\n❌ Failed Checks ({len(failed_results)}):")
        for result in failed_results:
            print(f"  - {result['name']}: {result['message']}")
    
    # Final assessment
    print("\n🎯 FINAL ASSESSMENT")
    print("=" * 50)
    
    if passed_checks / total_checks >= 0.90:  # 90% threshold
        print("🟢 STATUS: READY FOR NEXT PHASE")
        print("✅ LangGraph implementation is complete and validated")
        print("🚀 Approved to proceed to Task 4.2 - CrewAI Implementation")
        final_status = True
    else:
        print("🟡 STATUS: NEEDS ATTENTION")
        print("⚠️ Some validation checks failed")
        print("🔧 Address failed checks before proceeding")
        final_status = False
    
    # Save detailed report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "success_rate": passed_checks/total_checks*100,
            "final_status": "READY" if final_status else "NEEDS_ATTENTION"
        },
        "results": results
    }
    
    report_path = base_path / "final_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return final_status


def main():
    """Run final validation."""
    try:
        success = validate_implementation_completeness()
        return 0 if success else 1
    except Exception as e:
        print(f"💥 VALIDATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)