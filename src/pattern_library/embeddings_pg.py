"""
Pattern embedding service using FraiseQL 1.5 GraphQL API

FraiseQL 1.5 handles:
- Embedding generation (auto-generated on INSERT/UPDATE)
- Vector similarity search (GraphQL operators)
- Model loading and caching

SpecQL provides:
- Domain-specific text extraction (_pattern_to_text)
- Business logic for pattern search
"""

from typing import Dict, List, Optional
import httpx


class PatternEmbeddingService:
    """
    Pattern search service using FraiseQL 1.5 GraphQL API

    Simplified version that delegates all embedding operations to FraiseQL.
    Only maintains pattern-specific business logic.
    """

    def __init__(self, fraiseql_url: str = "http://localhost:4000/graphql"):
        """
        Initialize pattern embedding service

        Args:
            fraiseql_url: FraiseQL GraphQL endpoint URL
        """
        self.fraiseql_url = fraiseql_url
        self.client = httpx.Client(timeout=30.0)

    def retrieve_similar(
        self,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.5,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve top-K similar patterns using FraiseQL vector search

        FraiseQL 1.5 handles embedding generation and similarity search.

        Args:
            query_text: Natural language query (FraiseQL generates embedding)
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            category_filter: Optional category filter

        Returns:
            List of {id, name, category, description, similarity, ...}
        """
        # Build GraphQL query with optional category filter
        where_conditions = [
            {"embedding": {"cosineDistance": {"text": query_text, "threshold": threshold}}},
            {"deprecated": {"equals": False}}
        ]

        if category_filter:
            where_conditions.append({"category": {"equals": category_filter}})

        query = """
        query FindSimilarPatterns($query: String!, $topK: Int!, $where: DomainPatternWhereInput!) {
          domainPatterns(
            where: $where
            orderBy: { embedding: { cosineDistance: $query } }
            limit: $topK
          ) {
            id
            name
            category
            description
            parameters
            implementation
            similarity
          }
        }
        """

        variables = {
            "query": query_text,
            "topK": top_k,
            "where": {"AND": where_conditions}
        }

        response = self.client.post(
            self.fraiseql_url,
            json={"query": query, "variables": variables}
        )
        response.raise_for_status()

        result = response.json()
        if "errors" in result:
            raise RuntimeError(f"GraphQL errors: {result['errors']}")

        patterns = result["data"]["domainPatterns"]

        # Convert to legacy format for compatibility
        return [
            {
                "pattern_id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "description": p["description"],
                "parameters": p.get("parameters"),
                "similarity": p.get("similarity", 0.0)
            }
            for p in patterns
        ]

    def hybrid_search(
        self,
        query_text: str,
        category_filter: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Hybrid search: vector similarity + full-text search

        FraiseQL 1.5 handles both vector and full-text operations.

        Args:
            query_text: Search query
            category_filter: Optional category filter
            top_k: Number of results

        Returns:
            List of patterns with combined relevance score
        """
        where_conditions = [
            {
                "OR": [
                    {"embedding": {"cosineDistance": {"text": query_text, "threshold": 0.5}}},
                    {"searchVector": {"matches": query_text}}
                ]
            },
            {"deprecated": {"equals": False}}
        ]

        if category_filter:
            where_conditions.append({"category": {"equals": category_filter}})

        query = """
        query HybridPatternSearch($topK: Int!, $where: DomainPatternWhereInput!) {
          domainPatterns(
            where: $where
            orderBy: { _relevance: DESC }
            limit: $topK
          ) {
            id
            name
            category
            description
            _relevance
          }
        }
        """

        variables = {
            "topK": top_k,
            "where": {"AND": where_conditions}
        }

        response = self.client.post(
            self.fraiseql_url,
            json={"query": query, "variables": variables}
        )
        response.raise_for_status()

        result = response.json()
        if "errors" in result:
            raise RuntimeError(f"GraphQL errors: {result['errors']}")

        patterns = result["data"]["domainPatterns"]

        return [
            {
                "pattern_id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "description": p["description"],
                "combined_score": p.get("_relevance", 0.0)
            }
            for p in patterns
        ]

    @staticmethod
    def _pattern_to_text(pattern: Dict) -> str:
        """
        Convert pattern to searchable text

        Domain-specific logic for combining pattern fields.
        Used by FraiseQL's embedding configuration.
        """
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
        """Close HTTP client"""
        self.client.close()
