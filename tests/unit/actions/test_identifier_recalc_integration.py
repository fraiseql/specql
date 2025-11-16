"""
Unit tests for identifier recalculation integration in CoreLogicGenerator
"""

from src.core.ast_models import Action, ActionStep, Entity, FieldDefinition


def test_generate_identifier_recalc_call(core_logic_generator):
    """Test generation of identifier recalculation call"""
    entity = Entity(
        name="Contract",
        schema="tenant",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
        },
    )

    call = core_logic_generator._generate_identifier_recalc_call(entity)

    expected = """
    -- Recalculate identifier
    PERFORM tenant.recalcid_contract(
        v_contract_id,
        auth_tenant_id,
        auth_user_id
    );"""

    assert call == expected


def test_compile_update_with_identifier_recalc(core_logic_generator):
    """Test compilation of update step with identifier recalculation"""
    entity = Entity(
        name="Contract",
        schema="tenant",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
            "customer_contract_id": FieldDefinition(
                name="customer_contract_id", type_name="text"
            ),
            "updated_at": FieldDefinition(name="updated_at", type_name="timestamp"),
            "updated_by": FieldDefinition(name="updated_by", type_name="uuid"),
        },
    )

    step = ActionStep(
        type="update",
        fields={"customer_contract_id": "NEW-123", "recalculate_identifier": True},
    )

    action = Action(name="update_contract", steps=[step])

    compiled = core_logic_generator._compile_action_steps(action, entity)

    # Should contain update SQL followed by identifier recalculation
    sql = "\n".join(compiled)
    assert "UPDATE tenant.tb_contract" in sql
    assert "customer_contract_id = 'NEW-123'" in sql
    assert "updated_at = now()" in sql
    assert "updated_by = auth_user_id" in sql
    assert "PERFORM tenant.recalcid_contract(" in sql
    assert "v_contract_id," in sql
    assert "auth_tenant_id," in sql
    assert "auth_user_id" in sql
