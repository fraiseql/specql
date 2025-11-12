"""Tests for return_table action"""

import pytest
from src.core.specql_parser import SpecQLParser


def test_return_table_basic():
    """Test return_table action"""
    yaml_content = """
    entity: Report
    actions:
      - name: get_sales_report
        steps:
          - return_table:
              query: SELECT * FROM sales WHERE period = $period
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "return_table"
    assert "SELECT" in action.steps[0].return_table_query