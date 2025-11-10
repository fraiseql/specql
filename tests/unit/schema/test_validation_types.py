"""Test validation error types."""

from jinja2 import Template


class TestValidationErrorType:
    """Test core.hierarchy_validation_error composite type template."""

    def test_validation_error_type_template_exists(self):
        """Should have validation error type template."""
        try:
            with open("templates/sql/000_types.sql.jinja2") as f:
                template_content = f.read()
        except FileNotFoundError:
            # Template doesn't exist yet - this is expected for RED test
            assert False, "Template templates/sql/000_types.sql.jinja2 should exist"

        # Check that it contains the validation error type
        assert "hierarchy_validation_error" in template_content

    def test_validation_error_type_structure(self):
        """Should define validation error type with correct fields."""
        with open("templates/sql/000_types.sql.jinja2") as f:
            template = Template(f.read())

        result = template.render()

        # Should contain the type definition
        assert "CREATE TYPE core.hierarchy_validation_error AS" in result
        assert "error_code TEXT" in result
        assert "error_message TEXT" in result
        assert "hint TEXT" in result
        assert "detail JSONB" in result
