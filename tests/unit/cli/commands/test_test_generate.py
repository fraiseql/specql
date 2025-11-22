"""Tests for specql test generate command"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from cli.main import app


class TestGenerateCommand:
    """Test auto-test generation command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_entity(self, tmp_path):
        entity_file = tmp_path / "contact.yaml"
        entity_file.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  first_name: text
  status: enum(lead, qualified, customer)
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
""")
        return entity_file

    def test_generate_pgtap_tests(self, runner, sample_entity, tmp_path):
        """Test pgTAP test file generation"""
        output_dir = tmp_path / "tests"
        result = runner.invoke(
            app, ["test", "generate", str(sample_entity), "-o", str(output_dir), "--type", "pgtap"]
        )

        assert result.exit_code == 0
        test_file = output_dir / "pgtap" / "test_contact.sql"
        assert test_file.exists()
        content = test_file.read_text()
        assert "SELECT plan(" in content
        assert "has_table(" in content
        assert "qualify_lead" in content

    def test_generate_pytest_tests(self, runner, sample_entity, tmp_path):
        """Test pytest test file generation"""
        output_dir = tmp_path / "tests"
        result = runner.invoke(
            app, ["test", "generate", str(sample_entity), "-o", str(output_dir), "--type", "pytest"]
        )

        assert result.exit_code == 0
        test_file = output_dir / "pytest" / "test_contact.py"
        assert test_file.exists()
        content = test_file.read_text()
        assert "class TestContactIntegration" in content
        assert "def test_create_contact" in content
        assert "def test_qualify_lead" in content

    def test_generate_both_types(self, runner, sample_entity, tmp_path):
        """Test generating both pgTAP and pytest"""
        output_dir = tmp_path / "tests"
        result = runner.invoke(
            app, ["test", "generate", str(sample_entity), "-o", str(output_dir), "--type", "both"]
        )

        assert result.exit_code == 0
        assert (output_dir / "pgtap" / "test_contact.sql").exists()
        assert (output_dir / "pytest" / "test_contact.py").exists()

    def test_generate_with_seed(self, runner, sample_entity, tmp_path):
        """Test generating tests with accompanying seed data"""
        output_dir = tmp_path / "tests"
        result = runner.invoke(
            app, ["test", "generate", str(sample_entity), "-o", str(output_dir), "--with-seed"]
        )

        assert result.exit_code == 0
        assert (output_dir / "seeds" / "seed_contact.sql").exists()

    def test_generate_exclude_crud(self, runner, sample_entity, tmp_path):
        """Test excluding CRUD tests"""
        output_dir = tmp_path / "tests"
        result = runner.invoke(
            app,
            [
                "test",
                "generate",
                str(sample_entity),
                "-o",
                str(output_dir),
                "--type",
                "pytest",
                "--no-crud",
            ],
        )

        assert result.exit_code == 0
        content = (output_dir / "pytest" / "test_contact.py").read_text()
        assert "def test_create_contact" not in content
        assert "def test_qualify_lead" in content  # Actions still included

    def test_generate_constraint_tests(self, runner, sample_entity, tmp_path):
        """Test constraint test generation"""
        output_dir = tmp_path / "tests"
        result = runner.invoke(
            app,
            [
                "test",
                "generate",
                str(sample_entity),
                "-o",
                str(output_dir),
                "--type",
                "pgtap",
                "--include-constraints",
            ],
        )

        assert result.exit_code == 0
        content = (output_dir / "pgtap" / "test_contact.sql").read_text()
        assert "constraint" in content.lower() or "col_is_pk" in content
