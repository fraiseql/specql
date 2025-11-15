"""
Security tests for SQL injection prevention
"""

from src.generators.actions.step_compilers.insert_compiler import InsertStepCompiler
from src.generators.actions.database_operation_compiler import DatabaseOperationCompiler


class TestSQLInjectionPrevention:
    """Test suite for SQL injection prevention in action compilers"""

    def test_insert_compiler_prevents_sql_injection(self):
        """Verify insert compiler escapes malicious input"""
        compiler = InsertStepCompiler()

        malicious_values = [
            "test'; DROP TABLE users; --",
            "'; SELECT * FROM users WHERE '1'='1",
            "O'Reilly",  # Legitimate apostrophe
            "It's a trap!",
            "value' OR '1'='1",  # Classic SQL injection
            "'; DELETE FROM users; --",
        ]

        for value in malicious_values:
            # Compile insert with malicious value
            formatted = compiler._format_value(value)

            # Verify it's wrapped in single quotes
            assert formatted.startswith("'")
            assert formatted.endswith("'")

            # Verify the formatted value, when used in SQL, would be safe
            # The key test: count single quotes should be even (all properly escaped)
            single_quote_count = formatted.count("'")
            assert single_quote_count % 2 == 0, f"Uneven quotes in {formatted}"

            # Verify all single quotes in inner content are properly escaped (in pairs of '')
            inner_content = formatted[1:-1]  # Remove wrapping quotes

            # Find all single quote positions
            quote_positions = [i for i, c in enumerate(inner_content) if c == "'"]

            # They should all come in consecutive pairs
            assert len(quote_positions) % 2 == 0, (
                f"Odd number of quotes in: {inner_content}"
            )

            for i in range(0, len(quote_positions), 2):
                pos1, pos2 = quote_positions[i], quote_positions[i + 1]
                assert pos2 == pos1 + 1, (
                    f"Non-consecutive quotes at {pos1},{pos2} in: {inner_content}"
                )

    def test_database_operation_compiler_prevents_sql_injection(self):
        """Verify database operation compiler escapes malicious input"""
        compiler = DatabaseOperationCompiler()

        malicious_values = [
            "test'; DROP TABLE users; --",
            "'; SELECT * FROM users WHERE '1'='1",
            "O'Reilly",  # Legitimate apostrophe
            "It's a trap!",
            "value' OR '1'='1",  # Classic SQL injection
            "'; DELETE FROM users; --",
        ]

        for value in malicious_values:
            # Compile update with malicious value
            formatted = compiler._format_value(value)

            # Verify it's wrapped in single quotes
            assert formatted.startswith("'")
            assert formatted.endswith("'")

            # Verify the formatted value, when used in SQL, would be safe
            # The key test: count single quotes should be even (all properly escaped)
            single_quote_count = formatted.count("'")
            assert single_quote_count % 2 == 0, f"Uneven quotes in {formatted}"

            # Verify all single quotes in inner content are properly escaped (in pairs of '')
            inner_content = formatted[1:-1]  # Remove wrapping quotes

            # Find all single quote positions
            quote_positions = [i for i, c in enumerate(inner_content) if c == "'"]

            # They should all come in consecutive pairs
            assert len(quote_positions) % 2 == 0, (
                f"Odd number of quotes in: {inner_content}"
            )

            for i in range(0, len(quote_positions), 2):
                pos1, pos2 = quote_positions[i], quote_positions[i + 1]
                assert pos2 == pos1 + 1, (
                    f"Non-consecutive quotes at {pos1},{pos2} in: {inner_content}"
                )

    def test_legitimate_values_still_work(self):
        """Verify legitimate values are still formatted correctly"""
        insert_compiler = InsertStepCompiler()
        db_compiler = DatabaseOperationCompiler()

        test_values = [
            "normal string",
            "string with spaces",
            "string-with-dashes",
            "string_with_underscores",
            "123",  # Numbers as strings
        ]

        for value in test_values:
            insert_formatted = insert_compiler._format_value(value)
            db_formatted = db_compiler._format_value(value)

            # Should be wrapped in quotes
            assert insert_formatted.startswith("'")
            assert insert_formatted.endswith("'")
            assert db_formatted.startswith("'")
            assert db_formatted.endswith("'")

            # Should not have escaped quotes (no apostrophes to escape)
            assert "''" not in insert_formatted
            assert "''" not in db_formatted

    def test_empty_string_handling(self):
        """Verify empty strings are handled correctly"""
        insert_compiler = InsertStepCompiler()
        db_compiler = DatabaseOperationCompiler()

        # Empty string should be escaped as '' (two single quotes)
        insert_formatted = insert_compiler._format_value("")
        db_formatted = db_compiler._format_value("")

        assert insert_formatted == "''"
        assert db_formatted == "''"

    def test_variable_references_not_affected(self):
        """Verify variable references ($var) are not escaped"""
        compiler = InsertStepCompiler()

        variable_refs = [
            "$name",
            "$email",
            "$user_id",
            "$1",  # Positional parameter
        ]

        for var_ref in variable_refs:
            formatted = compiler._format_value(var_ref)

            # Should not be wrapped in quotes (variable reference)
            assert not formatted.startswith("'")
            assert not formatted.endswith("'")

            # Should have v_ prefix
            assert formatted.startswith("v_")

    def test_non_string_values_not_affected(self):
        """Verify non-string values are converted to string without quotes"""
        compiler = InsertStepCompiler()

        test_values = [
            123,
            45.67,
            True,
            False,
            None,
        ]

        for value in test_values:
            formatted = compiler._format_value(value)

            # Should not be wrapped in quotes
            assert not formatted.startswith("'")
            assert not formatted.endswith("'")

            # Should be string representation
            assert formatted == str(value)
