"""Tests for PatternService embedding functionality"""
import pytest
import numpy as np
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)


@pytest.fixture
def service():
    """Create service with in-memory repository"""
    repository = InMemoryPatternRepository()
    return PatternService(repository)


class TestPatternServiceEmbeddings:
    """Test embedding generation in PatternService"""

    def test_create_pattern_with_embedding(self, service):
        """Test creating pattern with auto-generated embedding"""
        pattern = service.create_pattern(
            name="test_email_validation",
            category="validation",
            description="Validates email addresses",
            implementation={"type": "regex", "pattern": r"^[^@]+@[^@]+\.[^@]+$"},
            generate_embedding=True
        )

        assert pattern.embedding is not None
        assert isinstance(pattern.embedding, list)
        assert len(pattern.embedding) == 384

    def test_create_pattern_without_embedding(self, service):
        """Test creating pattern without embedding"""
        pattern = service.create_pattern(
            name="test_pattern_no_embedding",
            category="test",
            description="Test pattern",
            generate_embedding=False
        )

        assert pattern.embedding is None

    def test_embedding_similarity_for_similar_patterns(self, service):
        """Test that similar patterns have similar embeddings"""
        pattern1 = service.create_pattern(
            name="email_validation",
            category="validation",
            description="Validates email addresses using regex",
            generate_embedding=True
        )

        pattern2 = service.create_pattern(
            name="email_check",
            category="validation",
            description="Checks if email address is valid",
            generate_embedding=True
        )

        # Convert to numpy arrays
        emb1 = np.array(pattern1.embedding)
        emb2 = np.array(pattern2.embedding)

        # Calculate cosine similarity
        similarity = float(np.dot(emb1, emb2))

        # Similar patterns should have high similarity
        assert similarity > 0.7