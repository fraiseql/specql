"""Tests for callback function generation."""

import pytest
from src.generators.actions.callback_generator import CallbackGenerator
from src.core.ast_models import ActionStep
from src.generators.actions.action_context import ActionContext


def test_generate_success_callback():
    """Generate on_success callback function"""
    step = ActionStep(
        type="call_service",
        service="stripe",
        operation="create_charge",
        on_success=[
            ActionStep(
                type="update",
                entity="Order",
                fields={"payment_status": "paid"},
                where_clause="pk_order = $job.entity_pk",
            )
        ],
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

    generator = CallbackGenerator(step, context)
    sql = generator.generate_success_callback()

    assert "CREATE FUNCTION" in sql
    assert "_job_run_id UUID" in sql
    assert "_output_data JSONB" in sql
    assert "UPDATE" in sql
