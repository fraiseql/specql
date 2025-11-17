"""Tests for reverse engineering CLI commands."""

import pytest
from src.cli.confiture_extensions import specql


class TestReverseCommandRegistration:
    """Test that reverse commands are properly registered in CLI."""

    def test_reverse_command_appears_in_help(self, cli_runner):
        """Verify 'reverse' command is discoverable in CLI help"""
        result = cli_runner.invoke(specql, ["--help"])
        assert "reverse" in result.output
        assert "Reverse engineer source code to SpecQL YAML" in result.output

    def test_reverse_sql_command_exists(self, cli_runner):
        """Verify 'reverse-sql' command exists"""
        result = cli_runner.invoke(specql, ["reverse-sql", "--help"])
        assert result.exit_code == 0
        assert "SQL_FILES" in result.output

    def test_reverse_python_command_exists(self, cli_runner):
        """Verify 'reverse-python' command exists"""
        result = cli_runner.invoke(specql, ["reverse-python", "--help"])
        assert result.exit_code == 0
        assert "PYTHON_FILES" in result.output

    def test_reverse_command_auto_detect_help(self, cli_runner):
        """Test reverse command help shows auto-detection info"""
        result = cli_runner.invoke(specql, ["reverse", "--help"])
        assert result.exit_code == 0
        assert "Auto-detects language" in result.output
        assert "INPUT_FILES" in result.output


class TestReverseCommandFunctionality:
    """Test basic functionality of reverse commands."""

    def test_reverse_command_requires_files(self, cli_runner):
        """Test that reverse command requires input files"""
        result = cli_runner.invoke(specql, ["reverse"])
        assert result.exit_code == 2  # Click error for missing required argument
        assert "Missing argument" in result.output

    def test_reverse_sql_command_requires_files(self, cli_runner):
        """Test that reverse-sql command requires files"""
        result = cli_runner.invoke(specql, ["reverse-sql"])
        assert result.exit_code == 0
        assert "No SQL files specified" in result.output

    def test_reverse_python_command_handles_empty_files(self, cli_runner):
        """Test that reverse-python command handles empty file list"""
        result = cli_runner.invoke(specql, ["reverse-python"])
        assert result.exit_code == 0
        assert "Successful: 0/0" in result.output
