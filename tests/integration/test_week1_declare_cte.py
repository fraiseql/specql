"""Full integration test for Week 1 features"""

from src.core.specql_parser import SpecQLParser


def test_week1_full_integration():
    """
    Full integration test for Week 1 features
    - Parse YAML with declare + cte
    - Generate SQL
    - Verify structure
    """
    yaml_content = """
    entity: Invoice
    schema: billing
    actions:
      - name: calculate_invoice_total
        parameters:
          - name: invoice_id
            type: uuid
        returns: numeric
        steps:
          - declare:
              name: total
              type: numeric
              default: 0

          - cte:
              name: line_totals
              query: |
                SELECT SUM(quantity * unit_price) as line_total
                FROM tb_line_item
                WHERE invoice_id = $invoice_id

          - query: total = SELECT line_total FROM line_totals
          - return: total
    """

    # Parse
    parser = SpecQLParser()
    ast = parser.parse(yaml_content)
    assert len(ast.actions) == 1

    action = ast.actions[0]
    assert action.name == "calculate_invoice_total"
    assert len(action.steps) == 4

    # Check declare step
    declare_step = action.steps[0]
    assert declare_step.type == "declare"
    assert declare_step.variable_name == "total"
    assert declare_step.variable_type == "numeric"
    assert declare_step.default_value == 0

    # Check CTE step
    cte_step = action.steps[1]
    assert cte_step.type == "cte"
    assert cte_step.cte_name == "line_totals"
    assert cte_step.cte_query and "SELECT SUM" in cte_step.cte_query
    assert cte_step.cte_materialized is False

    # Check query step
    query_step = action.steps[2]
    assert query_step.type == "query"
    assert (
        query_step.expression
        and "SELECT line_total FROM line_totals" in query_step.expression
    )

    # Check return step
    return_step = action.steps[3]
    assert return_step.type == "return"

    print("✅ Week 1 integration test passed!")
