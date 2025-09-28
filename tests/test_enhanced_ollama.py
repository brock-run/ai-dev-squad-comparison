#!/usr/bin/env python3
"""
Tests for Enhanced Ollama Integration

This test suite covers the new intelligent model routing, performance profiling,
and fallback capabilities.
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.ollama_integration import (
    TaskType,
    ModelCapability,
    TaskCharacteristics,
    ModelPerformance,
    ModelInfo,
    EnhancedOllamaManager,
    EnhancedAgentInterface,
    create_agent,
    get_model_recommendations,
    health_check_models
)

class TestTaskCharacteristics(unittest.TestCase):
    """Test task characteristic analysis."""
    
    def test_analyze_coding_prompt(self):
        """Test analysis of coding prompts."""
        prompt = "Write a Python function to calculate fibonacci numbers"
        characteristics = TaskCharacteristics.analyze_prompt(prompt)
        
        self.assertEqual(characteristics.task_type, TaskType.CODING)
        self.assertEqual(characteristics.complexity, "low")
        self.assertFalse(characteristics.requires_accuracy)
        self.assertFalse(characteristics.requires_speed)
    
    def test_analyze_complex_architecture_prompt(self):
        """Test analysis of complex architecture prompts."""
        prompt = """Design a comprehensive, scalable microservices architecture 
                   for a real-time chat application with advanced features"""
        characteristics = TaskCharacteristics.analyze_prompt(prompt)
        
        self.assertEqual(characteristics.task_type, TaskType.ARCHITECTURE)
        self.assertEqual(characteristics.complexity, "high")
        self.assertTrue(len(prompt) > 300)
    
    def test_analyze_testing_prompt(self):
        """Test analysis of testing prompts."""
        prompt = "Create accurate unit tests for the user authentication module"
        characteristics = TaskCharacteristics.analyze_prompt(prompt)
        
        self.assertEqual(characteristics.task_type, TaskType.TESTING)
        self.assertTrue(characteristics.requires_accuracy)
    
    def test_analyze_debugging_prompt(self):
        """Test analysis of debugging prompts."""
        prompt = "Debug this error: AttributeError in line 42"
        characteristics = TaskCharacteristics.analyze_prompt(prompt)
        
        self.assertEqual(characteristics.task_type, TaskType.DEBUGGING)

class TestModelPerformance(unittest.TestCase):
    """Test model performance tracking."""
    
    def test_model_performance_serialization(self):
        """Test serialization and deserialization of model performance."""
        performance = ModelPerformance(
            model_name="test_model",
            task_type=TaskType.CODING,
            avg_response_time=2.5,
            avg_tokens_per_second=25.0,
            success_rate=0.95,
            avg_quality_score=8.5,
            total_requests=100,
            last_updated=datetime.now()
        )
        
        # Test serialization
        data = performance.to_dict()
        self.assertIn('model_name', data)
        self.assertEqual(data['task_type'], TaskType.CODING.value)
        
        # Test deserialization
        restored = ModelPerformance.from_dict(data)
        self.assertEqual(restored.model_name, performance.model_name)
        self.assertEqual(restored.task_type, performance.task_type)
        self.assertEqual(restored.success_rate, performance.success_rate)

class TestModelInfo(unittest.TestCase):
    """Test model information handling."""
    
    def test_model_info_serialization(self):
        """Test serialization and deserialization of model info."""
        model_info = ModelInfo(
            name="test_model",
            size_gb=7.5,
            capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.SPEED],
            context_length=4096,
            is_available=True,
            health_status="healthy",
            last_health_check=datetime.now()
        )
        
        # Test serialization
        data = model_info.to_dict()
        self.assertIn('capabilities', data)
        self.assertEqual(len(data['capabilities']), 2)
        
        # Test deserialization
        restored = ModelInfo.from_dict(data)
        self.assertEqual(restored.name, model_info.name)
        self.assertEqual(len(restored.capabilities), 2)
        self.assertIn(ModelCapability.CODE_GENERATION, restored.capabilities)

class TestEnhancedOllamaManager(unittest.TestCase):
    """Test enhanced Ollama manager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        self.performance_path = os.path.join(self.temp_dir, "test_performance.json")
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('common.ollama_integration.OllamaClient')
    def test_manager_initialization(self, mock_client_class):
        """Test manager initialization with mocked client."""
        mock_client = Mock()
        mock_client.list_models.return_value = [
            {"name": "llama3.1:8b"},
            {"name": "codellama:13b"}
        ]
        mock_client.get_model_info.return_value = {"size": 8000000000}
        mock_client_class.return_value = mock_client
        
        manager = EnhancedOllamaManager(
            config_path=self.config_path,
            performance_db_path=self.performance_path
        )
        
        self.assertIsNotNone(manager.config)
        self.assertIn('default_models', manager.config)
        self.assertIn('task_specific_models', manager.config)
        self.assertEqual(len(manager.model_registry), 2)
    
    @patch('common.ollama_integration.OllamaClient')
    def test_model_recommendation(self, mock_client_class):
        """Test model recommendation logic."""
        mock_client = Mock()
        mock_client.list_models.return_value = [
            {"name": "llama3.1:8b"},
            {"name": "codellama:13b"}
        ]
        mock_client.get_model_info.return_value = {"size": 8000000000}
        mock_client_class.return_value = mock_client
        
        manager = EnhancedOllamaManager(
            config_path=self.config_path,
            performance_db_path=self.performance_path
        )
        
        # Test coding task recommendation
        task_characteristics = TaskCharacteristics(
            task_type=TaskType.CODING,
            complexity="medium",
            context_size=500,
            requires_accuracy=True,
            requires_speed=False,
            requires_creativity=False
        )
        
        recommended_model = manager.recommend_model(task_characteristics)
        self.assertIn(recommended_model, ["llama3.1:8b", "codellama:13b"])
    
    @patch('common.ollama_integration.OllamaClient')
    def test_performance_recording(self, mock_client_class):
        """Test performance recording and retrieval."""
        mock_client = Mock()
        mock_client.list_models.return_value = []
        mock_client_class.return_value = mock_client
        
        manager = EnhancedOllamaManager(
            config_path=self.config_path,
            performance_db_path=self.performance_path
        )
        
        # Record some performance data
        manager.record_performance(
            model_name="test_model",
            task_type=TaskType.CODING,
            execution_time=2.5,
            tokens_per_second=25.0,
            success=True,
            quality_score=8.0
        )
        
        # Check that performance was recorded
        perf_key = "test_model_coding"
        self.assertIn(perf_key, manager.performance_data)
        
        performance = manager.performance_data[perf_key]
        self.assertEqual(performance.model_name, "test_model")
        self.assertEqual(performance.task_type, TaskType.CODING)
        self.assertEqual(performance.success_rate, 1.0)
        self.assertEqual(performance.total_requests, 1)
        
        # Record another performance entry
        manager.record_performance(
            model_name="test_model",
            task_type=TaskType.CODING,
            execution_time=3.0,
            tokens_per_second=20.0,
            success=False,
            quality_score=5.0
        )
        
        # Check updated performance
        performance = manager.performance_data[perf_key]
        self.assertEqual(performance.total_requests, 2)
        self.assertEqual(performance.success_rate, 0.5)  # 1 success out of 2
        self.assertAlmostEqual(performance.avg_response_time, 2.75)  # (2.5 + 3.0) / 2
    
    @patch('common.ollama_integration.OllamaClient')
    def test_fallback_models(self, mock_client_class):
        """Test fallback model selection."""
        mock_client = Mock()
        mock_client.list_models.return_value = [
            {"name": "codellama:13b"},
            {"name": "codellama:7b"},
            {"name": "llama3.1:8b"}
        ]
        mock_client.get_model_info.return_value = {"size": 8000000000}
        mock_client_class.return_value = mock_client
        
        manager = EnhancedOllamaManager(
            config_path=self.config_path,
            performance_db_path=self.performance_path
        )
        
        fallbacks = manager.get_fallback_models("codellama:13b", TaskType.CODING)
        
        # Should return other coding models, excluding the primary
        self.assertNotIn("codellama:13b", fallbacks)
        self.assertTrue(len(fallbacks) > 0)

class TestEnhancedAgentInterface(unittest.TestCase):
    """Test enhanced agent interface."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        self.performance_path = os.path.join(self.temp_dir, "test_performance.json")
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('common.ollama_integration.OllamaClient')
    def test_agent_creation(self, mock_client_class):
        """Test agent creation with mocked client."""
        mock_client = Mock()
        mock_client.list_models.return_value = [{"name": "llama3.1:8b"}]
        mock_client.get_model_info.return_value = {"size": 8000000000}
        mock_client_class.return_value = mock_client
        
        manager = EnhancedOllamaManager(
            config_path=self.config_path,
            performance_db_path=self.performance_path
        )
        
        agent = EnhancedAgentInterface("developer", manager)
        
        self.assertEqual(agent.role, "developer")
        self.assertIsNotNone(agent.model)
        self.assertIsNotNone(agent.params)
    
    @patch('common.ollama_integration.OllamaClient')
    def test_agent_generate_with_fallback(self, mock_client_class):
        """Test agent generation with fallback logic."""
        mock_client = Mock()
        mock_client.list_models.return_value = [
            {"name": "codellama:13b"},
            {"name": "llama3.1:8b"}
        ]
        mock_client.get_model_info.return_value = {"size": 8000000000}
        
        # Mock generate method to fail first, succeed second
        mock_client.generate.side_effect = [
            Exception("Model unavailable"),  # First call fails
            {  # Second call succeeds
                "response": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
                "performance": {"tokens_per_second": 25.0}
            }
        ]
        
        mock_client_class.return_value = mock_client
        
        manager = EnhancedOllamaManager(
            config_path=self.config_path,
            performance_db_path=self.performance_path
        )
        
        agent = EnhancedAgentInterface("developer", manager)
        
        # This should succeed using fallback
        response = agent.generate(
            "Write a factorial function",
            task_type=TaskType.CODING
        )
        
        self.assertIn("factorial", response)
        self.assertEqual(mock_client.generate.call_count, 2)  # Called twice due to fallback
    
    def test_response_quality_assessment(self):
        """Test response quality assessment."""
        agent = EnhancedAgentInterface.__new__(EnhancedAgentInterface)  # Create without __init__
        
        # Test good response
        good_response = """
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        """
        quality = agent._assess_response_quality(good_response)
        self.assertGreater(quality, 5.0)
        
        # Test poor response
        poor_response = "error error error"
        quality = agent._assess_response_quality(poor_response)
        self.assertLess(quality, 5.0)
        
        # Test empty response
        empty_quality = agent._assess_response_quality("")
        self.assertEqual(empty_quality, 1.0)

class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    @patch('common.ollama_integration.EnhancedOllamaManager')
    def test_get_model_recommendations(self, mock_manager_class):
        """Test get_model_recommendations convenience function."""
        mock_manager = Mock()
        mock_manager.get_model_recommendations.return_value = {
            "primary_recommendation": "codellama:13b",
            "fallback_options": ["llama3.1:8b"],
            "reasoning": "Good for coding tasks"
        }
        mock_manager_class.return_value = mock_manager
        
        result = get_model_recommendations("Write a Python function")
        
        self.assertEqual(result["primary_recommendation"], "codellama:13b")
        self.assertIn("fallback_options", result)
    
    @patch('common.ollama_integration.EnhancedOllamaManager')
    def test_health_check_models(self, mock_manager_class):
        """Test health_check_models convenience function."""
        mock_manager = Mock()
        mock_manager.health_check_all_models.return_value = {
            "llama3.1:8b": "healthy",
            "codellama:13b": "healthy"
        }
        mock_manager_class.return_value = mock_manager
        
        result = health_check_models()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result["llama3.1:8b"], "healthy")
    
    @patch('common.ollama_integration.EnhancedOllamaManager')
    def test_create_agent(self, mock_manager_class):
        """Test create_agent convenience function."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        agent = create_agent("developer")
        
        self.assertIsInstance(agent, EnhancedAgentInterface)
        self.assertEqual(agent.role, "developer")

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)