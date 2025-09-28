#!/usr/bin/env python3
"""
Configuration Management CLI for AI Dev Squad Comparison
This utility provides command-line tools for managing system configuration.
"""
import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from common.config import (
    ConfigurationManager, load_config, create_default_config,
    get_config_manager, ORCHESTRATOR_TEMPLATES
)

def create_config_command(args):
    """Create a new configuration file."""
    output_file = args.output or "config/system.yaml"
    
    # Ensure directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    if Path(output_file).exists() and not args.force:
        print(f"Configuration file already exists: {output_file}")
        print("Use --force to overwrite")
        return 1
    
    create_default_config(output_file)
    print(f"Default configuration created: {output_file}")
    return 0

def validate_config_command(args):
    """Validate a configuration file."""
    config_file = args.config or "config/system.yaml"
    
    if not Path(config_file).exists():
        print(f"Configuration file not found: {config_file}")
        return 1
    
    try:
        manager = load_config(config_file)
        warnings = manager.validate_configuration()
        
        print(f"Configuration validation for: {config_file}")
        print("=" * 50)
        
        if not warnings:
            print("✅ Configuration is valid with no warnings")
            return 0
        else:
            print(f"⚠️  Configuration has {len(warnings)} warnings:")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
            return 0 if args.warnings_ok else 1
            
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return 1

def show_config_command(args):
    """Show current configuration."""
    config_file = args.config or "config/system.yaml"
    
    try:
        manager = load_config(config_file)
        
        if args.section:
            # Show specific section
            section_data = getattr(manager.config, args.section, None)
            if section_data is None:
                print(f"Configuration section not found: {args.section}")
                return 1
            
            print(f"Configuration section: {args.section}")
            print("=" * 50)
            print(yaml.dump(section_data.dict(), default_flow_style=False, indent=2))
        else:
            # Show full configuration
            print(f"Full configuration from: {config_file or 'defaults'}")
            print("=" * 50)
            config_dict = manager.config.dict(exclude_defaults=not args.include_defaults)
            print(yaml.dump(config_dict, default_flow_style=False, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1

def list_orchestrators_command(args):
    """List available orchestrators and their status."""
    config_file = args.config or "config/system.yaml"
    
    try:
        manager = load_config(config_file) if Path(config_file).exists() else ConfigurationManager()
        
        print("Available Orchestrators")
        print("=" * 50)
        
        orchestrator_names = [
            'langgraph', 'crewai', 'autogen', 'n8n', 'semantic_kernel',
            'claude_subagents', 'langroid', 'llamaindex', 'haystack', 'strands'
        ]
        
        for name in orchestrator_names:
            try:
                config = manager.get_orchestrator_config(name)
                status = "✅ Enabled" if config.enabled else "❌ Disabled"
                timeout = config.timeout_seconds
                primary_model = config.model_config.primary if hasattr(config.model_config, 'primary') else "N/A"
                
                print(f"{name:20} {status:12} Timeout: {timeout:4}s Model: {primary_model}")
                
                if args.verbose:
                    print(f"  Fallback Model: {getattr(config.model_config, 'fallback', 'N/A')}")
                    if hasattr(config, 'version') and config.version:
                        print(f"  Version: {config.version}")
                    if hasattr(config, 'language') and config.language:
                        print(f"  Language: {config.language}")
                    if hasattr(config, 'api_url') and config.api_url:
                        print(f"  API URL: {config.api_url}")
                    print()
                    
            except Exception as e:
                print(f"{name:20} ❌ Error: {e}")
        
        if not args.verbose:
            print("\nUse --verbose for detailed information")
        
        return 0
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1

def set_config_command(args):
    """Set a configuration value."""
    config_file = args.config or "config/system.yaml"
    
    # Load existing configuration or create new one
    if Path(config_file).exists():
        try:
            manager = load_config(config_file)
        except Exception as e:
            print(f"Error loading existing configuration: {e}")
            return 1
    else:
        manager = ConfigurationManager()
        print(f"Creating new configuration file: {config_file}")
    
    # Parse the key-value pair
    if '=' not in args.key_value:
        print("Key-value pair must be in format: key=value")
        return 1
    
    key, value = args.key_value.split('=', 1)
    
    # Parse value
    try:
        # Try to parse as YAML for complex values
        parsed_value = yaml.safe_load(value)
    except yaml.YAMLError:
        # Use as string if YAML parsing fails
        parsed_value = value
    
    # Apply the change
    try:
        config_dict = manager.config.dict()
        manager._set_nested_value(config_dict, key, parsed_value)
        
        # Validate the new configuration
        from common.config import SystemConfig
        new_config = SystemConfig(**config_dict)
        manager.config = new_config
        
        # Save to file
        Path(config_file).parent.mkdir(parents=True, exist_ok=True)
        manager.export_config(config_file)
        
        print(f"Configuration updated: {key} = {parsed_value}")
        print(f"Saved to: {config_file}")
        
        return 0
        
    except Exception as e:
        print(f"Error updating configuration: {e}")
        return 1

def get_config_command(args):
    """Get a configuration value."""
    config_file = args.config or "config/system.yaml"
    
    try:
        manager = load_config(config_file) if Path(config_file).exists() else ConfigurationManager()
        
        # Navigate to the requested key
        keys = args.key.split('.')
        current = manager.config.dict()
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                print(f"Configuration key not found: {args.key}")
                return 1
        
        print(f"{args.key}: {current}")
        return 0
        
    except Exception as e:
        print(f"Error getting configuration value: {e}")
        return 1

def template_command(args):
    """Show orchestrator configuration templates."""
    if args.orchestrator:
        if args.orchestrator not in ORCHESTRATOR_TEMPLATES:
            print(f"Unknown orchestrator: {args.orchestrator}")
            print(f"Available orchestrators: {', '.join(ORCHESTRATOR_TEMPLATES.keys())}")
            return 1
        
        print(f"Configuration template for: {args.orchestrator}")
        print("=" * 50)
        template = ORCHESTRATOR_TEMPLATES[args.orchestrator]
        print(yaml.dump({args.orchestrator: template}, default_flow_style=False, indent=2))
    else:
        print("Available orchestrator templates:")
        print("=" * 50)
        for name in sorted(ORCHESTRATOR_TEMPLATES.keys()):
            print(f"  {name}")
        print("\nUse --orchestrator <name> to see specific template")
    
    return 0

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Configuration Management CLI for AI Dev Squad Comparison",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create                           # Create default config
  %(prog)s create --output my-config.yaml  # Create config with custom name
  %(prog)s validate                         # Validate current config
  %(prog)s show                             # Show full configuration
  %(prog)s show --section orchestrators    # Show orchestrators section
  %(prog)s list                             # List orchestrators
  %(prog)s set orchestrators.langgraph.enabled=false  # Disable LangGraph
  %(prog)s get orchestrators.langgraph.enabled        # Get LangGraph status
  %(prog)s template --orchestrator crewai  # Show CrewAI template
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Configuration file path (default: config/system.yaml)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new configuration file')
    create_parser.add_argument('--output', '-o', help='Output file path')
    create_parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing file')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration file')
    validate_parser.add_argument('--warnings-ok', action='store_true', help='Exit with 0 even if warnings exist')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show configuration')
    show_parser.add_argument('--section', help='Show specific configuration section')
    show_parser.add_argument('--include-defaults', action='store_true', help='Include default values')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List orchestrators')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set configuration value')
    set_parser.add_argument('key_value', help='Key-value pair in format: key=value')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get configuration value')
    get_parser.add_argument('key', help='Configuration key (dot-separated)')
    
    # Template command
    template_parser = subparsers.add_parser('template', help='Show orchestrator templates')
    template_parser.add_argument('--orchestrator', help='Show template for specific orchestrator')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    command_map = {
        'create': create_config_command,
        'validate': validate_config_command,
        'show': show_config_command,
        'list': list_orchestrators_command,
        'set': set_config_command,
        'get': get_config_command,
        'template': template_command,
    }
    
    return command_map[args.command](args)

if __name__ == '__main__':
    sys.exit(main())