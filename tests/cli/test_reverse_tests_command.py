"""Tests for reverse-tests CLI command."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from src.cli.confiture_extensions import specql


class TestReverseTestsCommand:
    """Test reverse-tests CLI command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def sample_pgtap_test(self, tmp_path):
        """Create sample pgTAP test file."""
        test_file = tmp_path / "test_contact.sql"
        test_file.write_text("""
BEGIN;
SELECT plan(2);

-- Test: Contact table should exist
SELECT has_table('crm'::name, 'tb_contact'::name, 'Contact table exists');

-- Test: Contact should have email column
SELECT has_column('crm', 'tb_contact', 'email', 'Has email column');

SELECT * FROM finish();
ROLLBACK;
        """)
        return test_file

    def test_reverse_tests_help_works(self, runner):
        """reverse-tests --help should work."""
        result = runner.invoke(specql, ["reverse-tests", "--help"])
        assert result.exit_code == 0
        assert "Reverse engineer test files" in result.output

    def test_reverse_tests_requires_input_files(self, runner):
        """reverse-tests should require input files."""
        result = runner.invoke(specql, ["reverse-tests"])
        assert result.exit_code == 1
        assert "No input files specified" in result.output

    def test_reverse_tests_with_preview(self, runner, sample_pgtap_test):
        """reverse-tests with --preview should not prompt and show output."""
        result = runner.invoke(
            specql, ["reverse-tests", str(sample_pgtap_test), "--preview"]
        )

        # Should succeed without prompts
        assert result.exit_code == 0
        # Should show preview output
        assert "Contact" in result.output or "test_contact" in result.output
        # Should NOT contain prompt text
        assert "Aborted" not in result.output

    def test_reverse_tests_parses_pgtap(self, runner, sample_pgtap_test, tmp_path):
        """reverse-tests should parse pgTAP test file and create output."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            specql,
            [
                "reverse-tests",
                str(sample_pgtap_test),
                "--output-dir",
                str(output_dir),
                "--entity",
                "Contact",
                "--format",
                "yaml",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Should create YAML output
        expected_yaml = output_dir / "Contact_tests.yaml"
        assert expected_yaml.exists(), f"Expected {expected_yaml} to be created"

    def test_reverse_tests_analyze_coverage(self, runner, sample_pgtap_test):
        """reverse-tests --analyze-coverage should suggest missing tests."""
        result = runner.invoke(
            specql,
            [
                "reverse-tests",
                str(sample_pgtap_test),
                "--analyze-coverage",
                "--preview",
            ],
        )

        assert result.exit_code == 0
        # Should show coverage analysis
        assert "coverage" in result.output.lower() or "missing" in result.output.lower()

    def test_generated_yaml_content(self, runner, sample_pgtap_test, tmp_path):
        """Generated YAML should have correct structure."""
        output_dir = tmp_path / "output"

        runner.invoke(
            specql,
            [
                "reverse-tests",
                str(sample_pgtap_test),
                "--output-dir",
                str(output_dir),
                "--entity",
                "Contact",
                "--format",
                "yaml",
            ],
        )

        yaml_file = output_dir / "Contact_tests.yaml"
        content = yaml_file.read_text()

        # Should contain basic TestSpec structure
        assert "entity_name:" in content or "entity_name:" in content
        assert "scenarios:" in content
        assert "test_framework:" in content
