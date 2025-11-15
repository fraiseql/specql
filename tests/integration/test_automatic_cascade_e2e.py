"""
Integration tests for automatic GraphQL cascade generation

Tests cascade helper functions and data structure correctness
"""

from uuid import uuid4

import pytest


class TestCascadeDataStructure:
    """Test cascade data structure and helper functions"""

    @pytest.fixture(autouse=True)
    def setup_cascade_helpers(self, test_db):
        """Set up cascade helper functions for all tests"""
        # Drop functions first to ensure clean state
        test_db.execute("""
            DROP FUNCTION IF EXISTS app.cascade_entity(TEXT, UUID, TEXT, TEXT, TEXT);
            DROP FUNCTION IF EXISTS app.cascade_deleted(TEXT, UUID);
        """)
        test_db.commit()

        cascade_sql = """
-- Helper: Build cascade entity with full data from table view
CREATE OR REPLACE FUNCTION app.cascade_entity(
    p_typename TEXT,
    p_id UUID,
    p_operation TEXT,
    p_schema TEXT,
    p_view_name TEXT
) RETURNS JSONB AS $$
DECLARE
    v_entity_data JSONB;
BEGIN
    -- Try to fetch from table view first
    BEGIN
        EXECUTE format('SELECT data FROM %I.%I WHERE id = $1', p_schema, p_view_name)
        INTO v_entity_data
        USING p_id;
    EXCEPTION WHEN undefined_table THEN
        -- Fallback: try table directly
        BEGIN
            EXECUTE format(
                'SELECT row_to_json(t.*)::jsonb FROM %I.tb_%I t WHERE id = $1',
                p_schema,
                lower(p_typename)
            )
            INTO v_entity_data
            USING p_id;
        EXCEPTION WHEN OTHERS THEN
            v_entity_data := NULL;
        END;
    END;

    -- Build cascade entity structure
    RETURN jsonb_build_object(
        '__typename', p_typename,
        'id', p_id,
        'operation', p_operation,
        'entity', COALESCE(v_entity_data, '{}'::jsonb)
    );
END;
$$ LANGUAGE plpgsql;

-- Helper: Build deleted entity (no data, just ID)
CREATE OR REPLACE FUNCTION app.cascade_deleted(
    p_typename TEXT,
    p_id UUID
) RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        '__typename', p_typename,
        'id', p_id,
        'operation', 'DELETED'
    );
END;
$$ LANGUAGE plpgsql;
"""
        test_db.execute(cascade_sql)
        test_db.commit()

    def test_cascade_data_structure_correctness(self, test_db):
        """
        Test that cascade data structure matches FraiseQL expectations
        """
        # Create test data
        post_id = uuid4()
        uuid4()

        # Test cascade_entity function
        cursor = test_db.execute("""
            SELECT app.cascade_entity(
                'Post',
                %s::uuid,
                'CREATED',
                'blog',
                'tv_post'
            ) as cascade_data
        """, [str(post_id)])

        result = cursor.fetchone()
        cascade = result[0]  # First column of the result
        assert cascade['__typename'] == 'Post'
        assert cascade['id'] == str(post_id)
        assert cascade['operation'] == 'CREATED'
        assert 'entity' in cascade

    def test_cascade_deleted_structure(self, test_db):
        """
        Test cascade_deleted returns correct structure for deletions
        """
        entity_id = uuid4()

        cursor = test_db.execute("""
            SELECT app.cascade_deleted('Post', %s::uuid) as cascade_data
        """, [str(entity_id)])

        result = cursor.fetchone()
        cascade = result[0]  # First column of the result
        assert cascade['__typename'] == 'Post'
        assert cascade['id'] == str(entity_id)
        assert cascade['operation'] == 'DELETED'
        assert 'entity' not in cascade  # Deleted entities don't include data

    def test_cascade_jsonb_structure(self, test_db):
        """
        Test building complete cascade JSONB structure
        """
        post_id = uuid4()
        user_id = uuid4()

        # Build cascade structure manually
        cursor = test_db.execute("""
            SELECT jsonb_build_object(
                'updated', jsonb_build_array(
                    app.cascade_entity('Post', %s::uuid, 'CREATED', 'blog', 'tv_post'),
                    app.cascade_entity('User', %s::uuid, 'UPDATED', 'blog', 'tv_user')
                ),
                'deleted', jsonb_build_array(
                    app.cascade_deleted('Comment', %s::uuid)
                ),
                'invalidations', '[]'::jsonb,
                'metadata', jsonb_build_object(
                    'timestamp', now(),
                    'affectedCount', 3
                )
            ) as cascade_structure
        """, [str(post_id), str(user_id), str(uuid4())])

        result = cursor.fetchone()
        cascade = result[0]  # First column of the result

        # Verify structure
        assert 'updated' in cascade
        assert 'deleted' in cascade
        assert 'invalidations' in cascade
        assert 'metadata' in cascade

        # Verify updated entities
        updated = cascade['updated']
        assert len(updated) == 2
        assert updated[0]['__typename'] == 'Post'
        assert updated[0]['operation'] == 'CREATED'
        assert updated[1]['__typename'] == 'User'
        assert updated[1]['operation'] == 'UPDATED'

        # Verify deleted entities
        deleted = cascade['deleted']
        assert len(deleted) == 1
        assert deleted[0]['__typename'] == 'Comment'
        assert deleted[0]['operation'] == 'DELETED'

        # Verify metadata
        metadata = cascade['metadata']
        assert 'timestamp' in metadata
        assert metadata['affectedCount'] == 3