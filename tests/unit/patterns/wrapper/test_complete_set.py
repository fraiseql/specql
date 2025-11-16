"""Tests for complete set wrapper pattern."""

from src.patterns.wrapper.complete_set import generate_complete_set_wrapper


class TestCompleteSetWrapper:
    """Test complete set wrapper pattern."""

    def test_generate_complete_set_wrapper_basic(self):
        """Test basic complete set wrapper generation."""
        config = {
            "name": "v_count_allocations_by_location_optimized",
            "schema": "tenant",
            "materialized_view": "mv_count_allocations_by_location",
            "base_table": "tb_location",
            "key_field": "pk_location",
            "default_values": {"n_direct_allocations": 0, "n_total_allocations": 0},
            "ensure_zero_count_entities": True,
        }

        sql = generate_complete_set_wrapper(config)

        assert (
            "CREATE OR REPLACE VIEW tenant.v_count_allocations_by_location_optimized AS"
            in sql
        )
        assert "SELECT * FROM tenant.mv_count_allocations_by_location" in sql
        assert "UNION ALL" in sql
        assert "SELECT" in sql
        assert "base.pk_location" in sql
        assert "0 AS n_direct_allocations" in sql
        assert "0 AS n_total_allocations" in sql
        assert "FROM tenant.tb_location base" in sql
        assert "WHERE NOT EXISTS" in sql
        assert "AND base.deleted_at IS NULL" in sql

    def test_generate_complete_set_wrapper_no_defaults(self):
        """Test wrapper with no default values specified."""
        config = {
            "name": "v_simple_wrapper",
            "schema": "tenant",
            "materialized_view": "mv_simple",
            "base_table": "tb_entity",
            "key_field": "pk_entity",
            "default_values": {},
            "ensure_zero_count_entities": True,
        }

        sql = generate_complete_set_wrapper(config)

        # Should still generate the wrapper structure but with no default fields
        assert "CREATE OR REPLACE VIEW tenant.v_simple_wrapper AS" in sql
        assert "SELECT * FROM tenant.mv_simple" in sql
        assert "UNION ALL" in sql
        assert "base.pk_entity" in sql
        assert "FROM tenant.tb_entity base" in sql

    def test_generate_complete_set_wrapper_disabled_zero_count(self):
        """Test wrapper with zero count inclusion disabled."""
        config = {
            "name": "v_no_zero_counts",
            "schema": "tenant",
            "materialized_view": "mv_data",
            "base_table": "tb_entity",
            "key_field": "pk_entity",
            "default_values": {"count": 0},
            "ensure_zero_count_entities": False,
        }

        sql = generate_complete_set_wrapper(config)

        # Should only include materialized view results, no UNION ALL
        assert "CREATE OR REPLACE VIEW tenant.v_no_zero_counts AS" in sql
        assert "SELECT * FROM tenant.mv_data" in sql
        assert "UNION ALL" not in sql
        assert "NOT EXISTS" not in sql

    def test_generate_complete_set_wrapper_different_schemas(self):
        """Test wrapper with different schemas for MV and base table."""
        config = {
            "name": "v_cross_schema_wrapper",
            "schema": "tenant",
            "materialized_view": "app.mv_summary",
            "base_table": "public.tb_entity",
            "key_field": "id",
            "default_values": {"total": 0},
            "ensure_zero_count_entities": True,
        }

        sql = generate_complete_set_wrapper(config)

        assert "SELECT * FROM app.mv_summary" in sql
        assert "FROM public.tb_entity base" in sql
        assert "WHERE NOT EXISTS" in sql
        assert "FROM app.mv_summary mv" in sql
