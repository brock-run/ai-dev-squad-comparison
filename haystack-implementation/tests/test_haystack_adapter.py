"""
Comprehensive tests for Haystack Adapter implementation.

Tests cover RAG functionality, pipeline execution, agent coordination,
safety controls, and integration with the common agent API.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the adapter
from adapter import HaystackAdapter, HaystackAdapterError, SafePipelineWrapper, MockRAGAgent

# Import common types
try:
    from common.agent_api import TaskSchema, TaskStatus, RunResult
    from common.safety.policy import SecurityPolicy
    from common.safety.injection import ThreatLevel, InjectionDetection
except ImportError:
    # Mock the imports if not available
    class TaskSchema:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class TaskStatus:
        COMPLETED = "completed"
        FAILED = "failed"
        IN_PROGRESS = "in_progress"
    
    class RunResult:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class SecurityPolicy:
        pass
    
    class ThreatLevel:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    class InjectionDetection:
        def __init__(self, threat_level, description):
            self.threat_level = threat_level
            self.description = description


class TestHaystackAdapter:
    """Test suite for HaystackAdapter."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'haystack': {
                'model': 'gpt-3.5-turbo'
            },
            'github': {
                'enabled': False
            },
            'gitlab': {
                'enabled': False
            },
            'language': 'python'
        }
    
    @pytest.fixture
    def adapter(self, mock_config):
        """Create adapter instance for testing."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}, clear=False):
            return HaystackAdapter(config=mock_config)
    
    @pytest.fixture
    def sample_task(self):
        """Sample task for testing."""
        return TaskSchema(
            id="test-task-123",
            type="code_generation",
            inputs={
                "description": "Create a simple calculator function",
                "requirements": [
                    "Support basic arithmetic operations",
                    "Handle division by zero",
                    "Return numeric results"
                ]
            },
            repo_path="/test/repo",
            vcs_provider="github",
            mode="autonomous",
            seed=42,
            model_prefs={},
            timeout_seconds=300,
            resource_limits={},
            metadata={}
        )
    
    def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.name == "Haystack RAG Development Squad"
        assert adapter.version == "2.0.0"
        assert "RAG-enhanced" in adapter.description
        assert len(adapter.agents) == 3
        assert "research" in adapter.agents
        assert "architect" in adapter.agents
        assert "developer" in adapter.agents
    
    def test_adapter_initialization_without_haystack(self, mock_config):
        """Test adapter initialization when Haystack is not available."""
        with patch('adapter.HAYSTACK_AVAILABLE', False):
            adapter = HaystackAdapter(config=mock_config)
            assert adapter.document_store is None
            assert len(adapter.pipelines) == 0
    
    @pytest.mark.asyncio
    async def test_get_info(self, adapter):
        """Test get_info method."""
        info = await adapter.get_info()
        
        assert info["name"] == "Haystack RAG Development Squad"
        assert info["version"] == "2.0.0"
        assert info["framework"] == "haystack"
        assert "capabilities" in info
        assert "rag_features" in info
        assert "agents" in info
        assert "safety" in info
        assert len(info["capabilities"]) > 0
        assert len(info["supported_tasks"]) > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health check functionality."""
        health = await adapter.health_check()
        
        assert "status" in health
        assert "timestamp" in health
        assert "framework" in health
        assert "components" in health
        assert health["framework"] == "haystack"
        
        # Check component health
        components = health["components"]
        assert "haystack" in components
        assert "agents" in components
        assert "document_store" in components
        assert "pipelines" in components
        assert "safety" in components
        assert "vcs" in components
        assert "api_keys" in components
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, adapter):
        """Test metrics collection."""
        metrics = await adapter.get_metrics()
        
        assert "framework" in metrics
        assert "uptime_seconds" in metrics
        assert "tasks" in metrics
        assert "rag" in metrics
        assert "safety" in metrics
        assert "agents" in metrics
        assert "pipelines" in metrics
        
        assert metrics["framework"] == "haystack"
        assert metrics["tasks"]["success_rate"] >= 0
        assert metrics["agents"]["count"] == 3
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, adapter):
        """Test input sanitization with injection guard."""
        # Mock injection guard
        mock_guard = Mock()
        mock_guard.detect_injection.return_value = InjectionDetection(
            ThreatLevel.LOW, "Safe input"
        )
        adapter.injection_guard = mock_guard
        
        # Test safe input
        safe_input = await adapter._sanitize_input("normal text")
        assert safe_input == "normal text"
        
        # Test dangerous input
        mock_guard.detect_injection.return_value = InjectionDetection(
            ThreatLevel.HIGH, "Potential injection"
        )
        
        with pytest.raises(ValueError, match="Input failed safety check"):
            await adapter._sanitize_input("malicious input")
    
    @pytest.mark.asyncio
    async def test_task_validation(self, adapter, sample_task):
        """Test task validation and sanitization."""
        # Mock injection guard for safe validation
        mock_guard = Mock()
        mock_guard.detect_injection.return_value = InjectionDetection(
            ThreatLevel.LOW, "Safe input"
        )
        adapter.injection_guard = mock_guard
        
        validated_task = await adapter._validate_task(sample_task)
        
        assert validated_task.id == sample_task.id
        assert validated_task.type == sample_task.type
        assert validated_task.inputs["description"] == sample_task.inputs["description"]
        assert len(validated_task.inputs["requirements"]) == len(sample_task.inputs["requirements"])
    
    @pytest.mark.asyncio
    async def test_rag_workflow_execution(self, adapter):
        """Test RAG workflow execution."""
        # Mock the pipeline execution
        with patch.object(adapter, '_research_phase', return_value="Research complete"):
            with patch.object(adapter, '_architecture_phase', return_value="Architecture complete"):
                with patch.object(adapter, '_implementation_phase', return_value="Implementation complete"):
                    with patch.object(adapter, '_validation_phase', return_value="Validation complete"):
                        
                        result = await adapter._execute_rag_workflow(
                            "Test task", ["Requirement 1", "Requirement 2"]
                        )
                        
                        assert result["success"] is True
                        assert "research" in result
                        assert "architecture" in result
                        assert "implementation" in result
                        assert "validation" in result
                        assert result["agents_used"] == list(adapter.agents.keys())
    
    @pytest.mark.asyncio
    async def test_fallback_workflow(self, adapter):
        """Test fallback workflow when RAG is unavailable."""
        result = adapter._run_fallback_workflow(
            "Test task", ["Requirement 1", "Requirement 2"]
        )
        
        assert "task" in result
        assert "requirements" in result
        assert "research" in result
        assert "architecture" in result
        assert "implementation" in result
        assert "validation" in result
        assert result["fallback"] is True
    
    @pytest.mark.asyncio
    async def test_run_task_success(self, adapter, sample_task):
        """Test successful task execution."""
        # Mock the RAG workflow
        mock_result = {
            "task": "Test task",
            "success": True,
            "fallback": False,
            "agents_used": ["research", "architect", "developer"],
            "rag_queries": 2,
            "document_retrievals": 5
        }
        
        with patch.object(adapter, '_execute_rag_workflow', return_value=mock_result):
            with patch.object(adapter, '_validate_task', return_value=sample_task):
                
                results = []
                async for result in adapter.run_task(sample_task):
                    results.append(result)
                
                assert len(results) == 1
                result = results[0]
                assert result.task_id == sample_task.id
                assert result.status == TaskStatus.COMPLETED
                assert result.error is None
                assert result.result == mock_result
                assert "framework" in result.metadata
                assert result.metadata["framework"] == "haystack"
    
    @pytest.mark.asyncio
    async def test_run_task_failure(self, adapter, sample_task):
        """Test task execution failure."""
        # Mock validation to raise an exception
        with patch.object(adapter, '_validate_task', side_effect=ValueError("Validation failed")):
            
            results = []
            async for result in adapter.run_task(sample_task):
                results.append(result)
            
            assert len(results) == 1
            result = results[0]
            assert result.task_id == sample_task.id
            assert result.status == TaskStatus.FAILED
            assert result.error == "Validation failed"
            assert result.result is None
    
    @pytest.mark.asyncio
    async def test_research_phase(self, adapter):
        """Test research phase execution."""
        # Mock pipeline execution
        mock_pipeline = Mock()
        mock_pipeline.run_safe = AsyncMock(return_value={
            'llm': {'replies': ['Research results']},
            'retriever': {'documents': [Mock(), Mock()]}
        })
        adapter.safe_pipelines['research'] = mock_pipeline
        
        result = await adapter._research_phase("Test task", ["Requirement 1"])
        
        assert "Research results" in result
        assert adapter.metrics['rag_queries'] > 0
        assert adapter.metrics['document_retrievals'] > 0
    
    @pytest.mark.asyncio
    async def test_implementation_phase(self, adapter):
        """Test implementation phase execution."""
        # Mock pipeline execution
        mock_pipeline = Mock()
        mock_pipeline.run_safe = AsyncMock(return_value={
            'llm': {'replies': ['Implementation code']},
            'retriever': {'documents': [Mock(), Mock(), Mock()]}
        })
        adapter.safe_pipelines['implementation'] = mock_pipeline
        
        result = await adapter._implementation_phase("Test task", ["Requirement 1"], "Architecture")
        
        assert "Implementation code" in result
        assert adapter.metrics['rag_queries'] > 0
        assert adapter.metrics['document_retrievals'] > 0
    
    def test_generate_fallback_implementation(self, adapter):
        """Test fallback implementation generation."""
        implementation = adapter._generate_fallback_implementation("Test Calculator")
        
        assert "Test Calculator" in implementation
        assert "def main():" in implementation
        assert "if __name__ == \"__main__\":" in implementation
        assert "Haystack RAG" in implementation


class TestSafePipelineWrapper:
    """Test suite for SafePipelineWrapper."""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Mock Haystack pipeline."""
        pipeline = Mock()
        pipeline.run.return_value = {"output": "test result"}
        return pipeline
    
    @pytest.fixture
    def mock_policy(self):
        """Mock security policy."""
        policy = Mock()
        policy.execution.enabled = True
        return policy
    
    @pytest.fixture
    def wrapper(self, mock_pipeline, mock_policy):
        """Create SafePipelineWrapper for testing."""
        return SafePipelineWrapper(mock_pipeline, mock_policy)
    
    @pytest.mark.asyncio
    async def test_safe_execution(self, wrapper):
        """Test safe pipeline execution."""
        inputs = {"query": "test query"}
        result = await wrapper.run_safe(inputs)
        
        assert result == {"output": "test result"}
        assert wrapper.execution_count == 1
    
    @pytest.mark.asyncio
    async def test_injection_detection(self, wrapper):
        """Test injection detection in pipeline wrapper."""
        # Mock injection guard
        mock_guard = Mock()
        mock_guard.detect_injection.return_value = InjectionDetection(
            ThreatLevel.HIGH, "Malicious input detected"
        )
        wrapper.injection_guard = mock_guard
        
        inputs = {"query": "malicious query"}
        
        with pytest.raises(ValueError, match="Input 'query' failed safety check"):
            await wrapper.run_safe(inputs)


class TestMockRAGAgent:
    """Test suite for MockRAGAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create MockRAGAgent for testing."""
        return MockRAGAgent("Test Agent", "Test description")
    
    @pytest.mark.asyncio
    async def test_research(self, agent):
        """Test mock research functionality."""
        result = await agent.research("Test task", ["Requirement 1", "Requirement 2"])
        
        assert "Research Results" in result
        assert "Test task" in result
        assert "Requirement 1" in result
        assert "Requirement 2" in result
        assert "Test Agent" in result
    
    @pytest.mark.asyncio
    async def test_design_architecture(self, agent):
        """Test mock architecture design."""
        research = "Research data"
        result = await agent.design_architecture("Test task", ["Req 1"], research)
        
        assert "Architecture Design" in result
        assert "Test task" in result
        assert "Research data" in result[:300]  # Should include truncated research
        assert "Test Agent" in result
    
    @pytest.mark.asyncio
    async def test_implement(self, agent):
        """Test mock implementation."""
        result = await agent.implement("Test task", ["Req 1"], "Architecture")
        
        assert "Implementation" in result
        assert "Test task" in result
        assert "def main():" in result
        assert "Test Agent" in result


class TestIntegration:
    """Integration tests for Haystack adapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter for integration testing."""
        config = {
            'haystack': {'model': 'gpt-3.5-turbo'},
            'language': 'python'
        }
        return HaystackAdapter(config=config)
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, adapter):
        """Test complete end-to-end workflow."""
        task = TaskSchema(
            id="integration-test",
            type="code_generation",
            inputs={
                "description": "Create a simple function",
                "requirements": ["Return a greeting message"]
            },
            repo_path="/test",
            vcs_provider="github",
            mode="autonomous",
            seed=42,
            model_prefs={},
            timeout_seconds=300,
            resource_limits={},
            metadata={}
        )
        
        # Execute task
        results = []
        async for result in adapter.run_task(task):
            results.append(result)
        
        assert len(results) == 1
        result = results[0]
        assert result.task_id == "integration-test"
        assert result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        
        # Check metrics were updated
        metrics = await adapter.get_metrics()
        assert metrics["tasks"]["completed"] + metrics["tasks"]["failed"] > 0
    
    @pytest.mark.asyncio
    async def test_health_and_metrics_integration(self, adapter):
        """Test health check and metrics integration."""
        # Get initial health
        health = await adapter.health_check()
        assert health["status"] in ["healthy", "degraded"]
        
        # Get initial metrics
        metrics = await adapter.get_metrics()
        assert "framework" in metrics
        assert metrics["framework"] == "haystack"
        
        # Verify consistency
        assert health["components"]["agents"]["count"] == metrics["agents"]["count"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])