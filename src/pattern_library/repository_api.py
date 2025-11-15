"""
Repository-based PatternLibrary API

This is the new PatternLibrary that uses the repository pattern for better
architecture, testability, and storage abstraction.
"""

from typing import Any, Dict, List, Optional
from functools import lru_cache
from jinja2 import Template

from src.application.services.pattern_service import PatternService


class RepositoryPatternLibrary:
    """Repository-based pattern library for multi-language code generation"""

    def __init__(self, pattern_service: PatternService):
        """
        Initialize pattern library with repository pattern

        Args:
            pattern_service: PatternService instance with configured repository
        """
        self.pattern_service = pattern_service

    # ===== Pattern Management =====

    def add_pattern(
        self,
        name: str,
        category: str,
        abstract_syntax: Dict[str, Any],
        description: str = "",
        complexity_score: int = 1
    ) -> int:
        """Add a pattern to the library"""
        pattern = self.pattern_service.create_pattern(
            name=name,
            category=category,
            description=description,
            parameters=abstract_syntax,
            complexity_score=float(complexity_score),
            source_type="manual"
        )
        return pattern.id or 0

    @lru_cache(maxsize=128)
    def get_pattern(self, name: str) -> Optional[Dict[str, Any]]:
        """Get pattern by name"""
        try:
            pattern = self.pattern_service.get_pattern(name)
            return {
                'pattern_name': pattern.name,
                'pattern_category': pattern.category.value,
                'abstract_syntax': pattern.parameters,
                'description': pattern.description,
                'complexity_score': pattern.complexity_score
            }
        except ValueError:
            return None

    def list_patterns(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all patterns, optionally filtered by category"""
        if category:
            patterns = self.pattern_service.find_patterns_by_category(category)
        else:
            patterns = self.pattern_service.list_all_patterns()

        return [{
            'pattern_name': p.name,
            'pattern_category': p.category.value,
            'abstract_syntax': p.parameters,
            'description': p.description,
            'complexity_score': p.complexity_score
        } for p in patterns]

    def update_pattern(
        self,
        name: str,
        abstract_syntax: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        complexity_score: Optional[int] = None
    ) -> None:
        """Update an existing pattern"""
        self.pattern_service.update_pattern(
            name=name,
            parameters=abstract_syntax,
            description=description,
            complexity_score=float(complexity_score) if complexity_score else None
        )

    def deprecate_pattern(self, name: str, reason: str, replacement: Optional[str] = None) -> None:
        """Mark a pattern as deprecated"""
        self.pattern_service.deprecate_pattern(name, reason, replacement)

    def increment_usage(self, name: str) -> None:
        """Increment usage counter for a pattern"""
        self.pattern_service.increment_pattern_usage(name)

    # ===== Implementation Management =====

    def add_implementation(
        self,
        pattern_name: str,
        language_name: str,
        template: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an implementation for a pattern"""
        pattern = self.pattern_service.get_pattern(pattern_name)

        # Store implementation in pattern's implementation dict
        if 'implementations' not in pattern.implementation:
            pattern.implementation['implementations'] = {}

        pattern.implementation['implementations'][language_name] = {
            'template': template,
            'metadata': metadata or {}
        }

        self.pattern_service.update_pattern(
            name=pattern_name,
            implementation=pattern.implementation
        )

    def get_implementation(self, pattern_name: str, language_name: str) -> Optional[Dict[str, Any]]:
        """Get implementation for a pattern and language"""
        pattern = self.pattern_service.get_pattern(pattern_name)
        implementations = pattern.implementation.get('implementations', {})
        return implementations.get(language_name)

    # ===== Compilation =====

    def compile_pattern(
        self,
        pattern_name: str,
        language_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Compile a pattern with given context"""
        self.pattern_service.get_pattern(pattern_name)
        implementation = self.get_implementation(pattern_name, language_name)

        if not implementation:
            raise ValueError(f"No implementation found for pattern '{pattern_name}' in language '{language_name}'")

        template = Template(implementation['template'])
        return template.render(**context)

    # ===== Advanced Features =====

    def find_similar_patterns(self, pattern_name: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find patterns similar to the given pattern"""
        similar_patterns = self.pattern_service.find_similar_patterns(pattern_name, threshold)

        return [{
            'pattern_name': p.name,
            'pattern_category': p.category.value,
            'description': p.description,
            'similarity': 0.0  # Would need to calculate this properly
        } for p in similar_patterns]

    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get statistics about the pattern library"""
        all_patterns = self.pattern_service.list_all_patterns()

        stats = {
            'total_patterns': len(all_patterns),
            'categories': {},
            'active_patterns': 0,
            'deprecated_patterns': 0,
            'total_usage': 0
        }

        for pattern in all_patterns:
            # Count by category
            category = pattern.category.value
            stats['categories'][category] = stats['categories'].get(category, 0) + 1

            # Count active/deprecated
            if pattern.is_active:
                stats['active_patterns'] += 1
            else:
                stats['deprecated_patterns'] += 1

            # Sum usage
            stats['total_usage'] += pattern.times_instantiated

        return stats