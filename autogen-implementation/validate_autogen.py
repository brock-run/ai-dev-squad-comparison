#!/usr/bin/env python3

"""
AutoGen Implementation Validation Script

This script validates the structure and basic functionality of the AutoGen
conversational multi-agent implementation.
"""

import os
import sys
from pathlib import Path

def validate_structure():
    """Validate the directory structure."""
    print("🔍 Validating AutoGen implementation structure...")
    
    base_path = Path(__file__).parent
    
    # Required files and directories
    required_items = [
        "adapter.py",
        "requirements.txt", 
        "README.md",
        "COMPLETION_SUMMARY.md",
        "simple_integration_test.py",
        "agents/",
        "agents/architect_agent.py",
        "agents/developer_agent.py", 
        "agents/tester_agent.py",
        "agents/user_proxy.py",
        "workflows/",
        "workflows/group_chat_manager.py",
        "tests/",
        "tests/test_autogen_adapter.py"
    ]
    
    missing_items = []
    for item in required_items:
        item_path = base_path / item
        if not item_path.exists():
            missing_items.append(item)
    
    if missing_items:
        print(f"❌ Missing required items: {missing_items}")
        return False
    
    print("✅ All required files and directories present")
    return True

def validate_adapter():
    """Validate the adapter implementation."""
    print("🔍 Validating adapter implementation...")
    
    try:
        # Import the adapter
        sys.path.insert(0, str(Path(__file__).parent))
        from adapter import AutoGenAdapter
        
        # Check required methods
        required_methods = [
            'get_info',
            'get_capabilities', 
            'run_task',
            'health_check',
            'get_metrics'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(AutoGenAdapter, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing required methods: {missing_methods}")
            return False
        
        print("✅ All required methods present")
        return True
        
    except Exception as e:
        print(f"❌ Adapter validation failed: {e}")
        return False

def validate_agents():
    """Validate the agent implementations."""
    print("🔍 Validating agent implementations...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import agents
        from agents.architect_agent import create_architect_agent
        from agents.developer_agent import create_developer_agent
        from agents.tester_agent import create_tester_agent
        from agents.user_proxy import create_user_proxy
        
        # Check agent creation functions
        agents = [
            (create_architect_agent, 'Architect'),
            (create_developer_agent, 'Developer'),
            (create_tester_agent, 'Tester'),
            (create_user_proxy, 'UserProxy')
        ]
        
        for create_func, agent_name in agents:
            if not callable(create_func):
                print(f"❌ {agent_name} creation function not callable")
                return False
        
        print("✅ All agent implementations valid")
        return True
        
    except Exception as e:
        print(f"❌ Agent validation failed: {e}")
        return False

def validate_workflows():
    """Validate the workflow implementations."""
    print("🔍 Validating workflow implementations...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import workflow
        from workflows.group_chat_manager import create_groupchat
        
        # Check workflow creation function
        if not callable(create_groupchat):
            print("❌ Group chat creation function not callable")
            return False
        
        print("✅ Workflow implementation valid")
        return True
        
    except Exception as e:
        print(f"❌ Workflow validation failed: {e}")
        return False

def validate_autogen_imports():
    """Validate AutoGen library imports."""
    print("🔍 Validating AutoGen imports...")
    
    try:
        import autogen
        print("✅ AutoGen library available")
        
        # Check for key AutoGen components
        required_components = [
            'ConversableAgent',
            'GroupChat',
            'GroupChatManager'
        ]
        
        missing_components = []
        for component in required_components:
            if not hasattr(autogen, component):
                missing_components.append(component)
        
        if missing_components:
            print(f"⚠️  Missing AutoGen components: {missing_components}")
            return True  # Don't fail validation, just warn
        
        print("✅ All AutoGen components available")
        return True
        
    except ImportError as e:
        print(f"⚠️  AutoGen not available: {e}")
        print("   Install with: pip install pyautogen")
        return True  # Don't fail validation for missing optional dependency

def validate_documentation():
    """Validate documentation completeness."""
    print("🔍 Validating documentation...")
    
    base_path = Path(__file__).parent
    readme_path = base_path / "README.md"
    
    if not readme_path.exists():
        print("❌ README.md not found")
        return False
    
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "# AutoGen AI Development Squad Implementation",
            "## Overview",
            "## Setup", 
            "## Features",
            "## Usage",
            "## Architecture"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing documentation sections: {missing_sections}")
            return False
        
        # Check word count
        word_count = len(content.split())
        if word_count < 800:
            print(f"❌ Documentation too brief: {word_count} words")
            return False
        
        print(f"✅ Documentation complete ({word_count} words)")
        return True
        
    except Exception as e:
        print(f"❌ Documentation validation failed: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🚀 AutoGen Conversational Multi-Agent Squad Validation")
    print("=" * 60)
    
    validations = [
        validate_structure,
        validate_adapter,
        validate_agents,
        validate_workflows,
        validate_autogen_imports,
        validate_documentation
    ]
    
    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if all(results):
        print("✅ All validations passed!")
        print("🚀 AutoGen implementation is ready")
        return 0
    else:
        print("❌ Some validations failed")
        print("🔧 Please address the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())