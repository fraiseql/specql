# Pattern Detection: Automatic Schema Optimization

> **Automatically detect and apply common database patterns to improve your SpecQL entities**

## What You'll Learn

This guide covers SpecQL's pattern detection and application system:

- ✅ **`patterns detect`** - Analyze entities for common patterns
- ✅ **`patterns apply`** - Automatically enhance entities with patterns
- ✅ **Built-in patterns** - Audit trails, soft deletes, multi-tenancy, etc.
- ✅ **Custom patterns** - Define your own reusable patterns

## Prerequisites

- ✅ SpecQL CLI installed
- ✅ Entity YAML files to analyze
- ✅ Understanding of SpecQL entities

## Pattern Overview

### What are Patterns?

Patterns are reusable schema enhancements that implement common database design patterns:

- **Audit Trail**: Automatic tracking of created/updated timestamps and users
- **Soft Delete**: Logical deletion instead of physical removal
- **Multi-Tenant**: Automatic tenant isolation
- **State Machine**: Status field with valid transitions
- **Versioning**: Track entity changes over time

### Pattern Detection Process

1. **AST Analysis**: Parse entity YAML into abstract syntax tree
2. **Pattern Matching**: Compare against known pattern signatures
3. **Confidence Scoring**: Rate how well the entity matches each pattern
4. **Suggestion Generation**: Provide actionable recommendations

## Basic Usage

### Detect Patterns in Entities

```bash
# Analyze a single entity
specql patterns detect entities/user.yaml

# Analyze all entities in directory
specql patterns detect entities/

# Output as JSON for processing
specql patterns detect entities/ --format=json

# Set minimum confidence threshold
specql patterns detect entities/ --min-confidence=0.8
```

### Example Output

```
Analyzing entities/user.yaml...
Found patterns:
  • audit-trail (confidence: 0.95)
    Evidence: Entity has 'created_at', 'updated_at' fields
    Suggestion: Add 'created_by', 'updated_by' fields for complete audit trail

  • soft-delete (confidence: 0.85)
    Evidence: Entity has 'deleted_at' field
    Suggestion: Add index on 'deleted_at' and update queries to filter deleted records
```

## Applying Patterns

### Automatic Application

```bash
# Apply audit trail pattern
specql patterns apply audit-trail entities/user.yaml

# Preview changes without modifying
specql patterns apply audit-trail entities/user.yaml --preview

# Apply to all entities in directory
specql patterns apply audit-trail entities/
```

### What Gets Added

**Audit Trail Pattern** adds:
```yaml
fields:
  created_at: timestamp
  created_by: ref(User)
  updated_at: timestamp
  updated_by: ref(User)

indexes:
  - fields: [created_at]
  - fields: [updated_at]
```

**Soft Delete Pattern** adds:
```yaml
fields:
  deleted_at: timestamp

indexes:
  - fields: [deleted_at]
    where: "deleted_at IS NULL"

validation:
  - field: deleted_at
    rules:
      - nullable: true
```

## Built-in Patterns

### Audit Trail Pattern

**Detects**: Entities with some audit fields
**Applies**: Complete audit trail with user tracking

```yaml
# Before
entity: Post
fields:
  title: text
  content: text

# After applying audit-trail
entity: Post
fields:
  title: text
  content: text
  created_at: timestamp
  created_by: ref(User)
  updated_at: timestamp
  updated_by: ref(User)
```

### Soft Delete Pattern

**Detects**: Entities with `deleted_at` or similar fields
**Applies**: Proper soft delete implementation

```yaml
# Adds proper indexing and validation
indexes:
  - fields: [deleted_at]
    where: "deleted_at IS NULL"

validation:
  - field: deleted_at
    rules:
      - nullable: true
```

### Multi-Tenant Pattern

**Detects**: Entities with `tenant_id` fields
**Applies**: Row-level security and tenant isolation

```yaml
# Before
entity: Invoice
fields:
  tenant_id: uuid
  amount: decimal

# After applying multi-tenant
entity: Invoice
fields:
  tenant_id: uuid!
  amount: decimal

indexes:
  - fields: [tenant_id]

security:
  - policy: "tenant_isolation"
    using: "tenant_id = current_tenant_id()"
```

### State Machine Pattern

**Detects**: Entities with status enums
**Applies**: Valid state transitions and constraints

```yaml
# Before
entity: Order
fields:
  status: enum[pending, processing, shipped, delivered]

# After applying state-machine
entity: Order
fields:
  status: enum[pending, processing, shipped, delivered]!

validation:
  - field: status
    rules:
      - transitions:
          pending: [processing]
          processing: [shipped]
          shipped: [delivered]
          delivered: []
```

## Advanced Usage

### Custom Patterns

Create your own patterns by defining YAML specifications:

```yaml
# patterns/custom/ecommerce-product.yaml
pattern: ecommerce-product
description: "E-commerce product with inventory tracking"

detect:
  - field_exists: price
  - field_exists: sku
  - schema_equals: ecommerce

apply:
  fields:
    inventory_count: integer
    low_stock_threshold: integer
    is_active: boolean!

  validation:
    - field: price
      rules:
        - min: 0
    - field: inventory_count
      rules:
        - min: 0

  indexes:
    - fields: [sku]
      unique: true
    - fields: [is_active, inventory_count]
```

### Pattern Composition

Apply multiple patterns to a single entity:

```bash
# Apply multiple patterns
specql patterns apply audit-trail,soft-delete,versioned entities/document.yaml

# Or apply separately for control
specql patterns apply audit-trail entities/document.yaml
specql patterns apply soft-delete entities/document.yaml
specql patterns apply versioned entities/document.yaml
```

### Integration with Workflows

Patterns work seamlessly with other SpecQL commands:

```bash
# Detect patterns during sync
specql workflow sync entities/ --include-patterns

# Migrate and apply patterns
specql workflow migrate schema.sql --reverse-from=sql -o entities/
specql patterns apply audit-trail entities/
```

## CI/CD Integration

### Automated Pattern Application

```yaml
# .github/workflows/pattern-check.yml
name: Pattern Analysis
on:
  pull_request:
    paths:
      - 'entities/*.yaml'

jobs:
  patterns:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install SpecQL
        run: pip install specql

      - name: Detect Patterns
        run: |
          specql patterns detect entities/ --format=json > patterns.json

      - name: Apply Suggested Patterns
        run: |
          # Auto-apply high-confidence patterns
          for entity in entities/*.yaml; do
            specql patterns apply audit-trail "$entity" || true
            specql patterns apply soft-delete "$entity" || true
          done

      - name: Commit Pattern Improvements
        run: |
          if [ -n "$(git status --porcelain)" ]; then
            git config --global user.name 'SpecQL Bot'
            git config --global user.email 'bot@specql.dev'
            git add entities/
            git commit -m "Auto-apply detected patterns"
            git push
          fi
```

### Pattern Compliance Checks

```yaml
# Require certain patterns for entities
- name: Check Required Patterns
  run: |
    # Ensure all entities have audit trails
    for entity in entities/*.yaml; do
      if ! specql patterns detect "$entity" | grep -q "audit-trail"; then
        echo "Entity $entity missing audit trail pattern"
        exit 1
      fi
    done
```

## Best Practices

### Pattern Selection

1. **Start with Core Patterns**: Audit trail and soft delete are almost always beneficial
2. **Domain-Specific Patterns**: Multi-tenant for SaaS, state machines for workflows
3. **Confidence Thresholds**: Only apply patterns with >80% confidence automatically
4. **Manual Review**: Always review pattern applications before committing

### Pattern Conflicts

Some patterns may conflict - apply in this order:
1. **Audit Trail** (adds fields)
2. **Soft Delete** (adds fields)
3. **Multi-Tenant** (adds security)
4. **State Machine** (adds validation)

### Custom Pattern Development

```yaml
# patterns/custom/company-entity.yaml
pattern: company-entity
description: "Standard company entity with address"

detect:
  - field_exists: name
  - field_type: name = text
  - schema_in: [public, company]

apply:
  fields:
    address_line_1: text
    address_line_2: text
    city: text
    state: text
    postal_code: text
    country: text!

  validation:
    - field: country
      rules:
        - in: [US, CA, UK, AU]  # Supported countries
```

## Troubleshooting

### Detection Issues

**"No patterns detected"**
- Check entity YAML syntax
- Ensure fields match pattern signatures
- Try lowering `--min-confidence` threshold

**"Pattern confidence too low"**
- Add more fields that match the pattern
- Check if entity follows expected conventions

### Application Issues

**"Pattern already applied"**
- Pattern has already been applied to this entity
- Check for duplicate fields or validation rules

**"Conflicting patterns"**
- Some patterns modify the same fields
- Apply patterns in recommended order
- Manually resolve conflicts

### Performance

**Large entity sets**: Use `--parallel` for batch operations
**Complex patterns**: Simplify custom pattern rules

## Examples by Domain

### E-commerce

```bash
# Product entities
specql patterns apply audit-trail entities/product.yaml
specql patterns apply soft-delete entities/product.yaml

# Order entities
specql patterns apply audit-trail entities/order.yaml
specql patterns apply state-machine entities/order.yaml
```

### SaaS Application

```bash
# All entities in multi-tenant app
for entity in entities/*.yaml; do
  specql patterns apply multi-tenant "$entity"
  specql patterns apply audit-trail "$entity"
done
```

### Content Management

```bash
# Article entities
specql patterns apply audit-trail entities/article.yaml
specql patterns apply versioned entities/article.yaml
specql patterns apply soft-delete entities/article.yaml
```

## Next Steps

- **[Workflow Automation](workflow-automation.md)** - Integrate patterns with migrate/sync
- **[Validation Guide](../05_guides/validation.md)** - Custom validation rules
- **[Multi-Tenancy](../05_guides/multi-tenancy.md)** - Advanced tenant patterns

## Related Commands

- `specql workflow sync --include-patterns` - Sync with pattern detection
- `specql validate` - Ensure pattern applications are valid
- `specql generate` - Generate code with applied patterns

---

**Time to read: 8 minutes | Patterns covered: 5 | Use cases: Auto-enhancement, CI/CD, Custom patterns**</content>
</xai:function_call name="todowrite">
<parameter name="todos">[{"status":"completed","id":"create-pattern-guide"}]
