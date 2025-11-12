#!/usr/bin/env python3
"""
Unit tests for check-codes CLI command
"""

from pathlib import Path

from src.cli.commands.check_codes import check_table_code_uniqueness
from click.testing import CliRunner


class TestCheckCodes:
    """Test table code uniqueness checking"""

    def test_detects_duplicate_codes(self):
        """Test that duplicate table codes are detected"""
        # Create temporary YAML files with duplicate codes
        temp_dir = Path("/tmp/test_check_codes")
        temp_dir.mkdir(exist_ok=True)

        # File 1: Contact with table_code 013211
        contact_yaml = temp_dir / "contact.yaml"
        contact_yaml.write_text("""
entity: Contact
table_code: "013211"
schema: crm
fields:
  name:
    type: text
""")

        # File 2: Company with same table_code 013211
        company_yaml = temp_dir / "company.yaml"
        company_yaml.write_text("""
entity: Company
table_code: "013211"
schema: crm
fields:
  name:
    type: text
""")

        try:
            # This should detect the duplicate
            result = check_table_code_uniqueness([contact_yaml, company_yaml])

            # Should return duplicates dict with the code and list of entity names
            assert "013211" in result
            assert len(result["013211"]) == 2
            assert "Contact" in result["013211"]
            assert "Company" in result["013211"]

        finally:
            # Cleanup
            contact_yaml.unlink(missing_ok=True)
            company_yaml.unlink(missing_ok=True)
            temp_dir.rmdir()

    def test_no_duplicates_returns_empty(self):
        """Test that unique codes return empty dict"""
        temp_dir = Path("/tmp/test_check_codes_unique")
        temp_dir.mkdir(exist_ok=True)

        # File 1: Contact with table_code 013211
        contact_yaml = temp_dir / "contact.yaml"
        contact_yaml.write_text("""
entity: Contact
table_code: "013211"
schema: crm
fields:
  name:
    type: text
""")

        # File 2: Company with different table_code 013212
        company_yaml = temp_dir / "company.yaml"
        company_yaml.write_text("""
entity: Company
table_code: "013212"
schema: crm
fields:
  name:
    type: text
""")

        try:
            result = check_table_code_uniqueness([contact_yaml, company_yaml])
            assert result == {}

        finally:
            contact_yaml.unlink(missing_ok=True)
            company_yaml.unlink(missing_ok=True)
            temp_dir.rmdir()

    def test_handles_nested_table_code_format(self):
        """Test that organization.table_code format is handled"""
        temp_dir = Path("/tmp/test_check_codes_nested")
        temp_dir.mkdir(exist_ok=True)

        # File 1 with nested table_code
        entity1_yaml = temp_dir / "entity1.yaml"
        entity1_yaml.write_text("""
entity: TestEntity1
organization:
  table_code: "014511"
schema: test
fields:
  name:
    type: text
""")

        # File 2 with same nested table_code (duplicate)
        entity2_yaml = temp_dir / "entity2.yaml"
        entity2_yaml.write_text("""
entity: TestEntity2
organization:
  table_code: "014511"
schema: test
fields:
  name:
    type: text
""")

        try:
            result = check_table_code_uniqueness([entity1_yaml, entity2_yaml])
            # Should extract the code from nested format and detect duplicate
            assert "014511" in result
            assert len(result["014511"]) == 2
            assert "TestEntity1" in result["014511"]
            assert "TestEntity2" in result["014511"]

        finally:
            entity1_yaml.unlink(missing_ok=True)
            entity2_yaml.unlink(missing_ok=True)
            temp_dir.rmdir()

    def test_cli_command_exists(self):
        """Test that check-codes CLI command exists and can be invoked"""
        runner = CliRunner()
        from src.cli.confiture_extensions import specql

        # Check that the command exists in help
        result = runner.invoke(specql, ["--help"])
        assert result.exit_code == 0
        assert "check-codes" in result.output

    def test_cli_command_with_duplicates(self):
        """Test CLI command detects duplicates correctly"""
        runner = CliRunner()
        from src.cli.confiture_extensions import specql

        temp_dir = Path("/tmp/test_cli_duplicates")
        temp_dir.mkdir(exist_ok=True)

        # Create files with duplicate codes
        file1 = temp_dir / "entity1.yaml"
        file1.write_text("""
entity: Entity1
table_code: "013211"
schema: test
fields:
  name: text
""")

        file2 = temp_dir / "entity2.yaml"
        file2.write_text("""
entity: Entity2
table_code: "013211"
schema: test
fields:
  name: text
""")

        try:
            result = runner.invoke(specql, ["check-codes", str(file1), str(file2)])
            assert result.exit_code == 1  # Should fail with duplicates
            assert "FAILED" in result.output
            assert "013211" in result.output
            assert "Entity1" in result.output
            assert "Entity2" in result.output

        finally:
            file1.unlink(missing_ok=True)
            file2.unlink(missing_ok=True)
            temp_dir.rmdir()

    def test_cli_command_with_unique_codes(self):
        """Test CLI command passes with unique codes"""
        runner = CliRunner()
        from src.cli.confiture_extensions import specql

        temp_dir = Path("/tmp/test_cli_unique")
        temp_dir.mkdir(exist_ok=True)

        # Create files with unique codes
        file1 = temp_dir / "entity1.yaml"
        file1.write_text("""
entity: Entity1
table_code: "013211"
schema: test
fields:
  name: text
""")

        file2 = temp_dir / "entity2.yaml"
        file2.write_text("""
entity: Entity2
table_code: "013212"
schema: test
fields:
  name: text
""")

        try:
            result = runner.invoke(specql, ["check-codes", str(file1), str(file2)])
            assert result.exit_code == 0  # Should pass
            assert "PASSED" in result.output
            assert "unique" in result.output

        finally:
            file1.unlink(missing_ok=True)
            file2.unlink(missing_ok=True)
            temp_dir.rmdir()
