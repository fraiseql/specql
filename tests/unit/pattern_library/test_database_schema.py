import pytest
import sqlite3
from pathlib import Path


def test_database_schema_creation():
    """Test that schema creates all required tables"""
    db_path = Path("test_pattern_library.db")

    # Create schema
    conn = sqlite3.connect(db_path)
    with open("src/pattern_library/schema.sql") as f:
        conn.executescript(f.read())

    # Verify tables exist
    cursor = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = [
        "patterns",
        "languages",
        "pattern_implementations",
        "universal_types",
        "type_mappings",
        "expression_patterns",
        "expression_implementations",
        "language_capabilities",
        "pattern_dependencies",
    ]

    for table in expected_tables:
        assert table in tables, f"Missing table: {table}"

    conn.close()
    db_path.unlink()


def test_pattern_insert():
    """Test inserting a pattern"""
    db_path = Path("test_pattern_library.db")
    conn = sqlite3.connect(db_path)

    # Should fail - schema not created yet
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("""
            INSERT INTO patterns (pattern_name, pattern_category, abstract_syntax)
            VALUES ('declare', 'primitive', '{}')
        """)

    conn.close()
