#!/usr/bin/env python3
"""
Simple test to verify LangGraph adapter works with real dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapter import LangGraphAdapter

def test_adapter_creation():
    """Test that we can create a LangGraph adapter instance."""
    config = {
        'language': 'python',
        'vcs': {'enabled': True, 'repository': 'test/repo'},
        'human_review': {'enabled': False}
    }
    
    try:
        adapter = LangGraphAdapter(config)
        print(f"✓ Adapter created successfully")
        print(f"  Name: {adapter.name}")
        print(f"  Version: {adapter.version}")
        print(f"  Description: {adapter.description}")
        return True
    except Exception as e:
        print(f"✗ Failed to create adapter: {e}")
        return False

if __name__ == "__main__":
    success = test_adapter_creation()
    sys.exit(0 if success else 1)