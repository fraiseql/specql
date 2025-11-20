"""
Unit tests for SuccessResponseGenerator

Tests generation of mutation_result success responses with tv_ data support.
"""

from core.ast_models import (
    EntityDefinition,
    FieldDefinition,
    TableViewConfig,
    TableViewMode,
)
from generators.actions.action_context import ActionContext
from generators.actions.success_response_generator import SuccessResponseGenerator


class TestSuccessResponseGenerator:
    """Test SuccessResponseGenerator functionality"""

    def setup_method(self):
        """Setup generator instance for each test"""
        self.generator = SuccessResponseGenerator()

    def test_generate_object_data_with_table_view(self):
        """Test generating object_data from tv_ table when entity uses table views"""
        # Create entity with table view enabled
        entity = EntityDefinition(
            name="Review",
            schema="library",
            table_views=TableViewConfig(mode=TableViewMode.FORCE),
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(name="author", type_name="ref", reference_entity="User"),
            },
        )

        # Create action context
        context = ActionContext(
            function_name="library.update_review",
            entity_schema="library",
            entity_name="Review",
            entity=entity,
            steps=[],
            impact=None,
            has_impact_metadata=False,
        )

        # Generate object data
        result = self.generator.generate_object_data(context)

        # Verify it uses tv_ table
        expected = """
    -- Build result from table view (denormalized)
    SELECT data  -- JSONB from tv_
    FROM library.tv_review
    WHERE pk_review = v_pk
    INTO v_result.object_data;
"""

        assert result.strip() == expected.strip()

    def test_generate_object_data_without_table_view(self):
        """Test generating object_data from tb_ table when entity doesn't use table views"""
        # Create entity without table view
        entity = EntityDefinition(
            name="Review",
            schema="library",
            table_views=TableViewConfig(mode=TableViewMode.DISABLE),
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(name="author", type_name="ref", reference_entity="User"),
            },
        )

        # Create action context with impact metadata
        context = ActionContext(
            function_name="library.update_review",
            entity_schema="library",
            entity_name="Review",
            entity=entity,
            steps=[],
            impact={"primary": {"fields": ["rating"], "include_relations": ["author"]}},
            has_impact_metadata=True,
        )

        # Generate object data
        result = self.generator.generate_object_data(context)

        # Verify it builds JSONB from tb_ table
        assert "FROM library.tb_review c" in result
        assert "jsonb_build_object" in result
        assert "'rating', c.rating" in result
        assert "'author', null  -- TODO: Implement author relationship" in result

    def test_generate_success_response_complete(self):
        """Test generating complete success response"""
        # Create entity with table view
        entity = EntityDefinition(
            name="Review",
            schema="library",
            table_views=TableViewConfig(mode=TableViewMode.FORCE),
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
            },
        )

        # Create action context
        context = ActionContext(
            function_name="library.update_review",
            entity_schema="library",
            entity_name="Review",
            entity=entity,
            steps=[],
            impact={"primary": {"fields": ["rating"]}},
            has_impact_metadata=True,
        )

        # Generate success response
        result = self.generator.generate_success_response(context)

        # Verify structure
        assert "v_result.status := 'success';" in result
        assert "v_result.message := 'Operation completed successfully';" in result
        assert "SELECT data" in result  # Uses tv_ data
        assert "v_result.updated_fields := ARRAY['rating'];" in result
        assert "v_result.extra_metadata := jsonb_build_object" in result
