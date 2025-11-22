# tests/unit/cli/test_main.py
import sys
from pathlib import Path

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from click.testing import CliRunner


def test_main_help_shows_basic_info():
    """Main --help should show basic CLI information."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    # Basic info should be visible
    assert "SpecQL" in result.output
    assert "Business YAML" in result.output
    assert "generate" in result.output  # From quick start examples


def test_main_version():
    """--version should show SpecQL version."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "specql" in result.output.lower()
