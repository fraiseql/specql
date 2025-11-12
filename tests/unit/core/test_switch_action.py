"""Tests for switch action parsing and AST generation"""

import pytest
from src.core.specql_parser import SpecQLParser


def test_switch_basic():
    """Test basic switch/case statement"""
    yaml_content = """
    entity: Order
    actions:
      - name: process_order_by_type
        parameters:
          - name: order_type
            type: text
        steps:
          - switch:
              expression: $order_type
              cases:
                - when: 'standard'
                  then:
                    - update: Order SET processing_time = 24

                - when: 'express'
                  then:
                    - update: Order SET processing_time = 4

                - when: 'overnight'
                  then:
                    - update: Order SET processing_time = 1

              default:
                - reject: "Invalid order type"
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "switch"
    assert action.steps[0].switch_expression == "$order_type"
    assert len(action.steps[0].cases) == 3
    assert action.steps[0].default_steps is not None


def test_switch_with_multiple_conditions():
    """Test switch with complex case conditions"""
    yaml_content = """
    entity: Customer
    actions:
      - name: categorize_customer
        steps:
          - declare:
              name: category
              type: text

          - switch:
              expression: (total_purchases, years_active)
              cases:
                - when: total_purchases > 50000 AND years_active > 5
                  then:
                    - query: category = 'platinum'

                - when: total_purchases > 10000
                  then:
                    - query: category = 'gold'

                - when: total_purchases > 1000
                  then:
                    - query: category = 'silver'
              default:
                - query: category = 'bronze'

          - return: category
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    switch_step = action.steps[1]
    assert switch_step.type == "switch"
    assert len(switch_step.cases) == 3