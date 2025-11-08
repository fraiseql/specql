"""Tests for Core Logic Generator (Team C)"""

import pytest
from src.generators.core_logic_generator import CoreLogicGenerator
from src.core.ast_models import Entity, FieldDefinition, ActionStep


def test_generate_core_create_function():
    """Generate core create function with full pattern"""
    # Given: Entity with fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="text", nullable=False),
            "company": FieldDefinition(
                name="company", type_name="ref", reference_entity="Company", nullable=True
            ),
            "status": FieldDefinition(
                name="status", type_name="enum", values=["lead", "qualified"], nullable=False
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
    assert "RETURN app.log_and_return_mutation" in sql

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
    assert "RETURN app.log_and_return_mutation" in sql


def test_core_function_uses_trinity_helpers():
    """Core function uses Team B's Trinity helpers"""
    # Given: Entity with foreign key
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company")
        },
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
        fields={"email": FieldDefinition(name="email", type_name="text", nullable=False)},
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
        fields={"email": FieldDefinition(name="email", type_name="text", nullable=False)},
    )

    # When: Generate
    generator = CoreLogicGenerator()
    sql = generator.generate_core_create_function(entity)

    # Then: tenant_id in INSERT
    assert "tenant_id," in sql
    # Then: Value from JWT context
    assert "auth_tenant_id" in sql


def test_core_function_uses_trinity_naming():
    """Core function uses Trinity pattern variable names"""
    # Given: Entity
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={"email": FieldDefinition(name="email", type_name="text", nullable=False)},
    )

    # When: Generate core create function
    generator = CoreLogicGenerator()
    sql = generator.generate_core_create_function(entity)

    # Then: Uses Trinity pattern variable names
    assert "v_contact_id UUID := gen_random_uuid()" in sql
    assert "v_contact_pk INTEGER" in sql
    assert "auth_tenant_id UUID" in sql
    assert "auth_user_id UUID" in sql


def test_detect_action_pattern():
    """Test action pattern detection"""
    generator = CoreLogicGenerator()

    # Test CRUD patterns
    assert generator.detect_action_pattern("create_contact") == "create"
    assert generator.detect_action_pattern("update_user") == "update"
    assert generator.detect_action_pattern("delete_task") == "delete"

    # Test custom patterns
    assert generator.detect_action_pattern("qualify_lead") == "custom"
    assert generator.detect_action_pattern("send_notification") == "custom"
    assert generator.detect_action_pattern("process_payment") == "custom"


def test_generate_custom_action_basic():
    """Generate custom action with basic structure"""
    # Given: Entity with custom action
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={"email": FieldDefinition(name="email", type_name="text", nullable=False)},
    )

    # Mock action (simplified for testing)
    class MockAction:
        def __init__(self):
            self.name = "qualify_lead"
            self.description = "Qualify a lead contact"
            self.steps = []  # Empty for now

    action = MockAction()

    # When: Generate custom action
    generator = CoreLogicGenerator()
    sql = generator.generate_core_custom_action(entity, action)

    # Then: Custom action pattern
    assert "CREATE OR REPLACE FUNCTION crm.qualify_lead(" in sql
    assert "input_data app.type_qualify_lead_input" in sql
    assert "v_contact_id UUID := gen_random_uuid()" in sql
    assert "v_contact_pk INTEGER" in sql
    assert "RETURN app.log_and_return_mutation" in sql
