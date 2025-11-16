"""Integration tests for cascade helper functions with real PostgreSQL"""

import pytest
from uuid import uuid4


class TestCascadeHelpersE2E:
    """Test cascade helper functions with real PostgreSQL database"""

    @pytest.fixture(autouse=True)
    def setup_cascade_helpers(self, test_db):
        """Set up cascade helper functions for all tests"""
        # Use the real generated helpers from AppSchemaGenerator
        from src.generators.app_schema_generator import AppSchemaGenerator

        # Drop functions first to ensure clean state
        test_db.execute("""
            DROP FUNCTION IF EXISTS app.cascade_entity(TEXT, UUID, TEXT, TEXT, TEXT);
            DROP FUNCTION IF EXISTS app.cascade_deleted(TEXT, UUID);
        """)
        test_db.commit()

        # Generate and install the real cascade helpers
        generator = AppSchemaGenerator()
        cascade_sql = generator._generate_cascade_helpers()
        test_db.execute(cascade_sql)
        test_db.commit()

    def test_cascade_entity_with_table_view(self, test_db, isolated_schema):
        """Test cascade_entity() with table view"""
        schema_name = isolated_schema

        # Setup: Create table with view
        cursor = test_db.cursor()
        cursor.execute(f"""
            CREATE TABLE {schema_name}.tb_post (
                pk_post SERIAL PRIMARY KEY,
                id UUID NOT NULL UNIQUE,
                title TEXT,
                content TEXT
            );
            CREATE VIEW {schema_name}.tv_post AS
            SELECT
                id,
                title,
                content,
                jsonb_build_object(
                    'id', id,
                    'title', title,
                    'content', content
                ) as data
            FROM {schema_name}.tb_post;
        """)
        test_db.commit()

        # Insert test data
        post_id = uuid4()
        cursor.execute(
            f"INSERT INTO {schema_name}.tb_post (id, title, content) VALUES (%s, %s, %s)",
            [str(post_id), "Test Post", "Hello World"],
        )
        test_db.commit()

        # Test cascade_entity function
        cursor.execute(
            f"""
            SELECT app.cascade_entity(
                'Post',
                %s::uuid,
                'CREATED',
                '{schema_name}',
                'tv_post'
            ) as cascade_data
        """,
            [str(post_id)],
        )
        result = cursor.fetchone()

        cascade = result[0]  # First column of the result

        # Verify structure
        assert cascade["__typename"] == "Post"
        assert cascade["id"] == str(post_id)
        assert cascade["operation"] == "CREATED"
        assert "entity" in cascade
        assert cascade["entity"]["title"] == "Test Post"
        assert cascade["entity"]["content"] == "Hello World"

    def test_cascade_entity_fallback_to_table(self, test_db, isolated_schema):
        """Test cascade_entity() fallback to table when view doesn't exist"""
        schema_name = isolated_schema

        # Setup: Create table (no view)
        cursor = test_db.cursor()
        cursor.execute(f"""
            CREATE TABLE {schema_name}.tb_user (
                pk_user SERIAL PRIMARY KEY,
                id UUID NOT NULL UNIQUE,
                name TEXT,
                email TEXT
            );
        """)
        test_db.commit()

        # Insert test data
        user_id = uuid4()
        cursor.execute(
            f"INSERT INTO {schema_name}.tb_user (id, name, email) VALUES (%s, %s, %s)",
            [str(user_id), "Test User", "test@example.com"],
        )
        test_db.commit()

        # First, test direct table query to make sure data exists
        cursor.execute(
            f"SELECT * FROM {schema_name}.tb_user WHERE id = %s", [str(user_id)]
        )
        direct_result = cursor.fetchone()
        print(f"DEBUG: direct table query result = {direct_result}")

        # Test the raw SQL that the function should execute
        raw_sql = (
            f"SELECT row_to_json(t.*)::jsonb FROM {schema_name}.tb_user t WHERE id = %s"
        )
        print(f"DEBUG: raw SQL = {raw_sql}")
        cursor.execute(raw_sql, [str(user_id)])
        raw_result = cursor.fetchone()
        print(f"DEBUG: raw result = {raw_result}")

        # Check if the function exists
        cursor.execute(
            "SELECT proname FROM pg_proc WHERE proname = 'cascade_entity' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'app')"
        )
        func_exists = cursor.fetchone()
        print(f"DEBUG: function exists = {func_exists}")

        # Test cascade_entity with non-existent view (should fallback to table)
        cursor.execute(
            f"""
            SELECT app.cascade_entity(
                'User',
                %s::uuid,
                'UPDATED',
                '{schema_name}',
                'tv_user_nonexistent'
            ) as cascade_data
        """,
            [str(user_id)],
        )
        result = cursor.fetchone()

        cascade = result[0]

        # Debug: print actual result
        print(f"DEBUG: cascade = {cascade}")

        # Verify structure
        assert cascade["__typename"] == "User"
        assert cascade["id"] == str(user_id)
        assert cascade["operation"] == "UPDATED"
        assert "entity" in cascade
        # Table fallback should include all columns
        assert cascade["entity"]["name"] == "Test User"
        assert cascade["entity"]["email"] == "test@example.com"

    def test_cascade_deleted_structure(self, test_db):
        """Test cascade_deleted() returns correct structure"""
        user_id = uuid4()

        # Test cascade_deleted function
        cursor = test_db.cursor()
        cursor.execute(
            """
            SELECT app.cascade_deleted('User', %s::uuid) as cascade_data
        """,
            [str(user_id)],
        )
        result = cursor.fetchone()

        cascade = result[0]

        # Verify structure
        assert cascade["__typename"] == "User"
        assert cascade["id"] == str(user_id)
        assert cascade["operation"] == "DELETED"
        # Should not have entity data for deletions
        assert "entity" not in cascade

    def test_cascade_entity_with_missing_entity(self, test_db):
        """Test cascade_entity() handles missing entities gracefully"""
        missing_id = uuid4()

        # Test with non-existent entity
        cursor = test_db.cursor()
        cursor.execute(
            """
            SELECT app.cascade_entity(
                'Post',
                %s::uuid,
                'CREATED',
                'public',
                'tv_post'
            ) as cascade_data
        """,
            [str(missing_id)],
        )
        result = cursor.fetchone()

        cascade = result[0]

        # Should still return structure but with empty entity
        assert cascade["__typename"] == "Post"
        assert cascade["id"] == str(missing_id)
        assert cascade["operation"] == "CREATED"
        assert cascade["entity"] == {}  # Empty object for missing entity
