"""Integration test for Week 2 features: aggregate + subquery + call_function"""

from src.core.specql_parser import SpecQLParser


def test_week2_features_parse_correctly():
    """
    Test that aggregate + subquery + call_function parse correctly
    """
    yaml_content = """
    entity: Order
    schema: ecommerce
    actions:
      - name: calculate_order_with_analytics
        parameters:
          - name: order_id
            type: uuid
        returns: json
        steps:
          - declare:
              name: subtotal
              type: numeric
              default: 0

          # Aggregate: Calculate subtotal
          - aggregate:
              operation: sum
              field: amount
              from: tb_order_item
              where: order_id = $order_id
              as: subtotal

          # Subquery: Get average order value
          - subquery:
              query: SELECT AVG(total_amount) FROM tb_order
              as: avg_order_value

          # Call function: Calculate tax
          - call_function:
              function: ecommerce.calculate_tax
              arguments:
                amount: $subtotal
                rate: 0.0825
              returns: tax_amount

          # Return results
          - return:
              subtotal: $subtotal
              tax_amount: $tax_amount
    """

    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    assert len(entity_def.actions) == 1

    action = entity_def.actions[0]
    assert (
        len(action.steps) == 5
    )  # declare + aggregate + subquery + call_function + return

    # Check step types
    assert action.steps[0].type == "declare"
    assert action.steps[1].type == "aggregate"
    assert action.steps[2].type == "subquery"
    assert action.steps[3].type == "call_function"
    assert action.steps[4].type == "return"

    # Check aggregate step
    assert action.steps[1].aggregate_operation == "sum"
    assert action.steps[1].aggregate_field == "amount"
    assert action.steps[1].aggregate_from == "tb_order_item"
    assert action.steps[1].aggregate_as == "subtotal"

    # Check subquery step
    assert action.steps[2].subquery_query == "SELECT AVG(total_amount) FROM tb_order"
    assert action.steps[2].subquery_result_variable == "avg_order_value"

    # Check call_function step
    assert action.steps[3].call_function_name == "ecommerce.calculate_tax"
    assert action.steps[3].call_function_arguments == {
        "amount": "$subtotal",
        "rate": 0.0825,
    }
    assert action.steps[3].call_function_return_variable == "tax_amount"


def test_week2_grouped_aggregate_parsing():
    """
    Test Week 2 features with grouped aggregates
    """
    yaml_content = """
    entity: Analytics
    schema: reporting
    actions:
      - name: category_performance_analysis
        returns: json
        steps:
          - aggregate:
              operation: sum
              field: amount
              from: tb_sales
              group_by: category
              as: category_totals

          - aggregate:
              operation: sum
              field: amount
              from: tb_sales
              as: total_sales

          - subquery:
              query: SELECT AVG(amount) FROM tb_sales WHERE category = 'electronics'
              as: category_avg

          - call_function:
              function: reporting.calculate_growth_rate
              arguments:
                current_total: $total_sales
                previous_period: 30
              returns: growth_rate

          - return:
              category_totals: $category_totals
              total_sales: $total_sales
              category_average: $category_avg
              growth_rate: $growth_rate
    """

    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    assert len(entity_def.actions) == 1

    action = entity_def.actions[0]
    assert len(action.steps) == 5

    # Check grouped aggregate
    assert action.steps[0].type == "aggregate"
    assert action.steps[0].aggregate_group_by == "category"

    # Check regular aggregate
    assert action.steps[1].type == "aggregate"
    assert action.steps[1].aggregate_group_by is None

    # Check subquery
    assert action.steps[2].type == "subquery"

    # Check call_function
    assert action.steps[3].type == "call_function"
    assert action.steps[3].call_function_arguments == {
        "current_total": "$total_sales",
        "previous_period": 30,
    }
