"""
Tests for enhanced help text in generate command
"""

import pytest
from click.testing import CliRunner

from src.cli.confiture_extensions import specql


class TestGenerateHelp:
    """Test the enhanced help text for the generate command"""

    def test_help_contains_common_examples(self):
        """Test that help text includes common examples section"""
        runner = CliRunner()
        result = runner.invoke(specql, ["generate", "--help"])

        assert result.exit_code == 0
        assert "COMMON EXAMPLES:" in result.output
        assert "specql generate entities/**/*.yaml" in result.output
        assert "FraiseQL defaults: tv_* views" in result.output

    def test_help_contains_output_formats(self):
        """Test that help text includes output format descriptions"""
        runner = CliRunner()
        result = runner.invoke(specql, ["generate", "--help"])

        assert result.exit_code == 0
        assert "OUTPUT FORMATS:" in result.output
        assert "hierarchical (default)" in result.output
        assert "flat (--dev or --format=confiture)" in result.output

    def test_help_contains_generated_artifacts(self):
        """Test that help text describes what gets generated"""
        runner = CliRunner()
        result = runner.invoke(specql, ["generate", "--help"])

        assert result.exit_code == 0
        assert "GENERATED ARTIFACTS:" in result.output
        assert "Table definition (tb_*)" in result.output
        assert "Table view (tv_*)" in result.output
        assert "Helper functions" in result.output

    def test_help_contains_framework_defaults(self):
        """Test that help text includes framework-specific defaults"""
        runner = CliRunner()
        result = runner.invoke(specql, ["generate", "--help"])

        assert result.exit_code == 0
        assert "FRAMEWORK-SPECIFIC DEFAULTS:" in result.output
        assert "FraiseQL (default):" in result.output
        assert "Table views (tv_*) for GraphQL queries" in result.output

    def test_help_contains_table_views_explanation(self):
        """Test that help text explains table views for FraiseQL"""
        runner = CliRunner()
        result = runner.invoke(specql, ["generate", "--help"])

        assert result.exit_code == 0
        assert "TABLE VIEWS (tv_*) - FraiseQL Specific:" in result.output
        assert "GraphQL-friendly views" in result.output
        assert "--no-tv to skip table view generation" in result.output

    def test_help_contains_more_help_section(self):
        """Test that help text includes documentation links"""
        runner = CliRunner()
        result = runner.invoke(specql, ["generate", "--help"])

        assert result.exit_code == 0
        assert "MORE HELP:" in result.output
        assert "github.com/fraiseql/specql" in result.output