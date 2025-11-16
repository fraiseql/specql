"""Test core.validate_identifier_sequence() function."""

from jinja2 import Template


class TestValidateIdentifierSequence:
    """Test identifier sequence validation function."""

    def test_validate_identifier_sequence_template_exists(self):
        """Should have validate_identifier_sequence template."""
        try:
            with open(
                "templates/sql/hierarchy/validate_identifier_sequence.sql.jinja2"
            ) as f:
                template_content = f.read()
        except FileNotFoundError:
            # Template doesn't exist yet - this is expected for RED test
            assert False, (
                "Template templates/sql/hierarchy/validate_identifier_sequence.sql.jinja2 should exist"
            )

        # Check that it contains the function
        assert "validate_identifier_sequence" in template_content

    def test_validate_identifier_sequence_template_structure(self):
        """Should define function with correct signature and logic."""
        with open(
            "templates/sql/hierarchy/validate_identifier_sequence.sql.jinja2"
        ) as f:
            template = Template(f.read())

        result = template.render()

        # Should contain the function definition
        assert "CREATE OR REPLACE FUNCTION core.validate_identifier_sequence" in result
        assert "RETURNS core.hierarchy_validation_error" in result

        # Should have parameters
        assert "entity TEXT" in result
        assert "identifier TEXT" in result
        assert "sequence_number INTEGER" in result
        assert "tenant_id UUID" in result

        # Should have validation logic
        assert "sequence_limit_exceeded" in result
        assert "max_duplicates" in result
