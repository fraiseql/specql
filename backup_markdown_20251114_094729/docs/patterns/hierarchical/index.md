# Hierarchical Patterns

## Overview

Hierarchical patterns handle tree-structured data and parent-child relationships. These patterns are essential for organizational structures, geographical hierarchies, and any data with nested relationships.

**Use Cases:**
- Organizational charts (departments, teams)
- Geographical hierarchies (country → region → city)
- Product categories (main → sub → sub-sub)
- Bill of materials (assemblies → components)

## Hierarchical Flattener Pattern

**Category**: Hierarchical Patterns
**Use Case**: Flatten tree structures for frontend tree components
**Complexity**: High
**PrintOptim Examples**: 6 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_table` | string | ✅ | Commodity table with hierarchical data |
| `extracted_fields` | array | ✅ | JSONB fields to extract |
| `frontend_format` | enum | ✅ | rust_tree, react_tree, generic |
| `required_fields` | array | ✅ | id, parent_id, label, value |
| `path_field` | string | ❌ | ltree path field for advanced queries |

### Generated SQL

```sql
-- @fraiseql:view
-- @fraiseql:description Flattened location hierarchy for Rust tree component
CREATE OR REPLACE VIEW tenant.v_flat_location_for_rust_tree AS
SELECT
    (data->>'id')::uuid AS id,
    NULLIF(data->'parent'->>'id', '')::uuid AS parent_id,
    data->>'name' AS label,
    data->>'id' AS value,
    REPLACE(data->>'path', '.', '_')::text AS ltree_id,
    data
FROM tenant.tv_location
WHERE deleted_at IS NULL;

-- Index for parent lookup (tree traversal)
CREATE INDEX IF NOT EXISTS idx_v_flat_location_for_rust_tree_parent
    ON tenant.v_flat_location_for_rust_tree(parent_id)
    WHERE parent_id IS NOT NULL;

-- Index for ltree operations
CREATE INDEX IF NOT EXISTS idx_v_flat_location_for_rust_tree_ltree
    ON tenant.v_flat_location_for_rust_tree USING GIST (ltree_id);
```

### Examples

#### Example: Location Hierarchy for Frontend

```yaml
query_patterns:
  - name: flat_location_for_rust_tree
    pattern: hierarchical/flattener
    config:
      source_table: tv_location
      extracted_fields:
        - name: id
          expression: "(data->>'id')::uuid"
        - name: parent_id
          expression: "NULLIF(data->'parent'->>'id', '')::uuid"
        - name: label
          expression: "data->>'name'"
        - name: value
          expression: "data->>'id'"
      frontend_format: rust_tree
```

### When to Use

✅ **Use when:**
- Building tree components in frontend
- Need flattened hierarchy for UI consumption
- Working with JSONB hierarchical data
- Tree traversal and display operations

❌ **Don't use when:**
- Simple parent-child queries
- No frontend tree requirements
- Flat data structures

## Path Expander Pattern

**Category**: Hierarchical Patterns
**Use Case**: Expand ltree paths to arrays of ancestor data
**Complexity**: High
**PrintOptim Examples**: 4 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_entity` | entity_reference | ✅ | Hierarchical entity |
| `path_field` | string | ✅ | ltree path field |
| `expanded_fields` | array | ✅ | ancestor_ids, ancestor_names, etc. |
| `max_depth` | integer | ❌ | Limit ancestor expansion |

### Generated SQL

```sql
WITH expanded AS (
  SELECT
    pk_location,
    path,
    unnest(string_to_array(path::text, '.'))::integer AS ancestor_id
  FROM tb_location
),
enriched AS (
  SELECT
    e.pk_location,
    array_agg(a.name ORDER BY nlevel(a.path)) AS ancestor_names,
    array_agg(a.pk_location ORDER BY nlevel(a.path)) AS ancestor_ids
  FROM expanded e
  JOIN tb_location a ON a.pk_location = e.ancestor_id
  GROUP BY e.pk_location
)
SELECT * FROM enriched;
```

### Examples

#### Example: Location Breadcrumb Paths

```yaml
query_patterns:
  - name: location_breadcrumbs
    pattern: hierarchical/path_expander
    config:
      source_entity: Location
      path_field: path
      expanded_fields:
        - ancestor_ids
        - ancestor_names
        - breadcrumb_labels
```

### When to Use

✅ **Use when:**
- Need breadcrumb navigation
- Displaying hierarchical paths
- Ancestor-based queries and filtering
- Tree navigation UI components

❌ **Don't use when:**
- Simple parent lookups
- No breadcrumb requirements
- Flat hierarchies