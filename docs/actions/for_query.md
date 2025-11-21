# for_query - Iterate Over Query Results

Execute a block of steps for each row returned by a SQL query.

## Syntax

```yaml
- for_query: SELECT column1, column2 FROM table WHERE condition
  as: record_variable
  loop:
    - step1
    - step2
    # ... more steps
```

## Parameters

- `query`: SQL SELECT statement to execute
- `as`: Variable name for the current row (default: "rec")
- `loop`: Array of steps to execute for each row

## Examples

### Basic Iteration

```yaml
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
```

### Complex Query with Ordering

```yaml
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
```

## Accessing Row Data

Within the loop, access row columns using dot notation:

```yaml
- for_query: SELECT id, name, email FROM users
  as: user
  loop:
    - call_function:
        function: send_welcome_email
        arguments:
          user_id: user.id
          email: user.email
          name: user.name
```

## Notes

- The query is executed once at the start of the loop
- Each row becomes available as the specified variable
- Variables declared outside the loop are accessible inside
- Use appropriate indexing for large result sets
- The loop variable is scoped to the loop body
