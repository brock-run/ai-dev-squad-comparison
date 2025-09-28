#!/usr/bin/env python3
"""
Configuration Validation Script
This script validates the system configuration and provides detailed feedback.
"""
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.config import load_config, ConfigurationManager

def main():
    """Main validation script."""
    parser = argparse.ArgumentParser(
        description="Validate AI Dev Squad Comparison configuration"
    )
    parser.add_argument(
        '--config', '-c',
        default='config/system.yaml',
        help='Configuration file to validate (default: config/system.yaml)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed validation information'
    )
    parser.add_argument(
        '--warnings-as-errors',
        action='store_true',
        help='Treat warnings as errors'
    )
    
    args = parser.parse_args()
    
    config_file = Path(args.config)
    
    print(f"Validating configuration: {config_file}")
    print("=" * 60)
    
    # Check if file exists
    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        print(f"💡 Create a default configuration with:")
        print(f"   python -m common.config_cli create --output {config_file}")
        return 1
    
    try:
        # Load and validate configuration
        manager = load_config(str(config_file))
        warnings = manager.validate_configuration()
        
        # Show configuration summary
        if args.verbose:
            print("Configuration Summary:")
            print("-" * 30)
            enabled_orchestrators = manager.get_enabled_orchestrators()
            print(f"Enabled orchestrators: {len(enabled_orchestrators)}")
            for orchestrator in enabled_orchestrators:
                config = manager.get_orchestrator_config(orchestrator)
                print(f"  - {orchestrator}: {config.model_config.primary}")
            
            print(f"Safety enabled: {manager.config.safety.enabled}")
            print(f"Sandbox type: {manager.config.safety.sandbox_type}")
            print(f"VCS providers: ", end="")
            vcs_providers = []
            if manager.config.vcs.github and manager.config.vcs.github.enabled:
                vcs_providers.append("GitHub")
            if manager.config.vcs.gitlab and manager.config.vcs.gitlab.enabled:
                vcs_providers.append("GitLab")
            print(", ".join(vcs_providers) if vcs_providers else "None")
            
            print(f"Observability enabled: {manager.config.observability.structured_logging.enabled}")
            print(f"Dashboard port: {manager.config.observability.dashboard.port}")
            print()
        
        # Show validation results
        if not warnings:
            print("✅ Configuration is valid with no warnings")
            return 0
        else:
            print(f"⚠️  Configuration has {len(warnings)} warning(s):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
            
            if args.warnings_as_errors:
                print("\n❌ Treating warnings as errors")
                return 1
            else:
                print("\n✅ Configuration is valid (with warnings)")
                return 0
    
    except Exception as e:
        print(f"❌ Configuration validation failed:")
        print(f"   {e}")
        
        if args.verbose:
            import traceback
            print("\nDetailed error:")
            traceback.print_exc()
        
        return 1

if __name__ == '__main__':
    sys.exit(main())