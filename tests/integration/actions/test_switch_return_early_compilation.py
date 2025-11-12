"""Integration tests for switch and return_early action compilation"""

import pytest
from src.core.specql_parser import SpecQLParser
from src.generators.core_logic_generator import CoreLogicGenerator
from src.generators.schema.schema_registry import SchemaRegistry


def test_switch_compilation():
    """Test that switch steps compile to valid PL/pgSQL"""
    yaml_content = """
    entity: Order
    schema: sales
    fields:
      order_id: uuid
      status: text
      processing_time: integer
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
                    - query: processing_time = 24
                - when: 'express'
                  then:
                    - query: processing_time = 4
              default:
                - reject: "Invalid order type"
    """

    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    entity = entity_def
    action = entity.actions[0]

    # Create schema registry
    schema_registry = SchemaRegistry()

    # Generate core logic
    generator = CoreLogicGenerator(schema_registry)
    compiled_steps = generator._compile_action_steps(action, entity)

    # Should contain switch logic
    compiled_sql = "\n".join(compiled_steps)
    assert "CASE" in compiled_sql
    assert "WHEN" in compiled_sql
    assert "END CASE" in compiled_sql


def test_return_early_compilation():
    """Test that return_early steps compile to valid PL/pgSQL"""
    yaml_content = """
    entity: Calculator
    schema: math
    fields:
      calculator_id: uuid
    actions:
      - name: divide_numbers
        parameters:
          - name: numerator
            type: numeric
          - name: denominator
            type: numeric
        returns: numeric
        steps:
          - if: $denominator = 0
            then:
              - return_early: NULL
          - return: $numerator / $denominator
    """

    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    entity = entity_def
    action = entity.actions[0]

    print(f"DEBUG: Parsed action: {action.name}")
    print(f"DEBUG: Action steps: {len(action.steps)}")
    for i, step in enumerate(action.steps):
        print(f"DEBUG: Step {i}: {step.type}")

    # Create schema registry
    schema_registry = SchemaRegistry()

    # Generate core logic
    generator = CoreLogicGenerator(schema_registry)
    compiled_steps = generator._compile_action_steps(action, entity)

    print(f"DEBUG: Compiled steps: {compiled_steps}")

    # Should contain return logic
    compiled_sql = "\n".join(compiled_steps)
    assert "RETURN NULL;" in compiled_sql or "RETURN" in compiled_sql