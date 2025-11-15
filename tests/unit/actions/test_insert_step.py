"""
Test insert step compilation
"""

from src.core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from src.generators.actions.step_compilers.insert_compiler import InsertStepCompiler


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
        fields={
            "contact_id": "$pk",
            "message": "Contact qualified",
            "notification_type": "email",
        },
    )
    entity = create_test_entity()
    context = {}

    compiler = InsertStepCompiler()
    sql = compiler.compile(step, entity, context)

    assert "INSERT INTO crm.tb_notification" in sql
    assert "fk_contact, message, notification_type, created_at, created_by" in sql
    assert "v_pk, 'Contact qualified', 'email', now(), p_caller_id" in sql
    assert "RETURNING id INTO v_notification_id" in sql


def test_insert_step_with_different_schema():
    """Test insert step with entity from different schema"""
    step = ActionStep(
        type="insert",
        entity="LogEntry",
        fields={"level": "info", "message": "Test message"},
    )
    # Entity with different schema
    entity = EntityDefinition(
        name="Contact",
        schema="audit",  # Different schema
        fields={},
    )
    context = {}

    compiler = InsertStepCompiler()
    sql = compiler.compile(step, entity, context)

    # Should use entity's schema but step's entity name
    assert "INSERT INTO audit.tb_logentry" in sql


def test_insert_step_captures_entity_id():
    """INSERT step should capture RETURNING id INTO v_{entity}_id for cascade tracking"""
    step = ActionStep(
        type="insert",
        entity="Post",
        fields={"title": "Test Post", "content": "Hello World"},
    )
    entity = create_test_entity()
    context = {}

    compiler = InsertStepCompiler()
    sql = compiler.compile(step, entity, context)

    # Should capture ID for cascade tracking
    assert "RETURNING id INTO v_post_id" in sql or "v_post_id UUID" in sql
