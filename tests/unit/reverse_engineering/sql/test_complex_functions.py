"""
Tests for complex SQL function reverse engineering

These tests target capabilities that currently have low confidence (< 20%)
and need enhancement to reach 80%+ confidence.
"""

from src.reverse_engineering.algorithmic_parser import AlgorithmicParser


class TestComplexSQLFunctions:
    """Test complex SQL function parsing capabilities"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = AlgorithmicParser(use_heuristics=True, use_ai=False)

    def test_nested_cte_parsing(self):
        """Test parsing functions with nested CTEs"""
        sql = """
        CREATE FUNCTION calculate_hierarchy() RETURNS TABLE AS $$
        WITH RECURSIVE parent_chain AS (
            SELECT * FROM units WHERE parent_id IS NULL
            UNION ALL
            WITH child_units AS (
                SELECT * FROM units WHERE level > 1
            )
            SELECT u.* FROM units u
            JOIN parent_chain pc ON u.parent_id = pc.id
        )
        SELECT * FROM parent_chain;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.85
        assert "cte" in [step.type for step in result.steps]
        assert "recursive_hierarchy" in result.metadata.get("detected_patterns", [])
        # Note: Warnings are expected due to fallback parsing for complex SQL
        # EXPECTED: PASS (confidence improved from 11% to 85%+ with pattern detection)

    def test_exception_handler_parsing(self):
        """Test parsing EXCEPTION blocks"""
        sql = """
        CREATE FUNCTION safe_update() RETURNS void AS $$
        BEGIN
            UPDATE contacts SET status = 'active';
        EXCEPTION
            WHEN unique_violation THEN
                RAISE NOTICE 'Duplicate key';
            WHEN OTHERS THEN
                RAISE EXCEPTION 'Unknown error';
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        assert any(step.type == "try_except" for step in result.steps)
        # EXPECTED: PASS (EXCEPTION blocks now parsed with WHEN clauses support)

    def test_dynamic_sql_parsing(self):
        """Test parsing functions with dynamic SQL (EXECUTE)"""
        sql = """
        CREATE FUNCTION dynamic_query(table_name text, column_name text) RETURNS void AS $$
        DECLARE
            query_text text;
        BEGIN
            query_text := 'UPDATE ' || table_name || ' SET ' || column_name || ' = $1';
            EXECUTE query_text USING 'new_value';
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.75
        assert any(step.type == "execute" for step in result.steps)
        assert any("dynamic" in str(step).lower() for step in result.steps)
        # EXPECTED: PASS (EXECUTE now recognized with pattern detection)

    def test_complex_control_flow_parsing(self):
        """Test parsing nested loops and complex control flow"""
        sql = """
        CREATE FUNCTION process_batch() RETURNS void AS $$
        DECLARE
            contact_record record;
            batch_size int := 100;
        BEGIN
            FOR contact_record IN SELECT * FROM contacts WHERE status = 'pending' LOOP
                IF contact_record.priority > 5 THEN
                    -- High priority processing
                    UPDATE contacts SET status = 'processing' WHERE id = contact_record.id;
                    PERFORM process_high_priority(contact_record.id);
                ELSIF contact_record.priority > 2 THEN
                    -- Medium priority
                    UPDATE contacts SET status = 'queued' WHERE id = contact_record.id;
                ELSE
                    -- Low priority - skip for now
                    CONTINUE;
                END IF;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        assert any(step.type == "for_loop" for step in result.steps)
        assert any(step.type == "if_elseif" for step in result.steps)
        assert any(step.type == "continue" for step in result.steps)
        # EXPECTED: PASS (complex control flow now parsed with advanced FOR loops)

    def test_aggregate_with_filter_parsing(self):
        """Test parsing aggregate functions with FILTER clauses"""
        sql = """
        CREATE FUNCTION calculate_stats() RETURNS TABLE AS $$
        SELECT
            company_id,
            COUNT(*) as total_contacts,
            COUNT(*) FILTER (WHERE status = 'active') as active_contacts,
            AVG(created_at) FILTER (WHERE priority > 3) as avg_priority_date
        FROM contacts
        GROUP BY company_id;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        assert any("FILTER" in str(step) for step in result.steps)
        assert any(step.type == "aggregate" for step in result.steps)
        # EXPECTED: PASS (FILTER WHERE clauses now supported in aggregates)

    def test_window_function_parsing(self):
        """Test parsing window functions with complex frames"""
        sql = """
        CREATE FUNCTION rank_contacts() RETURNS TABLE AS $$
        SELECT
            id,
            company_id,
            created_at,
            ROW_NUMBER() OVER (
                PARTITION BY company_id
                ORDER BY created_at DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) as contact_rank,
            LAG(created_at, 1) OVER (
                PARTITION BY company_id
                ORDER BY created_at
            ) as prev_contact_date
        FROM contacts;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        assert any(step.type == "window_function" for step in result.steps)
        assert any("ROW_NUMBER" in str(step) for step in result.steps)
        # EXPECTED: PASS (window functions now parsed with PARTITION BY, ORDER BY patterns)

    def test_cursor_operations_parsing(self):
        """Test parsing cursor operations and FETCH statements"""
        sql = """
        CREATE FUNCTION process_with_cursor() RETURNS void AS $$
        DECLARE
            contact_cursor CURSOR FOR SELECT * FROM contacts WHERE status = 'pending';
            contact_record record;
        BEGIN
            OPEN contact_cursor;
            LOOP
                FETCH contact_cursor INTO contact_record;
                EXIT WHEN NOT FOUND;

                -- Process contact
                UPDATE contacts SET processed_at = NOW() WHERE id = contact_record.id;
            END LOOP;
            CLOSE contact_cursor;
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.75
        # Check for cursor declaration
        assert any(step.type == "cursor_declare" for step in result.steps)
        # Check for cursor operations
        assert any(
            step.type in ["cursor_open", "cursor_fetch", "cursor_close"] for step in result.steps
        )
        # Check for fetch specifically
        assert any(step.type == "cursor_fetch" for step in result.steps)
        # EXPECTED: PASS (cursor operations now properly parsed)
