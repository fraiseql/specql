"""Tests for incremental processing functionality."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from src.cli.confiture_extensions import specql


def test_incremental_only_processes_changed_files():
    """Test incremental mode only processes changed files"""

    cli_runner = CliRunner()

    # Create test project
    project_dir = Path(tempfile.mkdtemp()) / "test_project"
    project_dir.mkdir()

    # Create initial files
    (project_dir / "contact.rs").write_text("struct Contact { id: i32 }")
    (project_dir / "user.rs").write_text("struct User { id: i32 }")
    (project_dir / "task.rs").write_text("struct Task { id: i32 }")

    output_dir = Path(tempfile.mkdtemp()) / "output"

    try:
        # First run
        result1 = cli_runner.invoke(
            specql, ["reverse", str(project_dir), "--output-dir", str(output_dir)]
        )

        # Should succeed (may have errors but should run)
        assert result1.exit_code == 0

        # Modify one file
        (project_dir / "contact.rs").write_text("struct Contact { id: i32, name: String }")

        # Incremental run
        result2 = cli_runner.invoke(
            specql, ["reverse", str(project_dir), "--output-dir", str(output_dir), "--incremental"]
        )

        assert result2.exit_code == 0
        # Should indicate only 1 file processed
        assert "Found 1 changed files" in result2.output or "unchanged" in result2.output

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(project_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
