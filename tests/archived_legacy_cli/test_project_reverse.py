"""Integration tests for project-level reverse engineering."""

import pytest
from cli.confiture_extensions import specql
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """CLI runner for testing."""
    return CliRunner()


class TestProjectLevelReverseEngineering:
    """Test project-level reverse engineering functionality."""

    def test_reverse_entire_rust_project(self, cli_runner, tmp_path):
        """Test reversing an entire Rust project directory"""
        # Create a test project structure
        project_dir = tmp_path / "test_rust_project"
        project_dir.mkdir()

        (project_dir / "src").mkdir()
        (project_dir / "src" / "models").mkdir()

        # Create test Rust files
        contact_rs = project_dir / "src" / "models" / "contact.rs"
        contact_rs.write_text(
            """
use chrono::{DateTime, Utc};
use diesel::prelude::*;

#[derive(Queryable, Insertable)]
#[table_name = "contacts"]
pub struct Contact {
    pub id: Uuid,
    pub email: String,
    pub deleted_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}
"""
        )

        company_rs = project_dir / "src" / "models" / "company.rs"
        company_rs.write_text(
            """
use chrono::{DateTime, Utc};
use diesel::prelude::*;

#[derive(Queryable, Insertable)]
#[table_name = "companies"]
pub struct Company {
    pub id: Uuid,
    pub name: String,
    pub tenant_id: Uuid,
}
"""
        )

        result = cli_runner.invoke(
            specql,
            [
                "reverse",
                str(project_dir),
                "--framework",
                "diesel",
                "--with-patterns",
                "--output-dir",
                str(tmp_path / "output"),
                "--preview",  # Use preview to avoid actual file writing issues
            ],
        )

        assert result.exit_code == 0
        assert "Discovered" in result.output
        assert "files" in result.output

    def test_reverse_with_exclude_patterns(self, cli_runner, tmp_path):
        """Test excluding certain files from reverse engineering"""
        # Create test project with files to exclude
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        (project_dir / "src").mkdir()
        (project_dir / "src" / "models").mkdir()
        (project_dir / "tests").mkdir()

        # Create model file
        model_file = project_dir / "src" / "models" / "user.rs"
        model_file.write_text(
            """
pub struct User {
    pub id: Uuid,
    pub email: String,
}
"""
        )

        # Create test file that should be excluded
        test_file = project_dir / "tests" / "user_test.rs"
        test_file.write_text(
            """
#[test]
fn test_user() {
    // test code
}
"""
        )

        result = cli_runner.invoke(
            specql,
            [
                "reverse",
                str(project_dir),
                "--framework",
                "rust",
                "--exclude",
                "*/tests/*",
                "--preview",
            ],
        )

        assert result.exit_code == 0
        # Should not mention test files
        assert "user_test.rs" not in result.output
