"""Application Service for Pattern operations"""
from typing import List, Optional, Dict, Any
from src.domain.repositories.pattern_repository import PatternRepository
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType


class PatternService:
    """
    Application Service for Pattern operations

    Uses repository abstraction - doesn't care about storage implementation
    """

    def __init__(self, repository: PatternRepository):
        self.repository = repository

    def create_pattern(
        self,
        name: str,
        category: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        implementation: Optional[Dict[str, Any]] = None,
        complexity_score: Optional[float] = None,
        source_type: str = "manual"
    ) -> Pattern:
        """Create a new pattern"""
        pattern = Pattern(
            id=None,
            name=name,
            category=PatternCategory(category),
            description=description,
            parameters=parameters or {},
            implementation=implementation or {},
            source_type=SourceType(source_type),
            complexity_score=complexity_score
        )

        self.repository.save(pattern)
        return pattern

    def get_pattern(self, name: str) -> Pattern:
        """Get pattern by name"""
        return self.repository.get(name)

    def find_patterns_by_category(self, category: str) -> List[Pattern]:
        """Find patterns by category"""
        return self.repository.find_by_category(category)

    def list_all_patterns(self) -> List[Pattern]:
        """List all patterns"""
        return self.repository.list_all()

    def update_pattern(
        self,
        name: str,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        implementation: Optional[Dict[str, Any]] = None,
        complexity_score: Optional[float] = None
    ) -> Pattern:
        """Update an existing pattern"""
        pattern = self.repository.get(name)

        if description is not None:
            pattern.description = description
        if parameters is not None:
            pattern.parameters = parameters
        if implementation is not None:
            pattern.implementation = implementation
        if complexity_score is not None:
            pattern.complexity_score = complexity_score

        self.repository.save(pattern)
        return pattern

    def deprecate_pattern(self, name: str, reason: str, replacement_pattern: Optional[str] = None) -> None:
        """Mark a pattern as deprecated"""
        pattern = self.repository.get(name)

        replacement_id = None
        if replacement_pattern:
            replacement = self.repository.get(replacement_pattern)
            replacement_id = replacement.id

        pattern.mark_deprecated(reason, replacement_id)
        self.repository.save(pattern)

    def increment_pattern_usage(self, name: str) -> None:
        """Increment usage counter for a pattern"""
        pattern = self.repository.get(name)
        pattern.increment_usage()
        self.repository.save(pattern)

    def find_similar_patterns(self, pattern_name: str, threshold: float = 0.7) -> List[Pattern]:
        """Find patterns similar to the given pattern based on embeddings"""
        target_pattern = self.repository.get(pattern_name)
        if not target_pattern.has_embedding or target_pattern.embedding is None:
            return []

        all_patterns = self.repository.list_all()
        similar = []

        for pattern in all_patterns:
            if pattern.name != pattern_name and pattern.embedding is not None:
                if pattern.is_similar_to(target_pattern.embedding, threshold):
                    similar.append(pattern)

        return similar