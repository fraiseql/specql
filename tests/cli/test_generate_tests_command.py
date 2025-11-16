"""Tests for generate-tests CLI command."""

import pytest
from click.testing import CliRunner
from src.cli.confiture_extensions import specql


class TestGenerateTestsCommand:
    """Test generate-tests CLI command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def sample_entity(self, tmp_path):
        """Create sample entity YAML file."""
        entity_file = tmp_path / "contact.yaml"
        entity_file.write_text("""
entity: Contact
schema: crm

fields:
  email: email
  first_name: text
  last_name: text
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
        """)
        return entity_file

    def test_generate_tests_function_basic(self):
        """Test generate_tests core function directly."""
        from src.cli.generate_tests import _generate_tests_core
        import tempfile
        from pathlib import Path

        # Create a temporary entity file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
entity: TestEntity
schema: test
fields:
  name: text
  email: email
""")
            entity_file = f.name

        try:
            # Test with preview mode (should not fail)
            with tempfile.TemporaryDirectory() as output_dir:
                # This should not raise an exception
                result = _generate_tests_core(
                    entity_files=(entity_file,),
                    test_type="pgtap",
                    output_dir=output_dir,
                    preview=True,
                    verbose=False,
                    overwrite=False,
                )
                # Function should return 0 on success
                assert result == 0
        finally:
            Path(entity_file).unlink(missing_ok=True)

    def test_generate_tests_requires_entity_file(self, runner):
        """generate-tests should require entity file."""
        result = runner.invoke(specql, ["generate-tests"])
        assert result.exit_code != 0
        assert "entity" in result.output.lower() or "Usage" in result.output

    def test_generate_tests_pgtap_only(self, runner, sample_entity, tmp_path):
        """generate-tests --type pgtap should generate only pgTAP tests."""
        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                "generate-tests",
                str(sample_entity),
                "--type",
                "pgtap",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Should create pgTAP test files
        assert (output_dir / "test_contact_structure.sql").exists()
        assert (output_dir / "test_contact_crud.sql").exists()

        # Should NOT create pytest files
        assert not any(output_dir.glob("*.py"))

    def test_generate_tests_pytest_only(self, runner, sample_entity, tmp_path):
        """generate-tests --type pytest should generate only pytest tests."""
        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                "generate-tests",
                str(sample_entity),
                "--type",
                "pytest",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0

        # Should create pytest test files
        assert (output_dir / "test_contact_integration.py").exists()

        # Should NOT create SQL files
        assert not any(output_dir.glob("*.sql"))

    def test_generate_tests_all_types(self, runner, sample_entity, tmp_path):
        """generate-tests --type all should generate both pgTAP and pytest."""
        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                "generate-tests",
                str(sample_entity),
                "--type",
                "all",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0

        # Should create both pgTAP and pytest
        assert (output_dir / "test_contact_structure.sql").exists()
        assert (output_dir / "test_contact_crud.sql").exists()
        assert (output_dir / "test_contact_integration.py").exists()

    def test_generate_tests_multiple_entities(self, runner, tmp_path):
        """generate-tests should handle multiple entity files."""
        # Create multiple entities
        contact = tmp_path / "contact.yaml"
        contact.write_text("entity: Contact\nschema: crm\nfields:\n  email: email")

        company = tmp_path / "company.yaml"
        company.write_text("entity: Company\nschema: crm\nfields:\n  name: text")

        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                "generate-tests",
                str(contact),
                str(company),
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0

        # Should create tests for both entities
        assert any("contact" in f.name.lower() for f in output_dir.iterdir())
        assert any("company" in f.name.lower() for f in output_dir.iterdir())

    def test_generate_tests_preview_mode(self, runner, sample_entity, tmp_path):
        """generate-tests --preview should not write files."""
        output_dir = tmp_path / "tests"

        result = runner.invoke(
            specql,
            [
                "generate-tests",
                str(sample_entity),
                "--preview",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Preview" in result.output or "preview" in result.output

        # Should NOT create any files
        assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0

    def test_generated_pgtap_content(self, runner, sample_entity, tmp_path):
        """Generated pgTAP tests should have correct content."""
        output_dir = tmp_path / "tests"

        runner.invoke(
            specql,
            [
                "generate-tests",
                str(sample_entity),
                "--type",
                "pgtap",
                "--output-dir",
                str(output_dir),
            ],
        )

        structure_test = (output_dir / "test_contact_structure.sql").read_text()

        # Verify pgTAP test structure
        assert "BEGIN;" in structure_test
        assert "SELECT plan(" in structure_test
        assert "has_table" in structure_test
        assert "crm" in structure_test
        assert "tb_contact" in structure_test
        assert "SELECT * FROM finish();" in structure_test
        assert "ROLLBACK;" in structure_test

    def test_generated_pytest_content(self, runner, sample_entity, tmp_path):
        """Generated pytest tests should have correct content."""
        output_dir = tmp_path / "tests"

        runner.invoke(
            specql,
            [
                "generate-tests",
                str(sample_entity),
                "--type",
                "pytest",
                "--output-dir",
                str(output_dir),
            ],
        )

        pytest_test = (output_dir / "test_contact_integration.py").read_text()

        # Verify pytest test structure
        assert "import pytest" in pytest_test
        assert "class TestContactIntegration" in pytest_test
        assert "def test_create_contact" in pytest_test
        assert "app.create_contact" in pytest_test
        assert "assert result['status'] == 'success'" in pytest_test
