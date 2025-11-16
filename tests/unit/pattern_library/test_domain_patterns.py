"""Tests for domain pattern storage and instantiation (Tier 2)"""

import pytest
from src.pattern_library.api import PatternLibrary


class TestDomainPatterns:
    """Test domain pattern functionality"""

    def test_add_domain_pattern(self):
        """Test adding a domain pattern"""
        library = PatternLibrary(db_path=":memory:")

        pattern_id = library.add_domain_pattern(
            name="state_machine",
            category="workflow",
            description="State machine pattern with transitions",
            parameters={
                "entity": {"type": "string", "required": True},
                "states": {"type": "array", "required": True},
                "transitions": {"type": "object", "required": True},
                "guards": {"type": "object", "required": False},
            },
            implementation={
                "actions": [
                    {
                        "name": "transition_to_{state}",
                        "steps": [
                            {
                                "type": "query",
                                "sql": "SELECT state FROM tb_{entity} WHERE id = $id",
                            },
                            {
                                "type": "validate",
                                "condition": "state IN allowed_states",
                            },
                            {"type": "validate", "condition": "transition_allowed"},
                            {
                                "type": "update",
                                "entity": "{entity}",
                                "fields": {"state": "{target_state}"},
                            },
                            {
                                "type": "insert",
                                "entity": "{entity}_audit",
                                "fields": {"transition": "...", "timestamp": "NOW()"},
                            },
                        ],
                    }
                ]
            },
        )

        assert pattern_id > 0

        # Retrieve
        pattern = library.get_domain_pattern("state_machine")
        assert pattern is not None
        assert pattern["pattern_name"] == "state_machine"
        assert pattern["pattern_category"] == "workflow"

    def test_instantiate_domain_pattern(self):
        """Test instantiating a domain pattern for an entity"""
        library = PatternLibrary(db_path=":memory:")

        # Add pattern
        library.add_domain_pattern(
            name="audit_trail",
            category="audit",
            description="Automatic audit trail",
            parameters={"entity": {"type": "string"}},
            implementation={
                "fields": [
                    {"name": "created_at", "type": "timestamp", "default": "NOW()"},
                    {"name": "created_by", "type": "uuid"},
                    {"name": "updated_at", "type": "timestamp", "default": "NOW()"},
                    {"name": "updated_by", "type": "uuid"},
                    {"name": "version", "type": "integer", "default": 1},
                ],
                "triggers": [{"event": "before_update", "action": "increment_version"}],
            },
        )

        # Instantiate for Contact entity
        result = library.instantiate_domain_pattern(
            pattern_name="audit_trail",
            entity_name="Contact",
            parameters={"entity": "Contact"},
        )

        assert result is not None
        assert "fields" in result
        assert len(result["fields"]) == 5
        assert result["fields"][0]["name"] == "created_at"

    def test_get_all_domain_patterns(self):
        """Test retrieving all domain patterns"""
        library = PatternLibrary(db_path=":memory:")

        # Add multiple patterns
        library.add_domain_pattern("pattern1", "workflow", "desc1", {}, {})
        library.add_domain_pattern("pattern2", "audit", "desc2", {}, {})
        library.add_domain_pattern("pattern3", "workflow", "desc3", {}, {})

        # Get all
        all_patterns = library.get_all_domain_patterns()
        assert len(all_patterns) == 3

        # Get by category
        workflow_patterns = library.get_all_domain_patterns("workflow")
        assert len(workflow_patterns) == 2
        assert all(p["pattern_category"] == "workflow" for p in workflow_patterns)

    def test_domain_pattern_not_found(self):
        """Test error handling for non-existent patterns"""
        library = PatternLibrary(db_path=":memory:")

        pattern = library.get_domain_pattern("nonexistent")
        assert pattern is None

        with pytest.raises(ValueError, match="Domain pattern not found"):
            library.instantiate_domain_pattern("nonexistent", "TestEntity", {})

    def test_invalid_pattern_parameters(self):
        """Test validation of pattern parameters"""
        library = PatternLibrary(db_path=":memory:")

        library.add_domain_pattern(
            name="test_pattern",
            category="test",
            description="Test pattern",
            parameters={
                "required_param": {"type": "string", "required": True},
                "optional_param": {"type": "string", "required": False},
            },
            implementation={},
        )

        # Missing required parameter
        with pytest.raises(ValueError, match="Required parameter missing"):
            library.instantiate_domain_pattern(
                "test_pattern", "TestEntity", {"optional_param": "value"}
            )
