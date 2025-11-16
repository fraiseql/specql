"""Tests for locale-aware aggregation pattern"""

from src.patterns.pattern_registry import PatternRegistry


class TestLocaleAggregation:
    """Test locale-aware aggregation pattern generation"""

    def test_locale_aggregation_with_fallback(self):
        """Test: Generate localized aggregation with fallback logic"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("localization/locale_aggregation")

        # This should fail initially - pattern doesn't exist yet
        assert pattern is not None

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
                {"name": "category"},
                {"name": "created_at"},
            ],
        }

        config = {
            "name": "v_product_category_summary",
            "pattern": "localization/locale_aggregation",
            "config": {
                "group_by_field": "category",
                "aggregations": [
                    {
                        "metric": "total_products",
                        "function": "COUNT",
                        "field": "pk_product",
                    },
                    {"metric": "avg_price", "function": "AVG", "field": "price"},
                ],
                "fallback_locale": "en_US",
                "translation_table": "tl_product",
            },
        }

        sql = pattern.generate(entity, config)

        # Validate COALESCE fallback logic in GROUP BY
        assert "COALESCE" in sql
        assert "GROUP BY" in sql
        assert "COUNT" in sql
        assert "AVG" in sql
