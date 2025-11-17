"""
Tests for simple SQL function reverse engineering

These tests ensure basic functionality continues to work
while we enhance complex case handling.
"""

import pytest
from src.reverse_engineering.algorithmic_parser import AlgorithmicParser


class TestSimpleSQLFunctions:
    """Test simple SQL function parsing (should maintain 80%+ confidence)"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = AlgorithmicParser(use_heuristics=True, use_ai=False)

    def test_basic_select_function(self):
        """Test basic SELECT function parsing"""
        sql = """
        CREATE FUNCTION get_contact(contact_id int) RETURNS contacts AS $$
        BEGIN
            RETURN QUERY SELECT * FROM contacts WHERE id = contact_id;
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        assert result.function_name == "get_contact"
        assert len(result.steps) >= 1

    def test_basic_insert_function(self):
        """Test basic INSERT function parsing"""
        sql = """
        CREATE FUNCTION create_contact(email text, name text) RETURNS int AS $$
        DECLARE
            new_id int;
        BEGIN
            INSERT INTO contacts (email, name) VALUES (email, name) RETURNING id INTO new_id;
            RETURN new_id;
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        assert result.function_name == "create_contact"
        # INSERT statements are parsed as "query" type with SQL containing INSERT
        assert any(step.type == "query" and "INSERT" in step.sql.upper() for step in result.steps if hasattr(step, 'sql') and step.sql)

    def test_basic_update_function(self):
        """Test basic UPDATE function parsing"""
        sql = """
        CREATE FUNCTION update_contact(contact_id int, email text) RETURNS void AS $$
        BEGIN
            UPDATE contacts SET email = email WHERE id = contact_id;
        END;
        $$ LANGUAGE plpgsql;
        """

        result = self.parser.parse(sql)

        assert result.confidence >= 0.80
        assert result.function_name == "update_contact"
        # UPDATE statements are parsed as "query" type with SQL containing UPDATE
        assert any(step.type == "query" and "UPDATE" in step.sql.upper() for step in result.steps if hasattr(step, 'sql') and step.sql)
