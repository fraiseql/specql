"""
Tests for safe_slug utility function
Tests that safe_slug function handles all edge cases correctly
"""

import psycopg
import pytest


@pytest.fixture
def test_db():
    """PostgreSQL test database connection"""
    try:
        conn = psycopg.connect(
            host="localhost", dbname="test_specql", user="postgres", password="postgres"
        )
        # Enable required extensions
        conn.cursor().execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
        conn.commit()
        yield conn
        conn.close()
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL not available for integration tests")


def execute_sql(db, query):
    """Helper to execute SQL and return single result"""
    cursor = db.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None


class TestSafeSlug:
    """Test safe_slug utility function."""

    def test_normal_text(self, test_db):
        # First create the function
        test_db.cursor().execute("""
            CREATE OR REPLACE FUNCTION public.safe_slug(
                value TEXT,
                fallback TEXT DEFAULT 'unnamed'
            ) RETURNS TEXT AS $$
            DECLARE
                result TEXT;
            BEGIN
                -- Handle NULL or empty input
                IF value IS NULL OR trim(value) = '' THEN
                    RETURN fallback;
                END IF;

                -- Convert to slug: lowercase + unaccent + replace non-alphanumeric with '-'
                result := trim(BOTH '-' FROM regexp_replace(
                    lower(unaccent(value)),
                    '[^a-z0-9]+', '-', 'gi'
                ));

                -- Handle edge cases
                IF result = '' THEN
                    -- All characters were stripped (e.g., "---" or "###")
                    RETURN fallback;
                ELSIF result ~ '^[0-9]+$' THEN
                    -- All digits (e.g., "123") - prefix with 'n-' to avoid LTREE issues
                    RETURN 'n-' || result;
                ELSE
                    RETURN result;
                END IF;
            END;
            $$ LANGUAGE plpgsql IMMUTABLE STRICT;
        """)
        test_db.commit()

        result = execute_sql(test_db, "SELECT safe_slug('Normal Text')")
        assert result == "normal-text"

    def test_unicode_unaccent(self, test_db):
        result = execute_sql(test_db, "SELECT safe_slug('Café Straße')")
        assert result == "cafe-strasse"

    def test_special_characters(self, test_db):
        result = execute_sql(test_db, "SELECT safe_slug('Building #1')")
        assert result == "building-1"

    def test_all_digits(self, test_db):
        result = execute_sql(test_db, "SELECT safe_slug('123')")
        assert result == "n-123"

    def test_empty_string(self, test_db):
        result = execute_sql(test_db, "SELECT safe_slug('')")
        assert result == "unnamed"

    def test_all_special(self, test_db):
        result = execute_sql(test_db, "SELECT safe_slug('---')")
        assert result == "unnamed"

    def test_custom_fallback(self, test_db):
        result = execute_sql(test_db, "SELECT safe_slug('', 'default')")
        assert result == "default"

    def test_null_input(self, test_db):
        result = execute_sql(test_db, "SELECT safe_slug(NULL)")
        assert result == "unnamed"
