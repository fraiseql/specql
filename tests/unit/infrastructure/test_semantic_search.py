"""Tests for semantic search functionality"""

import pytest
from unittest.mock import patch
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository,
)
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType


@pytest.fixture
def service(repository):
    """Create pattern service"""
    from src.application.services.pattern_service import PatternService

    return PatternService(repository, fraiseql_url="http://localhost:4000/graphql")


@pytest.fixture
def repository():
    """Create in-memory repository with test patterns"""

    repo = InMemoryPatternRepository()

    # Create test patterns (embeddings handled by FraiseQL)
    patterns = [
        Pattern(
            id=None,
            name="email_validation",
            category=PatternCategory.VALIDATION,
            description="Validates email addresses using regex patterns",
            parameters={"field_types": ["text", "email"]},
            implementation={
                "sql": "CHECK email ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$)'"
            },
            times_instantiated=15,
            source_type=SourceType.MANUAL,
            complexity_score=3,
        ),
        Pattern(
            id=None,
            name="contact_validation",
            category=PatternCategory.VALIDATION,
            description="Validates contact information including emails and phone numbers",
            parameters={"field_types": ["text", "email", "phone"]},
            implementation={"sql": "Complex validation logic for contact fields"},
            times_instantiated=8,
            source_type=SourceType.MANUAL,
            complexity_score=5,
        ),
        Pattern(
            id=None,
            name="user_registration_workflow",
            category=PatternCategory.WORKFLOW,
            description="Complete user registration process with validation",
            parameters={"steps": ["validate", "create_user", "send_email"]},
            implementation={"workflow": "Multi-step registration process"},
            times_instantiated=25,
            source_type=SourceType.MANUAL,
            complexity_score=8,
        ),
        Pattern(
            id=None,
            name="data_migration",
            category=PatternCategory.WORKFLOW,
            description="Migrates data between different systems",
            parameters={"source": "database", "target": "api"},
            implementation={"workflow": "Extract, transform, load process"},
            times_instantiated=12,
            source_type=SourceType.MANUAL,
            complexity_score=7,
        ),
    ]

    # Save patterns (FraiseQL will auto-generate embeddings)
    for pattern in patterns:
        repo.save(pattern)

    return repo


class TestSemanticSearch:
    """Test semantic search functionality"""

    @patch("src.pattern_library.embeddings_pg.PatternEmbeddingService.retrieve_similar")
    def test_natural_language_search(self, mock_retrieve, service, repository):
        """Test natural language pattern search"""
        # Mock FraiseQL response
        mock_retrieve.return_value = [
            {"pattern_id": 1, "similarity": 0.95},
            {"pattern_id": 2, "similarity": 0.87},
            {"pattern_id": 3, "similarity": 0.72},
        ]

        # User types natural language query
        query = "I need to validate user email addresses"

        # Service handles search
        results = service.search_patterns_semantic(query, limit=5)

        assert len(results) == 3

        # Should find email validation patterns
        for pattern, similarity in results:
            assert isinstance(pattern, Pattern)
            assert 0.7 <= similarity <= 1.0  # Reasonable similarity range

        # Verify FraiseQL was called correctly
        mock_retrieve.assert_called_once_with(
            query_text=query, top_k=5, threshold=0.5, category_filter=None
        )

    @patch("src.pattern_library.embeddings_pg.PatternEmbeddingService.retrieve_similar")
    def test_search_with_category_filter(self, mock_retrieve, service):
        """Test semantic search with category filtering"""
        mock_retrieve.return_value = [{"pattern_id": 1, "similarity": 0.92}]

        results = service.search_patterns_semantic(
            "validate emails", limit=3, category="validation"
        )

        assert len(results) == 1
        mock_retrieve.assert_called_once_with(
            query_text="validate emails",
            top_k=3,
            threshold=0.5,
            category_filter="validation",
        )

    @patch("src.pattern_library.embeddings_pg.PatternEmbeddingService.retrieve_similar")
    def test_search_with_min_similarity_threshold(self, mock_retrieve, service):
        """Test filtering results by minimum similarity"""
        # Mock responses for different thresholds
        mock_retrieve.side_effect = [
            # High threshold call
            [{"pattern_id": 1, "similarity": 0.95}],
            # Low threshold call
            [
                {"pattern_id": 1, "similarity": 0.95},
                {"pattern_id": 2, "similarity": 0.78},
                {"pattern_id": 3, "similarity": 0.65},
            ],
        ]

        # Search with high threshold
        results_high = service.search_patterns_semantic(
            "database connection pooling",
            limit=10,
            min_similarity=0.8,  # High threshold
        )

        # Search with low threshold
        results_low = service.search_patterns_semantic(
            "database connection pooling",
            limit=10,
            min_similarity=0.3,  # Low threshold
        )

        # Low threshold should return more results
        assert len(results_low) >= len(results_high)

        # All high-threshold results should have similarity >= 0.8
        for _, similarity in results_high:
            assert similarity >= 0.8

    @patch("src.pattern_library.embeddings_pg.PatternEmbeddingService.retrieve_similar")
    def test_find_similar_patterns(self, mock_retrieve, service, repository):
        """Test finding patterns similar to a given pattern"""
        # Mock FraiseQL response for pattern similarity
        mock_retrieve.return_value = [
            {"pattern_id": 2, "similarity": 0.88},
            {"pattern_id": 3, "similarity": 0.76},
        ]

        # Get a pattern to find similar ones for
        base_pattern = repository.get_all()[0]  # Get first pattern

        # Find similar patterns
        similar = service.find_similar_patterns(pattern_id=base_pattern.id, limit=5)

        assert len(similar) == 2

        # Should not include the original pattern
        for pattern, _ in similar:
            assert pattern.id != base_pattern.id

        # Should be semantically similar
        for pattern, similarity in similar:
            assert similarity > 0.7
