"""Tests for pattern detection CLI commands."""

from cli.confiture_extensions import specql


class TestPatternDetectionCommandRegistration:
    """Test that pattern detection commands are properly registered in CLI."""

    def test_detect_patterns_command_exists(self, cli_runner):
        """Verify pattern detection command is accessible"""
        result = cli_runner.invoke(specql, ["detect-patterns", "--help"])
        assert result.exit_code == 0

    def test_detect_patterns_command_in_main_help(self, cli_runner):
        """Verify 'detect-patterns' command appears in main CLI help"""
        result = cli_runner.invoke(specql, ["--help"])
        assert "detect-patterns" in result.output
        assert "Detect architectural patterns" in result.output


class TestPatternDetectionFunctionality:
    """Test basic functionality of pattern detection commands."""

    def test_detect_patterns_requires_files(self, cli_runner):
        """Test that detect-patterns command requires input files"""
        result = cli_runner.invoke(specql, ["detect-patterns"])
        assert result.exit_code == 2  # Click error for missing required argument
        assert "Missing argument" in result.output

    def test_detect_patterns_in_rust_code(self, cli_runner, tmp_path):
        """Test pattern detection in Rust source"""
        # Create a test Rust file
        rust_code = """
use chrono::{DateTime, Utc};

pub struct Contact {
    pub email: String,
    pub deleted_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}
"""
        test_file = tmp_path / "test_model.rs"
        test_file.write_text(rust_code)

        result = cli_runner.invoke(
            specql, ["detect-patterns", str(test_file), "--min-confidence", "0.3"]
        )

        assert result.exit_code == 0
        assert "soft_delete" in result.output.lower() or "audit_trail" in result.output.lower()

    def test_detect_patterns_with_confidence_threshold(self, cli_runner, tmp_path):
        """Test filtering patterns by confidence"""
        # Create a test file with patterns
        rust_code = """
pub struct Contact {
    pub email: String,
    pub deleted_at: Option<DateTime<Utc>>,
}
"""
        test_file = tmp_path / "test_model.rs"
        test_file.write_text(rust_code)

        result = cli_runner.invoke(
            specql, ["detect-patterns", str(test_file), "--min-confidence", "0.90"]
        )

        assert result.exit_code == 0
