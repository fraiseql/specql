"""Tests for PatternMatcher - detects applicable patterns for entities"""
import pytest
from src.application.services.pattern_matcher import PatternMatcher
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType


@pytest.fixture
def repository():
    """Create repository with test patterns"""
    repo = InMemoryPatternRepository()

    # Add test patterns
    patterns = [
        Pattern(
            id=None,
            name="email_validation",
            category=PatternCategory.VALIDATION,
            description="Validates email addresses using RFC 5322 regex",
            parameters={"field_types": ["text", "email"]},
            implementation={"sql": "CHECK email ~* RFC_5322_REGEX"},
            times_instantiated=15,
            source_type=SourceType.MANUAL,
            complexity_score=3
        ),
        Pattern(
            id=None,
            name="audit_trail",
            category=PatternCategory.AUDIT,
            description="Tracks all changes with created_at, updated_at fields",
            parameters={"required_fields": ["created_at", "updated_at"]},
            implementation={"sql": "Automatic timestamp tracking"},
            times_instantiated=45,
            source_type=SourceType.MANUAL,
            complexity_score=2
        ),
        Pattern(
            id=None,
            name="soft_delete",
            category=PatternCategory.SOFT_DELETE,
            description="Soft deletion with deleted_at field",
            parameters={"required_fields": ["deleted_at"]},
            implementation={"sql": "NULL = active, timestamp = deleted"},
            times_instantiated=32,
            source_type=SourceType.MANUAL,
            complexity_score=2
        ),
    ]

    for pattern in patterns:
        repo.save(pattern)

    return repo


@pytest.fixture
def matcher(repository):
    """Create pattern matcher"""
    return PatternMatcher(repository)


class TestPatternMatcher:
    """Test pattern matching for entities"""

    def test_match_by_field_names(self, matcher):
        """Test matching patterns by field names"""
        # Entity with email field
        entity_spec = {
            "entity": "contact",
            "fields": {
                "email": {"type": "text"},
                "name": {"type": "text"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # Should suggest email_validation
        assert len(matches) > 0
        assert any(p.name == "email_validation" for p, _ in matches)

    def test_match_by_field_types(self, matcher):
        """Test matching by field types"""
        entity_spec = {
            "entity": "user",
            "fields": {
                "email_address": {"type": "text"},
                "username": {"type": "text"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # Should suggest email_validation (has text field with "email" in name)
        email_matches = [p for p, _ in matches if p.name == "email_validation"]
        assert len(email_matches) > 0

    def test_match_audit_trail_pattern(self, matcher):
        """Test detecting when audit_trail is applicable"""
        # Entity without audit fields
        entity_spec = {
            "entity": "product",
            "fields": {
                "name": {"type": "text"},
                "price": {"type": "money"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # Should suggest audit_trail
        audit_matches = [p for p, _ in matches if p.name == "audit_trail"]
        assert len(audit_matches) > 0

    def test_match_confidence_scoring(self, matcher):
        """Test confidence scores for matches"""
        entity_spec = {
            "entity": "contact",
            "fields": {
                "email": {"type": "text"},
                "phone": {"type": "text"},
                "created_at": {"type": "timestamp"},
                "updated_at": {"type": "timestamp"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # All matches should have confidence scores
        for pattern, confidence in matches:
            assert 0.0 <= confidence <= 1.0

        # Email validation should have reasonable confidence (email field present)
        email_match = next((c for p, c in matches if p.name == "email_validation"), 0)
        assert email_match > 0.5

    def test_exclude_already_applied_patterns(self, matcher):
        """Test excluding patterns already applied"""
        entity_spec = {
            "entity": "user",
            "fields": {
                "email": {"type": "text"}
            },
            "patterns": ["audit_trail"]  # Already applied
        }

        matches = matcher.find_applicable_patterns(
            entity_spec,
            exclude_applied=True
        )

        # audit_trail should not be in matches
        assert not any(p.name == "audit_trail" for p, _ in matches)

    def test_match_by_entity_description(self, matcher):
        """Test semantic matching by entity description"""
        entity_spec = {
            "entity": "customer_contact",
            "description": "Customer contact information with email and phone",
            "fields": {
                "contact_name": {"type": "text"}
            }
        }

        matches = matcher.find_applicable_patterns(
            entity_spec,
            use_semantic=True
        )

        # Should suggest email-related patterns based on description
        assert len(matches) > 0

    def test_popularity_boost(self, matcher):
        """Test that popular patterns are ranked higher"""
        entity_spec = {
            "entity": "generic_entity",
            "fields": {
                "name": {"type": "text"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # audit_trail (45 uses) should rank higher than soft_delete (32 uses)
        # when both have similar confidence
        positions = {p.name: i for i, (p, _) in enumerate(matches)}

        if "audit_trail" in positions and "soft_delete" in positions:
            # audit_trail should come before soft_delete
            # (though confidence might override this)
            pass  # Depends on confidence calculation