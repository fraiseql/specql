"""Test that reverse engineering produces valid YAML"""

import tempfile
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.confiture_extensions import specql


@pytest.fixture
def cli_runner():
    """Click CLI runner for testing."""
    return CliRunner()


def test_generated_yaml_passes_validation(cli_runner):
    """Test reverse → validate workflow"""
    # Create test Django model
    source_code = textwrap.dedent(
        """
        from django.db import models

        class Product(models.Model):
            name = models.CharField(max_length=255)
            price = models.DecimalField(max_digits=10, decimal_places=2)
            in_stock = models.BooleanField(default=True)
    """
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write source file
        source_file = Path(tmpdir) / "models.py"
        source_file.write_text(source_code)

        # Generate YAML
        output_dir = Path(tmpdir) / "entities"
        result = cli_runner.invoke(
            specql, ["reverse-python", str(source_file), "--output-dir", str(output_dir)]
        )
        assert result.exit_code == 0

        # Validate generated YAML
        yaml_files = list(output_dir.glob("*.yaml"))
        assert len(yaml_files) == 1

        # Should pass validation
        result = cli_runner.invoke(specql, ["validate"] + [str(f) for f in yaml_files])
        assert result.exit_code == 0


def test_generated_yaml_with_simple_actions(cli_runner):
    """Test validation of YAML with simple actions (no method calls)"""
    source_code = textwrap.dedent(
        """
        from django.db import models

        class Order(models.Model):
            status = models.CharField(max_length=50, default='pending')
    """
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = Path(tmpdir) / "models.py"
        source_file.write_text(source_code)

        output_dir = Path(tmpdir) / "entities"
        result = cli_runner.invoke(
            specql, ["reverse-python", str(source_file), "--output-dir", str(output_dir)]
        )
        assert result.exit_code == 0

        yaml_files = list(output_dir.glob("*.yaml"))
        result = cli_runner.invoke(specql, ["validate"] + [str(f) for f in yaml_files])

        # Should pass validation
        assert result.exit_code == 0

        yaml_files = list(output_dir.glob("*.yaml"))
        result = cli_runner.invoke(specql, ["validate"] + [str(f) for f in yaml_files])

        # Should pass validation
        assert result.exit_code == 0
