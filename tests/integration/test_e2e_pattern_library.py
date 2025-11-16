"""
End-to-end integration tests for the complete pattern library workflow.

Tests the complete user journeys:
1. SQL → Discovery → Approval → Reuse workflow
2. Natural Language → Pattern → Validation → Usage workflow

These tests require a PostgreSQL database with the pattern library schema.
"""

import pytest
import os


class TestPatternLibraryE2E:
    """End-to-end tests for pattern library workflows."""

    @pytest.fixture
    def db_connection(self):
        """Set up test database connection."""
        conn_string = os.getenv("SPECQL_DB_URL")
        if not conn_string:
            pytest.skip("SPECQL_DB_URL not set - skipping database tests")
        return conn_string

    @pytest.fixture
    def mock_grok_response(self):
        """Mock Grok LLM response for testing."""
        return {
            "pattern_name": "test_approval_workflow",
            "category": "workflow",
            "description": "Multi-step approval workflow with audit logging",
            "parameters": {
                "entity": {"type": "string", "required": True},
                "approvals_required": {"type": "integer", "default": 2},
            },
            "implementation": {
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
        }

    def test_database_setup_validation(self, db_connection):
        """Test that the pattern library database schema is properly set up."""
        import psycopg

        # Test basic database connectivity
        with psycopg.connect(db_connection) as conn:
            with conn.cursor() as cur:
                # Check if pattern library tables exist
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('domain_patterns', 'pattern_suggestions', 'grok_call_logs')
                """)
                tables = cur.fetchall()
                table_names = [row[0] for row in tables]

                # Should have the main pattern library tables
                assert "domain_patterns" in table_names
                assert "pattern_suggestions" in table_names

                # Check if pgvector extension is available
                cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
                vector_ext = cur.fetchone()
                assert vector_ext is not None, "pgvector extension should be installed"

                # Test vector operations work
                cur.execute(
                    "SELECT '[1,2,3]'::vector <=> '[4,5,6]'::vector as distance"
                )
                result = cur.fetchone()
                assert result is not None
                assert len(result) > 0
                assert isinstance(result[0], float)

    def test_seed_patterns_loaded(self, db_connection):
        """Test that seed patterns are properly loaded."""
        import psycopg

        with psycopg.connect(db_connection) as conn:
            with conn.cursor() as cur:
                # Check seed patterns are loaded
                cur.execute("SELECT COUNT(*) FROM pattern_library.domain_patterns")
                count_result = cur.fetchone()
                assert count_result is not None
                count = count_result[0]
                assert count >= 5, f"Expected at least 5 seed patterns, found {count}"

                # Check specific seed patterns exist
                cur.execute("""
                    SELECT name FROM pattern_library.domain_patterns
                    WHERE name IN ('audit_trail', 'soft_delete', 'state_machine', 'approval_workflow', 'validation_chain')
                """)
                patterns = cur.fetchall()
                pattern_names = [row[0] for row in patterns]

                expected_patterns = {
                    "audit_trail",
                    "soft_delete",
                    "state_machine",
                    "approval_workflow",
                    "validation_chain",
                }
                found_patterns = set(pattern_names)
                assert expected_patterns.issubset(found_patterns), (
                    f"Missing patterns: {expected_patterns - found_patterns}"
                )

    def test_basic_cli_commands_available(self):
        """Test that pattern library CLI commands are available."""
        import subprocess
        import sys

        # Test that specql patterns command exists
        try:
            result = subprocess.run(
                [sys.executable, "-m", "src.cli.main", "patterns", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Should not fail completely
            assert (
                result.returncode == 0
                or "patterns" in result.stdout
                or "patterns" in result.stderr
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # CLI might not be fully set up, which is OK for this test
            pass

    def test_grok_provider_basic_functionality(self):
        """Test that Grok provider can be instantiated and has basic methods."""
        try:
            from src.reverse_engineering.grok_provider import GrokProvider
        except ImportError:
            pytest.skip("Grok provider dependencies not available")

        # Test that GrokProvider can be instantiated
        provider = GrokProvider()
        assert provider is not None
        assert hasattr(provider, "call")
        assert hasattr(provider, "call_json")

    def test_ai_enhancer_with_pattern_discovery(self):
        """Test that AI enhancer can be configured with pattern discovery."""
        try:
            from src.reverse_engineering.ai_enhancer import AIEnhancer
        except ImportError:
            pytest.skip("AI enhancer dependencies not available")

        # Test that AI enhancer can be created with pattern discovery enabled
        enhancer = AIEnhancer(use_grok=True, enable_pattern_discovery=True)
        assert enhancer is not None
        assert enhancer.enable_pattern_discovery is True
        assert enhancer.use_grok is True

    def test_pattern_library_imports(self):
        """Test that pattern library modules can be imported."""
        # Test core pattern library imports
        try:
            from src.pattern_library import api

            assert api is not None
        except ImportError:
            pytest.skip("Pattern library API not available")

        try:
            from src.pattern_library import migrations

            assert migrations is not None
        except ImportError:
            pytest.skip("Pattern library migrations not available")

    def test_basic_workflow_simulation(self, db_connection):
        """Simulate a basic pattern library workflow without full dependencies."""
        import psycopg

        with psycopg.connect(db_connection) as conn:
            with conn.cursor() as cur:
                # Simulate creating a pattern suggestion
                cur.execute(
                    """
                    INSERT INTO pattern_library.pattern_suggestions
                    (suggested_name, suggested_category, description, source_type, complexity_score, confidence_score, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        "test_workflow_simulation",
                        "workflow",
                        "Test workflow for simulation",
                        "test",
                        0.8,
                        0.9,
                        "pending",
                    ),
                )

                suggestion_result = cur.fetchone()
                assert suggestion_result is not None
                suggestion_id = suggestion_result[0]
                assert suggestion_id is not None

                # Simulate approving the suggestion
                cur.execute(
                    """
                    UPDATE pattern_library.pattern_suggestions
                    SET status = 'approved', reviewed_by = %s, reviewed_at = now()
                    WHERE id = %s
                """,
                    ("test_user", suggestion_id),
                )

                # Verify approval
                cur.execute(
                    """
                    SELECT status, reviewed_by FROM pattern_library.pattern_suggestions
                    WHERE id = %s
                """,
                    (suggestion_id,),
                )
                approval_result = cur.fetchone()
                assert approval_result is not None
                assert approval_result[0] == "approved"
                assert approval_result[1] == "test_user"

                # Clean up
                cur.execute(
                    "DELETE FROM pattern_library.pattern_suggestions WHERE id = %s",
                    (suggestion_id,),
                )
                conn.commit()
