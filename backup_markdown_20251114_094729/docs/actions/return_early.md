# return_early - Early Return from Function

Exit a function early with an optional return value.

## Syntax

### Simple Return
```yaml
- return_early
```

### Return with Value
```yaml
- return_early: NULL
```

### Return Complex Value
```yaml
- return_early:
    success: false
    message: "Validation failed"
    data: null
```

## Compilation

### Simple Return
```sql
RETURN;
```

### Return with Value
```sql
RETURN NULL;
```

### Mutation Result Return
```sql
RETURN ROW(
    false::BOOLEAN,
    'Validation failed'::TEXT,
    '{}'::JSONB,
    '{}'::JSONB
)::app.mutation_result;
```

## Use Cases

Early returns are useful for:
- Input validation failures
- Permission checks
- Resource not found scenarios
- Premature termination conditions

## Examples

See `examples/actions/return_early_examples.yaml`