"""Tests for cursor action"""

from src.core.specql_parser import SpecQLParser


def test_cursor_basic():
    """Test cursor action"""
    yaml_content = """
    entity: Data
    actions:
      - name: process_large_dataset
        steps:
          - cursor:
              name: data_cursor
              query: SELECT * FROM large_table WHERE status = 'active'
              operations:
                - fetch_next
                - process_record
                - close
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "cursor"
    assert action.steps[0].cursor_name == "data_cursor"
    assert "SELECT" in action.steps[0].cursor_query