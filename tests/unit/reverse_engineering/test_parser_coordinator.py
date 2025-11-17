"""
Tests for ParserCoordinator - specialized parser coordination.
"""

import pytest
from src.reverse_engineering.parser_coordinator import ParserCoordinator, ParserResult


class TestParserCoordinator:
    """Test ParserCoordinator parser selection and execution"""

    @pytest.fixture
    def coordinator(self):
        return ParserCoordinator()

    def test_should_use_cte_parser_with_with_clause(self, coordinator):
        """Test CTE parser detection for WITH clause"""
        sql = "WITH active AS (SELECT * FROM tb_contact) SELECT * FROM active"

        # EXPECTED TO FAIL: ParserCoordinator not implemented
        assert coordinator.should_use_cte_parser(sql) is True

    def test_should_not_use_cte_parser_without_with(self, coordinator):
        """Test CTE parser not triggered without WITH"""
        sql = "SELECT * FROM tb_contact WHERE status = 'active'"

        assert coordinator.should_use_cte_parser(sql) is False

    def test_should_use_exception_parser_with_exception_block(self, coordinator):
        """Test exception parser detection"""
        sql = """
        BEGIN
            INSERT INTO tb_contact (email) VALUES ('test@example.com');
        EXCEPTION
            WHEN unique_violation THEN
                RAISE NOTICE 'Duplicate';
        END;
        """

        # EXPECTED TO FAIL
        assert coordinator.should_use_exception_parser(sql) is True

    def test_should_use_dynamic_sql_parser_with_execute(self, coordinator):
        """Test dynamic SQL parser detection"""
        sql = "EXECUTE 'SELECT * FROM ' || table_name"

        # EXPECTED TO FAIL
        assert coordinator.should_use_dynamic_sql_parser(sql) is True

    def test_should_use_cursor_parser_with_cursor(self, coordinator):
        """Test cursor parser detection"""
        sql = """
        DECLARE
            contact_cursor CURSOR FOR SELECT * FROM tb_contact;
        BEGIN
            OPEN contact_cursor;
        """

        # EXPECTED TO FAIL
        assert coordinator.should_use_cursor_parser(sql) is True

    def test_parse_with_cte_returns_result(self, coordinator):
        """Test CTE parser execution returns ParserResult"""
        sql = "WITH active AS (SELECT * FROM tb_contact WHERE active = true) SELECT * FROM active"

        # EXPECTED TO FAIL
        result = coordinator.parse_with_cte(sql)

        assert result is not None
        assert isinstance(result, ParserResult)
        assert result.success is True
        assert result.parser_used == "cte"
        assert result.confidence_boost > 0

    def test_parse_with_exception_returns_result(self, coordinator):
        """Test exception parser execution"""
        sql = """
        EXCEPTION
            WHEN unique_violation THEN
                RAISE NOTICE 'Duplicate';
        """

        # EXPECTED TO FAIL
        result = coordinator.parse_with_exception(sql)

        assert result is not None
        assert result.success is True
        assert result.parser_used == "exception"

    def test_parse_with_best_parsers_multiple_parsers(self, coordinator):
        """Test coordination returns multiple parser results"""
        sql = """
        WITH active AS (SELECT * FROM tb_contact WHERE active = true)
        SELECT
            COUNT(*) FILTER (WHERE status = 'qualified'),
            ROW_NUMBER() OVER (ORDER BY created_at)
        FROM active
        """

        # EXPECTED TO FAIL
        results = coordinator.parse_with_best_parsers(sql)

        # Should use CTE, aggregate, and window parsers
        assert len(results) >= 2
        parser_types = {r.parser_used for r in results}
        assert "cte" in parser_types
        assert "aggregate" in parser_types or "window" in parser_types

    def test_metrics_tracking_on_success(self, coordinator):
        """Test metrics are tracked on successful parse"""
        sql = "WITH active AS (SELECT * FROM tb_contact) SELECT * FROM active"

        # EXPECTED TO FAIL
        coordinator.parse_with_cte(sql)

        metrics = coordinator.get_metrics()
        assert metrics["cte"]["attempts"] == 1
        assert metrics["cte"]["successes"] == 1
        assert metrics["cte"]["failures"] == 0

    def test_metrics_tracking_on_failure(self, coordinator):
        """Test metrics are tracked on failed parse"""
        invalid_sql = "WITH incomplete syntax"

        # EXPECTED TO FAIL
        result = coordinator.parse_with_cte(invalid_sql)

        metrics = coordinator.get_metrics()
        assert metrics["cte"]["attempts"] == 1
        assert metrics["cte"]["failures"] == 1
        assert result is None  # Failed parse returns None

    def test_get_success_rates(self, coordinator):
        """Test success rate calculation"""
        # Simulate some parses
        coordinator.parse_with_cte("WITH a AS (SELECT 1) SELECT * FROM a")
        coordinator.parse_with_cte("WITH b AS (SELECT 2) SELECT * FROM b")
        coordinator.parse_with_cte("INVALID")  # This should fail

        # EXPECTED TO FAIL
        rates = coordinator.get_success_rates()

        assert "cte" in rates
        assert rates["cte"] == pytest.approx(0.666, abs=0.01)  # 2 successes / 3 attempts

    def test_reset_metrics(self, coordinator):
        """Test metrics can be reset"""
        coordinator.parse_with_cte("WITH a AS (SELECT 1) SELECT * FROM a")

        # EXPECTED TO FAIL
        coordinator.reset_metrics()

        metrics = coordinator.get_metrics()
        assert metrics["cte"]["attempts"] == 0
        assert metrics["cte"]["successes"] == 0

    def test_parser_result_includes_metadata(self, coordinator):
        """Test ParserResult includes useful metadata"""
        sql = """
        WITH RECURSIVE hierarchy AS (
            SELECT id, 0 as level FROM tb_unit WHERE parent_id IS NULL
            UNION ALL
            SELECT u.id, h.level + 1 FROM tb_unit u JOIN hierarchy h ON u.parent_id = h.id
        )
        SELECT * FROM hierarchy
        """

        # EXPECTED TO FAIL
        result = coordinator.parse_with_cte(sql)

        assert "is_recursive" in result.metadata
        assert result.metadata["is_recursive"] is True
        assert "cte_count" in result.metadata or "max_depth" in result.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
