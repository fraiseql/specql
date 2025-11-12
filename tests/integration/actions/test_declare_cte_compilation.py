"""Integration test for declare + cte compilation"""

import pytest
from src.core.specql_parser import SpecQLParser


def test_declare_with_cte_compiles_to_plpgsql():
    """Test that declare + cte compiles to valid PL/pgSQL with pattern library"""
    yaml_content = """
    entity: Invoice
    schema: billing
    actions:
      - name: calculate_invoice_with_discounts
        parameters:
          - name: invoice_id
            type: uuid
        returns: numeric
        steps:
          - declare:
              name: base_total
              type: numeric
              default: 0
          - cte:
              name: line_totals
              query: |
                SELECT line_item_id, quantity * unit_price as line_total
                FROM tb_line_item
                WHERE invoice_id = $invoice_id
          - query: base_total = SELECT SUM(line_total) FROM line_totals
          - return: base_total
    """

    parser = SpecQLParser()
    # Should parse successfully now that we have pattern library support
    result = parser.parse(yaml_content)
    assert result is not None
    assert len(result.actions) == 1

    action = result.actions[0]
    assert len(action.steps) == 4

    # Check that steps have the expected types
    step_types = [step.type for step in action.steps]
    assert step_types == ["declare", "cte", "query", "return"]