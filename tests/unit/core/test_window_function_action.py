"""Tests for window_function action"""

from src.core.specql_parser import SpecQLParser


def test_window_function_basic():
    """Test basic window function"""
    yaml_content = """
    entity: Sales
    actions:
      - name: rank_sales
        steps:
          - window_function:
              name: row_number
              partition_by: ["region"]
              order_by: ["total DESC"]
              as: sales_rank
          - return: sales_rank
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "window_function"
    assert action.steps[0].window_function_name == "row_number"
    assert action.steps[0].window_partition_by == ["region"]
    assert action.steps[0].window_order_by == ["total DESC"]
    assert action.steps[0].window_as == "sales_rank"
