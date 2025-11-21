"""Integration tests for workflow migrate command.

Tests the full pipeline: reverse → validate → generate.
"""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import app


@pytest.fixture
def cli_runner():
    """Click CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_sql_file():
    """Create a sample SQL file for testing."""
    sql_content = """
    CREATE TABLE crm.tb_contact (
        pk_contact SERIAL PRIMARY KEY,
        id UUID DEFAULT gen_random_uuid(),
        email TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE crm.tb_company (
        pk_company SERIAL PRIMARY KEY,
        id UUID DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        website TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    ALTER TABLE crm.tb_contact
    ADD CONSTRAINT fk_contact_company
    FOREIGN KEY (fk_company) REFERENCES crm.tb_company(pk_company);
    """

    def _create_file(tmpdir):
        sql_file = Path(tmpdir) / "contact.sql"
        sql_file.write_text(sql_content)
        return sql_file

    return _create_file


def test_migrate_sql_files_generates_yaml(cli_runner, sample_sql_file):
    """Full pipeline: SQL → YAML → SQL should produce valid output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create sample SQL input
        sql_file = sample_sql_file(tmpdir)

        result = cli_runner.invoke(
            app, ["workflow", "migrate", str(sql_file), "--reverse-from=sql", "-o", str(tmpdir)]
        )

        assert result.exit_code == 0
        assert (tmpdir / "entities" / "contact.yaml").exists()
        # Check that SQL files were generated (in db/schema structure)
        assert (tmpdir / "output" / "db" / "schema" / "10_tables" / "contact.sql").exists()


def test_migrate_python_django_models(cli_runner):
    """Django models → YAML → SQL pipeline."""
    django_content = """
from django.db import models

class Contact(models.Model):
    email = models.EmailField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_contact'

class Company(models.Model):
    name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_company'
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create Django models.py
        models_file = tmpdir / "models.py"
        models_file.write_text(django_content)

        result = cli_runner.invoke(
            app,
            ["workflow", "migrate", str(models_file), "--reverse-from=python", "-o", str(tmpdir)],
        )

        assert result.exit_code == 0
        assert (tmpdir / "entities" / "contact.yaml").exists()
        assert (tmpdir / "entities" / "company.yaml").exists()
        # Check that SQL files were generated
        assert (tmpdir / "output" / "db" / "schema" / "10_tables" / "contact.sql").exists()


def test_migrate_dry_run_no_files_created(cli_runner, sample_sql_file):
    """Dry run should show plan without creating files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create sample SQL input
        sql_file = sample_sql_file(tmpdir)

        result = cli_runner.invoke(
            app,
            [
                "workflow",
                "migrate",
                str(sql_file),
                "--reverse-from=sql",
                "--dry-run",
                "-o",
                str(tmpdir),
            ],
        )

        assert result.exit_code == 0
        assert "Dry-run mode" in result.output
        assert not (tmpdir / "entities").exists()
        assert not (tmpdir / "output").exists()


def test_migrate_validate_only_stops_early(cli_runner, sample_sql_file):
    """--validate-only should stop after phase 2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create sample SQL input
        sql_file = sample_sql_file(tmpdir)

        result = cli_runner.invoke(
            app,
            [
                "workflow",
                "migrate",
                str(sql_file),
                "--reverse-from=sql",
                "--validate-only",
                "-o",
                str(tmpdir),
            ],
        )

        assert result.exit_code == 0
        assert "Phase 2: Validation" in result.output
        assert "Stopping after validation" in result.output
        # Should not reach generation phase
        assert "Phase 3: Code generation" not in result.output
        assert not (tmpdir / "output").exists()


def test_migrate_continue_on_error_proceeds(cli_runner):
    """--continue-on-error should work correctly."""
    # Create valid SQL files
    valid_sql = """
    CREATE TABLE test.valid_table (
        id SERIAL PRIMARY KEY,
        name TEXT
    );
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create files
        valid_file = tmpdir / "valid.sql"
        valid_file.write_text(valid_sql)

        result = cli_runner.invoke(
            app,
            [
                "workflow",
                "migrate",
                str(valid_file),
                "--reverse-from=sql",
                "--continue-on-error",
                "-o",
                str(tmpdir),
            ],
        )

        # Should succeed
        assert result.exit_code == 0
        # Check that files were generated
        assert (tmpdir / "output" / "db" / "schema" / "10_tables" / "validtable.sql").exists()


def test_migrate_generate_only_uses_existing_yaml(cli_runner):
    """--generate-only should skip reverse and validation phases."""
    yaml_content = """entity: TestEntity
schema: test
fields:
  test_id: serial
  name: text
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create YAML file
        yaml_file = tmpdir / "test.yaml"
        yaml_file.write_text(yaml_content)

        result = cli_runner.invoke(
            app, ["workflow", "migrate", str(yaml_file), "--generate-only", "-o", str(tmpdir)]
        )

        assert result.exit_code == 0
        assert "Skipping reverse phase" in result.output
        # Check that SQL files were generated
        assert (tmpdir / "output" / "db" / "schema" / "10_tables" / "testentity.sql").exists()
