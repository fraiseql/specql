"""Integration test for table_code extraction through the full pipeline

This test verifies that table_code flows correctly from YAML → EntityDefinition → Entity
and can be used by downstream generators.
"""

import pytest

from cli.generate import convert_entity_definition_to_entity
from core.specql_parser import SpecQLParser


def test_table_code_integration_from_yaml():
    """Test that table_code flows from YAML through the entire parsing pipeline"""

    # Create test YAML content
    yaml_content = """
entity: Machine
schema: tenant

organization:
  table_code: "014511"
  domain_name: "Dimensions"

description: |
  Represents a physical printing device.

fields:
  code:
    type: text
    nullable: false
    description: "Machine identifier code"

  serial_number:
    type: text
    description: "Manufacturer serial number"
"""

    # Parse YAML → EntityDefinition
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)

    # Verify EntityDefinition has organization.table_code
    assert entity_def.organization is not None
    assert entity_def.organization.table_code == "014511"
    assert entity_def.organization.domain_name == "Dimensions"

    # Convert EntityDefinition → Entity
    entity = convert_entity_definition_to_entity(entity_def)

    # Verify Entity has extracted table_code
    assert (
        entity.table_code == "014511"
    ), f"Expected entity.table_code='014511', got '{entity.table_code}'"

    # Verify organization is preserved
    assert entity.organization is not None
    assert entity.organization.table_code == "014511"

    # Verify other fields are correct
    assert entity.name == "Machine"
    assert entity.schema == "tenant"
    assert "code" in entity.fields
    assert "serial_number" in entity.fields


def test_table_code_integration_without_organization():
    """Test that entities without organization field still work"""

    yaml_content = """
entity: SimpleEntity
schema: tenant

fields:
  name: text
"""

    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    entity = convert_entity_definition_to_entity(entity_def)

    # Should have None for table_code
    assert entity.table_code is None
    assert entity.organization is None


def test_table_code_integration_with_crm_entity():
    """Test with realistic CRM-style entity"""

    yaml_content = """
entity: Contact
schema: crm

organization:
  table_code: "012321"
  domain_name: "CRM"

description: |
  [012321 | Write-Side.CRM.Engagement.Contact]
  Customer contact information.

fields:
  email:
    type: text
    nullable: false

  company:
    type: text

  status:
    type: text
"""

    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    entity = convert_entity_definition_to_entity(entity_def)

    assert entity.table_code == "012321"
    assert entity.schema == "crm"
    assert entity.organization.domain_name == "CRM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
