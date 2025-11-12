"""Tests for cte action step"""

import pytest
from src.core.specql_parser import ParseError, SpecQLParser


def test_simple_cte():
    """Test simple CTE for query composition"""
    yaml_content = """
    entity: Report
    actions:
      - name: monthly_sales_report
        steps:
          - cte:
              name: monthly_totals
              query: |
                SELECT
                  DATE_TRUNC('month', order_date) AS month,
                  SUM(total_amount) AS monthly_total
                FROM tb_order
                WHERE EXTRACT(YEAR FROM order_date) = $year
                GROUP BY DATE_TRUNC('month', order_date)
          - query: result = SELECT * FROM monthly_totals ORDER BY month
          - return: result
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "cte"
    assert action.steps[0].cte_name == "monthly_totals"
    assert action.steps[0].cte_query is not None and "SELECT" in action.steps[0].cte_query


def test_multiple_ctes():
    """Test multiple CTEs with dependencies"""
    yaml_content = """
    entity: Analytics
    actions:
      - name: customer_lifetime_value
        steps:
          - cte:
              name: customer_orders
              query: |
                SELECT customer_id, COUNT(*) as order_count, SUM(total_amount) as total_spent
                FROM tb_order
                GROUP BY customer_id
          - cte:
              name: customer_segments
              query: |
                SELECT
                  customer_id,
                  CASE
                    WHEN total_spent > 10000 THEN 'vip'
                    WHEN total_spent > 1000 THEN 'regular'
                    ELSE 'occasional'
                  END as segment
                FROM customer_orders
          - query: result = SELECT * FROM customer_segments WHERE segment = $segment
          - return: result
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "cte"
    assert action.steps[1].type == "cte"
    assert action.steps[0].cte_name == "customer_orders"
    assert action.steps[1].cte_name == "customer_segments"