"""Tests for batch_operation action"""

from src.core.specql_parser import SpecQLParser


def test_batch_insert():
    """Test batch insert operation"""
    yaml_content = """
    entity: Product
    actions:
      - name: bulk_import_products
        steps:
          - batch_operation:
              type: insert
              entity: Product
              data:
                - {name: "Product A", price: 10.99, category: "electronics"}
                - {name: "Product B", price: 25.50, category: "books"}
                - {name: "Product C", price: 5.99, category: "clothing"}
          - return: "Products imported successfully"
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "batch_operation"
    assert action.steps[0].batch_operation_type == "insert"
    assert action.steps[0].batch_entity == "Product"
    assert len(action.steps[0].batch_data) == 3
    assert action.steps[0].batch_data[0]["name"] == "Product A"


def test_batch_update():
    """Test batch update operation"""
    yaml_content = """
    entity: Inventory
    actions:
      - name: update_stock_levels
        steps:
          - batch_operation:
              type: update
              entity: Inventory
              data:
                - {product_id: 1, quantity: 50, location: "warehouse_a"}
                - {product_id: 2, quantity: 25, location: "warehouse_b"}
                - {product_id: 3, quantity: 100, location: "warehouse_a"}
          - return: "Stock levels updated"
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "batch_operation"
    assert action.steps[0].batch_operation_type == "update"
    assert action.steps[0].batch_entity == "Inventory"
    assert len(action.steps[0].batch_data) == 3


def test_batch_delete():
    """Test batch delete operation"""
    yaml_content = """
    entity: Order
    actions:
      - name: cancel_orders
        steps:
          - batch_operation:
              type: delete
              entity: Order
              data:
                - {id: 1001}
                - {id: 1002}
                - {id: 1003}
          - return: "Orders cancelled"
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "batch_operation"
    assert action.steps[0].batch_operation_type == "delete"
    assert action.steps[0].batch_entity == "Order"
    assert len(action.steps[0].batch_data) == 3