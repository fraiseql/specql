"""Test core.recalculate_identifier() function."""

from jinja2 import Template


class TestRecalculateIdentifier:
    """Test identifier recalculation function."""

    def test_recalculate_identifier_template_exists(self):
        """Should have recalculate_identifier template."""
        try:
            with open("templates/sql/hierarchy/recalculate_identifier.sql.jinja2") as f:
                template_content = f.read()
        except FileNotFoundError:
            # Template doesn't exist yet - this is expected for RED test
            assert (
                False
            ), "Template templates/sql/hierarchy/recalculate_identifier.sql.jinja2 should exist"

        # Check that it contains the function
        assert "recalculate_identifier" in template_content

    def test_recalculate_identifier_template_structure(self):
        """Should define function with correct signature and logic."""
        with open("templates/sql/hierarchy/recalculate_identifier.sql.jinja2") as f:
            template = Template(f.read())

        result = template.render()

        # Should contain the function definition
        assert "CREATE OR REPLACE FUNCTION core.recalculate_identifier" in result
        assert "RETURNS INTEGER" in result

        # Should have parameters
        assert "entity TEXT" in result
        assert "recalculation_context" in result

        # Should have recalculation logic
        assert "safe_slug" in result
        assert "identifier_recalculated_at" in result
        assert "identifier_recalculated_by" in result
