# tests/unit/cli/commands/test_reverse.py
"""Tests for the reverse engineering CLI commands."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Click CLI runner for testing commands."""
    return CliRunner()


# ==============================================================================
# Reverse Group Tests
# ==============================================================================


def test_reverse_group_exists():
    """Reverse command group should exist in main CLI."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "reverse" in result.output


def test_reverse_help_shows_subcommands():
    """Reverse --help should show all subcommands."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "--help"])

    assert result.exit_code == 0
    assert "sql" in result.output
    assert "python" in result.output
    assert "typescript" in result.output
    assert "rust" in result.output
    assert "project" in result.output


# ==============================================================================
# Reverse SQL - Argument Tests
# ==============================================================================


def test_reverse_sql_requires_files():
    """Reverse sql should require at least one file."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "sql"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_reverse_sql_requires_output_dir():
    """Reverse sql should require output directory."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("test.sql").write_text("SELECT 1;")
        result = runner.invoke(app, ["reverse", "sql", "test.sql"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "--output-dir" in result.output


# ==============================================================================
# Reverse SQL - Integration Tests (with mocked parsers)
# ==============================================================================


@pytest.fixture
def mock_table_parser():
    """Mock SQLTableParser for tests without pglast."""
    with patch("reverse_engineering.table_parser.SQLTableParser") as mock:
        parser_instance = MagicMock()
        mock.return_value = parser_instance

        # Create mock ParsedTable
        from dataclasses import dataclass

        @dataclass
        class MockColumn:
            name: str
            type: str
            specql_type: str
            nullable: bool = True

        @dataclass
        class MockParsedTable:
            schema: str
            table_name: str
            columns: list
            primary_key: list = None

        parser_instance.parse_table.return_value = MockParsedTable(
            schema="crm",
            table_name="tb_contact",
            columns=[
                MockColumn("pk_contact", "INTEGER", "integer", False),
                MockColumn("id", "UUID", "uuid", False),
                MockColumn("email", "TEXT", "text", False),
                MockColumn("created_at", "TIMESTAMPTZ", "timestamp", True),
            ],
            primary_key=["pk_contact"],
        )
        yield mock


@pytest.fixture
def sample_sql_ddl():
    """Sample CREATE TABLE SQL for testing."""
    return """
CREATE TABLE crm.tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT NOT NULL,
    email TEXT NOT NULL,
    company TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""


@pytest.fixture
def sample_sql_with_fk():
    """Sample SQL with foreign key for testing."""
    return """
CREATE TABLE crm.tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    fk_company INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE crm.tb_contact ADD CONSTRAINT fk_contact_company
    FOREIGN KEY (fk_company) REFERENCES management.tb_organization(pk_organization);
"""


def test_reverse_sql_preview_mode(cli_runner, sample_sql_ddl):
    """Reverse sql --preview should not write files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("tables.sql").write_text(sample_sql_ddl)
        Path("out").mkdir()

        # Mock the parsers to avoid pglast dependency - patch at the source module
        with patch("reverse_engineering.table_parser.SQLTableParser") as MockParser:
            from dataclasses import dataclass

            @dataclass
            class MockColumn:
                name: str
                type: str
                specql_type: str
                nullable: bool = True

            @dataclass
            class MockTable:
                schema: str
                table_name: str
                columns: list
                primary_key: list = None

            parser_instance = MagicMock()
            parser_instance.parse_table.return_value = MockTable(
                schema="crm",
                table_name="tb_contact",
                columns=[MockColumn("email", "TEXT", "text", False)],
            )
            MockParser.return_value = parser_instance

            with patch("reverse_engineering.pattern_orchestrator.PatternDetectionOrchestrator"):
                with patch("reverse_engineering.fk_detector.ForeignKeyDetector"):
                    with patch(
                        "reverse_engineering.entity_generator.EntityYAMLGenerator"
                    ) as MockGen:
                        gen_instance = MagicMock()
                        gen_instance._table_to_entity_name.return_value = "Contact"
                        MockGen.return_value = gen_instance

                        result = cli_runner.invoke(
                            app, ["reverse", "sql", "tables.sql", "-o", "out/", "--preview"]
                        )

        # Preview should not create files
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) == 0
        assert "Preview" in result.output or "preview" in result.output.lower()


def test_reverse_sql_creates_output_directory(cli_runner, sample_sql_ddl):
    """Reverse sql should create output directory if it doesn't exist."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("tables.sql").write_text(sample_sql_ddl)

        # Directory should not exist yet
        assert not Path("new_output").exists()

        # Mock the parsers - patch at the source module
        with patch("reverse_engineering.table_parser.SQLTableParser") as MockParser:
            from dataclasses import dataclass

            @dataclass
            class MockColumn:
                name: str
                type: str
                specql_type: str
                nullable: bool = True

            @dataclass
            class MockTable:
                schema: str
                table_name: str
                columns: list
                primary_key: list = None

            parser_instance = MagicMock()
            parser_instance.parse_table.return_value = MockTable(
                schema="crm",
                table_name="tb_contact",
                columns=[MockColumn("email", "TEXT", "text", False)],
            )
            MockParser.return_value = parser_instance

            with patch(
                "reverse_engineering.pattern_orchestrator.PatternDetectionOrchestrator"
            ) as MockPattern:
                pattern_instance = MagicMock()
                pattern_instance.detect_all.return_value = MagicMock(
                    patterns=["trinity"], confidence=0.9
                )
                MockPattern.return_value = pattern_instance

                with patch("reverse_engineering.fk_detector.ForeignKeyDetector"):
                    with patch(
                        "reverse_engineering.entity_generator.EntityYAMLGenerator"
                    ) as MockGen:
                        gen_instance = MagicMock()
                        gen_instance._table_to_entity_name.return_value = "Contact"
                        gen_instance.generate.return_value = "entity: Contact\nschema: crm\n"
                        MockGen.return_value = gen_instance

                        result = cli_runner.invoke(
                            app, ["reverse", "sql", "tables.sql", "-o", "new_output/"]
                        )

        # Directory should have been created
        assert Path("new_output").exists()


# ==============================================================================
# Reverse SQL - Statement Extraction Tests
# ==============================================================================


def test_extract_statements_finds_create_table():
    """_extract_statements should find CREATE TABLE statements."""
    from cli.commands.reverse.sql import _extract_statements

    sql = """
    CREATE TABLE crm.tb_contact (
        pk_contact SERIAL PRIMARY KEY,
        email TEXT NOT NULL
    );
    """

    tables, functions, alters = _extract_statements(sql)

    assert len(tables) == 1
    assert "CREATE TABLE" in tables[0]
    assert "crm.tb_contact" in tables[0]


def test_extract_statements_finds_multiple_tables():
    """_extract_statements should find multiple CREATE TABLE statements."""
    from cli.commands.reverse.sql import _extract_statements

    sql = """
    CREATE TABLE crm.tb_contact (pk_contact SERIAL PRIMARY KEY);

    CREATE TABLE crm.tb_task (pk_task SERIAL PRIMARY KEY);
    """

    tables, functions, alters = _extract_statements(sql)

    assert len(tables) == 2


def test_extract_statements_finds_alter_table_fk():
    """_extract_statements should find ALTER TABLE FOREIGN KEY statements."""
    from cli.commands.reverse.sql import _extract_statements

    sql = """
    ALTER TABLE crm.tb_contact ADD CONSTRAINT fk_contact_company
        FOREIGN KEY (fk_company) REFERENCES management.tb_organization(pk_organization);
    """

    tables, functions, alters = _extract_statements(sql)

    assert len(alters) == 1
    assert "FOREIGN KEY" in alters[0]


def test_extract_statements_handles_if_not_exists():
    """_extract_statements should handle IF NOT EXISTS clause."""
    from cli.commands.reverse.sql import _extract_statements

    sql = """
    CREATE TABLE IF NOT EXISTS crm.tb_contact (
        pk_contact SERIAL PRIMARY KEY
    );
    """

    tables, functions, alters = _extract_statements(sql)

    assert len(tables) == 1


# ==============================================================================
# Reverse Project Tests
# ==============================================================================


def test_reverse_project_requires_directory():
    """Reverse project should require a directory argument."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "project"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_reverse_project_accepts_directory():
    """Reverse project should accept directory arguments."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("test_dir").mkdir()
        # Create a manage.py to make it detectable as Django
        Path("test_dir/manage.py").touch()
        result = runner.invoke(app, ["reverse", "project", "test_dir", "-o", "output"])

        assert result.exit_code == 0
        assert "Analyzing project" in result.output


# ==============================================================================
# Reverse SQL - Options Tests
# ==============================================================================


def test_reverse_sql_min_confidence_option():
    """Reverse sql should accept --min-confidence option."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "sql", "--help"])

    assert "--min-confidence" in result.output


def test_reverse_sql_no_ai_option():
    """Reverse sql should accept --no-ai option."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "sql", "--help"])

    assert "--no-ai" in result.output


def test_reverse_sql_with_patterns_option():
    """Reverse sql should accept --with-patterns option."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "sql", "--help"])

    assert "--with-patterns" in result.output


# ==============================================================================
# Reverse SQL - Error Handling Tests
# ==============================================================================


def test_reverse_sql_handles_missing_dependency():
    """Reverse sql should give helpful error when pglast is missing."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("test.sql").write_text("CREATE TABLE test (id INT);")

        # Mock ImportError for pglast - patch at the source module
        with patch(
            "reverse_engineering.table_parser.SQLTableParser",
            side_effect=ImportError("No module named 'pglast'"),
        ):
            result = runner.invoke(app, ["reverse", "sql", "test.sql", "-o", "out/"])

            # Should show helpful message about installing
            assert (
                "reverse" in result.output.lower()
                or "pglast" in result.output.lower()
                or "dependency" in result.output.lower()
            )


def test_reverse_sql_handles_parse_error():
    """Reverse sql should handle parse errors gracefully."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Invalid SQL
        Path("bad.sql").write_text("THIS IS NOT VALID SQL;")
        Path("out").mkdir()

        # Mock the parser to return no results - patch at the source module
        with patch("reverse_engineering.table_parser.SQLTableParser") as MockParser:
            parser_instance = MagicMock()
            parser_instance.parse_table.side_effect = ValueError("Parse error")
            MockParser.return_value = parser_instance

            with patch("reverse_engineering.pattern_orchestrator.PatternDetectionOrchestrator"):
                with patch("reverse_engineering.fk_detector.ForeignKeyDetector"):
                    with patch("reverse_engineering.entity_generator.EntityYAMLGenerator"):
                        result = runner.invoke(app, ["reverse", "sql", "bad.sql", "-o", "out/"])

        # Should not crash, just report issues
        assert result.exit_code == 0 or "error" in result.output.lower()
