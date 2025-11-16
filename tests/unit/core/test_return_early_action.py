"""Tests for return_early action parsing and AST generation"""

from src.core.specql_parser import SpecQLParser


def test_return_early_simple():
    """Test early return from function"""
    yaml_content = """
    entity: Order
    actions:
      - name: validate_and_process
        steps:
          - if: status != 'pending'
            then:
              - return_early:
                  success: false
                  message: "Order already processed"

          - if: total_amount <= 0
            then:
              - return_early:
                  success: false
                  message: "Invalid order amount"

          # Continue with processing
          - update: Order SET status = 'processing'
          - return:
              success: true
              message: "Order processing started"
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    early_return_steps = [
        s for s in action.steps[0].then_steps if s.type == "return_early"
    ]
    assert len(early_return_steps) == 1


def test_return_early_with_value():
    """Test early return with computed value"""
    yaml_content = """
    entity: Calculator
    actions:
      - name: divide_numbers
        parameters:
          - name: numerator
            type: numeric
          - name: denominator
            type: numeric
        returns: numeric
        steps:
          - if: denominator = 0
            then:
              - return_early: NULL

          - return: numerator / denominator
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].then_steps[0].type == "return_early"
    assert action.steps[0].then_steps[0].return_value is None
