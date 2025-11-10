"""Tests for assembly/simple_aggregation pattern."""

import pytest
from src.patterns.assembly.simple_aggregation import generate_simple_aggregation


class TestSimpleAggregation:
    """Test simple subquery aggregation pattern."""

    def test_generate_contract_with_items(self):
        """Test generation of v_contract_with_items (subquery aggregation)."""
        config = {
            "name": "v_contract_with_items",
            "pattern": "assembly/simple_aggregation",
            "config": {
                "parent_entity": "Contract",
                "child_entity": "ContractItem",
                "child_array_field": "items",
                "child_fields": [
                    {"name": "pk_contract_item", "expression": "ci.pk_contract_item"},
                    {"name": "quantity", "expression": "ci.quantity"},
                    {"name": "unit_price", "expression": "ci.unit_price"},
                ],
            },
        }

        sql = generate_simple_aggregation(config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "v_contract_with_items" in sql
        assert "SELECT" in sql
        assert "jsonb_agg" in sql
        assert "jsonb_build_object" in sql

        # Verify subquery structure
        assert "(" in sql  # Subquery
        assert "SELECT jsonb_agg" in sql
        assert "FROM tb_contract_item" in sql
        assert "WHERE" in sql
        assert "pk_contract" in sql

        # Verify JSONB array field
        assert "items" in sql

    def test_simple_aggregation_with_ordering(self):
        """Test simple aggregation with ordered results."""
        config = {
            "name": "v_product_with_features",
            "pattern": "assembly/simple_aggregation",
            "config": {
                "parent_entity": "Product",
                "child_entity": "ProductFeature",
                "child_array_field": "features",
                "child_fields": [
                    {"name": "name", "expression": "pf.name"},
                    {"name": "value", "expression": "pf.value"},
                ],
                "order_by": "pf.sort_order",
            },
        }

        sql = generate_simple_aggregation(config)

        # Should include ORDER BY in jsonb_agg
        assert "ORDER BY pf.sort_order" in sql

    def test_simple_aggregation_validation(self):
        """Test validation of simple aggregation configuration."""
        # Invalid config - missing required fields
        invalid_config = {
            "name": "v_invalid",
            "pattern": "assembly/simple_aggregation",
            "config": {
                # Missing parent_entity
                "child_entity": "Child"
            },
        }

        with pytest.raises(ValueError, match="parent_entity.*required"):
            generate_simple_aggregation(invalid_config)
