"""
Unit tests for duplicate check functionality in CoreLogicGenerator
"""

import pytest

from src.core.ast_models import Action, ActionStep, Entity, FieldDefinition


def test_compile_duplicate_check_step(core_logic_generator):
    """Test compilation of duplicate check step"""
    # Mock entity with fields
    entity = Entity(
        name="Contract",
        schema="tenant",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
            "customer_org": FieldDefinition(name="customer_org", type_name="uuid"),
            "provider_org": FieldDefinition(name="provider_org", type_name="uuid"),
            "customer_contract_id": FieldDefinition(name="customer_contract_id", type_name="text"),
        },
    )

    step = ActionStep(
        type="duplicate_check",
        fields={
            "fields": ["customer_org", "provider_org", "customer_contract_id"],
            "error_message": "Contract already exists for this customer/provider/contract_id",
            "return_conflict_object": True,
        },
    )

    action = Action(name="create_contract", steps=[step])

    compiled = core_logic_generator._compile_action_steps(action, entity)

    # Should contain duplicate check SQL
    sql = "\n".join(compiled)
    assert "SELECT id INTO v_existing_id" in sql
    assert "FROM tenant.tb_contract" in sql
    assert "customer_org = input_data.customer_org" in sql
    assert "provider_org = input_data.provider_org" in sql
    assert "customer_contract_id = input_data.customer_contract_id" in sql
    assert "IF v_existing_id IS NOT NULL THEN" in sql
    assert "SELECT data INTO v_existing_object" in sql
    assert "FROM tenant.v_contract_projection" in sql
    assert "RETURN app.log_and_return_mutation" in sql
    assert "noop:already_exists" in sql
    assert "Contract already exists for this customer/provider/contract_id" in sql


def test_compile_duplicate_check_without_conflict_object(core_logic_generator):
    """Test compilation of duplicate check step without conflict object"""
    # Mock entity with fields
    entity = Entity(
        name="Contract",
        schema="tenant",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
            "customer_org": FieldDefinition(name="customer_org", type_name="uuid"),
            "provider_org": FieldDefinition(name="provider_org", type_name="uuid"),
            "customer_contract_id": FieldDefinition(name="customer_contract_id", type_name="text"),
        },
    )

    step = ActionStep(
        type="duplicate_check",
        fields={
            "fields": ["customer_contract_id"],
            "error_message": "Contract ID already exists",
            "return_conflict_object": False,
        },
    )

    action = Action(name="create_contract", steps=[step])

    compiled = core_logic_generator._compile_action_steps(action, entity)

    # Should contain duplicate check SQL without conflict object loading
    sql = "\n".join(compiled)
    assert "SELECT id INTO v_existing_id" in sql
    assert "IF v_existing_id IS NOT NULL THEN" in sql
    assert "SELECT data INTO v_existing_object" not in sql  # Should not load conflict object
    assert "NULL,\n            NULL," in sql  # Should pass NULL for before/after objects
    assert "Contract ID already exists" in sql
