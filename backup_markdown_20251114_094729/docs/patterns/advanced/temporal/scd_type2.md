# Temporal SCD Type 2 Pattern

**Category**: Temporal Patterns
**Use Case**: Slowly Changing Dimensions with automatic version management
**Complexity**: Medium
**Enterprise Feature**: ✅ Yes

## Overview

The SCD Type 2 (Slowly Changing Dimension Type 2) pattern automatically manages entity versioning, creating new records for each change while preserving historical versions. Essential for:

- Customer address history
- Product catalog versioning
- Organizational structure changes
- Regulatory reporting with historical accuracy

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity` | entity_reference | ✅ | - | Entity to version |
| `effective_date_field` | string | ❌ | effective_date | When version became effective |
| `end_date_field` | string | ❌ | end_date | When version ended |
| `is_current_field` | string | ❌ | is_current | Current version flag |
| `version_number_field` | string | ❌ | version_number | Version sequence number |
| `surrogate_key_field` | string | ❌ | auto | Surrogate key for SCD |

## Generated SQL Features

- ✅ Automatic versioning triggers on UPDATE
- ✅ Surrogate keys for unique version identification
- ✅ Temporal validity ranges (`tsrange`)
- ✅ Version sequence numbering
- ✅ Current version constraints

## Examples

### Example 1: Customer Address History

```yaml
views:
  - name: v_customer_scd
    pattern: temporal/scd_type2
    config:
      entity: Customer
      effective_date_field: effective_date
      end_date_field: end_date
      is_current_field: is_current
      version_number_field: version_number
```

**Generated SQL**:
```sql
-- SCD Type 2 view
CREATE OR REPLACE VIEW tenant.v_customer_scd AS
SELECT
    -- Surrogate key (unique per version)
    ROW_NUMBER() OVER (ORDER BY pk_customer, effective_date) AS surrogate_key,

    -- Natural key (same across versions)
    pk_customer AS natural_key,

    -- All entity attributes
    v_customer_scd.*,

    -- SCD Type 2 metadata
    effective_date,
    end_date,
    is_current,

    -- Version tracking
    ROW_NUMBER() OVER (
        PARTITION BY pk_customer
        ORDER BY effective_date
    ) AS version_number,

    -- Validity range
    tsrange(effective_date, end_date, '[)') AS valid_period

FROM tenant.tb_customer v_customer_scd
WHERE deleted_at IS NULL;

-- Unique constraint on current version
CREATE UNIQUE INDEX IF NOT EXISTS idx_v_customer_scd_current_unique
    ON tenant.v_customer_scd(pk_customer)
    WHERE is_current = true;

-- Temporal index
CREATE INDEX IF NOT EXISTS idx_v_customer_scd_temporal_lookup
    ON tenant.v_customer_scd USING GIST (pk_customer, valid_period);

-- SCD trigger function
CREATE OR REPLACE FUNCTION tenant.tb_customer_scd_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Close old version
    UPDATE tenant.tb_customer
    SET
        end_date = CURRENT_DATE,
        is_current = false
    WHERE pk_customer = OLD.pk_customer
      AND is_current = true;

    -- Insert new version
    INSERT INTO tenant.tb_customer (
        pk_customer,
        -- ... all fields from NEW
        effective_date,
        end_date,
        is_current
    ) VALUES (
        NEW.pk_customer,
        -- ... all new values
        CURRENT_DATE,
        NULL,
        true
    );

    RETURN NULL;  -- Prevent original UPDATE
END;
$$ LANGUAGE plpgsql;

-- Attach trigger
CREATE TRIGGER trg_tb_customer_scd
BEFORE UPDATE ON tenant.tb_customer
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION tenant.tb_customer_scd_trigger();
```

## Usage Examples

### Version History Queries

```sql
-- Get all versions of customer #123
SELECT *
FROM v_customer_scd
WHERE natural_key = 123
ORDER BY version_number DESC;

-- Get current version only
SELECT *
FROM v_customer_scd
WHERE natural_key = 123
  AND is_current = true;

-- Get version effective on specific date
SELECT *
FROM v_customer_scd
WHERE natural_key = 123
  AND valid_period @> '2024-01-15'::date;
```

### Change Analysis

```sql
-- See what changed between versions
SELECT
    v1.natural_key,
    v1.version_number AS old_version,
    v2.version_number AS new_version,
    v1.address AS old_address,
    v2.address AS new_address,
    v2.effective_date AS change_date
FROM v_customer_scd v1
JOIN v_customer_scd v2
    ON v1.natural_key = v2.natural_key
    AND v1.version_number = v2.version_number - 1
WHERE v1.address IS DISTINCT FROM v2.address
ORDER BY v2.effective_date DESC;
```

### Reporting Queries

```sql
-- Customer count by version changes in last year
SELECT
    DATE_TRUNC('month', effective_date) AS month,
    COUNT(DISTINCT natural_key) AS customers_with_changes
FROM v_customer_scd
WHERE effective_date >= CURRENT_DATE - INTERVAL '1 year'
  AND version_number > 1  -- Exclude original versions
GROUP BY DATE_TRUNC('month', effective_date)
ORDER BY month;
```

## When to Use

✅ **Use when**:
- Need to track all historical versions of entities
- Changes are infrequent but must be preserved
- Regulatory requirements for historical accuracy
- Data warehousing and dimensional modeling

❌ **Don't use when**:
- Changes are very frequent (consider audit trail instead)
- Only current state matters (use snapshot pattern)
- Need to track who made changes (use audit trail)

## Performance Considerations

- **Indexing**: GiST indexes for temporal queries, unique constraints for current versions
- **Partitioning**: Consider partitioning by effective_date for large datasets
- **Trigger Overhead**: UPDATE operations become INSERT + UPDATE
- **Storage**: Each change creates a new row

## SCD Type 2 vs Other Patterns

| Pattern | Use Case | Storage | Query Complexity |
|---------|----------|---------|------------------|
| **SCD Type 2** | Full history, dimensional modeling | High (new row per change) | Medium |
| **Snapshot** | Point-in-time queries | Medium (computed ranges) | Low |
| **Audit Trail** | Complete change tracking | High (all changes logged) | High |

## Implementation Notes

- **Trigger Behavior**: UPDATE operations are converted to version closures + new version creation
- **Constraints**: Only one current version per natural key
- **Data Integrity**: Surrogate keys ensure unique version identification
- **Temporal Queries**: Use `@>` operator for point-in-time queries

## Related Patterns

- **Snapshot**: Point-in-time views without automatic versioning
- **Audit Trail**: Change tracking with user information
- **Temporal Range**: Filter by effective date ranges