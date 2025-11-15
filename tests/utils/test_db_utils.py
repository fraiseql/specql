"""
Test database utilities for round-trip testing.

Provides utilities for creating isolated test databases and executing SQL.
"""

import uuid
import psycopg
import psycopg.sql
from typing import Optional


def get_test_connection(db_name: str) -> psycopg.Connection:
    """
    Get a connection to a test database.

    Args:
        db_name: Database name

    Returns:
        psycopg connection object
    """
    # Use default connection parameters - assumes PostgreSQL is running locally
    conn_string = f"postgresql://lionel@localhost:5432/{db_name}"
    return psycopg.connect(conn_string)


def create_test_database(prefix: str = "test_") -> str:
    """
    Create a unique test database.

    Args:
        prefix: Prefix for database name

    Returns:
        Database name
    """
    db_name = f"{prefix}{uuid.uuid4().hex[:8]}"

    # Connect to default database to create the test database
    with psycopg.connect("postgresql://lionel@localhost:5432/specql_test") as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {db_name}")  # type: ignore

    return db_name


def drop_test_database(db_name: str):
    """
    Drop a test database.

    Args:
        db_name: Database name to drop
    """
    try:
        # Connect to default database to drop the test database
        with psycopg.connect("postgresql://lionel@localhost:5432/specql_test") as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # Terminate any active connections to the database
                cur.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                    (db_name,),
                )

                # Drop the database
                cur.execute(f"DROP DATABASE IF EXISTS {db_name}")  # type: ignore
    except Exception as e:
        # Log but don't fail - cleanup errors are not critical
        print(f"Warning: Could not drop test database {db_name}: {e}")


def execute_sql(conn: psycopg.Connection, sql: str):
    """
    Execute SQL statement(s).

    Args:
        conn: Database connection
        sql: SQL to execute (can contain multiple statements)
    """
    with conn.cursor() as cur:
        # Split on semicolons and execute each statement
        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        for statement in statements:
            if statement:
                # Use string directly - psycopg allows this in practice
                cur.execute(statement)  # type: ignore


def database_exists(db_name: str) -> bool:
    """
    Check if a database exists.

    Args:
        db_name: Database name to check

    Returns:
        True if database exists
    """
    try:
        with psycopg.connect("postgresql://lionel@localhost:5432/specql_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM pg_database WHERE datname = %s
                """,
                    (db_name,),
                )  # type: ignore
                return cur.fetchone() is not None
    except Exception:
        return False


def get_database_size(db_name: str) -> Optional[int]:
    """
    Get the size of a database in bytes.

    Args:
        db_name: Database name

    Returns:
        Size in bytes, or None if database doesn't exist
    """
    try:
        with psycopg.connect("postgresql://lionel@localhost:5432/specql_test") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT pg_database_size(%s)
                """,
                    (db_name,),
                )  # type: ignore
                result = cur.fetchone()
                return result[0] if result else None
    except Exception:
        return None
