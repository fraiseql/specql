"""
Unit tests for RefreshTableViewStepCompiler

Tests compilation of refresh_table_view steps to PL/pgSQL PERFORM calls.
"""

import pytest

from src.core.ast_models import (
    ActionStep,
    EntityDefinition,
    FieldDefinition,
    FieldTier,
    RefreshScope,
)
from src.generators.actions.step_compilers.refresh_table_view_compiler import (
    RefreshTableViewStepCompiler,
)


class TestRefreshTableViewStepCompiler:
    """Test RefreshTableViewStepCompiler functionality"""

    def setup_method(self):
        """Setup compiler instance for each test"""
        self.compiler = RefreshTableViewStepCompiler()

    def test_compile_refresh_self_scope(self):
        """Test compiling refresh_table_view with self scope"""
        # Create test entity
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(
                    name="author",
                    type_name="ref",
                    reference_entity="User",
                    tier=FieldTier.REFERENCE,
                ),
            },
        )

        # Create refresh step
        step = ActionStep(
            type="refresh_table_view",
            refresh_scope=RefreshScope.SELF,
            propagate_entities=[],
            refresh_strategy="immediate",
        )

        # Compile
        context = {"current_entity": entity}
        result = self.compiler.compile(step, entity, context)

        # Verify
        expected = """
    -- Refresh table view (self)
    PERFORM library.refresh_tv_review(v_pk_review);
""".strip()

        assert result == expected

    def test_compile_refresh_propagate_scope(self):
        """Test compiling refresh_table_view with propagate scope"""
        # Create test entity
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(
                    name="author",
                    type_name="ref",
                    reference_entity="User",
                    tier=FieldTier.REFERENCE,
                ),
                "book": FieldDefinition(
                    name="book",
                    type_name="ref",
                    reference_entity="Book",
                    tier=FieldTier.REFERENCE,
                ),
            },
        )

        # Create refresh step
        step = ActionStep(
            type="refresh_table_view",
            refresh_scope=RefreshScope.PROPAGATE,
            propagate_entities=["author", "book"],
            refresh_strategy="immediate",
        )

        # Compile with context that includes FK mappings
        context = {
            "current_entity": entity,
            "entity_registry": {
                "User": EntityDefinition(name="User", schema="crm"),
                "Book": EntityDefinition(name="Book", schema="library"),
            },
            "fk_vars": {
                "author": "v_fk_author",
                "book": "v_fk_book",
            },
        }
        result = self.compiler.compile(step, entity, context)

        # Verify
        expected_lines = [
            "-- Refresh table view (self + propagate)",
            "PERFORM library.refresh_tv_review(v_pk_review);",
            "PERFORM crm.refresh_tv_user(v_fk_author);",
            "PERFORM library.refresh_tv_book(v_fk_book);",
        ]
        expected = "\n    ".join(expected_lines)

        assert result == expected

    def test_compile_refresh_related_scope(self):
        """Test compiling refresh_table_view with related scope"""
        # Create test entity
        entity = EntityDefinition(
            name="User",
            schema="crm",
            fields={
                "name": FieldDefinition(name="name", type_name="text"),
            },
        )

        # Create dependent entities
        review_entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(
                    name="author",
                    type_name="ref",
                    reference_entity="User",
                    tier=FieldTier.REFERENCE,
                ),
            },
        )

        # Create refresh step
        step = ActionStep(
            type="refresh_table_view",
            refresh_scope=RefreshScope.RELATED,
            propagate_entities=[],
            refresh_strategy="immediate",
        )

        # Compile with entity registry
        context = {
            "current_entity": entity,
            "entity_registry": {
                "User": entity,
                "Review": review_entity,
            },
        }
        result = self.compiler.compile(step, entity, context)

        # Verify
        expected_lines = [
            "-- Refresh table view (self + all related)",
            "PERFORM crm.refresh_tv_user(v_pk_user);",
            "-- Refresh Review entities that reference this User",
            "PERFORM library.refresh_tv_review_by_user(v_pk_user);",
        ]
        expected = "\n    ".join(expected_lines)

        assert result == expected

    def test_compile_refresh_batch_scope(self):
        """Test compiling refresh_table_view with batch scope"""
        # Create test entity
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
            },
        )

        # Create refresh step
        step = ActionStep(
            type="refresh_table_view",
            refresh_scope=RefreshScope.BATCH,
            propagate_entities=[],
            refresh_strategy="immediate",
        )

        # Compile
        context = {"current_entity": entity}
        result = self.compiler.compile(step, entity, context)

        # Verify
        expected = """
    -- Queue for batch refresh (deferred)
    INSERT INTO pg_temp.tv_refresh_queue VALUES ('Review', v_pk_review);
""".strip()

        assert result == expected

    def test_compile_invalid_step_type(self):
        """Test that compiler rejects invalid step types"""
        entity = EntityDefinition(name="Test", schema="test")

        step = ActionStep(type="invalid_type")

        with pytest.raises(ValueError, match="Expected refresh_table_view step"):
            self.compiler.compile(step, entity, {})

    def test_get_fk_var_for_entity(self):
        """Test FK variable resolution"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "author": FieldDefinition(
                    name="author",
                    type_name="ref",
                    reference_entity="User",
                    tier=FieldTier.REFERENCE,
                ),
                "book": FieldDefinition(
                    name="book", type_name="ref", reference_entity="Book", tier=FieldTier.REFERENCE
                ),
            },
        )

        # Test existing FK
        result = self.compiler._get_fk_var_for_entity(entity, "User", {})
        assert result == "v_fk_author"

        # Test non-existing FK
        result = self.compiler._get_fk_var_for_entity(entity, "NonExistent", {})
        assert result is None

    def test_get_entity_schema(self):
        """Test entity schema resolution"""
        context = {
            "entity_registry": {
                "User": EntityDefinition(name="User", schema="crm"),
            },
            "current_entity": EntityDefinition(name="Review", schema="library"),
        }

        # Test from registry
        result = self.compiler._get_entity_schema("User", context)
        assert result == "crm"

        # Test fallback to current entity
        result = self.compiler._get_entity_schema("Unknown", context)
        assert result == "library"

    def test_find_dependent_entities(self):
        """Test finding entities that reference this one"""
        # Create entities
        user_entity = EntityDefinition(
            name="User",
            schema="crm",
            fields={"name": FieldDefinition(name="name", type_name="text")},
        )

        review_entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(
                    name="author",
                    type_name="ref",
                    reference_entity="User",
                    tier=FieldTier.REFERENCE,
                ),
            },
        )

        book_entity = EntityDefinition(
            name="Book",
            schema="library",
            fields={"title": FieldDefinition(name="title", type_name="text")},
        )

        context = {
            "entity_registry": {
                "User": user_entity,
                "Review": review_entity,
                "Book": book_entity,
            }
        }

        # Find dependents of User
        result = self.compiler._find_dependent_entities(user_entity, context)

        # Should find Review (which references User)
        assert len(result) == 1
        assert result[0].name == "Review"
        assert result[0].schema == "library"
