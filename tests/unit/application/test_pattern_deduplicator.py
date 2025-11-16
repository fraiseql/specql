"""Tests for pattern deduplication"""

import pytest
from src.application.services.pattern_deduplicator import PatternDeduplicator
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository,
)
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType


@pytest.fixture
def service_with_duplicates():
    """Create service with duplicate patterns"""
    repository = InMemoryPatternRepository()
    service = PatternService(repository)

    # Add similar patterns (potential duplicates)
    patterns = [
        Pattern(
            id=None,
            name="email_validation",
            category=PatternCategory.VALIDATION,
            description="Validates email addresses using RFC 5322",
            implementation={"sql": "REGEXP check"},
            times_instantiated=10,
            source_type=SourceType.MANUAL,
            complexity_score=3,
        ),
        Pattern(
            id=None,
            name="email_validator",
            category=PatternCategory.VALIDATION,
            description="Validates email addresses using RFC 5322 regex",
            implementation={"sql": "REGEXP validation"},
            times_instantiated=5,
            source_type=SourceType.MIGRATED,
            complexity_score=3,
        ),
        Pattern(
            id=None,
            name="phone_validation",
            category=PatternCategory.VALIDATION,
            description="Validates phone numbers",
            implementation={"sql": "Phone format check"},
            times_instantiated=8,
            source_type=SourceType.MANUAL,
            complexity_score=2,
        ),
    ]

    for pattern in patterns:
        repository.save(pattern)

    return service


@pytest.fixture
def deduplicator(service_with_duplicates):
    """Create deduplicator"""
    return PatternDeduplicator(service_with_duplicates)


class TestPatternDeduplicator:
    """Test pattern deduplication"""

    def test_find_duplicates(self, deduplicator):
        """Test finding duplicate patterns"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        # Should find email_validation and email_validator as duplicates
        assert len(duplicates) > 0

        # Check structure
        for group in duplicates:
            assert len(group) >= 2  # At least 2 patterns in duplicate group
            assert all(isinstance(p, Pattern) for p in group)

    def test_find_duplicates_high_threshold(self, deduplicator):
        """Test finding duplicates with high similarity threshold"""
        # Very high threshold should find fewer duplicates
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.99)

        # May not find any at this threshold
        assert isinstance(duplicates, list)

    def test_suggest_merge_candidates(self, deduplicator):
        """Test suggesting which patterns to keep vs merge"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        if duplicates:
            group = duplicates[0]
            suggestion = deduplicator.suggest_merge(group)

            assert "keep" in suggestion
            assert "merge" in suggestion
            assert suggestion["keep"] in group
            assert all(p in group for p in suggestion["merge"])

    def test_merge_strategy_most_used(self, deduplicator):
        """Test merge strategy: keep most used pattern"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        if duplicates:
            group = duplicates[0]
            suggestion = deduplicator.suggest_merge(group, strategy="most_used")

            # Should keep the pattern with most uses
            kept = suggestion["keep"]
            for pattern in suggestion["merge"]:
                assert kept.times_instantiated >= pattern.times_instantiated

    def test_merge_strategy_oldest(self, deduplicator):
        """Test merge strategy: keep oldest (manual) pattern"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        if duplicates:
            group = duplicates[0]
            suggestion = deduplicator.suggest_merge(group, strategy="oldest")

            # Should prefer manual over migrated
            kept = suggestion["keep"]
            assert kept.source_type == SourceType.MANUAL

    def test_merge_patterns(self, deduplicator, service_with_duplicates):
        """Test actually merging patterns"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        if duplicates:
            group = duplicates[0]
            suggestion = deduplicator.suggest_merge(group)

            # Perform merge
            merged = deduplicator.merge_patterns(
                keep=suggestion["keep"], merge=suggestion["merge"]
            )

            # Verify
            assert merged.name == suggestion["keep"].name

            # Merged patterns should be marked as deprecated
            for pattern in suggestion["merge"]:
                deprecated = service_with_duplicates.get_pattern_by_name(pattern.name)
                assert deprecated.deprecated
                assert deprecated.replacement_pattern_id == merged.id

    def test_calculate_pattern_similarity(self, deduplicator):
        """Test similarity calculation between patterns"""
        patterns = list(deduplicator.service.repository.list_all())

        if len(patterns) >= 2:
            similarity = deduplicator.calculate_similarity(patterns[0], patterns[1])

            assert 0.0 <= similarity <= 1.0
