"""
In-Memory Pattern Repository

For testing and development without database dependencies.
"""

from typing import List, Dict, Tuple, Optional
import math
from src.domain.repositories.pattern_repository import PatternRepository
from src.domain.entities.pattern import Pattern
from datetime import datetime


class InMemoryPatternRepository(PatternRepository):
    """In-memory implementation of PatternRepository for testing"""

    def __init__(self):
        self._patterns: Dict[str, Pattern] = {}
        self._next_id = 1

    def get(self, pattern_name: str) -> Pattern:
        """Get pattern by name"""
        if pattern_name not in self._patterns:
            raise ValueError(f"Pattern {pattern_name} not found")
        return self._patterns[pattern_name]

    def find_by_category(self, category: str) -> List[Pattern]:
        """Find patterns by category"""
        return [
            pattern for pattern in self._patterns.values()
            if pattern.category.value == category
        ]

    def save(self, pattern: Pattern) -> None:
        """Save pattern (insert or update)"""
        if pattern.id is None:
            pattern.id = self._next_id
            self._next_id += 1

        if pattern.created_at is None:
            pattern.created_at = datetime.now()

        pattern.updated_at = datetime.now()
        self._patterns[pattern.name] = pattern

    def list_all(self) -> List[Pattern]:
        """List all patterns"""
        return list(self._patterns.values())

    def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_similarity: float = 0.0,
        category: Optional[str] = None,
        include_deprecated: bool = False
    ) -> List[Tuple[Pattern, float]]:
        """
        Search patterns by semantic similarity (in-memory implementation)
        """
        results = []

        for pattern in self._patterns.values():
            # Skip if no embedding
            if not pattern.embedding:
                continue

            # Skip deprecated unless requested
            if not include_deprecated and pattern.deprecated:
                continue

            # Skip if category filter doesn't match
            if category and pattern.category.value != category:
                continue

            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, pattern.embedding)

            # Skip if below threshold
            if similarity < min_similarity:
                continue

            results.append((pattern, similarity))

        # Sort by similarity descending and limit
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def find_similar_to_pattern(
        self,
        pattern_id: int,
        limit: int = 10,
        min_similarity: float = 0.5,
        include_deprecated: bool = False
    ) -> List[Tuple[Pattern, float]]:
        """
        Find patterns similar to a given pattern
        """
        # Find reference pattern
        reference_pattern = None
        for pattern in self._patterns.values():
            if pattern.id == pattern_id:
                reference_pattern = pattern
                break

        if not reference_pattern or not reference_pattern.embedding:
            return []

        # Search using reference embedding
        results = self.search_by_similarity(
            query_embedding=reference_pattern.embedding,
            limit=limit + 1,  # +1 to account for filtering out self
            min_similarity=min_similarity,
            include_deprecated=include_deprecated
        )

        # Filter out the reference pattern itself
        filtered = [
            (p, sim) for p, sim in results
            if p.id != pattern_id
        ]

        return filtered[:limit]

    def find_by_id(self, pattern_id: int) -> Optional[Pattern]:
        """Find pattern by ID"""
        for pattern in self._patterns.values():
            if pattern.id == pattern_id:
                return pattern
        return None

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)