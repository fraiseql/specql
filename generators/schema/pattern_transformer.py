# Pattern Transformer System
# Provides extensible architecture for applying schema transformations based on patterns

from abc import ABC, abstractmethod
from typing import List
from core.ast_models import Entity, Pattern


class PatternTransformer(ABC):
    """Base class for pattern-based schema transformations.

    Pattern transformers are responsible for modifying generated DDL based on
    detected patterns in entity definitions. Each transformer handles a specific
    pattern type and applies the appropriate schema modifications.
    """

    @abstractmethod
    def applies_to(self, pattern: Pattern) -> bool:
        """Check if this transformer handles the given pattern.

        Args:
            pattern: The pattern to check

        Returns:
            True if this transformer can handle the pattern
        """
        pass

    @abstractmethod
    def transform_ddl(self, entity: Entity, ddl: str, pattern: Pattern) -> str:
        """Apply pattern transformations to generated DDL.

        Args:
            entity: The entity being processed
            ddl: The current DDL string to transform
            pattern: The pattern configuration

        Returns:
            Modified DDL string with pattern transformations applied
        """
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """Transformers with higher priority run first.

        Returns:
            Priority number (higher = runs earlier)
        """
        pass


class PatternTransformerRegistry:
    """Registry for managing pattern transformers."""

    def __init__(self):
        self.transformers: List[PatternTransformer] = []

    def register(self, transformer: PatternTransformer) -> None:
        """Register a pattern transformer."""
        self.transformers.append(transformer)
        # Sort by priority (highest first)
        self.transformers.sort(key=lambda t: t.get_priority(), reverse=True)

    def get_transformers_for_pattern(self, pattern: Pattern) -> List[PatternTransformer]:
        """Get all transformers that can handle the given pattern."""
        return [t for t in self.transformers if t.applies_to(pattern)]

    def get_all_transformers(self) -> List[PatternTransformer]:
        """Get all registered transformers."""
        return self.transformers.copy()
