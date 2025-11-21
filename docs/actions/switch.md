# switch - Switch/Case Statements

Execute different code paths based on the value of an expression.

## Syntax

### Simple Value Matching
```yaml
- switch:
    expression: $variable_name
    cases:
      - when: 'value1'
        then:
          - action1
          - action2
      - when: 'value2'
        then:
          - action3
    default:
      - default_action
```

### Complex Conditions
```yaml
- switch:
    expression: (field1, field2)
    cases:
      - when: field1 > 100 AND field2 = 'active'
        then:
          - high_value_active_action
      - when: field1 > 50
        then:
          - medium_value_action
    default:
      - low_value_action
```

## Compilation

### Simple Cases → CASE WHEN
```sql
CASE variable_name
  WHEN 'value1' THEN
    -- action1
    -- action2
  WHEN 'value2' THEN
    -- action3
  ELSE
    -- default_action
END CASE;
```

### Complex Conditions → IF/ELSIF
```sql
IF field1 > 100 AND field2 = 'active' THEN
  -- high_value_active_action
ELSIF field1 > 50 THEN
  -- medium_value_action
ELSE
  -- low_value_action
END IF;
```

## Examples

See `examples/actions/switch_examples.yaml`
