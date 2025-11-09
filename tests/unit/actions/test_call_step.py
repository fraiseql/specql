"""
Test call step compilation
"""

import pytest

from src.core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from src.generators.actions.step_compilers.call_compiler import CallStepCompiler


def create_test_entity():
    """Create a test EntityDefinition"""
    return EntityDefinition(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="text"),
        },
    )


def test_compile_call_step_simple():
    """Compile simple call step to PL/pgSQL PERFORM"""
    step = ActionStep(
        type="call",
        function_name="send_notification",
        arguments={
            "email": "owner_email",
            "message": "'Contact qualified'",
        },
    )
    entity = create_test_entity()
    context = {}

    compiler = CallStepCompiler()
    sql = compiler.compile(step, entity, context)

    # Should contain PERFORM call
    assert "PERFORM app.send_notification(" in sql
    # Should have named parameters
    assert "p_email := owner_email" in sql
    assert "p_message := 'Contact qualified'" in sql
    # Should end with closing paren and semicolon
    assert sql.strip().endswith(");")


def test_compile_call_step_no_args():
    """Compile call step with no arguments"""
    step = ActionStep(
        type="call",
        function_name="log_event",
        arguments={},
    )
    entity = create_test_entity()
    context = {}

    compiler = CallStepCompiler()
    sql = compiler.compile(step, entity, context)

    assert "PERFORM app.log_event();" in sql


def test_compile_call_step_wrong_type():
    """Test error when wrong step type passed to call compiler"""
    step = ActionStep(
        type="update",
        fields={"raw_set": "status = 'qualified'"},
    )
    entity = create_test_entity()
    context = {}

    compiler = CallStepCompiler()

    with pytest.raises(ValueError, match="Expected call step, got update"):
        compiler.compile(step, entity, context)


def test_compile_call_step_no_function_name():
    """Test error when call step has no function_name"""
    step = ActionStep(
        type="call",
        arguments={"email": "test@example.com"},
    )
    entity = create_test_entity()
    context = {}

    compiler = CallStepCompiler()

    with pytest.raises(ValueError, match="Call step must have a function_name"):
        compiler.compile(step, entity, context)
