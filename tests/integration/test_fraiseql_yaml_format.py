"""
End-to-end integration test for FraiseQL YAML format
Tests that complete SpecQL → SQL pipeline generates YAML-formatted comments
"""

import pytest

# Mark all tests as requiring database
pytestmark = pytest.mark.database

from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator


@pytest.fixture
def parser():
    """Create SpecQL parser"""
    return SpecQLParser()


@pytest.fixture
def orchestrator():
    """Create schema orchestrator"""
    return SchemaOrchestrator()


def test_complete_pipeline_generates_yaml_comments(parser, orchestrator):
    """Complete SpecQL → SQL pipeline should generate YAML-formatted comments"""
    yaml_content = """
    entity: Contact
    schema: crm
    description: Customer contact information
    fields:
      email: email!
      company: ref(Company)
      status: enum(lead, qualified)
    actions:
      - name: create_contact
        steps:
          - validate: email IS NOT NULL
          - insert: Contact
      - name: qualify_lead
        steps:
          - validate: status = 'lead'
          - update: Contact SET status = 'qualified'
    """

    # Parse
    entity = parser.parse(yaml_content)

    # Generate
    sql = orchestrator.generate_complete_schema(entity)

    # Verify YAML format in comments

    # 1. Table comment
    assert "COMMENT ON TABLE crm.tb_contact IS" in sql
    assert "@fraiseql:type" in sql
    assert "trinity: true" in sql

    # 2. Column comments
    assert "COMMENT ON COLUMN crm.tb_contact.id IS" in sql
    assert "@fraiseql:field" in sql
    assert "name: id" in sql  # YAML format
    assert "type: UUID!" in sql
    assert "required: true" in sql

    # 3. Composite type comments
    assert "COMMENT ON TYPE app.type_create_contact_input IS" in sql
    assert "@fraiseql:composite" in sql
    assert "name: CreateContactInput" in sql
    assert "tier: 2" in sql

    # 4. Function comments
    assert "COMMENT ON FUNCTION app.create_contact IS" in sql
    assert "@fraiseql:mutation" in sql
    assert "name: createContact" in sql
    assert "input_type: app.type_create_contact_input" in sql

    # Verify NO old format remains
    assert "@fraiseql:type name=" not in sql  # Old format
    assert "@fraiseql:field name=email,type=" not in sql  # Old format
