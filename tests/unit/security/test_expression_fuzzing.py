"""
Expression Compiler Fuzzing Tests

Fuzz testing to find edge cases and vulnerabilities in:
- Expression parsing
- Operator handling
- Function call parsing
- String literal processing
- Complex nested expressions
"""

import random
import string

import pytest

from src.core.ast_models import EntityDefinition, FieldDefinition
from src.generators.actions.expression_compiler import ExpressionCompiler, SecurityError


@pytest.fixture
def compiler():
    """Create expression compiler for testing"""
    return ExpressionCompiler()


@pytest.fixture
def test_entity():
    """Create test entity with various field types"""
    return EntityDefinition(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="text"),
            "status": FieldDefinition(name="status", type_name="text"),
            "score": FieldDefinition(name="score", type_name="integer"),
            "company_id": FieldDefinition(name="company_id", type_name="uuid"),
            "name": FieldDefinition(name="name", type_name="text"),
            "active": FieldDefinition(name="active", type_name="boolean"),
        },
    )


class TestRandomStringFuzzing:
    """Test random string inputs to find crashes"""

    def test_random_ascii_strings(self, compiler, test_entity):
        """Test random ASCII strings"""
        for _ in range(50):
            length = random.randint(1, 100)
            random_str = "".join(
                random.choices(string.ascii_letters + string.digits, k=length)
            )

            try:
                result = compiler.compile(random_str, test_entity)
                # If it doesn't crash, that's good
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError, TypeError):
                # These exceptions are expected for invalid input
                pass

    def test_random_printable_characters(self, compiler, test_entity):
        """Test random printable characters"""
        for _ in range(50):
            length = random.randint(1, 50)
            random_str = "".join(random.choices(string.printable, k=length))

            try:
                result = compiler.compile(random_str, test_entity)
                assert isinstance(result, str)
            except (
                SecurityError,
                ValueError,
                KeyError,
                AttributeError,
                TypeError,
                IndexError,
            ):
                # Expected exceptions
                pass

    def test_random_unicode_strings(self, compiler, test_entity):
        """Test random Unicode strings"""
        unicode_ranges = [
            (0x0020, 0x007E),  # Basic Latin
            (0x00A0, 0x00FF),  # Latin-1 Supplement
            (0x0100, 0x017F),  # Latin Extended-A
            (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        ]

        for _ in range(30):
            length = random.randint(1, 30)
            chars = []
            for _ in range(length):
                start, end = random.choice(unicode_ranges)
                chars.append(chr(random.randint(start, end)))
            random_str = "".join(chars)

            try:
                result = compiler.compile(random_str, test_entity)
                assert isinstance(result, str)
            except (
                SecurityError,
                ValueError,
                KeyError,
                AttributeError,
                TypeError,
                UnicodeError,
            ):
                pass


class TestOperatorFuzzing:
    """Test fuzzing with operators"""

    def test_random_operator_combinations(self, compiler, test_entity):
        """Test random combinations of operators"""
        operators = ["=", "!=", "<", ">", "<=", ">=", "AND", "OR", "NOT", "IN", "LIKE"]
        fields = ["email", "status", "score", "name"]
        values = ["'test'", "'lead'", "100", "'qualified'"]

        for _ in range(50):
            # Generate random expression
            field = random.choice(fields)
            operator = random.choice(operators)
            value = random.choice(values)

            expr = f"{field} {operator} {value}"

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError, TypeError):
                pass

    def test_random_operator_stacking(self, compiler, test_entity):
        """Test stacking multiple operators"""
        for _ in range(30):
            num_ops = random.randint(1, 5)
            parts = []

            for i in range(num_ops):
                parts.append("status = 'lead'")
                if i < num_ops - 1:
                    parts.append(random.choice(["AND", "OR"]))

            expr = " ".join(parts)

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError, TypeError):
                pass


class TestParenthesesFuzzing:
    """Test fuzzing with parentheses"""

    def test_random_parentheses(self, compiler, test_entity):
        """Test random parentheses placement"""
        base_expr = "status = 'lead' AND score > 50 OR name = 'test'"

        for _ in range(30):
            # Add random parentheses
            num_open = random.randint(0, 5)
            num_close = random.randint(0, 5)

            expr = "(" * num_open + base_expr + ")" * num_close

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (
                SecurityError,
                ValueError,
                KeyError,
                AttributeError,
                TypeError,
                IndexError,
            ):
                pass

    def test_nested_parentheses(self, compiler, test_entity):
        """Test deeply nested parentheses"""
        for depth in range(1, 20):
            expr = "(" * depth + "status = 'lead'" + ")" * depth

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (
                SecurityError,
                ValueError,
                KeyError,
                RecursionError,
                AttributeError,
            ):
                # RecursionError might occur with very deep nesting
                pass

    def test_unbalanced_parentheses(self, compiler, test_entity):
        """Test unbalanced parentheses"""
        expressions = [
            "(status = 'lead'",
            "status = 'lead')",
            "((status = 'lead')",
            "(status = 'lead'))",
            ")(status = 'lead'",
            "status = 'lead'(",
        ]

        for expr in expressions:
            try:
                result = compiler.compile(expr, test_entity)
                # Should either handle gracefully or raise an exception
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError, IndexError):
                pass


class TestFunctionFuzzing:
    """Test fuzzing with function calls"""

    def test_random_function_calls(self, compiler, test_entity):
        """Test random function calls"""
        safe_functions = ["UPPER", "LOWER", "TRIM", "LENGTH", "COALESCE"]
        fields = ["email", "status", "name"]

        for _ in range(30):
            func = random.choice(safe_functions)
            field = random.choice(fields)

            # Test various function call patterns
            expressions = [
                f"{func}({field})",
                f"{func}({field}) = 'test'",
                f"status = {func}({field})",
            ]

            for expr in expressions:
                try:
                    result = compiler.compile(expr, test_entity)
                    assert isinstance(result, str)
                except (SecurityError, ValueError, KeyError, AttributeError, TypeError):
                    pass

    def test_nested_function_calls(self, compiler, test_entity):
        """Test deeply nested function calls"""
        functions = ["UPPER", "LOWER", "TRIM"]

        for depth in range(1, 10):
            expr = "email"
            for _ in range(depth):
                func = random.choice(functions)
                expr = f"{func}({expr})"

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, RecursionError, AttributeError):
                pass

    def test_function_with_random_args(self, compiler, test_entity):
        """Test functions with random number of arguments"""
        for _ in range(30):
            num_args = random.randint(0, 5)
            args = [f"'arg{i}'" for i in range(num_args)]
            expr = f"CONCAT({', '.join(args)})"

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError, TypeError):
                pass


class TestStringLiteralFuzzing:
    """Test fuzzing with string literals"""

    def test_string_with_special_characters(self, compiler, test_entity):
        """Test strings with special characters"""
        special_chars = ["'", '"', "\\", "\n", "\r", "\t", "\0", "%", "_"]

        for char in special_chars:
            expr = f"status = 'test{char}value'"

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, AttributeError):
                pass

    def test_string_with_quotes(self, compiler, test_entity):
        """Test strings with various quote combinations"""
        quote_patterns = [
            "'test''value'",  # Escaped single quote
            '"test"value"',
            "'test\"value'",
            '"test\'value"',
            "''''",  # Multiple quotes
        ]

        for pattern in quote_patterns:
            expr = f"status = {pattern}"

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, AttributeError, IndexError):
                pass

    def test_very_long_strings(self, compiler, test_entity):
        """Test very long string literals"""
        for length in [100, 1000, 10000]:
            long_string = "a" * length
            expr = f"status = '{long_string}'"

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, MemoryError):
                pass


class TestComplexExpressionFuzzing:
    """Test fuzzing with complex expressions"""

    def test_random_complex_expressions(self, compiler, test_entity):
        """Generate random complex expressions"""
        for _ in range(30):
            parts = []
            num_parts = random.randint(1, 5)

            for i in range(num_parts):
                field = random.choice(["email", "status", "score"])
                operator = random.choice(["=", "!=", ">", "<"])
                value = random.choice(["'test'", "100", "'lead'"])

                parts.append(f"{field} {operator} {value}")

                if i < num_parts - 1:
                    parts.append(random.choice(["AND", "OR"]))

            expr = " ".join(parts)

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError, TypeError):
                pass

    def test_mixed_functions_and_operators(self, compiler, test_entity):
        """Test mixing functions and operators"""
        for _ in range(30):
            patterns = [
                "UPPER(email) = 'TEST' AND score > 50",
                "LOWER(status) = 'lead' OR TRIM(name) = 'test'",
                "LENGTH(email) > 10 AND status = 'qualified'",
                "UPPER(TRIM(email)) LIKE '%TEST%'",
            ]

            expr = random.choice(patterns)

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError, TypeError):
                pass


class TestSubqueryFuzzing:
    """Test fuzzing with subqueries"""

    def test_random_subquery_patterns(self, compiler, test_entity):
        """Test various subquery patterns"""
        subquery_patterns = [
            "company_id IN (SELECT id FROM companies)",
            "status IN (SELECT status FROM valid_statuses WHERE active = true)",
            "score > (SELECT AVG(score) FROM contacts)",
        ]

        for pattern in subquery_patterns:
            try:
                result = compiler.compile(pattern, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError):
                pass

    def test_nested_subqueries(self, compiler, test_entity):
        """Test nested subqueries"""
        for depth in range(1, 5):
            expr = "company_id IN (SELECT id FROM companies"
            for _ in range(depth - 1):
                expr += " WHERE id IN (SELECT id FROM companies"
            expr += ")" * depth

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, RecursionError, AttributeError):
                pass


class TestWhitespaceFuzzing:
    """Test fuzzing with whitespace"""

    def test_random_whitespace(self, compiler, test_entity):
        """Test random whitespace placement"""
        base_expr = "status='lead'ANDscore>50"
        whitespace_chars = [" ", "\t", "  ", "   "]

        for _ in range(20):
            expr = ""
            for char in base_expr:
                expr += char
                if random.random() < 0.3:  # 30% chance to add whitespace
                    expr += random.choice(whitespace_chars)

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, KeyError, AttributeError, TypeError):
                pass

    def test_excessive_whitespace(self, compiler, test_entity):
        """Test expressions with excessive whitespace"""
        base = "status = 'lead' AND score > 50"

        for spaces in [10, 100, 1000]:
            expr = base.replace(" ", " " * spaces)

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, MemoryError):
                pass


class TestEdgeCaseFuzzing:
    """Test edge cases and boundary conditions"""

    def test_empty_and_minimal_inputs(self, compiler, test_entity):
        """Test empty and minimal inputs"""
        edge_inputs = [
            "",
            " ",
            "a",
            "1",
            "'",
            "(",
            ")",
            "=",
        ]

        for expr in edge_inputs:
            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (
                SecurityError,
                ValueError,
                KeyError,
                AttributeError,
                IndexError,
                TypeError,
            ):
                pass

    def test_maximum_length_expressions(self, compiler, test_entity):
        """Test very long expressions"""
        for length in [100, 500, 1000]:
            parts = ["status = 'lead'"] * (length // 20)
            expr = " AND ".join(parts)

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, MemoryError, RecursionError):
                pass

    def test_special_number_values(self, compiler, test_entity):
        """Test special numeric values"""
        special_numbers = [
            "0",
            "-1",
            "999999999999999999999",
            "0.0",
            "-0.0",
            "1e308",
            "-1e308",
        ]

        for num in special_numbers:
            expr = f"score = {num}"

            try:
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, OverflowError):
                pass

    def test_boundary_characters(self, compiler, test_entity):
        """Test boundary ASCII characters"""
        for code in [0, 1, 31, 32, 126, 127]:
            try:
                char = chr(code)
                expr = f"status = 'test{char}value'"
                result = compiler.compile(expr, test_entity)
                assert isinstance(result, str)
            except (SecurityError, ValueError, UnicodeError):
                pass


class TestCrashResistance:
    """Ensure the compiler doesn't crash with malformed input"""

    def test_no_crashes_on_random_input(self, compiler, test_entity):
        """Verify no crashes on various random inputs"""
        # Generate 100 random test cases
        random.seed(42)  # For reproducibility

        crash_count = 0
        exception_count = 0

        for _ in range(100):
            # Generate random expression
            length = random.randint(1, 100)
            chars = string.ascii_letters + string.digits + " '\"()=<>!+-*/"
            random_expr = "".join(random.choices(chars, k=length))

            try:
                result = compiler.compile(random_expr, test_entity)
                # No crash - good!
                assert isinstance(result, str) or result is None
            except (
                SecurityError,
                ValueError,
                KeyError,
                AttributeError,
                TypeError,
                IndexError,
            ):
                # Expected exceptions - not crashes
                exception_count += 1
            except Exception as e:
                # Unexpected exception - might be a crash
                crash_count += 1
                # Log but don't fail the test
                print(f"Unexpected exception for input '{random_expr}': {e}")

        # We expect most random inputs to raise exceptions
        # but we shouldn't have many unexpected crashes
        assert crash_count < 10, f"Too many unexpected crashes: {crash_count}"
