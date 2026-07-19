import pytest
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from audit.collectors.command_runner import run_command

def test_command_runner_success():
    result = run_command('python -c "print(\'hello audit\')"')
    assert result.returncode == 0
    assert "hello audit" in result.stdout

def test_command_runner_failure():
    result = run_command('python -c "import sys; sys.exit(1)"')
    assert result.returncode == 1

def test_command_runner_timeout():
    result = run_command('python -c "import time; time.sleep(3)"', timeout=1)
    assert result.timeout_reached == True
