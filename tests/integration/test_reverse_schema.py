"""
Integration test for reverse-schema command.

Tests the complete pipeline from SQL files to SpecQL YAML entities.
"""

import pytest
import tempfile
from pathlib import Path
from src.parsers.plpgsql.schema_analyzer import SchemaAnalyzer
from src.core.specql_generator import SpecQLGenerator
import yaml


class TestReverseSchema:
    """Test reverse-schema functionality"""

    @pytest.fixture
    def analyzer(self):
        return SchemaAnalyzer()

    @pytest.fixture
    def generator(self):
        return SpecQLGenerator()

    def test_reverse_schema_full_pipeline(self, analyzer, generator):
        """Test complete reverse-schema pipeline"""

        # Create test SQL file
        sql_content = """
        CREATE TABLE catalog.tb_language (
            id INTEGER PRIMARY KEY,
            pk_language UUID NOT NULL,
            name VARCHAR(20),
            iso_code VARCHAR(10)
        );

        COMMENT ON TABLE catalog.tb_language IS '[Table: 010111 | Write-Side.Common.Locale.Language] Defines supported languages.';
        """

        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create hierarchical structure
            sql_file = (
                temp_path
                / "01_write_side"
                / "010_i18n"
                / "0101_locale"
                / "01011_language"
                / "010111_tb_language.sql"
            )
            sql_file.parent.mkdir(parents=True, exist_ok=True)
            sql_file.write_text(sql_content)

            # Parse with metadata
            entity = analyzer.parse_create_table_with_metadata(
                ddl=sql_content, file_path=sql_file, root_dir=temp_path
            )

            # Generate YAML
            yaml_content = generator.generate_yaml(entity)

            # Parse YAML to verify structure
            data = yaml.safe_load(yaml_content)

            # Verify basic structure
            assert data["entity"] == "Language"
            assert data["schema"] == "catalog"
            assert "Defines supported languages" in data["description"]

            # Verify organization metadata
            assert "organization" in data
            org = data["organization"]
            assert org["table_code"] == "010111"
            assert org["category"] == "write_side"
            assert org["domain_path"] == ["i18n", "locale", "language"]
            assert org["domain_hierarchy"] == ["Common", "Locale", "Language"]
            assert (
                org["file_path"]
                == "01_write_side/010_i18n/0101_locale/01011_language/010111_tb_language.sql"
            )
            assert org["table_type"] == "tb"

            # Verify fields
            assert "fields" in data
            fields = data["fields"]
            assert "name" in fields
            assert "iso_code" in fields

            # Verify metadata
            assert "_metadata" in data
            meta = data["_metadata"]
            assert meta["source"] == "reverse-schema"
            assert "generated_at" in meta
            assert meta["original_schema"] == "catalog"
            assert meta["original_table"] == "catalog.language"

    def test_reverse_schema_translation_table(self, analyzer, generator):
        """Test reverse-schema with translation table"""

        sql_content = """
        CREATE TABLE catalog.tl_continent (
            id INTEGER PRIMARY KEY,
            fk_continent INTEGER REFERENCES catalog.tb_continent(id),
            fk_language INTEGER REFERENCES catalog.tb_language(id),
            name VARCHAR(100) NOT NULL
        );

        COMMENT ON TABLE catalog.tl_continent IS '[Table: 010212 | Write-Side.Common.Geo.Continent] Translation table for continents.';
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            sql_file = (
                temp_path
                / "01_write_side"
                / "010_geo"
                / "0102_continent"
                / "01021_continent"
                / "010212_tl_continent.sql"
            )
            sql_file.parent.mkdir(parents=True, exist_ok=True)
            sql_file.write_text(sql_content)

            entity = analyzer.parse_create_table_with_metadata(
                ddl=sql_content, file_path=sql_file, root_dir=temp_path
            )

            yaml_content = generator.generate_yaml(entity)
            data = yaml.safe_load(yaml_content)

            # Verify translation table metadata
            assert data["entity"] == "Continent"
            org = data["organization"]
            assert org["table_code"] == "010212"
            assert org["table_type"] == "tl"  # translation table
            assert org["domain_path"] == ["geo", "continent", "continent"]

    def test_reverse_schema_without_comment(self, analyzer, generator):
        """Test reverse-schema with SQL file that has no COMMENT metadata"""

        sql_content = """
        CREATE TABLE catalog.tb_country (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            iso_code VARCHAR(3)
        );
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            sql_file = (
                temp_path
                / "01_write_side"
                / "010_i18n"
                / "0102_country"
                / "010221_tb_country.sql"
            )
            sql_file.parent.mkdir(parents=True, exist_ok=True)
            sql_file.write_text(sql_content)

            entity = analyzer.parse_create_table_with_metadata(
                ddl=sql_content, file_path=sql_file, root_dir=temp_path
            )

            yaml_content = generator.generate_yaml(entity)
            data = yaml.safe_load(yaml_content)

            # Should still extract file path metadata
            assert data["entity"] == "Country"
            org = data["organization"]
            assert org["table_code"] == "010221"
            assert org["category"] == "write_side"
            assert org["domain_path"] == ["i18n", "country"]
            # COMMENT-derived fields should be empty/default
            assert org.get("domain_hierarchy") == []

    def test_reverse_schema_table_code_consistency_warning(self, analyzer):
        """Test warning when table codes don't match between filename and COMMENT"""

        sql_content = """
        CREATE TABLE catalog.tb_language (
            id INTEGER PRIMARY KEY,
            name VARCHAR(20)
        );

        COMMENT ON TABLE catalog.tb_language IS '[Table: 999999 | Write-Side.Common.Locale.Language] Mismatched code.';
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            sql_file = (
                temp_path
                / "01_write_side"
                / "010_i18n"
                / "0101_locale"
                / "01011_language"
                / "010111_tb_language.sql"
            )
            sql_file.parent.mkdir(parents=True, exist_ok=True)
            sql_file.write_text(sql_content)

            # Should warn about mismatch but still process
            with pytest.warns(UserWarning, match="Table code mismatch"):
                entity = analyzer.parse_create_table_with_metadata(
                    ddl=sql_content, file_path=sql_file, root_dir=temp_path
                )

            # Should use COMMENT code (override)
            assert entity.organization["table_code"] == "999999"
