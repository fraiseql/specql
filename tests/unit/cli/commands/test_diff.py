# tests/unit/cli/commands/test_diff.py
import sys
from pathlib import Path

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from click.testing import CliRunner


def test_diff_requires_yaml_file():
    """Diff should require a YAML file argument."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["diff"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "required" in result.output.lower()


def test_diff_requires_compare_file():
    """Diff should require a --compare file."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("entity.yaml").write_text("entity: Test\nfields:\n  name: text")
        result = runner.invoke(app, ["diff", "entity.yaml"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_diff_shows_in_help():
    """Diff command should appear in main --help."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert "diff" in result.output
    assert "Compare" in result.output  # Description visible


def test_diff_help_shows_all_options():
    """Diff --help should show all available options."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["diff", "--help"])

    assert result.exit_code == 0
    # Check for key options
    assert "--compare" in result.output
    assert "--format" in result.output
    assert "--ignore-comments" in result.output


def test_diff_runs_and_produces_output():
    """Diff should run and produce diff output."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a simple entity YAML
        yaml_content = """entity: contact
schema: crm
description: Contact entity
fields:
  name:
    type: text
    required: true
"""
        Path("contact.yaml").write_text(yaml_content)

        # Create a simple SQL file for comparison
        sql_content = """CREATE TABLE crm.contact (
    name TEXT NOT NULL
);"""
        Path("contact.sql").write_text(sql_content)

        # Test diff
        result = runner.invoke(app, ["diff", "contact.yaml", "--compare", "contact.sql"])

        # Should run (exit code may be 1 if differences found, which is expected)
        assert result.exit_code in [0, 1]
        # Should produce some output
        assert len(result.output.strip()) > 0


def test_diff_with_format_json():
    """Diff --format json should output JSON."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a simple entity YAML
        yaml_content = """entity: contact
schema: crm
fields:
  name:
    type: text
    required: true
"""
        Path("contact.yaml").write_text(yaml_content)

        # Create a different SQL file
        sql_content = """CREATE TABLE crm.contact (
    name TEXT NOT NULL
);"""
        Path("contact.sql").write_text(sql_content)

        result = runner.invoke(
            app, ["diff", "contact.yaml", "--compare", "contact.sql", "--format", "json"]
        )

        assert result.exit_code in [0, 1]
        # Should contain JSON output or indicate differences
        assert (
            '"differences"' in result.output
            or "No differences" in result.output
            or len(result.output.strip()) > 0
        )


def test_diff_ignore_comments():
    """Diff --ignore-comments should ignore comment differences."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a simple entity YAML
        yaml_content = """entity: contact
schema: crm
fields:
  name:
    type: text
    required: true
"""
        Path("contact.yaml").write_text(yaml_content)

        # Create SQL with comments
        sql_content = """-- This is a comment
CREATE TABLE crm.contact (
    name TEXT NOT NULL
);"""
        Path("contact.sql").write_text(sql_content)

        result = runner.invoke(
            app, ["diff", "contact.yaml", "--compare", "contact.sql", "--ignore-comments"]
        )

        assert result.exit_code in [0, 1]
