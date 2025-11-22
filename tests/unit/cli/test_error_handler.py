# tests/unit/cli/test_error_handler.py
import sys
from pathlib import Path

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from click.testing import CliRunner


def test_cli_error_shows_message():
    """CLI errors should display user-friendly message."""
    import click

    from cli.utils.error_handler import CLIError, handle_cli_error

    @click.command()
    def test_cmd():
        with handle_cli_error():
            raise CLIError("Something went wrong", hint="Try --verbose")

    runner = CliRunner()
    result = runner.invoke(test_cmd, [])
    assert result.exit_code == 1
    assert "Something went wrong" in result.output
    assert "Try --verbose" in result.output


def test_validation_error_shows_file_location():
    """Validation errors should show file and line number."""
    import click

    from cli.utils.error_handler import ValidationError

    @click.command()
    def test_cmd():
        raise ValidationError("Invalid field type", file="entity.yaml", line=42)

    runner = CliRunner()
    result = runner.invoke(test_cmd, [])
    assert result.exit_code == 1
    assert "entity.yaml:42" in result.output
    assert "Invalid field type" in result.output
