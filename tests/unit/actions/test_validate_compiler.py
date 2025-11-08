from src.core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from src.generators.actions.step_compilers.validate_compiler import ValidateStepCompiler


def test_compile_simple_validate():
    """Test compiling simple validation step"""
    entity = EntityDefinition(
        name="Contact",
        schema="crm",
        fields={"status": FieldDefinition(name="status", type_name="text")},
    )

    step = ActionStep(type="validate", expression="status = 'lead'", error="not_a_lead")

    compiler = ValidateStepCompiler()
    sql = compiler.compile(step, entity, {})

    assert "SELECT status INTO v_status" in sql
    assert "FROM crm.tb_contact" in sql
    assert "WHERE pk_contact = v_pk" in sql
    assert "IF NOT (v_status = 'lead')" in sql
    assert "v_result.message := 'not_a_lead'" in sql


def test_compile_validate_multiple_fields():
    """Test validation with multiple fields"""
    entity = EntityDefinition(
        name="Contact",
        schema="crm",
        fields={
            "status": FieldDefinition(name="status", type_name="text"),
            "email": FieldDefinition(name="email", type_name="email"),
        },
    )

    step = ActionStep(
        type="validate", expression="status = 'lead' AND email IS NOT NULL", error="invalid_lead"
    )

    compiler = ValidateStepCompiler()
    sql = compiler.compile(step, entity, {})

    assert "SELECT status, email INTO v_status, v_email" in sql
    assert "v_status = 'lead' AND v_email IS NOT NULL" in sql
