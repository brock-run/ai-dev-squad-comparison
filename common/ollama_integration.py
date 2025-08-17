#!/usr/bin/env python3
"""
Ollama Integration Module for AI Dev Squad Comparison

This module provides a common interface for interacting with Ollama across all framework
implementations. It handles model management, inference, and performance tracking.
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ollama_integration")

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: Base URL for the Ollama API. If None, uses the OLLAMA_BASE_URL
                      environment variable or defaults to http://localhost:11434.
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.api_url = f"{self.base_url}/api"
        self._check_connection()
    
    def _check_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            True if connection is successful, raises an exception otherwise.
        """
        try:
            response = requests.get(f"{self.api_url}/tags")
            response.raise_for_status()
            logger.info(f"Successfully connected to Ollama at {self.base_url}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            raise ConnectionError(f"Could not connect to Ollama at {self.base_url}. "
                                 "Make sure Ollama is running and accessible.")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models.
        
        Returns:
            List of model information dictionaries.
        """
        response = requests.get(f"{self.api_url}/tags")
        response.raise_for_status()
        return response.json().get("models", [])
    
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
                stop_sequences: List[str] = None) -> Dict[str, Any]:
        """
        Generate text using the specified model.
        
        Args:
            model: Name of the model to use.
            prompt: The prompt to generate from.
            system_prompt: Optional system prompt for chat models.
            temperature: Sampling temperature (higher is more creative, lower is more deterministic).
            max_tokens: Maximum number of tokens to generate.
            stop_sequences: Optional list of sequences that will stop generation when encountered.
            
        Returns:
            Dictionary containing the generated text and metadata.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if stop_sequences:
            payload["stop"] = stop_sequences
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Add performance metrics
            result["performance"] = {
                "execution_time_seconds": time.time() - start_time,
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
            }
            
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating text with model {model}: {e}")
            raise
    
    def chat(self,
            model: str,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: int = 2048,
            stop_sequences: List[str] = None) -> Dict[str, Any]:
        """
        Chat with the specified model.
        
        Args:
            model: Name of the model to use.
            messages: List of message dictionaries with 'role' and 'content' keys.
                     Roles can be 'system', 'user', or 'assistant'.
            temperature: Sampling temperature.
            max_tokens: Maximum number of tokens to generate.
            stop_sequences: Optional list of sequences that will stop generation when encountered.
            
        Returns:
            Dictionary containing the chat response and metadata.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        
        if stop_sequences:
            payload["stop"] = stop_sequences
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/chat",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Add performance metrics
            result["performance"] = {
                "execution_time_seconds": time.time() - start_time,
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
            }
            
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in chat with model {model}: {e}")
            raise


class OllamaManager:
    """Manager for Ollama models and configurations."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Ollama manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses default locations.
        """
        self.client = OllamaClient()
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "ollama_config.json"
        )
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.
        
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
        
        # Default configuration
        default_config = {
            "default_models": {
                "architect": "codellama:13b",
                "developer": "codellama:13b",
                "tester": "llama3.1:8b",
                "general": "llama3.1:8b"
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
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
        
        return success
    
    def get_model_for_role(self, role: str) -> str:
        """
        Get the appropriate model for a specific agent role.
        
        Args:
            role: Agent role (architect, developer, tester, or general).
            
        Returns:
            Model name for the specified role.
        """
        return self.config["default_models"].get(role, self.config["default_models"]["general"])
    
    def get_parameters(self, custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get generation parameters, optionally overriding defaults with custom values.
        
        Args:
            custom_params: Custom parameters to override defaults.
            
        Returns:
            Dictionary of parameters.
        """
        params = self.config["parameters"].copy()
        if custom_params:
            params.update(custom_params)
        return params


class AgentInterface:
    """Interface for AI agents to interact with Ollama."""
    
    def __init__(self, role: str, ollama_manager: OllamaManager = None):
        """
        Initialize the agent interface.
        
        Args:
            role: Agent role (architect, developer, tester, or general).
            ollama_manager: Optional OllamaManager instance. If None, creates a new one.
        """
        self.role = role
        self.ollama_manager = ollama_manager or OllamaManager()
        self.model = self.ollama_manager.get_model_for_role(role)
        self.params = self.ollama_manager.get_parameters()
        self.client = self.ollama_manager.client
        
        # Ensure model is available
        self.ollama_manager.ensure_models_available([self.model])
    
    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """
        Generate text using the agent's model.
        
        Args:
            prompt: The prompt to generate from.
            system_prompt: Optional system prompt.
            **kwargs: Additional parameters to override defaults.
            
        Returns:
            Generated text.
        """
        params = self.params.copy()
        params.update(kwargs)
        
        result = self.client.generate(
            model=self.model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 2048),
            stop_sequences=params.get("stop_sequences")
        )
        
        return result["response"]
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Chat with the agent's model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            **kwargs: Additional parameters to override defaults.
            
        Returns:
            Model's response text.
        """
        params = self.params.copy()
        params.update(kwargs)
        
        result = self.client.chat(
            model=self.model,
            messages=messages,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 2048),
            stop_sequences=params.get("stop_sequences")
        )
        
        return result["message"]["content"]


def create_agent(role: str, **kwargs) -> AgentInterface:
    """
    Create an agent interface for the specified role.
    
    Args:
        role: Agent role (architect, developer, tester, or general).
        **kwargs: Additional parameters for the agent.
        
    Returns:
        Configured AgentInterface instance.
    """
    return AgentInterface(role, **kwargs)


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama Integration Module")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--pull", help="Pull a model")
    parser.add_argument("--test", action="store_true", help="Run a simple test")
    parser.add_argument("--role", default="general", help="Agent role for testing")
    
    args = parser.parse_args()
    
    if args.list_models:
        client = OllamaClient()
        models = client.list_models()
        print("Available models:")
        for model in models:
            print(f"- {model['name']}")
    
    elif args.pull:
        client = OllamaClient()
        success = client.pull_model(args.pull)
        print(f"Pull {'successful' if success else 'failed'}")
    
    elif args.test:
        agent = create_agent(args.role)
        print(f"Testing {args.role} agent with model {agent.model}")
        
        # Test generation
        prompt = "Write a simple Python function to calculate the factorial of a number."
        print(f"\nPrompt: {prompt}")
        response = agent.generate(prompt)
        print(f"\nResponse:\n{response}")
        
        # Test chat
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What are the key principles of clean code?"}
        ]
        print("\nChat test:")
        response = agent.chat(messages)
        print(f"\nResponse:\n{response}")
    
    else:
        print("No action specified. Use --help to see available options.")