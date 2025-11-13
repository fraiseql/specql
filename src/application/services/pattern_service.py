"""Application Service for Pattern operations"""
from typing import List, Optional, Dict, Any, Tuple
from src.domain.repositories.pattern_repository import PatternRepository
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType
from src.infrastructure.services.embedding_service import get_embedding_service


class PatternService:
    """
    Application Service for Pattern operations

    Uses repository abstraction - doesn't care about storage implementation
    """

    def __init__(self, repository: PatternRepository):
        self.repository = repository
        self.embedding_service = get_embedding_service()

    def create_pattern(
        self,
        name: str,
        category: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        implementation: Optional[Dict[str, Any]] = None,
        complexity_score: Optional[float] = None,
        source_type: str = "manual",
        generate_embedding: bool = True  # New parameter
    ) -> Pattern:
        """
        Create a new pattern

        Args:
            name: Pattern name
            category: Pattern category
            description: Pattern description
            parameters: Pattern parameters
            implementation: Implementation details
            complexity_score: Complexity (0-10)
            source_type: Source type
            generate_embedding: Whether to auto-generate embedding

        Returns:
            Created Pattern
        """
        # Generate embedding if requested
        embedding = None
        if generate_embedding:
            embedding_vector = self.embedding_service.create_pattern_embedding(
                pattern_name=name,
                description=description,
                implementation=str(implementation) if implementation else "",
                category=category
            )
            embedding = self.embedding_service.embedding_to_list(embedding_vector)

        pattern = Pattern(
            id=None,
            name=name,
            category=PatternCategory(category),
            description=description,
            parameters=parameters or {},
            implementation=implementation or {},
            embedding=embedding,
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

    def search_patterns_semantic(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5,
        category: Optional[str] = None
    ) -> List[Tuple[Pattern, float]]:
        """
        Search patterns using natural language query

        Args:
            query: Natural language search query
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold (0-1)
            category: Optional category filter

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> results = service.search_patterns_semantic(
            ...     "validate email addresses",
            ...     limit=5
            ... )
            >>> for pattern, similarity in results:
            ...     print(f"{pattern.name}: {similarity:.2%}")
        """
        # Generate embedding for query
        query_embedding_vector = self.embedding_service.generate_embedding(query)
        query_embedding = self.embedding_service.embedding_to_list(query_embedding_vector)

        # Search using repository method (to be implemented)
        return self.repository.search_by_similarity(
            query_embedding=query_embedding,
            limit=limit,
            min_similarity=min_similarity,
            category=category,
            include_deprecated=False
        )

    def find_similar_patterns(
        self,
        pattern_id: int,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Tuple[Pattern, float]]:
        """
        Find patterns similar to a given pattern

        Args:
            pattern_id: ID of reference pattern
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> email_pattern = service.get_pattern_by_name("email_validation")
            >>> similar = service.find_similar_patterns(
            ...     email_pattern.id,
            ...     limit=5
            ... )
        """
        return self.repository.find_similar_to_pattern(
            pattern_id=pattern_id,
            limit=limit,
            min_similarity=min_similarity,
            include_deprecated=False
        )

    def recommend_patterns_for_entity(
        self,
        entity_description: str,
        field_names: List[str],
        limit: int = 5
    ) -> List[Tuple[Pattern, float]]:
        """
        Recommend patterns for an entity based on description and fields

        Args:
            entity_description: Description of the entity
            field_names: List of field names in the entity
            limit: Maximum recommendations

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> recommendations = service.recommend_patterns_for_entity(
            ...     entity_description="Customer contact information",
            ...     field_names=["email", "phone", "address"],
            ...     limit=5
            ... )
        """
        # Combine description and field names into query
        query = f"{entity_description}. Fields: {', '.join(field_names)}"

        return self.search_patterns_semantic(
            query=query,
            limit=limit,
            min_similarity=0.6  # Higher threshold for recommendations
        )

    def get_pattern_by_name(self, name: str) -> Pattern:
        """Get pattern by name (alias for get_pattern)"""
        return self.get_pattern(name)

    def search_patterns_semantic(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5,
        category: Optional[str] = None
    ) -> List[Tuple[Pattern, float]]:
        """
        Search patterns using natural language query

        Args:
            query: Natural language search query
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold (0-1)
            category: Optional category filter

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> results = service.search_patterns_semantic(
            ...     "validate email addresses",
            ...     limit=5
            ... )
            >>> for pattern, similarity in results:
            ...     print(f"{pattern.name}: {similarity:.2%}")
        """
        # Generate embedding for query
        query_embedding_vector = self.embedding_service.generate_embedding(query)
        query_embedding = self.embedding_service.embedding_to_list(query_embedding_vector)

        # Search
        return self.repository.search_by_similarity(
            query_embedding=query_embedding,
            limit=limit,
            min_similarity=min_similarity,
            category=category,
            include_deprecated=False
        )

    def find_similar_patterns(
        self,
        pattern_id: int,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Tuple[Pattern, float]]:
        """
        Find patterns similar to a given pattern

        Args:
            pattern_id: ID of reference pattern
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> email_pattern = service.get_pattern_by_name("email_validation")
            >>> similar = service.find_similar_patterns(
            ...     email_pattern.id,
            ...     limit=5
            ... )
        """
        return self.repository.find_similar_to_pattern(
            pattern_id=pattern_id,
            limit=limit,
            min_similarity=min_similarity,
            include_deprecated=False
        )

    def recommend_patterns_for_entity(
        self,
        entity_description: str,
        field_names: List[str],
        limit: int = 5
    ) -> List[Tuple[Pattern, float]]:
        """
        Recommend patterns for an entity based on description and fields

        Args:
            entity_description: Description of the entity
            field_names: List of field names in the entity
            limit: Maximum recommendations

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> recommendations = service.recommend_patterns_for_entity(
            ...     entity_description="Customer contact information",
            ...     field_names=["email", "phone", "address"],
            ...     limit=5
            ... )
        """
        # Combine description and field names into query
        query = f"{entity_description}. Fields: {', '.join(field_names)}"

        return self.search_patterns_semantic(
            query=query,
            limit=limit,
            min_similarity=0.6  # Higher threshold for recommendations
        )