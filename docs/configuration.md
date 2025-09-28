# Configuration Management System

The AI Dev Squad Comparison platform uses a comprehensive configuration management system that provides unified configuration loading, validation, and management across all orchestrator frameworks and system components.

## Overview

The configuration system supports:
- **YAML-based configuration files** with comprehensive validation
- **Environment variable overrides** for deployment flexibility
- **CLI argument overrides** for runtime customization
- **Pydantic-based validation** with detailed error messages
- **Seed management** for reproducible execution
- **Model preference handling** with task-specific routing

## Configuration Structure

The system configuration is organized into logical sections:

```yaml
orchestrators:     # Framework-specific configurations
safety:           # Security and sandbox settings
vcs:              # Version control integration
observability:    # Telemetry and monitoring
ollama:           # Local model management
benchmarks:       # Evaluation and testing
```

## Quick Start

### 1. Create Default Configuration

```bash
# Create a default configuration file
python -m common.config_cli create

# Or create with custom name
python -m common.config_cli create --output my-config.yaml
```

### 2. Validate Configuration

```bash
# Validate the configuration
python -m common.config_cli validate

# Validate with detailed output
python scripts/validate_config.py --verbose
```

### 3. View Configuration

```bash
# Show full configuration
python -m common.config_cli show

# Show specific section
python -m common.config_cli show --section orchestrators
```

## Configuration File

### Basic Structure

```yaml
# config/system.yaml
orchestrators:
  langgraph:
    enabled: true
    model_config:
      primary: "codellama:13b"
      fallback: "llama2:7b"
    timeout_seconds: 1800

safety:
  enabled: true
  sandbox_type: "docker"
  resource_limits:
    max_memory_mb: 1024
    max_cpu_percent: 80

vcs:
  github:
    enabled: true
    token_env: "GITHUB_TOKEN"
    base_url: "https://api.github.com"
```

### Orchestrator Configuration

Each orchestrator can be individually configured:

```yaml
orchestrators:
  # Standard configuration
  langgraph:
    enabled: true
    model_config:
      primary: "codellama:13b"
      fallback: "llama2:7b"
    timeout_seconds: 1800
  
  # Framework-specific options
  crewai:
    enabled: true
    version: "v2"  # CrewAI-specific
    model_config:
      primary: "codellama:13b"
      fallback: "llama2:7b"
  
  semantic_kernel:
    enabled: true
    language: "python"  # or "csharp"
    model_config:
      primary: "codellama:13b"
      fallback: "llama2:7b"
  
  n8n:
    enabled: true
    api_url: "http://localhost:5678"  # n8n-specific
```

### Safety Configuration

Comprehensive security controls:

```yaml
safety:
  enabled: true
  sandbox_type: "docker"  # or "subprocess"
  
  resource_limits:
    max_memory_mb: 1024
    max_cpu_percent: 80
    timeout_seconds: 300
  
  network_policy:
    default_deny: true
    allowlist:
      - "api.github.com"
      - "gitlab.com"
  
  filesystem_policy:
    restrict_to_repo: true
    temp_dir_access: true
    system_access: false
  
  injection_detection:
    enabled: true
    patterns_file: "config/injection_patterns.yaml"
```

### VCS Configuration

GitHub and GitLab integration:

```yaml
vcs:
  github:
    enabled: true
    token_env: "GITHUB_TOKEN"
    base_url: "https://api.github.com"
    rate_limit:
      requests_per_hour: 5000
      retry_backoff: "exponential"
  
  gitlab:
    enabled: true
    token_env: "GITLAB_TOKEN"
    base_url: "https://gitlab.com/api/v4"
```

## Environment Variable Overrides

Any configuration value can be overridden using environment variables with the format:
`AI_DEV_SQUAD_<SECTION>_<SUBSECTION>_<KEY>`

Examples:
```bash
# Disable LangGraph
export AI_DEV_SQUAD_ORCHESTRATORS_LANGGRAPH_ENABLED=false

# Set custom Ollama URL
export AI_DEV_SQUAD_OLLAMA_BASE_URL=http://custom-ollama:11434

# Increase memory limit
export AI_DEV_SQUAD_SAFETY_RESOURCE_LIMITS_MAX_MEMORY_MB=2048
```

## CLI Argument Overrides

Configuration values can be overridden via CLI arguments:

```bash
# Using the config CLI
python -m common.config_cli set orchestrators.langgraph.enabled=false

# In application code (example)
python benchmark_suite.py --orchestrators.crewai.enabled=false --safety.enabled=true
```

## Configuration Management CLI

The configuration CLI provides comprehensive management tools:

### Create Configuration
```bash
# Create default configuration
python -m common.config_cli create

# Create with custom output
python -m common.config_cli create --output custom-config.yaml --force
```

### Validate Configuration
```bash
# Basic validation
python -m common.config_cli validate

# Validation with warnings as errors
python -m common.config_cli validate --warnings-ok
```

### View Configuration
```bash
# Show full configuration
python -m common.config_cli show

# Show specific section
python -m common.config_cli show --section orchestrators

# Include default values
python -m common.config_cli show --include-defaults
```

### List Orchestrators
```bash
# List all orchestrators
python -m common.config_cli list

# Detailed information
python -m common.config_cli list --verbose
```

### Get/Set Values
```bash
# Get a configuration value
python -m common.config_cli get orchestrators.langgraph.enabled

# Set a configuration value
python -m common.config_cli set orchestrators.langgraph.enabled=false

# Set complex values (YAML format)
python -m common.config_cli set 'orchestrators.langgraph.model_config={"primary": "codellama:7b"}'
```

### View Templates
```bash
# List available templates
python -m common.config_cli template

# Show specific template
python -m common.config_cli template --orchestrator crewai
```

## Programmatic Usage

### Basic Usage

```python
from common.config import load_config, get_config_manager

# Load configuration from file
manager = load_config("config/system.yaml")

# Get orchestrator configuration
langgraph_config = manager.get_orchestrator_config("langgraph")
print(f"LangGraph enabled: {langgraph_config.enabled}")

# Check if orchestrator is enabled
if manager.is_orchestrator_enabled("crewai"):
    print("CrewAI is enabled")

# Get enabled orchestrators
enabled = manager.get_enabled_orchestrators()
print(f"Enabled orchestrators: {enabled}")
```

### Advanced Usage

```python
from common.config import ConfigurationManager

# Create manager with overrides
manager = ConfigurationManager()
manager.load_from_file("config/system.yaml")
manager.load_from_env("AI_DEV_SQUAD_")
manager.load_from_cli({"orchestrators.langgraph.enabled": False})

# Get model for specific task
model = manager.get_model_for_task("bugfix", "langgraph")
print(f"Model for bugfix task: {model}")

# Generate reproducible seed
seed = manager.generate_seed(base_seed=42)
print(f"Generated seed: {seed}")

# Validate configuration
warnings = manager.validate_configuration()
if warnings:
    for warning in warnings:
        print(f"Warning: {warning}")
```

### Configuration in Applications

```python
from common.config import get_config_manager

def main():
    # Get global configuration manager
    config = get_config_manager()
    
    # Use configuration throughout application
    if config.config.safety.enabled:
        print("Safety controls are enabled")
    
    # Get orchestrator-specific settings
    for orchestrator in config.get_enabled_orchestrators():
        orch_config = config.get_orchestrator_config(orchestrator)
        print(f"{orchestrator}: {orch_config.model_config.primary}")
```

## Configuration Validation

The system provides comprehensive validation with detailed error messages:

### Validation Rules

- **Type validation**: Ensures correct data types for all fields
- **Range validation**: Validates numeric ranges (e.g., memory limits, ports)
- **Enum validation**: Validates enumerated values (e.g., log levels, sandbox types)
- **Cross-field validation**: Ensures consistent configuration across sections
- **File existence**: Validates referenced files exist
- **Environment variables**: Checks required environment variables

### Validation Warnings

The system provides warnings for common configuration issues:

- Missing environment variables for VCS tokens
- Missing configuration files (patterns, pricing)
- No enabled orchestrators
- Potentially problematic settings

### Custom Validation

```python
from common.config import ConfigurationManager

manager = ConfigurationManager()
manager.load_from_file("config/system.yaml")

# Run validation
warnings = manager.validate_configuration()

# Handle warnings
for warning in warnings:
    print(f"Configuration warning: {warning}")

# Export validated configuration
manager.export_config("validated-config.yaml")
```

## Best Practices

### 1. Configuration Organization
- Keep environment-specific settings in environment variables
- Use the base configuration file for common settings
- Document all custom configuration changes

### 2. Security
- Store sensitive tokens in environment variables, not configuration files
- Use minimal-scope tokens for VCS integration
- Enable safety controls in production environments

### 3. Performance
- Use appropriate model routing for different task types
- Enable caching for repeated operations
- Configure resource limits based on available hardware

### 4. Monitoring
- Enable structured logging for debugging
- Use OpenTelemetry for distributed tracing
- Monitor cost tracking for budget management

### 5. Validation
- Always validate configuration before deployment
- Use the CLI tools for configuration management
- Test configuration changes in development first

## Troubleshooting

### Common Issues

1. **Configuration file not found**
   ```bash
   python -m common.config_cli create
   ```

2. **Invalid YAML syntax**
   ```bash
   python -m common.config_cli validate --verbose
   ```

3. **Missing environment variables**
   ```bash
   export GITHUB_TOKEN=your_token_here
   export GITLAB_TOKEN=your_token_here
   ```

4. **Validation errors**
   ```bash
   python scripts/validate_config.py --verbose
   ```

### Debug Configuration Loading

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from common.config import load_config
manager = load_config("config/system.yaml")
```

### Reset to Defaults

```bash
# Backup current configuration
cp config/system.yaml config/system.yaml.backup

# Create new default configuration
python -m common.config_cli create --force
```

## Migration Guide

### From Previous Versions

If migrating from a previous configuration format:

1. **Backup existing configuration**
   ```bash
   cp config/system.yaml config/system.yaml.old
   ```

2. **Create new configuration**
   ```bash
   python -m common.config_cli create --output config/system.new.yaml
   ```

3. **Merge settings manually**
   Compare the old and new configurations and merge your custom settings.

4. **Validate new configuration**
   ```bash
   python -m common.config_cli validate --config config/system.new.yaml
   ```

5. **Replace old configuration**
   ```bash
   mv config/system.new.yaml config/system.yaml
   ```

## API Reference

See the inline documentation in `common/config.py` for detailed API reference and examples.