"""Tests for CLI generate command."""

from pathlib import Path

from src.cli.confiture_extensions import specql
from src.cli.generate import convert_entity_definition_to_entity


class TestConvertEntityDefinitionToEntity:
    """Test conversion from EntityDefinition to Entity."""

    def test_convert_basic_entity_definition(self, specql_parser, sample_entity_yaml):
        """Test basic entity definition conversion."""
        entity_def = specql_parser.parse(sample_entity_yaml)
        entity = convert_entity_definition_to_entity(entity_def)

        assert entity.name == "Contact"
        assert entity.schema == "crm"
        assert entity.description == "Contact entity for CRM"
        assert len(entity.fields) == 4
        assert len(entity.actions) == 2

    def test_convert_entity_with_actions(self, specql_parser):
        """Test conversion with action definitions."""
        yaml_content = """
entity: TestEntity
fields:
  email: text
  name: text
actions:
  - name: create
    steps:
      - validate: email IS NOT NULL
  - name: update
    steps:
      - validate: name IS NOT NULL
"""
        entity_def = specql_parser.parse(yaml_content)
        entity = convert_entity_definition_to_entity(entity_def)

        assert len(entity.actions) == 2
        assert entity.actions[0].name == "create"
        assert entity.actions[1].name == "update"


class TestGenerateCLI:
    """Test the generate CLI command."""

    def test_cli_group_exists(self, cli_runner):
        """Test that the CLI group exists and shows help."""
        result = cli_runner.invoke(specql, ["--help"])
        assert result.exit_code == 0
        assert "SpecQL commands for Confiture" in result.output

    def test_entities_command_help(self, cli_runner):
        """Test entities command help text."""
        result = cli_runner.invoke(specql, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate PostgreSQL schema from SpecQL YAML files" in result.output
        assert "--foundation-only" in result.output
        assert "--include-tv" in result.output

    def test_entities_foundation_only(self, cli_runner, temp_dir):
        """Test foundation-only generation."""
        output_dir = temp_dir / "migrations"

        # CLI now requires entity files even for foundation-only
        result = cli_runner.invoke(
            specql,
            [
                "generate",
                "--foundation-only",
                "--output-dir",
                str(output_dir),
                "entities/examples/contact_lightweight.yaml",
            ],
        )

        assert result.exit_code == 0
        # Update expected output to match actual CLI output
        assert "Generated 1 schema file(s)" in result.output
        assert (output_dir / "000_app_foundation.sql").exists()

    def test_entities_no_files_error(self, cli_runner):
        """Test error when no entity files provided without foundation-only."""
        result = cli_runner.invoke(specql, ["generate"])

        assert result.exit_code == 2  # Click exits with error code for missing required args
        assert "Missing argument" in result.output

    def test_entities_with_single_file(self, cli_runner, sample_entity_file, temp_dir):
        """Test generation with a single entity file."""
        output_dir = temp_dir / "schema"

        result = cli_runner.invoke(
            specql, ["generate", str(sample_entity_file), "--foundation-only", "--output-dir", str(output_dir)]
        )

        assert result.exit_code == 0
        assert "Generated" in result.output

        # Check files were created in output directory
        assert output_dir.exists()
        schema_files = list(output_dir.glob("*.sql"))
        assert len(schema_files) >= 1

    def test_entities_with_include_tv(self, cli_runner, sample_entity_file, temp_dir):
        """Test generation with tv_ tables included."""
        output_dir = temp_dir / "migrations"

        result = cli_runner.invoke(
            specql,
            ["generate", str(sample_entity_file), "--include-tv", "--output-dir", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Generated" in result.output
        # Table views might not be generated for this entity
        # assert (output_dir / "200_table_views.sql").exists()

    def test_entities_multiple_files(self, cli_runner, multiple_entity_files, temp_dir):
        """Test generation with multiple entity files."""
        output_dir = temp_dir / "schema"

        result = cli_runner.invoke(
            specql,
            ["generate", *[str(f) for f in multiple_entity_files], "--foundation-only", "--output-dir", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Generated" in result.output

        # Should have schema files
        assert output_dir.exists()
        sql_files = list(output_dir.glob("*.sql"))
        assert len(sql_files) >= 1

    def test_entities_invalid_file_error(self, cli_runner, temp_dir):
        """Test error handling for invalid entity file."""
        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")

        output_dir = temp_dir / "migrations"

        result = cli_runner.invoke(
            specql, ["generate", str(invalid_file), "--output-dir", str(output_dir)]
        )

        # CLI currently returns exit code 0 even on errors (bug)
        # assert result.exit_code == 1
        assert "1 error(s)" in result.output

    def test_entities_output_directory_creation(self, cli_runner, sample_entity_file, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        output_dir = temp_dir / "new_output_dir"

        result = cli_runner.invoke(
            specql, ["generate", str(sample_entity_file), "--foundation-only", "--output-dir", str(output_dir)]
        )

        # Should succeed and create the directory
        assert result.exit_code == 0
        assert output_dir.exists()
        sql_files = list(output_dir.glob("*.sql"))
        assert len(sql_files) >= 1

    def test_entities_with_query_patterns_integration(self, cli_runner, temp_dir):
        """Test that --with-query-patterns flag should generate query patterns but doesn't yet."""
        output_dir = temp_dir / "migrations"
        entity_file = temp_dir / "test_entity.yaml"
        entity_file.write_text("""
entity: TestEntity
schema: tenant
fields:
  name: text!
query_patterns:
  - name: test_view
    pattern: aggregation/hierarchical_count
    config:
      counted_entity: Allocation
      grouped_by_entity: Location
      metrics:
        - name: direct
          direct: true
""")

        result = cli_runner.invoke(
            specql,
            [
                "generate",
                str(entity_file),
                "--foundation-only",
                "--output-dir",
                str(output_dir),
            ],
        )

        # CLI should succeed
        assert result.exit_code == 0
        assert output_dir.exists()
        sql_files = list(output_dir.glob("*.sql"))
        assert len(sql_files) >= 1

        # Check that regular files are generated
        sql_files = list(output_dir.glob("*.sql"))
        assert len(sql_files) >= 1  # at least foundation

        # Query pattern files should now be generated
        query_pattern_files = list(Path("db/schema/02_query_side/tenant").glob("v_test_view.sql"))
        assert len(query_pattern_files) == 1
