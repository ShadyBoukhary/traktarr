"""
Fix for Config singleton import issues in tests.

This module patches the Config class to prevent import-time errors.
"""

import sys
from unittest.mock import Mock, patch

# Create a mock Config instance that can be used globally
mock_config_instance = Mock()
mock_config_instance.logfile = '/tmp/test.log'
mock_config_instance.cachefile = '/tmp/test.cache'
mock_config_instance.config_path = '/tmp/test.json'

# Create nested mock structure
mock_config_instance.cfg = Mock()
mock_config_instance.cfg.core = Mock()
mock_config_instance.cfg.core.debug = False

# Patch Config class at import time
original_import = __import__

def patched_import(name, *args, **kwargs):
    """Custom import that patches Config class when misc.config is imported."""
    module = original_import(name, *args, **kwargs)
    
    if name == 'misc.config':
        # Patch the Config class to return our mock
        Config = getattr(module, 'Config', None)
        if Config:
            # Replace the __call__ method of the singleton metaclass
            original_call = Config.__call__
            def mock_call(cls, *args, **kwargs):
                return mock_config_instance
            Config.__call__ = mock_call
    
    return module

# Apply the patch
__builtins__['__import__'] = patched_import
