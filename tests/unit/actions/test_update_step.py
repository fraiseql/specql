"""
Test update step compilation
"""

import pytest
from src.core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from src.generators.actions.step_compilers.update_compiler import UpdateStepCompiler


def create_test_entity():
    """Create a test EntityDefinition"""
    return EntityDefinition(
        name="Contact",
        schema="crm",
        fields={
            "status": FieldDefinition(name="status", type_name="text"),
            "email": FieldDefinition(name="email", type_name="text"),
        },
    )


def test_compile_update_step_simple():
    """Compile update step to SQL UPDATE"""
    step = ActionStep(type="update", fields={"raw_set": "status = 'qualified'"})
    entity = create_test_entity()
    context = {}

    compiler = UpdateStepCompiler()
    sql = compiler.compile(step, entity, context)

    assert "UPDATE crm.tb_contact" in sql
    assert "SET status = 'qualified'" in sql
    assert "updated_at = now()" in sql  # Auto-audit
    assert "updated_by = p_caller_id" in sql  # Auto-audit
    assert "WHERE pk_contact = v_pk" in sql
