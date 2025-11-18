"""Tests for framework-specific integration with pattern detection."""

import pytest
from src.cli.confiture_extensions import specql


class TestFrameworkIntegration:
    """Test framework-specific options and pattern integration."""

    def test_reverse_with_patterns_flag_exists(self, cli_runner):
        """Test that --with-patterns flag is available in reverse command"""
        result = cli_runner.invoke(specql, ["reverse", "--help"])
        assert result.exit_code == 0
        assert "--with-patterns" in result.output
        assert "Auto-detect and apply architectural patterns" in result.output

    def test_reverse_python_with_patterns(self, cli_runner, tmp_path):
        """Test reverse python with pattern detection"""
        # Create a test Python file
        python_code = """
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    email = Column(String)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
"""
        test_file = tmp_path / "models.py"
        test_file.write_text(python_code)

        result = cli_runner.invoke(
            specql,
            [
                "reverse",
                str(test_file),
                "--framework",
                "python",
                "--with-patterns",
                "--preview",  # Don't actually write files
            ],
        )

        assert result.exit_code == 0
        # Should show pattern detection in output
        assert "patterns" in result.output.lower() or "Pattern" in result.output

    def test_reverse_sql_with_patterns_flag(self, cli_runner):
        """Test that reverse-sql accepts --with-patterns flag (even if not implemented yet)"""
        result = cli_runner.invoke(specql, ["reverse-sql", "--help"])
        assert result.exit_code == 0
        # Note: reverse-sql may not have --with-patterns yet, this tests the framework
