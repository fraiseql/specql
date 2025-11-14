# aggregate - Aggregate Operations

Perform SQL aggregate functions (SUM, COUNT, AVG, etc.) on table data.

## Syntax

```yaml
- aggregate:
    operation: sum|count|avg|min|max
    field: field_name
    from: table_name
    where: condition (optional)
    group_by: field_name (optional)
    as: result_variable
```

## Parameters

- `operation`: The aggregate function (sum, count, avg, min, max)
- `field`: The field to aggregate (use "*" for COUNT(*))
- `from`: The table to query
- `where`: Optional WHERE condition
- `group_by`: Optional GROUP BY field (for grouped aggregates)
- `as`: Variable to store the result

## Examples

### Simple Sum
```yaml
entity: Invoice
actions:
  - name: calculate_total
    steps:
      - aggregate:
          operation: sum
          field: amount
          from: tb_line_item
          where: invoice_id = $invoice_id
          as: total_amount
      - return: total_amount
```

### Count Records
```yaml
entity: Order
actions:
  - name: get_order_count
    steps:
      - aggregate:
          operation: count
          field: id
          from: tb_order
          where: status = 'completed'
          as: completed_orders
      - return: completed_orders
```

### Grouped Aggregate
```yaml
entity: Analytics
actions:
  - name: sales_by_region
    steps:
      - aggregate:
          operation: sum
          field: amount
          from: tb_order
          group_by: region
          as: regional_totals
      - return: regional_totals
```

## Generated SQL

```sql
-- Simple aggregate
SELECT SUM(amount) INTO total_amount FROM tb_line_item WHERE invoice_id = $invoice_id;

-- Grouped aggregate
regional_totals := ARRAY(SELECT SUM(amount) FROM tb_order GROUP BY region);
```

## Notes

- For grouped aggregates, results are stored as arrays
- Single-value aggregates use SELECT INTO
- Supports all standard SQL aggregate functions