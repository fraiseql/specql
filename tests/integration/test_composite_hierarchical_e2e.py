"""End-to-end test of composite hierarchical identifiers."""

import pytest
from tests.utils.db_test import execute_sql, execute_query

# Mark all tests as requiring database
pytestmark = pytest.mark.database


class TestCompositeHierarchicalE2E:
    """Test complete allocation-style composite identifiers."""

    @pytest.fixture
    def allocation_schema(self, test_db):
        """Create allocation schema with dependencies."""
        # Create all dependent entities
        execute_sql(
            test_db,
            """
            CREATE SCHEMA tenant;
            CREATE SCHEMA management;

            -- Tenant
            CREATE TABLE management.tb_tenant (
                pk_tenant INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                identifier TEXT NOT NULL
            );

            -- Machine (hierarchical)
            CREATE TABLE tenant.tb_machine (
                pk_machine INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                fk_parent_machine INTEGER REFERENCES tenant.tb_machine(pk_machine),
                name TEXT NOT NULL,
                identifier TEXT
            );

            -- Location (hierarchical)
            CREATE TABLE tenant.tb_location (
                pk_location INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                fk_parent_location INTEGER REFERENCES tenant.tb_location(pk_location),
                name TEXT NOT NULL,
                identifier TEXT
            );

            -- Allocation (composite)
            CREATE TABLE tenant.tb_allocation (
                pk_allocation INTEGER PRIMARY KEY,
                id UUID DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                allocation_daterange TEXT NOT NULL,
                fk_machine INTEGER REFERENCES tenant.tb_machine(pk_machine),
                fk_location INTEGER REFERENCES tenant.tb_location(pk_location),
                identifier TEXT,
                base_identifier TEXT,
                sequence_number INTEGER DEFAULT 1
            );

            -- Sample data
            INSERT INTO management.tb_tenant VALUES (1, gen_random_uuid(), 'acme-corp');

            -- Machine hierarchy
            INSERT INTO tenant.tb_machine VALUES
                (1, gen_random_uuid(), (SELECT id FROM management.tb_tenant), NULL, 'HP', 'acme-corp|hp'),
                (2, gen_random_uuid(), (SELECT id FROM management.tb_tenant), 1, 'LaserJet', 'acme-corp|hp.laserjet'),
                (3, gen_random_uuid(), (SELECT id FROM management.tb_tenant), 2, 'S123', 'acme-corp|hp.laserjet.s123');

            -- Location hierarchy
            INSERT INTO tenant.tb_location VALUES
                (1, gen_random_uuid(), (SELECT id FROM management.tb_tenant), NULL, 'Warehouse', 'acme-corp|warehouse'),
                (2, gen_random_uuid(), (SELECT id FROM management.tb_tenant), 1, 'Floor 1', 'acme-corp|warehouse.floor1');

            -- Allocation
            INSERT INTO tenant.tb_allocation (pk_allocation, tenant_id, allocation_daterange, fk_machine, fk_location)
            VALUES (1, (SELECT id FROM management.tb_tenant), '2025-Q1', 3, 2);
        """,
        )
        yield
        execute_sql(test_db, "DROP SCHEMA tenant CASCADE; DROP SCHEMA management CASCADE;")

    def test_allocation_composite_identifier(self, test_db, allocation_schema):
        """Should generate allocation identifier with composition separator."""
        # Generate recalculate function (from SpecQL)
        # ... generator creates this function ...

        # Execute recalculation
        execute_sql(test_db, "SELECT tenant.recalculate_allocation_identifier()")

        # Verify result
        result = execute_query(
            test_db,
            """
            SELECT identifier, base_identifier
            FROM tenant.tb_allocation
            WHERE pk_allocation = 1;
        """,
        )

        # Expected: acme-corp|2025-Q1∘hp.laserjet.s123∘warehouse.floor1
        identifier = result["identifier"]

        assert identifier.startswith("acme-corp|")  # Tenant prefix
        assert "∘" in identifier  # Composition separator
        assert identifier.count("acme-corp") == 1  # Only one tenant prefix!
        assert "hp.laserjet.s123" in identifier  # Machine hierarchy with dots
        assert "warehouse.floor1" in identifier  # Location hierarchy with dots
        assert identifier == "acme-corp|2025-Q1∘hp.laserjet.s123∘warehouse.floor1"
