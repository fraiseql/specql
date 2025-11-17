"""Pytest fixtures for database integration tests"""

import os
from pathlib import Path

import psycopg
import pytest


@pytest.fixture(scope="session")
def db_config():
    """Database configuration from environment or defaults"""
    return {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "port": int(os.getenv("TEST_DB_PORT", "5432")),
        "dbname": os.getenv("TEST_DB_NAME", "specql_test"),
        "user": os.getenv("TEST_DB_USER", os.getenv("USER")),
        "password": os.getenv("TEST_DB_PASSWORD", ""),
    }


@pytest.fixture(scope="session")
def test_db_connection(db_config):
    """
    Create database connection for integration tests

    Environment variables (optional):
    - TEST_DB_HOST: Database host (default: localhost)
    - TEST_DB_PORT: Database port (default: 5432)
    - TEST_DB_NAME: Database name (default: specql_test)
    - TEST_DB_USER: Database user (default: current user)
    - TEST_DB_PASSWORD: Database password (default: empty)

    To skip database tests:
        pytest -m "not database"
    """
    try:
        # Build connection string
        conn_parts = [
            f"host={db_config['host']}",
            f"port={db_config['port']}",
            f"dbname={db_config['dbname']}",
            f"user={db_config['user']}",
        ]

        if db_config["password"]:
            conn_parts.append(f"password={db_config['password']}")

        conn_string = " ".join(conn_parts)

        # Connect
        conn = psycopg.connect(conn_string, autocommit=False)

        # Verify connection
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"\n✅ Database connected: {version[:50]}...")

        yield conn

        # Cleanup
        conn.close()

    except psycopg.OperationalError as e:
        pytest.skip(
            f"Database not available: {e}\n"
            f"To run database tests:\n"
            f"  1. Create database: createdb {db_config['dbname']}\n"
            f"  2. Run tests again (schema will be auto-deployed)"
        )


@pytest.fixture(scope="session")
def deploy_test_schema(test_db_connection):
    """
    Deploy test database schema if not already present.

    This fixture automatically loads:
    - setup_test_db.sql (schemas, tables, types, helper functions)
    - contact_actions.sql (Contact entity actions)

    Runs once per test session.
    """
    with test_db_connection.cursor() as cur:
        # Check if the create_contact function exists (more specific than just schema)
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid "
            "WHERE n.nspname = 'app' AND p.proname = 'create_contact')"
        )
        functions_exist = cur.fetchone()[0]

        if not functions_exist:
            print("\n🔧 Deploying test database schema...")

            # Load setup_test_db.sql
            test_dir = Path(__file__).parent
            setup_sql = test_dir / "setup_test_db.sql"
            actions_sql = test_dir / "contact_actions.sql"

            if setup_sql.exists():
                print("  📄 Loading setup_test_db.sql...")
                cur.execute(setup_sql.read_text())

            if actions_sql.exists():
                print("  📄 Loading contact_actions.sql...")
                cur.execute(actions_sql.read_text())

            test_db_connection.commit()
            print("  ✅ Schema deployed successfully")
        else:
            print("\n✅ Test schema already deployed")

    yield

    # No cleanup - keep schema for the entire session


@pytest.fixture
def clean_contact_table(test_db_connection):
    """Clean contact table before each test"""
    with test_db_connection.cursor() as cur:
        cur.execute("DELETE FROM crm.tb_contact")
        cur.execute("DELETE FROM crm.tb_company")
    test_db_connection.commit()

    yield test_db_connection

    # Cleanup after test
    test_db_connection.rollback()
