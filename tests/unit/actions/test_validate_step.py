"""
Test validate step compilation
"""

from core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from generators.actions.step_compilers.validate_compiler import ValidateStepCompiler


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


def test_compile_validate_step_simple():
    """Compile validate step to PL/pgSQL IF check"""
    step = ActionStep(type="validate", expression="status = 'lead'", error="not_a_lead")
    entity = create_test_entity()
    context = {}  # Empty context for now

    compiler = ValidateStepCompiler()
    sql = compiler.compile(step, entity, context)

    # Should generate variable fetch + validation
    assert "SELECT status INTO v_status" in sql
    assert "FROM crm.tb_contact" in sql
    assert "WHERE pk_contact = v_pk" in sql
    assert "IF NOT (v_status = 'lead') THEN" in sql
    assert "v_result.status := 'error'" in sql
    assert "v_result.message := 'not_a_lead'" in sql
    assert "RETURN v_result" in sql
