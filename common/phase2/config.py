"""Phase 2 Configuration Management

This module provides configuration management for Phase 2 AI mismatch resolution,
including AI service settings, resolution policies, and runtime parameters.

All configuration is validated and provides sensible defaults for different environments.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import (
    MismatchType,
    SafetyLevel,
    ResolutionActionType,
    EquivalenceMethod,
    ArtifactType,
    Environment
)


logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI service providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    LOCAL_LLM = "local_llm"


class CacheBackend(Enum):
    """Supported cache backends."""
    REDIS = "redis"
    MEMORY = "memory"
    DISK = "disk"
    DISABLED = "disabled"


@dataclass
class AIServiceConfig:
    """Configuration for AI service providers."""
    
    provider: AIProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30
    max_retries: int = 3
    rate_limit_rpm: int = 60
    cost_per_token: float = 0.0001
    enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider in {AIProvider.OPENAI, AIProvider.ANTHROPIC} and not self.api_key:
            raise ValueError(f"{self.provider.value} requires an API key")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if self.max_tokens < 1 or self.max_tokens > 32000:
            raise ValueError("Max tokens must be between 1 and 32000")


@dataclass
class CacheConfig:
    """Configuration for caching system."""
    
    backend: CacheBackend = CacheBackend.REDIS
    redis_url: str = "redis://localhost:6379/0"
    memory_max_size: int = 1000
    disk_cache_dir: str = "./cache/phase2"
    default_ttl: int = 3600  # 1 hour
    max_key_size: int = 1024
    compression: bool = True
    enabled: bool = True
    
    def __post_init__(self):
        """Validate cache configuration."""
        if self.backend == CacheBackend.DISK:
            Path(self.disk_cache_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class SecurityConfig:
    """Security and privacy configuration."""
    
    redaction_enabled: bool = True
    redaction_patterns: List[str] = field(default_factory=lambda: [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card
        r'\b[A-Z0-9]{20,}\b',  # API keys (heuristic)
    ])
    audit_logging: bool = True
    audit_log_path: str = "./logs/phase2/audit.log"
    max_ai_request_size: int = 1024 * 1024  # 1MB
    require_approval_for_destructive: bool = True
    dual_key_approval_required: bool = False
    
    def __post_init__(self):
        """Validate security configuration."""
        if self.audit_logging:
            Path(self.audit_log_path).parent.mkdir(parents=True, exist_ok=True)


class ResolutionPolicyConfig(BaseModel):
    """Configuration for resolution policies by environment and mismatch type."""
    
    environment: Environment = Field(..., description="Target environment")
    mismatch_type: MismatchType = Field(..., description="Mismatch type")
    allowed_actions: List[ResolutionActionType] = Field(..., description="Allowed resolution actions")
    safety_level: SafetyLevel = Field(..., description="Required safety level")
    confidence_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Minimum confidence threshold")
    auto_apply_enabled: bool = Field(False, description="Whether auto-apply is enabled")
    dual_key_required: bool = Field(False, description="Whether dual-key approval is required")
    
    @model_validator(mode='after')
    def validate_confidence_threshold(self):
        """Adjust confidence threshold based on environment."""
        if self.environment == Environment.PRODUCTION:
            self.confidence_threshold = max(self.confidence_threshold, 0.9)  # Higher threshold for production
        elif self.environment == Environment.DEVELOPMENT:
            self.confidence_threshold = max(self.confidence_threshold, 0.7)  # Lower threshold for development
        return self


class EquivalenceConfig(BaseModel):
    """Configuration for equivalence detection methods."""
    
    artifact_type: ArtifactType = Field(..., description="Artifact type")
    methods: List[EquivalenceMethod] = Field(..., description="Enabled equivalence methods")
    cosine_similarity_threshold: float = Field(0.86, ge=0.0, le=1.0, description="Cosine similarity threshold")
    llm_judge_prompt_id: str = Field("semantic_equivalence_v1", description="LLM judge prompt ID")
    ast_normalization_enabled: bool = Field(True, description="Whether AST normalization is enabled")
    test_execution_timeout: int = Field(30, ge=1, le=300, description="Test execution timeout in seconds")
    
    @field_validator('methods')
    @classmethod
    def validate_methods(cls, v):
        """Ensure at least one method is enabled."""
        if not v:
            raise ValueError("At least one equivalence method must be enabled")
        return v


class LearningConfig(BaseModel):
    """Configuration for learning and pattern recognition."""
    
    enabled: bool = Field(True, description="Whether learning is enabled")
    pattern_storage_backend: str = Field("vector_db", description="Pattern storage backend")
    vector_db_url: str = Field("http://localhost:8080", description="Vector database URL")
    embedding_model: str = Field("text-embedding-ada-002", description="Embedding model")
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Pattern similarity threshold")
    min_pattern_usage: int = Field(5, ge=1, description="Minimum usage before pattern is considered reliable")
    learning_rate: float = Field(0.1, ge=0.01, le=1.0, description="Learning rate for pattern updates")
    max_patterns_per_type: int = Field(1000, ge=10, description="Maximum patterns to store per mismatch type")
    
    @field_validator('learning_rate')
    @classmethod
    def validate_learning_rate(cls, v):
        """Ensure learning rate is reasonable."""
        if v > 0.5:
            logger.warning(f"Learning rate {v} is quite high, consider using a lower value")
        return v


class PerformanceConfig(BaseModel):
    """Configuration for performance optimization."""
    
    batch_size: int = Field(10, ge=1, le=100, description="Batch processing size")
    max_concurrent_analyses: int = Field(5, ge=1, le=20, description="Maximum concurrent AI analyses")
    analysis_timeout: int = Field(300, ge=30, le=1800, description="Analysis timeout in seconds")
    cache_analysis_results: bool = Field(True, description="Whether to cache analysis results")
    enable_parallel_processing: bool = Field(True, description="Whether to enable parallel processing")
    memory_limit_mb: int = Field(1024, ge=256, description="Memory limit in MB")
    
    @field_validator('max_concurrent_analyses')
    @classmethod
    def validate_concurrency(cls, v):
        """Warn about high concurrency settings."""
        if v > 10:
            logger.warning(f"High concurrency setting ({v}) may impact performance")
        return v


class Phase2Config(BaseModel):
    """Main configuration class for Phase 2 AI mismatch resolution."""
    
    # Core settings
    environment: Environment = Field(Environment.DEVELOPMENT, description="Deployment environment")
    debug: bool = Field(False, description="Enable debug mode")
    log_level: str = Field("INFO", description="Logging level")
    
    # AI service configuration
    ai_services: Dict[str, AIServiceConfig] = Field(default_factory=dict, description="AI service configurations")
    primary_ai_service: str = Field("openai", description="Primary AI service to use")
    fallback_ai_service: Optional[str] = Field(None, description="Fallback AI service")
    
    # Cache configuration
    cache: CacheConfig = Field(default_factory=CacheConfig, description="Cache configuration")
    
    # Security configuration
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="Security configuration")
    
    # Resolution policies
    resolution_policies: List[ResolutionPolicyConfig] = Field(default_factory=list, description="Resolution policies")
    
    # Equivalence configuration
    equivalence_configs: List[EquivalenceConfig] = Field(default_factory=list, description="Equivalence configurations")
    
    # Learning configuration
    learning: LearningConfig = Field(default_factory=LearningConfig, description="Learning configuration")
    
    # Performance configuration
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig, description="Performance configuration")
    
    # Database configuration
    database_url: str = Field("postgresql://localhost:5432/ai_dev_squad", description="Database connection URL")
    database_pool_size: int = Field(20, ge=5, le=100, description="Database connection pool size")
    
    @model_validator(mode='after')
    def validate_ai_services(self):
        """Validate AI service configuration."""
        if self.primary_ai_service and self.primary_ai_service not in self.ai_services:
            raise ValueError(f"Primary AI service '{self.primary_ai_service}' not found in ai_services")
        
        if self.fallback_ai_service and self.fallback_ai_service not in self.ai_services:
            raise ValueError(f"Fallback AI service '{self.fallback_ai_service}' not found in ai_services")
        
        return self
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    def get_ai_service(self, service_name: Optional[str] = None) -> Optional[AIServiceConfig]:
        """Get AI service configuration by name."""
        if service_name is None:
            service_name = self.primary_ai_service
        
        return self.ai_services.get(service_name)
    
    def get_resolution_policy(self, mismatch_type: Union[MismatchType, str], environment: Optional[Environment] = None) -> Optional[ResolutionPolicyConfig]:
        """Get resolution policy for mismatch type and environment."""
        if environment is None:
            environment = self.environment
        
        # Handle both enum and string values
        if isinstance(mismatch_type, str):
            mismatch_type = MismatchType(mismatch_type)
        
        for policy in self.resolution_policies:
            if policy.mismatch_type == mismatch_type and policy.environment == environment:
                return policy
        
        return None
    
    def get_equivalence_config(self, artifact_type: ArtifactType) -> Optional[EquivalenceConfig]:
        """Get equivalence configuration for artifact type."""
        for config in self.equivalence_configs:
            if config.artifact_type == artifact_type:
                return config
        
        return None
    
    def is_action_allowed(self, mismatch_type: MismatchType, action: ResolutionActionType, environment: Optional[Environment] = None) -> bool:
        """Check if an action is allowed for a mismatch type in the given environment."""
        policy = self.get_resolution_policy(mismatch_type, environment)
        if not policy:
            return False
        
        return action in policy.allowed_actions
    
    def requires_approval(self, mismatch_type: MismatchType, environment: Optional[Environment] = None) -> bool:
        """Check if a mismatch type requires approval in the given environment."""
        policy = self.get_resolution_policy(mismatch_type, environment)
        if not policy:
            return True  # Default to requiring approval
        
        return policy.safety_level in {SafetyLevel.ADVISORY, SafetyLevel.EXPERIMENTAL}


def load_config(config_path: Optional[str] = None) -> Phase2Config:
    """Load Phase 2 configuration from file or environment variables."""
    
    # Default configuration paths
    if config_path is None:
        config_paths = [
            "config/phase2_runtime.yaml",
            "/etc/ai-dev-squad/phase2.yaml",
            os.path.expanduser("~/.ai-dev-squad/phase2.yaml")
        ]
        
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break
    
    # Load from file if available
    config_data = {}
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
    
    # Override with environment variables
    env_overrides = _load_env_overrides()
    config_data.update(env_overrides)
    
    # Create configuration with defaults
    try:
        config = Phase2Config(**config_data)
        logger.info(f"Phase 2 configuration loaded successfully for environment: {config.environment.value}")
        return config
    except Exception as e:
        logger.error(f"Failed to create configuration: {e}")
        # Return default configuration
        return Phase2Config()


def _load_env_overrides() -> Dict[str, Any]:
    """Load configuration overrides from environment variables."""
    overrides = {}
    
    # Environment
    if env_val := os.getenv('PHASE2_ENVIRONMENT'):
        try:
            overrides['environment'] = Environment(env_val.lower())
        except ValueError:
            logger.warning(f"Invalid environment value: {env_val}")
    
    # Debug mode
    if env_val := os.getenv('PHASE2_DEBUG'):
        overrides['debug'] = env_val.lower() in {'true', '1', 'yes', 'on'}
    
    # Log level
    if env_val := os.getenv('PHASE2_LOG_LEVEL'):
        overrides['log_level'] = env_val.upper()
    
    # Database URL
    if env_val := os.getenv('PHASE2_DATABASE_URL'):
        overrides['database_url'] = env_val
    
    # Primary AI service
    if env_val := os.getenv('PHASE2_PRIMARY_AI_SERVICE'):
        overrides['primary_ai_service'] = env_val
    
    # AI service API keys
    ai_services = {}
    for provider in AIProvider:
        env_key = f'PHASE2_{provider.value.upper()}_API_KEY'
        if api_key := os.getenv(env_key):
            service_config = AIServiceConfig(
                provider=provider,
                api_key=api_key
            )
            ai_services[provider.value] = service_config
    
    if ai_services:
        overrides['ai_services'] = ai_services
    
    return overrides


def create_default_config(environment: Environment = Environment.DEVELOPMENT) -> Phase2Config:
    """Create a default configuration for the specified environment."""
    
    # Default AI services
    ai_services = {
        "openai": AIServiceConfig(
            provider=AIProvider.OPENAI,
            model="gpt-3.5-turbo",
            api_key=os.getenv('OPENAI_API_KEY'),
            enabled=bool(os.getenv('OPENAI_API_KEY'))
        ),
        "ollama": AIServiceConfig(
            provider=AIProvider.OLLAMA,
            base_url="http://localhost:11434",
            model="llama3.1:8b",
            enabled=True
        )
    }
    
    # Default resolution policies
    resolution_policies = []
    
    # Safe policies for all environments
    for env in Environment:
        # Whitespace - safe for auto-resolution
        resolution_policies.append(ResolutionPolicyConfig(
            environment=env,
            mismatch_type=MismatchType.WHITESPACE,
            allowed_actions=[ResolutionActionType.NORMALIZE_WHITESPACE],
            safety_level=SafetyLevel.AUTOMATIC,
            confidence_threshold=0.9,
            auto_apply_enabled=(env != Environment.PRODUCTION)
        ))
        
        # JSON ordering - safe for auto-resolution
        resolution_policies.append(ResolutionPolicyConfig(
            environment=env,
            mismatch_type=MismatchType.JSON_ORDERING,
            allowed_actions=[ResolutionActionType.CANONICALIZE_JSON],
            safety_level=SafetyLevel.AUTOMATIC,
            confidence_threshold=0.9,
            auto_apply_enabled=(env != Environment.PRODUCTION)
        ))
        
        # Semantic text - requires approval
        resolution_policies.append(ResolutionPolicyConfig(
            environment=env,
            mismatch_type=MismatchType.SEMANTICS_TEXT,
            allowed_actions=[ResolutionActionType.REWRITE_FORMATTING, ResolutionActionType.IGNORE_MISMATCH],
            safety_level=SafetyLevel.EXPERIMENTAL,
            confidence_threshold=0.95,
            auto_apply_enabled=False,
            dual_key_required=(env == Environment.PRODUCTION)
        ))
    
    # Default equivalence configurations
    equivalence_configs = [
        EquivalenceConfig(
            artifact_type=ArtifactType.TEXT,
            methods=[EquivalenceMethod.EXACT, EquivalenceMethod.COSINE_SIMILARITY]
        ),
        EquivalenceConfig(
            artifact_type=ArtifactType.JSON,
            methods=[EquivalenceMethod.EXACT, EquivalenceMethod.CANONICAL_JSON]
        ),
        EquivalenceConfig(
            artifact_type=ArtifactType.CODE,
            methods=[EquivalenceMethod.EXACT, EquivalenceMethod.AST_NORMALIZED]
        )
    ]
    
    return Phase2Config(
        environment=environment,
        ai_services=ai_services,
        primary_ai_service="ollama",
        fallback_ai_service="openai",
        resolution_policies=resolution_policies,
        equivalence_configs=equivalence_configs
    )


def save_config(config: Phase2Config, config_path: str) -> bool:
    """Save configuration to file."""
    try:
        # Convert to dictionary
        config_dict = config.dict()
        
        # Convert AI service configs to dictionaries
        if 'ai_services' in config_dict:
            ai_services_dict = {}
            for name, service_config in config_dict['ai_services'].items():
                if isinstance(service_config, AIServiceConfig):
                    ai_services_dict[name] = service_config.__dict__
                else:
                    ai_services_dict[name] = service_config
            config_dict['ai_services'] = ai_services_dict
        
        # Ensure directory exists
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to YAML file
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save configuration to {config_path}: {e}")
        return False


if __name__ == "__main__":
    # Test configuration loading and validation
    print("🧪 Testing Phase 2 configuration management...")
    
    try:
        # Test default configuration
        config = create_default_config(Environment.DEVELOPMENT)
        print(f"✅ Created default configuration for {config.environment.value}")
        
        # Test AI service access
        ai_service = config.get_ai_service("ollama")
        if ai_service:
            print(f"✅ Retrieved AI service: {ai_service.provider.value}")
        
        # Test resolution policy lookup
        policy = config.get_resolution_policy(MismatchType.WHITESPACE)
        if policy:
            print(f"✅ Retrieved resolution policy: {policy.safety_level.value}")
        
        # Test action permission check
        allowed = config.is_action_allowed(MismatchType.WHITESPACE, ResolutionActionType.NORMALIZE_WHITESPACE)
        print(f"✅ Action permission check: {allowed}")
        
        # Test configuration serialization
        config_dict = config.model_dump()
        print(f"✅ Configuration serialization successful")
        
        print("\\n🎉 Phase 2 configuration management working correctly!")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()