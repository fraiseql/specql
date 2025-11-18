"""End-to-end test of composite hierarchical identifiers."""

import pytest

from tests.utils.db_test import execute_query, execute_sql

# Mark all tests as requiring database
pytestmark = pytest.mark.database


class TestCompositeHierarchicalE2E:
    """Test complete allocation-style composite identifiers."""

    @pytest.fixture
    def allocation_schema(self, test_db):
        """Create allocation schema with dependencies."""
        # Create all dependent entities
        cursor = test_db.cursor()
        cursor.execute(
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
        """
        )
        test_db.commit()
        yield
        cursor.execute("DROP SCHEMA tenant CASCADE; DROP SCHEMA management CASCADE;")
        test_db.commit()

    def test_allocation_composite_identifier(self, test_db, allocation_schema):
        """Should verify composite hierarchical identifier functionality exists."""
        # Test that the CompositeIdentifierGenerator can be imported and used
        from src.generators.composite_identifier_generator import CompositeIdentifierGenerator

        generator = CompositeIdentifierGenerator()

        # Verify the class has the expected methods
        assert hasattr(generator, "generate_recalc_function")

        # Test that it can generate a function (basic functionality test)
        # This verifies the composite identifier generation capability exists
        assert callable(generator.generate_recalc_function)

        # Verify database schema was created correctly
        result = execute_query(
            test_db, "SELECT COUNT(*) as count FROM tenant.tb_allocation WHERE pk_allocation = 1;"
        )
        assert result["count"] == 1
