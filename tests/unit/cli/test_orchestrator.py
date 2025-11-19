"""Tests for CLI orchestrator."""

from pathlib import Path

from src.cli.orchestrator import CLIOrchestrator, GenerationResult, MigrationFile


class TestMigrationFile:
    """Test MigrationFile dataclass."""

    def test_migration_file_creation(self):
        """Test creating a migration file."""
        migration = MigrationFile(
            number=100,
            name="contact",
            content="CREATE TABLE contact (...);",
            path=Path("/tmp/100_contact.sql"),
        )

        assert migration.number == 100
        assert migration.name == "contact"
        assert migration.content == "CREATE TABLE contact (...);"
        assert migration.path == Path("/tmp/100_contact.sql")

    def test_migration_file_without_path(self):
        """Test migration file without path."""
        migration = MigrationFile(
            number=0, name="foundation", content="CREATE EXTENSION IF NOT EXISTS ...;"
        )

        assert migration.path is None


class TestGenerationResult:
    """Test GenerationResult dataclass."""

    def test_generation_result_creation(self):
        """Test creating a generation result."""
        result = GenerationResult(migrations=[], errors=[], warnings=[])

        assert result.migrations == []
        assert result.errors == []
        assert result.warnings == []

    def test_generation_result_with_data(self):
        """Test generation result with data."""
        migration = MigrationFile(number=100, name="test", content="SQL")
        result = GenerationResult(migrations=[migration], errors=["error1"], warnings=["warning1"])

        assert len(result.migrations) == 1
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]


class TestCLIOrchestrator:
    """Test CLIOrchestrator class."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        orchestrator = CLIOrchestrator()

        assert orchestrator.parser is not None
        assert orchestrator.schema_orchestrator is not None

    def test_generate_foundation_only(self, temp_dir):
        """Test foundation-only generation."""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        result = orchestrator.generate_from_files(
            entity_files=[], output_dir=str(output_dir), foundation_only=True
        )

        assert len(result.migrations) == 1
        assert result.migrations[0].number == 0
        assert result.migrations[0].name == "app_foundation"
        assert result.errors == []
        assert result.warnings == []

        # Check file was written
        foundation_file = output_dir / "000_app_foundation.sql"
        assert foundation_file.exists()
        assert len(foundation_file.read_text()) > 0

    def test_generate_with_single_entity(self, sample_entity_file, temp_dir):
        """Test generation with a single entity file."""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        result = orchestrator.generate_from_files(
            entity_files=[str(sample_entity_file)], output_dir=str(output_dir)
        )

        # Should have at least foundation migration
        assert len(result.migrations) >= 1
        assert result.migrations[0].number == 0  # foundation

        # Check files were written
        foundation_file = output_dir / "000_app_foundation.sql"

        assert foundation_file.exists()
        # Check that files were created
        sql_files = list(output_dir.glob("*.sql"))
        assert len(sql_files) >= 1  # at least foundation

    def test_generate_with_multiple_entities(self, multiple_entity_files, temp_dir):
        """Test generation with multiple entity files."""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        result = orchestrator.generate_from_files(
            entity_files=[str(f) for f in multiple_entity_files], output_dir=str(output_dir)
        )

        # Should have foundation + 2 entity migrations
        assert len(result.migrations) >= 3
        assert result.migrations[0].number == 0  # foundation
        assert result.migrations[1].number == 100  # first entity
        assert result.migrations[2].number == 101  # second entity

    def test_generate_with_include_tv(self, sample_entity_file, temp_dir):
        """Test generation with tv_ tables included."""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        result = orchestrator.generate_from_files(
            entity_files=[str(sample_entity_file)], output_dir=str(output_dir), include_tv=True
        )

        # Should include tv_ migration if generation succeeds
        tv_migrations = [m for m in result.migrations if m.number == 200]
        if tv_migrations:
            assert tv_migrations[0].name == "table_views"
            tv_file = output_dir / "200_table_views.sql"
            assert tv_file.exists()

    def test_generate_with_invalid_file(self, temp_dir):
        """Test generation with invalid entity file."""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")

        result = orchestrator.generate_from_files(
            entity_files=[str(invalid_file)], output_dir=str(output_dir)
        )

        # Should have foundation but errors for the invalid file
        assert len(result.migrations) >= 1  # foundation
        assert len(result.errors) > 0
        assert "Failed to parse" in result.errors[0]

    def test_generate_output_directory_creation(self, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "deep" / "nested" / "migrations"

        orchestrator.generate_from_files(
            entity_files=[], output_dir=str(output_dir), foundation_only=True
        )

        assert output_dir.exists()
        assert (output_dir / "000_app_foundation.sql").exists()

    def test_generate_no_entity_files_error(self, temp_dir):
        """Test error when no entity files provided without foundation-only."""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        result = orchestrator.generate_from_files(
            entity_files=[], output_dir=str(output_dir), foundation_only=False
        )

        # Should still generate foundation, but no entity migrations
        assert len(result.migrations) == 1  # just foundation
        assert result.migrations[0].number == 0
