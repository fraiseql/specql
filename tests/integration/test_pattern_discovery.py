"""
Integration tests for pattern discovery workflow.

Tests the complete flow:
1. Reverse engineer SQL with pattern discovery
2. Create pattern suggestions
3. Review and approve/reject suggestions
4. Verify patterns are added to library
"""

import pytest
import os


class TestPatternDiscovery:
    """Test pattern discovery end-to-end."""

    @pytest.fixture
    def db_connection(self):
        """Set up test database connection."""
        # This would need actual PostgreSQL test setup
        # For now, we'll mock or skip if no DB
        conn_string = os.getenv("SPECQL_DB_URL")
        if not conn_string:
            pytest.skip("SPECQL_DB_URL not set - skipping database tests")
        return conn_string

    def test_pattern_discovery_basic(self, db_connection):
        """Test basic pattern discovery from SQL."""
        # Sample SQL with a complex approval workflow pattern
        sql = """
        CREATE OR REPLACE FUNCTION approve_document(
            p_document_id INTEGER,
            p_approver_id INTEGER
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_status TEXT;
            v_approval_count INTEGER;
        BEGIN
            -- Check current status
            SELECT status INTO v_status
            FROM documents
            WHERE id = p_document_id;

            IF v_status != 'pending' THEN
                RAISE EXCEPTION 'Document not pending approval';
            END IF;

            -- Count existing approvals
            SELECT COUNT(*) INTO v_approval_count
            FROM document_approvals
            WHERE document_id = p_document_id;

            -- Require 2 approvals
            IF v_approval_count >= 2 THEN
                -- Update status to approved
                UPDATE documents
                SET status = 'approved',
                    approved_at = now(),
                    approved_by = p_approver_id
                WHERE id = p_document_id;

                -- Log approval
                INSERT INTO audit_log (action, entity_id, user_id, details)
                VALUES ('approve', p_document_id, p_approver_id, 'Document approved');

                RETURN TRUE;
            ELSE
                -- Add approval
                INSERT INTO document_approvals (document_id, approver_id, approved_at)
                VALUES (p_document_id, p_approver_id, now());

                RETURN FALSE; -- Still needs more approvals
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """

        # Test the algorithmic parser with pattern discovery
        from src.reverse_engineering.algorithmic_parser import AlgorithmicParser

        parser = AlgorithmicParser(
            use_heuristics=True, use_ai=True, enable_pattern_discovery=True
        )

        result = parser.parse(sql)

        # Verify basic parsing worked
        assert result.confidence > 0.7
        assert result.function_name == "approve_document"
        assert len(result.steps) > 5  # Complex function

        # Check if pattern discovery was attempted
        # (This would create suggestions in the database)
        assert hasattr(result, "metadata")
        if "discovered_patterns" in result.metadata:
            patterns = result.metadata["discovered_patterns"]
            assert isinstance(patterns, list)

    def test_suggestion_service_operations(self, db_connection):
        """Test pattern suggestion service operations."""
        from src.pattern_library.suggestion_service_pg import PatternSuggestionService

        service = PatternSuggestionService()

        try:
            # Create a test suggestion
            suggestion_id = service.create_suggestion(
                suggested_name="test_approval_workflow",
                suggested_category="workflow",
                description="Multi-step approval workflow with audit logging",
                parameters={
                    "entity": {"type": "string", "required": True},
                    "approvals_required": {"type": "integer", "default": 2},
                },
                implementation={
                    "fields": [
                        {"name": "status", "type": "enum(pending,approved,rejected)"},
                        {"name": "approved_at", "type": "timestamp"},
                        {"name": "approved_by", "type": "ref(User)"},
                    ],
                    "actions": [
                        {
                            "name": "approve",
                            "steps": [
                                {"validate": "status == 'pending'"},
                                {"update": "increment approval_count"},
                                {
                                    "condition": "approval_count >= approvals_required",
                                    "then": [
                                        {
                                            "update": "status = 'approved', approved_at = now()"
                                        },
                                        {"log": "Document approved"},
                                    ],
                                },
                            ],
                        }
                    ],
                },
                source_type="test",
                complexity_score=0.8,
                confidence_score=0.9,
            )

            assert suggestion_id is not None

            # Test retrieval
            suggestion = service.get_suggestion(suggestion_id)
            assert suggestion is not None
            assert suggestion["name"] == "test_approval_workflow"
            assert suggestion["status"] == "pending"

            # Test listing
            pending = service.list_pending()
            assert len(pending) >= 1
            found = any(s["id"] == suggestion_id for s in pending)
            assert found

            # Test approval
            success = service.approve_suggestion(suggestion_id, "test_user")
            assert success

            # Verify suggestion was approved
            suggestion = service.get_suggestion(suggestion_id)
            assert suggestion["status"] == "approved"
            assert suggestion["reviewed_by"] == "test_user"

        finally:
            service.close()

    def test_cli_commands_integration(self, db_connection):
        """Test CLI commands work together."""
        # This would require setting up a test database and running actual CLI commands
        # For now, we'll test the service layer which the CLI uses

        from src.pattern_library.suggestion_service_pg import PatternSuggestionService

        service = PatternSuggestionService()

        try:
            # Create multiple suggestions
            ids = []
            for i in range(3):
                suggestion_id = service.create_suggestion(
                    suggested_name=f"test_pattern_{i}",
                    suggested_category="workflow",
                    description=f"Test pattern {i} for CLI testing",
                    source_type="test",
                    complexity_score=0.5 + i * 0.1,
                    confidence_score=0.7 + i * 0.1,
                )
                ids.append(suggestion_id)

            # Test listing (like CLI review-suggestions)
            pending = service.list_pending(limit=10)
            assert len(pending) >= 3

            # Test approval workflow (like CLI approve)
            success = service.approve_suggestion(ids[0], "cli_test")
            assert success

            # Test rejection workflow (like CLI reject)
            success = service.reject_suggestion(ids[1], "Not reusable", "cli_test")
            assert success

            # Verify final state
            stats = service.get_stats()
            assert stats["approved"] >= 1
            assert stats["rejected"] >= 1
            assert stats["pending"] >= 1

        finally:
            service.close()

    def test_pattern_discovery_with_embeddings(self, db_connection):
        """Test that pattern discovery considers existing patterns."""
        # This test would verify that the similarity checking works
        # by ensuring patterns similar to existing ones aren't suggested

        from src.pattern_library.embeddings_pg import PatternEmbeddingService
        from src.pattern_library.suggestion_service_pg import PatternSuggestionService

        embedding_service = PatternEmbeddingService()
        suggestion_service = PatternSuggestionService()

        try:
            # Get existing patterns
            # This would check similarity against seed patterns
            # For now, just verify the services can be instantiated
            assert embedding_service is not None
            assert suggestion_service is not None

        finally:
            embedding_service.close()
            suggestion_service.close()

    def test_complexity_scoring(self):
        """Test complexity scoring logic."""
        from src.reverse_engineering.ai_enhancer import AIEnhancer

        enhancer = AIEnhancer(use_grok=False, enable_pattern_discovery=True)

        # Test simple SQL
        simple_sql = "SELECT * FROM users WHERE id = 1;"
        result = type("MockResult", (), {"steps": [1, 2, 3]})()  # Mock result
        score = enhancer._calculate_complexity_score(result, simple_sql)
        assert score < 0.5  # Should be low complexity

        # Test complex SQL
        complex_sql = """
        WITH RECURSIVE hierarchy AS (
            SELECT id, parent_id, name, 1 as level
            FROM categories
            WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.parent_id, c.name, h.level + 1
            FROM categories c
            JOIN hierarchy h ON c.parent_id = h.id
        ),
        stats AS (
            SELECT category_id, COUNT(*) as item_count,
                   AVG(price) as avg_price
            FROM items
            GROUP BY category_id
        )
        SELECT h.name, h.level, s.item_count, s.avg_price
        FROM hierarchy h
        LEFT JOIN stats s ON h.id = s.category_id
        ORDER BY h.level, h.name;
        """
        result.steps = list(range(15))  # Mock 15 steps
        score = enhancer._calculate_complexity_score(result, complex_sql)
        assert score > 0.7  # Should be high complexity
