"""Tests for translated view pattern"""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestTranslatedView:
    """Test translated view pattern generation"""

    def test_translated_view_with_fallback(self):
        """Test: Generate localized view with fallback logic"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("localization/translated_view")

        # This should fail initially - pattern doesn't exist yet
        assert pattern is not None

        entity = {
            "name": "Product",
            "schema": "tenant",
            "table": "tb_product",
            "pk_field": "pk_product",
            "fk_field": "fk_product",  # Foreign key to translation table
            "is_multi_tenant": True,
            "fields": [
                {"name": "pk_product"},
                {"name": "name"},
                {"name": "description"},
                {"name": "price"},
                {"name": "created_at"},
            ],
        }

        config = {
            "name": "v_product_localized",
            "pattern": "localization/translated_view",
            "config": {
                "translatable_fields": ["name", "description", "specifications"],
                "fallback_locale": "en_US",
                "translation_table": "tl_product",
            },
        }

        sql = pattern.generate(entity, config)

        # Validate COALESCE fallback logic
        assert "COALESCE" in sql
        assert "tl_product" in sql
        assert "en_US" in sql
