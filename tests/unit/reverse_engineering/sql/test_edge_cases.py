"""
Tests for SQL function edge cases and error handling

These tests ensure robust error handling and edge case coverage.
"""

from reverse_engineering.algorithmic_parser import AlgorithmicParser


class TestSQLEdgeCases:
    """Test edge cases and error conditions"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = AlgorithmicParser(use_heuristics=True, use_ai=False)

    def test_empty_function(self):
        """Test parsing empty function body"""
        sql = """
        CREATE FUNCTION empty_func() RETURNS void AS $$
        BEGIN
            -- Empty body
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.90  # Should be very confident about empty functions
        assert len(result.steps) == 0

    def test_syntax_error_recovery(self):
        """Test graceful handling of syntax errors"""
        sql = """
        CREATE FUNCTION broken_func() RETURNS void AS $$
        BEGIN
            SELECT * FROM;  -- Syntax error: missing table name
        END;
        $$ LANGUAGE plpgsql;
        """

        # Parser should handle errors gracefully with fallback parsing
        result = self.parser.parse(sql)

        # Should succeed with reduced confidence due to fallback
        assert result.confidence < 1.0
        # Should have warnings about fallback parsing
        assert len(result.warnings) > 0
        # Should still identify the function
        assert result.function_name == "broken_func"

    def test_very_long_function(self):
        """Test parsing very long functions"""
        # Generate a long function with many similar statements
        statements = []
        for i in range(100):
            statements.append(f"UPDATE contacts SET counter = counter + 1 WHERE id = {i};")

        sql = f"""
        CREATE FUNCTION long_function() RETURNS void AS $$
        BEGIN
            {" ".join(statements)}
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.70  # Should handle long functions reasonably well
        assert len(result.steps) >= 50  # Should parse most statements

    def test_simple_comments(self):
        """Test parsing functions with single-line comments"""
        # Note: Inline comments after SQL can interfere with statement parsing
        # This test verifies the parser can handle SQL with preceding comments
        sql = """
        CREATE FUNCTION commented_func() RETURNS void AS $$
        BEGIN
            -- This is a comment on its own line
            UPDATE contacts SET processed = true;
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        # Should parse the UPDATE statement despite the comment
        assert any(
            step.type == "query" and "UPDATE" in step.sql.upper()
            for step in result.steps
            if hasattr(step, "sql") and step.sql
        )
