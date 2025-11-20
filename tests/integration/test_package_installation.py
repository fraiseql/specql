"""Test that package installs and imports work correctly"""

import subprocess


def test_cli_import_works():
    """Test CLI main module can be imported"""
    # Test direct import
    from cli.main import app

    assert app is not None
    assert hasattr(app, "commands")


def test_cli_command_works():
    """Test CLI entry point works"""
    result = subprocess.run(["python", "-m", "cli.main", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "SpecQL" in result.stdout
