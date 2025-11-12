"""Pattern embedding service using PostgreSQL + pgvector."""

from sentence_transformers import SentenceTransformer
import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from typing import Dict, List, Optional
from pathlib import Path
import os

class PatternEmbeddingService:
    """
    Generate and manage pattern embeddings using PostgreSQL + pgvector.

    Features:
    - CPU-friendly sentence-transformers
    - Native pgvector storage and similarity search
    - HNSW index for 100x speedup
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize embedding service.

        Args:
            connection_string: PostgreSQL connection string (or uses SPECQL_DB_URL env)
            model_name: Sentence transformer model (384-dim, fast on CPU)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        # Connect to PostgreSQL
        self.conn_string = connection_string or os.getenv('SPECQL_DB_URL')
        if not self.conn_string:
            raise ValueError("No connection string provided and SPECQL_DB_URL not set")

        self.conn = psycopg.connect(self.conn_string)
        register_vector(self.conn)

        print(f"✓ Embedding service ready ({model_name}, PostgreSQL + pgvector)")

    def embed_pattern(self, pattern: Dict) -> np.ndarray:
        """
        Generate embedding for a domain pattern.

        Combines:
        - Pattern name and description
        - Category
        - Field names
        - Action names

        Returns:
            384-dim numpy array
        """
        text = self._pattern_to_text(pattern)
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.astype(np.float32)

    def embed_function(self, sql: str, description: str = "") -> np.ndarray:
        """Generate embedding for SQL function."""
        text = f"{description}\n{sql}" if description else sql
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.astype(np.float32)

    def update_pattern_embedding(self, pattern_id: int, embedding: np.ndarray):
        """Update pattern with embedding (native pgvector!)."""
        self.conn.execute(
            """
            UPDATE pattern_library.domain_patterns
            SET embedding = %s
            WHERE id = %s
            """,
            (embedding, pattern_id)
        )
        self.conn.commit()

    def generate_all_embeddings(self):
        """Batch generate embeddings for all patterns without embeddings."""
        cursor = self.conn.execute(
            """
            SELECT id, name, category, description, parameters, implementation
            FROM pattern_library.domain_patterns
            WHERE embedding IS NULL
            """
        )

        patterns = cursor.fetchall()
        print(f"Generating embeddings for {len(patterns)} patterns...")

        for i, row in enumerate(patterns, 1):
            pattern_id, name, category, description, parameters, implementation = row

            pattern = {
                'name': name,
                'category': category,
                'description': description,
                'parameters': parameters,
                'implementation': implementation
            }

            embedding = self.embed_pattern(pattern)
            self.update_pattern_embedding(pattern_id, embedding)

            if i % 10 == 0:
                print(f"  {i}/{len(patterns)} complete")

        print(f"✓ {len(patterns)} embeddings generated")

    def retrieve_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.5,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve top-K similar patterns using native pgvector.

        Uses HNSW index for fast approximate nearest neighbor search.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            category_filter: Optional category filter

        Returns:
            List of {pattern_id, name, category, description, similarity, ...}
        """
        # Build query
        query = """
            SELECT
                id,
                name,
                category,
                description,
                parameters,
                1 - (embedding <=> %s) AS similarity
            FROM pattern_library.domain_patterns
            WHERE embedding IS NOT NULL
                AND deprecated = FALSE
                AND (1 - (embedding <=> %s)) >= %s
        """

        params = [query_embedding, query_embedding, threshold]

        if category_filter:
            query += " AND category = %s"
            params.append(category_filter)

        query += " ORDER BY embedding <=> %s LIMIT %s"
        params.extend([query_embedding, top_k])

        # Execute
        cursor = self.conn.execute(query, params)

        results = []
        for row in cursor:
            results.append({
                'pattern_id': row[0],
                'name': row[1],
                'category': row[2],
                'description': row[3],
                'parameters': row[4],
                'similarity': float(row[5])
            })

        return results

    def hybrid_search(
        self,
        query_embedding: np.ndarray,
        query_text: Optional[str] = None,
        category_filter: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Hybrid search: vector similarity + full-text search + filters.

        Uses PostgreSQL function for optimized query.
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM pattern_library.hybrid_pattern_search(
                %s, %s, %s, %s
            )
            """,
            (query_embedding, query_text, category_filter, top_k)
        )

        results = []
        for row in cursor:
            results.append({
                'pattern_id': row[0],
                'name': row[1],
                'category': row[2],
                'description': row[3],
                'combined_score': float(row[4])
            })

        return results

    def _pattern_to_text(self, pattern: Dict) -> str:
        """Convert pattern to searchable text."""
        parts = [
            f"Pattern: {pattern.get('name', '')}",
            f"Category: {pattern.get('category', '')}",
            f"Description: {pattern.get('description', '')}"
        ]

        # Add field names if available
        impl = pattern.get('implementation', {})
        if isinstance(impl, dict) and 'fields' in impl:
            field_names = [f.get('name', '') for f in impl['fields']]
            parts.append(f"Fields: {', '.join(field_names)}")

        # Add action names
        if isinstance(impl, dict) and 'actions' in impl:
            action_names = [a.get('name', '') for a in impl['actions']]
            parts.append(f"Actions: {', '.join(action_names)}")

        return " | ".join(parts)

    def close(self):
        """Close database connection."""
        self.conn.close()