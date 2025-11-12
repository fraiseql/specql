"""Integration tests for locale fallback functionality"""

from src.patterns.pattern_registry import PatternRegistry


class TestLocaleFallback:
    """Test locale fallback in real database scenarios"""

    def test_multi_locale_fallback(self):
        """Test: Multi-locale queries with proper fallback"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("localization/translated_view")

        entity = {
            "name": "Product",
            "schema": "tenant",
            "table": "tb_product",
            "pk_field": "pk_product",
            "fk_field": "fk_product",
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
                "translatable_fields": ["name", "description"],
                "fallback_locale": "en_US",
                "translation_table": "tl_product",
                "current_locale_source": "CURRENT_SETTING('app.current_locale')",
                "include_all_locales": True,
            },
        }

        sql = pattern.generate(entity, config)

        # Validate SQL contains expected elements
        assert "COALESCE" in sql
        assert "tl_product" in sql
        assert "en_US" in sql
        assert "all_translations" in sql
        assert "jsonb_object_agg" in sql
        assert "CURRENT_SETTING('app.current_locale')" in sql

        # Validate proper JOIN structure
        assert "INNER JOIN" in sql  # For fallback locale
        assert "LEFT JOIN" in sql  # For current locale
