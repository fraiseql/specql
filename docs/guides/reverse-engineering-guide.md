# Reverse Engineering Guide

## Overview

SpecQL's reverse engineering feature allows you to convert existing PostgreSQL functions written in PL/pgSQL into SpecQL YAML actions. This is useful for migrating legacy codebases or understanding complex business logic.

## Supported SQL Features

The reverse engineering parser now supports the following advanced SQL constructs:

### ✅ Common Table Expressions (CTEs)

**Recursive CTEs** with depth tracking:
```sql
WITH RECURSIVE hierarchy AS (
    SELECT id, parent_id, name, 0 as level
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    SELECT c.id, c.parent_id, c.name, h.level + 1
    FROM categories c
    JOIN hierarchy h ON c.parent_id = h.id
)
SELECT * FROM hierarchy ORDER BY level, id;
```

**Nested CTEs** with multiple references:
```sql
WITH
active_users AS (SELECT id, email FROM users WHERE active = true),
recent_orders AS (SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id)
SELECT au.*, ro.order_count
FROM active_users au
LEFT JOIN recent_orders ro ON au.id = ro.user_id;
```

### ✅ Exception Handling

**WHEN clauses** with specific exception types:
```sql
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'Duplicate key';
    WHEN not_null_violation THEN
        RAISE EXCEPTION 'Required field missing';
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Unknown error: %', SQLERRM;
```

**Nested exception blocks** with transaction control:
```sql
BEGIN
    BEGIN
        -- Inner operations
        UPDATE accounts SET balance = balance - 100;
    EXCEPTION
        WHEN insufficient_funds THEN
            ROLLBACK;
            RAISE EXCEPTION 'Insufficient funds';
    END;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE EXCEPTION 'Transaction failed';
END;
```

### ✅ Cursor Operations

**Full cursor lifecycle** (DECLARE → OPEN → FETCH → CLOSE):
```sql
DECLARE
    contact_cursor CURSOR FOR SELECT * FROM contacts WHERE status = 'pending';
    contact_record record;
BEGIN
    OPEN contact_cursor;
    LOOP
        FETCH contact_cursor INTO contact_record;
        EXIT WHEN NOT FOUND;

        UPDATE contacts SET processed_at = NOW() WHERE id = contact_record.id;
    END LOOP;
    CLOSE contact_cursor;
END;
```

**Parameterized cursors**:
```sql
DECLARE
    status_cursor CURSOR (status_param text) FOR
        SELECT * FROM contacts WHERE status = status_param;
BEGIN
    OPEN status_cursor ('active');
    -- Process records
    CLOSE status_cursor;
END;
```

### ✅ Dynamic SQL

**EXECUTE statements** with dynamic query construction:
```sql
DECLARE
    query_text text;
    table_name text := 'contacts';
BEGIN
    query_text := 'UPDATE ' || table_name || ' SET processed = true WHERE id = $1';
    EXECUTE query_text USING contact_id;
END;
```

### ✅ Complex Control Flow

**Advanced FOR loops** with record iteration:
```sql
FOR contact_record IN SELECT * FROM contacts WHERE status = 'pending' LOOP
    IF contact_record.priority > 5 THEN
        UPDATE contacts SET status = 'processing' WHERE id = contact_record.id;
    ELSIF contact_record.priority > 2 THEN
        UPDATE contacts SET status = 'queued' WHERE id = contact_record.id;
    ELSE
        CONTINUE;
    END IF;
END LOOP;
```

### ✅ Window Functions

**PARTITION BY and ORDER BY patterns**:
```sql
SELECT
    id,
    company_id,
    ROW_NUMBER() OVER (
        PARTITION BY company_id
        ORDER BY created_at DESC
    ) as contact_rank,
    LAG(created_at, 1) OVER (
        PARTITION BY company_id
        ORDER BY created_at
    ) as prev_contact_date
FROM contacts;
```

### ✅ Aggregate Filters

**FILTER WHERE clauses** in aggregate functions:
```sql
SELECT
    company_id,
    COUNT(*) as total_contacts,
    COUNT(*) FILTER (WHERE status = 'active') as active_contacts,
    AVG(created_at) FILTER (WHERE priority > 3) as avg_priority_date
FROM contacts
GROUP BY company_id;
```

## Usage

### Basic Reverse Engineering

```bash
# Convert a single SQL function
specql reverse my_function.sql

# Convert multiple files with output directory
specql reverse functions/*.sql -o entities/

# Preview conversion without writing files
specql reverse my_function.sql --preview

# Set minimum confidence threshold
specql reverse my_function.sql --min-confidence=0.90
```

### Advanced Options

```bash
# Skip AI enhancement for faster processing
specql reverse my_function.sql --no-ai

# Generate comparison report
specql reverse my_function.sql --compare

# Use only heuristic parsing (no AI)
specql reverse my_function.sql --use-heuristics
```

## Output

The reverse engineering process generates SpecQL YAML files with:

- **Function metadata**: Name, schema, parameters, return type
- **Confidence score**: How well the SQL was understood (0.0-1.0)
- **Detected patterns**: CTE, exception handling, cursors, etc.
- **Step breakdown**: Parsed business logic steps
- **Warnings**: Areas where parsing was uncertain

### Example Output

```yaml
entity: ProcessContacts
schema: crm
actions:
- name: process_pending_contacts
  parameters:
  - name: batch_size
    type: integer
    default: 100
  returns: integer
  steps:
  - declare: contact_cursor CURSOR FOR SELECT * FROM contacts WHERE status = 'pending'
  - cursor_open: contact_cursor
  - for_loop:
      iterator: contact_record
      collection: contact_cursor
      steps:
      - if:
          condition: contact_record.priority > 5
          then:
          - update: Contact SET status = 'processing', processed_at = NOW()
          else:
          - update: Contact SET status = 'queued'
  - cursor_close: contact_cursor
_metadata:
  confidence: 0.85
  generated_by: algorithmic_parser
  detected_patterns:
  - cursor_operations
  - complex_control_flow
  warnings:
  - Used fallback parsing for complex cursor operations
```

## Confidence Scores

The parser assigns confidence scores based on parsing success:

- **0.80+**: High confidence - well understood constructs
- **0.60-0.79**: Medium confidence - some fallback parsing used
- **< 0.60**: Low confidence - significant parsing challenges

## Best Practices

### Input SQL Quality
- Use clear, well-formatted PL/pgSQL
- Add comments to explain complex logic
- Avoid overly complex nested structures
- Use meaningful variable names

### Validation
- Always review generated YAML for accuracy
- Test generated functions against original SQL
- Use `--preview` mode for initial assessment
- Check confidence scores before production use

### Iterative Improvement
- Start with simple functions to validate conversion
- Gradually increase complexity
- Use `--compare` reports to track improvements
- Provide feedback on parsing issues

## Troubleshooting

### Low Confidence Scores
- **Cause**: Complex SQL constructs not fully recognized
- **Solution**: Simplify SQL or add comments explaining intent

### Missing Steps
- **Cause**: Parser couldn't map SQL to SpecQL actions
- **Solution**: Rewrite SQL using supported patterns

### Incorrect Logic
- **Cause**: Ambiguous SQL interpretation
- **Solution**: Add comments or restructure for clarity

## Integration with Development Workflow

Reverse engineering fits into SpecQL's development workflow:

1. **Legacy Migration**: Convert existing PL/pgSQL to SpecQL YAML
2. **Code Understanding**: Parse complex functions to understand logic
3. **Refactoring**: Use parsed YAML as starting point for improvements
4. **Documentation**: Generate YAML documentation from SQL

## Limitations

- Some extremely complex SQL may require manual conversion
- Dynamic SQL with complex string concatenation may not be fully parsed
- Very deeply nested control structures may lose some fidelity
- Custom PostgreSQL extensions may not be recognized

## Future Enhancements

The reverse engineering parser continues to improve with support for:
- More window function variants
- Advanced cursor features
- Complex transaction handling
- Custom PostgreSQL types and extensions</content>
</xai:function_call/>

<xai:function_call name="todowrite">
<parameter name="todos">[{"content":"Document the new parsers in project documentation","status":"completed","priority":"high","id":"document_new_parsers"}]