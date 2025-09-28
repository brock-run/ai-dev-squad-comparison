"""
Configuration Management System for AI Dev Squad Comparison
This module provides unified configuration loading, validation, and management
across all orchestrator frameworks and system components.
"""
import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LogLevel(str, Enum):
    """Enumeration of supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SandboxType(str, Enum):
    """Enumeration of supported sandbox types."""
    DOCKER = "docker"
    SUBPROCESS = "subprocess"

class VCSProvider(str, Enum):
    """Enumeration of supported VCS providers."""
    GITHUB = "github"
    GITLAB = "gitlab"

class RetryStrategy(str, Enum):
    """Enumeration of retry strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"

# Pydantic Models for Configuration Validation

class ResourceLimits(BaseModel):
    """Resource limits configuration."""
    max_memory_mb: int = Field(default=1024, ge=128, le=32768)
    max_cpu_percent: int = Field(default=80, ge=10, le=100)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)

class NetworkPolicy(BaseModel):
    """Network access policy configuration."""
    default_deny: bool = Field(default=True)
    allowlist: List[str] = Field(default_factory=list)

class FilesystemPolicy(BaseModel):
    """Filesystem access policy configuration."""
    restrict_to_repo: bool = Field(default=True)
    temp_dir_access: bool = Field(default=True)
    system_access: bool = Field(default=False)

class InjectionDetection(BaseModel):
    """Prompt injection detection configuration."""
    enabled: bool = Field(default=True)
    patterns_file: str = Field(default="config/injection_patterns.yaml")

class LLMJudge(BaseModel):
    """LLM judge configuration for output filtering."""
    enabled: bool = Field(default=False)
    model: str = Field(default="llama2:7b")

class SafetyConfig(BaseModel):
    """Safety and security configuration."""
    enabled: bool = Field(default=True)
    sandbox_type: SandboxType = Field(default=SandboxType.DOCKER)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    network_policy: NetworkPolicy = Field(default_factory=NetworkPolicy)
    filesystem_policy: FilesystemPolicy = Field(default_factory=FilesystemPolicy)
    injection_detection: InjectionDetection = Field(default_factory=InjectionDetection)
    llm_judge: LLMJudge = Field(default_factory=LLMJudge)

class RateLimit(BaseModel):
    """Rate limiting configuration."""
    requests_per_hour: int = Field(default=5000, ge=100, le=10000)
    retry_backoff: RetryStrategy = Field(default=RetryStrategy.EXPONENTIAL)

class VCSProviderConfig(BaseModel):
    """VCS provider configuration."""
    enabled: bool = Field(default=True)
    token_env: str = Field(...)
    base_url: str = Field(...)
    rate_limit: RateLimit = Field(default_factory=RateLimit)

class VCSConfig(BaseModel):
    """Version control system configuration."""
    github: Optional[VCSProviderConfig] = None
    gitlab: Optional[VCSProviderConfig] = None

    @root_validator(skip_on_failure=True)
    def at_least_one_provider(cls, values):
        """Ensure at least one VCS provider is configured."""
        github = values.get('github')
        gitlab = values.get('gitlab')
        if not github and not gitlab:
            raise ValueError("At least one VCS provider must be configured")
        return values

class StructuredLogging(BaseModel):
    """Structured logging configuration."""
    enabled: bool = Field(default=True)
    format: str = Field(default="json", pattern="^(json|text)$")
    level: LogLevel = Field(default=LogLevel.INFO)

class OpenTelemetry(BaseModel):
    """OpenTelemetry configuration."""
    enabled: bool = Field(default=True)
    jaeger_endpoint: str = Field(default="http://localhost:14268/api/traces")
    service_name: str = Field(default="ai-dev-squad")

class CostTracking(BaseModel):
    """Cost tracking configuration."""
    enabled: bool = Field(default=True)
    pricing_config: str = Field(default="config/model_pricing.yaml")

class Dashboard(BaseModel):
    """Dashboard configuration."""
    enabled: bool = Field(default=True)
    port: int = Field(default=8050, ge=1024, le=65535)

class ObservabilityConfig(BaseModel):
    """Observability and telemetry configuration."""
    structured_logging: StructuredLogging = Field(default_factory=StructuredLogging)
    opentelemetry: OpenTelemetry = Field(default_factory=OpenTelemetry)
    cost_tracking: CostTracking = Field(default_factory=CostTracking)
    dashboard: Dashboard = Field(default_factory=Dashboard)

class ModelConfig(BaseModel):
    """Model configuration for orchestrators."""
    primary: str = Field(default="codellama:13b")
    fallback: str = Field(default="llama2:7b")

class OrchestratorConfig(BaseModel):
    """Individual orchestrator configuration."""
    enabled: bool = Field(default=True)
    model: ModelConfig = Field(default_factory=ModelConfig)
    timeout_seconds: int = Field(default=1800, ge=300, le=7200)
    version: Optional[str] = None
    language: Optional[str] = None  # For Semantic Kernel
    api_url: Optional[str] = None   # For n8n

class OrchestratorsConfig(BaseModel):
    """Configuration for all orchestrators."""
    langgraph: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    crewai: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    autogen: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    n8n: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    semantic_kernel: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    claude_subagents: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    langroid: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    llamaindex: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    haystack: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    strands: OrchestratorConfig = Field(default_factory=OrchestratorConfig)

class Caching(BaseModel):
    """Caching configuration."""
    enabled: bool = Field(default=True)
    ttl_seconds: int = Field(default=3600, ge=300, le=86400)

class Streaming(BaseModel):
    """Streaming configuration."""
    enabled: bool = Field(default=True)
    chunk_size: int = Field(default=1024, ge=256, le=8192)

class OllamaConfig(BaseModel):
    """Ollama configuration."""
    base_url: str = Field(default="http://localhost:11434")
    models: Dict[str, List[str]] = Field(default_factory=lambda: {
        "code_specialized": ["codellama:13b", "deepseek-coder:6.7b"],
        "general": ["llama2:7b", "mistral:7b"]
    })
    caching: Caching = Field(default_factory=Caching)
    streaming: Streaming = Field(default_factory=Streaming)

class Verification(BaseModel):
    """Benchmark verification configuration."""
    pytest_enabled: bool = Field(default=True)
    linting_enabled: bool = Field(default=True)
    semantic_analysis: bool = Field(default=True)

class SelfConsistency(BaseModel):
    """Self-consistency evaluation configuration."""
    enabled: bool = Field(default=True)
    runs: int = Field(default=5, ge=3, le=10)
    voting_strategy: str = Field(default="majority", pattern="^(majority|consensus)$")

class RecordReplay(BaseModel):
    """Record-replay configuration."""
    enabled: bool = Field(default=True)
    storage_path: str = Field(default="benchmark/recordings")

class BenchmarkConfig(BaseModel):
    """Benchmark configuration."""
    tasks: List[str] = Field(default_factory=lambda: [
        "bugfix", "feature_add", "qa", "optimize", "edge_case"
    ])
    verification: Verification = Field(default_factory=Verification)
    self_consistency: SelfConsistency = Field(default_factory=SelfConsistency)
    record_replay: RecordReplay = Field(default_factory=RecordReplay)

class SystemConfig(BaseModel):
    """Complete system configuration."""
    orchestrators: OrchestratorsConfig = Field(default_factory=OrchestratorsConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    vcs: VCSConfig = Field(default_factory=VCSConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    benchmarks: BenchmarkConfig = Field(default_factory=BenchmarkConfig)

    model_config = {"extra": "forbid", "validate_assignment": True}

@dataclass
class ConfigurationManager:
    """
    Central configuration manager for the AI Dev Squad Comparison platform.
    Handles loading, validation, and management of all system configurations.
    """
    
    config: SystemConfig = field(default_factory=SystemConfig)
    config_file: Optional[str] = None
    _env_overrides: Dict[str, Any] = field(default_factory=dict)
    _cli_overrides: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the configuration manager."""
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = getattr(logging, self.config.observability.structured_logging.level.value)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def load_from_file(self, config_file: str) -> 'ConfigurationManager':
        """
        Load configuration from a YAML file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            Self for method chaining
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML is invalid
            ValueError: If the configuration is invalid
        """
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                config_data = {}
            
            # Apply environment and CLI overrides
            config_data = self._apply_overrides(config_data)
            
            # Validate and create configuration
            self.config = SystemConfig(**config_data)
            self.config_file = config_file
            
            logger.info(f"Configuration loaded from {config_file}")
            return self
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in configuration file {config_file}: {e}")
        except Exception as e:
            raise ValueError(f"Invalid configuration in {config_file}: {e}")
    
    def load_from_env(self, prefix: str = "AI_DEV_SQUAD_") -> 'ConfigurationManager':
        """
        Load configuration overrides from environment variables.
        
        Args:
            prefix: Environment variable prefix
            
        Returns:
            Self for method chaining
        """
        env_overrides = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert environment variable to config path
                config_key = key[len(prefix):].lower().replace('_', '.')
                env_overrides[config_key] = self._parse_env_value(value)
        
        self._env_overrides = env_overrides
        logger.info(f"Loaded {len(env_overrides)} environment overrides")
        return self
    
    def load_from_cli(self, cli_args: Dict[str, Any]) -> 'ConfigurationManager':
        """
        Load configuration overrides from CLI arguments.
        
        Args:
            cli_args: Dictionary of CLI arguments
            
        Returns:
            Self for method chaining
        """
        self._cli_overrides = cli_args.copy()
        logger.info(f"Loaded {len(cli_args)} CLI overrides")
        return self
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value to appropriate type.
        
        Args:
            value: String value from environment
            
        Returns:
            Parsed value (bool, int, float, or string)
        """
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try JSON (for lists/dicts)
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Return as string
        return value
    
    def _apply_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment and CLI overrides to configuration data.
        
        Args:
            config_data: Base configuration data
            
        Returns:
            Configuration data with overrides applied
        """
        # Apply environment overrides
        for key, value in self._env_overrides.items():
            self._set_nested_value(config_data, key, value)
        
        # Apply CLI overrides (higher priority)
        for key, value in self._cli_overrides.items():
            self._set_nested_value(config_data, key, value)
        
        return config_data
    
    def _set_nested_value(self, data: Dict[str, Any], key_path: str, value: Any):
        """
        Set a nested value in a dictionary using dot notation.
        
        Args:
            data: Dictionary to modify
            key_path: Dot-separated key path (e.g., "orchestrators.langgraph.enabled")
            value: Value to set
        """
        keys = key_path.split('.')
        current = data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def get_orchestrator_config(self, orchestrator_name: str) -> OrchestratorConfig:
        """
        Get configuration for a specific orchestrator.
        
        Args:
            orchestrator_name: Name of the orchestrator
            
        Returns:
            Orchestrator configuration
            
        Raises:
            ValueError: If orchestrator is not found
        """
        if not hasattr(self.config.orchestrators, orchestrator_name):
            raise ValueError(f"Unknown orchestrator: {orchestrator_name}")
        
        return getattr(self.config.orchestrators, orchestrator_name)
    
    def is_orchestrator_enabled(self, orchestrator_name: str) -> bool:
        """
        Check if an orchestrator is enabled.
        
        Args:
            orchestrator_name: Name of the orchestrator
            
        Returns:
            True if enabled, False otherwise
        """
        try:
            return self.get_orchestrator_config(orchestrator_name).enabled
        except ValueError:
            return False
    
    def get_enabled_orchestrators(self) -> List[str]:
        """
        Get list of enabled orchestrator names.
        
        Returns:
            List of enabled orchestrator names
        """
        enabled = []
        for name in [
            'langgraph', 'crewai', 'autogen', 'n8n', 'semantic_kernel',
            'claude_subagents', 'langroid', 'llamaindex', 'haystack', 'strands'
        ]:
            if self.is_orchestrator_enabled(name):
                enabled.append(name)
        return enabled
    
    def get_model_for_task(self, task_type: str, orchestrator: str = None) -> str:
        """
        Get the recommended model for a specific task type.
        
        Args:
            task_type: Type of task (bugfix, feature_add, qa, optimize, edge_case)
            orchestrator: Specific orchestrator name (optional)
            
        Returns:
            Model name to use
        """
        # Task-specific model recommendations
        code_tasks = ['bugfix', 'feature_add', 'optimize']
        
        if orchestrator:
            orchestrator_config = self.get_orchestrator_config(orchestrator)
            if task_type in code_tasks:
                return orchestrator_config.model_config.primary
            else:
                return orchestrator_config.model_config.fallback
        
        # Default model selection
        if task_type in code_tasks:
            return self.config.ollama.models['code_specialized'][0]
        else:
            return self.config.ollama.models['general'][0]
    
    def generate_seed(self, base_seed: Optional[int] = None) -> int:
        """
        Generate a seed for reproducible execution.
        
        Args:
            base_seed: Base seed value (optional)
            
        Returns:
            Generated seed
        """
        if base_seed is not None:
            return base_seed
        
        # Generate from current configuration hash for reproducibility
        import hashlib
        config_str = str(self.config.dict())
        hash_obj = hashlib.md5(config_str.encode())
        return int(hash_obj.hexdigest()[:8], 16)
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration and return any warnings.
        
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check if any orchestrators are enabled
        if not self.get_enabled_orchestrators():
            warnings.append("No orchestrators are enabled")
        
        # Check VCS configuration
        if self.config.vcs.github and self.config.vcs.github.enabled:
            if not os.getenv(self.config.vcs.github.token_env):
                warnings.append(f"GitHub token not found in environment variable: {self.config.vcs.github.token_env}")
        
        if self.config.vcs.gitlab and self.config.vcs.gitlab.enabled:
            if not os.getenv(self.config.vcs.gitlab.token_env):
                warnings.append(f"GitLab token not found in environment variable: {self.config.vcs.gitlab.token_env}")
        
        # Check safety configuration files
        if self.config.safety.injection_detection.enabled:
            patterns_file = Path(self.config.safety.injection_detection.patterns_file)
            if not patterns_file.exists():
                warnings.append(f"Injection patterns file not found: {patterns_file}")
        
        # Check cost tracking configuration
        if self.config.observability.cost_tracking.enabled:
            pricing_file = Path(self.config.observability.cost_tracking.pricing_config)
            if not pricing_file.exists():
                warnings.append(f"Model pricing file not found: {pricing_file}")
        
        return warnings
    
    def export_config(self, output_file: str, include_defaults: bool = False):
        """
        Export current configuration to a YAML file.
        
        Args:
            output_file: Path to output file
            include_defaults: Whether to include default values
        """
        config_dict = self.config.dict(exclude_defaults=not include_defaults)
        
        with open(output_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration exported to {output_file}")

# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager() -> ConfigurationManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        Global configuration manager
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager

def load_config(config_file: str = "config/system.yaml", 
                env_prefix: str = "AI_DEV_SQUAD_",
                cli_args: Optional[Dict[str, Any]] = None) -> ConfigurationManager:
    """
    Load system configuration from file, environment, and CLI arguments.
    
    Args:
        config_file: Path to configuration file
        env_prefix: Environment variable prefix
        cli_args: CLI arguments dictionary
        
    Returns:
        Configured ConfigurationManager instance
    """
    global _config_manager
    
    _config_manager = ConfigurationManager()
    
    # Load from file if it exists
    if Path(config_file).exists():
        _config_manager.load_from_file(config_file)
    else:
        logger.warning(f"Configuration file not found: {config_file}, using defaults")
    
    # Load environment overrides
    _config_manager.load_from_env(env_prefix)
    
    # Load CLI overrides
    if cli_args:
        _config_manager.load_from_cli(cli_args)
    
    # Validate configuration
    warnings = _config_manager.validate_configuration()
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
    
    return _config_manager

def create_default_config(output_file: str = "config/system.yaml"):
    """
    Create a default configuration file.
    
    Args:
        output_file: Path to output configuration file
    """
    config_manager = ConfigurationManager()
    config_manager.export_config(output_file, include_defaults=True)
    logger.info(f"Default configuration created at {output_file}")

# Configuration templates for different orchestrators
ORCHESTRATOR_TEMPLATES = {
    'langgraph': {
        'enabled': True,
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    },
    'crewai': {
        'enabled': True,
        'version': 'v2',
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    },
    'autogen': {
        'enabled': True,
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    },
    'n8n': {
        'enabled': True,
        'api_url': 'http://localhost:5678',
        'timeout_seconds': 1800
    },
    'semantic_kernel': {
        'enabled': True,
        'language': 'python',
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    },
    'claude_subagents': {
        'enabled': True,
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    },
    'langroid': {
        'enabled': True,
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    },
    'llamaindex': {
        'enabled': True,
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    },
    'haystack': {
        'enabled': True,
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    },
    'strands': {
        'enabled': True,
        'model_config': {'primary': 'codellama:13b', 'fallback': 'llama2:7b'},
        'timeout_seconds': 1800
    }
}