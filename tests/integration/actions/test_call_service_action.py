"""Integration tests for call_service actions."""

import pytest
from src.generators.actions.action_orchestrator import ActionOrchestrator


def test_action_with_call_service_compiles():
    """Full action with call_service compiles"""
    yaml_content = """
    entity: Order
    actions:
      - name: place_order
        steps:
          - insert: Order
            as: order
          - call_service:
              service: stripe
              operation: create_charge
              input:
                amount: $order.total
    """

    orchestrator = ActionOrchestrator.from_yaml(yaml_content)
    sql = orchestrator.generate()

    # Should include job insertion
    assert "INSERT INTO jobs.tb_job_run" in sql

    # Should return job_id in response
    assert "payment_job_id" in sql or "job_id" in sql
