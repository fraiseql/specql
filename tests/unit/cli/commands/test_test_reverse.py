"""Tests for specql test reverse command"""

import pytest
from click.testing import CliRunner

from cli.main import app


class TestReverseCommand:
    """Test reverse engineering command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_pgtap(self, tmp_path):
        test_file = tmp_path / "test_contact.sql"
        test_file.write_text("""
-- pgTAP tests for Contact
BEGIN;
SELECT plan(10);

SELECT has_table('crm', 'tb_contact', 'Contact table exists');
SELECT has_column('crm', 'tb_contact', 'email', 'Has email column');
SELECT col_is_pk('crm', 'tb_contact', 'pk_contact', 'Has primary key');

-- CRUD tests
DO $$
DECLARE
    v_result app.mutation_result;
BEGIN
    v_result := app.create_contact('tenant-id', 'user-id', '{"email": "test@example.com"}');
    PERFORM ok(v_result.status = 'success', 'Create succeeds');
END $$;

SELECT * FROM finish();
ROLLBACK;
""")
        return test_file

    @pytest.fixture
    def sample_pytest(self, tmp_path):
        test_file = tmp_path / "test_contact.py"
        test_file.write_text('''
"""Integration tests for Contact"""
import pytest

class TestContactIntegration:
    def test_create_contact(self, db_connection):
        """Test creating contact"""
        result = execute("SELECT app.create_contact(...)")
        assert result["status"] == "success"

    def test_qualify_lead(self, db_connection):
        """Test qualify_lead action"""
        result = execute("SELECT crm.qualify_lead(...)")
        assert result["status"] == "success"
        assert result["object_data"]["status"] == "qualified"
''')
        return test_file

    def test_reverse_pgtap(self, runner, sample_pgtap, tmp_path):
        """Test reverse engineering pgTAP tests"""
        output_dir = tmp_path / "specs"
        result = runner.invoke(
            app, ["test", "reverse", str(sample_pgtap), "-o", str(output_dir), "--type", "pgtap"]
        )

        assert result.exit_code == 0
        spec_file = output_dir / "contact-test-spec_pgtap.yaml"
        assert spec_file.exists()
        content = spec_file.read_text()
        assert "entity: Contact" in content
        assert "table_exists" in content

    def test_reverse_pytest(self, runner, sample_pytest, tmp_path):
        """Test reverse engineering pytest tests"""
        output_dir = tmp_path / "specs"
        result = runner.invoke(
            app, ["test", "reverse", str(sample_pytest), "-o", str(output_dir), "--type", "pytest"]
        )

        assert result.exit_code == 0
        spec_file = output_dir / "contact-test-spec_pytest.yaml"
        assert spec_file.exists()
        content = spec_file.read_text()
        assert "qualify_lead" in content

    def test_reverse_auto_detect(self, runner, sample_pgtap, tmp_path):
        """Test auto-detection of test type"""
        output_dir = tmp_path / "specs"
        result = runner.invoke(
            app,
            [
                "test",
                "reverse",
                str(sample_pgtap),
                "-o",
                str(output_dir),
                # No --type, should auto-detect from .sql extension
            ],
        )

        assert result.exit_code == 0

    def test_reverse_preview(self, runner, sample_pgtap, tmp_path):
        """Test preview mode"""
        result = runner.invoke(app, ["test", "reverse", str(sample_pgtap), "--preview"])

        assert result.exit_code == 0
        assert "entity: Contact" in result.output
        # No files created
        assert not list(tmp_path.glob("specs/*.yaml"))

    def test_reverse_multiple_files(self, runner, sample_pgtap, sample_pytest, tmp_path):
        """Test reverse engineering multiple test files"""
        output_dir = tmp_path / "specs"
        result = runner.invoke(
            app, ["test", "reverse", str(sample_pgtap), str(sample_pytest), "-o", str(output_dir)]
        )

        assert result.exit_code == 0
        # Should create specs for both files
        spec_files = list(output_dir.glob("*.yaml"))
        assert len(spec_files) == 2

    def test_reverse_unknown_type(self, runner, tmp_path):
        """Test handling of unknown file types"""
        unknown_file = tmp_path / "unknown.txt"
        unknown_file.write_text("some random content")

        result = runner.invoke(app, ["test", "reverse", str(unknown_file)])

        assert result.exit_code == 0  # Should not fail, just warn
        assert "Could not detect test type" in result.output

    def test_reverse_output_directory_creation(self, runner, sample_pgtap, tmp_path):
        """Test that output directory is created if it doesn't exist"""
        output_dir = tmp_path / "deep" / "nested" / "specs"
        result = runner.invoke(app, ["test", "reverse", str(sample_pgtap), "-o", str(output_dir)])

        assert result.exit_code == 0
        assert output_dir.exists()
        spec_files = list(output_dir.glob("*.yaml"))
        assert len(spec_files) == 1
