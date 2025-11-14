# declare - Variable Declaration

Declare local variables for use within an action.

## Syntax

Single variable:
```yaml
- declare:
    name: variable_name
    type: numeric
    default: 0
```

Multiple variables:
```yaml
- declare:
    - name: total
      type: numeric
      default: 0
    - name: count
      type: integer
```

## Supported Types
- text, integer, bigint, numeric, decimal
- boolean, uuid, timestamp, date, time
- json, array

## Examples

See `examples/actions/declare_examples.yaml`