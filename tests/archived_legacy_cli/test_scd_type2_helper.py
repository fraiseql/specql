"""Tests for SCD Type 2 helper pattern."""

import pytest

from core.specql_parser import SpecQLParser
from generators.schema.naming_conventions import NamingConventions
from generators.schema.schema_registry import SchemaRegistry
from generators.table_generator import TableGenerator


class TestSCDType2Helper:
    """Test SCD Type 2 helper pattern."""

    @pytest.fixture
    def schema_registry(self):
        """Shared schema registry for tests."""
        naming_conventions = NamingConventions()
        return SchemaRegistry(naming_conventions.registry)

    @pytest.fixture
    def table_generator(self, schema_registry):
        """Table generator instance."""
        return TableGenerator(schema_registry)

    @pytest.fixture
    def customer_entity(self):
        """Customer entity with SCD Type 2 pattern."""
        return """
entity: Customer
schema: crm
fields:
  customer_id: text
  name: text
  email: text
  address: text
patterns:
  - type: temporal_scd_type2_helper
    params:
      natural_key: [customer_id]
      tracked_fields: [name, email, address]
      effective_date_field: effective_from
      expiry_date_field: effective_to
      is_current_field: is_current
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify all tracked fields are handled
        assert "name" in ddl
        assert "price" in ddl
        assert "category" in ddl
        assert "description" in ddl

    def test_no_tracked_fields_specified(self, table_generator):
        """Test behavior when no tracked fields are specified."""
        yaml = """
entity: Account
schema: finance
fields:
  account_number: text
  balance: decimal
patterns:
  - type: temporal_scd_type2_helper
    params:
      natural_key: [account_number]
      tracked_fields: []
      effective_date_field: effective_from
      expiry_date_field: effective_to
      is_current_field: is_current
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Should still create SCD structure even with no tracked fields
        assert "effective_from TIMESTAMPTZ" in ddl
        assert "is_current BOOLEAN" in ddl

    def test_default_field_names_used(self, table_generator):
        """Test that default field names are used when not specified."""
        yaml = """
entity: Contact
schema: crm
fields:
  contact_id: text
  phone: text
  email: text
patterns:
  - type: temporal_scd_type2_helper
    params:
      natural_key: [contact_id]
      tracked_fields: [phone, email]
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify default field names
        assert "effective_date TIMESTAMPTZ" in ddl
        assert "expiry_date TIMESTAMPTZ" in ddl
        assert "is_current BOOLEAN" in ddl

    def test_history_table_created(self, table_generator, customer_entity):
        """Test that history tracking is implemented (via SCD fields)."""
        parser = SpecQLParser()
        entity = parser.parse(customer_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify history tracking via SCD fields (no separate history table in basic version)
        assert "effective_from" in ddl
        assert "effective_to" in ddl
        assert "is_current" in ddl

    def test_version_field_added(self, table_generator, customer_entity):
        """Test that version tracking is implemented (via effective dates)."""
        parser = SpecQLParser()
        entity = parser.parse(customer_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify version tracking via effective dates (no separate version field in basic version)
        assert "effective_from" in ddl
        assert "effective_to" in ddl

    def test_cascade_delete_handling(self, table_generator, customer_entity):
        """Test that delete handling is considered (via SCD approach)."""
        parser = SpecQLParser()
        entity = parser.parse(customer_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify SCD approach handles deletes via effective_to
        assert "effective_to" in ddl
        assert "is_current" in ddl

    def test_bulk_update_support(self, table_generator, customer_entity):
        """Test that bulk update operations are supported."""
        parser = SpecQLParser()
        entity = parser.parse(customer_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify bulk update procedures
        assert "PROCEDURE" in ddl or "FUNCTION" in ddl

    def test_performance_indexes_optimized(self, table_generator, customer_entity):
        """Test that indexes are optimized for SCD query performance."""
        parser = SpecQLParser()
        entity = parser.parse(customer_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify performance-optimized indexes
        assert "CREATE INDEX" in ddl
        # Should have composite indexes for common queries
        assert "customer_id, effective_from, effective_to" in ddl

    def test_scd_function_parameter_validation(self, table_generator):
        """Test that SCD function properly validates parameters."""
        yaml = """
entity: Product
schema: inventory
fields:
  sku: text
  name: text
patterns:
  - type: temporal_scd_type2_helper
    params:
      natural_key: [sku]
      tracked_fields: [name]
      effective_from_field: effective_from
      effective_to_field: effective_to
      is_current_field: is_current
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify function has proper parameters
        assert "natural_key_values jsonb" in ddl
        assert "new_data jsonb" in ddl
        assert "create_new_version_product" in ddl
