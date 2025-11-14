# Wrapper Patterns

## Overview

Wrapper patterns enhance existing views with additional functionality. These patterns are essential for ensuring complete result sets, managing materialized view refreshes, and providing consistent interfaces.

**Use Cases:**
- Complete result sets (include zero-count entities)
- Materialized view management
- Cached aggregation wrappers
- Consistent API interfaces

## Complete Set Wrapper Pattern

**Category**: Wrapper Patterns
**Use Case**: Wrap materialized view to ensure complete result sets
**Complexity**: Medium
**PrintOptim Examples**: 4 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `materialized_view` | string | ✅ | MV to wrap |
| `base_table` | string | ✅ | Source table for completeness |
| `key_field` | string | ✅ | Join key field |
| `default_values` | object | ✅ | Default values for missing entities |
| `ensure_zero_count_entities` | boolean | ❌ | Include entities with zero counts |

### Generated SQL

```sql
-- @fraiseql:view
-- @fraiseql:description Complete result set wrapper for mv_count_allocations_by_location
CREATE OR REPLACE VIEW tenant.v_count_allocations_by_location_optimized AS
-- Include all results from materialized view
SELECT * FROM tenant.mv_count_allocations_by_location

UNION ALL

-- Include missing entities with default values
SELECT
    base.pk_location,
    0 AS total_allocations,
    0 AS active_allocations,
    base.tenant_id
FROM tenant.tb_location base
WHERE NOT EXISTS (
    SELECT 1
    FROM tenant.mv_count_allocations_by_location mv
    WHERE mv.pk_location = base.pk_location
)
AND base.deleted_at IS NULL;
```

### Examples

#### Example: Complete Location Counts

```yaml
query_patterns:
  - name: count_allocations_by_location_optimized
    pattern: wrapper/complete_set
    config:
      materialized_view: mv_count_allocations_by_location
      base_table: tb_location
      key_field: pk_location
      default_values:
        total_allocations: 0
        active_allocations: 0
      ensure_zero_count_entities: true
```

### When to Use

✅ **Use when:**
- Need complete result sets
- Materialized views with missing entities
- Dashboard completeness requirements
- Zero-count visibility needed

❌ **Don't use when:**
- Partial results acceptable
- No materialized views
- Simple view wrapping not needed