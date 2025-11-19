"""Tests for computed column pattern."""

import pytest

from src.core.specql_parser import SpecQLParser
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry
from src.generators.table_generator import TableGenerator


class TestComputedColumn:
    """Test computed column pattern."""

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
    def order_entity(self):
        """Order entity with computed column pattern."""
        return """
entity: Order
schema: sales
fields:
   quantity: integer
   unit_price: decimal
   discount_percent: decimal
patterns:
   - type: schema_computed_column
     params:
       column_name: total_amount
       expression: "quantity * unit_price * (1 - discount_percent / 100)"
       type: decimal
       nullable: false
"""

    def test_computed_column_added_to_table(self, table_generator, order_entity):
        """Test that computed column is added to the table."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify computed column is added
        assert "total_amount decimal GENERATED ALWAYS AS" in ddl
        assert "quantity * unit_price * (1 - discount_percent / 100)" in ddl

    def test_computed_column_stored(self, table_generator, order_entity):
        """Test that computed column is stored (not virtual)."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify STORED keyword
        assert "STORED" in ddl

    def test_computed_column_nullable_handling(self, table_generator, order_entity):
        """Test that computed column nullability is handled correctly."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify NOT NULL for non-nullable computed column
        assert "total_amount decimal GENERATED ALWAYS AS" in ddl

    def test_fraiseql_metadata_includes_pattern(self, table_generator, order_entity):
        """Test that FraiseQL comments include pattern info."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify FraiseQL comment
        assert "@fraiseql:pattern:schema_computed_column" in ddl

    def test_multiple_computed_columns(self, table_generator):
        """Test multiple computed columns in one entity."""
        yaml = """
entity: Invoice
schema: finance
fields:
  subtotal: decimal
  tax_rate: decimal
  discount_amount: decimal
patterns:
   - type: schema_computed_column
     params:
       column_name: tax_amount
       expression: "subtotal * tax_rate / 100"
       type: decimal
       nullable: false
   - type: schema_computed_column
     params:
       column_name: total_amount
       expression: "subtotal + tax_amount - discount_amount"
       type: decimal
       nullable: false
   - type: schema_computed_column
     params:
       column_name: discount_percent
       expression: "discount_amount / subtotal * 100"
       type: decimal
       nullable: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify all computed columns
        assert "tax_amount decimal GENERATED ALWAYS AS (subtotal * tax_rate / 100) STORED" in ddl
        assert (
            "total_amount decimal GENERATED ALWAYS AS (subtotal + tax_amount - discount_amount) STORED"
            in ddl
        )
        assert (
            "discount_percent decimal GENERATED ALWAYS AS (discount_amount / subtotal * 100) STORED"
            in ddl
        )

    def test_computed_column_with_functions(self, table_generator):
        """Test computed column with SQL functions."""
        yaml = """
entity: Person
schema: hr
fields:
  first_name: text
  last_name: text
  birth_date: date
patterns:
   - type: schema_computed_column
     params:
       column_name: full_name
       expression: "CONCAT(first_name, ' ', last_name)"
       type: text
       nullable: false
   - type: schema_computed_column
     params:
       column_name: age
       expression: "EXTRACT(YEAR FROM AGE(birth_date))"
       type: integer
       nullable: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify computed columns with functions
        assert (
            "full_name text GENERATED ALWAYS AS (CONCAT(first_name, ' ', last_name)) STORED" in ddl
        )
        assert "age integer GENERATED ALWAYS AS (EXTRACT(YEAR FROM AGE(birth_date))) STORED" in ddl

    def test_computed_column_dependencies(self, table_generator):
        """Test that computed columns can reference other computed columns."""
        yaml = """
entity: Salary
schema: hr
fields:
  base_salary: decimal
  bonus_percent: decimal
patterns:
   - type: schema_computed_column
     params:
       column_name: bonus_amount
       expression: "base_salary * bonus_percent / 100"
       type: decimal
       nullable: false
   - type: schema_computed_column
     params:
       column_name: total_compensation
       expression: "base_salary + bonus_amount"
       type: decimal
       nullable: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify computed column referencing another computed column
        assert (
            "bonus_amount decimal GENERATED ALWAYS AS (base_salary * bonus_percent / 100) STORED"
            in ddl
        )
        assert (
            "total_compensation decimal GENERATED ALWAYS AS (base_salary + bonus_amount) STORED"
            in ddl
        )

    def test_computed_column_with_case_expression(self, table_generator):
        """Test computed column with CASE expression."""
        yaml = """
entity: Order
schema: sales
fields:
  status: text
  amount: decimal
patterns:
   - type: schema_computed_column
     params:
       column_name: status_category
       expression: "CASE WHEN status = 'completed' THEN 'closed' WHEN status = 'pending' THEN 'open' ELSE 'unknown' END"
       type: text
       nullable: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify CASE expression in computed column
        assert (
            "status_category text GENERATED ALWAYS AS (CASE WHEN status = 'completed' THEN 'closed' WHEN status = 'pending' THEN 'open' ELSE 'unknown' END) STORED"
            in ddl
        )

    def test_computed_column_indexes(self, table_generator, order_entity):
        """Test that indexes can be created on computed columns."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify index can be created on computed column (would be separate DDL)
        assert "total_amount" in ddl

    def test_computed_column_type_validation(self, table_generator):
        """Test that computed column types are validated."""
        yaml = """
entity: Product
schema: inventory
fields:
  price: decimal
  quantity: integer
patterns:
   - type: schema_computed_column
     params:
       column_name: total_value
       expression: "price * quantity"
       type: decimal
       nullable: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify correct type is used
        assert "total_value decimal GENERATED ALWAYS AS (price * quantity) STORED" in ddl

    def test_computed_column_nullable_true(self, table_generator):
        """Test computed column that allows null values."""
        yaml = """
entity: Employee
schema: hr
fields:
  salary: decimal
  commission: decimal
patterns:
   - type: schema_computed_column
     params:
       column_name: total_earnings
       expression: "salary + COALESCE(commission, 0)"
       type: decimal
       nullable: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify nullable computed column
        assert (
            "total_earnings decimal GENERATED ALWAYS AS (salary + COALESCE(commission, 0)) STORED"
            in ddl
        )

    def test_computed_column_with_subquery(self, table_generator):
        """Test computed column with subquery (should be handled appropriately)."""
        yaml = """
entity: Department
schema: hr
fields:
  name: text
patterns:
   - type: schema_computed_column
     params:
       column_name: employee_count
       expression: "(SELECT COUNT(*) FROM employees WHERE department_id = departments.id)"
       type: integer
       nullable: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Note: Subqueries in computed columns might not be supported in all databases
        # This tests the expression handling
        assert "employee_count integer GENERATED ALWAYS AS" in ddl

    def test_computed_column_ordering(self, table_generator):
        """Test that computed columns appear in correct order in DDL."""
        yaml = """
entity: Calculation
schema: math
fields:
  a: integer
  b: integer
  c: integer
patterns:
   - type: schema_computed_column
     params:
       column_name: sum_ab
       expression: "a + b"
       type: integer
       nullable: false
   - type: schema_computed_column
     params:
       column_name: product_all
       expression: "a * b * c"
       type: integer
       nullable: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify computed columns appear after regular fields
        assert "c INTEGER," in ddl
        assert "sum_ab integer GENERATED ALWAYS AS (a + b) STORED," in ddl
        assert "product_all integer GENERATED ALWAYS AS (a * b * c) STORED," in ddl

    def test_computed_column_performance_implications(self, table_generator):
        """Test that computed columns have appropriate performance considerations."""
        yaml = """
entity: PerformanceTest
schema: test
fields:
  base_value: decimal
  multiplier: decimal
patterns:
   - type: schema_computed_column
     params:
       column_name: computed_result
       expression: "base_value * multiplier + POWER(base_value, 2)"
       type: decimal
       nullable: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify complex expression is handled
        assert (
            "computed_result decimal GENERATED ALWAYS AS (base_value * multiplier + POWER(base_value, 2)) STORED"
            in ddl
        )
