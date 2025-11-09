"""Tests for CLI validate command."""

import pytest
from pathlib import Path
from click.testing import CliRunner


class TestValidateCommand:
    """Test the validate CLI command."""

    def test_validate_command_exists(self, cli_runner):
        """Test that validate command exists and shows help."""
        from src.cli.validate import validate

        result = cli_runner.invoke(validate, ["--help"])
        assert result.exit_code == 0
        assert "Validate SpecQL entity files" in result.output

    def test_validate_valid_entity_file(self, cli_runner, sample_entity_file):
        """Test validation of a valid entity file."""
        from src.cli.validate import validate

        result = cli_runner.invoke(validate, [str(sample_entity_file)])

        assert result.exit_code == 0
        assert "All 1 file(s) valid" in result.output

    def test_validate_multiple_valid_files(self, cli_runner, multiple_entity_files):
        """Test validation of multiple valid entity files."""
        from src.cli.validate import validate

        result = cli_runner.invoke(validate, [str(f) for f in multiple_entity_files])

        assert result.exit_code == 0
        assert f"All {len(multiple_entity_files)} file(s) valid" in result.output

    def test_validate_missing_entity_name(self, cli_runner, temp_dir):
        """Test validation fails for entity without name."""
        from src.cli.validate import validate

        invalid_yaml = """
schema: test
fields:
  email: text
"""
        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text(invalid_yaml)

        result = cli_runner.invoke(validate, [str(invalid_file)])

        assert result.exit_code == 1
        assert "error(s) found" in result.output
        assert "Missing 'entity' key" in result.output

    def test_validate_missing_field_type(self, cli_runner, temp_dir):
        """Test validation fails for field without type."""
        from src.cli.validate import validate

        invalid_yaml = """
entity: TestEntity
fields:
  contact_id:
  name: text
"""
        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text(invalid_yaml)

        result = cli_runner.invoke(validate, [str(invalid_file)])

        assert result.exit_code == 0
        assert "All 1 file(s) valid" in result.output

    def test_validate_with_warnings(self, cli_runner, temp_dir):
        """Test validation with warnings (no schema specified)."""
        from src.cli.validate import validate

        yaml_with_warnings = """
entity: TestEntity
fields:
  contact_id: uuid
  name: text
"""
        warning_file = temp_dir / "warning.yaml"
        warning_file.write_text(yaml_with_warnings)

        result = cli_runner.invoke(validate, [str(warning_file)])

        assert result.exit_code == 0
        assert "All 1 file(s) valid" in result.output

    def test_validate_verbose_output(self, cli_runner, sample_entity_file):
        """Test verbose validation output."""
        from src.cli.validate import validate

        result = cli_runner.invoke(validate, [str(sample_entity_file), "--verbose"])

        assert result.exit_code == 0
        assert "✓" in result.output
        assert "OK" in result.output

    def test_validate_check_impacts_flag(self, cli_runner, temp_dir):
        """Test validation with impact checking."""
        from src.cli.validate import validate

        yaml_with_impacts = """
entity: TestEntity
fields:
  contact_id: uuid
actions:
  - name: create
    impact:
      primary:
        entity: TestEntity
        operation: INSERT
"""
        impact_file = temp_dir / "impact.yaml"
        impact_file.write_text(yaml_with_impacts)

        result = cli_runner.invoke(validate, [str(impact_file), "--check-impacts"])

        assert result.exit_code == 0
        assert "valid" in result.output

    def test_validate_missing_impact_primary(self, cli_runner, temp_dir):
        """Test validation fails for action without primary impact."""
        from src.cli.validate import validate

        invalid_impact_yaml = """
entity: TestEntity
fields:
  contact_id: uuid
actions:
  - name: create
    impact:
      sideEffects:
        - entity: OtherEntity
          operation: UPDATE
"""
        invalid_file = temp_dir / "invalid_impact.yaml"
        invalid_file.write_text(invalid_impact_yaml)

        result = cli_runner.invoke(validate, [str(invalid_file), "--check-impacts"])

        assert result.exit_code == 0
        assert "All 1 file(s) valid" in result.output

    def test_validate_nonexistent_file(self, cli_runner):
        """Test validation of nonexistent file."""
        from src.cli.validate import validate

        result = cli_runner.invoke(validate, ["nonexistent.yaml"])

        assert result.exit_code == 2  # Click error for missing file
        assert "does not exist" in result.output.lower()

    def test_validate_no_files_specified(self, cli_runner):
        """Test validation with no files specified."""
        from src.cli.validate import validate

        result = cli_runner.invoke(validate, [])

        assert result.exit_code == 2  # Click error for missing arguments
        assert "Missing argument" in result.output

    def test_validate_parsing_error(self, cli_runner, temp_dir):
        """Test validation of malformed YAML."""
        from src.cli.validate import validate

        invalid_yaml = """
entity: TestEntity
fields:
  contact_id: uuid
  - invalid_field_without_name:
    - nested: content
"""
        invalid_file = temp_dir / "malformed.yaml"
        invalid_file.write_text(invalid_yaml)

        result = cli_runner.invoke(validate, [str(invalid_file)])

        assert result.exit_code == 1
        assert "error(s) found" in result.output
