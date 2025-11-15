"""Tests for call_function action type"""


from src.core.specql_parser import SpecQLParser


def test_call_function_with_return():
    """Test calling function and capturing return value"""
    yaml_content = """
    entity: Invoice
    actions:
      - name: process_invoice
        steps:
          - declare:
              name: calculated_total
              type: numeric

          - call_function:
              function: billing.calculate_total
              arguments:
                invoice_id: $invoice_id
              returns: calculated_total

          - update: Invoice SET total_amount = calculated_total WHERE id = $invoice_id
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[1].type == "call_function"
    assert action.steps[1].call_function_name == "billing.calculate_total"
    assert action.steps[1].call_function_return_variable == "calculated_total"


def test_call_function_composition():
    """Test calling multiple functions in sequence"""
    yaml_content = """
    entity: Order
    actions:
      - name: complex_calculation
        steps:
          - call_function:
              function: calculate_subtotal
              arguments:
                order_id: $order_id
              returns: subtotal

          - call_function:
              function: calculate_tax
              arguments:
                amount: $subtotal
                region: $region
              returns: tax_amount

          - call_function:
              function: apply_discount
              arguments:
                amount: $subtotal
                customer_id: $customer_id
              returns: discount_amount

          - return: discount_amount
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    call_steps = [s for s in action.steps if s.type == "call_function"]
    assert len(call_steps) == 3