"""Test core.validate_hierarchy_change() function."""

from jinja2 import Template


class TestValidateHierarchyChange:
    """Test hierarchy validation function."""

    def test_validate_hierarchy_template_exists(self):
        """Should have validate_hierarchy_change template."""
        try:
            with open("templates/sql/hierarchy/validate_hierarchy_change.sql.jinja2") as f:
                template_content = f.read()
        except FileNotFoundError:
            # Template doesn't exist yet - this is expected for RED test
            assert False, (
                "Template templates/sql/hierarchy/validate_hierarchy_change.sql.jinja2 should exist"
            )

        # Check that it contains the function
        assert "validate_hierarchy_change" in template_content

    def test_validate_hierarchy_template_structure(self):
        """Should define function with correct signature and logic."""
        with open("templates/sql/hierarchy/validate_hierarchy_change.sql.jinja2") as f:
            template = Template(f.read())

        result = template.render()

        # Should contain the function definition
        assert "CREATE OR REPLACE FUNCTION core.validate_hierarchy_change" in result
        assert "RETURNS core.hierarchy_validation_error" in result

        # Should have parameters
        assert "entity TEXT" in result
        assert "node_pk INTEGER" in result
        assert "new_parent_pk INTEGER" in result

        # Should have validation logic
        assert "circular_reference" in result
        assert "depth_limit_exceeded" in result
        assert "ltree" in result  # Uses ltree for path operations
