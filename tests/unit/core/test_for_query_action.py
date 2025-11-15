"""Tests for for_query loop action"""

from src.core.specql_parser import SpecQLParser


def test_for_query_basic():
    """Test iteration over query results"""
    yaml_content = """
    entity: Report
    actions:
      - name: process_all_orders
        steps:
          - declare:
              name: total
              type: numeric
              default: 0
          - for_query: SELECT id, amount FROM orders WHERE status = 'active'
            as: order_record
            loop:
              - query: total = total + order_record.amount
              - if: order_record.amount > 1000
                then:
                  - call_function:
                      function: flag_large_order
                      arguments: {order_id: order_record.id}
          - return: total
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[1].type == "for_query"
    assert action.steps[1].for_query_sql == "SELECT id, amount FROM orders WHERE status = 'active'"
    assert action.steps[1].for_query_alias == "order_record"
    assert len(action.steps[1].for_query_body) == 2


def test_for_query_with_limit():
    """Test for_query with LIMIT and ORDER BY"""
    yaml_content = """
    entity: Notification
    actions:
      - name: send_recent_notifications
        steps:
          - for_query: |
              SELECT id, user_id, message
              FROM notifications
              WHERE sent_at IS NULL
              ORDER BY created_at DESC
              LIMIT 100
            as: notification
            loop:
              - call_service:
                  service: email_service
                  operation: send
                  input: {to: notification.user_id, message: notification.message}
              - update: Notification SET sent_at = now() WHERE id = notification.id
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "for_query"
    assert "ORDER BY created_at DESC" in action.steps[0].for_query_sql
    assert "LIMIT 100" in action.steps[0].for_query_sql
    assert action.steps[0].for_query_alias == "notification"