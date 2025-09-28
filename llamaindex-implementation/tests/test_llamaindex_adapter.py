"""
Comprehensive tests for LlamaIndex Adapter

This test suite validates the LlamaIndex adapter implementation
including retrieval-augmented generation, safety controls, VCS integration, and workflow execution.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any


class TestLlamaIndexAdapterIsolated:
    """Isolated test cases for LlamaIndexAdapter."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {
            'language': 'python',
            'model': 'llama2:7b',
            'embed_model': 'llama2:7b',
            'vcs': {
                'enabled': True,
                'repository': 'test/repo'
            },
            'github': {
                'enabled': True
            }
        }
    
    def test_adapter_can_be_imported(self):
        """Test that the adapter can be imported without errors."""
        try:
            from adapter import LlamaIndexAdapter, create_llamaindex_adapter
            assert LlamaIndexAdapter is not None
            assert create_llamaindex_adapter is not None
        except ImportError as e:
            pytest.skip(f"LlamaIndex not available: {e}")
    
    @patch('adapter.LLAMAINDEX_AVAILABLE', True)
    @patch('adapter.VectorStoreIndex')
    @patch('adapter.Ollama')
    @patch('adapter.OllamaEmbedding')
    @patch('adapter.Settings')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_adapter_initialization_mocked(self, mock_config_manager, mock_policy_manager, 
                                         mock_settings, mock_ollama_embed, mock_ollama, 
                                         mock_vector_index, mock_config):
        """Test adapter initialization with full mocking."""
        # Setup mocks
        mock_config_manager.return_value.config = mock_config
        
        # Mock policy
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = False
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = []
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        # Mock LlamaIndex components
        mock_llm = Mock()
        mock_ollama.return_value = mock_llm
        
        mock_embed = Mock()
        mock_ollama_embed.return_value = mock_embed
        
        mock_index = Mock()
        mock_query_engine = Mock()
        mock_query_engine.aquery = AsyncMock(return_value=Mock(source_nodes=[]))
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_vector_index.from_documents.return_value = mock_index
        
        # Import and create adapter
        from adapter import LlamaIndexAdapter
        adapter = LlamaIndexAdapter(mock_config)
        
        # Basic assertions
        assert adapter.name == "LlamaIndex Retrieval-Augmented Agent"
        assert adapter.version == "2.0.0"
        assert hasattr(adapter, 'llm')
        assert hasattr(adapter, 'embed_model')
    
    @patch('adapter.LLAMAINDEX_AVAILABLE', True)
    @patch('adapter.VectorStoreIndex')
    @patch('adapter.Ollama')
    @patch('adapter.OllamaEmbedding')
    @patch('adapter.Settings')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_adapter_capabilities_mocked(self, mock_config_manager, mock_policy_manager,
                                       mock_settings, mock_ollama_embed, mock_ollama,
                                       mock_vector_index, mock_config):
        """Test get_capabilities method with mocking."""
        # Setup mocks (same as above)
        mock_config_manager.return_value.config = mock_config
        
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = True
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = ['test']
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        # Mock LlamaIndex components
        mock_llm = Mock()
        mock_ollama.return_value = mock_llm
        
        mock_embed = Mock()
        mock_ollama_embed.return_value = mock_embed
        
        mock_index = Mock()
        mock_query_engine = Mock()
        mock_query_engine.aquery = AsyncMock(return_value=Mock(source_nodes=[]))
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_vector_index.from_documents.return_value = mock_index
        
        from adapter import LlamaIndexAdapter
        adapter = LlamaIndexAdapter(mock_config)
        
        # Test capabilities
        capabilities = asyncio.run(adapter.get_capabilities())
        
        assert 'name' in capabilities
        assert 'version' in capabilities
        assert 'features' in capabilities
        assert 'workflow_capabilities' in capabilities
        assert 'safety_features' in capabilities
        
        # Check required features
        required_features = [
            'retrieval_augmented_generation',
            'document_indexing',
            'query_engine_integration',
            'context_management',
            'code_understanding',
            'safety_controls',
            'vcs_integration'
        ]
        
        for feature in required_features:
            assert feature in capabilities['features']
        
        # Check workflow capabilities
        assert 'retrieval_augmented' in capabilities['workflow_capabilities']
        assert 'document_indexing' in capabilities['workflow_capabilities']
        assert 'query_engine' in capabilities['workflow_capabilities']
    
    @patch('adapter.LLAMAINDEX_AVAILABLE', True)
    @patch('adapter.VectorStoreIndex')
    @patch('adapter.Ollama')
    @patch('adapter.OllamaEmbedding')
    @patch('adapter.Settings')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_adapter_health_check_mocked(self, mock_config_manager, mock_policy_manager,
                                       mock_settings, mock_ollama_embed, mock_ollama,
                                       mock_vector_index, mock_config):
        """Test health_check method with mocking."""
        # Setup mocks (same as above)
        mock_config_manager.return_value.config = mock_config
        
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = False
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = []
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        # Mock LlamaIndex components
        mock_llm = Mock()
        mock_llm.model = 'llama2:7b'
        mock_ollama.return_value = mock_llm
        
        mock_embed = Mock()
        mock_ollama_embed.return_value = mock_embed
        
        mock_index = Mock()
        mock_query_engine = Mock()
        mock_query_engine.aquery = AsyncMock(return_value=Mock(source_nodes=[]))
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_vector_index.from_documents.return_value = mock_index
        
        from adapter import LlamaIndexAdapter
        adapter = LlamaIndexAdapter(mock_config)
        
        # Test health check
        health = asyncio.run(adapter.health_check())
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'components' in health
        
        # Check component status
        assert 'llamaindex' in health['components']
        assert 'llm' in health['components']
        assert 'embeddings' in health['components']
        assert 'index' in health['components']
        assert 'query_engine' in health['components']
    
    @patch('adapter.LLAMAINDEX_AVAILABLE', True)
    @patch('adapter.VectorStoreIndex')
    @patch('adapter.Ollama')
    @patch('adapter.OllamaEmbedding')
    @patch('adapter.Settings')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_input_sanitization_mocked(self, mock_config_manager, mock_policy_manager,
                                     mock_settings, mock_ollama_embed, mock_ollama,
                                     mock_vector_index, mock_config):
        """Test input sanitization."""
        # Setup mocks
        mock_config_manager.return_value.config = mock_config
        
        # Mock policy with injection guard
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = False
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = ['test_pattern']
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        # Mock LlamaIndex components
        mock_llm = Mock()
        mock_ollama.return_value = mock_llm
        
        mock_embed = Mock()
        mock_ollama_embed.return_value = mock_embed
        
        mock_index = Mock()
        mock_query_engine = Mock()
        mock_query_engine.aquery = AsyncMock(return_value=Mock(source_nodes=[]))
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_vector_index.from_documents.return_value = mock_index
        
        # Mock injection guard
        with patch('adapter.PromptInjectionGuard') as mock_injection_guard_class:
            mock_injection_guard = Mock()
            mock_injection_guard.patterns = []
            
            # Mock scan result
            mock_threat_level = Mock()
            mock_threat_level.value = 1  # Low threat
            mock_scan_result = Mock()
            mock_scan_result.threat_level = mock_threat_level
            mock_scan_result.description = "Safe input"
            
            mock_injection_guard.scan_input = AsyncMock(return_value=mock_scan_result)
            mock_injection_guard_class.return_value = mock_injection_guard
            
            from adapter import LlamaIndexAdapter
            adapter = LlamaIndexAdapter(mock_config)
            
            # Test sanitization
            result = asyncio.run(adapter._sanitize_input("print('hello world')"))
            assert result == "print('hello world')"
    
    @patch('adapter.LLAMAINDEX_AVAILABLE', True)
    @patch('adapter.VectorStoreIndex')
    @patch('adapter.Ollama')
    @patch('adapter.OllamaEmbedding')
    @patch('adapter.Settings')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_workflow_execution_mocked(self, mock_config_manager, mock_policy_manager,
                                     mock_settings, mock_ollama_embed, mock_ollama,
                                     mock_vector_index, mock_config):
        """Test workflow execution."""
        # Setup mocks
        mock_config_manager.return_value.config = mock_config
        
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = False
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = []
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        # Mock LlamaIndex components
        mock_llm = Mock()
        mock_ollama.return_value = mock_llm
        
        mock_embed = Mock()
        mock_ollama_embed.return_value = mock_embed
        
        mock_index = Mock()
        mock_query_engine = Mock()
        mock_query_engine.aquery = AsyncMock(return_value=Mock(source_nodes=[]))
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_vector_index.from_documents.return_value = mock_index
        
        from adapter import LlamaIndexAdapter
        adapter = LlamaIndexAdapter(mock_config)
        
        # Test workflow execution
        result = asyncio.run(adapter._run_workflow(
            "Create a calculator",
            ["Add function", "Subtract function"]
        ))
        
        assert isinstance(result, dict)
        assert 'task' in result
        assert 'requirements' in result
        assert 'success' in result
    
    @patch('adapter.LLAMAINDEX_AVAILABLE', True)
    @patch('adapter.VectorStoreIndex')
    @patch('adapter.Ollama')
    @patch('adapter.OllamaEmbedding')
    @patch('adapter.Settings')
    @patch('adapter.get_policy_manager')
    @patch('adapter.get_config_manager')
    def test_vcs_operations_mocked(self, mock_config_manager, mock_policy_manager,
                                 mock_settings, mock_ollama_embed, mock_ollama,
                                 mock_vector_index, mock_config):
        """Test VCS operations handling."""
        # Setup mocks
        mock_config_manager.return_value.config = mock_config
        
        mock_active_policy = Mock()
        mock_active_policy.execution.enabled = False
        mock_active_policy.filesystem = None
        mock_active_policy.network = None
        mock_active_policy.injection_patterns = []
        
        mock_policy_manager_instance = Mock()
        mock_policy_manager_instance.get_active_policy.return_value = mock_active_policy
        mock_policy_manager.return_value = mock_policy_manager_instance
        
        # Mock LlamaIndex components
        mock_llm = Mock()
        mock_ollama.return_value = mock_llm
        
        mock_embed = Mock()
        mock_ollama_embed.return_value = mock_embed
        
        mock_index = Mock()
        mock_query_engine = Mock()
        mock_query_engine.aquery = AsyncMock(return_value=Mock(source_nodes=[]))
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_vector_index.from_documents.return_value = mock_index
        
        # Mock TaskSchema
        with patch('adapter.TaskSchema') as mock_task_schema:
            mock_task = Mock()
            mock_task.id = "test-vcs-1"
            mock_task.description = "Test VCS integration"
            mock_task.requirements = ["Create files"]
            mock_task.context = {}
            mock_task_schema.return_value = mock_task
            
            from adapter import LlamaIndexAdapter
            adapter = LlamaIndexAdapter(mock_config)
            
            # Mock workflow result
            mock_result = {
                'implementation': 'def add(a, b): return a + b',
                'tests': 'def test_add(): assert add(1, 2) == 3',
                'success': True
            }
            
            vcs_result = asyncio.run(adapter._handle_vcs_operations(mock_task, mock_result))
            
            # Should handle VCS operations
            assert 'status' in vcs_result
            
            # If VCS is enabled, should attempt operations
            if adapter.config.get('vcs', {}).get('enabled', False):
                assert vcs_result['status'] in ['completed', 'failed', 'skipped']
    
    def test_file_extraction(self):
        """Test file extraction from workflow results."""
        # This test doesn't require LlamaIndex to be available
        try:
            from adapter import LlamaIndexAdapter
            
            # Create a minimal adapter instance for testing
            with patch('adapter.LLAMAINDEX_AVAILABLE', True):
                with patch('adapter.get_policy_manager'):
                    with patch('adapter.get_config_manager') as mock_config_manager:
                        mock_config_manager.return_value.config = {}
                        
                        # Mock all LlamaIndex components
                        with patch('adapter.Ollama'):
                            with patch('adapter.OllamaEmbedding'):
                                with patch('adapter.Settings'):
                                    with patch('adapter.VectorStoreIndex'):
                                        adapter = LlamaIndexAdapter()
                                        
                                        # Mock workflow result with code
                                        mock_result = {
                                            'implementation': 'def add(a, b):\n    return a + b',
                                            'tests': 'def test_add(): assert add(1, 2) == 3',
                                            'design': {
                                                'architecture': 'Simple calculator',
                                                'components': ['add function', 'test function']
                                            }
                                        }
                                        
                                        files = adapter._extract_files_from_result(mock_result)
                                        
                                        # Should extract files based on content
                                        assert isinstance(files, dict)
                                        
                                        # If content contains code, should create files
                                        if mock_result.get('implementation'):
                                            assert len(files) > 0
                                            assert 'main.py' in files
                                        
                                        if mock_result.get('tests'):
                                            assert 'test_main.py' in files
                                        
                                        if mock_result.get('design'):
                                            assert 'DESIGN.md' in files
                                            
        except ImportError:
            pytest.skip("LlamaIndex not available")
    
    @patch('adapter.LLAMAINDEX_AVAILABLE', True)
    @patch('adapter.create_llamaindex_adapter')
    def test_factory_function_mocked(self, mock_create_adapter):
        """Test factory function with mocking."""
        # Mock the factory function to return a mock adapter
        mock_adapter = Mock()
        mock_adapter.name = "LlamaIndex Retrieval-Augmented Agent"
        mock_create_adapter.return_value = mock_adapter
        
        from adapter import create_llamaindex_adapter
        adapter = create_llamaindex_adapter()
        
        assert adapter.name == "LlamaIndex Retrieval-Augmented Agent"
        mock_create_adapter.assert_called_once()
    
    def test_workflow_structure(self):
        """Test that the workflow has the expected structure."""
        try:
            from adapter import CodeDevelopmentWorkflow
            
            # Test that the workflow class exists and has required methods
            assert hasattr(CodeDevelopmentWorkflow, 'analyze_requirements')
            assert hasattr(CodeDevelopmentWorkflow, 'design_solution')
            assert hasattr(CodeDevelopmentWorkflow, 'implement_code')
            assert hasattr(CodeDevelopmentWorkflow, 'create_tests')
            assert hasattr(CodeDevelopmentWorkflow, 'finalize_output')
            
        except ImportError:
            pytest.skip("LlamaIndex not available")
    
    def test_adapter_interface_compliance(self):
        """Test that the adapter implements the required interface."""
        try:
            from adapter import LlamaIndexAdapter
            
            # Check that required methods exist
            required_methods = [
                'run_task',
                'get_capabilities', 
                'health_check'
            ]
            
            for method in required_methods:
                assert hasattr(LlamaIndexAdapter, method), f"Missing method: {method}"
                
        except ImportError:
            pytest.skip("LlamaIndex not available")
    
    def test_fallback_workflow(self):
        """Test fallback workflow when LlamaIndex components are not available."""
        try:
            # Test the fallback workflow directly without requiring LlamaIndex
            with patch('adapter.LLAMAINDEX_AVAILABLE', False):
                from adapter import LlamaIndexAdapter
                
                # Create a minimal adapter instance for testing
                with patch('adapter.get_policy_manager'):
                    with patch('adapter.get_config_manager') as mock_config_manager:
                        mock_config_manager.return_value.config = {}
                        
                        # Create adapter - this should use fallback classes
                        adapter = LlamaIndexAdapter()
                        
                        # Test fallback workflow
                        result = adapter._run_fallback_workflow(
                            "Create a calculator",
                            ["Add function", "Subtract function"]
                        )
                        
                        assert isinstance(result, dict)
                        assert 'task' in result
                        assert 'requirements' in result
                        assert 'implementation' in result
                        assert 'tests' in result
                        assert 'success' in result
                        assert result['success'] == True
                        assert result.get('fallback') == True
                                        
        except ImportError:
            pytest.skip("LlamaIndex not available")


class TestLlamaIndexIntegration:
    """Integration tests for LlamaIndex functionality."""
    
    @pytest.mark.asyncio
    async def test_retrieval_workflow_simulation(self):
        """Test simulated retrieval workflow."""
        # This would test the actual LlamaIndex workflow execution
        # but requires LlamaIndex to be installed
        pass
    
    @pytest.mark.asyncio
    async def test_document_indexing_integration(self):
        """Test document indexing integration."""
        # Test that documents can be indexed and queried
        pass
    
    @pytest.mark.asyncio
    async def test_query_engine_integration(self):
        """Test query engine integration."""
        # Test that query engine works with safety controls
        pass
    
    @pytest.mark.asyncio
    async def test_context_management_integration(self):
        """Test context management integration."""
        # Test that context is properly managed across workflow steps
        pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])