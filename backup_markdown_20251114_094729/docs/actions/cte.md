# cte - Common Table Expression

Define reusable query expressions (CTEs) for complex queries.

## Syntax

```yaml
- cte:
    name: cte_name
    query: |
      SELECT ...
      FROM ...
    materialized: false  # optional
```

## Multiple CTEs

```yaml
- cte:
    name: first_cte
    query: SELECT ...

- cte:
    name: second_cte
    query: |
      SELECT ...
      FROM first_cte  # Can reference previous CTEs
```

## Examples

See `examples/actions/cte_examples.yaml`