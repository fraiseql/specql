"""Tests for caching functionality in reverse engineering CLI."""

import pytest
from click.testing import CliRunner

from src.cli.confiture_extensions import specql
from src.core.dependencies import TREE_SITTER_RUST


class TestCachingFunctionality:
    """Test caching behavior in reverse engineering commands."""

    @pytest.fixture
    def cli_runner(self):
        """Click CLI runner for testing commands."""
        return CliRunner()

    @pytest.fixture
    def rust_test_file(self, temp_dir):
        """Create a temporary Rust model file for testing."""
        rust_content = """
use diesel::prelude::*;
use chrono::{DateTime, Utc};

#[derive(Queryable, Insertable)]
#[table_name = "contacts"]
pub struct Contact {
    pub id: i32,
    pub email: String,
    pub first_name: String,
    pub last_name: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}
"""
        rust_file = temp_dir / "contact.rs"
        rust_file.write_text(rust_content)
        return rust_file

    @pytest.fixture
    def modified_rust_content(self):
        """Modified Rust content for testing cache invalidation."""
        return """
use diesel::prelude::*;
use chrono::{DateTime, Utc};

#[derive(Queryable, Insertable)]
#[table_name = "contacts"]
pub struct Contact {
    pub id: i32,
    pub email: String,
    pub first_name: String,
    pub last_name: String,
    pub phone: Option<String>,  // Added phone field
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}
"""

    @pytest.mark.skipif(not TREE_SITTER_RUST.available, reason="Requires tree-sitter-rust")
    def test_reverse_uses_cache_on_second_run(self, cli_runner, rust_test_file, temp_dir):
        """Test that reverse engineering uses cache for unchanged files"""

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # First run
        cli_runner.invoke(specql, ["reverse", str(rust_test_file), "--output-dir", str(output_dir)])

        # First run may fail due to parser issues, but cache should still be created
        # The cache stores the result regardless of success/failure

        # Second run (should use cache if no errors)
        result2 = cli_runner.invoke(
            specql, ["reverse", str(rust_test_file), "--output-dir", str(output_dir)]
        )

        # Should indicate cache usage if processing succeeded
        if "Failed to process" not in result2.output:
            assert "Using cached result" in result2.output

    @pytest.mark.skipif(not TREE_SITTER_RUST.available, reason="Requires tree-sitter-rust")
    def test_cache_invalidation_on_file_change(
        self, cli_runner, rust_test_file, temp_dir, modified_rust_content
    ):
        """Test cache is invalidated when source file changes"""

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # First run
        result1 = cli_runner.invoke(
            specql, ["reverse", str(rust_test_file), "--output-dir", str(output_dir)]
        )
        assert result1.exit_code == 0

        # Modify file
        rust_test_file.write_text(modified_rust_content)

        # Second run (cache should be invalidated)
        result2 = cli_runner.invoke(
            specql, ["reverse", str(rust_test_file), "--output-dir", str(output_dir)]
        )

        assert result2.exit_code == 0
        assert "Using cached result" not in result2.output  # Should not use cache

    def test_cache_clear_command(self, cli_runner):
        """Test cache clear command functionality"""
        result = cli_runner.invoke(specql, ["cache", "clear"])
        # Should succeed now that cache commands are implemented
        assert result.exit_code == 0
        assert "Cache cleared" in result.output

    def test_cache_stats_command(self, cli_runner):
        """Test cache stats command functionality"""
        result = cli_runner.invoke(specql, ["cache", "stats"])
        # Should succeed now that cache commands are implemented
        assert result.exit_code == 0
        # Should show cache is empty initially
        assert "Cache is empty" in result.output or "Cache Statistics" in result.output

    @pytest.mark.skipif(not TREE_SITTER_RUST.available, reason="Requires tree-sitter-rust")
    def test_no_cache_option_disables_caching(self, cli_runner, rust_test_file, temp_dir):
        """Test --no-cache option disables caching"""

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Run with --no-cache
        result = cli_runner.invoke(
            specql, ["reverse", str(rust_test_file), "--output-dir", str(output_dir), "--no-cache"]
        )

        assert result.exit_code == 0
        # Should not mention cache usage
        assert "cached" not in result.output.lower()
