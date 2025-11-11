"""Tests for call_service step parsing."""

import pytest
from src.core.ast_models import CallServiceStep
from src.core.specql_parser import SpecQLParser


def test_parse_call_service_basic():
    """Parse basic call_service step"""
    yaml_content = """
    entity: Order
    actions:
      - name: send_receipt
        steps:
          - call_service:
              service: sendgrid
              operation: send_email
              input:
                to: $order.customer_email
                subject: "Receipt"
    """
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)
    action = entity.actions[0]
    assert len(action.steps) == 1
    step = action.steps[0]
    assert step.type == "call_service"
    assert step.service == "sendgrid"
    assert step.operation == "send_email"


def test_call_service_with_callbacks():
    """Parse call_service with success/failure callbacks"""
    yaml_content = """
    entity: Order
    actions:
      - name: charge_order
        steps:
          - call_service:
              service: stripe
              operation: create_charge
              on_success:
                - update: Order SET status = 'paid'
              on_failure:
                - update: Order SET status = 'failed'
    """
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)
    step = entity.actions[0].steps[0]
    assert len(step.on_success) == 1
    assert len(step.on_failure) == 1
