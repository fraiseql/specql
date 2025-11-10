# Junction Patterns

## Overview

Junction patterns resolve N-to-N (many-to-many) relationships by traversing through intermediate junction tables. These patterns are essential for complex business logic where entities are connected through multiple relationship layers.

**Use Cases:**
- Contract → Financing Condition → Model relationships
- Product → Category → Attribute mappings
- User → Role → Permission hierarchies

## Resolver Pattern

**Category**: Junction Patterns
**Use Case**: Resolve many-to-many relationships through junction tables
**Complexity**: Medium
**PrintOptim Examples**: 15 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_entity` | entity_reference | ✅ | Starting entity in N-to-N relationship |
| `junction_tables` | array | ✅ | Intermediate junction tables with join keys |
| `target_entity` | entity_reference | ✅ | Final entity to resolve to |
| `output_fields` | array | ❌ | Fields to include (default: all PKs + tenant_id) |
| `schema` | string | ❌ | Target schema (default: tenant) |

### Generated SQL

```sql
CREATE OR REPLACE VIEW tenant.v_financing_condition_and_model_by_contract AS
SELECT DISTINCT
    c.pk_contract,
    fc.pk_financing_condition,
    m.pk_model,
    c.tenant_id
FROM tb_contract c
INNER JOIN tb_contract_financing_condition cfc
    ON cfc.contract_id = c.pk_contract
INNER JOIN tb_financing_condition fc
    ON fc.pk_financing_condition = cfc.financing_condition_id
INNER JOIN tb_financing_condition_model fcm
    ON fcm.financing_condition_id = fc.pk_financing_condition
INNER JOIN tb_model m
    ON m.pk_model = fcm.model_id
WHERE c.deleted_at IS NULL
  AND cfc.deleted_at IS NULL
  AND fc.deleted_at IS NULL
  AND fcm.deleted_at IS NULL
  AND m.deleted_at IS NULL
  AND c.tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid;
```

### Examples

#### Example 1: Contract → Financing Condition → Model

```yaml
query_patterns:
  - name: financing_condition_and_model_by_contract
    pattern: junction/resolver
    config:
      source_entity: Contract
      junction_tables:
        - table: ContractFinancingCondition
          left_key: contract_id
          right_key: financing_condition_id
        - table: FinancingConditionModel
          left_key: financing_condition_id
          right_key: model_id
      target_entity: Model
```

#### Example 2: Product → Category → Attribute (2-hop)

```yaml
query_patterns:
  - name: product_attributes_by_category
    pattern: junction/resolver
    config:
      source_entity: Product
      junction_tables:
        - table: ProductCategory
          left_key: product_id
          right_key: category_id
      target_entity: CategoryAttribute
```

### When to Use

✅ **Use when:**
- Resolving N-to-N relationships through junction tables
- Need efficient traversal of multi-hop relationships
- Want to expose intermediate junction data
- Building complex entity graphs

❌ **Don't use when:**
- Simple 1-to-N relationships (use direct JOIN)
- Need aggregation (use aggregation patterns)
- Performance-critical paths (consider materialized views)

## Aggregated Resolver Pattern

**Category**: Junction Patterns
**Use Case**: Junction resolver with JSONB array aggregation
**Complexity**: High
**PrintOptim Examples**: 8 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_entity` | entity_reference | ✅ | Parent entity for aggregation |
| `junction_path` | array | ✅ | Path through junction tables |
| `aggregate_into` | string | ✅ | Field name for JSONB array |
| `order_by` | array | ❌ | Optional ordering for aggregated items |

### Generated SQL

```sql
CREATE OR REPLACE VIEW tenant.v_machine_items AS
SELECT
    m.pk_machine,
    jsonb_agg(
        jsonb_build_object(
            'id', i.pk_item,
            'name', i.name,
            'quantity', mi.quantity
        ) ORDER BY i.name
    ) AS items
FROM tb_machine m
LEFT JOIN tb_machine_item mi ON mi.machine_id = m.pk_machine
LEFT JOIN tb_item i ON i.pk_item = mi.item_id
WHERE m.deleted_at IS NULL
  AND mi.deleted_at IS NULL
  AND i.deleted_at IS NULL
GROUP BY m.pk_machine;
```

### Examples

#### Example: Machine with Items Array

```yaml
query_patterns:
  - name: machine_items
    pattern: junction/aggregated_resolver
    config:
      source_entity: Machine
      junction_path:
        - table: MachineItem
          left_key: machine_id
          right_key: item_id
      target_entity: Item
      aggregate_into: items
      order_by: [name]
```

### When to Use

✅ **Use when:**
- Need nested JSONB arrays from junction relationships
- Building API responses with related data
- Frontend needs hierarchical data structures

❌ **Don't use when:**
- Simple lookups (use basic resolver)
- Large datasets (performance impact)
- Real-time requirements (consider caching)