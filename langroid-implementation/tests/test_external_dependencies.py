"""
External dependency tests for Langroid implementation.

Tests integration with external services and dependencies.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from langroid_implementation.adapter import LangroidAdapter, LANGROID_AVAILABLE


@pytest.mark.external
class TestExternalDependencies:
    """Test external dependencies and integrations."""
    
    @pytest.fixture
    def adapter_config(self):
        """Configuration for external testing."""
        return {
            'language': 'python',
            'langroid': {
                'model': 'gpt-3.5-turbo'
            },
            'vcs': {
                'github': {
                    'enabled': True,
                    'token': os.getenv('GITHUB_TOKEN', 'test-token'),
                    'owner': 'test-owner',
                    'repo': 'test-repo'
                }
            }
        }
    
    @pytest.mark.skipif(not LANGROID_AVAILABLE, reason="Langroid not available")
    def test_langroid_import(self):
        """Test Langroid library import and basic functionality."""
        try:
            import langroid as lr
            
            # Test basic Langroid functionality
            assert hasattr(lr, 'ChatAgent')
            assert hasattr(lr, 'Task')
            
            print(f"✅ Langroid version: {lr.__version__}")
            
        except ImportError as e:
            pytest.fail(f"Langroid import failed: {e}")
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OpenAI API key not available")
    @pytest.mark.asyncio
    async def test_openai_integration(self, adapter_config):
        """Test OpenAI API integration if key is available."""
        adapter_config['langroid']['api_key'] = os.getenv('OPENAI_API_KEY')
        adapter = LangroidAdapter(adapter_config)
        
        # Test that adapter initializes with OpenAI config
        assert adapter.openai_api_key is not None
        
        # Test health check includes OpenAI status
        health = await adapter.health_check()
        assert 'components' in health
    
    @pytest.mark.skipif(not os.getenv('GITHUB_TOKEN'), reason="GitHub token not available")
    def test_github_api_connectivity(self):
        """Test GitHub API connectivity if token is available."""
        token = os.getenv('GITHUB_TOKEN')
        
        # Test basic GitHub API connectivity
        headers = {'Authorization': f'token {token}'}
        
        try:
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ GitHub API connectivity successful")
            else:
                print(f"⚠️  GitHub API returned status: {response.status_code}")
                
        except requests.RequestException as e:
            pytest.fail(f"GitHub API connectivity failed: {e}")
    
    def test_network_connectivity(self):
        """Test basic network connectivity."""
        try:
            # Test connectivity to common services
            test_urls = [
                'https://api.github.com',
                'https://api.openai.com',
                'https://httpbin.org/get'
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    print(f"✅ {url}: {response.status_code}")
                except requests.RequestException as e:
                    print(f"⚠️  {url}: {e}")
                    
        except Exception as e:
            pytest.fail(f"Network connectivity test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_adapter_with_external_config(self, adapter_config):
        """Test adapter with external configuration."""
        adapter = LangroidAdapter(adapter_config)
        
        # Test capabilities with external config
        capabilities = await adapter.get_capabilities()
        
        assert 'conversation_style_interactions' in capabilities['features']
        assert 'vcs_providers' in capabilities
        
        # Test health check
        health = await adapter.health_check()
        
        assert 'status' in health
        assert 'components' in health


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "external"])