"""
Quick Test Verification

This is a simple test to verify our test setup is working.
"""

from unittest.mock import Mock, patch
from click.testing import CliRunner


def test_basic_setup():
    """Test that basic test infrastructure works."""
    # Test mock functionality
    mock = Mock()
    mock.test_method.return_value = "test_result"
    assert mock.test_method() == "test_result"
    
    # Test Click CLI runner
    runner = CliRunner()
    assert runner is not None
    
    print("✅ Basic test setup verification passed!")


def test_patch_functionality():
    """Test that patching works correctly."""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        
        import os.path
        result = os.path.exists('/fake/path')
        assert result is True
        mock_exists.assert_called_once_with('/fake/path')
    
    print("✅ Patch functionality verification passed!")


if __name__ == "__main__":
    test_basic_setup()
    test_patch_functionality()
    print("✅ All verification tests passed!")
