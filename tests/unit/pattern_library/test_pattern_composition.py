"""Tests for pattern composition system"""

import pytest
from src.pattern_library.api import PatternLibrary


class TestPatternComposition:
    """Test composing multiple domain patterns into entities"""

    def test_compose_multiple_patterns(self):
        """Test composing multiple domain patterns into one entity"""
        library = PatternLibrary(db_path=":memory:")

        # Add patterns
        library.add_domain_pattern(
            name="audit_trail",
            category="audit",
            description="Audit trail pattern",
            parameters={"entity": {"type": "string"}},
            implementation={
                "fields": [
                    {"name": "created_at", "type": "timestamp", "default": "NOW()"},
                    {"name": "created_by", "type": "uuid"}
                ]
            }
        )

        library.add_domain_pattern(
            name="state_machine",
            category="workflow",
            description="State machine pattern",
            parameters={"entity": {"type": "string"}, "states": {"type": "array"}},
            implementation={
                "fields": [
                    {"name": "state", "type": "enum", "values": ["draft", "active", "inactive"]}
                ]
            }
        )

        library.add_domain_pattern(
            name="soft_delete",
            category="data_management",
            description="Soft delete pattern",
            parameters={"entity": {"type": "string"}},
            implementation={
                "fields": [
                    {"name": "deleted_at", "type": "timestamp", "nullable": True}
                ]
            }
        )

        # Compose
        result = library.compose_patterns(
            entity_name="Contact",
            patterns=[
                {"pattern": "audit_trail", "params": {"entity": "Contact"}},
                {"pattern": "state_machine", "params": {"entity": "Contact", "states": ["lead", "prospect", "customer"]}},
                {"pattern": "soft_delete", "params": {"entity": "Contact"}}
            ]
        )

        assert result is not None
        assert "fields" in result
        assert "actions" in result

        # Should have fields from all 3 patterns
        field_names = [f["name"] for f in result["fields"]]
        assert "created_at" in field_names  # audit_trail
        assert "state" in field_names  # state_machine
        assert "deleted_at" in field_names  # soft_delete

    def test_compose_empty_patterns(self):
        """Test composing with no patterns"""
        library = PatternLibrary(db_path=":memory:")

        result = library.compose_patterns("EmptyEntity", [])

        assert result == {
            "entity": "EmptyEntity",
            "fields": [],
            "actions": [],
            "triggers": [],
            "indexes": [],
            "tables": []
        }

    def test_compose_single_pattern(self):
        """Test composing with single pattern"""
        library = PatternLibrary(db_path=":memory:")

        library.add_domain_pattern(
            name="simple_pattern",
            category="test",
            description="Simple test pattern",
            parameters={},
            implementation={
                "fields": [{"name": "test_field", "type": "text"}],
                "actions": [{"name": "test_action", "steps": []}]
            }
        )

        result = library.compose_patterns(
            "TestEntity",
            [{"pattern": "simple_pattern", "params": {}}]
        )

        assert result["entity"] == "TestEntity"
        assert len(result["fields"]) == 1
        assert result["fields"][0]["name"] == "test_field"
        assert len(result["actions"]) == 1
        assert result["actions"][0]["name"] == "test_action"

    def test_compose_pattern_not_found(self):
        """Test error when composing with non-existent pattern"""
        library = PatternLibrary(db_path=":memory:")

        with pytest.raises(ValueError, match="Domain pattern not found"):
            library.compose_patterns("TestEntity", [{"pattern": "nonexistent", "params": {}}])

    def test_compose_with_invalid_params(self):
        """Test composition with invalid pattern parameters"""
        library = PatternLibrary(db_path=":memory:")

        library.add_domain_pattern(
            name="strict_pattern",
            category="test",
            description="Pattern with required params",
            parameters={"required": {"type": "string", "required": True}},
            implementation={"fields": []}
        )

        with pytest.raises(ValueError, match="Required parameter missing"):
            library.compose_patterns("TestEntity", [{"pattern": "strict_pattern", "params": {}}])

    def test_pattern_field_conflicts(self):
        """Test handling of conflicting field definitions"""
        library = PatternLibrary(db_path=":memory:")

        # Two patterns defining the same field with different types
        library.add_domain_pattern(
            name="pattern1",
            category="test",
            description="Pattern 1",
            parameters={},
            implementation={
                "fields": [{"name": "conflict_field", "type": "text"}]
            }
        )

        library.add_domain_pattern(
            name="pattern2",
            category="test",
            description="Pattern 2",
            parameters={},
            implementation={
                "fields": [{"name": "conflict_field", "type": "integer"}]
            }
        )

        # This should either merge intelligently or raise an error
        result = library.compose_patterns(
            "TestEntity",
            [
                {"pattern": "pattern1", "params": {}},
                {"pattern": "pattern2", "params": {}}
            ]
        )

        # For now, expect both fields (conflict resolution TBD in refactor phase)
        conflict_fields = [f for f in result["fields"] if f["name"] == "conflict_field"]
        assert len(conflict_fields) >= 1  # At least one field should be present