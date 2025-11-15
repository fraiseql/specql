"""Tests for upsert action"""

from src.core.specql_parser import SpecQLParser


def test_upsert_basic():
    """Test basic upsert (INSERT ON CONFLICT UPDATE)"""
    yaml_content = """
    entity: Product
    actions:
      - name: upsert_product
        steps:
          - upsert:
              entity: Product
              fields:
                id: $product_id
                name: $name
                price: $price
                updated_at: now()
              conflict_target: id
              conflict_action:
                price: EXCLUDED.price
                updated_at: EXCLUDED.updated_at
          - return: "Product upserted"
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "upsert"
    assert action.steps[0].upsert_entity == "Product"
    assert action.steps[0].upsert_fields["id"] == "$product_id"
    assert action.steps[0].upsert_conflict_target == "id"
    assert action.steps[0].upsert_conflict_action["price"] == "EXCLUDED.price"


def test_upsert_multiple_conflict_targets():
    """Test upsert with multiple conflict target columns"""
    yaml_content = """
    entity: Inventory
    actions:
      - name: update_stock
        steps:
          - upsert:
              entity: Inventory
              fields:
                product_id: $product_id
                warehouse_id: $warehouse_id
                quantity: $quantity
                last_updated: now()
              conflict_target: (product_id, warehouse_id)
              conflict_action:
                quantity: Inventory.quantity + EXCLUDED.quantity
                last_updated: EXCLUDED.last_updated
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "upsert"
    assert action.steps[0].upsert_conflict_target == "(product_id, warehouse_id)"
    expected_action = {
        "quantity": "Inventory.quantity + EXCLUDED.quantity",
        "last_updated": "EXCLUDED.last_updated"
    }
    assert action.steps[0].upsert_conflict_action == expected_action


def test_upsert_no_conflict():
    """Test upsert with DO NOTHING on conflict"""
    yaml_content = """
    entity: User
    actions:
      - name: insert_if_not_exists
        steps:
          - upsert:
              entity: User
              fields:
                email: $email
                name: $name
                created_at: now()
              conflict_target: email
              conflict_action: DO_NOTHING
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "upsert"
    assert action.steps[0].upsert_conflict_action == "DO_NOTHING"