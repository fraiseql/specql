# Temporal Range Pattern

**Category**: Temporal Patterns
**Use Case**: Filter entities by effective date ranges and validity periods
**Complexity**: Low
**Enterprise Feature**: ✅ Yes

## Overview

The temporal range pattern provides efficient filtering of entities based on their effective dates and validity periods. This pattern is essential for:

- Current vs historical data separation
- Future-dated content management
- Date range analytics
- Validity period queries

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity` | entity_reference | ✅ | - | Entity to filter temporally |
| `start_date_field` | string | ✅ | - | Start of validity period |
| `end_date_field` | string | ❌ | NULL | End of validity period (NULL = ongoing) |
| `filter_mode` | enum | ❌ | current | Predefined filter mode |
| `custom_date_range` | object | ❌ | - | Custom date range filter |

## Generated SQL Features

- ✅ `daterange` validity periods with GiST indexing
- ✅ Predefined filter modes (current, future, historical)
- ✅ Custom date range filtering
- ✅ Convenience flags for temporal status
- ✅ Efficient range overlap queries

## Examples

### Example 1: Current Contracts

```yaml
views:
  - name: v_contract_current
    pattern: temporal/temporal_range
    config:
      entity: Contract
      start_date_field: effective_date
      end_date_field: expiration_date
      filter_mode: current
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_contract_current AS
SELECT
    v_contract_current.*,

    -- Computed validity range
    daterange(effective_date, expiration_date, '[)') AS validity_range,

    -- Convenience flags
    CASE
        WHEN effective_date <= CURRENT_DATE
            AND (expiration_date IS NULL OR expiration_date >= CURRENT_DATE)
        THEN true
        ELSE false
    END AS is_currently_valid,

    CASE
        WHEN effective_date > CURRENT_DATE THEN true
        ELSE false
    END AS is_future,

    CASE
        WHEN expiration_date IS NOT NULL AND expiration_date < CURRENT_DATE
        THEN true
        ELSE false
    END AS is_historical

FROM tenant.tb_contract v_contract_current
WHERE v_contract_current.deleted_at IS NULL
  AND effective_date <= CURRENT_DATE
  AND (expiration_date IS NULL OR expiration_date >= CURRENT_DATE);

-- Temporal range index
CREATE INDEX IF NOT EXISTS idx_v_contract_current_validity_range
    ON tenant.v_contract_current USING GIST (validity_range);
```

### Example 2: Future Contracts

```yaml
views:
  - name: v_contract_future
    pattern: temporal/temporal_range
    config:
      entity: Contract
      start_date_field: effective_date
      end_date_field: expiration_date
      filter_mode: future
```

### Example 3: Custom Date Range

```yaml
views:
  - name: v_contract_q1_2024
    pattern: temporal/temporal_range
    config:
      entity: Contract
      start_date_field: effective_date
      end_date_field: expiration_date
      filter_mode: custom_range
      custom_date_range:
        start: "2024-01-01"
        end: "2024-04-01"
```

## Usage Examples

### Current State Queries

```sql
-- Get all currently active contracts
SELECT * FROM v_contract_current;

-- Count active contracts by type
SELECT contract_type, COUNT(*) AS active_count
FROM v_contract_current
GROUP BY contract_type
ORDER BY active_count DESC;
```

### Historical Analysis

```sql
-- Contracts that were active during Q1 2024
SELECT *
FROM v_contract_temporal
WHERE validity_range && daterange('2024-01-01', '2024-04-01');

-- Contracts that became effective in 2024
SELECT *
FROM v_contract_temporal
WHERE EXTRACT(YEAR FROM effective_date) = 2024;
```

### Future Planning

```sql
-- Contracts that will become active next month
SELECT *
FROM v_contract_future
WHERE effective_date <= CURRENT_DATE + INTERVAL '1 month';

-- Upcoming expirations
SELECT *
FROM v_contract_current
WHERE expiration_date <= CURRENT_DATE + INTERVAL '30 days'
ORDER BY expiration_date;
```

### Advanced Range Queries

```sql
-- Find overlapping contracts for same customer
SELECT c1.pk_contract, c2.pk_contract, c1.validity_range && c2.validity_range AS overlaps
FROM v_contract_temporal c1
JOIN v_contract_temporal c2
    ON c1.fk_customer = c2.fk_customer
    AND c1.pk_contract < c2.pk_contract
    AND c1.validity_range && c2.validity_range;  -- Ranges overlap
```

## When to Use

✅ **Use when**:
- Need to separate current/historical/future data
- Require date range filtering
- Building dashboards with temporal dimensions
- Managing validity periods

❌ **Don't use when**:
- All data is current (use direct table access)
- Need point-in-time snapshots (use snapshot pattern)
- Complex temporal relationships (use SCD Type 2)

## Performance Considerations

- **Indexing**: GiST indexes enable fast range overlap queries (`&&`, `@>`, `<<`, etc.)
- **Partitioning**: Consider date-based partitioning for time-series data
- **Materialized Views**: For frequently queried temporal subsets
- **Query Planning**: PostgreSQL can use range indexes for complex temporal filters

## Range Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `&&` | Overlap (ranges overlap) | `range1 && range2` |
| `@>` | Contains (range contains point/date) | `range @> '2024-01-01'::date` |
| `<@` | Contained by (point/date in range) | `'2024-01-01'::date <@ range` |
| `<<` | Strictly left of (ends before start) | `range1 << range2` |
| `>>` | Strictly right of (starts after end) | `range1 >> range2` |

## Related Patterns

- **Snapshot**: Point-in-time queries with validity ranges
- **SCD Type 2**: Version management with temporal ranges
- **Audit Trail**: Historical change tracking