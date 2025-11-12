"""Integration tests for locale-aware aggregation"""

from src.patterns.pattern_registry import PatternRegistry


class TestLocaleAggregationIntegration:
    """Test locale-aware aggregation in real scenarios"""

    def test_aggregation_with_multiple_locales(self):
        """Test: Aggregation works with multiple locale fallbacks"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("localization/locale_aggregation")

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
                    {"metric": "total_products", "function": "COUNT", "field": "pk_product"},
                    {"metric": "avg_price", "function": "AVG", "field": "price"},
                ],
                "fallback_locale": "en_US",
                "translation_table": "tl_product",
            },
        }

        sql = pattern.generate(entity, config)

        # Validate SQL structure
        assert "COALESCE" in sql
        assert "GROUP BY" in sql
        assert "COUNT(tb_product.pk_product)" in sql
        assert "AVG(tb_product.price)" in sql
        assert "INNER JOIN" in sql  # For fallback
        assert "LEFT JOIN" in sql  # For current locale

        # Validate proper aggregation structure
        assert "total_products" in sql
        assert "avg_price" in sql
