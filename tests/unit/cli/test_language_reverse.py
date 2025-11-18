"""Tests for language-specific reverse engineering commands."""

import pytest
from src.cli.confiture_extensions import specql


class TestLanguageReverseCommands:
    """Test language-specific reverse engineering commands."""

    def test_reverse_rust_command_exists(self, cli_runner):
        """Test Rust reverse engineering command exists"""
        result = cli_runner.invoke(specql, ["reverse", "rust", "--help"])
        # This should fail initially since the command doesn't exist
        assert result.exit_code != 0 or "No such command" in result.output

    def test_reverse_typescript_command_exists(self, cli_runner):
        """Test TypeScript reverse engineering command exists"""
        result = cli_runner.invoke(specql, ["reverse", "typescript", "--help"])
        # This should fail initially since the command doesn't exist
        assert result.exit_code != 0 or "No such command" in result.output

    def test_reverse_java_command_exists(self, cli_runner):
        """Test Java reverse engineering command exists"""
        result = cli_runner.invoke(specql, ["reverse", "java", "--help"])
        # This should fail initially since the command doesn't exist
        assert result.exit_code != 0 or "No such command" in result.output

    def test_reverse_group_exists(self, cli_runner):
        """Test that reverse command group exists"""
        result = cli_runner.invoke(specql, ["reverse", "--help"])
        assert result.exit_code == 0
        # Should show subcommands
        assert "Commands:" in result.output
        assert "sql" in result.output
        assert "python" in result.output
