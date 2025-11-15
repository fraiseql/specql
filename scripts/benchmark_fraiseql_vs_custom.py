#!/usr/bin/env python3
"""
Benchmark FraiseQL 1.5 Vector Queries vs SpecQL Custom Functions

This script compares the performance of FraiseQL 1.5 GraphQL vector queries
against SpecQL's custom SQL search functions.

Run this after FraiseQL 1.5 is installed and both implementations are available.
"""

import time
import statistics
import psycopg
from typing import List, Dict, Any, Optional
import requests


class FraiseQLClient:
    """Simple GraphQL client for FraiseQL"""

    def __init__(self, endpoint: str = "http://localhost:4000/graphql"):
        self.endpoint = endpoint

    def query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query"""
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.endpoint, json=payload, headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()["data"]


class DatabaseClient:
    """Direct PostgreSQL client for testing custom functions"""

    def __init__(self, connection_string: str):
        self.conn = psycopg.connect(connection_string)

    def execute_custom_function(
        self, query_embedding: List[float], limit: int = 10
    ) -> List[Dict]:
        """Execute SpecQL's custom search function"""
        query = """
        SELECT * FROM pattern_library.find_similar_patterns(
            %s::vector(384), %s, 0.5
        )
        """
        cursor = self.conn.execute(query, (query_embedding, limit))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()


def generate_test_queries() -> List[str]:
    """Generate diverse test queries for benchmarking"""
    return [
        "user authentication pattern",
        "audit trail implementation",
        "data validation workflow",
        "soft delete mechanism",
        "role-based access control",
        "event sourcing pattern",
        "CQRS architecture",
        "API rate limiting",
        "database indexing strategy",
        "error handling pattern",
    ]


def benchmark_fraiseql(
    client: FraiseQLClient, queries: List[str], runs: int = 5
) -> Dict[str, float]:
    """Benchmark FraiseQL vector queries"""
    times = []

    fraiseql_query = """
    query FindSimilarPatterns($queryText: String!, $limit: Int!) {
      domainPatterns(
        where: {
          embedding: {
            cosineDistance: { text: $queryText, threshold: 0.5 }
          }
        }
        limit: $limit
      ) {
        id
        name
        category
        description
        similarity
      }
    }
    """

    for query_text in queries:
        for _ in range(runs):
            start_time = time.time()
            client.query(fraiseql_query, {"queryText": query_text, "limit": 10})
            end_time = time.time()
            times.append(end_time - start_time)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "p95": statistics.quantiles(times, n=20)[18],  # 95th percentile
        "p99": statistics.quantiles(times, n=100)[98],  # 99th percentile
        "min": min(times),
        "max": max(times),
        "total_queries": len(queries) * runs,
    }


def benchmark_custom_functions(
    db_client: DatabaseClient, queries: List[str], runs: int = 5
) -> Dict[str, float]:
    """Benchmark SpecQL custom SQL functions"""
    times = []

    # First, we need embeddings for the text queries
    # In a real benchmark, we'd use the EmbeddingService
    # For now, using dummy embeddings
    dummy_embedding = [0.1] * 384

    for query_text in queries:
        for _ in range(runs):
            start_time = time.time()
            db_client.execute_custom_function(dummy_embedding, limit=10)
            end_time = time.time()
            times.append(end_time - start_time)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "p95": statistics.quantiles(times, n=20)[18],
        "p99": statistics.quantiles(times, n=100)[98],
        "min": min(times),
        "max": max(times),
        "total_queries": len(queries) * runs,
    }


def print_results(fraiseql_stats: Dict[str, float], custom_stats: Dict[str, float]):
    """Print benchmark results"""
    print("FraiseQL 1.5 vs SpecQL Custom Functions - Performance Benchmark")
    print("=" * 70)
    print()

    print("Test Configuration:")
    print(f"  • Queries tested: {fraiseql_stats['total_queries']}")
    print("  • Metric: Response time (seconds)")
    print("  • Test: Cosine distance search, limit 10, threshold 0.5")
    print()

    print("FraiseQL 1.5 GraphQL Vector Queries:")
    print(f"  • Mean:   {fraiseql_stats['mean']:.4f}s")
    print(f"  • Median: {fraiseql_stats['median']:.4f}s")
    print(f"  • P95:    {fraiseql_stats['p95']:.4f}s")
    print(f"  • P99:    {fraiseql_stats['p99']:.4f}s")
    print(f"  • Min:    {fraiseql_stats['min']:.4f}s")
    print(f"  • Max:    {fraiseql_stats['max']:.4f}s")
    print()

    print("SpecQL Custom SQL Functions:")
    print(f"  • Mean:   {custom_stats['mean']:.4f}s")
    print(f"  • Median: {custom_stats['median']:.4f}s")
    print(f"  • P95:    {custom_stats['p95']:.4f}s")
    print(f"  • P99:    {custom_stats['p99']:.4f}s")
    print(f"  • Min:    {custom_stats['min']:.4f}s")
    print(f"  • Max:    {custom_stats['max']:.4f}s")
    print()

    # Performance comparison
    speedup = custom_stats["mean"] / fraiseql_stats["mean"]
    print("Performance Comparison:")
    if speedup > 1:
        print(f"  • Custom SQL is {speedup:.2f}x faster than FraiseQL")
    else:
        print(f"  • FraiseQL is {1 / speedup:.2f}x faster than Custom SQL")
        print("  ⚠️  FraiseQL is slower - investigate optimization opportunities")
    print()

    # Recommendations
    print("Recommendations:")
    if fraiseql_stats["p95"] < 0.1:  # Sub-100ms P95
        print("  ✅ FraiseQL performance meets production requirements (< 100ms P95)")
    else:
        print("  ⚠️  FraiseQL P95 > 100ms - may need optimization")

    if speedup >= 0.8:  # Within 20% of custom functions
        print("  ✅ FraiseQL performance comparable to custom functions")
        print("  ✅ Migration recommended")
    else:
        print("  ⚠️  Significant performance gap - consider keeping custom functions")
        print("  💡 Consider FraiseQL optimizations or hybrid approach")


def main():
    """Main benchmark function"""
    print("FraiseQL 1.5 vs SpecQL Custom Functions Benchmark")
    print("=" * 60)
    print()

    # Check if FraiseQL is available
    try:
        fraiseql_client = FraiseQLClient()
        # Test basic connectivity
        fraiseql_client.query("{ __typename }")
        print("✅ FraiseQL 1.5 detected and responding")
    except Exception as e:
        print(f"❌ FraiseQL 1.5 not available: {e}")
        print()
        print("Prerequisites:")
        print("  1. FraiseQL 1.5 installed and running on localhost:4000")
        print("  2. Database with pattern_library schema populated")
        print("  3. Embedding vectors generated for domain_patterns")
        return 1

    # Check database connectivity
    db_url = "postgresql://specql_user:password@localhost:5432/specql"
    try:
        db_client = DatabaseClient(db_url)
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Connection string: {db_url}")
        return 1

    try:
        # Generate test queries
        queries = generate_test_queries()
        print(f"📝 Generated {len(queries)} test queries")

        # Run benchmarks
        print("🏃 Running FraiseQL benchmark...")
        fraiseql_stats = benchmark_fraiseql(fraiseql_client, queries)

        print("🏃 Running custom functions benchmark...")
        custom_stats = benchmark_custom_functions(db_client, queries)

        # Print results
        print()
        print_results(fraiseql_stats, custom_stats)

    finally:
        db_client.close()

    return 0


if __name__ == "__main__":
    exit(main())
