"""
Tests for workflow command group.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from cli.main import app


class TestWorkflowCommands:
    """Test workflow command group functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.test_dir = Path(__file__).parent.parent.parent.parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)

        # Create test YAML files
        self.user_yaml = self.test_dir / "user.yaml"
        self.user_yaml.write_text("""
name: user
table: users
fields:
  id: integer primary_key
  email: string unique
  name: string
""")

        self.post_yaml = self.test_dir / "post.yaml"
        self.post_yaml.write_text("""
name: post
table: posts
fields:
  id: integer primary_key
  title: string
  content: text
  user_id: integer foreign_key:users.id
""")

    def teardown_method(self):
        """Clean up test fixtures."""
        for file in [self.user_yaml, self.post_yaml]:
            if file.exists():
                file.unlink()
        if self.test_dir.exists():
            import shutil

            shutil.rmtree(self.test_dir)

    def test_workflow_group_help(self):
        """Test workflow command group help."""
        result = self.runner.invoke(app, ["workflow", "--help"])
        assert result.exit_code == 0
        assert "Multi-step automation" in result.output
        assert "migrate" in result.output
        assert "sync" in result.output

    def test_migrate_help(self):
        """Test migrate subcommand help."""
        result = self.runner.invoke(app, ["workflow", "migrate", "--help"])
        assert result.exit_code == 0
        assert "full migration pipeline" in result.output
        assert "--reverse-from" in result.output
        assert "--dry-run" in result.output

    def test_sync_help(self):
        """Test sync subcommand help."""
        result = self.runner.invoke(app, ["workflow", "sync", "--help"])
        assert result.exit_code == 0
        assert "Incremental synchronization" in result.output
        assert "--watch" in result.output
        assert "--force" in result.output

    def test_migrate_dry_run(self):
        """Test migrate command with dry-run."""
        result = self.runner.invoke(
            app, ["workflow", "migrate", str(self.user_yaml), str(self.post_yaml), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Dry-run mode" in result.output
        assert "Migration Plan" in result.output
        assert "Pipeline complete" in result.output

    def test_migrate_with_progress(self):
        """Test migrate command with progress reporting."""
        result = self.runner.invoke(
            app,
            [
                "workflow",
                "migrate",
                str(self.user_yaml),
                str(self.post_yaml),
                "--progress",
                "--continue-on-error",
            ],
        )
        assert result.exit_code == 0
        assert "Starting SpecQL migration pipeline" in result.output
        assert "Phase 1: Reverse engineering" in result.output
        assert "Phase 2: Validation" in result.output
        assert "Phase 3: Code generation" in result.output
        assert "Migration pipeline completed successfully" in result.output

    def test_migrate_validate_only(self):
        """Test migrate command with validate-only flag."""
        result = self.runner.invoke(
            app, ["workflow", "migrate", str(self.user_yaml), "--validate-only"]
        )
        assert result.exit_code == 0
        assert "Stopping after validation" in result.output

    def test_sync_dry_run(self):
        """Test sync command with dry-run."""
        result = self.runner.invoke(app, ["workflow", "sync", str(self.test_dir), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry-run mode" in result.output
        assert "Sync Plan" in result.output
        assert "Ready to sync" in result.output

    def test_sync_with_progress(self):
        """Test sync command with progress reporting."""
        result = self.runner.invoke(app, ["workflow", "sync", str(self.test_dir), "--progress"])
        assert result.exit_code == 0
        assert "Starting SpecQL incremental sync" in result.output
        assert "Found" in result.output and "changed file(s)" in result.output
        assert "Sync completed" in result.output

    def test_sync_force_regeneration(self):
        """Test sync command with force flag."""
        result = self.runner.invoke(
            app, ["workflow", "sync", str(self.test_dir), "--force", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Force regeneration" in result.output

    def test_migrate_reverse_from_sql(self):
        """Test migrate command with reverse-from=sql."""
        # Create a dummy SQL file
        sql_file = self.test_dir / "test.sql"
        sql_file.write_text("CREATE TABLE test (id INTEGER);")

        result = self.runner.invoke(
            app, ["workflow", "migrate", str(sql_file), "--reverse-from=sql", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Source type: sql" in result.output

        sql_file.unlink()

    def test_sync_with_exclude(self):
        """Test sync command with exclude patterns."""
        result = self.runner.invoke(
            app, ["workflow", "sync", str(self.test_dir), "--exclude=user.yaml", "--dry-run"]
        )
        assert result.exit_code == 0
        # Should still work, just with filtering

    def test_migrate_generate_only(self):
        """Test migrate command with generate-only flag."""
        result = self.runner.invoke(
            app, ["workflow", "migrate", str(self.user_yaml), "--generate-only", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Phase 1: Skipped" in result.output

    def test_sync_parallel_processing(self):
        """Test sync command with parallel processing."""
        result = self.runner.invoke(
            app, ["workflow", "sync", str(self.test_dir), "--parallel=2", "--dry-run"]
        )
        assert result.exit_code == 0
        # Parallel option should be accepted

    def test_workflow_error_handling(self):
        """Test error handling in workflow commands."""
        # Test with non-existent file
        result = self.runner.invoke(app, ["workflow", "migrate", "nonexistent.yaml"])
        assert result.exit_code == 2  # Click parameter error
        assert "Error" in result.output or "does not exist" in result.output
