"""Tests for while loop action"""

from src.core.specql_parser import SpecQLParser


def test_while_basic():
    """Test basic while loop with counter"""
    yaml_content = """
    entity: Counter
    actions:
      - name: countdown
        steps:
          - declare:
              name: counter
              type: integer
              default: 10
          - while: counter > 0
            loop:
              - query: counter = counter - 1
              - if: counter = 5
                then:
                  - return_early: "Halfway done"
          - return: "Done"
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[1].type == "while"
    assert action.steps[1].while_condition == "counter > 0"
    assert len(action.steps[1].loop_body) == 2


def test_while_with_complex_condition():
    """Test while with complex boolean condition"""
    yaml_content = """
    entity: Processor
    actions:
      - name: process_until_complete
        steps:
          - declare:
              name: status
              type: text
              default: 'pending'
          - declare:
              name: attempts
              type: integer
              default: 0
          - while: status != 'complete' AND attempts < 5
            loop:
              - call_function:
                  function: process_batch
                  returns: batch_result
              - query: status = batch_result.status
              - query: attempts = attempts + 1
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[2].type == "while"
    assert action.steps[2].while_condition == "status != 'complete' AND attempts < 5"
    assert len(action.steps[2].loop_body) == 3
