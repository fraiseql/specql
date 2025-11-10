"""Test tenant prefix stripping for composite identifiers."""

import pytest

from tests.utils.db_test import execute_query, execute_sql


class TestStripTenantPrefix:
    """Test stripping tenant prefix from referenced identifiers."""

    @pytest.fixture
    def composite_setup(self, db):
        """Create entities for composite testing."""
        execute_sql(
            db,
            """
            CREATE SCHEMA tenant;
            CREATE SCHEMA management;

            CREATE TABLE management.tb_tenant (
                pk_tenant INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                identifier TEXT NOT NULL
            );

            CREATE TABLE tenant.tb_machine (
                pk_machine INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                identifier TEXT NOT NULL
            );

            CREATE TABLE tenant.tb_location (
                pk_location INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                identifier TEXT NOT NULL
            );

            INSERT INTO management.tb_tenant (pk_tenant, id, identifier)
            VALUES (1, gen_random_uuid(), 'acme-corp');

            INSERT INTO tenant.tb_machine (pk_machine, tenant_id, identifier)
            VALUES (1, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), 'acme-corp|hp.laser.s123');

            INSERT INTO tenant.tb_location (pk_location, tenant_id, identifier)
            VALUES (1, (SELECT id FROM management.tb_tenant WHERE pk_tenant = 1), 'acme-corp|warehouse.floor1');
        """,
        )
        yield
        execute_sql(db, "DROP SCHEMA tenant CASCADE; DROP SCHEMA management CASCADE;")

    def test_strip_tenant_prefix_from_machine(self, db, composite_setup):
        """Should strip tenant prefix from machine identifier."""
        result = execute_query(
            db,
            """
            SELECT
                m.identifier AS full_identifier,
                REGEXP_REPLACE(
                    m.identifier,
                    '^' || (SELECT identifier FROM management.tb_tenant WHERE id = m.tenant_id) || '\\|',
                    ''
                ) AS stripped_identifier
            FROM tenant.tb_machine m
            WHERE pk_machine = 1;
        """,
        )

        assert result["full_identifier"] == "acme-corp|hp.laser.s123"
        assert result["stripped_identifier"] == "hp.laser.s123"  # Prefix stripped!

    def test_composite_identifier_without_duplicate_tenant(self, db, composite_setup):
        """Composite identifier should not have duplicate tenant prefix."""
        # Simulate allocation identifier construction
        result = execute_query(
            db,
            """
            SELECT
                (SELECT identifier FROM management.tb_tenant WHERE pk_tenant = 1)
                    || '|2025-Q1∘'
                    || REGEXP_REPLACE(m.identifier, '^' || (SELECT identifier FROM management.tb_tenant WHERE id = m.tenant_id) || '\\|', '')
                    || '∘'
                    || REGEXP_REPLACE(l.identifier, '^' || (SELECT identifier FROM management.tb_tenant WHERE id = l.tenant_id) || '\\|', '')
                AS composite_identifier
            FROM tenant.tb_machine m, tenant.tb_location l
            WHERE m.pk_machine = 1 AND l.pk_location = 1;
        """,
        )

        composite = result["composite_identifier"]

        # Should be: acme-corp|2025-Q1∘hp.laser.s123∘warehouse.floor1
        assert composite == "acme-corp|2025-Q1∘hp.laser.s123∘warehouse.floor1"

        # Should NOT be: acme-corp|2025-Q1∘acme-corp|hp.laser.s123∘acme-corp|warehouse.floor1
        assert "acme-corp|acme-corp" not in composite
        assert composite.count("acme-corp") == 1  # Only once at start!
