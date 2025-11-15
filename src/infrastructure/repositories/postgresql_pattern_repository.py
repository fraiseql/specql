"""PostgreSQL-backed Pattern Repository"""
import psycopg
import json
from typing import List, Optional, Tuple
from src.domain.repositories.pattern_repository import PatternRepository
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType


class PostgreSQLPatternRepository(PatternRepository):
    """PostgreSQL-backed repository for Pattern aggregate"""

    def __init__(self, db_url: str):
        self.db_url = db_url

    def get(self, pattern_name: str) -> Pattern:
        """Get pattern by name from PostgreSQL"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, category, description, parameters, implementation,
                           embedding, times_instantiated, source_type, complexity_score,
                           deprecated, deprecated_reason, replacement_pattern_id,
                           created_at, updated_at
                    FROM pattern_library.domain_patterns
                    WHERE name = %s
                """, (pattern_name,))

                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Pattern {pattern_name} not found")

                return self._row_to_pattern(row)

    def find_by_category(self, category: str) -> List[Pattern]:
        """Find patterns by category"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, category, description, parameters, implementation,
                           embedding, times_instantiated, source_type, complexity_score,
                           deprecated, deprecated_reason, replacement_pattern_id,
                           created_at, updated_at
                    FROM pattern_library.domain_patterns
                    WHERE category = %s
                    ORDER BY name
                """, (category,))

                return [self._row_to_pattern(row) for row in cur.fetchall()]

    def save(self, pattern: Pattern) -> None:
        """Save pattern to PostgreSQL (transactional)"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                if pattern.id is None:
                    # Insert new pattern (let PostgreSQL generate id)
                    cur.execute("""
                        INSERT INTO pattern_library.domain_patterns
                        (name, category, description, parameters, implementation,
                         embedding, times_instantiated, source_type, complexity_score,
                         deprecated, deprecated_reason, replacement_pattern_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO UPDATE SET
                            category = EXCLUDED.category,
                            description = EXCLUDED.description,
                            parameters = EXCLUDED.parameters,
                            implementation = EXCLUDED.implementation,
                            embedding = EXCLUDED.embedding,
                            times_instantiated = EXCLUDED.times_instantiated,
                            source_type = EXCLUDED.source_type,
                            complexity_score = EXCLUDED.complexity_score,
                            deprecated = EXCLUDED.deprecated,
                            deprecated_reason = EXCLUDED.deprecated_reason,
                            replacement_pattern_id = EXCLUDED.replacement_pattern_id,
                            updated_at = now()
                        RETURNING id
                    """, (
                        pattern.name,
                        pattern.category.value,
                        pattern.description,
                        json.dumps(pattern.parameters),
                        json.dumps(pattern.implementation),
                        pattern.embedding,
                        pattern.times_instantiated,
                        pattern.source_type.value,
                        pattern.complexity_score,
                        pattern.deprecated,
                        pattern.deprecated_reason,
                        pattern.replacement_pattern_id
                    ))
                    result = cur.fetchone()
                    if result:
                        pattern.id = result[0]
                else:
                    # Update existing pattern
                    cur.execute("""
                        INSERT INTO pattern_library.domain_patterns
                        (id, name, category, description, parameters, implementation,
                         embedding, times_instantiated, source_type, complexity_score,
                         deprecated, deprecated_reason, replacement_pattern_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO UPDATE SET
                            category = EXCLUDED.category,
                            description = EXCLUDED.description,
                            parameters = EXCLUDED.parameters,
                            implementation = EXCLUDED.implementation,
                            embedding = EXCLUDED.embedding,
                            times_instantiated = EXCLUDED.times_instantiated,
                            source_type = EXCLUDED.source_type,
                            complexity_score = EXCLUDED.complexity_score,
                            deprecated = EXCLUDED.deprecated,
                            deprecated_reason = EXCLUDED.deprecated_reason,
                            replacement_pattern_id = EXCLUDED.replacement_pattern_id,
                            updated_at = now()
                        RETURNING id
                    """, (
                        pattern.id,
                        pattern.name,
                        pattern.category.value,
                        pattern.description,
                        json.dumps(pattern.parameters),
                        json.dumps(pattern.implementation),
                        pattern.embedding,
                        pattern.times_instantiated,
                        pattern.source_type.value,
                        pattern.complexity_score,
                        pattern.deprecated,
                        pattern.deprecated_reason,
                        pattern.replacement_pattern_id
                    ))
                    result = cur.fetchone()
                    if result:
                        pattern.id = result[0]

                conn.commit()

    def list_all(self) -> List[Pattern]:
        """List all patterns"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, category, description, parameters, implementation,
                           embedding, times_instantiated, source_type, complexity_score,
                           deprecated, deprecated_reason, replacement_pattern_id,
                           created_at, updated_at
                    FROM pattern_library.domain_patterns
                    ORDER BY name
                """)

                return [self._row_to_pattern(row) for row in cur.fetchall()]

    def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_similarity: float = 0.0,
        category: Optional[str] = None,
        include_deprecated: bool = False
    ) -> List[Tuple[Pattern, float]]:
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
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Simplified query for now - include deprecated=false by default
                # TODO: Add proper filtering support
                cur.execute("""
                    SELECT
                        id, name, category, description, parameters, implementation,
                        embedding, times_instantiated, source_type, complexity_score,
                        deprecated, deprecated_reason, replacement_pattern_id,
                        created_at, updated_at,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM pattern_library.domain_patterns
                    WHERE embedding IS NOT NULL
                        AND deprecated = false
                        AND (1 - (embedding <=> %s::vector)) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, min_similarity, query_embedding, limit))

                results = []
                for row in cur.fetchall():
                    # Last column is similarity
                    *pattern_data, similarity = row
                    pattern = self._row_to_pattern(pattern_data)
                    results.append((pattern, float(similarity)))

                return results

    def find_similar_to_pattern(
        self,
        pattern_id: int,
        limit: int = 10,
        min_similarity: float = 0.5,
        include_deprecated: bool = False
    ) -> List[Tuple[Pattern, float]]:
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
        # Get reference pattern's embedding
        pattern = self.find_by_id(pattern_id)
        if not pattern or not pattern.embedding:
            return []

        # Search using its embedding
        results = self.search_by_similarity(
            query_embedding=pattern.embedding,
            limit=limit + 1,  # +1 because we'll filter out the reference pattern
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
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, category, description, parameters, implementation,
                           embedding, times_instantiated, source_type, complexity_score,
                           deprecated, deprecated_reason, replacement_pattern_id,
                           created_at, updated_at
                    FROM pattern_library.domain_patterns
                    WHERE id = %s
                """, (pattern_id,))

                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_pattern(row)

    def _row_to_pattern(self, row) -> Pattern:
        """Convert database row to Pattern entity"""
        return Pattern(
            id=row[0],
            name=row[1],
            category=PatternCategory(row[2]),
            description=row[3],
            parameters=row[4] if row[4] else {},
            implementation=row[5] if row[5] else {},
            embedding=row[6],
            times_instantiated=row[7] or 0,
            source_type=SourceType(row[8] or 'manual'),
            complexity_score=row[9],
            deprecated=row[10] or False,
            deprecated_reason=row[11],
            replacement_pattern_id=row[12],
            created_at=row[13],
            updated_at=row[14]
        )