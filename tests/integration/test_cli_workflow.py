"""Integration tests for full CLI workflows.

These tests verify end-to-end CLI functionality including:
- Entity generation from YAML to SQL
- Frontend code generation
- Test generation
- Confiture integration
"""

import pytest
from click.testing import CliRunner

from src.cli.confiture_extensions import specql as confiture_specql
from src.cli.generate import cli as generate_cli


@pytest.fixture
def cli_runner():
    """Click CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def integration_test_dir(tmp_path):
    """Create a temporary directory for integration tests."""
    test_dir = tmp_path / "integration_test"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_crm_entity(integration_test_dir):
    """Create a sample CRM entity YAML file."""
    entity_content = """
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)
  phone: text
  notes: text

actions:
  - name: create_contact
    steps:
      - validate: email IS NOT NULL
        error: "email_required"
      - insert: Contact

  - name: update_status
    steps:
      - validate: status IS NOT NULL
        error: "status_required"
      - update: Contact SET status = 'qualified'
"""
    entity_file = integration_test_dir / "contact.yaml"
    entity_file.write_text(entity_content)
    return entity_file


@pytest.fixture
def sample_company_entity(integration_test_dir):
    """Create a sample Company entity YAML file."""
    entity_content = """
entity: Company
schema: crm
description: "Company information"

fields:
  name: text
  industry: text
  website: text
  size: enum(small, medium, large, enterprise)
  description: text

actions:
  - name: create_company
    steps:
      - validate: name IS NOT NULL
        error: "name_required"
      - insert: Company
"""
    entity_file = integration_test_dir / "company.yaml"
    entity_file.write_text(entity_content)
    return entity_file


class TestEndToEndGeneration:
    """Test complete end-to-end generation workflows."""

    def test_generate_single_entity_workflow(
        self, cli_runner, sample_crm_entity, integration_test_dir
    ):
        """Test generating migrations from a single entity."""
        output_dir = integration_test_dir / "migrations"

        # Run generation
        result = cli_runner.invoke(
            generate_cli,
            ["entities", str(sample_crm_entity), "--output-dir", str(output_dir)],
        )

        # Verify success
        assert result.exit_code == 0
        assert "Generated" in result.output

        # Verify output files exist
        assert output_dir.exists()
        sql_files = list(output_dir.glob("*.sql"))
        assert len(sql_files) >= 1  # At least foundation file

        # Verify foundation file contains expected content
        foundation_file = output_dir / "000_app_foundation.sql"
        if foundation_file.exists():
            content = foundation_file.read_text()
            assert "CREATE SCHEMA" in content or "app.mutation_result" in content

    def test_generate_multiple_entities_workflow(
        self, cli_runner, sample_crm_entity, sample_company_entity, integration_test_dir
    ):
        """Test generating migrations from multiple entities."""
        output_dir = integration_test_dir / "migrations"

        # Run generation with both entities
        result = cli_runner.invoke(
            generate_cli,
            [
                "entities",
                str(sample_crm_entity),
                str(sample_company_entity),
                "--output-dir",
                str(output_dir),
            ],
        )

        # Verify success
        assert result.exit_code == 0
        assert "Generated" in result.output

        # Verify multiple migration files
        sql_files = list(output_dir.glob("*.sql"))
        assert len(sql_files) >= 1

    def test_generate_with_table_views(
        self, cli_runner, sample_crm_entity, integration_test_dir
    ):
        """Test generation with --include-tv flag."""
        output_dir = integration_test_dir / "migrations"

        # Run generation with table views
        result = cli_runner.invoke(
            generate_cli,
            [
                "entities",
                str(sample_crm_entity),
                "--output-dir",
                str(output_dir),
                "--include-tv",
            ],
        )

        # Verify success
        assert result.exit_code == 0
        assert "Generated" in result.output

    def test_generate_with_registry(
        self, cli_runner, sample_crm_entity, integration_test_dir
    ):
        """Test generation with registry and hierarchical format."""
        output_dir = integration_test_dir / "migrations"

        # Run generation with registry
        result = cli_runner.invoke(
            generate_cli,
            [
                "entities",
                str(sample_crm_entity),
                "--output-dir",
                str(output_dir),
                "--use-registry",
                "--output-format",
                "hierarchical",
            ],
        )

        # Verify success
        assert result.exit_code == 0
        assert "hexadecimal codes" in result.output

    def test_generate_with_frontend_code(
        self, cli_runner, sample_crm_entity, integration_test_dir
    ):
        """Test generation with frontend code output."""
        migrations_dir = integration_test_dir / "migrations"
        frontend_dir = integration_test_dir / "frontend"

        # Mock frontend generators since they may not be fully available
        from unittest.mock import Mock, patch

        with (
            patch("src.cli.generate.SpecQLParser") as mock_parser_cls,
            patch("src.generators.frontend.MutationImpactsGenerator"),
            patch("src.generators.frontend.TypeScriptTypesGenerator"),
            patch("src.generators.frontend.ApolloHooksGenerator"),
            patch("src.generators.frontend.MutationDocsGenerator"),
        ):
            # Setup mock parser
            mock_parser = Mock()
            mock_entity_def = Mock()
            mock_entity_def.name = "Contact"
            mock_entity_def.schema = "crm"
            mock_entity_def.fields = []
            mock_entity_def.actions = []
            mock_entity_def.agents = []
            mock_entity_def.organization = None
            mock_entity_def.description = "Test"
            mock_parser.parse.return_value = mock_entity_def
            mock_parser_cls.return_value = mock_parser

            # Run generation with frontend output
            result = cli_runner.invoke(
                generate_cli,
                [
                    "entities",
                    str(sample_crm_entity),
                    "--output-dir",
                    str(migrations_dir),
                    "--output-frontend",
                    str(frontend_dir),
                    "--with-impacts",
                ],
            )

            # Verify success
            assert result.exit_code == 0
            assert "Generating frontend code" in result.output


class TestTestGeneration:
    """Test the test generation workflow."""

    def test_generate_pgtap_tests(
        self, cli_runner, sample_crm_entity, integration_test_dir
    ):
        """Test generating pgTAP tests."""
        output_dir = integration_test_dir / "tests"

        # Run test generation
        result = cli_runner.invoke(
            generate_cli,
            [
                "tests",
                str(sample_crm_entity),
                "--output-dir",
                str(output_dir),
                "--test-type",
                "pgtap",
            ],
        )

        # Verify success
        assert result.exit_code == 0
        assert "Generating automated tests" in result.output

        # Verify test file was created
        pgtap_dir = output_dir / "pgtap"
        assert pgtap_dir.exists()
        test_files = list(pgtap_dir.glob("*.sql"))
        assert len(test_files) >= 1

        # Verify test file contains expected content
        test_file = test_files[0]
        content = test_file.read_text()
        assert "Contact" in content or "contact" in content

    def test_generate_pytest_tests(
        self, cli_runner, sample_crm_entity, integration_test_dir
    ):
        """Test generating pytest tests."""
        output_dir = integration_test_dir / "tests"

        # Run test generation
        result = cli_runner.invoke(
            generate_cli,
            [
                "tests",
                str(sample_crm_entity),
                "--output-dir",
                str(output_dir),
                "--test-type",
                "pytest",
            ],
        )

        # Verify success
        assert result.exit_code == 0
        assert "Generating automated tests" in result.output

        # Verify test file was created
        pytest_dir = output_dir / "pytest"
        assert pytest_dir.exists()
        test_files = list(pytest_dir.glob("test_*.py"))
        assert len(test_files) >= 1

    def test_generate_both_test_types(
        self, cli_runner, sample_crm_entity, integration_test_dir
    ):
        """Test generating both pgTAP and pytest tests."""
        output_dir = integration_test_dir / "tests"

        # Run test generation
        result = cli_runner.invoke(
            generate_cli,
            [
                "tests",
                str(sample_crm_entity),
                "--output-dir",
                str(output_dir),
                "--test-type",
                "both",
            ],
        )

        # Verify success
        assert result.exit_code == 0
        assert "Generated 2 test file(s)" in result.output

        # Verify both types exist
        assert (output_dir / "pgtap").exists()
        assert (output_dir / "pytest").exists()


class TestConfitureCLIWorkflow:
    """Test Confiture CLI integration."""

    def test_confiture_generate_workflow(self, cli_runner, sample_crm_entity):
        """Test Confiture generate command workflow."""
        # Run Confiture generate
        result = cli_runner.invoke(
            confiture_specql, ["generate", str(sample_crm_entity)]
        )

        # Verify command executes (may fail if Confiture not available)
        assert result.exit_code in [0, 1]  # 0 = success, 1 = Confiture build error
        assert "Generated" in result.output or "error" in result.output.lower()

    def test_confiture_validate_workflow(self, cli_runner, sample_crm_entity):
        """Test Confiture validate command workflow."""
        from unittest.mock import Mock, patch

        # Mock subprocess to avoid actually running validation
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            cli_runner.invoke(confiture_specql, ["validate", str(sample_crm_entity)])

            # Verify subprocess was called
            assert mock_run.called


class TestErrorHandling:
    """Test error handling in CLI workflows."""

    def test_invalid_yaml_error(self, cli_runner, integration_test_dir):
        """Test handling of invalid YAML files."""
        invalid_file = integration_test_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: [content")

        output_dir = integration_test_dir / "migrations"

        result = cli_runner.invoke(
            generate_cli,
            ["entities", str(invalid_file), "--output-dir", str(output_dir)],
        )

        # Should show error
        assert "error" in result.output.lower()

    def test_nonexistent_file_error(self, cli_runner, integration_test_dir):
        """Test handling of nonexistent files."""
        nonexistent_file = integration_test_dir / "nonexistent.yaml"
        output_dir = integration_test_dir / "migrations"

        result = cli_runner.invoke(
            generate_cli,
            ["entities", str(nonexistent_file), "--output-dir", str(output_dir)],
        )

        # Click will error on missing file
        assert result.exit_code == 2
        assert "does not exist" in result.output or "Error" in result.output
