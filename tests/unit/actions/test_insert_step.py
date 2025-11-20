"""
Test insert step compilation
"""

from core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from generators.actions.step_compilers.insert_compiler import InsertStepCompiler


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


def test_compile_insert_step_simple():
    """Compile insert step to SQL INSERT"""
    step = ActionStep(
        type="insert",
        entity="Notification",
        fields={"contact_id": "$pk", "message": "Contact qualified", "notification_type": "email"},
    )
    entity = create_test_entity()
    context = {}

    compiler = InsertStepCompiler()
    sql = compiler.compile(step, entity, context)

    assert "INSERT INTO crm.tb_notification" in sql
    assert "fk_contact, message, notification_type, created_at, created_by" in sql
    assert "v_pk, 'Contact qualified', 'email', now(), p_caller_id" in sql
    assert "RETURNING pk_notification INTO v_notification_pk" in sql
