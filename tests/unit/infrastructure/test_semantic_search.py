"""Tests for semantic search functionality"""
import pytest
import os
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)
from src.application.services.pattern_service import PatternService
from src.infrastructure.services.embedding_service import get_embedding_service


@pytest.fixture
def db_url():
    """Get database URL"""
    return os.getenv("SPECQL_DB_URL", "postgresql://specql_user:specql_dev_password@localhost/specql")


@pytest.fixture
def repository(db_url):
    """Create PostgreSQL repository"""
    return PostgreSQLPatternRepository(db_url)


@pytest.fixture
def service(repository):
    """Create pattern service"""
    return PatternService(repository)


@pytest.fixture
def embedding_service():
    """Get embedding service"""
    return get_embedding_service()


class TestSemanticSearch:
    """Test semantic search functionality"""

    def test_search_by_similarity(self, repository, embedding_service):
        """Test finding patterns by semantic similarity"""
        # Create query embedding
        query_text = "validate email addresses"
        query_embedding = embedding_service.generate_embedding(query_text)
        query_list = embedding_service.embedding_to_list(query_embedding)

        # Search
        results = repository.search_by_similarity(
            query_embedding=query_list,
            limit=5,
            min_similarity=0.5
        )

        # Should find patterns
        assert len(results) > 0

        # Results should be tuples of (Pattern, similarity_score)
        for pattern, similarity in results:
            assert pattern.embedding is not None
            assert 0.0 <= similarity <= 1.0
            # Should be relevant to email validation
            assert any(
                keyword in pattern.name.lower() or keyword in pattern.description.lower()
                for keyword in ["email", "validation", "contact"]
            )

        # Results should be sorted by similarity (descending)
        similarities = [sim for _, sim in results]
        assert similarities == sorted(similarities, reverse=True)

    def test_search_with_min_similarity_threshold(self, repository, embedding_service):
        """Test filtering results by minimum similarity"""
        query_text = "database connection pooling"
        query_embedding = embedding_service.generate_embedding(query_text)
        query_list = embedding_service.embedding_to_list(query_embedding)

        # Search with high threshold
        results_high = repository.search_by_similarity(
            query_embedding=query_list,
            limit=10,
            min_similarity=0.8  # High threshold
        )

        # Search with low threshold
        results_low = repository.search_by_similarity(
            query_embedding=query_list,
            limit=10,
            min_similarity=0.3  # Low threshold
        )

        # Low threshold should return more results
        assert len(results_low) >= len(results_high)

        # All high-threshold results should have similarity >= 0.8
        for _, similarity in results_high:
            assert similarity >= 0.8

    def test_natural_language_search(self, service):
        """Test natural language pattern search"""
        # User types natural language query
        query = "I need to validate user email addresses"

        # Service handles search
        results = service.search_patterns_semantic(query, limit=5)

        assert len(results) > 0

        # Should find email validation patterns
        for pattern, similarity in results:
            print(f"{pattern.name}: {similarity:.3f}")
            assert similarity > 0.5  # Reasonable threshold

    def test_find_similar_patterns(self, service, repository):
        """Test finding patterns similar to a given pattern"""
        # Get a pattern
        email_pattern = repository.find_by_id(1)  # Assuming pattern with ID 1 exists
        if email_pattern and email_pattern.embedding:
            # Find similar patterns
            similar = service.find_similar_patterns(
                pattern_id=email_pattern.id,
                limit=5
            )

            assert len(similar) > 0

            # Should not include the original pattern
            for pattern, _ in similar:
                assert pattern.id != email_pattern.id

            # Should be semantically similar
            for pattern, similarity in similar:
                assert similarity > 0.5