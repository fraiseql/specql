"""End-to-end tests for pattern detection CLI."""

import tempfile

import pytest
from cli.confiture_extensions import specql


class TestPatternDetectionE2E:
    """E2E tests for pattern detection functionality."""

    @pytest.fixture
    def cli_runner(self):
        """CLI runner fixture."""
        from click.testing import CliRunner

        return CliRunner()

    def test_detect_soft_delete_in_rust(self, cli_runner):
        """E2E test: Detect soft delete pattern in Rust code"""
        rust_code = """
use chrono::{DateTime, Utc};

#[derive(Queryable, Insertable)]
pub struct Contact {
    pub id: Uuid,
    pub email: String,
    pub deleted_at: Option<DateTime<Utc>>,
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_file = f.name

        result = cli_runner.invoke(
            specql, ["detect-patterns", temp_file, "--min-confidence", "0.3"]
        )

        assert result.exit_code == 0
        assert "soft_delete" in result.output.lower()
        assert "confidence" in result.output.lower()

    def test_detect_multiple_patterns_in_rust(self, cli_runner):
        """E2E test: Detect multiple patterns in comprehensive Rust code"""
        rust_code = """
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Queryable, Insertable)]
pub struct Contact {
    pub id: Uuid,
    pub tenant_id: Uuid,
    pub email: String,
    pub deleted_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub created_by: Option<Uuid>,
    pub updated_by: Option<Uuid>,
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_file = f.name

        result = cli_runner.invoke(
            specql, ["detect-patterns", temp_file, "--min-confidence", "0.3"]
        )

        assert result.exit_code == 0
        assert "soft_delete" in result.output.lower()
        assert "audit_trail" in result.output.lower()
        assert "multi_tenant" in result.output.lower()

    def test_detect_patterns_json_output(self, cli_runner):
        """E2E test: JSON output format"""
        rust_code = """
pub struct Contact {
    pub deleted_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_file = f.name

        result = cli_runner.invoke(
            specql, ["detect-patterns", temp_file, "--format", "json", "--min-confidence", "0.3"]
        )

        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert "patterns" in data[0]

    def test_detect_specific_patterns_only(self, cli_runner):
        """E2E test: Detect only specified patterns"""
        rust_code = """
pub struct Contact {
    pub deleted_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub tenant_id: Uuid,
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_file = f.name

        result = cli_runner.invoke(
            specql,
            ["detect-patterns", temp_file, "--patterns", "soft_delete", "--min-confidence", "0.3"],
        )

        assert result.exit_code == 0
        assert "soft_delete" in result.output.lower()
        # Should not contain other patterns
        assert "audit_trail" not in result.output.lower()
        assert "multi_tenant" not in result.output.lower()
