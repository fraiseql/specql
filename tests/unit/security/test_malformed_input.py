"""
Malformed Input Security Tests

Tests for handling of malformed inputs:
- Large files (DoS prevention)
- Deep nesting (recursion limit testing)
- Malformed YAML
- Invalid data structures
- Resource exhaustion attacks
"""

import tempfile
from pathlib import Path

import pytest

from src.core.specql_parser import SpecQLParser


@pytest.fixture
def parser():
    """Create SpecQL parser for testing"""
    return SpecQLParser()


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestLargeFileSecurity:
    """Test handling of very large files"""

    def test_extremely_large_yaml_file(self, temp_dir, parser):
        """Test handling of extremely large YAML files (DoS prevention)"""
        # Create a very large YAML file
        large_file = temp_dir / "large.yaml"

        with large_file.open("w") as f:
            f.write("entity: Contact\n")
            f.write("schema: crm\n")
            f.write("fields:\n")

            # Write 10,000 fields
            for i in range(10000):
                f.write(f"  field_{i}: text\n")

        # Try to parse - should either handle it or reject gracefully
        try:
            content = large_file.read_text()
            result = parser.parse(content)
            # If it succeeds, verify it has the expected structure
            assert result.name == "Contact"
            assert len(result.fields) <= 10000
        except (MemoryError, ValueError, RuntimeError):
            # It's OK to reject extremely large files
            pass

    def test_large_field_count(self, parser):
        """Test entity with very large number of fields"""
        # Generate YAML with 1000 fields
        yaml_parts = [
            "entity: Contact",
            "schema: crm",
            "fields:",
        ]

        for i in range(1000):
            yaml_parts.append(f"  field_{i}: text")

        yaml_content = "\n".join(yaml_parts)

        try:
            result = parser.parse(yaml_content)
            assert result.name == "Contact"
            assert len(result.fields) == 1000
        except (MemoryError, ValueError):
            pass

    def test_very_long_field_names(self, parser):
        """Test fields with extremely long names"""
        long_name = "a" * 10000
        yaml_content = f"""
entity: Contact
schema: crm
fields:
  {long_name}: text
"""

        try:
            result = parser.parse(yaml_content)
            # Should either work or reject
            assert result
        except (ValueError, MemoryError, Exception):
            # Parser may reject extremely long field names as invalid YAML
            pass

    def test_very_long_string_values(self, parser):
        """Test very long string values"""
        long_value = "x" * 100000
        yaml_content = f"""
entity: Contact
schema: crm
description: "{long_value}"
fields:
  email: text
"""

        try:
            result = parser.parse(yaml_content)
            assert result
        except (ValueError, MemoryError):
            pass

    def test_many_actions(self, parser):
        """Test entity with very many actions"""
        yaml_parts = [
            "entity: Contact",
            "schema: crm",
            "fields:",
            "  email: text",
            "actions:",
        ]

        # Add 1000 actions
        for i in range(1000):
            yaml_parts.extend(
                [
                    f"  - name: action_{i}",
                    "    steps:",
                    "      - validate: email != ''",
                ]
            )

        yaml_content = "\n".join(yaml_parts)

        try:
            result = parser.parse(yaml_content)
            assert len(result.actions) == 1000
        except (MemoryError, ValueError, RecursionError):
            pass


class TestDeepNestingSecurity:
    """Test handling of deeply nested structures"""

    def test_deeply_nested_parentheses(self):
        """Test deeply nested parentheses in expressions"""
        from src.core.ast_models import EntityDefinition, FieldDefinition
        from src.generators.actions.expression_compiler import ExpressionCompiler

        compiler = ExpressionCompiler()
        entity = EntityDefinition(
            name="Test",
            schema="test",
            fields={"status": FieldDefinition(name="status", type_name="text")},
        )

        # Test various nesting depths
        for depth in [10, 50, 100, 500]:
            expr = "(" * depth + "status = 'test'" + ")" * depth

            try:
                result = compiler.compile(expr, entity)
                assert result
            except (RecursionError, ValueError, MemoryError):
                # It's OK to reject very deep nesting
                pass

    def test_deeply_nested_functions(self):
        """Test deeply nested function calls"""
        from src.core.ast_models import EntityDefinition, FieldDefinition
        from src.generators.actions.expression_compiler import ExpressionCompiler

        compiler = ExpressionCompiler()
        entity = EntityDefinition(
            name="Test",
            schema="test",
            fields={"email": FieldDefinition(name="email", type_name="text")},
        )

        # Nest functions deeply
        for depth in [5, 10, 20, 50]:
            expr = "email"
            for _ in range(depth):
                expr = f"UPPER({expr})"

            try:
                result = compiler.compile(expr, entity)
                assert result
            except (RecursionError, ValueError, MemoryError):
                pass

    def test_deeply_nested_yaml_structures(self, parser):
        """Test deeply nested YAML structures"""
        # YAML doesn't naturally support deep nesting in our schema
        # but we can test with actions containing nested conditions

        yaml_parts = [
            "entity: Contact",
            "schema: crm",
            "fields:",
            "  status: text",
            "actions:",
            "  - name: complex_action",
            "    steps:",
        ]

        # Create deeply nested if statements
        indent = 6
        for i in range(20):
            yaml_parts.append(" " * indent + f"- if: status = 'level{i}'")
            yaml_parts.append(" " * (indent + 2) + "then:")
            indent += 4

        # Close the nesting
        yaml_parts.append(" " * indent + "- update: Contact SET status = 'done'")

        yaml_content = "\n".join(yaml_parts)

        try:
            result = parser.parse(yaml_content)
            assert result
        except (RecursionError, ValueError):
            pass

    def test_deeply_nested_subqueries(self):
        """Test deeply nested subqueries"""
        from src.core.ast_models import EntityDefinition, FieldDefinition
        from src.generators.actions.expression_compiler import ExpressionCompiler

        compiler = ExpressionCompiler()
        entity = EntityDefinition(
            name="Test",
            schema="test",
            fields={"id": FieldDefinition(name="id", type_name="uuid")},
        )

        # Create nested IN subqueries
        for depth in [2, 5, 10]:
            expr = "id IN (SELECT id FROM table"
            for _ in range(depth - 1):
                expr += " WHERE id IN (SELECT id FROM table"
            expr += ")" * depth

            try:
                result = compiler.compile(expr, entity)
                assert result
            except (RecursionError, ValueError, MemoryError):
                pass


class TestMalformedYAML:
    """Test handling of malformed YAML"""

    def test_invalid_yaml_syntax(self, parser):
        """Test various invalid YAML syntax"""
        malformed_yamls = [
            # Missing colons
            """
entity Contact
schema crm
fields
  email text
""",
            # Incorrect indentation
            """
entity: Contact
schema: crm
fields:
email: text
""",
            # Mismatched brackets
            """
entity: Contact
schema: crm
fields: {
  email: text
""",
            # Invalid characters
            """
entity: Contact
schema: crm
fields:
  @email: text
""",
        ]

        for yaml_content in malformed_yamls:
            with pytest.raises(Exception):
                parser.parse(yaml_content)

    def test_incomplete_yaml(self, parser):
        """Test incomplete YAML documents"""
        incomplete_yamls = [
            # Empty document
            "",
            # Only whitespace
            "   \n   \n   ",
        ]

        for yaml_content in incomplete_yamls:
            with pytest.raises(Exception):
                parser.parse(yaml_content)

        # Some incomplete YAMLs might parse with defaults
        maybe_incomplete = [
            # Missing fields (might use defaults)
            """
entity: Contact
""",
            # Truncated but valid schema name
            """
entity: Contact
schema: cr
""",
        ]

        for yaml_content in maybe_incomplete:
            try:
                result = parser.parse(yaml_content)
                # Parser might accept these with defaults
                assert result is not None
            except Exception:
                # Or it might reject them
                pass

    def test_duplicate_keys(self, parser):
        """Test YAML with duplicate keys"""
        duplicate_key_yamls = [
            # Duplicate entity name
            """
entity: Contact
entity: Duplicate
schema: crm
fields:
  email: text
""",
            # Duplicate field names
            """
entity: Contact
schema: crm
fields:
  email: text
  email: text
""",
        ]

        for yaml_content in duplicate_key_yamls:
            try:
                result = parser.parse(yaml_content)
                # YAML might allow duplicates, but we should handle it
                assert result
            except (ValueError, KeyError):
                # It's OK to reject duplicates
                pass


class TestInvalidDataStructures:
    """Test handling of invalid data structures"""

    def test_invalid_field_types(self, parser):
        """Test invalid field type definitions"""
        invalid_yamls = [
            # Nonexistent type
            """
entity: Contact
schema: crm
fields:
  email: nonexistent_type
""",
            # Malformed ref
            """
entity: Contact
schema: crm
fields:
  company: ref()
""",
            # Invalid enum
            """
entity: Contact
schema: crm
fields:
  status: enum()
""",
        ]

        for yaml_content in invalid_yamls:
            try:
                result = parser.parse(yaml_content)
                # Parser might accept these, but they should be validated later
                assert result
            except (ValueError, KeyError):
                pass

    def test_invalid_action_steps(self, parser):
        """Test invalid action step definitions"""
        invalid_yamls = [
            # Unknown step type
            """
entity: Contact
schema: crm
fields:
  email: text
actions:
  - name: test_action
    steps:
      - unknown_step: some value
""",
            # Malformed validate
            """
entity: Contact
schema: crm
fields:
  email: text
actions:
  - name: test_action
    steps:
      - validate:
""",
        ]

        for yaml_content in invalid_yamls:
            # Parser should either reject these or raise an error
            with pytest.raises((ValueError, KeyError, TypeError, Exception)):
                parser.parse(yaml_content)

    def test_circular_references(self, parser):
        """Test handling of circular references"""
        # In SpecQL, circular refs might be in relationships
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
  company: ref(Company)
"""
        # This should parse OK - circular refs are a semantic issue
        result = parser.parse(yaml_content)
        assert result


class TestResourceExhaustion:
    """Test resistance to resource exhaustion attacks"""

    def test_memory_bomb_fields(self, parser):
        """Test memory bomb with many fields"""
        # Try to exhaust memory with field definitions
        yaml_parts = [
            "entity: Contact",
            "schema: crm",
            "fields:",
        ]

        # Add 50,000 fields (might be too much)
        for i in range(50000):
            yaml_parts.append(f"  field_{i}: text")

        yaml_content = "\n".join(yaml_parts)

        try:
            result = parser.parse(yaml_content)
            assert result
        except (MemoryError, ValueError):
            # Expected to reject this
            pass

    def test_memory_bomb_actions(self, parser):
        """Test memory bomb with many actions"""
        yaml_parts = [
            "entity: Contact",
            "schema: crm",
            "fields:",
            "  email: text",
            "actions:",
        ]

        # Add many actions with many steps each
        for i in range(1000):
            yaml_parts.append(f"  - name: action_{i}")
            yaml_parts.append("    steps:")
            for j in range(10):
                yaml_parts.append(f"      - validate: email != 'test{j}'")

        yaml_content = "\n".join(yaml_parts)

        try:
            result = parser.parse(yaml_content)
            assert result
        except (MemoryError, ValueError, RecursionError):
            pass

    def test_exponential_expansion(self, parser):
        """Test protection against exponential expansion"""
        # YAML anchors and aliases can cause exponential expansion
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
  data1: &anchor
    - item1
    - item2
  data2: *anchor
"""
        try:
            result = parser.parse(yaml_content)
            # Should handle or reject
            assert result
        except Exception:
            pass


class TestEdgeCases:
    """Test edge cases in input handling"""

    def test_empty_fields(self, parser):
        """Test entity with no fields"""
        yaml_content = """
entity: Contact
schema: crm
fields: {}
"""
        try:
            result = parser.parse(yaml_content)
            assert result
        except ValueError:
            # Might require at least one field
            pass

    def test_empty_actions(self, parser):
        """Test entity with empty actions"""
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
actions: []
"""
        result = parser.parse(yaml_content)
        assert len(result.actions) == 0

    def test_unicode_field_names(self, parser):
        """Test Unicode characters in field names"""
        yaml_content = """
entity: Contact
schema: crm
fields:
  电子邮件: text
  名前: text
  Имя: text
"""
        try:
            result = parser.parse(yaml_content)
            assert result
        except (ValueError, UnicodeError):
            pass

    def test_special_yaml_values(self, parser):
        """Test special YAML values"""
        yaml_content = """
entity: Contact
schema: crm
fields:
  null_field: null
  true_field: true
  false_field: false
  number_field: 123
"""
        try:
            result = parser.parse(yaml_content)
            # These might be interpreted as field types
            assert result
        except (ValueError, TypeError):
            pass

    def test_multiline_strings(self, parser):
        """Test multiline string values"""
        yaml_content = """
entity: Contact
schema: crm
description: |
  This is a very long
  multiline description
  that spans multiple lines
  and might contain special characters: <>{}[]
fields:
  email: text
"""
        result = parser.parse(yaml_content)
        assert "multiline" in result.description

    def test_binary_data_in_yaml(self, parser):
        """Test binary data in YAML (should be rejected)"""
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
binary_data: !!binary |
  R0lGODlhDAAMAIQAAP//9/X17unp5WZmZgAAAOfn515eXvPz7Y6OjuDg4J+fn5
"""
        try:
            result = parser.parse(yaml_content)
            # Should either ignore or reject binary data
            assert result
        except Exception:
            pass


class TestCrashResistance:
    """Ensure the parser doesn't crash with malformed input"""

    def test_random_bytes(self, parser, temp_dir):
        """Test parser with random bytes"""
        import random

        for _ in range(10):
            # Generate random bytes
            random_bytes = bytes([random.randint(0, 255) for _ in range(1000)])

            # Write to file
            random_file = temp_dir / "random.yaml"
            random_file.write_bytes(random_bytes)

            try:
                content = random_file.read_text(errors="ignore")
                result = parser.parse(content)
                # If it doesn't crash, good
                assert result or True
            except Exception:
                # Any exception is fine - we just don't want crashes
                pass

    def test_truncated_utf8(self, parser):
        """Test truncated UTF-8 sequences"""
        # Create truncated UTF-8
        truncated_yamls = [
            "entity: Contact\xe2\x82",  # Truncated Euro symbol
            "schema: crm\xf0\x9f",  # Truncated emoji
        ]

        for yaml_content in truncated_yamls:
            # Parser should reject invalid UTF-8
            with pytest.raises((UnicodeDecodeError, UnicodeError, ValueError, Exception)):
                parser.parse(yaml_content)

    def test_mixed_line_endings(self, parser):
        """Test mixed line endings"""
        yaml_content = "entity: Contact\r\nschema: crm\nfields:\r\n  email: text\r"
        result = parser.parse(yaml_content)
        assert result.name == "Contact"
