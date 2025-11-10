"""Tests for hierarchical path expander pattern."""

import pytest
from src.patterns.hierarchical.path_expander import generate_path_expander


class TestHierarchicalPathExpander:
    """Test hierarchical path expander pattern generation."""

    def test_generate_location_ancestor_names(self):
        """Test generating v_location_ancestor_names view."""
        config = {
            "name": "v_location_ancestor_names",
            "pattern": "hierarchical/path_expander",
            "config": {
                "source_entity": "Location",
                "path_field": "path",
                "expanded_fields": ["ancestor_names", "ancestor_ids"],
            },
        }

        sql = generate_path_expander(config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "v_location_ancestor_names" in sql
        assert "FROM tenant.tb_location" in sql

        # Verify CTE structure
        assert "WITH expanded AS" in sql
        assert "enriched AS" in sql

        # Verify path expansion
        assert "unnest(string_to_array(path::text, '.'))::integer AS ancestor_id" in sql
        assert "array_agg(a.name ORDER BY nlevel(a.path)) AS ancestor_names" in sql
        assert "array_agg(a.pk_location ORDER BY nlevel(a.path)) AS ancestor_ids" in sql

        # Verify final select
        assert "SELECT * FROM enriched" in sql

    def test_generate_location_breadcrumb_labels(self):
        """Test generating breadcrumb labels from path."""
        config = {
            "name": "v_location_breadcrumbs",
            "pattern": "hierarchical/path_expander",
            "config": {
                "source_entity": "Location",
                "path_field": "hierarchy_path",
                "expanded_fields": ["breadcrumb_labels", "ancestor_ids"],
            },
        }

        sql = generate_path_expander(config)

        assert "v_location_breadcrumbs" in sql
        assert "unnest(string_to_array(hierarchy_path::text, '.'))::integer AS ancestor_id" in sql
        assert (
            "array_agg(a.display_name ORDER BY nlevel(a.hierarchy_path)) AS breadcrumb_labels"
            in sql
        )

    def test_generate_org_unit_ancestors(self):
        """Test generating organizational unit ancestors."""
        config = {
            "name": "v_org_unit_ancestors",
            "pattern": "hierarchical/path_expander",
            "config": {
                "source_entity": "OrganizationalUnit",
                "path_field": "tree_path",
                "expanded_fields": ["ancestor_names", "ancestor_ids", "breadcrumb_labels"],
            },
        }

        sql = generate_path_expander(config)

        assert "v_org_unit_ancestors" in sql
        assert "FROM tenant.tb_organizational_unit" in sql
        assert "unnest(string_to_array(tree_path::text, '.'))::integer AS ancestor_id" in sql
        assert "array_agg(a.name ORDER BY nlevel(a.tree_path)) AS ancestor_names" in sql
        assert "array_agg(a.display_name ORDER BY nlevel(a.tree_path)) AS breadcrumb_labels" in sql

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raise appropriate errors."""
        config = {
            "name": "v_incomplete",
            "pattern": "hierarchical/path_expander",
            "config": {
                # Missing source_entity
                "path_field": "path",
                "expanded_fields": ["ancestor_names"],
            },
        }

        with pytest.raises(ValueError, match="source_entity is required"):
            generate_path_expander(config)

    def test_missing_path_field_raises_error(self):
        """Test that missing path_field raises error."""
        config = {
            "name": "v_no_path",
            "pattern": "hierarchical/path_expander",
            "config": {
                "source_entity": "Location",
                # Missing path_field
                "expanded_fields": ["ancestor_names"],
            },
        }

        with pytest.raises(ValueError, match="path_field is required"):
            generate_path_expander(config)

    def test_empty_expanded_fields_raises_error(self):
        """Test that empty expanded_fields raises error."""
        config = {
            "name": "v_no_fields",
            "pattern": "hierarchical/path_expander",
            "config": {
                "source_entity": "Location",
                "path_field": "path",
                "expanded_fields": [],  # Empty
            },
        }

        with pytest.raises(ValueError, match="expanded_fields cannot be empty"):
            generate_path_expander(config)

    def test_invalid_expanded_field_raises_error(self):
        """Test that invalid expanded field raises error."""
        config = {
            "name": "v_invalid_field",
            "pattern": "hierarchical/path_expander",
            "config": {
                "source_entity": "Location",
                "path_field": "path",
                "expanded_fields": ["invalid_field"],
            },
        }

        with pytest.raises(ValueError, match="Invalid expanded field"):
            generate_path_expander(config)
