# tests/unit/cli/commands/test_reverse.py
import sys
from pathlib import Path

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from click.testing import CliRunner


def test_reverse_group_exists():
    """Reverse command group should exist in main CLI."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "reverse" in result.output


def test_reverse_help_shows_subcommands():
    """Reverse --help should show all subcommands."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "--help"])

    assert result.exit_code == 0
    assert "sql" in result.output
    assert "python" in result.output
    assert "typescript" in result.output
    assert "rust" in result.output
    assert "project" in result.output


def test_reverse_sql_requires_files():
    """Reverse sql should require at least one file."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "sql"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_reverse_sql_accepts_files():
    """Reverse sql should accept file arguments."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("test.sql").write_text("CREATE TABLE test (id INT);")
        result = runner.invoke(app, ["reverse", "sql", "test.sql", "-o", "output"])

        # Should not fail due to argument parsing
        assert "Missing argument" not in result.output
        assert "Phase 3 reverse sql command processed" in result.output


def test_reverse_project_requires_directory():
    """Reverse project should require a directory argument."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "project"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_reverse_project_accepts_directory():
    """Reverse project should accept directory arguments."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("test_dir").mkdir()
        result = runner.invoke(app, ["reverse", "project", "test_dir", "-o", "output"])

        assert result.exit_code == 0
        assert "Analyzing project" in result.output
