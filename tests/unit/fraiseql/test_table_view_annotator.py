"""
Unit tests for tv_ table FraiseQL annotation generator
"""

from core.ast_models import (
    EntityDefinition,
    ExtraFilterColumn,
    FieldDefinition,
    IncludeRelation,
    TableViewConfig,
)
from generators.fraiseql.table_view_annotator import TableViewAnnotator


class TestTableAnnotation:
    """Test table-level @fraiseql:table annotations"""

    def test_generates_table_annotation(self):
        """Test: Generates @fraiseql:table annotation for tv_ table"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={},
            actions=[],
            table_views=TableViewConfig(
                include_relations=[IncludeRelation(entity_name="author", fields=["name", "email"])]
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "COMMENT ON TABLE library.tv_review" in sql
        assert "@fraiseql:table" in sql
        assert "source=materialized" in sql
        assert "refresh=explicit" in sql
        assert "primary=true" in sql

    def test_skips_annotation_if_no_table_views(self):
        """Test: No annotations generated if entity has no table views"""
        entity = EntityDefinition(
            name="Contact",
            schema="crm",
            fields={},
            actions=[],
            table_views=None,  # No table views
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert sql == ""


class TestInternalColumnAnnotations:
    """Test internal column annotations (pk_*, fk_*, refreshed_at)"""

    def test_marks_primary_key_as_internal(self):
        """Test: pk_* column marked with internal=true"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={},
            actions=[],
            table_views=TableViewConfig(
                include_relations=[IncludeRelation(entity_name="author", fields=["name", "email"])]
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "COMMENT ON COLUMN library.tv_review.pk_review" in sql
        assert "@fraiseql:field internal=true" in sql
        assert "Internal primary key" in sql

    def test_marks_foreign_keys_as_internal(self):
        """Test: fk_* columns marked with internal=true"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "author": FieldDefinition(name="author", type_name="ref(User)"),
                "book": FieldDefinition(name="book", type_name="ref(Book)"),
            },
            actions=[],
            table_views=TableViewConfig(
                include_relations=[
                    IncludeRelation(entity_name="User", fields=["name", "email"]),
                    IncludeRelation(entity_name="Book", fields=["title", "isbn"]),
                ]
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        # Both FK columns should be marked internal
        assert "COMMENT ON COLUMN library.tv_review.fk_user" in sql
        assert "COMMENT ON COLUMN library.tv_review.fk_book" in sql
        assert sql.count("internal=true") >= 4  # pk + 2 fks + refreshed_at

    def test_marks_refreshed_at_as_internal(self):
        """Test: refreshed_at column marked with internal=true"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={},
            actions=[],
            table_views=TableViewConfig(
                include_relations=[IncludeRelation(entity_name="User", fields=["name", "email"])]
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "COMMENT ON COLUMN library.tv_review.refreshed_at" in sql
        assert "@fraiseql:field internal=true" in sql


class TestFilterColumnAnnotations:
    """Test filter column annotations for efficient WHERE clauses"""

    def test_annotates_tenant_id_as_filter(self):
        """Test: tenant_id annotated as UUID filter"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={},
            actions=[],
            table_views=TableViewConfig(
                include_relations=[IncludeRelation(entity_name="author", fields=["name", "email"])]
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "COMMENT ON COLUMN library.tv_review.tenant_id" in sql
        assert "@fraiseql:filter type=UUID" in sql
        assert "index=btree" in sql
        assert "performance=optimized" in sql

    def test_annotates_uuid_foreign_keys_as_filters(self):
        """Test: UUID FK columns annotated with relation info"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "author": FieldDefinition(name="author", type_name="ref(User)"),
                "book": FieldDefinition(name="book", type_name="ref(Book)"),
            },
            actions=[],
            table_views=TableViewConfig(
                include_relations=[
                    IncludeRelation(entity_name="User", fields=["name", "email"]),
                    IncludeRelation(entity_name="Book", fields=["title", "isbn"]),
                ]
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        # user_id filter (extracted from ref(User))
        assert "COMMENT ON COLUMN library.tv_review.user_id" in sql
        assert "@fraiseql:filter type=UUID" in sql
        assert "relation=User" in sql

        # book_id filter
        assert "COMMENT ON COLUMN library.tv_review.book_id" in sql
        assert "relation=Book" in sql

    def test_annotates_extra_filter_columns(self):
        """Test: Extra filter columns annotated with correct types"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "created_at": FieldDefinition(name="created_at", type_name="timestamp"),
            },
            actions=[],
            table_views=TableViewConfig(
                include_relations=[IncludeRelation(entity_name="author", fields=["name", "email"])],
                extra_filter_columns=[
                    ExtraFilterColumn(name="rating", type="INTEGER", index_type="btree"),
                    ExtraFilterColumn(name="created_at", type="TIMESTAMPTZ", index_type="btree"),
                ],
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        # rating filter
        assert "COMMENT ON COLUMN library.tv_review.rating" in sql
        assert "@fraiseql:filter type=Int" in sql

        # created_at filter
        assert "COMMENT ON COLUMN library.tv_review.created_at" in sql
        assert "@fraiseql:filter type=DateTime" in sql

    # Note: Hierarchical path annotation test skipped for now
    # EntityDefinition doesn't have hierarchical field, would need to add it


class TestDataColumnAnnotation:
    """Test JSONB data column annotation"""

    def test_annotates_data_column_with_expand(self):
        """Test: data column annotated with expand=true"""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={},
            actions=[],
            table_views=TableViewConfig(
                include_relations=[IncludeRelation(entity_name="author", fields=["name", "email"])]
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "COMMENT ON COLUMN library.tv_review.data" in sql
        assert "@fraiseql:jsonb expand=true" in sql
        assert "Denormalized Review data" in sql


class TestSQLTypeMapping:
    """Test SQL type to GraphQL type mapping"""

    def test_maps_sql_types_to_graphql(self):
        """Test: SQL types correctly mapped to GraphQL types"""
        entity = EntityDefinition(
            name="Product",
            schema="catalog",
            fields={
                "name": FieldDefinition(name="name", type_name="text"),
                "quantity": FieldDefinition(name="quantity", type_name="integer"),
                "price": FieldDefinition(name="price", type_name="decimal"),
                "active": FieldDefinition(name="active", type_name="boolean"),
            },
            actions=[],
            table_views=TableViewConfig(
                include_relations=[],
                extra_filter_columns=[
                    ExtraFilterColumn(name="quantity", type="INTEGER", index_type="btree"),
                    ExtraFilterColumn(name="price", type="NUMERIC", index_type="btree"),
                    ExtraFilterColumn(name="active", type="BOOLEAN", index_type="btree"),
                ],
            ),
        )

        annotator = TableViewAnnotator(entity)
        sql = annotator.generate_annotations()

        assert "type=Int" in sql  # INTEGER → Int
        assert "type=Float" in sql  # NUMERIC → Float
        assert "type=Boolean" in sql  # BOOLEAN → Boolean
