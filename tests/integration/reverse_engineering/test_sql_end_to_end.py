"""
End-to-end tests for SQL reverse engineering

These tests verify the complete pipeline from SQL to SpecQL YAML.
"""

from reverse_engineering.algorithmic_parser import AlgorithmicParser


class TestSQLEndToEnd:
    """Test complete SQL reverse engineering pipeline"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = AlgorithmicParser(use_heuristics=True, use_ai=False)

    def test_complex_function_to_yaml(self):
        """Test converting complex SQL function to YAML"""
        sql = """
        CREATE FUNCTION calculate_hierarchy() RETURNS TABLE AS $$
        WITH RECURSIVE parent_chain AS (
            SELECT * FROM units WHERE parent_id IS NULL
            UNION ALL
            SELECT u.* FROM units u
            JOIN parent_chain pc ON u.parent_id = pc.id
        )
        SELECT * FROM parent_chain;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        # Should generate valid YAML
        yaml_output = self.parser._to_yaml(result)
        assert "name:" in yaml_output  # Function name in YAML
        assert "confidence:" in yaml_output
        assert "steps:" in yaml_output
        assert "cte:" in yaml_output  # Should contain CTE step

        # Confidence should be high for complex cases after implementation
        assert result.confidence >= 0.85  # Improved from 11% to 85%+

    def test_exception_handler_to_yaml(self):
        """Test converting function with exception handlers to YAML"""
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

        yaml_output = self.parser._to_yaml(result)
        assert "name:" in yaml_output
        assert result.confidence >= 0.8  # Exception handlers now implemented
        assert "try_except" in yaml_output  # Should contain exception handling steps

    def test_dynamic_sql_to_yaml(self):
        """Test converting function with dynamic SQL to YAML"""
        sql = """
        CREATE FUNCTION dynamic_query(table_name text) RETURNS void AS $$
        DECLARE
            query_text text;
        BEGIN
            query_text := 'UPDATE ' || table_name || ' SET processed = true';
            EXECUTE query_text;
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        yaml_output = self.parser._to_yaml(result)
        assert "name:" in yaml_output
        assert result.confidence >= 0.8  # Dynamic SQL now implemented
        assert "execute" in yaml_output  # Should contain EXECUTE step

    def test_cursor_operations_to_yaml(self):
        """Test converting function with cursor operations to YAML"""
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
                UPDATE contacts SET processed_at = NOW() WHERE id = contact_record.id;
            END LOOP;
            CLOSE contact_cursor;
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        yaml_output = self.parser._to_yaml(result)
        assert "name:" in yaml_output
        assert result.confidence >= 0.75  # Cursor operations now implemented
        assert "cursor_declare" in yaml_output
        assert "cursor_open" in yaml_output
        assert "cursor_fetch" in yaml_output
        assert "cursor_close" in yaml_output

    def test_window_functions_to_yaml(self):
        """Test converting function with window functions to YAML"""
        sql = """
        CREATE FUNCTION rank_contacts() RETURNS TABLE AS $$
        SELECT
            id,
            company_id,
            created_at,
            ROW_NUMBER() OVER (
                PARTITION BY company_id
                ORDER BY created_at DESC
            ) as contact_rank,
            LAG(created_at, 1) OVER (
                PARTITION BY company_id
                ORDER BY created_at
            ) as prev_contact_date
        FROM contacts;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        yaml_output = self.parser._to_yaml(result)
        assert "name:" in yaml_output
        assert result.confidence >= 0.8  # Window functions now implemented
        assert "window_function" in yaml_output
        # Verify window function step is detected
        assert any(step.type == "window_function" for step in result.steps)

    def test_aggregate_filters_to_yaml(self):
        """Test converting function with aggregate filters to YAML"""
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

        yaml_output = self.parser._to_yaml(result)
        assert "name:" in yaml_output
        assert result.confidence >= 0.8  # Aggregate filters now implemented
        assert "aggregate" in yaml_output
        # Verify aggregate step is detected
        assert any(step.type == "aggregate" for step in result.steps)
