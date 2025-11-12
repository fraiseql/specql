"""
Integration tests for cascade audit query functions
"""



class TestCascadeAuditQueries:
    """Integration tests for cascade-aware audit query functions"""

    def test_cascade_audit_query_functions(self, test_db):
        """Test cascade-aware audit query functions"""

        # Setup: Create audit table with cascade data
        setup_sql = """
            CREATE SCHEMA IF NOT EXISTS blog;
            CREATE SCHEMA IF NOT EXISTS app;

            CREATE TABLE app.audit_post (
                audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                entity_id UUID NOT NULL,
                tenant_id UUID NOT NULL,
                operation_type TEXT,
                new_values JSONB,
                cascade_data JSONB,
                cascade_entities TEXT[],
                cascade_source TEXT,
                changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            -- Insert test audit data
            INSERT INTO app.audit_post (entity_id, tenant_id, operation_type, new_values, cascade_data, cascade_entities, cascade_source)
            VALUES
                ('11111111-1111-1111-1111-111111111111'::uuid, 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'::uuid, 'INSERT', '{"title": "Post 1"}',
                 '{"updated": [{"__typename": "Post", "id": "11111111-1111-1111-1111-111111111111", "operation": "CREATED"},
                               {"__typename": "User", "id": "22222222-2222-2222-2222-222222222222", "operation": "UPDATED"}]}',
                 ARRAY['Post', 'User'], 'create_post'),

                ('33333333-3333-3333-3333-333333333333'::uuid, 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'::uuid, 'INSERT', '{"title": "Post 2"}',
                 '{"updated": [{"__typename": "Post", "id": "33333333-3333-3333-3333-333333333333", "operation": "CREATED"}]}',
                 ARRAY['Post'], 'create_post'),

                ('44444444-4444-4444-4444-444444444444'::uuid, 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'::uuid, 'UPDATE', '{"title": "Updated Post"}',
                 '{"updated": [{"__typename": "Comment", "id": "55555555-5555-5555-5555-555555555555", "operation": "UPDATED"}]}',
                 ARRAY['Comment'], 'update_post');

            -- Create cascade-aware query functions
            CREATE OR REPLACE FUNCTION app.get_post_audit_history(
                p_entity_id UUID,
                p_tenant_id UUID,
                p_limit INTEGER DEFAULT 100,
                p_offset INTEGER DEFAULT 0
            )
            RETURNS TABLE (
                audit_id UUID,
                operation_type TEXT,
                changed_by UUID,
                changed_at TIMESTAMP WITH TIME ZONE,
                old_values JSONB,
                new_values JSONB,
                change_reason TEXT
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    a.audit_id,
                    a.operation_type,
                    NULL::UUID,
                    a.changed_at,
                    NULL::JSONB,
                    a.new_values,
                    'Entity modified'::TEXT
                FROM app.audit_post a
                WHERE a.entity_id = p_entity_id
                  AND a.tenant_id = p_tenant_id
                ORDER BY a.changed_at DESC
                LIMIT p_limit OFFSET p_offset;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION app.get_post_audit_history_with_cascade(
                p_entity_id UUID,
                p_tenant_id UUID,
                p_limit INTEGER DEFAULT 100,
                p_offset INTEGER DEFAULT 0,
                p_affected_entity TEXT DEFAULT NULL
            )
            RETURNS TABLE (
                audit_id UUID,
                operation_type TEXT,
                changed_by UUID,
                changed_at TIMESTAMP WITH TIME ZONE,
                old_values JSONB,
                new_values JSONB,
                change_reason TEXT,
                cascade_data JSONB,
                cascade_entities TEXT[],
                cascade_source TEXT,
                affected_entity_count INTEGER
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    a.audit_id,
                    a.operation_type,
                    NULL::UUID,
                    a.changed_at,
                    NULL::JSONB,
                    a.new_values,
                    'Entity modified'::TEXT,
                    a.cascade_data,
                    a.cascade_entities,
                    a.cascade_source,
                    COALESCE(array_length(a.cascade_entities, 1), 0)
                FROM app.audit_post a
                WHERE a.entity_id = p_entity_id
                  AND a.tenant_id = p_tenant_id
                  AND (
                      p_affected_entity IS NULL
                      OR p_affected_entity = ANY(a.cascade_entities)
                  )
                ORDER BY a.changed_at DESC
                LIMIT p_limit OFFSET p_offset;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION app.get_mutations_affecting_entity(
                p_entity_type TEXT,
                p_tenant_id UUID,
                p_limit INTEGER DEFAULT 100
            )
            RETURNS TABLE (
                audit_id UUID,
                primary_entity_id UUID,
                mutation_name TEXT,
                changed_at TIMESTAMP WITH TIME ZONE,
                cascade_data JSONB
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    a.audit_id,
                    a.entity_id,
                    a.cascade_source,
                    a.changed_at,
                    a.cascade_data
                FROM app.audit_post a
                WHERE a.tenant_id = p_tenant_id
                  AND p_entity_type = ANY(a.cascade_entities)
                ORDER BY a.changed_at DESC
                LIMIT p_limit;
            END;
            $$ LANGUAGE plpgsql;
        """

        test_db.execute(setup_sql)

        tenant_uuid = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

        # Test standard audit history (backward compatible)
        standard_result = test_db.execute(f"""
            SELECT * FROM app.get_post_audit_history(
                '11111111-1111-1111-1111-111111111111'::uuid,
                '{tenant_uuid}'::uuid
            )
        """).fetchall()

        assert len(standard_result) == 1
        # Standard query doesn't include cascade (backward compatible)
        assert len(standard_result[0]) == 7  # 7 columns without cascade

        # Test cascade-aware audit history
        cascade_result = test_db.execute(f"""
            SELECT * FROM app.get_post_audit_history_with_cascade(
                '11111111-1111-1111-1111-111111111111'::uuid,
                '{tenant_uuid}'::uuid
            )
        """).fetchall()

        assert len(cascade_result) == 1
        audit_id, operation_type, changed_by, changed_at, old_values, new_values, change_reason, cascade_data, cascade_entities, cascade_source, affected_entity_count = cascade_result[0]

        assert cascade_data is not None
        assert 'updated' in cascade_data
        assert len(cascade_data['updated']) == 2
        assert cascade_entities == ['Post', 'User']
        assert cascade_source == 'create_post'
        assert affected_entity_count == 2

        # Test filtering by affected entity
        user_affecting_result = test_db.execute(f"""
            SELECT * FROM app.get_post_audit_history_with_cascade(
                '11111111-1111-1111-1111-111111111111'::uuid,
                '{tenant_uuid}'::uuid,
                100, 0, 'User'
            )
        """).fetchall()

        assert len(user_affecting_result) == 1

        # Test filtering by non-matching entity
        comment_affecting_result = test_db.execute(f"""
            SELECT * FROM app.get_post_audit_history_with_cascade(
                '11111111-1111-1111-1111-111111111111'::uuid,
                '{tenant_uuid}'::uuid,
                100, 0, 'Comment'
            )
        """).fetchall()

        assert len(comment_affecting_result) == 0

        # Test mutations affecting entity function
        user_mutations = test_db.execute(f"""
            SELECT * FROM app.get_mutations_affecting_entity(
                'User',
                '{tenant_uuid}'::uuid
            )
        """).fetchall()

        assert len(user_mutations) == 1
        audit_id, primary_entity_id, mutation_name, changed_at, cascade_data = user_mutations[0]
        assert str(primary_entity_id) == '11111111-1111-1111-1111-111111111111'
        assert mutation_name == 'create_post'

        # Test mutations affecting Comment
        comment_mutations = test_db.execute(f"""
            SELECT * FROM app.get_mutations_affecting_entity(
                'Comment',
                '{tenant_uuid}'::uuid
            )
        """).fetchall()

        assert len(comment_mutations) == 1
        audit_id, primary_entity_id, mutation_name, changed_at, cascade_data = comment_mutations[0]
        assert str(primary_entity_id) == '44444444-4444-4444-4444-444444444444'
        assert mutation_name == 'update_post'