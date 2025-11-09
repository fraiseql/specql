"""
Test notify step compilation
"""

import pytest

from src.core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from src.generators.actions.step_compilers.notify_compiler import NotifyStepCompiler


def create_test_entity():
    """Create a test EntityDefinition"""
    return EntityDefinition(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="text"),
        },
    )


def test_compile_notify_step_simple():
    """Compile simple notify step to PL/pgSQL PERFORM emit_event"""
    step = ActionStep(
        type="notify",
        arguments={
            "recipient": "owner_email",
            "channel": "email",
            "message": "Contact qualified",
        },
    )
    entity = create_test_entity()
    context = {"operation": "update"}

    compiler = NotifyStepCompiler()
    sql = compiler.compile(step, entity, context)

    # Should contain PERFORM emit_event call
    assert "PERFORM app.emit_event(" in sql
    # Should have tenant_id parameter
    assert "p_tenant_id := auth_tenant_id" in sql
    # Should have event type
    assert "p_event_type := 'notification.email'" in sql
    # Should have payload with jsonb_build_object
    assert "p_payload := jsonb_build_object(" in sql
    # Should contain recipient in payload
    assert "'recipient', owner_email" in sql
    # Should contain channel in payload
    assert "'channel', 'email'" in sql
    # Should contain message in payload
    assert "'message', 'Contact qualified'" in sql
    # Should contain entity info
    assert "'entity', 'contact'" in sql
    assert "'entity_id', v_contact_id" in sql
    # Should contain operation from context
    assert "'operation', 'update'" in sql


def test_compile_notify_step_minimal():
    """Compile notify step with minimal arguments (uses defaults)"""
    step = ActionStep(
        type="notify",
        arguments={},
    )
    entity = create_test_entity()
    context = {}

    compiler = NotifyStepCompiler()
    sql = compiler.compile(step, entity, context)

    # Should use defaults
    assert "'recipient', user" in sql
    assert "'channel', 'email'" in sql
    assert "'message', 'Contact updated'" in sql


def test_compile_notify_step_wrong_type():
    """Test error when wrong step type passed to notify compiler"""
    step = ActionStep(
        type="update",
        fields={"raw_set": "status = 'qualified'"},
    )
    entity = create_test_entity()
    context = {}

    compiler = NotifyStepCompiler()

    with pytest.raises(ValueError, match="Expected notify step, got update"):
        compiler.compile(step, entity, context)
