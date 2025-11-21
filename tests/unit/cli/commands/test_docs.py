"""Tests for docs CLI command."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def sample_entity_yaml():
    return """
entity: Contact
schema: crm
description: Contact management entity

fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)

actions:
  - name: create_contact
    description: Create a new contact
    steps:
      - insert: Contact
"""


# ============================================================================
# Basic CLI argument tests
# ============================================================================


def test_docs_requires_files():
    """docs should require file arguments."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["docs"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Error" in result.output


def test_docs_shows_in_help():
    """docs should appear in main help."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "docs" in result.output


def test_docs_help_shows_options():
    """docs --help should show all options."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["docs", "--help"])

    assert result.exit_code == 0
    assert "--output" in result.output or "-o" in result.output
    assert "--format" in result.output


def test_docs_file_not_found(cli_runner):
    """docs should error on missing file."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        result = cli_runner.invoke(app, ["docs", "nonexistent.yaml", "-o", "out/"])

        assert result.exit_code != 0


# ============================================================================
# Basic documentation generation tests
# ============================================================================


def test_docs_creates_output_directory(cli_runner, sample_entity_yaml):
    """docs should create output directory if it doesn't exist."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "docs/generated/"])

        assert result.exit_code == 0
        assert Path("docs/generated/").exists()


def test_docs_generates_index(cli_runner, sample_entity_yaml):
    """docs should generate an index.md file."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        assert Path("out/index.md").exists()


def test_docs_generates_entity_docs(cli_runner, sample_entity_yaml):
    """docs should generate entity-specific documentation."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        entity_docs = list(Path("out/entities/").glob("*.md"))
        assert len(entity_docs) >= 1


def test_docs_preview_mode(cli_runner, sample_entity_yaml):
    """docs --preview should not write files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/", "--preview"])

        assert result.exit_code == 0
        # Should not create any files in preview mode
        assert not Path("out/index.md").exists()


# ============================================================================
# Entity documentation content tests
# ============================================================================


def test_docs_entity_has_name(cli_runner, sample_entity_yaml):
    """Entity docs should include entity name."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        entity_doc = Path("out/entities/contact.md").read_text()
        assert "Contact" in entity_doc


def test_docs_entity_has_fields_table(cli_runner, sample_entity_yaml):
    """Entity docs should include fields table."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        entity_doc = Path("out/entities/contact.md").read_text()
        assert "email" in entity_doc
        assert "first_name" in entity_doc


def test_docs_entity_has_description(cli_runner, sample_entity_yaml):
    """Entity docs should include entity description."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        entity_doc = Path("out/entities/contact.md").read_text()
        assert "Contact management" in entity_doc


def test_docs_entity_shows_references(cli_runner, sample_entity_yaml):
    """Entity docs should show reference fields."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        entity_doc = Path("out/entities/contact.md").read_text()
        assert "Company" in entity_doc or "ref" in entity_doc


def test_docs_entity_shows_enums(cli_runner, sample_entity_yaml):
    """Entity docs should show enum values."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        entity_doc = Path("out/entities/contact.md").read_text()
        assert "lead" in entity_doc or "qualified" in entity_doc


# ============================================================================
# Mutation documentation tests
# ============================================================================


def test_docs_generates_mutations_doc(cli_runner, sample_entity_yaml):
    """docs should generate mutations documentation."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        assert Path("out/mutations/mutations.md").exists()


def test_docs_mutations_has_action_reference(cli_runner, sample_entity_yaml):
    """Mutations doc should reference entity actions."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/"])

        assert result.exit_code == 0
        mutations_doc = Path("out/mutations/mutations.md").read_text()
        assert "create_contact" in mutations_doc


# ============================================================================
# Format tests
# ============================================================================


def test_docs_json_format(cli_runner, sample_entity_yaml):
    """docs --format=json should generate JSON output."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/", "--format", "json"])

        assert result.exit_code == 0
        assert Path("out/docs.json").exists()


def test_docs_html_format(cli_runner, sample_entity_yaml):
    """docs --format=html should generate HTML output."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.yaml").write_text(sample_entity_yaml)

        result = cli_runner.invoke(app, ["docs", "contact.yaml", "-o", "out/", "--format", "html"])

        assert result.exit_code == 0
        html_files = list(Path("out/").glob("**/*.html"))
        assert len(html_files) >= 1
