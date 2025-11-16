"""Tests for array_build action"""

from src.core.specql_parser import SpecQLParser


def test_array_build_simple():
    """Test building a simple array"""
    yaml_content = """
    entity: Product
    actions:
      - name: get_product_tags
        steps:
          - array_build:
              name: tags
              elements:
                - "electronics"
                - "gadget"
                - "wireless"
          - return: tags
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "array_build"
    assert action.steps[0].array_variable_name == "tags"
    assert action.steps[0].array_elements == ["electronics", "gadget", "wireless"]


def test_array_build_with_variables():
    """Test building array with variable references"""
    yaml_content = """
    entity: Order
    actions:
      - name: create_order_items
        steps:
          - array_build:
              name: item_ids
              elements:
                - $item1_id
                - $item2_id
                - $item3_id
          - return: item_ids
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "array_build"
    assert action.steps[0].array_variable_name == "item_ids"
    assert action.steps[0].array_elements == ["$item1_id", "$item2_id", "$item3_id"]


def test_array_build_mixed_types():
    """Test building array with mixed data types"""
    yaml_content = """
    entity: Report
    actions:
      - name: generate_summary
        steps:
          - array_build:
              name: summary_data
              elements:
                - "Total Sales"
                - 125000.50
                - true
                - $report_date
          - return: summary_data
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "array_build"
    assert action.steps[0].array_variable_name == "summary_data"
    expected = ["Total Sales", 125000.50, True, "$report_date"]
    assert action.steps[0].array_elements == expected
