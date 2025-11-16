"""
Performance benchmarks for the pattern library system.

Tests database operations, vector search performance, and basic system responsiveness.
"""

import pytest
import time


class TestPatternLibraryPerformance:
    """Performance tests for pattern library components."""

    @pytest.fixture
    def db_connection(self):
        """Set up test database connection."""
        import os

        conn_string = os.getenv("SPECQL_DB_URL")
        if not conn_string:
            pytest.skip("SPECQL_DB_URL not set - skipping database tests")
        return conn_string

    def test_database_query_performance(self, db_connection):
        """Benchmark basic database query performance."""
        import psycopg

        with psycopg.connect(db_connection) as conn:
            with conn.cursor() as cur:
                # Test pattern retrieval performance
                start_time = time.time()
                cur.execute("""
                    SELECT id, name, description, category, parameters, implementation
                    FROM pattern_library.domain_patterns
                    LIMIT 50
                """)
                cur.fetchall()
                query_time = time.time() - start_time

                print(".4f")
                assert query_time < 0.1, ".4f"

                # Test JSONB query performance
                start_time = time.time()
                cur.execute("""
                    SELECT COUNT(*) FROM pattern_library.domain_patterns
                    WHERE parameters->>'entity' IS NOT NULL
                """)
                jsonb_query_time = time.time() - start_time

                print(".4f")
                assert jsonb_query_time < 0.05, ".4f"

    def test_vector_operations_performance(self, db_connection):
        """Benchmark pgvector operations."""
        import psycopg

        with psycopg.connect(db_connection) as conn:
            with conn.cursor() as cur:
                # Test vector distance calculations
                test_vectors = [
                    ([0.1, 0.2, 0.3], [0.4, 0.5, 0.6]),
                    ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
                    ([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
                ]

                total_time = 0
                operations = 0

                for vec1, vec2 in test_vectors:
                    start_time = time.time()
                    cur.execute(
                        """
                        SELECT %s::vector <=> %s::vector as cosine_distance,
                               %s::vector <-> %s::vector as l2_distance
                    """,
                        (vec1, vec2, vec1, vec2),
                    )
                    result = cur.fetchone()
                    operation_time = time.time() - start_time

                    total_time += operation_time
                    operations += 1

                    assert result is not None
                    assert len(result) == 2

                avg_time = total_time / operations
                print(".6f")
                assert avg_time < 0.001, ".6f"

    def test_suggestion_crud_performance(self, db_connection):
        """Benchmark pattern suggestion CRUD operations."""
        import psycopg

        with psycopg.connect(db_connection) as conn:
            with conn.cursor() as cur:
                # Test creating multiple suggestions
                start_time = time.time()
                suggestion_ids = []

                for i in range(10):
                    cur.execute(
                        """
                        INSERT INTO pattern_library.pattern_suggestions
                        (suggested_name, suggested_category, description, source_type,
                         complexity_score, confidence_score, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """,
                        (
                            f"perf_suggestion_{i}",
                            "workflow",
                            f"Performance test suggestion {i} with some description",
                            "performance_test",
                            0.5 + (i % 5) * 0.1,
                            0.7 + (i % 3) * 0.1,
                            "pending",
                        ),
                    )
                    result = cur.fetchone()
                    assert result is not None
                    suggestion_ids.append(result[0])

                time.time() - start_time
                print(".4f")

                # Test bulk retrieval
                start_time = time.time()
                cur.execute(
                    """
                    SELECT id, suggested_name, status FROM pattern_library.pattern_suggestions
                    WHERE id = ANY(%s)
                """,
                    (suggestion_ids,),
                )
                results = cur.fetchall()
                time.time() - start_time

                print(".4f")
                assert len(results) == 10

                # Test updates
                start_time = time.time()
                for suggestion_id in suggestion_ids[:5]:  # Update half
                    cur.execute(
                        """
                        UPDATE pattern_library.pattern_suggestions
                        SET status = 'approved', reviewed_by = 'perf_test', reviewed_at = now()
                        WHERE id = %s
                    """,
                        (suggestion_id,),
                    )

                time.time() - start_time
                print(".4f")

                # Clean up
                cur.execute(
                    "DELETE FROM pattern_library.pattern_suggestions WHERE id = ANY(%s)",
                    (suggestion_ids,),
                )
                conn.commit()

    def test_jsonb_query_performance(self, db_connection):
        """Benchmark JSONB queries on pattern data."""
        import psycopg

        with psycopg.connect(db_connection) as conn:
            with conn.cursor() as cur:
                # Test JSONB queries on existing patterns
                queries = [
                    (
                        "Simple key exists",
                        "SELECT COUNT(*) FROM pattern_library.domain_patterns WHERE parameters ? 'entity'",
                    ),
                    (
                        "Nested key exists",
                        "SELECT COUNT(*) FROM pattern_library.domain_patterns WHERE parameters->'approvals_required' IS NOT NULL",
                    ),
                    (
                        "GIN index query",
                        "SELECT COUNT(*) FROM pattern_library.domain_patterns WHERE parameters @@ '$.entity == \"*\"'",
                    ),
                ]

                for query_name, query in queries:
                    start_time = time.time()
                    cur.execute(query)
                    cur.fetchone()
                    query_time = time.time() - start_time

                    print(".4f")
                    assert query_time < 0.05, ".4f"

    def test_full_text_search_performance(self, db_connection):
        """Benchmark full-text search on patterns."""
        import psycopg

        with psycopg.connect(db_connection) as conn:
            with conn.cursor() as cur:
                # Test full-text search queries
                search_terms = ["workflow", "approval", "audit", "state"]

                for term in search_terms:
                    start_time = time.time()
                    cur.execute(
                        """
                        SELECT COUNT(*) FROM pattern_library.domain_patterns
                        WHERE to_tsvector('english', description) @@ plainto_tsquery('english', %s)
                    """,
                        (term,),
                    )
                    cur.fetchone()
                    search_time = time.time() - start_time

                    print(".4f")
                    assert search_time < 0.02, ".4f"

    def test_concurrent_database_operations(self, db_connection):
        """Test database performance under concurrent operations."""
        import threading
        import psycopg

        results = []
        errors = []

        def worker_thread(worker_id):
            """Worker thread for concurrent database operations."""
            try:
                with psycopg.connect(db_connection) as conn:
                    with conn.cursor() as cur:
                        start_time = time.time()

                        # Insert test suggestion
                        cur.execute(
                            """
                            INSERT INTO pattern_library.pattern_suggestions
                            (suggested_name, suggested_category, description, source_type, status)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                        """,
                            (
                                f"concurrent_suggestion_{worker_id}",
                                "workflow",
                                f"Concurrent test suggestion {worker_id}",
                                "performance_test",
                                "pending",
                            ),
                        )

                        result = cur.fetchone()
                        assert result is not None
                        suggestion_id = result[0]

                        # Query it back
                        cur.execute(
                            """
                            SELECT suggested_name FROM pattern_library.pattern_suggestions
                            WHERE id = %s
                        """,
                            (suggestion_id,),
                        )
                        result = cur.fetchone()

                        # Clean up
                        cur.execute(
                            "DELETE FROM pattern_library.pattern_suggestions WHERE id = %s",
                            (suggestion_id,),
                        )
                        conn.commit()

                        operation_time = time.time() - start_time
                        results.append(
                            {
                                "worker_id": worker_id,
                                "operation_time": operation_time,
                                "success": result is not None,
                            }
                        )

            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Run concurrent threads
        threads = []
        num_threads = 5

        start_time = time.time()
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        assert len(results) == num_threads, (
            f"Expected {num_threads} results, got {len(results)}"
        )
        assert len(errors) == 0, f"Concurrent operations had errors: {errors}"

        avg_operation_time = sum(r["operation_time"] for r in results) / len(results)
        print(".4f")
        print(".3f")

        assert avg_operation_time < 0.1, ".4f"
        assert total_time < 1.0, ".3f"
