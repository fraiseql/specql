"""
Tests for Polymorphic Type Resolver Pattern.

Tests the polymorphic/type_resolver pattern that resolves ambiguous PKs to entity types.
"""

import pytest
from unittest.mock import Mock

from src.patterns.pattern_registry import PatternRegistry


class TestPolymorphicTypeResolver:
    """Test the polymorphic type resolver pattern."""

    def test_generate_type_resolver_view(self):
        """Test generating a polymorphic type resolver view."""
        registry = PatternRegistry()

        # Mock entity data
        entity = {
            "name": "Pricing",
            "schema": "tenant",
            "query_patterns": [
                {
                    "name": "pk_class_resolver",
                    "pattern": "polymorphic/type_resolver",
                    "config": {
                        "discriminator_field": "class",
                        "variants": [
                            {
                                "entity": {
                                    "schema": "tenant",
                                    "table": "tb_product",
                                    "pk_field": "pk_product",
                                },
                                "key_field": "pk_product",
                                "class_value": "product",
                            },
                            {
                                "entity": {
                                    "schema": "tenant",
                                    "table": "tb_contract_item",
                                    "pk_field": "pk_contract_item",
                                },
                                "key_field": "pk_contract_item",
                                "class_value": "contract_item",
                            },
                        ],
                        "output_key": "pk_value",
                        "schema": "tenant",
                        "materialized": True,
                    },
                }
            ],
        }

        # This should work once the pattern is implemented
        pattern = registry.get_pattern("polymorphic/type_resolver")
        sql = pattern.generate(entity, entity["query_patterns"][0])

        # Verify the generated SQL contains expected elements
        assert "CREATE OR REPLACE VIEW tenant.v_pk_class_resolver AS" in sql
        assert "pk_product AS pk_value" in sql
        assert "'product'::text AS class" in sql
        assert "FROM tenant.tb_product" in sql
        assert "UNION ALL" in sql
        assert "pk_contract_item AS pk_value" in sql
        assert "'contract_item'::text AS class" in sql
        assert "FROM tenant.tb_contract_item" in sql
        assert "CREATE MATERIALIZED VIEW tenant.mv_pk_class_resolver AS" in sql
        assert "CREATE UNIQUE INDEX" in sql
        assert "refresh_mv_pk_class_resolver" in sql

    def test_type_resolver_with_minimal_config(self):
        """Test type resolver with minimal configuration."""
        registry = PatternRegistry()

        entity = {
            "name": "TestEntity",
            "schema": "tenant",
            "query_patterns": [
                {
                    "name": "simple_resolver",
                    "pattern": "polymorphic/type_resolver",
                    "config": {
                        "discriminator_field": "type",
                        "variants": [
                            {
                                "entity": {
                                    "schema": "tenant",
                                    "table": "tb_entity_a",
                                    "pk_field": "id",
                                },
                                "key_field": "id",
                                "class_value": "A",
                            }
                        ],
                        "output_key": "entity_id",
                    },
                }
            ],
        }

        pattern = registry.get_pattern("polymorphic/type_resolver")
        sql = pattern.generate(entity, entity["query_patterns"][0])

        # Should use defaults for schema and materialized
        assert "CREATE OR REPLACE VIEW tenant.v_simple_resolver AS" in sql
        assert "entity_id" in sql
        assert "type" in sql
        # Should not include materialized view by default
        assert "CREATE MATERIALIZED VIEW" not in sql

    def test_type_resolver_validation(self):
        """Test that invalid configurations are rejected."""
        registry = PatternRegistry()

        # Missing required discriminator_field
        invalid_config = {
            "name": "invalid_resolver",
            "pattern": "polymorphic/type_resolver",
            "config": {
                "variants": [
                    {
                        "entity": {"schema": "tenant", "table": "tb_test", "pk_field": "id"},
                        "key_field": "id",
                        "class_value": "test",
                    }
                ]
            },
        }

        entity = {"name": "Test", "schema": "tenant", "query_patterns": [invalid_config]}

        with pytest.raises(ValueError, match="discriminator_field.*required"):
            pattern = registry.get_pattern("polymorphic/type_resolver")
            pattern.generate(entity, invalid_config)
