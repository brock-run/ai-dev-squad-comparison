#!/usr/bin/env python3
"""
Haystack Implementation Validation Script

This script validates the structure and basic functionality of the Haystack
RAG Development Squad implementation.
"""

import os
import sys
from pathlib import Path

def validate_structure():
    """Validate the directory structure."""
    print("🔍 Validating Haystack implementation structure...")
    
    base_path = Path(__file__).parent
    
    # Required files and directories
    required_items = [
        "adapter.py",
        "requirements.txt", 
        "README.md",
        "COMPLETION_SUMMARY.md",
        "simple_integration_test.py",
        "agents/",
        "agents/rag_developer_agent.py",
        "agents/knowledge_architect_agent.py", 
        "agents/research_agent.py",
        "pipelines/",
        "pipelines/development_pipeline.py",
        "tests/",
        "tests/test_haystack_adapter.py"
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
        from adapter import HaystackAdapter
        
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
            if not hasattr(HaystackAdapter, method):
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
        from agents.rag_developer_agent import RAGDeveloperAgent
        from agents.knowledge_architect_agent import KnowledgeArchitectAgent
        from agents.research_agent import ResearchAgent
        
        # Check agent methods
        agents = [
            (RAGDeveloperAgent, ['implement']),
            (KnowledgeArchitectAgent, ['design_architecture']),
            (ResearchAgent, ['research'])
        ]
        
        for agent_class, required_methods in agents:
            for method in required_methods:
                if not hasattr(agent_class, method):
                    print(f"❌ {agent_class.__name__} missing method: {method}")
                    return False
        
        print("✅ All agent implementations valid")
        return True
        
    except Exception as e:
        print(f"❌ Agent validation failed: {e}")
        return False

def validate_pipelines():
    """Validate the pipeline implementations."""
    print("🔍 Validating pipeline implementations...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import pipeline
        from pipelines.development_pipeline import DevelopmentPipeline
        
        # Check pipeline methods
        required_methods = [
            'execute_research',
            'execute_implementation',
            'execute_review',
            'execute_testing'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(DevelopmentPipeline, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing pipeline methods: {missing_methods}")
            return False
        
        print("✅ Pipeline implementation valid")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline validation failed: {e}")
        return False

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
            "# Haystack RAG Development Squad",
            "## Overview",
            "## Features", 
            "## Setup",
            "## Usage"
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
        if word_count < 500:
            print(f"❌ Documentation too brief: {word_count} words")
            return False
        
        print(f"✅ Documentation complete ({word_count} words)")
        return True
        
    except Exception as e:
        print(f"❌ Documentation validation failed: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🚀 Haystack RAG Development Squad Validation")
    print("=" * 50)
    
    validations = [
        validate_structure,
        validate_adapter,
        validate_agents,
        validate_pipelines,
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
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if all(results):
        print("✅ All validations passed!")
        print("🚀 Haystack implementation is ready")
        return 0
    else:
        print("❌ Some validations failed")
        print("🔧 Please address the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())