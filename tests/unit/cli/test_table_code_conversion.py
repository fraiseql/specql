"""Test table_code extraction from organization to entity

This module tests the conversion function that bridges EntityDefinition
(parsed from YAML) to Entity (used by code generators), specifically
verifying that organization.table_code is properly extracted to entity.table_code.
"""

import pytest
from src.core.ast_models import EntityDefinition, Organization
from src.cli.generate import convert_entity_definition_to_entity


def test_table_code_extracted_from_organization():
    """Test that table_code is properly extracted from organization"""
    # Create EntityDefinition with organization.table_code
    org = Organization(table_code="012321", domain_name="CRM")
    entity_def = EntityDefinition(
        name="TestEntity",
        schema="tenant",
        description="Test entity",
        fields={},
        actions=[],
        agents=[],
        organization=org,
    )

    # Convert to Entity
    entity = convert_entity_definition_to_entity(entity_def)

    # Verify table_code was extracted
    assert entity.table_code == "012321", (
        f"Expected table_code='012321', got '{entity.table_code}'"
    )
    assert entity.organization is not None
    assert entity.organization.table_code == "012321"


def test_table_code_none_when_no_organization():
    """Test that table_code is None when organization is missing"""
    entity_def = EntityDefinition(
        name="TestEntity",
        schema="tenant",
        description="Test entity",
        fields={},
        actions=[],
        agents=[],
        organization=None,
    )

    entity = convert_entity_definition_to_entity(entity_def)

    assert entity.table_code is None
    assert entity.organization is None


def test_table_code_none_when_organization_has_no_code():
    """Test that table_code is None when organization exists but has no table_code"""
    org = Organization(table_code=None, domain_name="CRM")
    entity_def = EntityDefinition(
        name="TestEntity",
        schema="tenant",
        description="Test entity",
        fields={},
        actions=[],
        agents=[],
        organization=org,
    )

    entity = convert_entity_definition_to_entity(entity_def)

    assert entity.table_code is None
    assert entity.organization is not None


def test_table_code_extraction_with_six_digit_code():
    """Test extraction with properly formatted 6-digit table code"""
    org = Organization(table_code="014511", domain_name="Dimensions")
    entity_def = EntityDefinition(
        name="Machine",
        schema="tenant",
        description="Printing machine",
        fields={},
        actions=[],
        agents=[],
        organization=org,
    )

    entity = convert_entity_definition_to_entity(entity_def)

    assert entity.table_code == "014511"
    assert entity.organization.table_code == "014511"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
