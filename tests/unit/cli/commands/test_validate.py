"""
Tests for the validate CLI command.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import app


@pytest.fixture
def cli_runner():
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def valid_entity_yaml():
    """Valid SpecQL entity YAML."""
    return """entity: Contact
schema: crm
fields:
  email: text
  phone: text
  status: enum(lead, qualified, customer)
"""


@pytest.fixture
def invalid_yaml():
    """Invalid YAML syntax."""
    return """entity:
  - this: is
  invalid: [yaml
"""


@pytest.fixture
def missing_entity_yaml():
    """YAML missing required entity key."""
    return """schema: crm
fields:
  email: text
"""


class TestValidateCommand:
    """Tests for specql validate command."""

    def test_validate_shows_in_help(self, cli_runner):
        """Validate command should appear in main help."""
        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "validate" in result.output

    def test_validate_help(self, cli_runner):
        """Validate --help should show usage."""
        result = cli_runner.invoke(app, ["validate", "--help"])

        assert result.exit_code == 0
        assert "Validate SpecQL YAML" in result.output
        assert "--strict" in result.output
        assert "--schema-registry" in result.output

    def test_validate_requires_files(self, cli_runner):
        """Validate should require at least one file argument."""
        result = cli_runner.invoke(app, ["validate"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "required" in result.output.lower()

    def test_validate_valid_yaml(self, cli_runner, valid_entity_yaml):
        """Validate should pass for valid YAML."""
        with cli_runner.isolated_filesystem():
            Path("entity.yaml").write_text(valid_entity_yaml)

            result = cli_runner.invoke(app, ["validate", "entity.yaml"])

            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_validate_invalid_yaml_syntax(self, cli_runner, invalid_yaml):
        """Validate should fail for invalid YAML syntax."""
        with cli_runner.isolated_filesystem():
            Path("bad.yaml").write_text(invalid_yaml)

            result = cli_runner.invoke(app, ["validate", "bad.yaml"])

            assert result.exit_code == 1
            assert "failed" in result.output.lower() or "error" in result.output.lower()

    def test_validate_missing_entity_key(self, cli_runner, missing_entity_yaml):
        """Validate should fail when entity key is missing."""
        with cli_runner.isolated_filesystem():
            Path("no_entity.yaml").write_text(missing_entity_yaml)

            result = cli_runner.invoke(app, ["validate", "no_entity.yaml"])

            assert result.exit_code == 1
            assert "entity" in result.output.lower()

    def test_validate_multiple_files(self, cli_runner, valid_entity_yaml):
        """Validate should handle multiple files."""
        with cli_runner.isolated_filesystem():
            Path("entity1.yaml").write_text(valid_entity_yaml)
            Path("entity2.yaml").write_text(valid_entity_yaml.replace("Contact", "Organization"))

            result = cli_runner.invoke(app, ["validate", "entity1.yaml", "entity2.yaml"])

            assert result.exit_code == 0
            assert "2 file(s) valid" in result.output

    def test_validate_mixed_valid_invalid(self, cli_runner, valid_entity_yaml, invalid_yaml):
        """Validate should report both valid and invalid files."""
        with cli_runner.isolated_filesystem():
            Path("good.yaml").write_text(valid_entity_yaml)
            Path("bad.yaml").write_text(invalid_yaml)

            result = cli_runner.invoke(app, ["validate", "good.yaml", "bad.yaml"])

            assert result.exit_code == 1
            assert "1 file(s) failed" in result.output

    def test_validate_verbose(self, cli_runner, valid_entity_yaml):
        """Validate --verbose should show entity names."""
        with cli_runner.isolated_filesystem():
            Path("entity.yaml").write_text(valid_entity_yaml)

            result = cli_runner.invoke(app, ["validate", "entity.yaml", "--verbose"])

            assert result.exit_code == 0
            assert "Contact" in result.output

    def test_validate_strict_warns_on_public_schema(self, cli_runner):
        """Validate --strict should fail on warnings like default schema."""
        yaml_content = """entity: Contact
fields:
  email: text
"""
        with cli_runner.isolated_filesystem():
            Path("entity.yaml").write_text(yaml_content)

            # Without --strict, should pass with warning
            result = cli_runner.invoke(app, ["validate", "entity.yaml"])
            assert result.exit_code == 0
            assert "warning" in result.output.lower()

            # With --strict, should fail
            result = cli_runner.invoke(app, ["validate", "entity.yaml", "--strict"])
            assert result.exit_code == 1

    def test_validate_warns_on_camel_case_fields(self, cli_runner):
        """Validate should warn about camelCase field names."""
        yaml_content = """entity: Contact
schema: crm
fields:
  firstName: text
  lastName: text
"""
        with cli_runner.isolated_filesystem():
            Path("entity.yaml").write_text(yaml_content)

            result = cli_runner.invoke(app, ["validate", "entity.yaml"])

            assert result.exit_code == 0
            assert "camelCase" in result.output or "snake_case" in result.output

    def test_validate_nonexistent_file(self, cli_runner):
        """Validate should fail for nonexistent files."""
        result = cli_runner.invoke(app, ["validate", "nonexistent.yaml"])

        assert result.exit_code != 0

    def test_validate_with_actions(self, cli_runner):
        """Validate should handle entities with actions."""
        yaml_content = """entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified)
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
"""
        with cli_runner.isolated_filesystem():
            Path("entity.yaml").write_text(yaml_content)

            result = cli_runner.invoke(app, ["validate", "entity.yaml"])

            assert result.exit_code == 0
            assert "valid" in result.output.lower()


class TestValidateEdgeCases:
    """Edge case tests for validate command."""

    def test_validate_empty_file(self, cli_runner):
        """Validate should handle empty files gracefully."""
        with cli_runner.isolated_filesystem():
            Path("empty.yaml").write_text("")

            result = cli_runner.invoke(app, ["validate", "empty.yaml"])

            assert result.exit_code == 1

    def test_validate_non_dict_yaml(self, cli_runner):
        """Validate should fail for non-dictionary YAML."""
        with cli_runner.isolated_filesystem():
            Path("list.yaml").write_text("- item1\n- item2\n")

            result = cli_runner.invoke(app, ["validate", "list.yaml"])

            assert result.exit_code == 1

    def test_validate_complex_entity_format(self, cli_runner):
        """Validate should handle complex entity format."""
        yaml_content = """entity:
  name: Contact
  schema: crm
  description: Contact entity for CRM
fields:
  email: text
"""
        with cli_runner.isolated_filesystem():
            Path("entity.yaml").write_text(yaml_content)

            result = cli_runner.invoke(app, ["validate", "entity.yaml"])

            assert result.exit_code == 0
