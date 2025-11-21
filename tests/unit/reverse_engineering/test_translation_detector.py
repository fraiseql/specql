"""Tests for translation table detection functionality."""

from reverse_engineering.table_parser import SQLTableParser
from reverse_engineering.translation_detector import TranslationMerger, TranslationTableDetector


class TestTranslationTableDetector:
    """Test cases for translation table detection."""

    def test_detect_translation_table(self):
        """Test detection of translation table patterns."""
        main_sql = """
        CREATE TABLE catalog.tb_manufacturer (
            pk_manufacturer UUID PRIMARY KEY,
            name TEXT,
            color_name TEXT
        );
        """

        translation_sql = """
        CREATE TABLE catalog.tb_manufacturer_translation (
            fk_manufacturer UUID NOT NULL
                REFERENCES catalog.tb_manufacturer(pk_manufacturer) ON DELETE CASCADE,
            locale TEXT NOT NULL
                REFERENCES tb_locale(code) ON DELETE CASCADE,
            name TEXT,
            color_name TEXT,
            PRIMARY KEY (fk_manufacturer, locale)
        );
        """

        parser = SQLTableParser()

        parser.parse_table(main_sql)  # Parse main table (used for context)
        translation_table = parser.parse_table(translation_sql)

        detector = TranslationTableDetector()
        result = detector.detect(translation_table)

        assert result.is_translation_table is True
        assert result.parent_table == "tb_manufacturer"
        assert result.fk_column == "fk_manufacturer"
        assert result.locale_column == "locale"
        assert result.translatable_fields == ["name", "color_name"]

    def test_merge_translation_into_entity(self):
        """Test merging translation fields into parent entity."""
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

        merger = TranslationMerger()
        result = merger.merge(main_table, translation_table)

        # Should create nested translations structure
        assert "translations" in result
        assert result["translations"]["locale"] == "ref(Locale)"
        assert result["translations"]["name"] == "text"
        assert result["translations"]["color_name"] == "text"

        # Should remove base table duplicate fields
        assert "name" not in result
        assert "color_name" not in result
