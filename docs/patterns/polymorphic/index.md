# Polymorphic Patterns

## Overview

Polymorphic patterns handle entities that can represent different types of objects. These patterns are essential when you have ambiguous primary keys that could refer to different entity types.

**Use Cases:**
- Product or contract item references
- Generic document attachments
- User or organization references
- Flexible relationship modeling

## Type Resolver Pattern

**Category**: Polymorphic Patterns
**Use Case**: Resolve ambiguous PKs to entity types
**Complexity**: High
**PrintOptim Examples**: 2 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `discriminator_field` | string | ✅ | Field indicating the type (e.g., "class") |
| `variants` | array | ✅ | Entity variants with their classes |
| `output_key` | string | ✅ | Unified PK field name |

### Generated SQL

```sql
-- @fraiseql:view
-- @fraiseql:description Polymorphic type resolver for product_or_item
CREATE OR REPLACE VIEW tenant.v_pk_class_resolver AS
SELECT
    p.pk_product AS pk_value,
    'product'::text AS class
FROM tenant.tb_product p
WHERE p.deleted_at IS NULL
UNION ALL
SELECT
    ci.pk_contract_item AS pk_value,
    'contract_item'::text AS class
FROM tenant.tb_contract_item ci
WHERE ci.deleted_at IS NULL;

-- Materialized version for performance
CREATE MATERIALIZED VIEW tenant.m_pk_class_resolver AS
SELECT * FROM tenant.v_pk_class_resolver;

-- Unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_m_pk_class_resolver_pk_class
    ON tenant.m_pk_class_resolver(pk_value, class);
```

### Examples

#### Example: Product or Contract Item

```yaml
query_patterns:
  - name: pk_class_resolver
    pattern: polymorphic/type_resolver
    config:
      discriminator_field: class
      variants:
        - entity: Product
          key_field: pk_product
          class_value: product
        - entity: ContractItem
          key_field: pk_contract_item
          class_value: contract_item
      output_key: pk_value
```

### When to Use

✅ **Use when:**
- Ambiguous foreign keys to multiple entities
- Generic relationships (attachments, comments)
- Flexible schema design
- Type discrimination needed

❌ **Don't use when:**
- Clear entity relationships
- No type ambiguity
- Simple foreign keys