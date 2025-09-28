"""
Unit tests for the Configuration Management System.
These tests validate configuration loading, validation, and management
functionality across all system components.
"""
import pytest
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
from pydantic import ValidationError

from common.config import (
    ConfigurationManager, SystemConfig, SafetyConfig, VCSConfig, 
    ObservabilityConfig, OllamaConfig, BenchmarkConfig,
    OrchestratorConfig, OrchestratorsConfig, VCSProviderConfig,
    ResourceLimits, NetworkPolicy, FilesystemPolicy,
    LogLevel, SandboxType, VCSProvider, RetryStrategy,
    get_config_manager, load_config, create_default_config,
    ORCHESTRATOR_TEMPLATES
)

class TestConfigurationModels:
    """Test cases for Pydantic configuration models."""
    
    def test_resource_limits_validation(self):
        """Test resource limits validation."""
        # Valid configuration
        limits = ResourceLimits(max_memory_mb=2048, max_cpu_percent=90, timeout_seconds=600)
        assert limits.max_memory_mb == 2048
        assert limits.max_cpu_percent == 90
        assert limits.timeout_seconds == 600
        
        # Invalid memory (too low)
        with pytest.raises(ValidationError):
            ResourceLimits(max_memory_mb=64)
        
        # Invalid CPU (too high)
        with pytest.raises(ValidationError):
            ResourceLimits(max_cpu_percent=150)
        
        # Invalid timeout (too low)
        with pytest.raises(ValidationError):
            ResourceLimits(timeout_seconds=10)
    
    def test_network_policy_validation(self):
        """Test network policy validation."""
        policy = NetworkPolicy(default_deny=True, allowlist=["api.github.com", "gitlab.com"])
        assert policy.default_deny is True
        assert len(policy.allowlist) == 2
        assert "api.github.com" in policy.allowlist
    
    def test_safety_config_validation(self):
        """Test safety configuration validation."""
        config = SafetyConfig(
            enabled=True,
            sandbox_type=SandboxType.DOCKER,
            resource_limits=ResourceLimits(),
            network_policy=NetworkPolicy()
        )
        assert config.enabled is True
        assert config.sandbox_type == SandboxType.DOCKER
        assert isinstance(config.resource_limits, ResourceLimits)
        assert isinstance(config.network_policy, NetworkPolicy)
    
    def test_vcs_config_validation(self):
        """Test VCS configuration validation."""
        # Valid configuration with GitHub
        github_config = VCSProviderConfig(
            enabled=True,
            token_env="GITHUB_TOKEN",
            base_url="https://api.github.com"
        )
        vcs_config = VCSConfig(github=github_config)
        assert vcs_config.github.enabled is True
        
        # Invalid configuration (no providers)
        with pytest.raises(ValidationError):
            VCSConfig()
    
    def test_orchestrator_config_validation(self):
        """Test orchestrator configuration validation."""
        config = OrchestratorConfig(
            enabled=True,
            timeout_seconds=1800
        )
        assert config.enabled is True
        assert config.timeout_seconds == 1800
        assert config.model_config.primary == "codellama:13b"  # default
        
        # Invalid timeout (too low)
        with pytest.raises(ValidationError):
            OrchestratorConfig(timeout_seconds=100)
    
    def test_system_config_validation(self):
        """Test complete system configuration validation."""
        # Create minimal valid configuration
        github_config = VCSProviderConfig(
            enabled=True,
            token_env="GITHUB_TOKEN",
            base_url="https://api.github.com"
        )
        vcs_config = VCSConfig(github=github_config)
        
        system_config = SystemConfig(vcs=vcs_config)
        assert isinstance(system_config.orchestrators, OrchestratorsConfig)
        assert isinstance(system_config.safety, SafetyConfig)
        assert isinstance(system_config.vcs, VCSConfig)
        assert isinstance(system_config.observability, ObservabilityConfig)
        assert isinstance(system_config.ollama, OllamaConfig)
        assert isinstance(system_config.benchmarks, BenchmarkConfig)

class TestConfigurationManager:
    """Test cases for ConfigurationManager functionality."""
    
    def test_initialization(self):
        """Test configuration manager initialization."""
        manager = ConfigurationManager()
        assert isinstance(manager.config, SystemConfig)
        assert manager.config_file is None
        assert len(manager._env_overrides) == 0
        assert len(manager._cli_overrides) == 0
    
    def test_load_from_file_success(self):
        """Test successful configuration loading from file."""
        config_data = {
            'vcs': {
                'github': {
                    'enabled': True,
                    'token_env': 'GITHUB_TOKEN',
                    'base_url': 'https://api.github.com'
                }
            },
            'orchestrators': {
                'langgraph': {
                    'enabled': True,
                    'timeout_seconds': 2400
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            manager = ConfigurationManager()
            manager.load_from_file(config_file)
            
            assert manager.config_file == config_file
            assert manager.config.orchestrators.langgraph.timeout_seconds == 2400
            assert manager.config.vcs.github.enabled is True
        finally:
            os.unlink(config_file)
    
    def test_load_from_file_not_found(self):
        """Test configuration loading from non-existent file."""
        manager = ConfigurationManager()
        with pytest.raises(FileNotFoundError):
            manager.load_from_file("non_existent_file.yaml")
    
    def test_load_from_file_invalid_yaml(self):
        """Test configuration loading from invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_file = f.name
        
        try:
            manager = ConfigurationManager()
            with pytest.raises(yaml.YAMLError):
                manager.load_from_file(config_file)
        finally:
            os.unlink(config_file)
    
    def test_load_from_env(self):
        """Test configuration loading from environment variables."""
        env_vars = {
            'AI_DEV_SQUAD_ORCHESTRATORS_LANGGRAPH_ENABLED': 'false',
            'AI_DEV_SQUAD_SAFETY_ENABLED': 'true',
            'AI_DEV_SQUAD_OLLAMA_BASE_URL': 'http://custom:11434'
        }
        
        with patch.dict(os.environ, env_vars):
            manager = ConfigurationManager()
            manager.load_from_env()
            
            assert len(manager._env_overrides) == 3
            assert manager._env_overrides['orchestrators.langgraph.enabled'] is False
            assert manager._env_overrides['safety.enabled'] is True
            assert manager._env_overrides['ollama.base_url'] == 'http://custom:11434'
    
    def test_load_from_cli(self):
        """Test configuration loading from CLI arguments."""
        cli_args = {
            'orchestrators.crewai.enabled': False,
            'benchmarks.self_consistency.runs': 3,
            'observability.dashboard.port': 9000
        }
        
        manager = ConfigurationManager()
        manager.load_from_cli(cli_args)
        
        assert len(manager._cli_overrides) == 3
        assert manager._cli_overrides['orchestrators.crewai.enabled'] is False
        assert manager._cli_overrides['benchmarks.self_consistency.runs'] == 3
    
    def test_parse_env_value(self):
        """Test environment value parsing."""
        manager = ConfigurationManager()
        
        # Boolean values
        assert manager._parse_env_value('true') is True
        assert manager._parse_env_value('false') is False
        assert manager._parse_env_value('True') is True
        assert manager._parse_env_value('FALSE') is False
        
        # Integer values
        assert manager._parse_env_value('42') == 42
        assert manager._parse_env_value('-10') == -10
        
        # Float values
        assert manager._parse_env_value('3.14') == 3.14
        assert manager._parse_env_value('-2.5') == -2.5
        
        # JSON values
        assert manager._parse_env_value('["a", "b", "c"]') == ["a", "b", "c"]
        assert manager._parse_env_value('{"key": "value"}') == {"key": "value"}
        
        # String values
        assert manager._parse_env_value('hello world') == 'hello world'
        assert manager._parse_env_value('') == ''
    
    def test_apply_overrides(self):
        """Test configuration override application."""
        manager = ConfigurationManager()
        manager._env_overrides = {
            'orchestrators.langgraph.enabled': False,
            'safety.enabled': True
        }
        manager._cli_overrides = {
            'orchestrators.langgraph.timeout_seconds': 3600,
            'safety.enabled': False  # CLI should override env
        }
        
        config_data = {
            'orchestrators': {
                'langgraph': {
                    'enabled': True,
                    'timeout_seconds': 1800
                }
            }
        }
        
        result = manager._apply_overrides(config_data)
        
        assert result['orchestrators']['langgraph']['enabled'] is False  # env override
        assert result['orchestrators']['langgraph']['timeout_seconds'] == 3600  # cli override
        assert result['safety']['enabled'] is False  # cli overrides env
    
    def test_get_orchestrator_config(self):
        """Test orchestrator configuration retrieval."""
        manager = ConfigurationManager()
        
        # Valid orchestrator
        config = manager.get_orchestrator_config('langgraph')
        assert isinstance(config, OrchestratorConfig)
        assert config.enabled is True
        
        # Invalid orchestrator
        with pytest.raises(ValueError, match="Unknown orchestrator"):
            manager.get_orchestrator_config('invalid_orchestrator')
    
    def test_is_orchestrator_enabled(self):
        """Test orchestrator enabled check."""
        manager = ConfigurationManager()
        
        # Default enabled orchestrator
        assert manager.is_orchestrator_enabled('langgraph') is True
        
        # Invalid orchestrator
        assert manager.is_orchestrator_enabled('invalid_orchestrator') is False
    
    def test_get_enabled_orchestrators(self):
        """Test getting list of enabled orchestrators."""
        manager = ConfigurationManager()
        enabled = manager.get_enabled_orchestrators()
        
        # All orchestrators should be enabled by default
        expected_orchestrators = [
            'langgraph', 'crewai', 'autogen', 'n8n', 'semantic_kernel',
            'claude_subagents', 'langroid', 'llamaindex', 'haystack', 'strands'
        ]
        
        for orchestrator in expected_orchestrators:
            assert orchestrator in enabled
    
    def test_get_model_for_task(self):
        """Test model selection for different task types."""
        manager = ConfigurationManager()
        
        # Code tasks should use code-specialized models
        code_tasks = ['bugfix', 'feature_add', 'optimize']
        for task in code_tasks:
            model = manager.get_model_for_task(task)
            assert model in manager.config.ollama.models['code_specialized']
        
        # Other tasks should use general models
        other_tasks = ['qa', 'edge_case']
        for task in other_tasks:
            model = manager.get_model_for_task(task)
            assert model in manager.config.ollama.models['general']
        
        # Orchestrator-specific model selection
        model = manager.get_model_for_task('bugfix', 'langgraph')
        langgraph_config = manager.get_orchestrator_config('langgraph')
        assert model == langgraph_config.model_config.primary
    
    def test_generate_seed(self):
        """Test seed generation."""
        manager = ConfigurationManager()
        
        # With base seed
        seed = manager.generate_seed(42)
        assert seed == 42
        
        # Without base seed (should be deterministic based on config)
        seed1 = manager.generate_seed()
        seed2 = manager.generate_seed()
        assert seed1 == seed2  # Should be same for same config
        assert isinstance(seed1, int)
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        manager = ConfigurationManager()
        
        # Should have warnings for missing token environment variables
        warnings = manager.validate_configuration()
        assert len(warnings) > 0
        
        # Check for specific warnings
        warning_messages = ' '.join(warnings)
        assert 'token not found' in warning_messages.lower()
    
    def test_export_config(self):
        """Test configuration export."""
        manager = ConfigurationManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            output_file = f.name
        
        try:
            manager.export_config(output_file)
            
            # Verify file was created and contains valid YAML
            assert Path(output_file).exists()
            with open(output_file, 'r') as f:
                exported_config = yaml.safe_load(f)
            
            assert isinstance(exported_config, dict)
            assert 'orchestrators' in exported_config
            assert 'safety' in exported_config
        finally:
            os.unlink(output_file)

class TestGlobalFunctions:
    """Test cases for global configuration functions."""
    
    def test_get_config_manager(self):
        """Test global configuration manager retrieval."""
        # Reset global state
        import common.config
        common.config._config_manager = None
        
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        # Should return the same instance
        assert manager1 is manager2
        assert isinstance(manager1, ConfigurationManager)
    
    def test_load_config_with_file(self):
        """Test global configuration loading with file."""
        config_data = {
            'vcs': {
                'github': {
                    'enabled': True,
                    'token_env': 'GITHUB_TOKEN',
                    'base_url': 'https://api.github.com'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            manager = load_config(config_file)
            assert isinstance(manager, ConfigurationManager)
            assert manager.config_file == config_file
        finally:
            os.unlink(config_file)
    
    def test_load_config_without_file(self):
        """Test global configuration loading without file."""
        manager = load_config("non_existent_file.yaml")
        assert isinstance(manager, ConfigurationManager)
        assert manager.config_file is None  # Should use defaults
    
    def test_load_config_with_env_and_cli(self):
        """Test global configuration loading with environment and CLI overrides."""
        env_vars = {
            'AI_DEV_SQUAD_SAFETY_ENABLED': 'false'
        }
        cli_args = {
            'orchestrators.langgraph.enabled': False
        }
        
        with patch.dict(os.environ, env_vars):
            manager = load_config(
                config_file="non_existent_file.yaml",
                env_prefix="AI_DEV_SQUAD_",
                cli_args=cli_args
            )
            
            assert isinstance(manager, ConfigurationManager)
            assert len(manager._env_overrides) == 1
            assert len(manager._cli_overrides) == 1
    
    def test_create_default_config(self):
        """Test default configuration creation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            output_file = f.name
        
        try:
            create_default_config(output_file)
            
            # Verify file was created
            assert Path(output_file).exists()
            
            # Verify it contains valid configuration
            with open(output_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            assert isinstance(config_data, dict)
            assert 'orchestrators' in config_data
            assert 'safety' in config_data
            assert 'vcs' in config_data
        finally:
            os.unlink(output_file)

class TestOrchestratorTemplates:
    """Test cases for orchestrator configuration templates."""
    
    def test_orchestrator_templates_exist(self):
        """Test that templates exist for all orchestrators."""
        expected_orchestrators = [
            'langgraph', 'crewai', 'autogen', 'n8n', 'semantic_kernel',
            'claude_subagents', 'langroid', 'llamaindex', 'haystack', 'strands'
        ]
        
        for orchestrator in expected_orchestrators:
            assert orchestrator in ORCHESTRATOR_TEMPLATES
            template = ORCHESTRATOR_TEMPLATES[orchestrator]
            assert 'enabled' in template
            assert isinstance(template['enabled'], bool)
    
    def test_orchestrator_template_structure(self):
        """Test orchestrator template structure."""
        for name, template in ORCHESTRATOR_TEMPLATES.items():
            assert 'enabled' in template
            assert 'timeout_seconds' in template
            
            # Most should have model_config
            if name != 'n8n':  # n8n uses workflows, not direct models
                assert 'model_config' in template
                assert 'primary' in template['model_config']
                assert 'fallback' in template['model_config']

class TestIntegration:
    """Integration tests for the complete configuration system."""
    
    def test_end_to_end_configuration_loading(self):
        """Test complete configuration loading workflow."""
        # Create test configuration file
        config_data = {
            'vcs': {
                'github': {
                    'enabled': True,
                    'token_env': 'GITHUB_TOKEN',
                    'base_url': 'https://api.github.com'
                }
            },
            'orchestrators': {
                'langgraph': {
                    'enabled': True,
                    'timeout_seconds': 2400
                },
                'crewai': {
                    'enabled': False
                }
            },
            'safety': {
                'enabled': True,
                'sandbox_type': 'docker'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        # Set up environment variables
        env_vars = {
            'AI_DEV_SQUAD_ORCHESTRATORS_AUTOGEN_ENABLED': 'false',
            'AI_DEV_SQUAD_SAFETY_RESOURCE_LIMITS_MAX_MEMORY_MB': '2048'
        }
        
        # Set up CLI arguments
        cli_args = {
            'orchestrators.n8n.enabled': False,
            'benchmarks.self_consistency.runs': 7
        }
        
        try:
            with patch.dict(os.environ, env_vars):
                manager = load_config(
                    config_file=config_file,
                    env_prefix="AI_DEV_SQUAD_",
                    cli_args=cli_args
                )
                
                # Verify file configuration
                assert manager.config.orchestrators.langgraph.timeout_seconds == 2400
                assert manager.config.orchestrators.crewai.enabled is False
                assert manager.config.safety.enabled is True
                
                # Verify environment overrides
                assert manager.config.orchestrators.autogen.enabled is False
                assert manager.config.safety.resource_limits.max_memory_mb == 2048
                
                # Verify CLI overrides
                assert manager.config.orchestrators.n8n.enabled is False
                assert manager.config.benchmarks.self_consistency.runs == 7
                
                # Test utility functions
                enabled_orchestrators = manager.get_enabled_orchestrators()
                assert 'langgraph' in enabled_orchestrators
                assert 'crewai' not in enabled_orchestrators
                assert 'autogen' not in enabled_orchestrators
                assert 'n8n' not in enabled_orchestrators
                
                # Test model selection
                model = manager.get_model_for_task('bugfix', 'langgraph')
                assert model == manager.config.orchestrators.langgraph.model_config.primary
                
        finally:
            os.unlink(config_file)

if __name__ == "__main__":
    pytest.main([__file__])