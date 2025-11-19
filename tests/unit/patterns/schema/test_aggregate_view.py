"""Tests for aggregate view pattern."""

import pytest

from src.core.specql_parser import SpecQLParser
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry
from src.generators.table_generator import TableGenerator


class TestAggregateView:
    """Test aggregate view pattern."""

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
        """Order entity with aggregate view pattern."""
        return """
entity: Order
schema: sales
fields:
  customer_id: ref(Customer)
  order_date: date
  total_amount: decimal
patterns:
  - type: aggregate_view
    params:
      group_by: [customer_id]
      aggregates:
        - field: total_amount
          function: sum
          alias: total_spent
        - field: order_date
          function: count
          alias: order_count
      refresh_mode: auto
      indexes:
        - name: customer_id
          fields: [customer_id]
          using: btree
"""

    def test_aggregate_view_created(self, table_generator, order_entity):
        """Test that aggregate view is generated."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify aggregate view creation
        assert "CREATE MATERIALIZED VIEW sales.mv_order_agg AS" in ddl
        assert "SELECT" in ddl
        assert "customer_id" in ddl
        assert "SUM(total_amount) AS total_spent" in ddl
        assert "COUNT(order_date) AS order_count" in ddl
        assert "FROM sales.tb_order" in ddl
        assert "GROUP BY customer_id" in ddl

    def test_group_by_columns_included(self, table_generator, order_entity):
        """Test that group by columns are included in view."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify customer_id in view
        assert "customer_id" in ddl
        assert "GROUP BY customer_id" in ddl

    def test_aggregate_functions_applied(self, table_generator, order_entity):
        """Test that aggregate functions are correctly applied."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify SUM and COUNT functions
        assert "SUM(total_amount) AS total_spent" in ddl
        assert "COUNT(order_date) AS order_count" in ddl

    def test_view_indexes_created(self, table_generator, order_entity):
        """Test that indexes are created on aggregate view."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify indexes on view
        assert "CREATE INDEX idx_mv_order_agg_customer_id" in ddl
        assert "ON sales.mv_order_agg" in ddl
        assert "customer_id" in ddl

    def test_refresh_triggers_generated(self, table_generator, order_entity):
        """Test that refresh triggers are generated for auto mode."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify triggers for auto refresh
        assert "CREATE OR REPLACE FUNCTION sales.refresh_mv_order_agg()" in ddl
        assert "REFRESH MATERIALIZED VIEW sales.mv_order_agg;" in ddl
        assert "CREATE TRIGGER tr_refresh_mv_order_agg" in ddl
        assert "AFTER INSERT OR UPDATE OR DELETE ON sales.tb_order" in ddl

    def test_manual_refresh_mode_no_triggers(self, table_generator):
        """Test that manual refresh mode doesn't create triggers."""
        yaml = """
entity: Order
schema: sales
fields:
  customer_id: ref(Customer)
  total_amount: decimal
patterns:
  - type: aggregate_view
    params:
      group_by: [customer_id]
      aggregates:
        - field: total_amount
          function: sum
      refresh_mode: manual
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # No triggers in manual mode
        assert "CREATE TRIGGER" not in ddl
        assert "CREATE OR REPLACE FUNCTION refresh_mv_order_agg()" not in ddl

    def test_fraiseql_metadata_includes_pattern(self, table_generator, order_entity):
        """Test that FraiseQL comments include pattern info."""
        parser = SpecQLParser()
        entity = parser.parse(order_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify FraiseQL comment in table comment
        assert "@fraiseql:pattern:aggregate_view" in ddl

    def test_multiple_aggregates_same_field(self, table_generator):
        """Test multiple aggregate functions on the same field."""
        yaml = """
entity: Product
schema: inventory
fields:
  category_id: ref(Category)
  price: decimal
  stock_quantity: integer
patterns:
  - type: aggregate_view
    params:
      group_by: [category_id]
      aggregates:
        - field: price
          function: sum
          alias: total_value
        - field: price
          function: avg
          alias: avg_price
        - field: price
          function: min
          alias: min_price
        - field: price
          function: max
          alias: max_price
        - field: stock_quantity
          function: sum
          alias: total_stock
      refresh_mode: manual
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify all aggregate functions
        assert "SUM(price) AS total_value" in ddl
        assert "AVG(price) AS avg_price" in ddl
        assert "MIN(price) AS min_price" in ddl
        assert "MAX(price) AS max_price" in ddl
        assert "SUM(stock_quantity) AS total_stock" in ddl

    def test_multiple_group_by_columns(self, table_generator):
        """Test aggregate view with multiple group by columns."""
        yaml = """
entity: Sale
schema: sales
fields:
  store_id: ref(Store)
  product_id: ref(Product)
  region_id: ref(Region)
  amount: decimal
patterns:
  - type: aggregate_view
    params:
      group_by: [store_id, region_id]
      aggregates:
        - field: amount
          function: sum
          alias: total_sales
        - field: product_id
          function: count
          alias: products_sold
      refresh_mode: manual
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify multiple group by columns
        assert "store_id, region_id" in ddl
        assert "GROUP BY store_id, region_id" in ddl
        assert "SUM(amount) AS total_sales" in ddl
        assert "COUNT(product_id) AS products_sold" in ddl

    def test_incremental_refresh_mode(self, table_generator):
        """Test incremental refresh mode (placeholder for future implementation)."""
        yaml = """
entity: Transaction
schema: finance
fields:
  account_id: ref(Account)
  amount: decimal
patterns:
  - type: aggregate_view
    params:
      group_by: [account_id]
      aggregates:
        - field: amount
          function: sum
      refresh_mode: incremental
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # For now, incremental mode behaves like manual (no triggers)
        assert "CREATE TRIGGER" not in ddl
        assert "CREATE MATERIALIZED VIEW finance.mv_transaction_agg" in ddl

    def test_view_name_generation(self, table_generator):
        """Test that view names are generated correctly."""
        yaml = """
entity: UserActivity
schema: analytics
fields:
  user_id: ref(User)
  event_type: text
  duration: integer
patterns:
  - type: aggregate_view
    params:
      group_by: [user_id, event_type]
      aggregates:
        - field: duration
          function: avg
      refresh_mode: manual
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify view name generation
        assert "CREATE MATERIALIZED VIEW analytics.mv_useractivity_agg" in ddl

    def test_no_aggregates_specified(self, table_generator):
        """Test behavior when no aggregates are specified (should still work with count)."""
        yaml = """
entity: Visit
schema: web
fields:
  page_id: ref(Page)
  visitor_id: ref(Visitor)
patterns:
  - type: aggregate_view
    params:
      group_by: [page_id]
      aggregates: []
      refresh_mode: manual
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Should still create view with just group by columns
        assert "CREATE MATERIALIZED VIEW web.mv_visit_agg" in ddl
        assert "page_id" in ddl
        assert "GROUP BY page_id" in ddl

    def test_case_insensitive_function_names(self, table_generator):
        """Test that function names are handled case-insensitively."""
        yaml = """
entity: Metric
schema: monitoring
fields:
  service_id: ref(Service)
  value: decimal
patterns:
  - type: aggregate_view
    params:
      group_by: [service_id]
      aggregates:
        - field: value
          function: SUM
          alias: total
        - field: value
          function: avg
          alias: average
        - field: service_id
          function: Count
          alias: count
      refresh_mode: manual
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify functions are uppercased in SQL
        assert "SUM(value) AS total" in ddl
        assert "AVG(value) AS average" in ddl
        assert "COUNT(service_id) AS count" in ddl

    def test_default_alias_generation(self, table_generator):
        """Test default alias generation when not specified."""
        yaml = """
entity: LogEntry
schema: audit
fields:
  user_id: ref(User)
  action: text
  timestamp: timestamp
patterns:
  - type: aggregate_view
    params:
      group_by: [user_id]
      aggregates:
        - field: action
          function: count
        - field: timestamp
          function: max
      refresh_mode: manual
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify default aliases
        assert "COUNT(action) AS count_action" in ddl
        assert "MAX(timestamp) AS max_timestamp" in ddl
