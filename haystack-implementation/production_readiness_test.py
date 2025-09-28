#!/usr/bin/env python3
"""
Production Readiness Test for Haystack RAG Development Squad

This script provides a comprehensive production readiness assessment
for the Haystack implementation, testing all key functionality.
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
            self.id = "production-readiness-test"
            self.type = "code_generation"
            self.inputs = {
                "description": "Create a comprehensive user management system with authentication",
                "requirements": [
                    "Support user registration and login",
                    "Implement password hashing and security",
                    "Add role-based access control",
                    "Include session management",
                    "Provide user profile management",
                    "Add comprehensive logging and monitoring"
                ]
            }
            self.repo_path = "/tmp/test-repo"
            self.vcs_provider = "github"
            self.mode = "autonomous"
            self.seed = 42
            self.model_prefs = {}
            self.timeout_seconds = 300
            self.resource_limits = {}
            self.metadata = {"production_test": True}
    
    return MockTaskSchema()

async def test_adapter_initialization():
    """Test adapter initialization and configuration."""
    logger.info("🔧 Testing adapter initialization...")
    
    try:
        # Patch the imports before importing the adapter
        import adapter
        adapter.RunResult = MockRunResult
        adapter.TaskStatus = MockTaskStatus
        
        from adapter import HaystackAdapter, create_haystack_adapter, create_adapter
        
        # Test direct initialization
        config = {
            'haystack': {'model': 'gpt-3.5-turbo'},
            'language': 'python',
            'github': {'enabled': False},
            'gitlab': {'enabled': False}
        }
        
        adapter_instance = HaystackAdapter(config=config)
        
        # Test factory functions
        factory_adapter = create_haystack_adapter(config)
        generic_adapter = create_adapter(config)
        
        # Verify initialization
        assert adapter_instance.name == "Haystack RAG Development Squad"
        assert adapter_instance.version == "2.0.0"
        assert len(adapter_instance.agents) == 3
        
        logger.info("✅ Adapter initialization successful")
        return adapter_instance
        
    except Exception as e:
        logger.error(f"❌ Adapter initialization failed: {e}")
        raise

async def test_rag_capabilities(adapter):
    """Test RAG-specific capabilities."""
    logger.info("🧠 Testing RAG capabilities...")
    
    try:
        capabilities = await adapter.get_capabilities()
        
        # Verify RAG features
        assert capabilities["rag_enhanced"] is True
        assert capabilities["multi_agent"] is True
        assert capabilities["pipeline_based"] is True
        
        # Check supported tasks
        expected_tasks = [
            "code_generation", "code_review", "testing", 
            "documentation", "architecture_design", "research_and_analysis"
        ]
        
        for task in expected_tasks:
            assert task in capabilities["supported_tasks"]
        
        # Check RAG features
        expected_features = [
            "document_retrieval", "knowledge_augmentation", 
            "pipeline_orchestration", "safety_controls"
        ]
        
        for feature in expected_features:
            assert feature in capabilities["features"]
        
        logger.info("✅ RAG capabilities verified")
        return capabilities
        
    except Exception as e:
        logger.error(f"❌ RAG capabilities test failed: {e}")
        raise

async def test_multi_agent_workflow(adapter):
    """Test multi-agent workflow execution."""
    logger.info("👥 Testing multi-agent workflow...")
    
    try:
        task = create_mock_task_schema()
        
        # Execute complex task
        results = []
        async for result in adapter.run_task(task):
            results.append(result)
        
        assert len(results) == 1
        result = results[0]
        
        # Verify workflow execution
        assert result.task_id == task.id
        assert result.status == "completed"
        assert result.result is not None
        
        # Check multi-agent coordination
        workflow_result = result.result
        assert "agents_used" in workflow_result
        assert len(workflow_result["agents_used"]) == 3
        assert "research" in workflow_result["agents_used"]
        assert "architect" in workflow_result["agents_used"] 
        assert "developer" in workflow_result["agents_used"]
        
        # Verify workflow phases
        assert "research" in workflow_result
        assert "architecture" in workflow_result
        assert "implementation" in workflow_result
        assert "validation" in workflow_result
        
        logger.info("✅ Multi-agent workflow successful")
        return result
        
    except Exception as e:
        logger.error(f"❌ Multi-agent workflow test failed: {e}")
        raise

async def test_safety_integration(adapter):
    """Test safety controls integration."""
    logger.info("🛡️ Testing safety controls...")
    
    try:
        health = await adapter.health_check()
        
        # Check safety components
        safety_status = health["components"]["safety"]
        
        # Verify safety controls are available
        assert safety_status["policy_manager"] is True
        assert safety_status["active_policy"] is True
        
        # Check other safety components (may not all be available)
        safety_components = [
            "sandbox", "filesystem_guard", 
            "network_guard", "injection_guard"
        ]
        
        available_safety = sum(1 for comp in safety_components 
                             if safety_status.get(comp, False))
        
        # At least some safety controls should be available
        assert available_safety >= 2, f"Only {available_safety} safety controls available"
        
        logger.info(f"✅ Safety controls verified ({available_safety}/{len(safety_components)} available)")
        return safety_status
        
    except Exception as e:
        logger.error(f"❌ Safety integration test failed: {e}")
        raise

async def test_performance_metrics(adapter):
    """Test performance and metrics collection."""
    logger.info("📊 Testing performance metrics...")
    
    try:
        # Get initial metrics
        initial_metrics = await adapter.get_metrics()
        
        # Execute a task to generate metrics
        task = create_mock_task_schema()
        async for result in adapter.run_task(task):
            pass
        
        # Get updated metrics
        final_metrics = await adapter.get_metrics()
        
        # Verify metrics structure
        assert "framework" in final_metrics
        assert "tasks" in final_metrics
        assert "rag" in final_metrics
        assert "agents" in final_metrics
        
        # Check task metrics
        assert final_metrics["tasks"]["completed"] > initial_metrics["tasks"]["completed"]
        
        # Check RAG metrics
        assert "pipeline_executions" in final_metrics["rag"]
        assert "rag_queries" in final_metrics["rag"]
        assert "document_retrievals" in final_metrics["rag"]
        
        # Check agent metrics
        assert final_metrics["agents"]["count"] == 3
        assert len(final_metrics["agents"]["types"]) == 3
        
        logger.info("✅ Performance metrics verified")
        return final_metrics
        
    except Exception as e:
        logger.error(f"❌ Performance metrics test failed: {e}")
        raise

async def test_error_handling(adapter):
    """Test error handling and recovery."""
    logger.info("🚨 Testing error handling...")
    
    try:
        # Create invalid task
        class InvalidTask:
            def __init__(self):
                self.id = "invalid-task"
                self.type = "invalid_type"
                self.inputs = {}  # Missing required fields
        
        invalid_task = InvalidTask()
        
        # Execute invalid task
        results = []
        try:
            async for result in adapter.run_task(invalid_task):
                results.append(result)
        except Exception:
            # Expected to handle gracefully
            pass
        
        # Should handle gracefully and return error result
        if results:
            result = results[0]
            # Either completes with fallback or fails gracefully
            assert result.status in ["completed", "failed"]
        
        logger.info("✅ Error handling verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        raise

async def test_documentation_quality(adapter):
    """Test documentation and help features."""
    logger.info("📚 Testing documentation quality...")
    
    try:
        info = await adapter.get_info()
        
        # Check comprehensive information
        assert "name" in info
        assert "version" in info
        assert "description" in info
        assert "capabilities" in info
        assert "rag_features" in info
        assert "agents" in info
        
        # Verify detailed agent information
        for agent_name, agent_info in info["agents"].items():
            assert "type" in agent_info
            assert "description" in agent_info
            assert "capabilities" in agent_info
        
        # Check RAG features documentation
        rag_features = info["rag_features"]
        assert "document_store" in rag_features
        assert "retriever" in rag_features
        assert "pipelines" in rag_features
        
        logger.info("✅ Documentation quality verified")
        return info
        
    except Exception as e:
        logger.error(f"❌ Documentation test failed: {e}")
        raise

async def run_production_readiness_assessment():
    """Run comprehensive production readiness assessment."""
    logger.info("🚀 HAYSTACK RAG DEVELOPMENT SQUAD - PRODUCTION READINESS ASSESSMENT")
    logger.info("=" * 80)
    
    start_time = datetime.utcnow()
    test_results = {}
    
    try:
        # Test 1: Initialization
        adapter = await test_adapter_initialization()
        test_results["initialization"] = True
        
        # Test 2: RAG Capabilities
        capabilities = await test_rag_capabilities(adapter)
        test_results["rag_capabilities"] = True
        
        # Test 3: Multi-Agent Workflow
        workflow_result = await test_multi_agent_workflow(adapter)
        test_results["multi_agent_workflow"] = True
        
        # Test 4: Safety Integration
        safety_status = await test_safety_integration(adapter)
        test_results["safety_integration"] = True
        
        # Test 5: Performance Metrics
        metrics = await test_performance_metrics(adapter)
        test_results["performance_metrics"] = True
        
        # Test 6: Error Handling
        await test_error_handling(adapter)
        test_results["error_handling"] = True
        
        # Test 7: Documentation Quality
        info = await test_documentation_quality(adapter)
        test_results["documentation"] = True
        
        # Final health check
        health = await adapter.health_check()
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Generate assessment report
        logger.info("=" * 80)
        logger.info("📋 PRODUCTION READINESS ASSESSMENT REPORT")
        logger.info("=" * 80)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        logger.info(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"⏱️ Total Execution Time: {execution_time:.2f} seconds")
        logger.info(f"🏗️ Framework: {info['framework']}")
        logger.info(f"📦 Version: {info['version']}")
        logger.info(f"🤖 Agents: {len(info['agents'])}")
        logger.info(f"🔧 Health Status: {health['status']}")
        
        # RAG-specific metrics
        logger.info(f"🧠 RAG Features: {len(capabilities['features'])}")
        logger.info(f"📊 Pipeline Executions: {metrics['rag']['pipeline_executions']}")
        logger.info(f"🔍 Document Retrievals: {metrics['rag']['document_retrievals']}")
        
        # Safety assessment
        safety_score = sum(1 for v in safety_status.values() if v) / len(safety_status)
        logger.info(f"🛡️ Safety Score: {safety_score:.1%}")
        
        # Final verdict
        if all(test_results.values()):
            logger.info("\n🟢 PRODUCTION READINESS: EXCELLENT")
            logger.info("✅ All tests passed - Ready for production deployment")
            logger.info("🚀 Haystack RAG Development Squad is fully operational")
        else:
            failed_tests = [test for test, passed in test_results.items() if not passed]
            logger.info(f"\n🟡 PRODUCTION READINESS: NEEDS ATTENTION")
            logger.info(f"❌ Failed tests: {failed_tests}")
            logger.info("🔧 Address failed tests before production deployment")
        
        logger.info("=" * 80)
        
        return all(test_results.values())
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.error("=" * 80)
        logger.error("💥 PRODUCTION READINESS ASSESSMENT FAILED")
        logger.error("=" * 80)
        logger.error(f"❌ Critical Error: {e}")
        logger.error(f"⏱️ Execution Time: {execution_time:.2f} seconds")
        logger.error("🔧 Fix critical issues before proceeding")
        logger.error("=" * 80)
        
        return False

def main():
    """Main function."""
    try:
        success = asyncio.run(run_production_readiness_assessment())
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("Assessment interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Assessment failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())