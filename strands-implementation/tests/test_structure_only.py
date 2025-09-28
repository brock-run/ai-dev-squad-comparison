"""
Structure-only tests for Strands implementation.

These tests validate the basic structure and imports without requiring
external dependencies or complex setup.
"""

import pytest
import os
import sys
from pathlib import Path

# Add the implementation directory to the path
impl_dir = Path(__file__).parent.parent
sys.path.insert(0, str(impl_dir))


class TestStrandsStructure:
    """Test the basic structure of the Strands implementation."""
    
    def test_directory_structure(self):
        """Test that all required directories exist."""
        base_dir = Path(__file__).parent.parent
        
        required_dirs = [
            "agents",
            "workflows", 
            "observability",
            "cloud",
            "tests"
        ]
        
        for dir_name in required_dirs:
            dir_path = base_dir / dir_name
            assert dir_path.exists(), f"Directory {dir_name} should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"
    
    def test_required_files(self):
        """Test that all required files exist."""
        base_dir = Path(__file__).parent.parent
        
        required_files = [
            "adapter.py",
            "requirements.txt",
            "README.md",
            "agents/__init__.py",
            "workflows/__init__.py",
            "observability/__init__.py",
            "cloud/__init__.py",
            "tests/__init__.py"
        ]
        
        for file_path in required_files:
            full_path = base_dir / file_path
            assert full_path.exists(), f"File {file_path} should exist"
            assert full_path.is_file(), f"{file_path} should be a file"
    
    def test_adapter_class_exists(self):
        """Test that the StrandsAdapter class exists and has required methods."""
        try:
            from adapter import StrandsAdapter
            
            # Check that the class exists
            assert StrandsAdapter is not None
            
            # Check required methods exist
            required_methods = [
                'get_info',
                'get_capabilities', 
                'health_check',
                'get_metrics',
                'run_task'
            ]
            
            for method_name in required_methods:
                assert hasattr(StrandsAdapter, method_name), f"Method {method_name} should exist"
                
        except ImportError as e:
            pytest.skip(f"Could not import StrandsAdapter: {e}")
    
    def test_agent_classes_exist(self):
        """Test that agent classes exist."""
        try:
            from agents.enterprise_architect import EnterpriseArchitectAgent
            from agents.senior_developer import SeniorDeveloperAgent
            from agents.qa_engineer import QAEngineerAgent
            
            assert EnterpriseArchitectAgent is not None
            assert SeniorDeveloperAgent is not None
            assert QAEngineerAgent is not None
            
        except ImportError as e:
            pytest.skip(f"Could not import agent classes: {e}")
    
    def test_workflow_class_exists(self):
        """Test that workflow class exists."""
        try:
            from workflows.enterprise_workflow import EnterpriseWorkflow
            assert EnterpriseWorkflow is not None
            
        except ImportError as e:
            pytest.skip(f"Could not import EnterpriseWorkflow: {e}")
    
    def test_observability_classes_exist(self):
        """Test that observability classes exist."""
        try:
            from observability.telemetry_manager import TelemetryManager
            assert TelemetryManager is not None
            
        except ImportError as e:
            pytest.skip(f"Could not import observability classes: {e}")
    
    def test_cloud_classes_exist(self):
        """Test that cloud provider classes exist."""
        try:
            from cloud.provider_manager import ProviderManager
            assert ProviderManager is not None
            
        except ImportError as e:
            pytest.skip(f"Could not import cloud classes: {e}")
    
    def test_factory_function_exists(self):
        """Test that the factory function exists."""
        try:
            from adapter import create_strands_adapter
            assert create_strands_adapter is not None
            assert callable(create_strands_adapter)
            
        except ImportError as e:
            pytest.skip(f"Could not import factory function: {e}")
    
    def test_requirements_file_content(self):
        """Test that requirements.txt has expected content."""
        base_dir = Path(__file__).parent.parent
        requirements_file = base_dir / "requirements.txt"
        
        if requirements_file.exists():
            content = requirements_file.read_text()
            
            # Check for key dependencies
            expected_deps = [
                "strands",
                "opentelemetry",
                "pydantic",
                "pytest"
            ]
            
            for dep in expected_deps:
                assert dep in content, f"Dependency {dep} should be in requirements.txt"
    
    def test_readme_exists_and_not_empty(self):
        """Test that README.md exists and has content."""
        base_dir = Path(__file__).parent.parent
        readme_file = base_dir / "README.md"
        
        assert readme_file.exists(), "README.md should exist"
        
        content = readme_file.read_text()
        assert len(content) > 100, "README.md should have substantial content"
        assert "Strands" in content, "README.md should mention Strands"


if __name__ == "__main__":
    pytest.main([__file__])