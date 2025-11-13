"""Tests for EmbeddingService"""
import pytest
import numpy as np
from src.infrastructure.services.embedding_service import EmbeddingService


@pytest.fixture
def service():
    """Create embedding service"""
    return EmbeddingService(model_name="all-MiniLM-L6-v2")


class TestEmbeddingService:
    """Test embedding generation service"""

    def test_service_initialization(self, service):
        """Test service initializes successfully"""
        assert service.model is not None
        assert service.model_name == "all-MiniLM-L6-v2"
        assert service.embedding_dimension == 384

    def test_generate_embedding_single_text(self, service):
        """Test generating embedding for single text"""
        text = "Email validation pattern for user input"
        embedding = service.generate_embedding(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32

    def test_generate_embedding_batch(self, service):
        """Test generating embeddings for batch of texts"""
        texts = [
            "Email validation pattern",
            "Phone number validation",
            "Address validation"
        ]
        embeddings = service.generate_embeddings_batch(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, 384)
        assert embeddings.dtype == np.float32

    def test_embedding_similarity(self, service):
        """Test that similar texts have similar embeddings"""
        text1 = "Email validation pattern"
        text2 = "Email address validation"
        text3 = "Database connection pooling"

        emb1 = service.generate_embedding(text1)
        emb2 = service.generate_embedding(text2)
        emb3 = service.generate_embedding(text3)

        # Cosine similarity
        sim_1_2 = service.cosine_similarity(emb1, emb2)
        sim_1_3 = service.cosine_similarity(emb1, emb3)

        # Similar texts should have higher similarity
        assert sim_1_2 > sim_1_3
        assert sim_1_2 > 0.7  # Threshold for similar texts

    def test_embedding_normalization(self, service):
        """Test that embeddings are normalized"""
        text = "Test pattern"
        embedding = service.generate_embedding(text)

        # L2 norm should be close to 1.0 for normalized vectors
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01

    def test_empty_text_handling(self, service):
        """Test handling of empty text"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.generate_embedding("")

    def test_batch_empty_list(self, service):
        """Test handling of empty batch"""
        with pytest.raises(ValueError, match="Batch cannot be empty"):
            service.generate_embeddings_batch([])

    def test_caching(self, service):
        """Test that identical texts return cached embeddings"""
        text = "Cached pattern"

        # Generate twice
        emb1 = service.generate_embedding(text)
        emb2 = service.generate_embedding(text)

        # Should be identical (cached)
        assert np.array_equal(emb1, emb2)

    def test_pattern_embedding_content(self, service):
        """Test embedding generation from pattern components"""
        # Pattern metadata
        pattern_name = "email_validation"
        description = "Validates email addresses using regex"
        implementation = "REGEXP MATCH email against RFC 5322"

        # Combine for embedding
        text = f"{pattern_name} {description} {implementation}"
        embedding = service.generate_embedding(text)

        assert embedding.shape == (384,)

    def test_embedding_to_list(self, service):
        """Test converting embedding to list for PostgreSQL"""
        text = "Test pattern"
        embedding = service.generate_embedding(text)

        embedding_list = service.embedding_to_list(embedding)

        assert isinstance(embedding_list, list)
        assert len(embedding_list) == 384
        assert all(isinstance(x, float) for x in embedding_list)