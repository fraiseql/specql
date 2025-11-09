"""
E2E integration test for tv_ table FraiseQL annotations
Tests complete integration: SchemaOrchestrator → TableViewAnnotator
"""

from src.core.ast_models import (
    EntityDefinition,
    ExtraFilterColumn,
    FieldDefinition,
    IncludeRelation,
    TableViewConfig,
    TableViewMode,
)
from src.generators.schema_orchestrator import SchemaOrchestrator


class TestTableViewAnnotationsE2E:
    """End-to-end tests for tv_ table FraiseQL annotation generation"""

    def test_complete_tv_table_with_annotations(self):
        """Test: Complete tv_ table generation includes FraiseQL annotations"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "author": FieldDefinition(name="author", type_name="ref(User)"),
                "book": FieldDefinition(name="book", type_name="ref(Book)"),
                "rating": FieldDefinition(name="rating", type_name="integer"),
            },
            actions=[],
            table_views=TableViewConfig(
                include_relations=[
                    IncludeRelation(entity_name="User", fields=["name", "email"]),
                    IncludeRelation(entity_name="Book", fields=["title", "isbn"]),
                ],
                extra_filter_columns=[
                    ExtraFilterColumn(name="rating", type="INTEGER", index_type="btree"),
                ],
            ),
        )

        orchestrator = SchemaOrchestrator()
        sql = orchestrator.generate_table_views([entity])

        # Verify table creation
        assert "CREATE TABLE library.tv_review" in sql
        assert "pk_review INTEGER PRIMARY KEY" in sql
        assert "fk_user INTEGER" in sql
        assert "fk_book INTEGER" in sql
        assert "data JSONB NOT NULL" in sql

        # Verify FraiseQL table annotation
        assert "COMMENT ON TABLE library.tv_review IS" in sql
        assert "@fraiseql:table source=materialized" in sql
        assert "refresh=explicit" in sql
        assert "primary=true" in sql

        # Verify internal column annotations
        assert "COMMENT ON COLUMN library.tv_review.pk_review" in sql
        assert "@fraiseql:field internal=true" in sql
        assert "Internal primary key" in sql

        assert "COMMENT ON COLUMN library.tv_review.fk_user" in sql
        assert "Internal FK for User" in sql

        assert "COMMENT ON COLUMN library.tv_review.fk_book" in sql
        assert "Internal FK for Book" in sql

        assert "COMMENT ON COLUMN library.tv_review.refreshed_at" in sql
        assert "Last refresh timestamp" in sql

        # Verify filter column annotations
        assert "COMMENT ON COLUMN library.tv_review.tenant_id" in sql
        assert "@fraiseql:filter type=UUID" in sql
        assert "Multi-tenant filter" in sql

        assert "COMMENT ON COLUMN library.tv_review.user_id" in sql
        assert "relation=User" in sql

        assert "COMMENT ON COLUMN library.tv_review.book_id" in sql
        assert "relation=Book" in sql

        assert "COMMENT ON COLUMN library.tv_review.rating" in sql
        assert "@fraiseql:filter type=Int" in sql

        # Verify data column annotation
        assert "COMMENT ON COLUMN library.tv_review.data" in sql
        assert "@fraiseql:jsonb expand=true" in sql
        assert "Denormalized Review data" in sql

    def test_no_annotations_for_entity_without_table_views(self):
        """Test: No FraiseQL annotations generated for entities without table views"""
        entity = EntityDefinition(
            name="Contact",
            schema="crm",
            fields={},
            actions=[],
            table_views=None,  # No table views
        )

        orchestrator = SchemaOrchestrator()
        sql = orchestrator.generate_table_views([entity])

        # Should be empty - no table views to generate
        assert sql == ""

    def test_multiple_entities_generate_annotations(self):
        """Test: Multiple entities generate separate annotation blocks"""
        entities = [
            EntityDefinition(
                name="User",
                schema="library",
                fields={},
                actions=[],
                table_views=TableViewConfig(mode=TableViewMode.FORCE, include_relations=[]),
            ),
            EntityDefinition(
                name="Book",
                schema="library",
                fields={},
                actions=[],
                table_views=TableViewConfig(mode=TableViewMode.FORCE, include_relations=[]),
            ),
        ]

        orchestrator = SchemaOrchestrator()
        sql = orchestrator.generate_table_views(entities)

        # Both tables should be created
        assert "CREATE TABLE library.tv_user" in sql
        assert "CREATE TABLE library.tv_book" in sql

        # Both should have FraiseQL annotations
        assert sql.count("@fraiseql:table") == 2
        assert sql.count("@fraiseql:jsonb expand=true") == 2

        # Should be separated by annotation headers
        assert "FraiseQL Annotations: library.tv_user" in sql
        assert "FraiseQL Annotations: library.tv_book" in sql
