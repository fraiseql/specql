"""
Tests for input validation limits (DoS prevention)

These tests ensure that the parser rejects:
1. YAML files that are too large (DoS prevention)
2. YAML with excessive nesting depth (stack overflow prevention)
3. Entities with too many fields (complexity prevention)
"""

import pytest

from src.core.exceptions import SpecQLValidationError
from src.core.specql_parser import ParseError, SpecQLParser


class TestYAMLFileSizeLimits:
    """Test maximum YAML file size limits"""

    def test_yaml_file_within_size_limit(self):
        """Valid YAML file within size limit should parse successfully"""
        parser = SpecQLParser()
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
  name: text
"""
        # Should not raise any exception
        entity = parser.parse(yaml_content)
        assert entity.name == "Contact"

    def test_yaml_file_exceeds_size_limit(self):
        """YAML file exceeding size limit should be rejected"""
        parser = SpecQLParser()

        # Create a YAML file larger than the limit (e.g., 1MB)
        # Use padding instead of many fields to avoid triggering field count limit first
        large_yaml = "entity: Contact\nschema: crm\nfields:\n  email: text\n"
        large_yaml += "description: |\n"
        # Add padding to exceed 1MB (1,048,576 bytes)
        padding_size = 1_048_600  # Slightly over 1MB
        large_yaml += "  " + ("x" * padding_size) + "\n"

        # Should raise ParseError for file size
        with pytest.raises(ParseError, match="YAML file size .* exceeds maximum allowed"):
            parser.parse(large_yaml)

    def test_yaml_file_at_size_limit_boundary(self):
        """YAML file at exactly the size limit should be allowed"""
        parser = SpecQLParser()

        # Create a YAML file at exactly the limit
        # We'll need to know the exact limit to test this boundary
        # For now, assume limit is 1MB = 1,048,576 bytes
        yaml_content = "entity: Contact\nschema: crm\nfields:\n"
        yaml_content += "  email: text\n"

        # Pad to just under 1MB
        padding_size = 1048576 - len(yaml_content) - 100  # Leave some margin
        yaml_content += "  description: text  # " + ("x" * padding_size) + "\n"

        # Should parse successfully
        entity = parser.parse(yaml_content)
        assert entity.name == "Contact"


class TestYAMLNestingDepthLimits:
    """Test maximum YAML nesting depth limits"""

    def test_yaml_within_nesting_depth_limit(self):
        """YAML with reasonable nesting depth should parse successfully"""
        parser = SpecQLParser()
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
  status: text
actions:
  - name: update_contact
    steps:
      - if: email != null
        then:
          - validate: email matches email_pattern
          - update: Contact SET status = 'validated'
"""
        # Should not raise any exception
        entity = parser.parse(yaml_content)
        assert entity.name == "Contact"

    def test_yaml_exceeds_nesting_depth_limit(self):
        """YAML exceeding nesting depth limit should be rejected"""
        parser = SpecQLParser()

        # Create deeply nested structure (e.g., 100 levels of if/then)
        yaml_content = "entity: Contact\nschema: crm\nfields:\n  email: text\nactions:\n"
        yaml_content += "  - name: deeply_nested\n    steps:\n"

        # Build 100 levels of nested if/then
        indent = "      "
        for i in range(100):
            yaml_content += f"{indent * i}      - if: email != null\n"
            yaml_content += f"{indent * i}        then:\n"

        # Add final step
        yaml_content += f"{indent * 100}          - validate: email != null\n"

        # Should raise ParseError for nesting depth
        with pytest.raises(ParseError, match="YAML nesting depth .* exceeds maximum allowed"):
            parser.parse(yaml_content)

    def test_yaml_at_nesting_depth_boundary(self):
        """YAML at exactly the nesting depth limit should be allowed"""
        parser = SpecQLParser()

        # Create structure at exactly the limit (e.g., 50 levels)
        # Account for base YAML structure depth and each if/then adds 2 levels (if dict, then list)
        # We need to stay within 50 levels total
        yaml_content = "entity: Contact\nschema: crm\nfields:\n  email: text\nactions:\n"
        yaml_content += "  - name: at_limit\n    steps:\n"

        # Build 22 levels of nested if/then to stay at depth 50
        # Each iteration adds ~2 levels (if dict + then list)
        indent = "      "
        for i in range(22):
            yaml_content += f"{indent * i}      - if: email != null\n"
            yaml_content += f"{indent * i}        then:\n"

        yaml_content += f"{indent * 22}          - validate: email != null\n"

        # Should parse successfully
        entity = parser.parse(yaml_content)
        assert entity.name == "Contact"


class TestEntityFieldCountLimits:
    """Test maximum field count limits per entity"""

    def test_entity_within_field_count_limit(self):
        """Entity with reasonable field count should parse successfully"""
        parser = SpecQLParser()
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
  name: text
  phone: text
  company: ref(Company)
  status: enum(active, inactive)
"""
        # Should not raise any exception
        entity = parser.parse(yaml_content)
        assert entity.name == "Contact"
        assert len(entity.fields) == 5

    def test_entity_exceeds_field_count_limit(self):
        """Entity exceeding field count limit should be rejected"""
        parser = SpecQLParser()

        # Create entity with too many fields (e.g., 1001 fields)
        yaml_content = "entity: Contact\nschema: crm\nfields:\n"
        for i in range(1001):
            yaml_content += f"  field_{i}: text\n"

        # Should raise SpecQLValidationError for field count
        with pytest.raises(SpecQLValidationError, match="Field count .* exceeds maximum allowed"):
            parser.parse(yaml_content)

    def test_entity_at_field_count_boundary(self):
        """Entity at exactly the field count limit should be allowed"""
        parser = SpecQLParser()

        # Create entity with exactly 1000 fields (assuming limit is 1000)
        yaml_content = "entity: Contact\nschema: crm\nfields:\n"
        for i in range(1000):
            yaml_content += f"  field_{i}: text\n"

        # Should parse successfully
        entity = parser.parse(yaml_content)
        assert entity.name == "Contact"
        assert len(entity.fields) == 1000


class TestActionCountLimits:
    """Test maximum action count limits per entity"""

    def test_entity_within_action_count_limit(self):
        """Entity with reasonable action count should parse successfully"""
        parser = SpecQLParser()
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
actions:
  - name: action1
    steps:
      - validate: email != null
  - name: action2
    steps:
      - validate: email != null
"""
        # Should not raise any exception
        entity = parser.parse(yaml_content)
        assert entity.name == "Contact"
        assert len(entity.actions) == 2

    def test_entity_exceeds_action_count_limit(self):
        """Entity exceeding action count limit should be rejected"""
        parser = SpecQLParser()

        # Create entity with too many actions (e.g., 101 actions)
        yaml_content = "entity: Contact\nschema: crm\nfields:\n  email: text\nactions:\n"
        for i in range(101):
            yaml_content += f"  - name: action_{i}\n"
            yaml_content += f"    steps:\n"
            yaml_content += f"      - validate: email != null\n"

        # Should raise SpecQLValidationError for action count
        with pytest.raises(SpecQLValidationError, match="Action count .* exceeds maximum allowed"):
            parser.parse(yaml_content)

    def test_entity_at_action_count_boundary(self):
        """Entity at exactly the action count limit should be allowed"""
        parser = SpecQLParser()

        # Create entity with exactly 100 actions (assuming limit is 100)
        yaml_content = "entity: Contact\nschema: crm\nfields:\n  email: text\nactions:\n"
        for i in range(100):
            yaml_content += f"  - name: action_{i}\n"
            yaml_content += f"    steps:\n"
            yaml_content += f"      - validate: email != null\n"

        # Should parse successfully
        entity = parser.parse(yaml_content)
        assert entity.name == "Contact"
        assert len(entity.actions) == 100


class TestStepsPerActionLimit:
    """Test maximum steps per action limit"""

    def test_action_within_steps_limit(self):
        """Action with reasonable step count should parse successfully"""
        parser = SpecQLParser()
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
  status: text
actions:
  - name: update_contact
    steps:
      - validate: email != null
      - update: Contact SET status = 'validated'
      - validate: status = 'validated'
"""
        # Should not raise any exception
        entity = parser.parse(yaml_content)
        assert len(entity.actions[0].steps) == 3

    def test_action_exceeds_steps_limit(self):
        """Action exceeding steps limit should be rejected"""
        parser = SpecQLParser()

        # Create action with too many steps (e.g., 501 steps)
        yaml_content = "entity: Contact\nschema: crm\nfields:\n  email: text\nactions:\n"
        yaml_content += "  - name: many_steps\n    steps:\n"
        for i in range(501):
            yaml_content += f"      - validate: email != null\n"

        # Should raise SpecQLValidationError for steps count
        with pytest.raises(SpecQLValidationError, match="Steps count .* exceeds maximum allowed"):
            parser.parse(yaml_content)

    def test_action_at_steps_limit_boundary(self):
        """Action at exactly the steps limit should be allowed"""
        parser = SpecQLParser()

        # Create action with exactly 500 steps (assuming limit is 500)
        yaml_content = "entity: Contact\nschema: crm\nfields:\n  email: text\nactions:\n"
        yaml_content += "  - name: at_limit\n    steps:\n"
        for i in range(500):
            yaml_content += f"      - validate: email != null\n"

        # Should parse successfully
        entity = parser.parse(yaml_content)
        assert len(entity.actions[0].steps) == 500
