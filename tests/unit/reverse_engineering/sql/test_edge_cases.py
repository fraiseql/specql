"""
Tests for SQL function edge cases and error handling

These tests ensure robust error handling and edge case coverage.
"""

import pytest
from src.reverse_engineering.algorithmic_parser import AlgorithmicParser


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

        # Should not crash, should provide meaningful error
        with pytest.raises(ValueError):
            self.parser.parse(sql)

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

    def test_nested_comments(self):
        """Test parsing functions with nested comments"""
        sql = """
        CREATE FUNCTION commented_func() RETURNS void AS $$
        BEGIN
            -- This is a comment
            /* This is a block comment
               SELECT * FROM contacts;  -- SQL inside comment should be ignored
               /* Nested comment */
               UPDATE contacts SET status = 'active';
            */
            UPDATE contacts SET processed = true;  -- Real SQL
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        # Should ignore SQL inside comments
        assert any(step.type == "update" for step in result.steps)
        # Should not parse the commented UPDATE
