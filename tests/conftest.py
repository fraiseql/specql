"""
Pytest configuration and shared fixtures
"""
from pathlib import Path
from typing import Any, Dict

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory"""
    return Path(__file__).parent / 'fixtures'


@pytest.fixture
def entity_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return path to entity YAML fixtures"""
    return fixtures_dir / 'entities'


@pytest.fixture
def simple_contact_yaml(entity_fixtures_dir: Path) -> str:
    """Return simple contact entity YAML"""
    return """
entity: Contact
  schema: crm
  description: "Simple CRM contact"

  fields:
    first_name: text
    last_name: text
    email: text
    status: enum(lead, qualified, customer)

  actions:
    - name: create_contact
      steps:
        - validate: email MATCHES email_pattern
          error: "invalid_email"
        - insert: Contact
"""


@pytest.fixture
def mock_entity_dict() -> Dict[str, Any]:
    """Return mock entity dictionary for testing"""
    return {
        'entity': {
            'name': 'Contact',
            'schema': 'crm',
            'description': 'Mock contact entity',
            'fields': {
                'email': {'type': 'text', 'nullable': False},
                'status': {'type': 'enum', 'values': ['lead', 'qualified']}
            },
            'actions': [
                {
                    'name': 'create_contact',
                    'steps': [
                        {'validate': 'email MATCHES email_pattern', 'error': 'invalid_email'},
                        {'insert': 'Contact'}
                    ]
                }
            ]
        }
    }


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create temporary output directory for generated files"""
    output_dir = tmp_path / 'generated'
    output_dir.mkdir(exist_ok=True)
    return output_dir


# Markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (slower)")
    config.addinivalue_line("markers", "benchmark: Performance benchmarks")
