# subquery - Subquery Operations

Execute subqueries and capture their results in variables.

## Syntax

```yaml
- subquery:
    query: SQL query string
    as: result_variable
```

## Parameters

- `query`: The SQL subquery to execute
- `as`: Variable to store the single result value

## Examples

### Simple Subquery
```yaml
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
```

### Subquery in WHERE Clause
```yaml
entity: Customer
actions:
  - name: find_high_value_customers
    steps:
      - query: |
          SELECT * FROM tb_customer
          WHERE id IN (
            SELECT customer_id FROM tb_order
            WHERE total_amount > 1000
            GROUP BY customer_id
            HAVING COUNT(*) > 5
          )
      - return: result
```

## Generated SQL

```sql
-- Subquery result capture
SELECT (SELECT AVG(total_amount) FROM tb_order) INTO avg_order_value;
```

## Notes

- Subqueries should return single values
- For multi-row results, use regular `query` steps
- Supports complex nested subqueries