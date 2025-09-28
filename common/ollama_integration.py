#!/usr/bin/env python3
"""
Enhanced Ollama Integration Module for AI Dev Squad Comparison

This module provides an intelligent interface for interacting with Ollama across all framework
implementations. It handles model management, inference, performance tracking, intelligent
routing, and fallback strategies.
"""

import os
import json
import time
import logging
import requests
import hashlib
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from enum import Enum
from pathlib import Path

# Import caching system
try:
    from .caching import get_cache, CacheStrategy
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    logger.warning("Caching system not available")

# Import context management system
try:
    from .context_management import (
        get_context_manager, 
        ContextStrategy, 
        MessageImportance,
        StreamingResponseHandler,
        AsyncStreamingHandler
    )
    CONTEXT_MANAGEMENT_AVAILABLE = True
except ImportError:
    CONTEXT_MANAGEMENT_AVAILABLE = False
    logger.warning("Context management system not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ollama_integration")


class TaskType(Enum):
    """Types of tasks for intelligent model routing."""
    CODING = "coding"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    GENERAL = "general"


class ModelCapability(Enum):
    """Model capabilities for routing decisions."""
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    REASONING = "reasoning"
    CREATIVITY = "creativity"
    SPEED = "speed"
    ACCURACY = "accuracy"
    CONTEXT_LENGTH = "context_length"


@dataclass
class ModelPerformance:
    """Performance metrics for a model."""
    model_name: str
    task_type: TaskType
    avg_response_time: float
    avg_tokens_per_second: float
    success_rate: float
    avg_quality_score: float
    total_requests: int
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['task_type'] = self.task_type.value
        result['last_updated'] = self.last_updated.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelPerformance':
        """Create from dictionary."""
        data['task_type'] = TaskType(data['task_type'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    size_gb: float
    capabilities: List[ModelCapability]
    context_length: int
    is_available: bool
    health_status: str = "unknown"
    last_health_check: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['capabilities'] = [cap.value for cap in self.capabilities]
        if self.last_health_check:
            result['last_health_check'] = self.last_health_check.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInfo':
        """Create from dictionary."""
        data['capabilities'] = [ModelCapability(cap) for cap in data['capabilities']]
        if data.get('last_health_check'):
            data['last_health_check'] = datetime.fromisoformat(data['last_health_check'])
        return cls(**data)


@dataclass
class TaskCharacteristics:
    """Characteristics of a task for model routing."""
    task_type: TaskType
    complexity: str  # "low", "medium", "high"
    context_size: int
    requires_accuracy: bool
    requires_speed: bool
    requires_creativity: bool
    
    @classmethod
    def analyze_prompt(cls, prompt: str, task_type: TaskType = None) -> 'TaskCharacteristics':
        """Analyze a prompt to determine task characteristics."""
        # Simple heuristics for task analysis
        prompt_lower = prompt.lower()
        
        # Determine task type if not provided
        if task_type is None:
            if any(word in prompt_lower for word in ['code', 'function', 'class', 'implement', 'write']):
                task_type = TaskType.CODING
            elif any(word in prompt_lower for word in ['test', 'verify', 'check', 'validate']):
                task_type = TaskType.TESTING
            elif any(word in prompt_lower for word in ['design', 'architecture', 'system', 'structure']):
                task_type = TaskType.ARCHITECTURE
            elif any(word in prompt_lower for word in ['debug', 'fix', 'error', 'bug']):
                task_type = TaskType.DEBUGGING
            elif any(word in prompt_lower for word in ['document', 'explain', 'describe']):
                task_type = TaskType.DOCUMENTATION
            elif any(word in prompt_lower for word in ['analyze', 'review', 'examine']):
                task_type = TaskType.ANALYSIS
            elif any(word in prompt_lower for word in ['plan', 'strategy', 'approach']):
                task_type = TaskType.PLANNING
            else:
                task_type = TaskType.GENERAL
        
        # Determine complexity
        complexity_indicators = len([word for word in ['complex', 'advanced', 'sophisticated', 'comprehensive'] if word in prompt_lower])
        if complexity_indicators >= 2 or len(prompt) > 1000:
            complexity = "high"
        elif complexity_indicators >= 1 or len(prompt) > 300:
            complexity = "medium"
        else:
            complexity = "low"
        
        # Determine requirements
        requires_accuracy = any(word in prompt_lower for word in ['accurate', 'precise', 'correct', 'exact'])
        requires_speed = any(word in prompt_lower for word in ['quick', 'fast', 'rapid', 'immediate'])
        requires_creativity = any(word in prompt_lower for word in ['creative', 'innovative', 'novel', 'unique'])
        
        return cls(
            task_type=task_type,
            complexity=complexity,
            context_size=len(prompt),
            requires_accuracy=requires_accuracy,
            requires_speed=requires_speed,
            requires_creativity=requires_creativity
        )

class OllamaClient:
    """Enhanced client for interacting with Ollama API with health monitoring."""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: Base URL for the Ollama API. If None, uses the OLLAMA_BASE_URL
                      environment variable or defaults to http://localhost:11434.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.api_url = f"{self.base_url}/api"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
        self._last_health_check = None
        self._is_healthy = False
        self._check_connection()
    
    def _check_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            True if connection is successful, raises an exception otherwise.
        """
        try:
            response = self.session.get(f"{self.api_url}/tags", timeout=self.timeout)
            response.raise_for_status()
            self._is_healthy = True
            self._last_health_check = datetime.now()
            logger.info(f"Successfully connected to Ollama at {self.base_url}")
            return True
        except requests.exceptions.RequestException as e:
            self._is_healthy = False
            self._last_health_check = datetime.now()
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            raise ConnectionError(f"Could not connect to Ollama at {self.base_url}. "
                                 "Make sure Ollama is running and accessible.")
    
    def health_check(self, force: bool = False) -> bool:
        """
        Perform a health check on the Ollama service.
        
        Args:
            force: Force a new health check even if recently checked.
            
        Returns:
            True if healthy, False otherwise.
        """
        # Skip if recently checked and not forced
        if not force and self._last_health_check:
            time_since_check = datetime.now() - self._last_health_check
            if time_since_check < timedelta(minutes=1):
                return self._is_healthy
        
        try:
            response = self.session.get(f"{self.api_url}/tags", timeout=5)
            response.raise_for_status()
            self._is_healthy = True
            self._last_health_check = datetime.now()
            return True
        except requests.exceptions.RequestException as e:
            self._is_healthy = False
            self._last_health_check = datetime.now()
            logger.warning(f"Health check failed for Ollama at {self.base_url}: {e}")
            return False
    
    def is_healthy(self) -> bool:
        """
        Check if the client is healthy (cached result).
        
        Returns:
            True if healthy based on last health check.
        """
        return self._is_healthy
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models with enhanced information.
        
        Returns:
            List of model information dictionaries.
        """
        try:
            response = self.session.get(f"{self.api_url}/tags", timeout=self.timeout)
            response.raise_for_status()
            models = response.json().get("models", [])
            
            # Enhance model information
            enhanced_models = []
            for model in models:
                enhanced_model = model.copy()
                enhanced_model['health_status'] = 'available'
                enhanced_model['last_health_check'] = datetime.now().isoformat()
                enhanced_models.append(enhanced_model)
            
            return enhanced_models
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            Model information dictionary or None if not found.
        """
        try:
            response = self.session.post(
                f"{self.api_url}/show",
                json={"name": model_name},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
            return None
    
    def is_model_available(self, model_name: str) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model_name: Name of the model to check.
            
        Returns:
            True if model is available, False otherwise.
        """
        models = self.list_models()
        return any(model['name'] == model_name for model in models)
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama library.
        
        Args:
            model_name: Name of the model to pull (e.g., "llama3.1:8b").
            
        Returns:
            True if successful, False otherwise.
        """
        logger.info(f"Pulling model: {model_name}")
        try:
            response = requests.post(
                f"{self.api_url}/pull",
                json={"name": model_name}
            )
            response.raise_for_status()
            logger.info(f"Successfully pulled model: {model_name}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def generate(self, 
                model: str, 
                prompt: str, 
                system_prompt: str = None,
                temperature: float = 0.7,
                max_tokens: int = 2048,
                stop_sequences: List[str] = None,
                stream: bool = False) -> Dict[str, Any]:
        """
        Generate text using the specified model with enhanced error handling.
        
        Args:
            model: Name of the model to use.
            prompt: The prompt to generate from.
            system_prompt: Optional system prompt for chat models.
            temperature: Sampling temperature (higher is more creative, lower is more deterministic).
            max_tokens: Maximum number of tokens to generate.
            stop_sequences: Optional list of sequences that will stop generation when encountered.
            stream: Whether to stream the response.
            
        Returns:
            Dictionary containing the generated text and metadata.
        """
        # Check model availability first
        if not self.is_model_available(model):
            raise ValueError(f"Model {model} is not available. Available models: {[m['name'] for m in self.list_models()]}")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": stream
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if stop_sequences:
            payload["stop"] = stop_sequences
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=self.timeout if not stream else None
            )
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                return self._handle_streaming_response(response, start_time)
            else:
                result = response.json()
                
                # Add enhanced performance metrics
                execution_time = time.time() - start_time
                prompt_tokens = result.get("prompt_eval_count", 0)
                completion_tokens = result.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens
                
                result["performance"] = {
                    "execution_time_seconds": execution_time,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "tokens_per_second": completion_tokens / execution_time if execution_time > 0 else 0,
                    "model_name": model,
                    "timestamp": datetime.now().isoformat()
                }
                
                return result
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout generating text with model {model}")
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating text with model {model}: {e}")
            raise
    
    def chat(self,
            model: str,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: int = 2048,
            stop_sequences: List[str] = None,
            stream: bool = False) -> Dict[str, Any]:
        """
        Chat with the specified model with enhanced error handling.
        
        Args:
            model: Name of the model to use.
            messages: List of message dictionaries with 'role' and 'content' keys.
                     Roles can be 'system', 'user', or 'assistant'.
            temperature: Sampling temperature.
            max_tokens: Maximum number of tokens to generate.
            stop_sequences: Optional list of sequences that will stop generation when encountered.
            stream: Whether to stream the response.
            
        Returns:
            Dictionary containing the chat response and metadata.
        """
        # Check model availability first
        if not self.is_model_available(model):
            raise ValueError(f"Model {model} is not available. Available models: {[m['name'] for m in self.list_models()]}")
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": stream
        }
        
        if stop_sequences:
            payload["stop"] = stop_sequences
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.api_url}/chat",
                json=payload,
                timeout=self.timeout if not stream else None
            )
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                return self._handle_streaming_response(response, start_time)
            else:
                result = response.json()
                
                # Add enhanced performance metrics
                execution_time = time.time() - start_time
                prompt_tokens = result.get("prompt_eval_count", 0)
                completion_tokens = result.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens
                
                result["performance"] = {
                    "execution_time_seconds": execution_time,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "tokens_per_second": completion_tokens / execution_time if execution_time > 0 else 0,
                    "model_name": model,
                    "timestamp": datetime.now().isoformat()
                }
                
                return result
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout in chat with model {model}")
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in chat with model {model}: {e}")
            raise
    
    def _handle_streaming_response(self, response: requests.Response, start_time: float) -> Dict[str, Any]:
        """
        Handle streaming response from Ollama.
        
        Args:
            response: The streaming response object.
            start_time: Start time of the request.
            
        Returns:
            Dictionary containing the complete response and metadata.
        """
        full_response = ""
        total_tokens = 0
        
        try:
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    if 'response' in chunk:
                        full_response += chunk['response']
                    if 'eval_count' in chunk:
                        total_tokens = chunk['eval_count']
                    if chunk.get('done', False):
                        break
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing streaming response: {e}")
            raise
        
        execution_time = time.time() - start_time
        
        return {
            "response": full_response,
            "performance": {
                "execution_time_seconds": execution_time,
                "completion_tokens": total_tokens,
                "tokens_per_second": total_tokens / execution_time if execution_time > 0 else 0,
                "timestamp": datetime.now().isoformat(),
                "streaming": True
            }
        }


class EnhancedOllamaManager:
    """Enhanced manager for Ollama models with intelligent routing and performance profiling."""
    
    def __init__(self, config_path: str = None, performance_db_path: str = None):
        """
        Initialize the enhanced Ollama manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses default locations.
            performance_db_path: Path to the performance database file.
        """
        self.client = OllamaClient()
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "ollama_config.json"
        )
        self.performance_db_path = performance_db_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "model_performance.json"
        )
        self.config = self._load_config()
        self.performance_data = self._load_performance_data()
        self.model_registry = self._build_model_registry()
        self._last_health_check = None
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create enhanced default.
        
        Returns:
            Configuration dictionary.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
            except Exception as e:
                logger.warning(f"Error loading config from {self.config_path}: {e}")
        
        # Enhanced default configuration
        default_config = {
            "default_models": {
                "architect": "codellama:13b",
                "developer": "codellama:13b", 
                "tester": "llama3.1:8b",
                "general": "llama3.1:8b"
            },
            "task_specific_models": {
                TaskType.CODING.value: ["codellama:13b", "codellama:7b"],
                TaskType.ARCHITECTURE.value: ["codellama:13b", "llama3.1:8b"],
                TaskType.TESTING.value: ["llama3.1:8b", "codellama:7b"],
                TaskType.DEBUGGING.value: ["codellama:13b", "llama3.1:8b"],
                TaskType.DOCUMENTATION.value: ["llama3.1:8b", "mistral:7b"],
                TaskType.ANALYSIS.value: ["llama3.1:8b", "codellama:13b"],
                TaskType.PLANNING.value: ["llama3.1:8b", "codellama:13b"],
                TaskType.GENERAL.value: ["llama3.1:8b", "mistral:7b"]
            },
            "model_capabilities": {
                "codellama:13b": [
                    ModelCapability.CODE_GENERATION.value,
                    ModelCapability.CODE_ANALYSIS.value,
                    ModelCapability.ACCURACY.value,
                    ModelCapability.CONTEXT_LENGTH.value
                ],
                "codellama:7b": [
                    ModelCapability.CODE_GENERATION.value,
                    ModelCapability.SPEED.value
                ],
                "llama3.1:8b": [
                    ModelCapability.REASONING.value,
                    ModelCapability.CREATIVITY.value,
                    ModelCapability.ACCURACY.value
                ],
                "mistral:7b": [
                    ModelCapability.SPEED.value,
                    ModelCapability.CREATIVITY.value
                ]
            },
            "routing_preferences": {
                "prefer_speed": False,
                "prefer_accuracy": True,
                "fallback_enabled": True,
                "health_check_interval": 300,  # 5 minutes
                "performance_weight": 0.7,
                "availability_weight": 0.3
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _load_performance_data(self) -> Dict[str, ModelPerformance]:
        """
        Load performance data from file.
        
        Returns:
            Dictionary of model performance data.
        """
        if os.path.exists(self.performance_db_path):
            try:
                with open(self.performance_db_path, 'r') as f:
                    data = json.load(f)
                
                performance_data = {}
                for key, perf_dict in data.items():
                    performance_data[key] = ModelPerformance.from_dict(perf_dict)
                
                logger.info(f"Loaded performance data from {self.performance_db_path}")
                return performance_data
            except Exception as e:
                logger.warning(f"Error loading performance data from {self.performance_db_path}: {e}")
        
        return {}
    
    def _save_performance_data(self) -> None:
        """Save performance data to file."""
        try:
            data = {}
            for key, performance in self.performance_data.items():
                data[key] = performance.to_dict()
            
            os.makedirs(os.path.dirname(self.performance_db_path), exist_ok=True)
            with open(self.performance_db_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved performance data to {self.performance_db_path}")
        except Exception as e:
            logger.error(f"Error saving performance data to {self.performance_db_path}: {e}")
    
    def _build_model_registry(self) -> Dict[str, ModelInfo]:
        """
        Build a registry of available models with their capabilities.
        
        Returns:
            Dictionary mapping model names to ModelInfo objects.
        """
        registry = {}
        available_models = self.client.list_models()
        
        for model_data in available_models:
            model_name = model_data['name']
            
            # Get capabilities from config
            capabilities = []
            if model_name in self.config.get('model_capabilities', {}):
                cap_strings = self.config['model_capabilities'][model_name]
                capabilities = [ModelCapability(cap) for cap in cap_strings]
            
            # Get model info from Ollama
            model_info = self.client.get_model_info(model_name)
            size_gb = 0.0
            context_length = 4096  # Default
            
            if model_info:
                # Extract size and context length from model info
                size_gb = model_info.get('size', 0) / (1024**3)  # Convert to GB
                # Context length might be in model details
                if 'details' in model_info:
                    context_length = model_info['details'].get('parameter_size', 4096)
            
            registry[model_name] = ModelInfo(
                name=model_name,
                size_gb=size_gb,
                capabilities=capabilities,
                context_length=context_length,
                is_available=True,
                health_status="healthy",
                last_health_check=datetime.now()
            )
        
        return registry
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save.
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config to {self.config_path}: {e}")
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            new_config: New configuration values to merge with existing config.
        """
        self.config.update(new_config)
        self._save_config(self.config)
    
    def recommend_model(self, task_characteristics: TaskCharacteristics) -> str:
        """
        Recommend the best model for given task characteristics.
        
        Args:
            task_characteristics: Characteristics of the task.
            
        Returns:
            Recommended model name.
        """
        # Get candidate models for the task type
        task_models = self.config.get('task_specific_models', {}).get(
            task_characteristics.task_type.value, 
            list(self.config['default_models'].values())
        )
        
        # Filter by availability
        available_models = [model for model in task_models if model in self.model_registry]
        
        if not available_models:
            logger.warning(f"No available models for task type {task_characteristics.task_type}")
            return self.config['default_models']['general']
        
        # Score models based on task requirements and performance
        model_scores = {}
        
        for model_name in available_models:
            model_info = self.model_registry[model_name]
            score = self._calculate_model_score(model_info, task_characteristics)
            model_scores[model_name] = score
        
        # Return the highest scoring model
        best_model = max(model_scores.items(), key=lambda x: x[1])[0]
        logger.info(f"Recommended model {best_model} for {task_characteristics.task_type} task")
        return best_model
    
    def _calculate_model_score(self, model_info: ModelInfo, task_characteristics: TaskCharacteristics) -> float:
        """
        Calculate a score for how well a model fits task characteristics.
        
        Args:
            model_info: Information about the model.
            task_characteristics: Characteristics of the task.
            
        Returns:
            Score between 0 and 1.
        """
        score = 0.0
        
        # Base capability matching
        required_capabilities = self._get_required_capabilities(task_characteristics)
        capability_match = len(set(model_info.capabilities) & set(required_capabilities))
        capability_score = capability_match / max(len(required_capabilities), 1)
        score += capability_score * 0.4
        
        # Performance history
        perf_key = f"{model_info.name}_{task_characteristics.task_type.value}"
        if perf_key in self.performance_data:
            performance = self.performance_data[perf_key]
            # Normalize performance metrics
            perf_score = (performance.success_rate * 0.4 + 
                         min(performance.avg_quality_score / 10.0, 1.0) * 0.3 +
                         min(performance.avg_tokens_per_second / 50.0, 1.0) * 0.3)
            score += perf_score * 0.4
        else:
            # No performance data, use moderate score
            score += 0.2
        
        # Health and availability
        if model_info.health_status == "healthy":
            score += 0.2
        elif model_info.health_status == "degraded":
            score += 0.1
        
        # Task-specific preferences
        routing_prefs = self.config.get('routing_preferences', {})
        
        if task_characteristics.requires_speed and routing_prefs.get('prefer_speed', False):
            if ModelCapability.SPEED in model_info.capabilities:
                score += 0.1
        
        if task_characteristics.requires_accuracy and routing_prefs.get('prefer_accuracy', True):
            if ModelCapability.ACCURACY in model_info.capabilities:
                score += 0.1
        
        # Context length consideration
        if task_characteristics.context_size > model_info.context_length * 0.8:
            score -= 0.2  # Penalize if context is too large
        
        return min(score, 1.0)
    
    def _get_required_capabilities(self, task_characteristics: TaskCharacteristics) -> List[ModelCapability]:
        """
        Get required capabilities based on task characteristics.
        
        Args:
            task_characteristics: Characteristics of the task.
            
        Returns:
            List of required capabilities.
        """
        capabilities = []
        
        if task_characteristics.task_type in [TaskType.CODING, TaskType.DEBUGGING]:
            capabilities.extend([ModelCapability.CODE_GENERATION, ModelCapability.CODE_ANALYSIS])
        
        if task_characteristics.task_type == TaskType.ARCHITECTURE:
            capabilities.extend([ModelCapability.REASONING, ModelCapability.ACCURACY])
        
        if task_characteristics.requires_accuracy:
            capabilities.append(ModelCapability.ACCURACY)
        
        if task_characteristics.requires_speed:
            capabilities.append(ModelCapability.SPEED)
        
        if task_characteristics.requires_creativity:
            capabilities.append(ModelCapability.CREATIVITY)
        
        if task_characteristics.context_size > 8000:
            capabilities.append(ModelCapability.CONTEXT_LENGTH)
        
        return capabilities
    
    def get_fallback_models(self, primary_model: str, task_type: TaskType) -> List[str]:
        """
        Get fallback models for a primary model.
        
        Args:
            primary_model: The primary model that failed.
            task_type: Type of task.
            
        Returns:
            List of fallback model names.
        """
        # Get all models for the task type
        task_models = self.config.get('task_specific_models', {}).get(
            task_type.value, 
            list(self.config['default_models'].values())
        )
        
        # Remove the primary model and return available alternatives
        fallbacks = [model for model in task_models 
                    if model != primary_model and model in self.model_registry]
        
        # Sort by health status and performance
        fallbacks.sort(key=lambda m: (
            self.model_registry[m].health_status == "healthy",
            self._get_model_performance_score(m, task_type)
        ), reverse=True)
        
        return fallbacks
    
    def _get_model_performance_score(self, model_name: str, task_type: TaskType) -> float:
        """
        Get performance score for a model and task type.
        
        Args:
            model_name: Name of the model.
            task_type: Type of task.
            
        Returns:
            Performance score between 0 and 1.
        """
        perf_key = f"{model_name}_{task_type.value}"
        if perf_key in self.performance_data:
            performance = self.performance_data[perf_key]
            return (performance.success_rate + performance.avg_quality_score / 10.0) / 2.0
        return 0.5  # Default score for unknown performance
    
    def ensure_models_available(self, models: List[str] = None) -> bool:
        """
        Ensure that specified models are available, pulling them if necessary.
        
        Args:
            models: List of model names to ensure. If None, uses default models.
            
        Returns:
            True if all models are available, False otherwise.
        """
        if models is None:
            models = list(self.config["default_models"].values())
        
        available_models = [model["name"] for model in self.client.list_models()]
        success = True
        
        for model in models:
            if model not in available_models:
                logger.info(f"Model {model} not found locally, pulling...")
                if not self.client.pull_model(model):
                    logger.error(f"Failed to pull model {model}")
                    success = False
                else:
                    # Update model registry after successful pull
                    self._update_model_registry()
        
        return success
    
    def _update_model_registry(self) -> None:
        """Update the model registry with current available models."""
        self.model_registry = self._build_model_registry()
    
    def record_performance(self, model_name: str, task_type: TaskType, 
                          execution_time: float, tokens_per_second: float,
                          success: bool, quality_score: float = 5.0) -> None:
        """
        Record performance metrics for a model and task type.
        
        Args:
            model_name: Name of the model.
            task_type: Type of task performed.
            execution_time: Time taken for execution in seconds.
            tokens_per_second: Tokens generated per second.
            success: Whether the task was successful.
            quality_score: Quality score from 0-10.
        """
        perf_key = f"{model_name}_{task_type.value}"
        
        if perf_key in self.performance_data:
            # Update existing performance data
            perf = self.performance_data[perf_key]
            
            # Calculate running averages
            total_requests = perf.total_requests + 1
            perf.avg_response_time = ((perf.avg_response_time * perf.total_requests + execution_time) 
                                    / total_requests)
            perf.avg_tokens_per_second = ((perf.avg_tokens_per_second * perf.total_requests + tokens_per_second) 
                                        / total_requests)
            perf.avg_quality_score = ((perf.avg_quality_score * perf.total_requests + quality_score) 
                                    / total_requests)
            
            # Update success rate
            total_successes = perf.success_rate * perf.total_requests + (1 if success else 0)
            perf.success_rate = total_successes / total_requests
            
            perf.total_requests = total_requests
            perf.last_updated = datetime.now()
        else:
            # Create new performance record
            self.performance_data[perf_key] = ModelPerformance(
                model_name=model_name,
                task_type=task_type,
                avg_response_time=execution_time,
                avg_tokens_per_second=tokens_per_second,
                success_rate=1.0 if success else 0.0,
                avg_quality_score=quality_score,
                total_requests=1,
                last_updated=datetime.now()
            )
        
        # Save performance data periodically
        if len(self.performance_data) % 10 == 0:  # Save every 10 records
            self._save_performance_data()
    
    def get_performance_summary(self, model_name: str = None, task_type: TaskType = None) -> Dict[str, Any]:
        """
        Get performance summary for models and task types.
        
        Args:
            model_name: Optional model name to filter by.
            task_type: Optional task type to filter by.
            
        Returns:
            Performance summary dictionary.
        """
        filtered_data = {}
        
        for key, performance in self.performance_data.items():
            if model_name and performance.model_name != model_name:
                continue
            if task_type and performance.task_type != task_type:
                continue
            filtered_data[key] = performance
        
        if not filtered_data:
            return {"message": "No performance data found for the specified criteria"}
        
        # Calculate aggregate statistics
        total_requests = sum(p.total_requests for p in filtered_data.values())
        avg_response_time = sum(p.avg_response_time * p.total_requests for p in filtered_data.values()) / total_requests
        avg_success_rate = sum(p.success_rate * p.total_requests for p in filtered_data.values()) / total_requests
        avg_quality = sum(p.avg_quality_score * p.total_requests for p in filtered_data.values()) / total_requests
        
        return {
            "total_requests": total_requests,
            "avg_response_time": avg_response_time,
            "avg_success_rate": avg_success_rate,
            "avg_quality_score": avg_quality,
            "model_count": len(set(p.model_name for p in filtered_data.values())),
            "task_types": list(set(p.task_type.value for p in filtered_data.values())),
            "detailed_performance": {k: v.to_dict() for k, v in filtered_data.items()}
        }
    
    def health_check_all_models(self) -> Dict[str, str]:
        """
        Perform health check on all registered models.
        
        Returns:
            Dictionary mapping model names to health status.
        """
        health_status = {}
        
        for model_name, model_info in self.model_registry.items():
            try:
                # Try a simple generation to test model health
                result = self.client.generate(
                    model=model_name,
                    prompt="Hello",
                    max_tokens=10
                )
                
                if result and 'response' in result:
                    model_info.health_status = "healthy"
                    health_status[model_name] = "healthy"
                else:
                    model_info.health_status = "degraded"
                    health_status[model_name] = "degraded"
                    
            except Exception as e:
                logger.warning(f"Health check failed for model {model_name}: {e}")
                model_info.health_status = "unhealthy"
                health_status[model_name] = "unhealthy"
            
            model_info.last_health_check = datetime.now()
        
        self._last_health_check = datetime.now()
        return health_status
    
    def get_model_recommendations(self, task_description: str, task_type: TaskType = None) -> Dict[str, Any]:
        """
        Get model recommendations for a task description.
        
        Args:
            task_description: Description of the task.
            task_type: Optional explicit task type.
            
        Returns:
            Dictionary with recommendations and reasoning.
        """
        # Analyze task characteristics
        task_characteristics = TaskCharacteristics.analyze_prompt(task_description, task_type)
        
        # Get primary recommendation
        primary_model = self.recommend_model(task_characteristics)
        
        # Get fallback options
        fallback_models = self.get_fallback_models(primary_model, task_characteristics.task_type)
        
        # Get performance data for context
        primary_perf_key = f"{primary_model}_{task_characteristics.task_type.value}"
        primary_performance = self.performance_data.get(primary_perf_key)
        
        return {
            "primary_recommendation": primary_model,
            "fallback_options": fallback_models[:3],  # Top 3 fallbacks
            "task_characteristics": {
                "task_type": task_characteristics.task_type.value,
                "complexity": task_characteristics.complexity,
                "context_size": task_characteristics.context_size,
                "requires_accuracy": task_characteristics.requires_accuracy,
                "requires_speed": task_characteristics.requires_speed,
                "requires_creativity": task_characteristics.requires_creativity
            },
            "primary_model_performance": primary_performance.to_dict() if primary_performance else None,
            "reasoning": self._generate_recommendation_reasoning(primary_model, task_characteristics)
        }
    
    def _generate_recommendation_reasoning(self, model_name: str, task_characteristics: TaskCharacteristics) -> str:
        """
        Generate human-readable reasoning for model recommendation.
        
        Args:
            model_name: Recommended model name.
            task_characteristics: Task characteristics.
            
        Returns:
            Reasoning string.
        """
        model_info = self.model_registry.get(model_name)
        if not model_info:
            return f"Model {model_name} recommended as fallback option."
        
        reasons = []
        
        # Capability matching
        if ModelCapability.CODE_GENERATION in model_info.capabilities and task_characteristics.task_type in [TaskType.CODING, TaskType.DEBUGGING]:
            reasons.append("strong code generation capabilities")
        
        if ModelCapability.REASONING in model_info.capabilities and task_characteristics.task_type in [TaskType.ARCHITECTURE, TaskType.ANALYSIS]:
            reasons.append("excellent reasoning abilities")
        
        if ModelCapability.ACCURACY in model_info.capabilities and task_characteristics.requires_accuracy:
            reasons.append("high accuracy for precise tasks")
        
        if ModelCapability.SPEED in model_info.capabilities and task_characteristics.requires_speed:
            reasons.append("fast response times")
        
        # Performance history
        perf_key = f"{model_name}_{task_characteristics.task_type.value}"
        if perf_key in self.performance_data:
            performance = self.performance_data[perf_key]
            if performance.success_rate > 0.8:
                reasons.append(f"proven track record ({performance.success_rate:.1%} success rate)")
        
        # Health status
        if model_info.health_status == "healthy":
            reasons.append("currently healthy and available")
        
        if not reasons:
            reasons.append("best available option for this task type")
        
        return f"Recommended due to {', '.join(reasons)}."
    
    def get_model_for_role(self, role: str, task_description: str = None) -> str:
        """
        Get the appropriate model for a specific agent role with intelligent routing.
        
        Args:
            role: Agent role (architect, developer, tester, or general).
            task_description: Optional task description for better model selection.
            
        Returns:
            Model name for the specified role.
        """
        if task_description:
            # Use intelligent routing based on task description
            recommendations = self.get_model_recommendations(task_description)
            return recommendations["primary_recommendation"]
        else:
            # Fall back to role-based default
            return self.config["default_models"].get(role, self.config["default_models"]["general"])
    
    def get_parameters(self, role: str = None, custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get generation parameters with role-specific defaults.
        
        Args:
            role: Agent role for role-specific parameters.
            custom_params: Custom parameters to override defaults.
            
        Returns:
            Dictionary of parameters.
        """
        params = self.config["parameters"].copy()
        
        # Add role-specific parameters if available
        if role and "role_specific_parameters" in self.config:
            role_params = self.config["role_specific_parameters"].get(role, {})
            params.update(role_params)
        
        # Apply custom overrides
        if custom_params:
            params.update(custom_params)
        
        return params


# Maintain backward compatibility
OllamaManager = EnhancedOllamaManager


class EnhancedAgentInterface:
    """Enhanced interface for AI agents with intelligent model routing and fallback."""
    
    def __init__(self, role: str, ollama_manager: EnhancedOllamaManager = None, 
                 enable_caching: bool = True, enable_context_management: bool = True,
                 max_context_tokens: int = None):
        """
        Initialize the enhanced agent interface.
        
        Args:
            role: Agent role (architect, developer, tester, or general).
            ollama_manager: Optional EnhancedOllamaManager instance. If None, creates a new one.
            enable_caching: Whether to enable intelligent caching.
            enable_context_management: Whether to enable context management.
            max_context_tokens: Maximum tokens for context window.
        """
        self.role = role
        self.ollama_manager = ollama_manager or EnhancedOllamaManager()
        self.client = self.ollama_manager.client
        self._current_model = None
        self._fallback_models = []
        self.enable_caching = enable_caching and CACHING_AVAILABLE
        self.enable_context_management = enable_context_management and CONTEXT_MANAGEMENT_AVAILABLE
        
        # Initialize cache if available
        if self.enable_caching:
            self.cache = get_cache()
        else:
            self.cache = None
        
        # Initialize context management if available
        if self.enable_context_management:
            self.context_manager = get_context_manager()
            self.max_context_tokens = max_context_tokens or 4096
            self._active_conversations = {}
        else:
            self.context_manager = None
            self.max_context_tokens = None
        
        # Get initial model for role
        self.model = self.ollama_manager.get_model_for_role(role)
        self.params = self.ollama_manager.get_parameters(role)
        
        # Ensure model is available
        self.ollama_manager.ensure_models_available([self.model])
    
    def generate(self, prompt: str, system_prompt: str = None, task_type: TaskType = None, 
                use_cache: bool = True, **kwargs) -> str:
        """
        Generate text using intelligent model selection with caching and fallback.
        
        Args:
            prompt: The prompt to generate from.
            system_prompt: Optional system prompt.
            task_type: Optional task type for better model selection.
            use_cache: Whether to use caching for this request.
            **kwargs: Additional parameters to override defaults.
            
        Returns:
            Generated text.
        """
        # Get optimal model for this specific task
        if task_type or len(prompt) > 100:  # Use intelligent routing for substantial prompts
            recommendations = self.ollama_manager.get_model_recommendations(prompt, task_type)
            selected_model = recommendations["primary_recommendation"]
            fallback_models = recommendations["fallback_options"]
        else:
            selected_model = self.model
            fallback_models = self.ollama_manager.get_fallback_models(
                selected_model, 
                task_type or TaskType.GENERAL
            )
        
        # Merge parameters
        params = self.params.copy()
        params.update(kwargs)
        
        # Add role-specific system prompt if not provided
        if not system_prompt and "system_prompt" in params:
            system_prompt = params["system_prompt"]
        
        # Create context for caching
        cache_context = {
            "system_prompt": system_prompt,
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 2048),
            "task_type": task_type.value if task_type else None,
            "role": self.role
        }
        
        # Check cache first if enabled
        if self.enable_caching and use_cache and self.cache:
            cached_response = self.cache.get(prompt, selected_model, cache_context)
            if cached_response:
                logger.debug(f"Cache hit for model {selected_model}")
                # Update cache stats for performance tracking
                if hasattr(self.cache.stats, 'avg_response_time_cached'):
                    # This is a cache hit, so response time is near zero
                    self.cache.stats.avg_response_time_cached = 0.1  # Minimal time for cache lookup
                return cached_response
        
        # Try primary model first, then fallbacks
        models_to_try = [selected_model] + fallback_models
        last_error = None
        
        for model_name in models_to_try:
            try:
                start_time = time.time()
                
                result = self.client.generate(
                    model=model_name,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 2048),
                    stop_sequences=params.get("stop_sequences"),
                    stream=params.get("stream", False)
                )
                
                # Record performance
                execution_time = time.time() - start_time
                performance = result.get("performance", {})
                tokens_per_second = performance.get("tokens_per_second", 0)
                quality_score = self._assess_response_quality(result["response"])
                
                self.ollama_manager.record_performance(
                    model_name=model_name,
                    task_type=task_type or TaskType.GENERAL,
                    execution_time=execution_time,
                    tokens_per_second=tokens_per_second,
                    success=True,
                    quality_score=quality_score
                )
                
                # Cache the response if caching is enabled and response quality is good
                if (self.enable_caching and use_cache and self.cache and 
                    quality_score >= 6.0 and not params.get("stream", False)):
                    
                    # Determine TTL based on task type and quality
                    ttl_seconds = self._calculate_cache_ttl(task_type, quality_score, execution_time)
                    
                    self.cache.put(
                        prompt=prompt,
                        model_name=model_name,
                        response=result["response"],
                        metadata={
                            "execution_time": execution_time,
                            "tokens_per_second": tokens_per_second,
                            "quality_score": quality_score,
                            "task_type": task_type.value if task_type else None,
                            "role": self.role
                        },
                        context=cache_context,
                        performance_score=quality_score,
                        ttl_seconds=ttl_seconds
                    )
                    
                    logger.debug(f"Cached response for model {model_name} with TTL {ttl_seconds}s")
                
                # Update cache stats for uncached response time
                if self.enable_caching and self.cache:
                    # Update running average of uncached response times
                    current_avg = self.cache.stats.avg_response_time_uncached
                    total_requests = self.cache.stats.total_requests
                    if total_requests > 0:
                        self.cache.stats.avg_response_time_uncached = (
                            (current_avg * (total_requests - 1) + execution_time) / total_requests
                        )
                    else:
                        self.cache.stats.avg_response_time_uncached = execution_time
                
                logger.info(f"Successfully generated text using model {model_name}")
                return result["response"]
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to generate with model {model_name}: {e}")
                
                # Record failure
                self.ollama_manager.record_performance(
                    model_name=model_name,
                    task_type=task_type or TaskType.GENERAL,
                    execution_time=0,
                    tokens_per_second=0,
                    success=False,
                    quality_score=0
                )
                
                continue
        
        # If all models failed, raise the last error
        raise RuntimeError(f"All models failed. Last error: {last_error}")
    
    def _calculate_cache_ttl(self, task_type: Optional[TaskType], quality_score: float, 
                           execution_time: float) -> int:
        """
        Calculate appropriate TTL for cache entry based on task characteristics.
        
        Args:
            task_type: Type of task.
            quality_score: Quality score of the response.
            execution_time: Time taken to generate the response.
            
        Returns:
            TTL in seconds.
        """
        base_ttl = 3600  # 1 hour default
        
        # Adjust based on task type
        if task_type == TaskType.CODING:
            base_ttl = 7200  # Code solutions are more stable
        elif task_type == TaskType.DOCUMENTATION:
            base_ttl = 14400  # Documentation is very stable
        elif task_type == TaskType.DEBUGGING:
            base_ttl = 1800  # Debug solutions may be context-specific
        elif task_type == TaskType.GENERAL:
            base_ttl = 900  # General responses are less stable
        
        # Adjust based on quality - higher quality responses cached longer
        quality_multiplier = min(quality_score / 5.0, 2.0)  # Max 2x multiplier
        
        # Adjust based on execution time - expensive responses cached longer
        if execution_time > 10.0:  # Very slow responses
            time_multiplier = 2.0
        elif execution_time > 5.0:  # Slow responses
            time_multiplier = 1.5
        else:
            time_multiplier = 1.0
        
        final_ttl = int(base_ttl * quality_multiplier * time_multiplier)
        
        # Ensure reasonable bounds
        return max(300, min(final_ttl, 86400))  # Between 5 minutes and 24 hours
    
    def _assess_response_quality(self, response: str) -> float:
        """
        Assess the quality of a response (simple heuristic).
        
        Args:
            response: The generated response.
            
        Returns:
            Quality score from 0-10.
        """
        if not response or len(response.strip()) < 10:
            return 1.0
        
        # Simple quality heuristics
        score = 5.0  # Base score
        
        # Length consideration
        if 50 <= len(response) <= 2000:
            score += 1.0
        elif len(response) > 2000:
            score += 0.5
        
        # Check for code blocks (good for coding tasks)
        if "```" in response:
            score += 1.0
        
        # Check for structured content
        if any(marker in response for marker in ["1.", "2.", "-", "*"]):
            score += 0.5
        
        # Penalize very repetitive content
        words = response.split()
        if len(set(words)) < len(words) * 0.3:  # Less than 30% unique words
            score -= 2.0
        
        return max(0.0, min(10.0, score))
    
    def generate_streaming(self, prompt: str, system_prompt: str = None, 
                          task_type: TaskType = None, callback: Callable[[str], None] = None,
                          **kwargs) -> Iterator[str]:
        """
        Generate text with streaming response.
        
        Args:
            prompt: The prompt to generate from.
            system_prompt: Optional system prompt.
            task_type: Optional task type for better model selection.
            callback: Optional callback for each chunk.
            **kwargs: Additional parameters.
            
        Yields:
            Response chunks as they arrive.
        """
        # Get optimal model for this task
        if task_type or len(prompt) > 100:
            recommendations = self.ollama_manager.get_model_recommendations(prompt, task_type)
            selected_model = recommendations["primary_recommendation"]
            fallback_models = recommendations["fallback_options"]
        else:
            selected_model = self.model
            fallback_models = self.ollama_manager.get_fallback_models(
                selected_model, 
                task_type or TaskType.GENERAL
            )
        
        # Merge parameters
        params = self.params.copy()
        params.update(kwargs)
        params["stream"] = True  # Force streaming
        
        # Add role-specific system prompt if not provided
        if not system_prompt and "system_prompt" in params:
            system_prompt = params["system_prompt"]
        
        # Initialize streaming handler
        streaming_handler = StreamingResponseHandler(callback)
        streaming_handler.start_streaming()
        
        # Try primary model first, then fallbacks
        models_to_try = [selected_model] + fallback_models
        last_error = None
        
        for model_name in models_to_try:
            try:
                start_time = time.time()
                
                # Make streaming request
                response = self.client.session.post(
                    f"{self.client.api_url}/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "system": system_prompt,
                        "temperature": params.get("temperature", 0.7),
                        "num_predict": params.get("max_tokens", 2048),
                        "stream": True
                    },
                    stream=True,
                    timeout=None
                )
                response.raise_for_status()
                
                # Process streaming response
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line.decode('utf-8'))
                            if 'response' in chunk_data:
                                chunk = chunk_data['response']
                                processed_chunk = streaming_handler.process_chunk(chunk)
                                yield processed_chunk
                            
                            if chunk_data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
                
                # Record successful streaming
                stats = streaming_handler.finish_streaming()
                self.ollama_manager.record_performance(
                    model_name=model_name,
                    task_type=task_type or TaskType.GENERAL,
                    execution_time=stats["duration_seconds"],
                    tokens_per_second=stats["tokens_per_second"],
                    success=True,
                    quality_score=self._assess_response_quality(stats["complete_response"])
                )
                
                logger.info(f"Successfully completed streaming generation with model {model_name}")
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to stream with model {model_name}: {e}")
                
                # Record failure
                self.ollama_manager.record_performance(
                    model_name=model_name,
                    task_type=task_type or TaskType.GENERAL,
                    execution_time=0,
                    tokens_per_second=0,
                    success=False,
                    quality_score=0
                )
                
                continue
        
        # If all models failed, raise the last error
        raise RuntimeError(f"All streaming models failed. Last error: {last_error}")
    
    def start_conversation(self, conversation_id: str = None, 
                          context_strategy: ContextStrategy = None,
                          max_tokens: int = None) -> str:
        """
        Start a new conversation with context management.
        
        Args:
            conversation_id: Optional conversation ID. If None, generates one.
            context_strategy: Context management strategy.
            max_tokens: Maximum tokens for context.
            
        Returns:
            Conversation ID.
        """
        if not self.enable_context_management:
            raise RuntimeError("Context management not enabled")
        
        if conversation_id is None:
            conversation_id = f"{self.role}_{int(time.time())}"
        
        # Create context window
        context = self.context_manager.create_context(
            conversation_id=conversation_id,
            model_name=self.model,
            max_tokens=max_tokens or self.max_context_tokens,
            strategy=context_strategy or ContextStrategy.SLIDING_WINDOW
        )
        
        self._active_conversations[conversation_id] = {
            "created_at": datetime.now(),
            "model": self.model,
            "strategy": context_strategy or ContextStrategy.SLIDING_WINDOW
        }
        
        logger.info(f"Started conversation {conversation_id} with context management")
        return conversation_id
    
    def chat_with_context(self, conversation_id: str, message: str,
                         task_type: TaskType = None, importance: MessageImportance = None,
                         use_cache: bool = True, **kwargs) -> str:
        """
        Chat with automatic context management.
        
        Args:
            conversation_id: Conversation identifier.
            message: User message.
            task_type: Optional task type.
            importance: Message importance level.
            use_cache: Whether to use caching.
            **kwargs: Additional parameters.
            
        Returns:
            Assistant response.
        """
        if not self.enable_context_management:
            raise RuntimeError("Context management not enabled")
        
        # Add user message to context
        self.context_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            importance=importance or MessageImportance.HIGH
        )
        
        # Get managed context for model
        messages = self.context_manager.get_messages_for_model(conversation_id)
        
        # Generate response using managed context
        response = self.chat(messages, task_type=task_type, use_cache=use_cache, **kwargs)
        
        # Add assistant response to context
        self.context_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            importance=MessageImportance.MEDIUM
        )
        
        return response
    
    def chat_streaming_with_context(self, conversation_id: str, message: str,
                                   task_type: TaskType = None, 
                                   importance: MessageImportance = None,
                                   callback: Callable[[str], None] = None,
                                   **kwargs) -> Iterator[str]:
        """
        Chat with streaming and context management.
        
        Args:
            conversation_id: Conversation identifier.
            message: User message.
            task_type: Optional task type.
            importance: Message importance level.
            callback: Optional callback for chunks.
            **kwargs: Additional parameters.
            
        Yields:
            Response chunks as they arrive.
        """
        if not self.enable_context_management:
            raise RuntimeError("Context management not enabled")
        
        # Add user message to context
        self.context_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            importance=importance or MessageImportance.HIGH
        )
        
        # Get managed context for model
        messages = self.context_manager.get_messages_for_model(conversation_id)
        
        # Convert messages to prompt format for streaming
        conversation_text = " ".join([f"{msg['role']}: {msg['content']}" for msg in messages[-3:]])
        
        # Stream response
        complete_response = ""
        for chunk in self.generate_streaming(
            prompt=conversation_text, 
            task_type=task_type, 
            callback=callback,
            **kwargs
        ):
            complete_response += chunk
            yield chunk
        
        # Add complete response to context
        self.context_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=complete_response,
            importance=MessageImportance.MEDIUM
        )
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get summary of a conversation's context.
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            Conversation summary.
        """
        if not self.enable_context_management:
            return {"error": "Context management not enabled"}
        
        stats = self.context_manager.get_context_stats(conversation_id)
        
        if conversation_id in self._active_conversations:
            conv_info = self._active_conversations[conversation_id]
            stats.update({
                "created_at": conv_info["created_at"].isoformat(),
                "model": conv_info["model"],
                "strategy": conv_info["strategy"].value if hasattr(conv_info["strategy"], 'value') else str(conv_info["strategy"])
            })
        
        return stats
    
    def optimize_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Optimize context for a conversation.
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            Optimization results.
        """
        if not self.enable_context_management:
            return {"error": "Context management not enabled"}
        
        return self.context_manager.optimize_context(conversation_id)
    
    def end_conversation(self, conversation_id: str) -> bool:
        """
        End a conversation and clean up context.
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            True if ended successfully.
        """
        if not self.enable_context_management:
            return False
        
        # Clear from context manager
        context_cleared = self.context_manager.clear_context(conversation_id)
        
        # Clear from active conversations
        if conversation_id in self._active_conversations:
            del self._active_conversations[conversation_id]
        
        logger.info(f"Ended conversation {conversation_id}")
        return context_cleared
    
    def chat(self, messages: List[Dict[str, str]], task_type: TaskType = None, 
            use_cache: bool = True, **kwargs) -> str:
        """
        Chat with intelligent model selection, caching, and fallback.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            task_type: Optional task type for better model selection.
            use_cache: Whether to use caching for this request.
            **kwargs: Additional parameters to override defaults.
            
        Returns:
            Model's response text.
        """
        # Extract user content for model recommendation and caching
        user_content = " ".join([msg["content"] for msg in messages if msg["role"] == "user"])
        
        # Create a conversation hash for caching (include recent context)
        conversation_text = " ".join([f"{msg['role']}: {msg['content']}" for msg in messages[-3:]])  # Last 3 messages
        
        # Get optimal model for this conversation
        if task_type or len(user_content) > 100:
            recommendations = self.ollama_manager.get_model_recommendations(user_content, task_type)
            selected_model = recommendations["primary_recommendation"]
            fallback_models = recommendations["fallback_options"]
        else:
            selected_model = self.model
            fallback_models = self.ollama_manager.get_fallback_models(
                selected_model, 
                task_type or TaskType.GENERAL
            )
        
        # Merge parameters
        params = self.params.copy()
        params.update(kwargs)
        
        # Create context for caching
        cache_context = {
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 2048),
            "task_type": task_type.value if task_type else None,
            "role": self.role,
            "conversation_length": len(messages)
        }
        
        # Check cache first if enabled (use conversation text as prompt)
        if self.enable_caching and use_cache and self.cache:
            cached_response = self.cache.get(conversation_text, selected_model, cache_context)
            if cached_response:
                logger.debug(f"Cache hit for chat with model {selected_model}")
                return cached_response
        
        # Try primary model first, then fallbacks
        models_to_try = [selected_model] + fallback_models
        last_error = None
        
        for model_name in models_to_try:
            try:
                start_time = time.time()
                
                result = self.client.chat(
                    model=model_name,
                    messages=messages,
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 2048),
                    stop_sequences=params.get("stop_sequences"),
                    stream=params.get("stream", False)
                )
                
                # Record performance
                execution_time = time.time() - start_time
                performance = result.get("performance", {})
                tokens_per_second = performance.get("tokens_per_second", 0)
                
                response_content = result.get("message", {}).get("content", result.get("response", ""))
                quality_score = self._assess_response_quality(response_content)
                
                self.ollama_manager.record_performance(
                    model_name=model_name,
                    task_type=task_type or TaskType.GENERAL,
                    execution_time=execution_time,
                    tokens_per_second=tokens_per_second,
                    success=True,
                    quality_score=quality_score
                )
                
                # Cache the response if caching is enabled and response quality is good
                # Note: Chat responses are cached more conservatively due to context sensitivity
                if (self.enable_caching and use_cache and self.cache and 
                    quality_score >= 7.0 and not params.get("stream", False) and
                    len(messages) <= 5):  # Only cache short conversations
                    
                    # Shorter TTL for chat responses due to context sensitivity
                    ttl_seconds = self._calculate_cache_ttl(task_type, quality_score, execution_time) // 2
                    
                    self.cache.put(
                        prompt=conversation_text,
                        model_name=model_name,
                        response=response_content,
                        metadata={
                            "execution_time": execution_time,
                            "tokens_per_second": tokens_per_second,
                            "quality_score": quality_score,
                            "task_type": task_type.value if task_type else None,
                            "role": self.role,
                            "conversation_length": len(messages),
                            "is_chat": True
                        },
                        context=cache_context,
                        performance_score=quality_score,
                        ttl_seconds=ttl_seconds
                    )
                    
                    logger.debug(f"Cached chat response for model {model_name} with TTL {ttl_seconds}s")
                
                logger.info(f"Successfully completed chat using model {model_name}")
                return response_content
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to chat with model {model_name}: {e}")
                
                # Record failure
                self.ollama_manager.record_performance(
                    model_name=model_name,
                    task_type=task_type or TaskType.GENERAL,
                    execution_time=0,
                    tokens_per_second=0,
                    success=False,
                    quality_score=0
                )
                
                continue
        
        # If all models failed, raise the last error
        raise RuntimeError(f"All models failed. Last error: {last_error}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status information about available models.
        
        Returns:
            Dictionary with model status information.
        """
        status = {
            "current_model": self.model,
            "role": self.role,
            "available_models": list(self.ollama_manager.model_registry.keys()),
            "health_status": {name: info.health_status 
                            for name, info in self.ollama_manager.model_registry.items()},
            "performance_summary": self.ollama_manager.get_performance_summary(),
            "caching_enabled": self.enable_caching,
            "context_management_enabled": self.enable_context_management
        }
        
        # Add cache statistics if caching is enabled
        if self.enable_caching and self.cache:
            cache_stats = self.cache.get_stats()
            status["cache_stats"] = {
                "hit_rate": cache_stats.hit_rate,
                "total_requests": cache_stats.total_requests,
                "cache_size": cache_stats.cache_size,
                "total_size_mb": cache_stats.total_size_bytes / (1024 * 1024),
                "performance_improvement": cache_stats.performance_improvement
            }
        
        # Add context management statistics if enabled
        if self.enable_context_management and self.context_manager:
            all_contexts = self.context_manager.get_all_contexts()
            status["context_stats"] = {
                "active_conversations": len(self._active_conversations),
                "total_contexts": len(all_contexts),
                "max_context_tokens": self.max_context_tokens,
                "context_summaries": all_contexts
            }
        
        return status
    
    def clear_cache(self) -> None:
        """Clear the agent's cache."""
        if self.enable_caching and self.cache:
            self.cache.clear()
            logger.info(f"Cleared cache for {self.role} agent")
    
    def invalidate_model_cache(self, model_name: str) -> int:
        """
        Invalidate cache entries for a specific model.
        
        Args:
            model_name: Name of the model to invalidate cache for.
            
        Returns:
            Number of entries invalidated.
        """
        if self.enable_caching and self.cache:
            count = self.cache.invalidate_by_model(model_name)
            logger.info(f"Invalidated {count} cache entries for model {model_name}")
            return count
        return 0
    
    def optimize_cache(self) -> Dict[str, Any]:
        """
        Optimize the agent's cache performance.
        
        Returns:
            Dictionary with optimization results.
        """
        if self.enable_caching and self.cache:
            return self.cache.optimize()
        return {"message": "Caching not enabled"}
    
    def get_cache_recommendations(self) -> List[str]:
        """
        Get recommendations for cache optimization.
        
        Returns:
            List of recommendation strings.
        """
        if not self.enable_caching or not self.cache:
            return ["Enable caching to get performance benefits"]
        
        stats = self.cache.get_stats()
        recommendations = []
        
        if stats.hit_rate < 0.2:
            recommendations.append("Consider increasing cache TTL or size - low hit rate detected")
        
        if stats.total_size_bytes > self.cache.max_size_bytes * 0.9:
            recommendations.append("Cache is nearly full - consider increasing max size")
        
        if stats.performance_improvement < 0.3:
            recommendations.append("Low performance improvement - review caching strategy")
        
        if stats.total_requests > 100 and stats.hit_rate > 0.7:
            recommendations.append("Excellent cache performance - consider increasing cache size for even better results")
        
        return recommendations or ["Cache performance is optimal"]


# Maintain backward compatibility
AgentInterface = EnhancedAgentInterface


def create_agent(role: str, enable_caching: bool = True, 
                enable_context_management: bool = True,
                max_context_tokens: int = None, **kwargs) -> EnhancedAgentInterface:
    """
    Create an enhanced agent interface for the specified role.
    
    Args:
        role: Agent role (architect, developer, tester, or general).
        enable_caching: Whether to enable intelligent caching.
        enable_context_management: Whether to enable context management.
        max_context_tokens: Maximum tokens for context window.
        **kwargs: Additional parameters for the agent.
        
    Returns:
        Configured EnhancedAgentInterface instance.
    """
    return EnhancedAgentInterface(
        role, 
        enable_caching=enable_caching,
        enable_context_management=enable_context_management,
        max_context_tokens=max_context_tokens,
        **kwargs
    )


def get_model_recommendations(task_description: str, task_type: TaskType = None) -> Dict[str, Any]:
    """
    Get model recommendations for a task (convenience function).
    
    Args:
        task_description: Description of the task.
        task_type: Optional explicit task type.
        
    Returns:
        Dictionary with recommendations and reasoning.
    """
    manager = EnhancedOllamaManager()
    return manager.get_model_recommendations(task_description, task_type)


def health_check_models() -> Dict[str, str]:
    """
    Perform health check on all models (convenience function).
    
    Returns:
        Dictionary mapping model names to health status.
    """
    manager = EnhancedOllamaManager()
    return manager.health_check_all_models()


if __name__ == "__main__":
    # Enhanced example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Ollama Integration Module")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--pull", help="Pull a model")
    parser.add_argument("--test", action="store_true", help="Run a simple test")
    parser.add_argument("--role", default="general", help="Agent role for testing")
    parser.add_argument("--health-check", action="store_true", help="Check health of all models")
    parser.add_argument("--performance", action="store_true", help="Show performance summary")
    parser.add_argument("--recommend", help="Get model recommendation for a task")
    parser.add_argument("--task-type", help="Task type for recommendation", 
                       choices=[t.value for t in TaskType])
    
    args = parser.parse_args()
    
    if args.list_models:
        client = OllamaClient()
        models = client.list_models()
        print("Available models:")
        for model in models:
            print(f"- {model['name']} (Status: {model.get('health_status', 'unknown')})")
    
    elif args.pull:
        client = OllamaClient()
        success = client.pull_model(args.pull)
        print(f"Pull {'successful' if success else 'failed'}")
    
    elif args.health_check:
        print("Performing health check on all models...")
        health_status = health_check_models()
        for model, status in health_status.items():
            print(f"- {model}: {status}")
    
    elif args.performance:
        manager = EnhancedOllamaManager()
        summary = manager.get_performance_summary()
        print("Performance Summary:")
        print(f"- Total requests: {summary.get('total_requests', 0)}")
        print(f"- Average response time: {summary.get('avg_response_time', 0):.2f}s")
        print(f"- Average success rate: {summary.get('avg_success_rate', 0):.1%}")
        print(f"- Average quality score: {summary.get('avg_quality_score', 0):.1f}/10")
    
    elif args.recommend:
        task_type = TaskType(args.task_type) if args.task_type else None
        recommendations = get_model_recommendations(args.recommend, task_type)
        
        print(f"Task: {args.recommend}")
        print(f"Recommended model: {recommendations['primary_recommendation']}")
        print(f"Reasoning: {recommendations['reasoning']}")
        print(f"Fallback options: {', '.join(recommendations['fallback_options'])}")
        print(f"Task characteristics: {recommendations['task_characteristics']}")
    
    elif args.test:
        agent = create_agent(args.role)
        print(f"Testing {args.role} agent with intelligent model routing")
        
        # Test generation with task type
        prompt = "Write a simple Python function to calculate the factorial of a number."
        print(f"\nPrompt: {prompt}")
        response = agent.generate(prompt, task_type=TaskType.CODING)
        print(f"\nResponse:\n{response}")
        
        # Test chat
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What are the key principles of clean code?"}
        ]
        print("\nChat test:")
        response = agent.chat(messages, task_type=TaskType.GENERAL)
        print(f"\nResponse:\n{response}")
        
        # Show model status
        print("\nModel Status:")
        status = agent.get_model_status()
        print(f"Current model: {status['current_model']}")
        print(f"Available models: {len(status['available_models'])}")
        print(f"Health status: {status['health_status']}")
    
    else:
        print("Enhanced Ollama Integration Module")
        print("Use --help to see available options.")
        print("\nNew features:")
        print("- Intelligent model routing based on task characteristics")
        print("- Automatic fallback to alternative models")
        print("- Performance profiling and optimization")
        print("- Health monitoring and recovery")
        print("- Task-specific model recommendations")