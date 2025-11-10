"""CLI test fixtures and configuration."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator


@pytest.fixture
def cli_runner():
    """Click CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_entity_yaml():
    """Sample entity YAML content for testing."""
    return """
entity: Contact
schema: crm
description: "Contact entity for CRM"

fields:
  email: text
  first_name: text
  last_name: text
  phone: text

actions:
  - name: create
    type: create
    description: "Create a new contact"

  - name: update
    type: update
    description: "Update contact information"
"""


@pytest.fixture
def sample_entity_file(temp_dir, sample_entity_yaml):
    """Create a temporary entity YAML file."""
    entity_file = temp_dir / "contact.yaml"
    entity_file.write_text(sample_entity_yaml)
    return entity_file


@pytest.fixture
def multiple_entity_files(temp_dir, sample_entity_yaml):
    """Create multiple temporary entity YAML files."""
    files = []

    # Contact entity
    contact_file = temp_dir / "contact.yaml"
    contact_file.write_text(sample_entity_yaml)
    files.append(contact_file)

    # Task entity
    task_yaml = """
entity: Task
schema: crm
description: "Task entity for CRM"

fields:
  title: text
  description: text
  priority: enum(low, medium, high)

actions:
  - name: create
    type: create
"""
    task_file = temp_dir / "task.yaml"
    task_file.write_text(task_yaml)
    files.append(task_file)

    return files


@pytest.fixture
def specql_parser():
    """SpecQL parser instance."""
    return SpecQLParser()


@pytest.fixture
def schema_orchestrator():
    """Schema orchestrator instance."""
    return SchemaOrchestrator()


@pytest.fixture
def parsed_entity(specql_parser, sample_entity_yaml):
    """Parsed entity definition."""
    return specql_parser.parse(sample_entity_yaml)


@pytest.fixture
def output_dir(temp_dir):
    """Output directory for generated files."""
    output = temp_dir / "output"
    output.mkdir()
    return output
