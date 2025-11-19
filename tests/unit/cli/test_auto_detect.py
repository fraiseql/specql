"""Tests for auto-detection functionality."""


import pytest

from src.cli.confiture_extensions import specql
from src.core.dependencies import PGLAST, TREE_SITTER_RUST


class TestAutoDetection:
    """Test auto-detection of source code languages."""

    @pytest.mark.skipif(not TREE_SITTER_RUST.available, reason="Requires tree-sitter-rust")
    def test_auto_detect_rust_file(self, cli_runner, tmp_path):
        """Auto-detect Rust source files"""
        # Create a test Rust file
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""
        #[derive(Debug)]
        struct User {
            id: i32,
            name: String,
        }
        """)

        result = cli_runner.invoke(specql, ["reverse", str(rust_file)])
        # Should auto-detect and process as Rust
        assert result.exit_code == 0
        assert "Rust" in result.output or "Processed" in result.output

    def test_auto_detect_typescript_file(self, cli_runner, tmp_path):
        """Auto-detect TypeScript files"""
        # Create a test TypeScript file
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("""
        interface User {
            id: number;
            name: string;
        }
        """)

        result = cli_runner.invoke(specql, ["reverse", str(ts_file)])
        # Should auto-detect and process as TypeScript
        assert result.exit_code == 0
        assert "TypeScript" in result.output or "Processed" in result.output

    def test_auto_detect_python_file(self, cli_runner, tmp_path):
        """Auto-detect Python files"""
        # Create a test Python file
        py_file = tmp_path / "test.py"
        py_file.write_text("""
        class User:
            def __init__(self, id: int, name: str):
                self.id = id
                self.name = name
        """)

        result = cli_runner.invoke(specql, ["reverse", str(py_file)])
        # Should auto-detect and process as Python
        assert result.exit_code == 0
        assert "Detected language: python" in result.output

    def test_auto_detect_java_file(self, cli_runner, tmp_path):
        """Auto-detect Java files"""
        # Create a test Java file
        java_file = tmp_path / "test.java"
        java_file.write_text("""
        public class User {
            private int id;
            private String name;
        }
        """)

        result = cli_runner.invoke(specql, ["reverse", str(java_file)])
        # Should auto-detect and process as Java
        assert result.exit_code == 0
        assert "Java" in result.output or "Processed" in result.output

    @pytest.mark.skipif(not PGLAST.available, reason="Requires pglast")
    def test_auto_detect_sql_file(self, cli_runner, tmp_path):
        """Auto-detect SQL files"""
        # Create a test SQL file
        sql_file = tmp_path / "test.sql"
        sql_file.write_text("""
        CREATE FUNCTION get_user(user_id INT)
        RETURNS TABLE(id INT, name TEXT) AS $$
        SELECT id, name FROM users WHERE id = user_id;
        $$ LANGUAGE SQL;
        """)

        result = cli_runner.invoke(specql, ["reverse", "--preview", str(sql_file)])
        # Should auto-detect and process as SQL
        assert result.exit_code == 0
        assert "Detected language: sql" in result.output

    @pytest.mark.skipif(not PGLAST.available, reason="Requires pglast")
    def test_explicit_framework_override(self, cli_runner, tmp_path):
        """Test explicit framework specification overrides auto-detection"""
        # Create a Python file but specify SQL framework
        py_file = tmp_path / "test.py"
        py_file.write_text("""
        class User:
            def __init__(self, id: int, name: str):
                self.id = id
                self.name = name
        """)

        result = cli_runner.invoke(
            specql, ["reverse", "--framework", "sql", "--preview", str(py_file)]
        )
        # Should NOT show "Detected language: python" and should try SQL parsing
        assert result.exit_code == 0
        assert "Detected language: python" not in result.output  # No auto-detection
        assert "Processing" in result.output  # SQL parser was invoked
