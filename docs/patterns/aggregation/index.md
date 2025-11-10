# Aggregation Patterns

## Overview

Aggregation patterns calculate metrics and statistics across related entities. These patterns handle counting, summing, and other aggregate operations while maintaining proper multi-tenant filtering and soft delete handling.

**Use Cases:**
- Dashboard metrics and KPIs
- Status summaries and counts
- Hierarchical rollups and statistics
- Boolean status flags from aggregations

## Count Aggregation Pattern

**Category**: Aggregation Patterns
**Use Case**: Count child entities grouped by parent with conditional metrics
**Complexity**: Medium
**PrintOptim Examples**: 12 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `counted_entity` | entity_reference | ✅ | Entity being counted (child) |
| `grouped_by_entity` | entity_reference | ✅ | Entity to group by (parent) |
| `join_condition` | string | ❌ | Custom JOIN condition |
| `metrics` | array | ✅ | Metrics with names and conditions |
| `schema` | string | ❌ | Target schema (default: tenant) |

### Generated SQL

```sql
CREATE OR REPLACE VIEW tenant.v_count_allocations_by_network AS
SELECT
    nc.pk_network_configuration,
    COUNT(CASE WHEN TRUE THEN 1 END) AS total_allocations,
    COUNT(CASE WHEN a.status = 'active' THEN 1 END) AS active_allocations,
    nc.tenant_id
FROM tb_network_configuration nc
LEFT JOIN tb_allocation a
    ON a.network_configuration_id = nc.pk_network_configuration
WHERE nc.deleted_at IS NULL
  AND (a.deleted_at IS NULL OR a.pk_allocation IS NULL)
  AND nc.tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid
GROUP BY nc.pk_network_configuration, nc.tenant_id;
```

### Examples

#### Example 1: Count Allocations by Network

```yaml
query_patterns:
  - name: count_allocations_by_network
    pattern: aggregation/count_aggregation
    config:
      counted_entity: Allocation
      grouped_by_entity: NetworkConfiguration
      metrics:
        - name: total_allocations
          condition: "TRUE"
        - name: active_allocations
          condition: "allocation.status = 'active'"
```

#### Example 2: Count Contracts by Location

```yaml
query_patterns:
  - name: count_contracts_by_location
    pattern: aggregation/count_aggregation
    config:
      counted_entity: Contract
      grouped_by_entity: Location
      metrics:
        - name: active_contracts
          condition: "contract.status = 'active' AND contract.start_date <= CURRENT_DATE AND (contract.end_date IS NULL OR contract.end_date >= CURRENT_DATE)"
```

### When to Use

✅ **Use when:**
- Need counts grouped by parent entities
- Multiple conditional metrics required
- Dashboard and reporting queries
- Status summaries

❌ **Don't use when:**
- Simple single counts (use direct aggregation)
- Complex hierarchical aggregations (use hierarchical patterns)
- Real-time requirements (consider materialized views)

## Hierarchical Count Pattern

**Category**: Aggregation Patterns
**Use Case**: Hierarchical aggregation using ltree paths
**Complexity**: High
**PrintOptim Examples**: 8 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `counted_entity` | entity_reference | ✅ | Entity being counted |
| `grouped_by_entity` | entity_reference | ✅ | Hierarchical entity to group by |
| `metrics` | array | ✅ | Direct vs hierarchical counts |
| `path_field` | string | ❌ | ltree path field (default: path) |

### Generated SQL

```sql
CREATE OR REPLACE VIEW tenant.v_count_allocations_by_location AS
SELECT
    loc.pk_location,
    COUNT(CASE WHEN a.location_id = loc.pk_location THEN 1 END) AS direct_allocations,
    COUNT(CASE WHEN loc.path @> a.location_path THEN 1 END) AS total_allocations,
    loc.path,
    loc.tenant_id
FROM tb_location loc
LEFT JOIN tb_allocation a
    ON a.tenant_id = loc.tenant_id
WHERE loc.deleted_at IS NULL
  AND (a.deleted_at IS NULL OR a.pk_allocation IS NULL)
GROUP BY loc.pk_location, loc.path, loc.tenant_id;
```

### Examples

#### Example: Location Hierarchy Counts

```yaml
query_patterns:
  - name: count_allocations_by_location
    pattern: aggregation/hierarchical_count
    config:
      counted_entity: Allocation
      grouped_by_entity: Location
      metrics:
        - name: allocations
          direct: true
          hierarchical: true
```

### When to Use

✅ **Use when:**
- Hierarchical data with ltree paths
- Need both direct and total counts
- Organizational or geographical hierarchies
- Tree-structured aggregations

❌ **Don't use when:**
- Flat hierarchies (use basic count aggregation)
- No ltree paths available
- Simple parent-child relationships

## Boolean Flags Pattern

**Category**: Aggregation Patterns
**Use Case**: Derive boolean status flags from aggregations
**Complexity**: Medium
**PrintOptim Examples**: 9 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_entity` | entity_reference | ✅ | Entity to add flags to |
| `flags` | array | ✅ | Boolean flags with conditions |
| `array_field` | string | ❌ | Optional JSONB array field |

### Generated SQL

```sql
CREATE OR REPLACE VIEW tenant.v_current_allocations_by_machine AS
SELECT
    m.pk_machine,
    (EXISTS(SELECT 1 FROM tb_allocation a WHERE a.machine_id = m.pk_machine AND a.status = 'active')) AS has_active_allocations,
    (COUNT(CASE WHEN a.status = 'error' THEN 1 END) > 0) AS has_errors,
    COALESCE(jsonb_agg(
        jsonb_build_object('id', a.pk_allocation, 'status', a.status)
        ORDER BY a.created_at DESC
    ), '[]'::jsonb) AS recent_allocations,
    m.tenant_id
FROM tb_machine m
LEFT JOIN tb_allocation a ON a.machine_id = m.pk_machine
WHERE m.deleted_at IS NULL
  AND (a.deleted_at IS NULL OR a.pk_allocation IS NULL)
GROUP BY m.pk_machine, m.tenant_id;
```

### Examples

#### Example: Machine Status Flags

```yaml
query_patterns:
  - name: current_allocations_by_machine
    pattern: aggregation/boolean_flags
    config:
      source_entity: Machine
      flags:
        - name: has_active_allocations
          condition: "EXISTS(SELECT 1 FROM tb_allocation a WHERE a.machine_id = machine.pk_machine AND a.status = 'active')"
        - name: has_errors
          condition: "COUNT(CASE WHEN allocation.status = 'error' THEN 1 END) > 0"
      array_field: recent_allocations
```

### When to Use

✅ **Use when:**
- Need boolean status indicators
- Combining aggregations with existence checks
- API responses requiring status flags
- Dashboard status indicators

❌ **Don't use when:**
- Only simple aggregations needed
- No boolean logic required
- Performance-critical (consider computed columns)