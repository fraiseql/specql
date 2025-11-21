# Extraction Patterns

Extraction patterns create efficient views that pre-filter data for optimal LEFT JOIN performance. These patterns are essential when you need to join with tables that have many NULL values or when you want to avoid processing irrelevant rows in JOIN operations.

## Overview

Extraction patterns solve a common performance problem: when doing LEFT JOINs with tables containing many NULL values, the database still needs to process all rows. By extracting only the relevant (non-NULL) data into separate views, you can make LEFT JOINs much more efficient.

## Component Extractor Pattern

The `extraction/component` pattern extracts non-NULL components from entities for efficient LEFT JOIN operations.

### Use Cases

✅ **Use when:**
- You have optional fields that are frequently NULL
- You need to LEFT JOIN with tables containing sparse data
- Performance is critical for read operations
- You want to avoid processing NULL rows in JOINs

❌ **Don't use when:**
- All fields are required (not NULL)
- The table has very few NULL values
- You're doing INNER JOINs (use direct joins instead)

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_entity` | entity_reference | ✅ | Entity containing the data to extract |
| `source_table` | string | ❌ | Specific table to extract from (defaults to entity table) |
| `extracted_fields` | array | ✅ | Fields to extract from the source |
| `filter_condition` | string | ❌ | SQL WHERE condition to filter extracted rows |
| `purpose` | string | ❌ | Documentation explaining why this extraction exists |
| `schema` | string | ❌ | Target schema (default: tenant) |

### Examples

#### Location Coordinates Extraction

```yaml
query_patterns:
  - name: coordinates
    pattern: extraction/component
    config:
      source_entity: Location
      extracted_fields:
        - name: latitude
        - name: longitude
      filter_condition: "latitude IS NOT NULL AND longitude IS NOT NULL"
      purpose: "Extract locations with coordinates to avoid NULL values in LEFT JOINs for mapping features"
```

**Generated SQL:**
```sql
CREATE OR REPLACE VIEW tenant.v_coordinates AS
SELECT
    pk_location AS pk_location,
    latitude,
    longitude
FROM tenant.tb_location
WHERE deleted_at IS NULL
  AND latitude IS NOT NULL AND longitude IS NOT NULL
  AND tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid;

CREATE INDEX IF NOT EXISTS idx_v_coordinates_pk_location
    ON tenant.v_coordinates(pk_location);
```

**Usage:**
```sql
-- Efficient LEFT JOIN - only processes rows with coordinates
SELECT
    loc.*,
    coords.latitude,
    coords.longitude
FROM tb_location loc
LEFT JOIN v_coordinates coords
    ON coords.pk_location = loc.pk_location;
```

#### Machine Warranty Information

```yaml
query_patterns:
  - name: warranty_info
    pattern: extraction/component
    config:
      source_entity: Machine
      extracted_fields:
        - name: warranty_end_date
        - name: installation_date
      filter_condition: "warranty_end_date IS NOT NULL"
      purpose: "Extract machines with warranty information for service planning"
```

## Temporal Extractor Pattern

The `extraction/temporal` pattern extracts entities based on temporal criteria (current, future, historical).

### Use Cases

✅ **Use when:**
- You need to filter entities by date ranges
- You have temporal business logic (active contracts, future events, etc.)
- You want to create cached views for temporal queries
- Performance is important for time-based filtering

❌ **Don't use when:**
- You don't have date/time fields
- You're doing simple equality filters
- Real-time accuracy is more important than performance

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_entity` | entity_reference | ✅ | Entity containing temporal data |
| `source_table` | string | ❌ | Specific table to extract from |
| `temporal_mode` | enum | ✅ | Type of temporal filtering: current, future, historical, date_range |
| `date_field_start` | string | ✅ | Field containing the start date/time |
| `date_field_end` | string | ❌ | Field containing the end date/time |
| `reference_date` | string | ❌ | Reference date (default: CURRENT_DATE) |
| `purpose` | string | ❌ | Documentation explaining the temporal logic |
| `schema` | string | ❌ | Target schema (default: tenant) |

### Examples

#### Current Active Contracts

```yaml
query_patterns:
  - name: current_contracts
    pattern: extraction/temporal
    config:
      source_entity: Contract
      temporal_mode: current
      date_field_start: start_date
      date_field_end: end_date
      reference_date: "CURRENT_DATE"
      purpose: "Extract currently active contracts for dashboard and reporting"
```

**Generated SQL:**
```sql
CREATE OR REPLACE VIEW tenant.v_current_contracts AS
SELECT *
FROM tenant.tb_contract
WHERE deleted_at IS NULL
  AND start_date <= CURRENT_DATE
  AND (end_date IS NULL OR end_date >= CURRENT_DATE)
  AND tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid;

CREATE INDEX IF NOT EXISTS idx_v_current_contracts_start_date
    ON tenant.v_current_contracts(start_date)
    INCLUDE (end_date);
```

#### Future Contracts

```yaml
query_patterns:
  - name: upcoming_contracts
    pattern: extraction/temporal
    config:
      source_entity: Contract
      temporal_mode: future
      date_field_start: start_date
      reference_date: "CURRENT_DATE"
      purpose: "Extract upcoming contracts for planning and forecasting"
```

#### Historical/Expired Contracts

```yaml
query_patterns:
  - name: expired_contracts
    pattern: extraction/temporal
    config:
      source_entity: Contract
      temporal_mode: historical
      date_field_start: start_date
      date_field_end: end_date
      reference_date: "CURRENT_DATE"
      purpose: "Extract expired contracts for historical analysis"
```

## When to Use

✅ **Use when:**
- You have optional fields that are frequently NULL
- You need to LEFT JOIN with tables containing sparse data
- Performance is critical for read operations
- You want to avoid processing NULL rows in JOINs

❌ **Don't use when:**
- All fields are required (not NULL)
- The table has very few NULL values
- You're doing INNER JOINs (use direct joins instead)

## Performance Benefits

### Before (Direct LEFT JOIN)
```sql
SELECT
    loc.*,
    loc.latitude,
    loc.longitude
FROM tb_location loc
LEFT JOIN tb_location coords
    ON coords.pk_location = loc.pk_location
    AND coords.latitude IS NOT NULL
    AND coords.longitude IS NOT NULL;
```
- Processes ALL location rows
- Evaluates NULL conditions for every row
- Poor performance with large datasets

### After (Extraction Pattern)
```sql
SELECT
    loc.*,
    coords.latitude,
    coords.longitude
FROM tb_location loc
LEFT JOIN v_coordinates coords
    ON coords.pk_location = loc.pk_location;
```
- Only processes locations with coordinates
- Pre-filtered data with indexes
- Much faster execution

## Best Practices

1. **Index Strategy**: Always include indexes on join keys and filter fields
2. **Naming Convention**: Use descriptive names like `v_{entity}_coordinates`
3. **Documentation**: Always include `purpose` to explain why extraction exists
4. **Refresh Strategy**: Consider materialized views for very large datasets
5. **Monitoring**: Watch for changes in data distribution that might affect performance

## Migration from Manual Views

When migrating from manually written SQL views:

1. Identify the filtering logic in your existing view
2. Map the filters to pattern parameters
3. Replace manual SQL with pattern configuration
4. Test for equivalent results
5. Remove the manual SQL file

### Example Migration

**Before (manual SQL):**
```sql
CREATE VIEW v_location_coordinates AS
SELECT
    pk_location,
    latitude,
    longitude
FROM tb_location
WHERE latitude IS NOT NULL
  AND longitude IS NOT NULL
  AND deleted_at IS NULL;
```

**After (pattern):**
```yaml
query_patterns:
  - name: coordinates
    pattern: extraction/component
    config:
      source_entity: Location
      extracted_fields:
        - name: latitude
        - name: longitude
      filter_condition: "latitude IS NOT NULL AND longitude IS NOT NULL"
```
