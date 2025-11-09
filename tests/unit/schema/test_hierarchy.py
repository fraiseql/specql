"""
Tests for LTREE hierarchy path functionality
Tests INTEGER-based LTREE path calculation and management
"""

import pytest
from jinja2 import Template


class TestHierarchyTemplates:
    """Test hierarchy template rendering and structure."""

    def test_calculate_path_template_renders(self):
        """Test that calculate_path template renders correctly."""
        with open("templates/sql/hierarchy/calculate_path.sql.jinja2", "r") as f:
            template = Template(f.read())

        result = template.render(schema="tenant", entity_lower="location")

        assert "CREATE OR REPLACE FUNCTION tenant.calculate_location_path" in result
        assert "RETURNS ltree" in result
        assert "p_pk_location INTEGER" in result
        assert "fk_parent_location" in result
        assert "path::text || '.' || p_pk_location::text" in result
        assert "@specql:hierarchy" in result

    def test_recalculate_descendants_template_renders(self):
        """Test that recalculate_descendants template renders correctly."""
        with open("templates/sql/hierarchy/recalculate_descendants.sql.jinja2", "r") as f:
            template = Template(f.read())

        result = template.render(schema="tenant", entity_lower="location")

        assert "CREATE OR REPLACE FUNCTION tenant.recalculate_location_descendant_paths" in result
        assert "RETURNS INTEGER" in result
        assert "RECURSIVE subtree" in result
        assert "calculate_location_path" in result
        assert "path_updated_at = now()" in result
        assert "path_updated_by" in result
        assert "IS DISTINCT FROM" in result  # Idempotent check


class TestHierarchyTemplateIntegration:
    """Test that hierarchy templates work together."""

    def test_all_hierarchy_templates_render_with_same_entity(self):
        """Test that all hierarchy templates render consistently for the same entity."""
        entity_config = {"schema": "inventory", "entity_lower": "category"}

        # Test calculate_path
        with open("templates/sql/hierarchy/calculate_path.sql.jinja2", "r") as f:
            calc_template = Template(f.read())
        calc_result = calc_template.render(**entity_config)
        assert "inventory.calculate_category_path" in calc_result

        # Test recalculate descendants
        with open("templates/sql/hierarchy/recalculate_descendants.sql.jinja2", "r") as f:
            recalc_template = Template(f.read())
        recalc_result = recalc_template.render(**entity_config)
        assert "inventory.recalculate_category_descendant_paths" in recalc_result

    def test_hierarchy_templates_contain_proper_dependencies(self):
        """Test that templates reference each other correctly."""
        entity_config = {"schema": "tenant", "entity_lower": "department"}

        # Recalculate should reference calculate function
        with open("templates/sql/hierarchy/recalculate_descendants.sql.jinja2", "r") as f:
            recalc_template = Template(f.read())
        recalc_result = recalc_template.render(**entity_config)

        assert "tenant.calculate_department_path" in recalc_result
