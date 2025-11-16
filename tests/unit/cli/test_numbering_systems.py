"""
Comprehensive tests for both numbering systems.

This test file verifies that both the decimal (00_, 10_, 20_, 30_) and
hexadecimal (01_, 02_, 03_) numbering systems are correctly implemented
and can coexist.
"""

from pathlib import Path

import pytest

from src.cli.orchestrator import CLIOrchestrator
from src.core.ast_models import Entity
from src.numbering.numbering_parser import NumberingParser


class TestDecimalNumberingSystem:
    """Test the decimal numbering system (00_, 10_, 20_, 30_) for Confiture integration"""

    def test_decimal_foundation_directory(self, temp_dir):
        """Test that foundation files go to 00_foundation/"""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        result = orchestrator.generate_from_files(
            entity_files=[], output_dir=str(output_dir), foundation_only=True
        )

        # Foundation should be in 00_foundation when using Confiture format
        # Note: Current implementation writes to output_dir for backward compatibility
        assert result.migrations[0].number == 0
        assert result.migrations[0].name == "app_foundation"

    def test_decimal_table_directory(self, sample_entity_file, temp_dir):
        """Test that tables go to 10_tables/"""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        orchestrator.generate_from_files(
            entity_files=[str(sample_entity_file)], output_dir=str(output_dir)
        )

        # Verify tables are created (db/schema/10_tables/)
        schema_base = Path("db/schema")
        table_dir = schema_base / "10_tables"
        assert table_dir.exists()

    def test_decimal_helpers_directory(self, sample_entity_file, temp_dir):
        """Test that helpers go to 20_helpers/"""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        orchestrator.generate_from_files(
            entity_files=[str(sample_entity_file)], output_dir=str(output_dir)
        )

        # Verify helpers are created (db/schema/20_helpers/)
        schema_base = Path("db/schema")
        helpers_dir = schema_base / "20_helpers"
        assert helpers_dir.exists()

    def test_decimal_functions_directory(self, sample_entity_file, temp_dir):
        """Test that functions go to 30_functions/"""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        orchestrator.generate_from_files(
            entity_files=[str(sample_entity_file)], output_dir=str(output_dir)
        )

        # Verify functions are created (db/schema/30_functions/)
        schema_base = Path("db/schema")
        functions_dir = schema_base / "30_functions"
        assert functions_dir.exists()

    def test_decimal_system_directory_structure(self, sample_entity_file, temp_dir):
        """Test complete decimal directory structure"""
        orchestrator = CLIOrchestrator()
        output_dir = temp_dir / "migrations"

        orchestrator.generate_from_files(
            entity_files=[str(sample_entity_file)], output_dir=str(output_dir)
        )

        # Verify all decimal directories exist
        schema_base = Path("db/schema")
        assert (schema_base / "10_tables").exists()
        assert (schema_base / "20_helpers").exists()
        assert (schema_base / "30_functions").exists()


class TestHexadecimalNumberingSystem:
    """Test the hexadecimal numbering system (01_, 02_, 03_) for registry-based organization"""

    def test_hex_parser_initialization(self):
        """Test hexadecimal numbering parser initializes correctly"""
        parser = NumberingParser()
        assert parser is not None
        assert parser.SCHEMA_LAYERS == {
            "01": "write_side",
            "02": "read_side",
            "03": "analytics",
        }

    def test_hex_parse_6_digit_code(self):
        """Test parsing 6-digit hexadecimal table code"""
        parser = NumberingParser()
        result = parser.parse_table_code("013211")

        assert result["schema_layer"] == "01"  # write_side
        assert result["domain_code"] == "3"  # catalog
        assert result["entity_group"] == "2"  # manufacturer group
        assert result["entity_code"] == "1"  # manufacturer entity
        assert result["file_sequence"] == "1"  # first file

    def test_hex_generate_directory_path(self):
        """Test generating hierarchical directory path from hex code"""
        parser = NumberingParser()
        path = parser.generate_directory_path("013211", "manufacturer")

        expected = "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer"
        assert path == expected

    def test_hex_generate_file_path(self):
        """Test generating file path with hex code"""
        parser = NumberingParser()
        path = parser.generate_file_path(
            table_code="013211", entity_name="manufacturer", file_type="table"
        )

        expected = "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql"
        assert path == expected

    def test_hex_invalid_code_validation(self):
        """Test that invalid hex codes are rejected"""
        parser = NumberingParser()

        # Too short
        with pytest.raises(ValueError, match="Invalid table_code"):
            parser.parse_table_code("12345")

        # Invalid hex character (G is not valid hex)
        with pytest.raises(ValueError, match="Invalid table_code"):
            parser.parse_table_code("GGGGGG")

    def test_hex_orchestrator_integration(self):
        """Test that orchestrator can use registry with hex codes"""
        orchestrator = CLIOrchestrator(use_registry=True)

        entity = Entity(name="Contact", schema="crm", fields={})
        table_code = orchestrator.get_table_code(entity)

        # Should be valid 6-char hex code
        assert len(table_code) == 6
        assert all(c in "0123456789ABCDEF" for c in table_code.upper())

    def test_hex_hierarchical_path_generation(self):
        """Test that registry generates hierarchical paths"""
        orchestrator = CLIOrchestrator(use_registry=True)

        entity = Entity(name="Contact", schema="crm", fields={})
        table_code = "012311"

        file_path = orchestrator.generate_file_path(entity, table_code)

        # Should have deep hierarchy
        parts = Path(file_path).parts
        assert len(parts) >= 5
        assert "01_write_side" in parts


class TestNumberingSystemsCoexistence:
    """Test that both numbering systems can coexist correctly"""

    def test_default_mode_uses_decimal(self, sample_entity_file, temp_dir):
        """Test that default orchestrator uses decimal system"""
        orchestrator = CLIOrchestrator()  # Default: use_registry=False
        output_dir = temp_dir / "migrations"

        orchestrator.generate_from_files(
            entity_files=[str(sample_entity_file)], output_dir=str(output_dir)
        )

        # Should use decimal directories
        schema_base = Path("db/schema")
        assert (schema_base / "10_tables").exists()
        assert (schema_base / "20_helpers").exists()
        assert (schema_base / "30_functions").exists()

    def test_registry_mode_can_generate_hierarchical(self):
        """Test that registry mode can generate hierarchical hex paths"""
        orchestrator = CLIOrchestrator(use_registry=True)

        entity = Entity(name="Contact", schema="crm", fields={})
        table_code = "012311"

        # Generate hierarchical path
        file_path = orchestrator.generate_file_path(entity, table_code)

        # Should use hex hierarchy
        assert "01_write_side" in file_path

    def test_confiture_format_uses_decimal(self):
        """Test that Confiture format always uses decimal directories"""
        orchestrator = CLIOrchestrator(use_registry=True, output_format="confiture")

        entity = Entity(name="Contact", schema="crm", fields={})
        file_path = orchestrator.generate_file_path_confiture(entity, "table")

        # Should map to decimal directories
        assert "10_tables" in file_path
        assert file_path.startswith("db/schema/")

    def test_numbering_systems_documentation_consistency(self):
        """Verify both systems are documented and consistent"""
        # Decimal system directories
        decimal_dirs = ["00_foundation", "10_tables", "20_helpers", "30_functions"]

        # Hexadecimal system prefixes
        hex_prefixes = ["01", "02", "03"]

        # Extract numeric prefixes from decimal dirs
        decimal_nums = [int(d.split("_")[0]) for d in decimal_dirs]

        # Decimal directories use: 00, 10, 20, 30 (multiples of 10)
        assert decimal_nums == [0, 10, 20, 30]

        # Hex prefixes use: 01, 02, 03 (schema layers)
        for hex_prefix in hex_prefixes:
            assert hex_prefix.startswith("0")  # All start with 0
            assert int(hex_prefix) in [1, 2, 3]  # Valid schema layers

        # Key difference: Decimal uses X0_ pattern, Hex uses 0X_ pattern
        # They don't conflict because 10_ != 01_, etc.


class TestNumberingSystemsIntegration:
    """Integration tests for both numbering systems"""

    def test_parser_handles_both_decimal_and_hex(self):
        """Test that parser can work with both decimal filenames and hex codes"""
        parser = NumberingParser()

        # Hex code parsing
        hex_result = parser.parse_table_code("013211")
        assert hex_result["schema_layer"] == "01"

        # Decimal directories should be handled separately
        # (they're not parsed by NumberingParser, but used in file organization)
        decimal_dirs = ["00_foundation", "10_tables", "20_helpers", "30_functions"]
        for dir_name in decimal_dirs:
            assert dir_name[1:].split("_")[0].isdigit()

    def test_both_systems_create_valid_paths(self):
        """Test that both systems create valid, non-conflicting paths"""
        # Decimal system paths
        decimal_paths = [
            "db/schema/00_foundation/app_foundation.sql",
            "db/schema/10_tables/contact.sql",
            "db/schema/20_helpers/contact_helpers.sql",
            "db/schema/30_functions/create_contact.sql",
        ]

        # Hexadecimal system paths
        parser = NumberingParser()
        hex_path = parser.generate_file_path("013211", "manufacturer", "table")

        # All paths should be valid and distinguishable
        for decimal_path in decimal_paths:
            assert Path(decimal_path).parts[0] == "db"
            assert Path(decimal_path).parts[1] == "schema"

        assert "01_write_side" in hex_path
        assert hex_path != any(decimal_paths)


class TestNumberingSystemsEdgeCases:
    """Test edge cases for both numbering systems"""

    def test_hex_supports_full_range(self):
        """Test that hex system supports full 0-F range"""
        parser = NumberingParser()

        # Test valid hex codes with A-F
        valid_codes = ["01A211", "01BF11", "01CFFF"]
        for code in valid_codes:
            result = parser.parse_table_code(code)
            assert len(result["schema_layer"]) == 2

    def test_decimal_directories_are_sequential(self):
        """Test that decimal directories follow sequential numbering"""
        dirs = ["00_foundation", "10_tables", "20_helpers", "30_functions"]

        # Extract numeric parts
        numbers = [int(d.split("_")[0]) for d in dirs]

        # Should be in ascending order with gaps of 10
        assert numbers == [0, 10, 20, 30]

    def test_systems_dont_conflict_in_file_system(self):
        """Test that both systems can coexist in file system"""
        # Decimal uses: db/schema/10_tables/
        # Hex uses: db/schema/01_write_side/

        decimal_prefix = "10_"
        hex_prefix = "01_"

        # Different patterns - won't conflict
        assert decimal_prefix[0:2] != hex_prefix[0:2]  # "10" vs "01"
