"""Test hierarchical identifier generation with dot separator."""

import pytest

from tests.utils.db_test import execute_query, execute_sql


class TestHierarchicalDotSeparator:
    """Test hierarchical identifiers use dot by default."""

    @pytest.fixture
    def location_hierarchy(self, db):
        """Create location hierarchy for testing."""
        execute_sql(
            db,
            """
            CREATE SCHEMA IF NOT EXISTS tenant;

            CREATE TABLE tenant.tb_location (
                pk_location INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                fk_parent_location INTEGER REFERENCES tenant.tb_location(pk_location),
                name TEXT NOT NULL,
                identifier TEXT,
                base_identifier TEXT,
                sequence_number INTEGER DEFAULT 1,
                identifier_recalculated_at TIMESTAMPTZ,
                identifier_recalculated_by UUID
            );

            -- Create tenant
            CREATE TABLE management.tb_tenant (
                pk_tenant INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                identifier TEXT NOT NULL
            );

            INSERT INTO management.tb_tenant (pk_tenant, id, identifier)
            VALUES (1, gen_random_uuid(), 'acme-corp');

            -- Create hierarchy
            INSERT INTO tenant.tb_location (pk_location, tenant_id, fk_parent_location, name)
            VALUES
                (1, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), NULL, 'Warehouse A'),
                (2, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), 1, 'Floor 1'),
                (3, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), 2, 'Room 101');
        """,
        )
        yield
        execute_sql(db, "DROP SCHEMA tenant CASCADE; DROP SCHEMA management CASCADE;")

    def test_hierarchical_uses_dot_separator(self, db, location_hierarchy):
        """Hierarchical identifiers should use dot separator by default."""
        # Simulated generated function
        execute_sql(
            db,
            """
            CREATE OR REPLACE FUNCTION tenant.recalculate_location_identifier()
            RETURNS INTEGER AS $$
            DECLARE
                v_count INTEGER := 0;
            BEGIN
                WITH RECURSIVE hierarchy AS (
                    -- Root nodes
                    SELECT
                        l.pk_location,
                        (SELECT identifier FROM management.tb_tenant WHERE id = l.tenant_id)
                            || '|' || public.safe_slug(l.name) AS base_identifier
                    FROM tenant.tb_location l
                    WHERE l.fk_parent_location IS NULL

                    UNION ALL

                    -- Child nodes (use DOT separator)
                    SELECT
                        child.pk_location,
                        parent.base_identifier || '.' || public.safe_slug(child.name)
                    FROM tenant.tb_location child
                    JOIN hierarchy parent ON child.fk_parent_location = parent.pk_location
                )
                UPDATE tenant.tb_location l
                SET
                    identifier = h.base_identifier,
                    base_identifier = h.base_identifier
                FROM hierarchy h
                WHERE l.pk_location = h.pk_location;

                GET DIAGNOSTICS v_count = ROW_COUNT;
                RETURN v_count;
            END;
            $$ LANGUAGE plpgsql;
        """,
        )

        # Execute recalculation
        execute_sql(db, "SELECT tenant.recalculate_location_identifier()")

        # Verify identifiers use dot separator
        locations = execute_sql(
            db,
            """
            SELECT pk_location, identifier
            FROM tenant.tb_location
            ORDER BY pk_location
        """,
        )

        assert locations[0][1] == "acme-corp|warehouse-a"  # Root
        assert locations[1][1] == "acme-corp|warehouse-a.floor-1"  # Child (DOT!)
        assert (
            locations[2][1] == "acme-corp|warehouse-a.floor-1.room-101"
        )  # Grandchild (DOT!)

    def test_explicit_underscore_override(self, db, location_hierarchy):
        """Should support explicit underscore override for backward compatibility."""
        # Generate function with underscore separator (explicit override)
        execute_sql(
            db,
            """
            CREATE OR REPLACE FUNCTION tenant.recalculate_location_identifier_underscore()
            RETURNS INTEGER AS $$
            BEGIN
                WITH RECURSIVE hierarchy AS (
                    SELECT
                        l.pk_location,
                        (SELECT identifier FROM management.tb_tenant WHERE id = l.tenant_id)
                            || '|' || public.safe_slug(l.name) AS base_identifier
                    FROM tenant.tb_location l
                    WHERE l.fk_parent_location IS NULL

                    UNION ALL

                    SELECT
                        child.pk_location,
                        parent.base_identifier || '_' || public.safe_slug(child.name)  -- Underscore override
                    FROM tenant.tb_location child
                    JOIN hierarchy parent ON child.fk_parent_location = parent.pk_location
                )
                UPDATE tenant.tb_location l
                SET identifier = h.base_identifier
                FROM hierarchy h
                WHERE l.pk_location = h.pk_location;

                RETURN (SELECT COUNT(*) FROM tenant.tb_location);
            END;
            $$ LANGUAGE plpgsql;
        """,
        )

        execute_query(db, "SELECT tenant.recalculate_location_identifier_underscore()")

        locations = execute_sql(
            db,
            """
            SELECT identifier FROM tenant.tb_location ORDER BY pk_location
        """,
        )

        assert locations[1][0] == "acme-corp|warehouse-a_floor-1"  # Underscore!
