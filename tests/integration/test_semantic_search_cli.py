"""Integration tests for semantic search CLI"""
import subprocess
import pytest
import os


@pytest.fixture
def db_url():
    """Get database URL"""
    return os.getenv("SPECQL_DB_URL", "postgresql://specql_user:specql_dev_password@localhost/specql")


@pytest.mark.skipif(
    not os.getenv("SPECQL_DB_URL"),
    reason="Requires PostgreSQL database"
)
class TestSemanticSearchCLI:
    """Test semantic search CLI commands"""

    def test_search_command(self):
        """Test basic search command"""
        result = subprocess.run(
            ["specql", "patterns", "search", "email validation", "--limit", "5"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Found" in result.stdout or "No matching patterns found" in result.stdout

    def test_search_with_category_filter(self):
        """Test search with category filter"""
        result = subprocess.run(
            [
                "specql", "patterns", "search", "validation",
                "--category", "validation",
                "--limit", "10"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should either find results or indicate no matches
        assert "Found" in result.stdout or "No matching patterns found" in result.stdout

    def test_similar_command(self):
        """Test finding similar patterns"""
        # First check if email_validation pattern exists
        check_result = subprocess.run(
            ["specql", "patterns", "get", "email_validation"],
            capture_output=True,
            text=True
        )

        if check_result.returncode == 0:
            # Pattern exists, test similar
            result = subprocess.run(
                ["specql", "patterns", "similar", "email_validation", "--limit", "3"],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0
            assert "similar" in result.stdout.lower() or "No similar patterns found" in result.stdout
        else:
            # Pattern doesn't exist, skip test
            pytest.skip("email_validation pattern not found in database")

    def test_recommend_command(self):
        """Test pattern recommendations"""
        result = subprocess.run(
            [
                "specql", "patterns", "recommend",
                "--entity-description", "Customer contact information",
                "--field", "email",
                "--field", "phone",
                "--limit", "5"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Recommended" in result.stdout or "No pattern recommendations found" in result.stdout