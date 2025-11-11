"""Tests for call_service step compiler."""

import pytest
from src.generators.actions.step_compilers.call_service_step_compiler import CallServiceStepCompiler
from src.core.ast_models import ActionStep
from src.generators.actions.action_context import ActionContext


def test_compile_call_service_basic():
    """Compile call_service to INSERT INTO jobs.tb_job_run"""
    step = ActionStep(
        type="call_service",
        service="sendgrid",
        operation="send_email",
        input={"to": "$order.customer_email", "subject": "Receipt"},
    )

    # Mock context
    context = ActionContext(
        function_name="crm.send_receipt",
        entity_schema="crm",
        entity_name="Order",
        entity=None,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )

    compiler = CallServiceStepCompiler(step, context)
    sql = compiler.compile()

    assert "INSERT INTO jobs.tb_job_run" in sql
    assert "'sendgrid'" in sql
    assert "'send_email'" in sql
    assert "jsonb_build_object" in sql
    assert "_job_id_sendgridsendemail" in sql


def test_compile_service_input_expressions():
    """Compile input expressions to JSON"""
    step = ActionStep(
        type="call_service",
        service="stripe",
        operation="create_charge",
        input={"amount": "$order.total", "customer": "$order.customer_id"},
    )

    # Mock context
    context = ActionContext(
        function_name="crm.place_order",
        entity_schema="crm",
        entity_name="Order",
        entity=None,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )

    compiler = CallServiceStepCompiler(step, context)
    sql = compiler.compile()

    assert "_order.total" in sql  # Trinity resolution
    assert "_order.customer_id" in sql
    assert "_job_id_stripecreatecharge" in sql
