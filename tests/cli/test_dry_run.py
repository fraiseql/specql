"""Test --dry-run flag functionality."""

import pytest
from click.testing import CliRunner
from src.cli.confiture_extensions import specql
import tempfile
from pathlib import Path


def test_dry_run_shows_files_without_writing():
    """--dry-run should show what would be generated without writing."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test entity
        entity_file = Path(tmpdir) / "contact.yaml"
        entity_file.write_text("""entity: Contact
schema: crm
fields:
  name: text
  email: email
""")

        output_dir = Path(tmpdir) / "output"

        # Run with --dry-run
        result = runner.invoke(
            specql,
            [
                "generate",
                str(entity_file),
                "--output-dir",
                str(output_dir),
                "--dry-run",
            ],
            input="y\n",
        )

        # Should succeed
        assert result.exit_code == 0

        # Should mention dry run
        assert "DRY RUN" in result.output or "dry run" in result.output.lower()

        # Should show files that would be generated
        assert "contact" in result.output.lower() or "Contact" in result.output

        # Should NOT create output directory
        assert not output_dir.exists(), "Dry run should not create files"

        # Should NOT create any SQL files
        assert len(list(Path(tmpdir).rglob("*.sql"))) == 0


def test_dry_run_shows_file_count():
    """--dry-run should show count of files to be generated."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        entity_file = Path(tmpdir) / "user.yaml"
        entity_file.write_text("""entity: User
schema: auth
fields:
  username: text
  email: email
""")

        result = runner.invoke(
            specql, ["generate", str(entity_file), "--dry-run"], input="y\n"
        )

        assert result.exit_code == 0
        # Should show some count
        assert any(word in result.output.lower() for word in ["file", "would generate"])


def test_normal_generation_without_dry_run():
    """Without --dry-run, files should be created."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        entity_file = Path(tmpdir) / "product.yaml"
        entity_file.write_text("""entity: Product
schema: shop
fields:
  name: text
  price: decimal
""")

        output_dir = Path(tmpdir) / "output"

        result = runner.invoke(
            specql,
            ["generate", str(entity_file), "--output-dir", str(output_dir)],
            input="y\n",
        )

        assert result.exit_code == 0

        # Should create files
        assert output_dir.exists()
        generated_files = list(output_dir.rglob("*.sql"))
        assert len(generated_files) > 0, "Should generate SQL files"
