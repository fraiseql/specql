"""Tests for Core Logic Generator (Team C)"""

import pytest
from src.generators.core_logic_generator import CoreLogicGenerator
from src.core.ast_models import Entity, FieldDefinition


def test_generate_core_create_function():
    """Generate core create function with full pattern"""
    # Given: Entity with fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type="text", nullable=False),
            "company": FieldDefinition(
                name="company", type="ref", target_entity="Company", nullable=True
            ),
            "status": FieldDefinition(
                name="status", type="enum", values=["lead", "qualified"], nullable=False
            ),
        },
    )

    # When: Generate core function
    generator = CoreLogicGenerator()
    sql = generator.generate_core_create_function(entity)

    # Then: Correct signature
    assert "CREATE OR REPLACE FUNCTION crm.create_contact(" in sql
    assert "auth_tenant_id UUID" in sql
    assert "input_data app.type_create_contact_input" in sql
    assert "input_payload JSONB" in sql
    assert "auth_user_id UUID" in sql
    assert "RETURNS app.mutation_result" in sql

    # Then: Validation logic
    assert "IF input_data.email IS NULL THEN" in sql
    assert "RETURN crm.log_and_return_mutation" in sql

    # Then: Trinity resolution (UUID → INTEGER) with tenant filtering
    assert "v_fk_company := crm.company_pk(input_data.company_id::TEXT, auth_tenant_id)" in sql

    # Then: INSERT with all fields
    assert "INSERT INTO crm.tb_contact (" in sql
    assert "tenant_id," in sql
    assert "created_by" in sql
    assert "VALUES (" in sql
    assert "auth_tenant_id," in sql  # tenant_id from JWT
    assert "auth_user_id" in sql  # created_by from JWT

    # Then: Return mutation result
    assert "RETURN crm.log_and_return_mutation" in sql


def test_core_function_uses_trinity_helpers():
    """Core function uses Team B's Trinity helpers"""
    # Given: Entity with foreign key
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={"company": FieldDefinition(name="company", type="ref", target_entity="Company")},
    )

    # When: Generate
    generator = CoreLogicGenerator()
    sql = generator.generate_core_create_function(entity)

    # Then: Uses entity_pk() helper with tenant_id for tenant-specific schema
    assert "crm.company_pk(input_data.company_id::TEXT, auth_tenant_id)" in sql


def test_core_function_populates_audit_fields():
    """Core function populates all audit fields"""
    # Given: Entity with basic fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={"email": FieldDefinition(name="email", type="text", nullable=False)},
    )

    # When: Generate
    generator = CoreLogicGenerator()
    sql = generator.generate_core_create_function(entity)

    # Then: All audit fields in INSERT
    assert "created_at," in sql
    assert "created_by" in sql
    # Then: Values from JWT and now()
    assert "now()" in sql
    assert "auth_user_id" in sql


def test_core_function_populates_tenant_id():
    """Core function populates denormalized tenant_id"""
    # Given: Entity with basic fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={"email": FieldDefinition(name="email", type="text", nullable=False)},
    )

    # When: Generate
    generator = CoreLogicGenerator()
    sql = generator.generate_core_create_function(entity)

    # Then: tenant_id in INSERT
    assert "tenant_id," in sql
    # Then: Value from JWT context
    assert "auth_tenant_id" in sql
