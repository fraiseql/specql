"""Performance tests for semantic search"""
import pytest
import time
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)
from src.application.services.pattern_service import PatternService
from src.infrastructure.services.embedding_service import get_embedding_service
from src.core.config import get_config


@pytest.fixture
def service():
    """Create service"""
    config = get_config()
    if not config.database_url:
        pytest.skip("Database not configured")

    repository = PostgreSQLPatternRepository(config.database_url)
    return PatternService(repository)


@pytest.mark.skipif(
    not get_config().database_url,
    reason="Requires PostgreSQL database"
)
class TestSemanticSearchPerformance:
    """Performance benchmarks for semantic search"""

    def test_single_search_performance(self, service):
        """Test single search query performance"""
        query = "validate email addresses"

        start = time.time()
        results = service.search_patterns_semantic(query, limit=10)
        elapsed = time.time() - start

        print(f"\n⏱️  Single search: {elapsed*1000:.2f}ms")
        print(f"   Results: {len(results)}")

        # Should be fast (< 100ms)
        assert elapsed < 0.1

    def test_batch_search_performance(self, service):
        """Test multiple searches performance"""
        queries = [
            "email validation",
            "phone number formatting",
            "address validation",
            "date parsing",
            "money formatting",
        ]

        start = time.time()
        for query in queries:
            service.search_patterns_semantic(query, limit=5)
        elapsed = time.time() - start

        avg_time = elapsed / len(queries)
        print(f"\n⏱️  Batch search ({len(queries)} queries): {elapsed*1000:.2f}ms")
        print(f"   Average per query: {avg_time*1000:.2f}ms")

        # Average should be fast
        assert avg_time < 0.1

    def test_embedding_generation_performance(self):
        """Test embedding generation performance"""
        embedding_service = get_embedding_service()

        texts = [
            "Email validation pattern",
            "Phone number validation",
            "Address formatting",
        ] * 10  # 30 texts

        start = time.time()
        embeddings = embedding_service.generate_embeddings_batch(texts)
        elapsed = time.time() - start

        avg_time = elapsed / len(texts)
        print(f"\n⏱️  Embedding generation ({len(texts)} texts): {elapsed*1000:.2f}ms")
        print(f"   Average per text: {avg_time*1000:.2f}ms")
        print(f"   Throughput: {len(texts)/elapsed:.1f} texts/sec")

        # Should handle batch efficiently
        assert avg_time < 0.01  # < 10ms per text