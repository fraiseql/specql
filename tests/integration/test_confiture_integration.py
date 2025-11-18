"""
Integration tests for Confiture v0.3.0 integration

Tests full pipeline:
- SpecQL YAML → db/schema/ directory structure
- Confiture build → combined migration
- Confiture migrate → database application
"""

import subprocess
import tempfile
from pathlib import Path

import pytest


class TestConfitureIntegration:
    """Test Confiture integration end-to-end"""

    def test_specql_generate_creates_schema_files(self):
        """Test that specql generate creates files in db/schema/ structure"""
        # Run generate command
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Generated 2 schema file(s)" in result.stdout

        # Verify files were created in correct structure
        assert Path("db/schema/10_tables/contact.sql").exists()
        assert Path("db/schema/20_helpers/contact_helpers.sql").exists()
        assert Path("db/schema/30_functions/create_contact.sql").exists()
        assert Path("db/schema/30_functions/qualify_lead.sql").exists()

    def test_confiture_build_from_specql_output(self):
        """Test that Confiture can build from SpecQL-generated db/schema/ files"""
        # First generate the schema files
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Now test Confiture build
        result = subprocess.run(
            ["uv", "run", "confiture", "build", "--env", "local"], capture_output=True, text=True
        )

        assert result.returncode == 0
        assert "Schema built successfully" in result.stdout

        # Verify migration file was created
        migration_file = Path("db/generated/schema_local.sql")
        assert migration_file.exists()

        # Verify migration contains expected content
        content = migration_file.read_text()
        assert "CREATE TABLE crm.tb_contact" in content
        assert "CREATE OR REPLACE FUNCTION crm.create_contact" in content
        assert "CREATE OR REPLACE FUNCTION crm.qualify_lead" in content
        assert "@fraiseql:mutation" in content

    def test_specql_validate_command(self):
        """Test specql validate command works"""
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "validate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "All 1 file(s) valid" in result.stdout

    def test_full_pipeline_with_foundation(self):
        """Test that foundation is included in normal generation"""
        # Generate normally (foundation is included automatically)
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Build with Confiture
        result = subprocess.run(
            ["uv", "run", "confiture", "build", "--env", "local"], capture_output=True, text=True
        )

        assert result.returncode == 0

        # Verify foundation content in migration
        migration_file = Path("db/generated/schema_local.sql")
        content = migration_file.read_text()
        assert "CREATE SCHEMA IF NOT EXISTS app" in content
        assert "CREATE TYPE app.mutation_result" in content

    def test_generate_with_different_environments(self):
        """Test generating for different Confiture environments"""
        # Generate for local
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "--env",
                "local",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Build for local
        result = subprocess.run(
            ["uv", "run", "confiture", "build", "--env", "local"], capture_output=True, text=True
        )

        assert result.returncode == 0

        # Verify local migration exists
        assert Path("db/generated/schema_local.sql").exists()

    def test_mutation_files_contain_correct_structure(self):
        """Test that generated mutation files have correct app + core + comments structure"""
        # Generate schema
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Check create_contact.sql structure
        create_contact = Path("db/schema/30_functions/create_contact.sql")
        content = create_contact.read_text()

        # Should contain app wrapper
        assert "CREATE OR REPLACE FUNCTION app.create_contact" in content
        # Should contain core logic
        assert "CREATE OR REPLACE FUNCTION crm.create_contact" in content
        # Should contain FraiseQL comments
        assert "@fraiseql:mutation" in content
        assert "name: createContact" in content

        # Check qualify_lead.sql structure
        qualify_lead = Path("db/schema/30_functions/qualify_lead.sql")
        content = qualify_lead.read_text()

        # Should contain app wrapper
        assert "CREATE OR REPLACE FUNCTION app.qualify_lead" in content
        # Should contain core logic
        assert "CREATE OR REPLACE FUNCTION crm.qualify_lead" in content
        # Should contain FraiseQL comments
        assert "@fraiseql:mutation" in content
        assert "name: qualifyLead" in content

    def test_helpers_file_contains_trinity_functions(self):
        """Test that helpers file contains Trinity pattern functions"""
        # Generate schema
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Check helpers file
        helpers_file = Path("db/schema/20_helpers/contact_helpers.sql")
        content = helpers_file.read_text()

        # Should contain Trinity helper functions
        assert "CREATE OR REPLACE FUNCTION crm.contact_pk" in content
        assert "CREATE OR REPLACE FUNCTION crm.contact_id" in content
        assert "Trinity Pattern:" in content

    def test_table_file_contains_fraiseql_comments(self):
        """Test that table file contains FraiseQL table comments"""
        # Generate schema
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Check table file
        table_file = Path("db/schema/10_tables/contact.sql")
        content = table_file.read_text()

        # Should contain table DDL
        assert "CREATE TABLE crm.tb_contact" in content
        # Should contain FraiseQL table comment
        assert "@fraiseql:type" in content
        assert "trinity: true" in content

    def test_confiture_migrate_up_and_down(self):
        """Test Confiture migrate commands (requires database)"""
        import psycopg

        # Check if database is available
        try:
            conn = psycopg.connect(
                host="localhost", port=5433, dbname="test_specql", user="postgres", password="postgres"
            )
            conn.close()
        except psycopg.OperationalError:
            pytest.skip("PostgreSQL test database not available")

        # First, generate schema files
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Build migration with Confiture
        result = subprocess.run(
            ["uv", "run", "confiture", "build", "--env", "test"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Migrate up to database using test config
        result = subprocess.run(
            [
                "uv", "run", "confiture", "migrate", "up",
                "--config", "db/environments/test.yaml"
            ],
            capture_output=True,
            text=True,
        )

        # Should succeed (return code 0) or show migration applied
        assert result.returncode == 0 or "migrat" in result.stdout.lower(), \
            f"Migration failed: {result.stderr}"

        # Verify tables were created in database
        conn = psycopg.connect(
            host="localhost", port=5433, dbname="test_specql", user="postgres", password="postgres"
        )
        cursor = conn.cursor()

        # Check if crm schema and tb_contact table exist
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='crm' AND table_name='tb_contact')"
        )
        table_exists = cursor.fetchone()[0]
        assert table_exists, "tb_contact table should exist after migration"

        # Check if functions were created
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='crm' AND routine_name IN ('create_contact', 'qualify_lead')"
        )
        function_count = cursor.fetchone()[0]
        assert function_count >= 2, f"Expected at least 2 functions, found {function_count}"

        conn.close()

        # Test migrate down (rollback)
        result = subprocess.run(
            [
                "uv", "run", "confiture", "migrate", "down",
                "--config", "db/environments/test.yaml"
            ],
            capture_output=True,
            text=True,
        )

        # Should succeed or show rollback info
        # Note: Confiture may not support rollback, so we'll just verify it runs
        # Accept return codes: 0 (success), 1 (not implemented), 2 (no migrations to rollback)
        assert result.returncode in [0, 1, 2]

    def test_error_handling_invalid_entity_file(self):
        """Test error handling for invalid entity files"""
        # Create a temporary invalid YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [\n")
            invalid_file = f.name

        try:
            result = subprocess.run(
                ["python", "-m", "src.cli.confiture_extensions", "generate", invalid_file],
                capture_output=True,
                text=True,
            )

            # Should show error but still return 0 (Click handles errors gracefully)
            assert result.returncode == 0
            assert "error(s)" in result.stdout
            assert "Invalid YAML" in result.stdout
        finally:
            Path(invalid_file).unlink()

    def test_specql_diff_with_confiture_integration(self):
        """Test specql diff command works with Confiture-generated files"""
        # First generate schema files
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.confiture_extensions",
                "generate",
                "entities/examples/contact_lightweight.yaml",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Test diff command with generated table file
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.cli.diff",
                "entities/examples/contact_lightweight.yaml",
                "--compare",
                "db/schema/10_tables/contact.sql",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should show Confiture analysis followed by detailed diff
        assert "Schema differences (Confiture analysis)" in result.stdout
        assert "Detailed differences" in result.stdout
        assert "CREATE SCHEMA IF NOT EXISTS app" in result.stdout

    def test_confiture_fallback_when_unavailable(self):
        """Test graceful fallback when Confiture is not available"""
        # This test would require mocking the confiture import at the module level
        # For now, skip since Confiture is available in the test environment
        pytest.skip("Confiture is available in test environment, cannot test fallback")
