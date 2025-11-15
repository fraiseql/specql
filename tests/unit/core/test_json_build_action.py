"""Tests for json_build action"""

from src.core.specql_parser import SpecQLParser


def test_json_build_simple_object():
    """Test building a simple JSON object"""
    yaml_content = """
    entity: User
    actions:
      - name: create_user_profile
        steps:
          - json_build:
              name: profile
              object:
                name: $name
                email: $email
                age: $age
          - return: profile
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "json_build"
    assert action.steps[0].json_variable_name == "profile"
    assert action.steps[0].json_object == {"name": "$name", "email": "$email", "age": "$age"}


def test_json_build_nested_object():
    """Test building nested JSON objects"""
    yaml_content = """
    entity: Order
    actions:
      - name: create_order_summary
        steps:
          - json_build:
              name: summary
              object:
                id: $order_id
                customer:
                  name: $customer_name
                  email: $customer_email
                items: $line_items
                total: $total_amount
          - return: summary
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "json_build"
    expected = {
        "id": "$order_id",
        "customer": {
            "name": "$customer_name",
            "email": "$customer_email"
        },
        "items": "$line_items",
        "total": "$total_amount"
    }
    assert action.steps[0].json_object == expected


def test_json_build_with_expressions():
    """Test json_build with computed expressions"""
    yaml_content = """
    entity: Report
    actions:
      - name: generate_report
        steps:
          - json_build:
              name: report_data
              object:
                period: $period
                total_sales: SUM(sales.amount)
                average_order: AVG(orders.total)
                status: 'completed'
          - return: report_data
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "json_build"
    expected = {
        "period": "$period",
        "total_sales": "SUM(sales.amount)",
        "average_order": "AVG(orders.total)",
        "status": "completed"
    }
    assert action.steps[0].json_object == expected