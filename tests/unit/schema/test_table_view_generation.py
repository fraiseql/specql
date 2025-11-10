import pytest

from src.core.ast_models import (
    EntityDefinition,
    ExtraFilterColumn,
    FieldDefinition,
    IncludeRelation,
    TableViewConfig,
    TableViewMode,
)
from src.generators.schema.table_view_dependency import TableViewDependencyResolver
from src.generators.schema.table_view_generator import TableViewGenerator


class TestTableViewGeneration:
    """Test tv_ table generation."""

    def test_basic_tv_generation(self):
        """Test basic tv_ table DDL generation."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(name="author", type_name="ref(User)"),
            },
        )

        print(f"Entity fields: {list(entity.fields.keys())}")  # Debug
        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()
        print(f"Generated SQL: {sql}")  # Debug

        assert "CREATE TABLE library.tv_review" in sql
        assert "pk_review INTEGER PRIMARY KEY" in sql
        assert "id UUID NOT NULL UNIQUE" in sql
        assert "tenant_id UUID NOT NULL" in sql
        assert "fk_user INTEGER" in sql
        assert "user_id UUID" in sql
        assert "data JSONB NOT NULL" in sql

    def test_indexes_generated(self):
        """Test indexes are generated correctly."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={"author": FieldDefinition(name="author", type_name="ref(User)")},
            table_views=TableViewConfig(
                extra_filter_columns=[ExtraFilterColumn.from_string("rating")]
            ),
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "idx_tv_review_tenant" in sql
        assert "idx_tv_review_user_id" in sql
        assert "idx_tv_review_rating" in sql
        assert "idx_tv_review_data" in sql
        assert "USING GIN(data)" in sql

    def test_hierarchical_entity(self):
        """Test hierarchical entity gets path column."""
        entity = EntityDefinition(
            name="Location",
            schema="management",
            fields={"parent": FieldDefinition(name="parent", type_name="ref(Location)")},
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "path LTREE NOT NULL" in sql
        assert "idx_tv_location_path" in sql
        assert "USING GIST(path)" in sql

    def test_no_generation_when_disabled(self):
        """Test no generation when table_views mode is DISABLE."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={"author": FieldDefinition(name="author", type_name="ref(User)")},
            table_views=TableViewConfig(mode=TableViewMode.DISABLE),
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert sql == ""

    def test_generation_when_forced(self):
        """Test generation when table_views mode is FORCE."""
        entity = EntityDefinition(
            name="Simple",
            schema="test",
            fields={},  # No foreign keys
            table_views=TableViewConfig(mode=TableViewMode.FORCE),
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "CREATE TABLE test.tv_simple" in sql

    def test_extra_filter_column_with_explicit_type(self):
        """Test extra filter column with explicit type."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "dummy": FieldDefinition(
                    name="dummy", type_name="ref(Dummy)"
                )  # Add FK to trigger generation
            },
            table_views=TableViewConfig(
                extra_filter_columns=[ExtraFilterColumn(name="rating", type="INTEGER")]
            ),
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "rating INTEGER" in sql

    def test_extra_filter_column_with_source(self):
        """Test extra filter column with source field."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "dummy": FieldDefinition(
                    name="dummy", type_name="ref(Dummy)"
                ),  # Add FK to trigger generation
            },
            table_views=TableViewConfig(
                extra_filter_columns=[
                    ExtraFilterColumn(name="stars", source="rating", type="INTEGER")
                ]
            ),
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "stars INTEGER" in sql

    def test_extra_filter_column_gin_trgm_index(self):
        """Test GIN trigram index for text search."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "dummy": FieldDefinition(
                    name="dummy", type_name="ref(Dummy)"
                )  # Add FK to trigger generation
            },
            table_views=TableViewConfig(
                extra_filter_columns=[ExtraFilterColumn(name="title", index_type="gin_trgm")]
            ),
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "USING GIN(title gin_trgm_ops)" in sql

    def test_extra_filter_column_gist_index(self):
        """Test GIST index for extra filter column."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "dummy": FieldDefinition(
                    name="dummy", type_name="ref(Dummy)"
                )  # Add FK to trigger generation
            },
            table_views=TableViewConfig(
                extra_filter_columns=[ExtraFilterColumn(name="location", index_type="gist")]
            ),
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "USING GIST(location)" in sql

    def test_multiple_foreign_keys(self):
        """Test entity with multiple foreign keys."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "author": FieldDefinition(name="author", type_name="ref(User)"),
                "book": FieldDefinition(name="book", type_name="ref(Book)"),
                "publisher": FieldDefinition(name="publisher", type_name="ref(Publisher)"),
            },
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        # Should have FK columns for all references
        assert "fk_user INTEGER" in sql
        assert "fk_book INTEGER" in sql
        assert "fk_publisher INTEGER" in sql

        # Should have UUID columns for all references
        assert "user_id UUID" in sql
        assert "book_id UUID" in sql
        assert "publisher_id UUID" in sql

        # Should have indexes for all UUID columns
        assert "idx_tv_review_user_id" in sql
        assert "idx_tv_review_book_id" in sql
        assert "idx_tv_review_publisher_id" in sql

    def test_refresh_function_generated(self):
        """Test refresh function is generated."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={"author": FieldDefinition(name="author", type_name="ref(User)")},
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        assert "CREATE OR REPLACE FUNCTION library.refresh_tv_review" in sql
        assert "p_pk_review INTEGER DEFAULT NULL" in sql
        assert "DELETE FROM library.tv_review" in sql
        assert "INSERT INTO library.tv_review" in sql

    def test_refresh_function_joins_tv_tables(self):
        """Test refresh function JOINs to tv_ tables (not tb_!)."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={"author": FieldDefinition(name="author", type_name="ref(User)")},
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        # Should JOIN to tv_user, not tb_user!
        assert "LEFT JOIN library.tv_user tv_user" in sql
        assert "tv_user.data" in sql
        assert "tb_user" not in sql  # Should NOT join to tb_!

    def test_refresh_function_jsonb_composition(self):
        """Test refresh function composes JSONB from tv_ tables."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(name="author", type_name="ref(User)"),
            },
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        # Should include scalar fields from base table
        assert "'rating', base.rating" in sql
        # Should include related data from tv_ table
        assert "'author', tv_user.data" in sql

    def test_explicit_field_selection(self):
        """Test explicit field selection from relations."""
        entity = EntityDefinition(
            name="Review",
            schema="library",
            fields={
                "rating": FieldDefinition(name="rating", type_name="integer"),
                "author": FieldDefinition(name="author", type_name="ref(User)"),
            },
            table_views=TableViewConfig(
                include_relations=[IncludeRelation(entity_name="author", fields=["name", "email"])]
            ),
        )

        generator = TableViewGenerator(entity, {})
        sql = generator.generate_schema()

        # Should extract only specified fields
        assert "tv_user.data->'name'" in sql or "tv_user.data->>'name'" in sql
        assert "tv_user.data->'email'" in sql or "tv_user.data->>'email'" in sql


class TestTableViewDependencyResolution:
    """Test tv_ dependency resolution and ordering."""

    def test_build_dependency_graph(self):
        """Test dependency graph construction from entity references."""
        entities = [
            EntityDefinition(name="User", schema="crm", fields={}),
            EntityDefinition(
                name="Post",
                schema="blog",
                fields={"author": FieldDefinition(name="author", type_name="ref(User)")},
            ),
            EntityDefinition(
                name="Comment",
                schema="blog",
                fields={
                    "post": FieldDefinition(name="post", type_name="ref(Post)"),
                    "author": FieldDefinition(name="author", type_name="ref(User)"),
                },
            ),
        ]

        resolver = TableViewDependencyResolver(entities)

        expected_graph = {"User": {"Post", "Comment"}, "Post": {"Comment"}, "Comment": set()}

        assert resolver.dependency_graph == expected_graph

    def test_get_generation_order_simple(self):
        """Test topological sort for simple dependency chain."""
        entities = [
            EntityDefinition(name="User", schema="crm", fields={}),
            EntityDefinition(
                name="Post",
                schema="blog",
                fields={"author": FieldDefinition(name="author", type_name="ref(User)")},
            ),
        ]

        resolver = TableViewDependencyResolver(entities)
        order = resolver.get_generation_order()

        # User should come before Post
        user_idx = order.index("User")
        post_idx = order.index("Post")
        assert user_idx < post_idx

    def test_get_generation_order_complex(self):
        """Test topological sort for complex dependency graph."""
        entities = [
            EntityDefinition(name="User", schema="crm", fields={}),
            EntityDefinition(name="Category", schema="blog", fields={}),
            EntityDefinition(
                name="Post",
                schema="blog",
                fields={
                    "author": FieldDefinition(name="author", type_name="ref(User)"),
                    "category": FieldDefinition(name="category", type_name="ref(Category)"),
                },
            ),
            EntityDefinition(
                name="Comment",
                schema="blog",
                fields={
                    "post": FieldDefinition(name="post", type_name="ref(Post)"),
                    "author": FieldDefinition(name="author", type_name="ref(User)"),
                },
            ),
        ]

        resolver = TableViewDependencyResolver(entities)
        order = resolver.get_generation_order()

        # Check that dependencies come before dependents
        user_idx = order.index("User")
        category_idx = order.index("Category")
        post_idx = order.index("Post")
        comment_idx = order.index("Comment")

        assert user_idx < post_idx
        assert user_idx < comment_idx
        assert category_idx < post_idx
        assert post_idx < comment_idx

    def test_get_refresh_order_for_entity(self):
        """Test finding entities that depend on a given entity."""
        entities = [
            EntityDefinition(name="User", schema="crm", fields={}),
            EntityDefinition(
                name="Post",
                schema="blog",
                fields={"author": FieldDefinition(name="author", type_name="ref(User)")},
            ),
            EntityDefinition(
                name="Comment",
                schema="blog",
                fields={
                    "post": FieldDefinition(name="post", type_name="ref(Post)"),
                    "author": FieldDefinition(name="author", type_name="ref(User)"),
                },
            ),
        ]

        resolver = TableViewDependencyResolver(entities)

        # When User changes, Post and Comment should be refreshed
        dependents = resolver.get_refresh_order_for_entity("User")
        assert set(dependents) == {"Post", "Comment"}

        # When Post changes, only Comment should be refreshed
        dependents = resolver.get_refresh_order_for_entity("Post")
        assert dependents == ["Comment"]

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        entities = [
            EntityDefinition(
                name="A",
                schema="test",
                fields={"ref_b": FieldDefinition(name="ref_b", type_name="ref(B)")},
            ),
            EntityDefinition(
                name="B",
                schema="test",
                fields={"ref_a": FieldDefinition(name="ref_a", type_name="ref(A)")},
            ),
        ]

        resolver = TableViewDependencyResolver(entities)

        with pytest.raises(ValueError, match="Circular dependency detected"):
            resolver.get_generation_order()

    def test_self_reference_not_circular(self):
        """Test that self-referencing entities don't create circular dependencies."""
        entities = [
            EntityDefinition(
                name="Category",
                schema="blog",
                fields={"parent": FieldDefinition(name="parent", type_name="ref(Category)")},
            )
        ]

        resolver = TableViewDependencyResolver(entities)

        # Should not detect circular dependency for self-reference
        order = resolver.get_generation_order()
        assert order == ["Category"]
