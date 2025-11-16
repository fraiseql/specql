"""Tests for subquery action type"""

from src.core.specql_parser import SpecQLParser


def test_subquery_in_where():
    """Test subquery in WHERE clause"""
    yaml_content = """
    entity: Customer
    actions:
      - name: find_high_value_customers
        steps:
          - query: |
              SELECT * FROM tb_customer
              WHERE id IN (
                subquery:
                  SELECT customer_id FROM tb_order
                  WHERE total_amount > 1000
                  GROUP BY customer_id
                  HAVING COUNT(*) > 5
              )
          - return: result
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    # Check that the query step was parsed (there are 2 steps total: query + return)
    assert len(action.steps) == 2
    assert action.steps[0].type == "query"


def test_subquery_as_value():
    """Test subquery returning single value"""
    yaml_content = """
    entity: Order
    actions:
      - name: calculate_order_with_avg
        steps:
          - declare:
              name: avg_order_value
              type: numeric

          - subquery:
              query: SELECT AVG(total_amount) FROM tb_order
              as: avg_order_value

          - if: total_amount > avg_order_value
            then:
              - update: Order SET status = 'high_value'
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[1].type == "subquery"
    assert action.steps[1].subquery_result_variable == "avg_order_value"
