"""
Unit tests for hard delete functionality in CoreLogicGenerator
"""

from src.core.ast_models import Action, ActionStep, Entity, FieldDefinition


def test_compile_soft_delete_step(core_logic_generator):
    """Test compilation of soft delete step"""
    entity = Entity(
        name="Contract",
        schema="tenant",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
        },
    )

    step = ActionStep(type="delete", fields={"supports_hard_delete": False})

    action = Action(name="delete_contract", steps=[step])

    compiled = core_logic_generator._compile_action_steps(action, entity)

    # Should contain soft delete SQL
    sql = "\n".join(compiled)
    assert "UPDATE tenant.tb_contract" in sql
    assert "deleted_at = NOW()" in sql
    assert "deleted_by = auth_user_id" in sql
    assert "soft_deleted" in sql


def test_compile_hard_delete_step(core_logic_generator):
    """Test compilation of hard delete step"""
    entity = Entity(
        name="Contract",
        schema="tenant",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
        },
    )

    step = ActionStep(
        type="delete", fields={"supports_hard_delete": True, "check_dependencies": []}
    )

    action = Action(name="delete_contract", steps=[step])

    compiled = core_logic_generator._compile_action_steps(action, entity)

    # Should contain hard delete SQL
    sql = "\n".join(compiled)
    assert "DELETE FROM tenant.tb_contract" in sql
    assert "WHERE id = v_contract_id" in sql
    assert "'DELETE', 'deleted'" in sql


def test_compile_hard_delete_with_dependencies(core_logic_generator):
    """Test compilation of hard delete with dependency checking"""
    entity = Entity(
        name="Machine",
        schema="tenant",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
        },
    )

    step = ActionStep(
        type="delete",
        fields={
            "supports_hard_delete": True,
            "check_dependencies": [
                {
                    "entity": "Allocation",
                    "field": "machine_id",
                    "block_hard_delete": True,
                }
            ],
        },
    )

    action = Action(name="delete_machine", steps=[step])

    compiled = core_logic_generator._compile_action_steps(action, entity)

    # Should contain dependency checking and hard delete
    sql = "\n".join(compiled)
    assert "v_has_dependencies BOOLEAN := FALSE" in sql
    assert "Check Allocation dependency" in sql
    assert "IF v_hard_delete AND v_has_dependencies THEN" in sql
    assert "noop:cannot_delete_with_dependencies" in sql
    assert "DELETE FROM tenant.tb_machine" in sql
