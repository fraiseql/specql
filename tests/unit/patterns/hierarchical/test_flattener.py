"""Tests for hierarchical flattener pattern."""

import pytest
from src.patterns.hierarchical.flattener import generate_hierarchical_flattener


class TestHierarchicalFlattener:
    """Test hierarchical flattener pattern generation."""

    def test_generate_flat_location_for_rust_tree(self):
        """Test generating v_flat_location_for_rust_tree view."""
        config = {
            "name": "v_flat_location_for_rust_tree",
            "pattern": "hierarchical/flattener",
            "config": {
                "source_table": "tv_location",
                "extracted_fields": [
                    {"name": "code", "expression": "data->>'code'"},
                    {"name": "name", "expression": "data->>'name'"},
                    {"name": "type", "expression": "data->>'type'"},
                    {
                        "name": "is_active",
                        "expression": "(data->>'is_active')::boolean",
                    },
                ],
                "frontend_format": "rust_tree",
                "label_field": "name",
                "path_field": "path",
            },
        }

        sql = generate_hierarchical_flattener(config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "v_flat_location_for_rust_tree" in sql
        assert "FROM tenant.tv_location" in sql

        # Verify extracted fields
        assert "data->>'code' AS code" in sql
        assert "data->>'name' AS name" in sql
        assert "data->>'type' AS type" in sql
        assert "(data->>'is_active')::boolean AS is_active" in sql

        # Verify required tree fields
        assert "(data->>'id')::uuid AS id" in sql
        assert "NULLIF(data->'parent'->>'id', '')::uuid AS parent_id" in sql
        assert "data->>'name' AS label" in sql
        assert "data->>'id' AS value" in sql

        # Verify ltree field
        assert "REPLACE(data->>'path', '.', '_')::text AS ltree_id" in sql

        # Verify indexes
        assert (
            "CREATE INDEX IF NOT EXISTS idx_v_flat_location_for_rust_tree_parent" in sql
        )
        assert (
            "CREATE INDEX IF NOT EXISTS idx_v_flat_location_for_rust_tree_ltree" in sql
        )

        # Verify WHERE clause
        assert "WHERE deleted_at IS NULL" in sql

    def test_generate_flat_location_for_react_tree(self):
        """Test generating flattener for React tree component."""
        config = {
            "name": "v_flat_location_for_react_tree",
            "pattern": "hierarchical/flattener",
            "config": {
                "source_table": "tv_location",
                "extracted_fields": [
                    {"name": "code", "expression": "data->>'code'"},
                    {"name": "display_name", "expression": "data->>'display_name'"},
                ],
                "frontend_format": "react_tree",
                "label_field": "display_name",
            },
        }

        sql = generate_hierarchical_flattener(config)

        # Verify React-specific formatting
        assert "v_flat_location_for_react_tree" in sql
        assert "data->>'display_name' AS label" in sql
        # No path_field specified, so no ltree index
        assert "idx_v_flat_location_for_react_tree_ltree" not in sql

    def test_generate_generic_flattener(self):
        """Test generating generic flattener without frontend format."""
        config = {
            "name": "v_flat_generic",
            "pattern": "hierarchical/flattener",
            "config": {
                "source_table": "tv_category",
                "extracted_fields": [
                    {"name": "title", "expression": "data->>'title'"},
                    {"name": "description", "expression": "data->>'description'"},
                ],
                "frontend_format": "generic",
                "label_field": "title",
                "path_field": "hierarchy_path",
            },
        }

        sql = generate_hierarchical_flattener(config)

        assert "v_flat_generic" in sql
        assert "FROM tenant.tv_category" in sql
        assert "REPLACE(data->>'hierarchy_path', '.', '_')::text AS ltree_id" in sql

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raise appropriate errors."""
        config = {
            "name": "v_incomplete",
            "pattern": "hierarchical/flattener",
            "config": {
                # Missing source_table
                "extracted_fields": [{"name": "test", "expression": "data->>'test'"}]
            },
        }

        with pytest.raises(ValueError, match="source_table is required"):
            generate_hierarchical_flattener(config)

    def test_invalid_frontend_format_raises_error(self):
        """Test that invalid frontend format raises error."""
        config = {
            "name": "v_invalid_format",
            "pattern": "hierarchical/flattener",
            "config": {
                "source_table": "tv_test",
                "extracted_fields": [{"name": "test", "expression": "data->>'test'"}],
                "frontend_format": "invalid_format",
            },
        }

        with pytest.raises(ValueError, match="frontend_format must be one of"):
            generate_hierarchical_flattener(config)
