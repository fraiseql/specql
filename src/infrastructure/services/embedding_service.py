"""Service for generating text embeddings using sentence-transformers"""
import numpy as np
from typing import List, Optional
from functools import lru_cache
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Service for generating semantic embeddings from text

    Uses sentence-transformers with all-MiniLM-L6-v2 model:
    - 384-dimensional embeddings
    - Fast inference (~5ms per text)
    - Good quality for semantic similarity
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service

        Args:
            model_name: Sentence-transformers model name
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = 384  # all-MiniLM-L6-v2 dimension

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            384-dimensional numpy array (float32)

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Generate embedding
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,  # L2 normalization for cosine similarity
            show_progress_bar=False
        )

        return np.array(embedding).astype(np.float32)

    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for batch of texts

        Args:
            texts: List of texts to embed

        Returns:
            (N, 384) numpy array where N = len(texts)

        Raises:
            ValueError: If batch is empty
        """
        if not texts:
            raise ValueError("Batch cannot be empty")

        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("All texts in batch are empty")

        # Generate embeddings
        embeddings = self.model.encode(
            valid_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32  # Process in batches of 32
        )

        return np.array(embeddings).astype(np.float32)

    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            emb1: First embedding
            emb2: Second embedding

        Returns:
            Similarity score between -1 and 1 (1 = identical)
        """
        # For normalized vectors, cosine similarity = dot product
        return float(np.dot(emb1, emb2))

    @staticmethod
    def embedding_to_list(embedding: np.ndarray) -> List[float]:
        """
        Convert numpy embedding to list for PostgreSQL

        Args:
            embedding: Numpy array

        Returns:
            List of floats
        """
        return embedding.tolist()

    def create_pattern_embedding(
        self,
        pattern_name: str,
        description: str,
        implementation: Optional[str] = None,
        category: Optional[str] = None
    ) -> np.ndarray:
        """
        Create embedding for a pattern combining multiple components

        Args:
            pattern_name: Pattern name
            description: Pattern description
            implementation: Optional implementation details
            category: Optional category

        Returns:
            384-dimensional embedding
        """
        # Combine components with weights
        components = [
            pattern_name,  # Name is important
            description,   # Description is most important
        ]

        if implementation:
            components.append(implementation)

        if category:
            components.append(f"category: {category}")

        # Join with spaces
        text = " ".join(components)

        return self.generate_embedding(text)


# Singleton instance for reuse across application
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get singleton embedding service instance

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service