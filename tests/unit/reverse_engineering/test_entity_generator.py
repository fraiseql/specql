"""Tests for entity YAML generation functionality."""

import yaml

from reverse_engineering.entity_generator import EntityYAMLGenerator
from reverse_engineering.fk_detector import ForeignKeyDetector
from reverse_engineering.pattern_orchestrator import PatternDetectionOrchestrator
from reverse_engineering.table_parser import SQLTableParser
from reverse_engineering.translation_detector import TranslationMerger


class TestEntityYAMLGenerator:
    """Test cases for entity YAML generation."""

    def test_generate_entity_yaml(self):
        """Test basic entity YAML generation."""
        sql = """
        CREATE TABLE catalog.tb_manufacturer (
            identifier TEXT NOT NULL,
            name TEXT,
            abbreviation CHAR(2) NOT NULL
        );
        """

        parser = SQLTableParser()
        parsed_table = parser.parse_table(sql)

        pattern_detector = PatternDetectionOrchestrator()
        patterns = pattern_detector.detect_all(parsed_table)

        generator = EntityYAMLGenerator()
        yaml_output = generator.generate(parsed_table, patterns)

        expected = """entity: Manufacturer
schema: catalog
description: Auto-generated from catalog.tb_manufacturer

fields:
  identifier: text!
  name: text
  abbreviation: char(2)!

patterns:
- trinity

_metadata:
  source_table: catalog.tb_manufacturer
  confidence: 0.0
  detected_patterns: [trinity]
  generated_by: specql-reverse-schema
  generated_at: """

        # Check that the YAML contains the expected structure
        assert "entity: Manufacturer" in yaml_output
        assert "schema: catalog" in yaml_output
        assert "identifier: text!" in yaml_output
        assert "name: text" in yaml_output
        assert "abbreviation: char(2)!" in yaml_output
        assert "patterns:" in yaml_output
        assert "_metadata:" in yaml_output

    def test_generate_entity_with_references(self):
        """Test entity generation with foreign key references."""
        sql = """
        CREATE TABLE catalog.tb_manufacturer (
            pk_manufacturer UUID PRIMARY KEY,
            fk_company UUID,
            name TEXT
        );
        """

        alter_sql = """
        ALTER TABLE catalog.tb_manufacturer
            ADD CONSTRAINT tb_manufacturer_fk_company_fkey
            FOREIGN KEY (fk_company)
            REFERENCES management.tb_organization(pk_organization);
        """

        parser = SQLTableParser()
        parsed_table = parser.parse_table(sql)

        pattern_detector = PatternDetectionOrchestrator()
        patterns = pattern_detector.detect_all(parsed_table)

        fk_detector = ForeignKeyDetector()
        foreign_keys = fk_detector.detect(parsed_table, [alter_sql])

        generator = EntityYAMLGenerator()
        yaml_output = generator.generate(parsed_table, patterns, foreign_keys)

        # Should convert fk_company to company: ref(Organization)
        assert "company: ref(Organization)" in yaml_output
        assert "fk_company" not in yaml_output  # Should be renamed
        assert "name: text" in yaml_output

    def test_generate_entity_with_translations(self):
        """Test entity generation with translation fields."""
        main_sql = """
        CREATE TABLE catalog.tb_manufacturer (
            pk_manufacturer UUID PRIMARY KEY,
            name TEXT,
            color_name TEXT
        );
        """

        translation_sql = """
        CREATE TABLE catalog.tb_manufacturer_translation (
            fk_manufacturer UUID NOT NULL,
            locale TEXT NOT NULL,
            name TEXT,
            color_name TEXT,
            PRIMARY KEY (fk_manufacturer, locale)
        );
        """

        parser = SQLTableParser()
        main_table = parser.parse_table(main_sql)
        translation_table = parser.parse_table(translation_sql)

        pattern_detector = PatternDetectionOrchestrator()
        patterns = pattern_detector.detect_all(main_table)

        merger = TranslationMerger()
        merged_fields = merger.merge(main_table, translation_table)

        # Create a mock entity with merged fields
        entity_data = {
            "entity": "Manufacturer",
            "schema": "catalog",
            "description": "Test entity",
            "fields": merged_fields,
            "patterns": ["translation"],
            "_metadata": {
                "source_table": "catalog.tb_manufacturer",
                "confidence": 0.9,
                "generated_by": "specql-reverse-schema",
            },
        }

        yaml_output = yaml.dump(entity_data, default_flow_style=False, sort_keys=False)

        # Should create nested translations structure
        assert "translations:" in yaml_output
        assert "locale: ref(Locale)" in yaml_output
        assert "name: text" in yaml_output
        assert "color_name: text" in yaml_output

        # Should remove base table duplicate fields
        assert "name: text" in yaml_output  # Should be in translations
        assert "color_name: text" in yaml_output  # Should be in translations
        # Check that name/color_name don't appear in the main fields
        lines = yaml_output.split("\n")
        in_fields = False
        in_translations = False
        main_field_names = []
        translation_field_names = []
        for line in lines:
            if line.startswith("fields:"):
                in_fields = True
                continue
            elif line.startswith("patterns:") or line.startswith("_metadata:"):
                in_fields = False
                in_translations = False
            elif in_fields and line.startswith("  translations:"):
                in_translations = True
            elif (
                in_fields and in_translations and line.strip().startswith(("name:", "color_name:"))
            ):
                translation_field_names.append(line.strip().split(":")[0])
            elif (
                in_fields
                and not in_translations
                and line.strip().startswith(("name:", "color_name:"))
            ):
                main_field_names.append(line.strip().split(":")[0])

        assert "name" in translation_field_names
        assert "color_name" in translation_field_names
        assert "name" not in main_field_names
        assert "color_name" not in main_field_names
