# Temporal Snapshot Pattern

**Category**: Temporal Patterns
**Use Case**: Point-in-time queries, version history tracking
**Complexity**: Medium
**Enterprise Feature**: ✅ Yes

## Overview

The temporal snapshot pattern enables querying historical states of entities using PostgreSQL range types (`tsrange`). This pattern is essential for:

- Contract version tracking
- Audit compliance (SOC2, GDPR)
- Historical reporting
- Time-travel queries

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity` | entity_reference | ✅ | - | Entity to snapshot |
| `effective_date_field` | string | ✅ | - | When version became effective |
| `end_date_field` | string | ❌ | NULL | When version was superseded |
| `snapshot_mode` | enum | ❌ | point_in_time | Snapshot retrieval mode |
| `include_validity_range` | boolean | ❌ | true | Include tsrange column |

## Generated SQL Features

- ✅ `tsrange` validity periods with GiST indexing
- ✅ `LEAD()` window function for auto-computed end dates
- ✅ Point-in-time queries using `@>` operator
- ✅ `is_current` flag for active versions
- ✅ Temporal joins with overlapping ranges

## Examples

### Example 1: Contract Version History

```yaml
views:
  - name: v_contract_snapshot
    pattern: temporal/snapshot
    config:
      entity: Contract
      effective_date_field: effective_date
      end_date_field: superseded_date
      snapshot_mode: full_history
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_contract_snapshot AS
SELECT
    pk_contract,
    v_contract_snapshot.*,

    -- Temporal validity range
    tsrange(
        effective_date,
        LEAD(effective_date) OVER (
            PARTITION BY pk_contract
            ORDER BY effective_date
        ),
        '[)'  -- Inclusive start, exclusive end
    ) AS valid_period,

    -- Convenience flags
    superseded_date IS NULL AS is_current,
    effective_date AS version_effective_date,
    LEAD(effective_date) OVER (
        PARTITION BY pk_contract
        ORDER BY effective_date
    ) AS version_superseded_date

FROM tenant.tb_contract v_contract_snapshot
WHERE deleted_at IS NULL
ORDER BY pk_contract, effective_date DESC;

-- Temporal index for point-in-time queries
CREATE INDEX IF NOT EXISTS idx_v_contract_snapshot_temporal
    ON tenant.v_contract_snapshot USING GIST (pk_contract, valid_period);

-- Index for current version lookup
CREATE INDEX IF NOT EXISTS idx_v_contract_snapshot_current
    ON tenant.v_contract_snapshot(pk_contract)
    WHERE is_current = true;

COMMENT ON VIEW tenant.v_contract_snapshot IS
    'Temporal snapshot of Contract with validity ranges. Query as of date: WHERE valid_period @> ''2024-01-15''::date';
```

### Example 2: Current State Only

```yaml
views:
  - name: v_contract_current
    pattern: temporal/snapshot
    config:
      entity: Contract
      effective_date_field: effective_date
      end_date_field: superseded_date
      snapshot_mode: current_only
```

## Usage Examples

### Point-in-Time Queries

```sql
-- Get contract state as of 2024-01-15
SELECT *
FROM v_contract_snapshot
WHERE valid_period @> '2024-01-15'::date;

-- Get all historical versions of contract #123
SELECT *
FROM v_contract_snapshot
WHERE pk_contract = 123
ORDER BY version_effective_date DESC;

-- Get only current versions
SELECT *
FROM v_contract_snapshot
WHERE is_current = true;
```

### Temporal Joins

```sql
-- Join contracts with their pricing at the same time
SELECT c.*, p.price
FROM v_contract_snapshot c
JOIN v_pricing_snapshot p
    ON c.pk_contract = p.fk_contract
    AND c.valid_period && p.valid_period  -- Overlapping validity periods
WHERE c.valid_period @> '2024-01-15'::date;
```

### Historical Reporting

```sql
-- Count contracts by month of creation
SELECT
    DATE_TRUNC('month', version_effective_date) AS month,
    COUNT(*) AS new_contracts
FROM v_contract_snapshot
WHERE version_effective_date >= '2024-01-01'
GROUP BY DATE_TRUNC('month', version_effective_date)
ORDER BY month;
```

## When to Use

✅ **Use when**:
- Need to track entity version history
- Require point-in-time queries
- Building audit trails or compliance reports
- Managing slowly changing dimensions

❌ **Don't use when**:
- Entity never changes (use direct table access)
- Need real-time performance (consider materialized views)
- Simple current state queries (use base table)

## Performance Considerations

- **Indexing**: GiST indexes on `tsrange` columns enable fast temporal queries
- **Partitioning**: Consider date-based partitioning for large datasets
- **Materialized Views**: For frequently queried historical data
- **Archival**: Implement data retention policies for old versions

## Related Patterns

- **Audit Trail**: Complete change history with before/after values
- **SCD Type 2**: Automated version management with triggers
- **Temporal Range**: Filter entities by effective date ranges