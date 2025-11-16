"""Tests for materialized view refresh orchestration."""

from src.patterns.wrapper.mv_refresh import (
    generate_refresh_function,
    generate_refresh_trigger,
)


class TestMVRefreshOrchestration:
    """Test materialized view refresh orchestration."""

    def test_generate_refresh_function_basic(self):
        """Test basic refresh function generation."""
        config = {
            "mv_name": "mv_count_allocations_by_location",
            "schema": "tenant",
            "concurrent": True,
            "log_table": "app.mv_refresh_log",
        }

        sql = generate_refresh_function(config)

        assert (
            f"CREATE OR REPLACE FUNCTION {config['schema']}.refresh_{config['mv_name']}()"
            in sql
        )
        assert "REFRESH MATERIALIZED VIEW CONCURRENTLY" in sql
        assert f"{config['schema']}.{config['mv_name']}" in sql
        assert "INSERT INTO app.mv_refresh_log" in sql
        assert "LANGUAGE plpgsql" in sql

    def test_generate_refresh_function_non_concurrent(self):
        """Test refresh function without CONCURRENTLY."""
        config = {
            "mv_name": "mv_expensive_calculation",
            "schema": "tenant",
            "concurrent": False,
        }

        sql = generate_refresh_function(config)

        assert "REFRESH MATERIALIZED VIEW" in sql
        assert "CONCURRENTLY" not in sql

    def test_generate_refresh_function_no_logging(self):
        """Test refresh function without logging."""
        config = {"mv_name": "mv_simple", "schema": "tenant", "concurrent": True}

        sql = generate_refresh_function(config)

        assert "INSERT INTO" not in sql
        assert "mv_refresh_log" not in sql

    def test_generate_refresh_trigger_basic(self):
        """Test basic refresh trigger generation."""
        config = {
            "mv_name": "mv_count_allocations_by_location",
            "schema": "tenant",
            "base_table": "tb_location",
            "base_schema": "tenant",
            "trigger_name": "trg_refresh_mv_count_allocations",
        }

        sql = generate_refresh_trigger(config)

        assert f"CREATE TRIGGER {config['trigger_name']}" in sql
        assert "AFTER INSERT OR UPDATE OR DELETE" in sql
        assert f"ON {config['base_schema']}.{config['base_table']}" in sql
        assert "FOR EACH STATEMENT" in sql
        assert f"invalidate_mv_cache('{config['mv_name']}')" in sql

    def test_generate_refresh_trigger_cross_schema(self):
        """Test refresh trigger with cross-schema references."""
        config = {
            "mv_name": "mv_cross_schema",
            "schema": "tenant",
            "base_table": "tb_entity",
            "base_schema": "public",
            "trigger_name": "trg_refresh_cross_schema",
        }

        sql = generate_refresh_trigger(config)

        assert f"ON {config['base_schema']}.{config['base_table']}" in sql
        assert f"'{config['mv_name']}'" in sql

    def test_generate_refresh_orchestration_complete(self):
        """Test complete refresh orchestration generation."""
        from src.patterns.wrapper.mv_refresh import generate_refresh_orchestration

        config = {
            "mv_name": "mv_test",
            "schema": "tenant",
            "base_table": "tb_test",
            "concurrent": True,
            "log_table": "app.mv_refresh_log",
            "trigger_name": "trg_refresh_mv_test",
        }

        sql = generate_refresh_orchestration(config)

        # Should contain both function and trigger
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "CREATE TRIGGER" in sql
        assert "REFRESH MATERIALIZED VIEW CONCURRENTLY" in sql
        assert "AFTER INSERT OR UPDATE OR DELETE" in sql
