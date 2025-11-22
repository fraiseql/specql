# tests/unit/cli/commands/test_generate.py
import sys
from pathlib import Path

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from click.testing import CliRunner


def test_generate_requires_files():
    """Generate should require at least one YAML file."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["generate"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "required" in result.output.lower()


def test_generate_accepts_yaml_files():
    """Generate should accept YAML file arguments."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("entity.yaml").write_text("entity: Test\nfields:\n  name: text")
        result = runner.invoke(app, ["generate", "entity.yaml"])

        # Should not fail due to argument parsing
        assert "Missing argument" not in result.output


def test_generate_shows_in_help():
    """Generate command should appear in main --help."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert "generate" in result.output
    assert "Generate" in result.output  # Description visible


def test_generate_dry_run():
    """Generate --dry-run should show preview without creating files."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("entity.yaml").write_text("entity: Test\nfields:\n  name: text")
        result = runner.invoke(
            app, ["generate", "entity.yaml", "--dry-run", "--output", "migrations"]
        )

        assert result.exit_code == 0
        assert "Dry-run mode" in result.output
        assert "Would generate to" in result.output
        # Should not create any files
        assert not Path("migrations").exists()


def test_generate_with_options():
    """Generate should accept all documented options."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("entity.yaml").write_text("entity: Test\nfields:\n  name: text")

        # Test various option combinations
        result = runner.invoke(
            app,
            [
                "generate",
                "entity.yaml",
                "--dry-run",
                "--output",
                "migrations",
                "--use-registry",
                "--with-impacts",
                "--include-tv",
                "--output-format",
                "confiture",
            ],
        )

        assert result.exit_code == 0
        assert "registry-based table codes" in result.output
        assert "mutation impacts" in result.output
        assert "table views" in result.output


def test_generate_help_shows_all_options():
    """Generate --help should show all available options."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["generate", "--help"])

    assert result.exit_code == 0
    # Check for key options
    assert "--dry-run" in result.output
    assert "--use-registry" in result.output
    assert "--with-impacts" in result.output
    assert "--include-tv" in result.output
    assert "--foundation-only" in result.output
    assert "--actions-only" in result.output
    assert "--frontend" in result.output
    assert "--tests" in result.output
