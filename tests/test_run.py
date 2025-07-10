"""
Test for run.py module.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from app import create_app


def test_app_creation():
    """Test that the app can be created from run.py."""
    from run import app
    assert app is not None
    assert hasattr(app, 'config')


def test_environment_port_handling():
    """Test environment variable handling."""
    # Test default port
    with patch.dict(os.environ, {}, clear=True):
        port = int(os.environ.get("PORT", 8080))
        assert port == 8080
    
    # Test custom port
    with patch.dict(os.environ, {"PORT": "9000"}):
        port = int(os.environ.get("PORT", 8080))
        assert port == 9000


def test_main_function():
    """Test the main() function that starts the development server."""
    import run
    
    # Mock app.run to prevent actual server startup
    with patch.object(run.app, 'run') as mock_run:
        # Test with default port
        with patch.dict(os.environ, {}, clear=True):
            run.main()
            mock_run.assert_called_once_with(host="0.0.0.0", port=8080, debug=True)
        
        mock_run.reset_mock()
        
        # Test with custom port
        with patch.dict(os.environ, {"PORT": "9000"}):
            run.main()
            mock_run.assert_called_once_with(host="0.0.0.0", port=9000, debug=True)


def test_main_execution_path():
    """Test the if __name__ == '__main__' execution path using subprocess."""
    import subprocess
    import os
    import tempfile
    
    # Create a test script that patches the Flask app to prevent server startup
    test_script_content = '''
import sys
import os
from unittest.mock import patch, MagicMock

# Add current directory to path to import our modules
sys.path.insert(0, os.getcwd())

# Create a mock app that doesn't actually start a server
mock_app = MagicMock()

# Patch the Flask app creation to return our mock
with patch('app.create_app', return_value=mock_app):
    # Import and execute run.py as if it were the main module
    with open('run.py', 'r') as f:
        code = f.read()
    
    # Execute the code with __name__ set to __main__
    exec(compile(code, 'run.py', 'exec'), {'__name__': '__main__'})

# Verify that app.run was called with expected parameters
expected_port = int(os.environ.get("PORT", 8080))
mock_app.run.assert_called_once_with(host="0.0.0.0", port=expected_port, debug=True)
print("SUCCESS: main execution path tested")
'''
    
    # Write the test script to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script_content)
        test_script_path = f.name
    
    try:
        # Run the test script as a subprocess
        result = subprocess.run(
            [sys.executable, test_script_path],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "PORT": "8080"}
        )
        
        # Check that the test passed
        assert result.returncode == 0, f"Test script failed: {result.stderr}"
        assert "SUCCESS: main execution path tested" in result.stdout
        
    finally:
        # Clean up the temporary file
        os.unlink(test_script_path)