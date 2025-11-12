"""Tests for declare action step"""

import pytest
from src.core.specql_parser import ParseError, SpecQLParser


def test_declare_variable_integer():
    """Test declaring an integer variable"""
    yaml_content = """
    entity: Invoice
    actions:
      - name: calculate_total
        steps:
          - declare:
              name: subtotal
              type: numeric
              default: 0
          - query: subtotal = SUM(amount) FROM tb_line_item WHERE invoice_id = $invoice_id
          - return: subtotal
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "declare"
    assert action.steps[0].variable_name == "subtotal"
    assert action.steps[0].variable_type == "numeric"
    assert action.steps[0].default_value == 0


def test_declare_multiple_variables():
    """Test declaring multiple variables"""
    yaml_content = """
    entity: Order
    actions:
      - name: process_order
        steps:
          - declare:
              - name: tax_rate
                type: numeric
                default: 0.0825
              - name: discount_amount
                type: numeric
                default: 0
              - name: final_total
                type: numeric
          - query: final_total = (subtotal * (1 + tax_rate)) - discount_amount
          - return: final_total
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert len(action.steps[0].declarations) == 3
    assert action.steps[0].declarations[0].name == "tax_rate"