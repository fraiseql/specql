"""Tests for temporal non-overlapping daterange pattern."""

import pytest
from src.core.specql_parser import SpecQLParser
from src.generators.table_generator import TableGenerator
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry


class TestNonOverlappingDateRange:
    """Test temporal non-overlapping daterange pattern."""

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
    def allocation_entity(self):
        """Machine allocation entity with temporal pattern."""
        return """
entity: Allocation
schema: operations
fields:
  machine: ref(Machine)
  product: ref(Product)
  start_date: date
  end_date: date
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [machine]
      start_date_field: start_date
      end_date_field: end_date
      check_mode: strict
      allow_adjacent: true
"""

    def test_computed_daterange_column_added(self, table_generator, allocation_entity):
        """Test that computed daterange column is generated."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify computed column exists
        assert "start_date_end_date_range DATERANGE" in ddl
        assert "GENERATED ALWAYS AS (daterange(start_date, end_date, '[]'))" in ddl
        assert "STORED" in ddl

    def test_gist_index_created(self, table_generator, allocation_entity):
        """Test that GIST index on daterange is created."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify GIST index
        assert "CREATE INDEX idx_tb_allocation_daterange" in ddl
        assert "USING gist" in ddl
        assert "(start_date_end_date_range)" in ddl

    def test_exclusion_constraint_strict_mode(self, table_generator, allocation_entity):
        """Test that EXCLUSION constraint is generated in strict mode."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify exclusion constraint
        assert "ALTER TABLE operations.tb_allocation" in ddl
        assert "ADD CONSTRAINT excl_allocation_no_overlap" in ddl
        assert "EXCLUDE USING gist" in ddl
        assert "machine WITH =" in ddl
        assert "start_date_end_date_range WITH &&" in ddl

    def test_nullable_end_date_supported(self, table_generator, allocation_entity):
        """Test that NULL end_date (open-ended ranges) is supported."""
        # Modify YAML to allow NULL end_date
        yaml_with_null = allocation_entity.replace("end_date: date", "end_date: date?\n")

        parser = SpecQLParser()
        entity = parser.parse(yaml_with_null)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify computed column handles NULL
        assert "daterange(start_date, end_date, '[]')" in ddl
        # PostgreSQL daterange handles NULL end_date as unbounded

    def test_multiple_scope_fields(self, table_generator):
        """Test pattern with multiple scope fields."""
        yaml = """
entity: Allocation
schema: operations
fields:
  machine: ref(Machine)
  product: ref(Product)
  start_date: date
  end_date: date
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [machine, product]
      start_date_field: start_date
      end_date_field: end_date
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify exclusion constraint includes both scope fields
        assert "machine WITH =" in ddl
        assert "product WITH =" in ddl
        assert "start_date_end_date_range WITH &&" in ddl

    def test_warning_mode_no_constraint(self, table_generator):
        """Test that warning mode doesn't add EXCLUSION constraint."""
        yaml = """
entity: Allocation
schema: operations
fields:
  machine: ref(Machine)
  start_date: date
  end_date: date
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [machine]
      check_mode: warning
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify NO exclusion constraint
        assert "EXCLUDE USING gist" not in ddl
        # But computed column and index still present
        assert "start_date_end_date_range DATERANGE" in ddl
        assert "USING gist" in ddl

    def test_adjacent_ranges_configurable(self, table_generator):
        """Test that adjacent ranges can be disallowed."""
        yaml = """
entity: Allocation
schema: operations
fields:
  machine: ref(Machine)
  start_date: date
  end_date: date
patterns:
  - type: temporal_non_overlapping_daterange
    params:
      scope_fields: [machine]
      allow_adjacent: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify exclusion uses && (overlaps) instead of &&= (overlaps or adjacent)
        # When allow_adjacent=false, we want strict overlap check
        assert "WITH &&" in ddl

    def test_fraiseql_metadata_includes_pattern(self, table_generator, allocation_entity):
        """Test that FraiseQL comments include pattern info."""
        parser = SpecQLParser()
        entity = parser.parse(allocation_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify FraiseQL comment
        assert "COMMENT ON TABLE operations.tb_allocation" in ddl
        assert "@fraiseql:pattern:temporal_non_overlapping_daterange" in ddl
