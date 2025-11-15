"""
Pattern matching service - detects applicable patterns for entities

Uses FraiseQL 1.5 for semantic pattern matching via GraphQL API.
"""
from typing import List, Tuple, Dict, Any
from src.domain.entities.pattern import Pattern
from src.domain.repositories.pattern_repository import PatternRepository
from src.pattern_library.embeddings_pg import PatternEmbeddingService


class PatternMatcher:
    """
    Matches patterns to entities based on structure and semantics

    Uses multiple signals:
    - Field names (e.g., "email" → email_validation)
    - Field types (e.g., text fields → validation patterns)
    - Entity description (semantic matching via FraiseQL)
    - Pattern popularity (boost frequently used patterns)
    """

    def __init__(self, repository: PatternRepository, fraiseql_url: str = "http://localhost:4000/graphql"):
        self.repository = repository
        self.embedding_service = PatternEmbeddingService(fraiseql_url)

    def find_applicable_patterns(
        self,
        entity_spec: Dict[str, Any],
        limit: int = 5,
        min_confidence: float = 0.5,
        exclude_applied: bool = True,
        use_semantic: bool = True
    ) -> List[Tuple[Pattern, float]]:
        """
        Find patterns applicable to an entity

        Args:
            entity_spec: Entity specification dict
            limit: Maximum patterns to return
            min_confidence: Minimum confidence threshold (0-1)
            exclude_applied: Exclude patterns already applied
            use_semantic: Use semantic matching

        Returns:
            List of (Pattern, confidence) tuples, sorted by confidence DESC
        """
        # Get all non-deprecated patterns
        all_patterns = self.repository.list_all()
        active_patterns = [p for p in all_patterns if not p.deprecated]

        # Exclude already applied patterns
        if exclude_applied and "patterns" in entity_spec:
            applied_pattern_names = set(entity_spec.get("patterns", []))
            active_patterns = [
                p for p in active_patterns
                if p.name not in applied_pattern_names
            ]

        # Calculate confidence for each pattern
        scored_patterns = []
        for pattern in active_patterns:
            confidence = self._calculate_confidence(
                pattern=pattern,
                entity_spec=entity_spec,
                use_semantic=use_semantic
            )

            if confidence >= min_confidence:
                scored_patterns.append((pattern, confidence))

        # Sort by confidence DESC
        scored_patterns.sort(key=lambda x: x[1], reverse=True)

        return scored_patterns[:limit]

    def _calculate_confidence(
        self,
        pattern: Pattern,
        entity_spec: Dict[str, Any],
        use_semantic: bool
    ) -> float:
        """
        Calculate confidence that pattern applies to entity

        Combines multiple signals:
        - Field name matching
        - Field type matching
        - Semantic similarity (if enabled)
        - Pattern popularity

        Returns:
            Confidence score 0.0-1.0
        """
        signals = []

        # Signal 1: Field name matching
        field_name_score = self._field_name_matching(pattern, entity_spec)
        if field_name_score > 0:
            signals.append(("field_names", field_name_score, 0.4))

        # Signal 2: Field type matching
        field_type_score = self._field_type_matching(pattern, entity_spec)
        if field_type_score > 0:
            signals.append(("field_types", field_type_score, 0.3))

        # Signal 3: Semantic similarity
        if use_semantic and entity_spec.get("description"):
            semantic_score = self._semantic_matching(pattern, entity_spec)
            if semantic_score > 0:
                signals.append(("semantic", semantic_score, 0.2))

        # Signal 4: Popularity boost
        popularity_score = self._popularity_score(pattern)
        signals.append(("popularity", popularity_score, 0.1))

        # Weighted average
        if not signals:
            return 0.0

        total_weight = sum(weight for _, _, weight in signals)
        weighted_sum = sum(score * weight for _, score, weight in signals)

        return weighted_sum / total_weight

    def _field_name_matching(
        self,
        pattern: Pattern,
        entity_spec: Dict[str, Any]
    ) -> float:
        """
        Score based on field name matching

        Example:
            Pattern: email_validation
            Entity fields: ["email", "name", "phone"]
            Match: "email" in field names → high score
        """
        fields = entity_spec.get("fields", {})
        field_names = set(fields.keys())

        # Extract keywords from pattern name
        pattern_keywords = self._extract_keywords(pattern.name)

        # Check for keyword matches in field names
        matches = 0
        for keyword in pattern_keywords:
            if any(keyword in field_name.lower() for field_name in field_names):
                matches += 1

        if not pattern_keywords:
            return 0.0

        return min(matches / len(pattern_keywords), 1.0)

    def _field_type_matching(
        self,
        pattern: Pattern,
        entity_spec: Dict[str, Any]
    ) -> float:
        """
        Score based on field type matching

        Example:
            Pattern: email_validation (applies to text fields)
            Entity: has text field
            → Match
        """
        fields = entity_spec.get("fields", {})

        # Get expected field types from pattern parameters
        expected_types = pattern.parameters.get("field_types", [])
        if not expected_types:
            return 0.0

        # Check if entity has fields of expected types
        entity_types = [f.get("type") for f in fields.values()]

        matches = sum(1 for t in expected_types if t in entity_types)

        return matches / len(expected_types) if expected_types else 0.0

    def _semantic_matching(
        self,
        pattern: Pattern,
        entity_spec: Dict[str, Any]
    ) -> float:
        """
        Score based on semantic similarity between entity description and pattern

        Uses embeddings to measure similarity
        """
        description = entity_spec.get("description", "")
        if not description or not pattern.embedding:
            return 0.0

        # Generate embedding for entity description
        entity_embedding = self.embedding_service.generate_embedding(description)

        # Calculate similarity with pattern embedding
        import numpy as np
        pattern_embedding_array = np.array(pattern.embedding)

        similarity = self.embedding_service.cosine_similarity(
            entity_embedding,
            pattern_embedding_array
        )

        # Map [-1, 1] to [0, 1]
        return (similarity + 1) / 2

    def _popularity_score(self, pattern: Pattern) -> float:
        """
        Score based on pattern usage (popularity)

        More popular patterns get slight boost
        """
        # Logarithmic scaling to avoid over-weighting popular patterns
        import math

        if pattern.times_instantiated == 0:
            return 0.3  # Base score for unused patterns

        # Log scale: 1 use = 0.5, 10 uses = 0.7, 100 uses = 0.9
        score = 0.3 + (math.log10(pattern.times_instantiated + 1) / 2.5)

        return min(score, 1.0)

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """
        Extract keywords from pattern name

        Example:
            "email_validation" → ["email", "validation"]
        """
        # Split on underscores and filter short words
        words = text.split("_")
        return [w.lower() for w in words if len(w) >= 3]