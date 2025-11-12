"""
In-Memory Pattern Repository

For testing and development without database dependencies.
"""

from typing import List, Dict, Any
from src.domain.repositories.pattern_repository import PatternRepository
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType
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