# tests/unit/cli/commands/reverse/test_python.py
"""Tests for reverse python CLI command."""

import sys
from pathlib import Path

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def sample_django_model():
    return '''
from django.db import models

class Contact(models.Model):
    email = models.CharField(max_length=255)
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="lead")

    class Meta:
        db_table = "contacts"
'''


@pytest.fixture
def sample_pydantic_model():
    return '''
from pydantic import BaseModel
from typing import Optional

class Contact(BaseModel):
    email: str
    company_id: Optional[int] = None
    status: str = "lead"
'''


@pytest.fixture
def sample_sqlalchemy_model():
    return '''
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
'''


@pytest.fixture
def sample_dataclass_model():
    return '''
from dataclasses import dataclass
from typing import Optional

@dataclass
class Contact:
    """A contact entity."""
    email: str
    company_id: Optional[int] = None
    status: str = "lead"
'''


# ============================================================================
# Basic CLI argument tests
# ============================================================================


def test_reverse_python_requires_files():
    """reverse python should require file arguments."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "python"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Error" in result.output


def test_reverse_python_requires_output_dir(cli_runner):
    """reverse python should require output directory."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text("class Foo: pass")
        result = cli_runner.invoke(app, ["reverse", "python", "models.py"])

        assert result.exit_code != 0


def test_reverse_python_file_not_found(cli_runner):
    """reverse python should error on missing file."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("out").mkdir()
        result = cli_runner.invoke(
            app, ["reverse", "python", "nonexistent.py", "-o", "out/"]
        )

        assert result.exit_code != 0


# ============================================================================
# Django model parsing tests
# ============================================================================


def test_reverse_python_parses_django_model(cli_runner, sample_django_model):
    """reverse python should parse Django models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        # Check YAML content
        yaml_content = yaml_files[0].read_text()
        assert "Contact" in yaml_content or "contact" in yaml_content


def test_reverse_python_detects_django_framework(cli_runner, sample_django_model):
    """reverse python should auto-detect Django framework."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        # Check output mentions Django
        assert "django" in result.output.lower()


def test_reverse_python_extracts_django_fields(cli_runner, sample_django_model):
    """reverse python should extract fields from Django models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        yaml_content = yaml_files[0].read_text()
        assert "email" in yaml_content


# ============================================================================
# Pydantic model parsing tests
# ============================================================================


def test_reverse_python_parses_pydantic_model(cli_runner, sample_pydantic_model):
    """reverse python should parse Pydantic models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("schemas.py").write_text(sample_pydantic_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "schemas.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1


def test_reverse_python_detects_pydantic_framework(cli_runner, sample_pydantic_model):
    """reverse python should auto-detect Pydantic framework."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("schemas.py").write_text(sample_pydantic_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "schemas.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        assert "pydantic" in result.output.lower()


# ============================================================================
# SQLAlchemy model parsing tests
# ============================================================================


def test_reverse_python_parses_sqlalchemy_model(cli_runner, sample_sqlalchemy_model):
    """reverse python should parse SQLAlchemy models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_sqlalchemy_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0


# ============================================================================
# Dataclass parsing tests
# ============================================================================


def test_reverse_python_parses_dataclass(cli_runner, sample_dataclass_model):
    """reverse python should parse dataclasses."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_dataclass_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0


# ============================================================================
# Preview mode tests
# ============================================================================


def test_reverse_python_preview_mode(cli_runner, sample_django_model):
    """reverse python --preview should not write files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/", "--preview"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) == 0


def test_reverse_python_preview_shows_entities(cli_runner, sample_django_model):
    """reverse python --preview should show what would be generated."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/", "--preview"]
        )

        assert result.exit_code == 0
        # Should mention the entity name in preview
        assert "contact" in result.output.lower() or "Contact" in result.output


# ============================================================================
# Framework override tests
# ============================================================================


def test_reverse_python_framework_override(cli_runner, sample_django_model):
    """reverse python --framework should override auto-detection."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/", "--framework", "sqlalchemy"]
        )

        # Should still work even if framework doesn't match
        assert result.exit_code == 0


# ============================================================================
# Multiple files tests
# ============================================================================


def test_reverse_python_multiple_files(cli_runner, sample_django_model):
    """reverse python should handle multiple files."""
    from cli.main import app

    task_model = sample_django_model.replace("Contact", "Task").replace("contact", "task")

    with cli_runner.isolated_filesystem():
        Path("contact.py").write_text(sample_django_model)
        Path("task.py").write_text(task_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "contact.py", "task.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        # Should generate YAML for both entities
        assert len(yaml_files) >= 1


# ============================================================================
# Edge case tests
# ============================================================================


def test_reverse_python_handles_empty_file(cli_runner):
    """reverse python should handle empty Python files gracefully."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("empty.py").write_text("")
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "empty.py", "-o", "out/"]
        )

        # Should not crash
        assert result.exit_code == 0


def test_reverse_python_handles_no_models(cli_runner):
    """reverse python should handle files with no model classes."""
    from cli.main import app

    non_model_code = '''
def helper_function():
    return 42

class NotAModel:
    """This is not a Django/Pydantic model."""
    x = 1
    y = 2
'''

    with cli_runner.isolated_filesystem():
        Path("utils.py").write_text(non_model_code)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "utils.py", "-o", "out/"]
        )

        # Should not crash, just find 0 entities
        assert result.exit_code == 0


def test_reverse_python_handles_syntax_error(cli_runner):
    """reverse python should handle Python syntax errors gracefully."""
    from cli.main import app

    invalid_python = '''
class Contact(models.Model:  # Missing closing paren
    email = models.CharField(max_length=255
'''

    with cli_runner.isolated_filesystem():
        Path("invalid.py").write_text(invalid_python)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "invalid.py", "-o", "out/"]
        )

        # Should handle error gracefully
        # Accept either success (skipped file) or controlled failure
        assert result.exit_code in [0, 1]


# ============================================================================
# YAML output format tests
# ============================================================================


def test_reverse_python_yaml_has_metadata(cli_runner, sample_django_model):
    """Generated YAML should include source metadata."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        yaml_content = yaml_files[0].read_text()
        # Should have metadata about source language
        assert "python" in yaml_content.lower() or "_metadata" in yaml_content


def test_reverse_python_yaml_has_entity_name(cli_runner, sample_django_model):
    """Generated YAML should have entity name."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        yaml_content = yaml_files[0].read_text()
        assert "entity:" in yaml_content
