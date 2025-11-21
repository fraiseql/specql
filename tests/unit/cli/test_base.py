# tests/unit/cli/test_base.py
import sys
from pathlib import Path

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from click.testing import CliRunner


def test_common_options_adds_verbose():
    """Common options decorator should add --verbose flag."""
    from cli.base import common_options
    import click

    @click.command()
    @common_options
    def sample_cmd(verbose, quiet, output_dir):
        pass

    # Should have --verbose option
    assert any(p.name == "verbose" for p in sample_cmd.params)


def test_common_options_adds_quiet():
    """Common options decorator should add --quiet flag."""
    from cli.base import common_options
    import click

    @click.command()
    @common_options
    def sample_cmd(verbose, quiet, output_dir):
        pass

    # Should have --quiet option
    assert any(p.name == "quiet" for p in sample_cmd.params)


def test_verbose_and_quiet_mutually_exclusive():
    """--verbose and --quiet should be mutually exclusive."""
    from cli.base import common_options, validate_common_options
    import click

    @click.command()
    @common_options
    def sample_cmd(verbose, quiet, output_dir):
        validate_common_options(verbose=verbose, quiet=quiet)

    runner = CliRunner()
    result = runner.invoke(sample_cmd, ["--verbose", "--quiet"])
    assert result.exit_code != 0
