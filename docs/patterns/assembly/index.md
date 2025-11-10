# Assembly Patterns

## Overview

Assembly patterns build complex nested data structures from multiple related entities. These patterns are essential for creating hierarchical JSON responses and complex business object representations.

**Use Cases:**
- Contract price trees with multiple levels
- Product configurations with nested options
- Organizational structures with detailed hierarchies
- Complex business object assembly

## Tree Builder Pattern

**Category**: Assembly Patterns
**Use Case**: Build deeply nested hierarchies with multi-CTE composition
**Complexity**: Very High
**PrintOptim Examples**: 2 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `root_entity` | entity_reference | ✅ | Root entity for the hierarchy |
| `hierarchy` | array | ✅ | Level definitions with sources and joins |
| `max_depth` | integer | ❌ | Maximum nesting depth (default: 4) |

### Generated SQL

Complex multi-CTE structure with nested JSONB aggregation.

### Examples

#### Example: Contract Price Tree

```yaml
query_patterns:
  - name: contract_price_tree
    pattern: assembly/tree_builder
    config:
      root_entity: Contract
      hierarchy:
        - level: contract_base
          source: tv_contract
          group_by: [pk_contract]
        - level: contract_items
          source: tv_contract_item
          child_levels: [pricing_tiers]
      max_depth: 4
```

### When to Use

✅ **Use when:**
- Complex nested JSONB structures
- Multi-level business hierarchies
- Deep entity relationships
- Frontend needs rich object graphs

❌ **Don't use when:**
- Simple aggregations suffice
- Flat data structures
- Performance-critical paths

## Simple Aggregation Pattern

**Category**: Assembly Patterns
**Use Case**: Simple nested aggregation with subquery
**Complexity**: Medium
**PrintOptim Examples**: 3 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parent_entity` | entity_reference | ✅ | Parent entity |
| `child_entity` | entity_reference | ✅ | Child entity for aggregation |
| `child_array_field` | string | ✅ | JSONB array field name |
| `child_fields` | array | ✅ | Fields to include in child objects |

### Generated SQL

```sql
CREATE OR REPLACE VIEW tenant.v_contract_with_items AS
SELECT
    c.*,
    (
        SELECT jsonb_agg(jsonb_build_object(
            'id', ci.pk_contract_item,
            'name', ci.name,
            'quantity', ci.quantity
        ))
        FROM tenant.tb_contract_item ci
        WHERE ci.contract_id = c.pk_contract
          AND ci.deleted_at IS NULL
    ) AS items
FROM tenant.tb_contract c
WHERE c.deleted_at IS NULL;
```

### Examples

#### Example: Contract with Items

```yaml
query_patterns:
  - name: contract_with_items
    pattern: assembly/simple_aggregation
    config:
      parent_entity: Contract
      child_entity: ContractItem
      child_array_field: items
      child_fields:
        - name: id
          expression: pk_contract_item
        - name: name
        - name: quantity
```

### When to Use

✅ **Use when:**
- 1-level nested aggregations
- JSONB array responses needed
- Simple parent-child relationships
- API object composition

❌ **Don't use when:**
- Complex multi-level hierarchies
- Flat responses sufficient
- Performance-critical (use separate queries)