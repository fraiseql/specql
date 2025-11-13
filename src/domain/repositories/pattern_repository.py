"""Pattern Repository Protocol"""
from typing import Protocol, TYPE_CHECKING, List, Tuple, Optional

if TYPE_CHECKING:
    from src.domain.entities.pattern import Pattern

class PatternRepository(Protocol):
    """Repository for Pattern aggregate root"""

    def get(self, pattern_name: str) -> "Pattern":
        """Get pattern by name - raises if not found"""
        ...

    def find_by_category(self, category: str) -> list["Pattern"]:
        """Find patterns by category"""
        ...

    def save(self, pattern: "Pattern") -> None:
        """Save pattern"""
        ...

    def list_all(self) -> list["Pattern"]:
        """List all patterns"""
        ...

    def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_similarity: float = 0.0,
        category: Optional[str] = None,
        include_deprecated: bool = False
    ) -> List[Tuple["Pattern", float]]:
        """
        Search patterns by semantic similarity

        Args:
            query_embedding: Query embedding vector (384-dim)
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold (0-1)
            category: Optional category filter
            include_deprecated: Whether to include deprecated patterns

        Returns:
            List of (Pattern, similarity_score) tuples, sorted by similarity DESC
        """
        ...

    def find_similar_to_pattern(
        self,
        pattern_id: int,
        limit: int = 10,
        min_similarity: float = 0.5,
        include_deprecated: bool = False
    ) -> List[Tuple["Pattern", float]]:
        """
        Find patterns similar to a given pattern

        Args:
            pattern_id: ID of reference pattern
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold
            include_deprecated: Whether to include deprecated patterns

        Returns:
            List of (Pattern, similarity_score) tuples, excluding the reference pattern
        """
        ...

    def find_by_id(self, pattern_id: int) -> Optional["Pattern"]:
        """Find pattern by ID"""
        ...