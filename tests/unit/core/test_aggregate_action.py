"""Tests for aggregate action type"""


from src.core.specql_parser import SpecQLParser


def test_aggregate_in_query():
    """Test aggregate functions in queries"""
    yaml_content = """
    entity: Report
    actions:
      - name: sales_summary
        steps:
          - aggregate:
              operation: sum
              field: amount
              from: tb_order
              where: status = 'completed'
              as: total_sales
          - aggregate:
              operation: count
              field: id
              from: tb_order
              where: status = 'completed'
              as: order_count
          - return:
              total_sales: $total_sales
              order_count: $order_count
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "aggregate"
    assert action.steps[0].aggregate_operation == "sum"
    assert action.steps[0].aggregate_field == "amount"

def test_aggregate_with_group_by():
    """Test aggregate with grouping"""
    yaml_content = """
    entity: Analytics
    actions:
      - name: sales_by_region
        steps:
          - aggregate:
              operation: sum
              field: amount
              from: tb_order
              group_by: region
              as: regional_totals
          - return: regional_totals
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].aggregate_group_by == "region"