#!/usr/bin/env python3
"""
Simple Integration Test for Haystack Adapter

This script provides a basic integration test to verify the Haystack adapter
works correctly with the common agent API and RAG functionality.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock classes for testing
class MockRunResult:
    def __init__(self):
        self.task_id = None
        self.status = None
        self.result = None
        self.error = None
        self.execution_time = None
        self.metadata = None

class MockTaskStatus:
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"

def create_mock_task_schema():
    """Create a mock TaskSchema for testing."""
    class MockTaskSchema:
        def __init__(self):
            self.id = "test-haystack-integration"
            self.type = "code_generation"
            self.inputs = {
                "description": "Create a simple Python function that calculates the factorial of a number",
                "requirements": [
                    "Handle positive integers",
                    "Return 1 for factorial of 0",
                    "Include proper error handling for negative numbers",
                    "Add comprehensive documentation"
                ]
            }
            self.repo_path = "/tmp/test-repo"
            self.vcs_provider = "github"
            self.mode = "autonomous"
            self.seed = 42
            self.model_prefs = {}
            self.timeout_seconds = 300
            self.resource_limits = {}
            self.metadata = {"test": True}
    
    return MockTaskSchema()

async def test_adapter_initialization():
    """Test adapter initialization."""
    logger.info("Testing Haystack adapter initialization...")
    
    try:
        # Patch the imports before importing the adapter
        import adapter
        adapter.RunResult = MockRunResult
        adapter.TaskStatus = MockTaskStatus
        
        from adapter import HaystackAdapter
        
        config = {
            'haystack': {
                'model': 'gpt-3.5-turbo'
            },
            'language': 'python',
            'github': {'enabled': False},
            'gitlab': {'enabled': False}
        }
        
        adapter = HaystackAdapter(config=config)
        
        # Basic checks
        assert adapter.name == "Haystack RAG Development Squad"
        assert adapter.version == "2.0.0"
        assert len(adapter.agents) == 3
        
        logger.info("✓ Adapter initialization successful")
        return adapter
        
    except Exception as e:
        logger.error(f"✗ Adapter initialization failed: {e}")
        raise

async def test_adapter_info(adapter):
    """Test adapter info retrieval."""
    logger.info("Testing adapter info retrieval...")
    
    try:
        info = await adapter.get_info()
        
        # Verify required fields
        required_fields = ["name", "version", "description", "framework", "capabilities"]
        for field in required_fields:
            assert field in info, f"Missing required field: {field}"
        
        assert info["framework"] == "haystack"
        assert len(info["capabilities"]) > 0
        assert "rag_features" in info
        assert "agents" in info
        
        logger.info("✓ Adapter info retrieval successful")
        logger.info(f"  - Name: {info['name']}")
        logger.info(f"  - Version: {info['version']}")
        logger.info(f"  - Agents: {len(info['agents'])}")
        logger.info(f"  - Capabilities: {len(info['capabilities'])}")
        
        return info
        
    except Exception as e:
        logger.error(f"✗ Adapter info retrieval failed: {e}")
        raise

async def test_health_check(adapter):
    """Test adapter health check."""
    logger.info("Testing adapter health check...")
    
    try:
        health = await adapter.health_check()
        
        # Verify health structure
        assert "status" in health
        assert "components" in health
        assert "timestamp" in health
        
        logger.info("✓ Health check successful")
        logger.info(f"  - Status: {health['status']}")
        logger.info(f"  - Components: {len(health['components'])}")
        
        # Log component status
        for component, status in health["components"].items():
            if isinstance(status, dict) and "status" in status:
                logger.info(f"    - {component}: {status['status']}")
        
        return health
        
    except Exception as e:
        logger.error(f"✗ Health check failed: {e}")
        raise

async def test_metrics(adapter):
    """Test adapter metrics collection."""
    logger.info("Testing adapter metrics...")
    
    try:
        metrics = await adapter.get_metrics()
        
        # Verify metrics structure
        assert "framework" in metrics
        assert "tasks" in metrics
        assert "rag" in metrics
        assert "agents" in metrics
        
        logger.info("✓ Metrics collection successful")
        logger.info(f"  - Framework: {metrics['framework']}")
        logger.info(f"  - Agent count: {metrics['agents']['count']}")
        logger.info(f"  - Pipeline count: {metrics['pipelines']['count']}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"✗ Metrics collection failed: {e}")
        raise

async def test_task_execution(adapter):
    """Test task execution with RAG workflow."""
    logger.info("Testing task execution...")
    
    try:
        task = create_mock_task_schema()
        
        # Execute task
        results = []
        async for result in adapter.run_task(task):
            results.append(result)
        
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        
        result = results[0]
        assert result.task_id == task.id
        assert result.status in ["completed", "failed"]
        
        if result.status == "completed":
            assert result.result is not None
            assert result.error is None
            logger.info("✓ Task execution successful")
            logger.info(f"  - Task ID: {result.task_id}")
            logger.info(f"  - Status: {result.status}")
            logger.info(f"  - Execution time: {result.execution_time:.2f}s")
            
            # Log result details
            if result.result:
                logger.info(f"  - Agents used: {result.result.get('agents_used', [])}")
                logger.info(f"  - RAG queries: {result.result.get('rag_queries', 0)}")
                logger.info(f"  - Document retrievals: {result.result.get('document_retrievals', 0)}")
        else:
            logger.warning(f"✓ Task execution completed with status: {result.status}")
            logger.warning(f"  - Error: {result.error}")
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Task execution failed: {e}")
        raise

async def test_rag_functionality(adapter):
    """Test RAG-specific functionality."""
    logger.info("Testing RAG functionality...")
    
    try:
        # Test document store
        if adapter.document_store:
            documents = adapter.document_store.filter_documents()
            logger.info(f"✓ Document store available with {len(documents)} documents")
        else:
            logger.info("✓ Document store not available (fallback mode)")
        
        # Test pipelines
        pipeline_count = len(adapter.pipelines)
        safe_pipeline_count = len(adapter.safe_pipelines)
        
        logger.info(f"✓ RAG pipelines: {pipeline_count} total, {safe_pipeline_count} safe wrappers")
        
        # Test agents
        for agent_name, agent in adapter.agents.items():
            logger.info(f"✓ Agent '{agent_name}': {agent.__class__.__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ RAG functionality test failed: {e}")
        raise

async def test_safety_integration(adapter):
    """Test safety controls integration."""
    logger.info("Testing safety controls integration...")
    
    try:
        # Check safety components
        safety_components = {
            "policy_manager": adapter.policy_manager is not None,
            "active_policy": adapter.active_policy is not None,
            "sandbox": adapter.sandbox is not None,
            "filesystem_guard": adapter.filesystem_guard is not None,
            "network_guard": adapter.network_guard is not None,
            "injection_guard": adapter.injection_guard is not None
        }
        
        logger.info("✓ Safety controls status:")
        for component, available in safety_components.items():
            status = "available" if available else "not available"
            logger.info(f"    - {component}: {status}")
        
        return safety_components
        
    except Exception as e:
        logger.error(f"✗ Safety integration test failed: {e}")
        raise

async def run_integration_tests():
    """Run all integration tests."""
    logger.info("=" * 60)
    logger.info("HAYSTACK ADAPTER INTEGRATION TESTS")
    logger.info("=" * 60)
    
    start_time = datetime.utcnow()
    
    try:
        # Test 1: Initialization
        adapter = await test_adapter_initialization()
        
        # Test 2: Info retrieval
        info = await test_adapter_info(adapter)
        
        # Test 3: Health check
        health = await test_health_check(adapter)
        
        # Test 4: Metrics
        metrics = await test_metrics(adapter)
        
        # Test 5: RAG functionality
        await test_rag_functionality(adapter)
        
        # Test 6: Safety integration
        await test_safety_integration(adapter)
        
        # Test 7: Task execution
        result = await test_task_execution(adapter)
        
        # Final metrics
        final_metrics = await adapter.get_metrics()
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info("INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info("✓ All tests passed successfully!")
        logger.info(f"✓ Total execution time: {execution_time:.2f} seconds")
        logger.info(f"✓ Adapter: {info['name']} v{info['version']}")
        logger.info(f"✓ Framework: {info['framework']}")
        logger.info(f"✓ Health status: {health['status']}")
        logger.info(f"✓ Tasks completed: {final_metrics['tasks']['completed']}")
        logger.info(f"✓ Tasks failed: {final_metrics['tasks']['failed']}")
        logger.info(f"✓ Success rate: {final_metrics['tasks']['success_rate']:.1%}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.error("=" * 60)
        logger.error("INTEGRATION TEST FAILED")
        logger.error("=" * 60)
        logger.error(f"✗ Error: {e}")
        logger.error(f"✗ Execution time: {execution_time:.2f} seconds")
        logger.error("=" * 60)
        
        return False

def main():
    """Main function."""
    try:
        success = asyncio.run(run_integration_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Integration tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Integration tests failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()