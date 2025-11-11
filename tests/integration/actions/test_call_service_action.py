"""Integration tests for call_service actions."""

import pytest
from src.generators.actions.action_orchestrator import ActionOrchestrator
from src.registry.service_registry import ServiceRegistry, Service, ServiceOperation
from src.runners.execution_types import ExecutionType


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

    # Mock service registry
    service = Service(
        name="stripe",
        type="payment",
        category="financial",
        operations=[ServiceOperation(name="create_charge", input_schema={}, output_schema={})],
        execution_type=ExecutionType.HTTP,
        runner_config={},
        security_policy={},
    )
    service_registry = ServiceRegistry(services=[service])

    orchestrator = ActionOrchestrator.from_yaml(yaml_content, service_registry=service_registry)
    sql = orchestrator.generate()

    # Should include job insertion
    assert "INSERT INTO jobs.tb_job_run" in sql

    # Should return job_id in response
    assert "payment_job_id" in sql or "job_id" in sql


def test_action_with_call_service_retry_config():
    """Full action with call_service retry configuration compiles"""
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
              max_retries: 5
              timeout: 30
    """

    # Mock service registry
    service = Service(
        name="stripe",
        type="payment",
        category="financial",
        operations=[ServiceOperation(name="create_charge", input_schema={}, output_schema={})],
        execution_type=ExecutionType.HTTP,
        runner_config={},
        security_policy={},
    )
    service_registry = ServiceRegistry(services=[service])

    orchestrator = ActionOrchestrator.from_yaml(yaml_content, service_registry=service_registry)
    sql = orchestrator.generate()

    # Should include job insertion
    assert "INSERT INTO jobs.tb_job_run" in sql

    # Should include retry configuration
    assert "max_attempts" in sql
    assert "6" in sql  # max_retries + 1 (initial attempt)

    # Should include timeout configuration
    assert "timeout_seconds" in sql
    assert "30" in sql  # timeout value

    # Should return job_id in response
    assert "job_id" in sql
