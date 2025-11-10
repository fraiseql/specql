"""Tests for assembly/tree_builder pattern."""

import pytest
from src.patterns.assembly.tree_builder import generate_tree_builder


class TestTreeBuilder:
    """Test complex multi-CTE tree builder pattern."""

    def test_generate_contract_price_tree(self):
        """Test generation of v_contract_price_tree (199 lines, 8 CTEs, 4 levels deep)."""
        config = {
            "name": "v_contract_price_tree",
            "pattern": "assembly/tree_builder",
            "config": {
                "root_entity": "Contract",
                "hierarchy": [
                    {
                        "level": "contract_base",
                        "source": "tb_contract",
                        "group_by": ["pk_contract"],
                        "child_levels": [
                            {
                                "level": "contract_items",
                                "source": "tb_contract_item",
                                "group_by": ["pk_contract"],
                                "array_field": "items",
                                "fields": [
                                    {
                                        "name": "pk_contract_item",
                                        "expression": "ci.pk_contract_item",
                                    },
                                    {"name": "quantity", "expression": "ci.quantity"},
                                    {"name": "unit_price", "expression": "ci.unit_price"},
                                ],
                            },
                            {
                                "level": "contract_prices",
                                "source": "tb_contract_price",
                                "group_by": ["pk_contract"],
                                "array_field": "prices",
                                "fields": [
                                    {
                                        "name": "pk_contract_price",
                                        "expression": "cp.pk_contract_price",
                                    },
                                    {"name": "price_type", "expression": "cp.price_type"},
                                    {"name": "amount", "expression": "cp.amount"},
                                ],
                                "child_levels": [
                                    {
                                        "level": "price_components",
                                        "source": "tb_price_component",
                                        "group_by": ["pk_contract_price"],
                                        "array_field": "components",
                                        "fields": [
                                            {
                                                "name": "pk_price_component",
                                                "expression": "pc.pk_price_component",
                                            },
                                            {
                                                "name": "component_type",
                                                "expression": "pc.component_type",
                                            },
                                            {"name": "value", "expression": "pc.value"},
                                        ],
                                    }
                                ],
                            },
                        ],
                    }
                ],
                "max_depth": 4,
            },
        }

        # This should generate a complex SQL with 8 CTEs
        sql = generate_tree_builder(config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "v_contract_price_tree" in sql
        assert "WITH" in sql  # CTEs present
        assert "contract_base" in sql
        assert "contract_items" in sql
        assert "contract_prices" in sql
        assert "price_components" in sql

        # Verify JSONB aggregation
        assert "jsonb_agg" in sql
        assert "jsonb_build_object" in sql

        # Verify hierarchical structure
        assert "items" in sql
        assert "prices" in sql
        assert "components" in sql

    def test_tree_builder_with_nested_aggregation(self):
        """Test tree builder with deeply nested aggregations."""
        config = {
            "name": "v_nested_tree",
            "pattern": "assembly/tree_builder",
            "config": {
                "root_entity": "Root",
                "hierarchy": [
                    {
                        "level": "root_level",
                        "source": "tb_root",
                        "group_by": ["pk_root"],
                        "child_levels": [
                            {
                                "level": "level1",
                                "source": "tb_level1",
                                "group_by": ["pk_root"],
                                "array_field": "level1_data",
                                "fields": [{"name": "id", "expression": "l1.id"}],
                                "child_levels": [
                                    {
                                        "level": "level2",
                                        "source": "tb_level2",
                                        "group_by": ["pk_level1"],
                                        "array_field": "level2_data",
                                        "fields": [{"name": "id", "expression": "l2.id"}],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }

        sql = generate_tree_builder(config)

        # Should have nested CTE structure
        assert "level1" in sql
        assert "level2" in sql
        assert "level1_data" in sql
        assert "level2_data" in sql

    def test_tree_builder_validation(self):
        """Test validation of tree builder configuration."""
        # Invalid config - missing required fields
        invalid_config = {
            "name": "v_invalid",
            "pattern": "assembly/tree_builder",
            "config": {
                # Missing root_entity
                "hierarchy": []
            },
        }

        with pytest.raises(ValueError, match="root_entity.*required"):
            generate_tree_builder(invalid_config)
