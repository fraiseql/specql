"""
End-to-end integration tests for SpecQL CLI workflows.
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestCLIEndToEnd:
    """Test complete CLI workflows from start to finish."""

    def test_cli_help_complete(self):
        """Test that all command groups appear in main help."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Check all command groups are present
        assert "generate" in help_text
        assert "reverse" in help_text
        assert "patterns" in help_text
        assert "init" in help_text
        assert "workflow" in help_text

    def test_workflow_migrate_dry_run(self):
        """Test full workflow migrate dry-run with real files."""
        test_dir = Path(__file__).parent.parent.parent
        entities_dir = test_dir / "entities"

        # Get actual YAML files
        yaml_files = list(entities_dir.glob("*.yaml"))
        file_args = [str(f) for f in yaml_files]

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "workflow", "migrate", "--dry-run", "--progress"]
            + file_args,
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        output = result.stdout

        # Check pipeline phases
        assert "Starting SpecQL migration pipeline" in output
        assert "Dry-run mode" in output
        assert "Migration Plan" in output
        assert "Pipeline complete" in output

    def test_workflow_sync_dry_run(self):
        """Test workflow sync dry-run."""
        test_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "workflow", "sync", "entities/", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        output = result.stdout

        assert "Starting SpecQL incremental sync" in output
        assert "Dry-run mode" in output
        assert "Sync Plan" in output

    def test_reverse_subcommands_available(self):
        """Test that all reverse subcommands are available."""
        test_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "reverse", "--help"],
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Check all reverse subcommands
        assert "sql" in help_text
        assert "python" in help_text
        assert "typescript" in help_text
        assert "rust" in help_text
        assert "project" in help_text

    def test_init_subcommands_available(self):
        """Test that all init subcommands are available."""
        test_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Check all init subcommands
        assert "project" in help_text
        assert "entity" in help_text
        assert "registry" in help_text

    def test_patterns_subcommands_available(self):
        """Test that all patterns subcommands are available."""
        test_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "patterns", "--help"],
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Check all patterns subcommands
        assert "detect" in help_text
        assert "apply" in help_text

    def test_workflow_subcommands_available(self):
        """Test that all workflow subcommands are available."""
        test_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "workflow", "--help"],
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Check all workflow subcommands
        assert "migrate" in help_text
        assert "sync" in help_text

    def test_generate_command_help(self):
        """Test generate command help shows all options."""
        test_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "generate", "--help"],
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Check key options are present
        assert "--foundation-only" in help_text
        assert "--actions-only" in help_text
        assert "--dry-run" in help_text
        assert "--frontend" in help_text

    def test_error_handling_invalid_command(self):
        """Test error handling for invalid commands."""
        test_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "nonexistent"],
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        # Should return error code
        assert result.returncode == 2
        assert "Error: No such command" in result.stderr

    def test_workflow_migrate_with_continue_on_error(self):
        """Test workflow migrate with error recovery."""
        test_dir = Path(__file__).parent.parent.parent
        entities_dir = test_dir / "entities"

        # Get actual YAML files
        yaml_files = list(entities_dir.glob("*.yaml"))
        file_args = [str(f) for f in yaml_files]

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.main",
                "workflow",
                "migrate",
                "--progress",
                "--continue-on-error",
            ]
            + file_args,
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        output = result.stdout

        # Should complete despite simulated validation errors
        assert "Migration pipeline completed successfully" in output
        assert "Generated" in output and "file(s)" in output

    @pytest.mark.parametrize(
        "command_group", ["generate", "reverse", "patterns", "init", "workflow"]
    )
    def test_command_group_verbose_quiet_flags(self, command_group):
        """Test that all command groups accept verbose and quiet flags."""
        test_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", command_group, "--help"],
            capture_output=True,
            text=True,
            cwd=test_dir,
        )

        assert result.returncode == 0
        help_text = result.stdout

        # All command groups should have these common options
        assert "--verbose" in help_text or "-v" in help_text
        assert "--quiet" in help_text or "-q" in help_text
