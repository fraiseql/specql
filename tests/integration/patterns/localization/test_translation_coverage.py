"""Test translation coverage reporting"""

import pytest
from src.patterns.localization.translation_utils import TranslationManager


class TestTranslationCoverage:
    """Test translation coverage analysis"""

    def test_coverage_report_generation(self):
        """Test: Generate translation coverage metrics"""
        manager = TranslationManager()

        report = manager.generate_translation_coverage_report()

        # Validate report structure
        assert isinstance(report, dict)
        assert "total_records" in report
        assert "locales" in report
        assert "coverage" in report

    def test_missing_translations_detection(self):
        """Test: Detect missing translations"""
        manager = TranslationManager()

        missing = manager.detect_missing_translations("Product", "fr_FR")

        # Should return a list (even if empty for now)
        assert isinstance(missing, list)

    def test_coalesce_fallback_generation(self):
        """Test: Generate COALESCE fallback SQL"""
        manager = TranslationManager()

        sql = manager.generate_coalesce_fallback("name", ["fr_table", "en_table"])

        expected = "COALESCE(fr_table.name, en_table.name)"
        assert sql == expected
