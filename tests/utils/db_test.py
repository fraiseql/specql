"""
Database test utilities for unit tests that need PostgreSQL access.
"""

import psycopg
import pytest


@pytest.fixture
def db():
    """PostgreSQL test database connection"""
    try:
        conn = psycopg.connect(
            host="localhost", dbname="test_specql", user="postgres", password="postgres"
        )
        # Enable required extensions
        conn.cursor().execute("CREATE EXTENSION IF NOT EXISTS ltree;")
        conn.commit()
        yield conn
        conn.close()
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL not available for integration tests")


def execute_sql(db, query, *args):
    """Execute SQL query and return all results"""
    cursor = db.cursor()
    cursor.execute(query, args)
    return cursor.fetchall()


def execute_query(db, query, *args):
    """Execute SQL query and return single result as dict"""
    cursor = db.cursor()
    cursor.execute(query, args)
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    result = cursor.fetchone()
    if result:
        return dict(zip(columns, result))
    return None
